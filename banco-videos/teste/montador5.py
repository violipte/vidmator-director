# -*- coding: utf-8 -*-
"""MONTADOR (Stage 4, parte Python) — resolvido.json -> pacote de montagem p/ Remotion.
- Copia assets + narração p/ remotion/public/jobs/<nome>/
- Mapeia dados (formato LLM) -> props REAIS dos componentes do acervo
- Gera montagem.json (beats + seções/wash + áudio) que o Montagem.tsx renderiza.
Uso: python montador.py --job _job_hilux --plano <plano_beats.json> --audio <mp3> --nome hilux_mont
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).parent))
from acervo_registry import R as REG_R, DEPRECATED, escolher, rebuild, frase_de_tela, frase_forcada, humanizar, _nums_do_texto, set_style, corte, SWAP_TO_OVL  # noqa
from acervo_registry import _OVL_DIM as _OVL_DIM_M  # noqa — dim por overlay (R-72b)
from diretor_v2_pass import natureza_do_beat, CADEIA  # noqa

REMOTION_PUB = Path(r"F:/Canal Dark/Aplicativo de Edição/remotion/public")
REG_INFO = {r["comp"]: r for r in REG_R}


# mapear_props MORREU (QA Piter 21/07): defaults de exemplo (Hilux 90/78, Tehran->Dubai,
# "SUBJECT") vazavam pro video. O REGISTRY e a UNICA porta de render agora (pass no main).


def _dic5(d):
    """dados do LLM podem vir como LISTA — normaliza p/ dict (31/07)."""
    if isinstance(d, (list, tuple)):
        d = next((x for x in d if isinstance(x, dict)), None)
    return d if isinstance(d, dict) else {}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--job", required=True)
    ap.add_argument("--plano", required=True)
    ap.add_argument("--audio", required=True)
    ap.add_argument("--nome", required=True)
    ap.add_argument("--roteiro", default="", help="roteiro ORIGINAL (valida nomes próprios "
                                                  "contra erro de STT; default: <job>/roteiro*.txt)")
    a = ap.parse_args()

    job = Path(a.job) if Path(a.job).is_absolute() else Path(r"F:/Canal Dark/Aplicativo de Edição/banco-videos") / a.job
    # job novo (curador5 sozinho) não tem o consolidado do executor — a pasta
    # resolvido/ abaixo é a fonte; o consolidado é opcional
    # roteiro = fonte de verdade dos nomes próprios (o diretor lê a TRANSCRIÇÃO, e o
    # STT troca nome: "Minas Gerais" -> "Nasgerice" virou autor de citação no ar)
    _rot = Path(a.roteiro) if a.roteiro else next(iter(sorted(job.glob("roteiro*.txt"))), None)
    if _rot and Path(_rot).exists():
        from acervo_registry import set_roteiro  # noqa
        set_roteiro(Path(_rot).read_text(encoding="utf-8", errors="ignore"))
        print(f"roteiro de validação: {Path(_rot).name}")
    else:
        print("!! sem roteiro — atribuições de citação NÃO serão validadas")

    _rj = job / "resolvido.json"
    resolvido = json.loads(_rj.read_text(encoding="utf-8")) if _rj.exists() else []
    # 27/07: o CURADOR grava por-beat em resolvido/ (inclui banco secao=900) e NÃO
    # atualiza o resolvido.json consolidado do executor — sem este merge o banco de
    # nicho inteiro ficava invisível pro montador (40 clipes fora da montagem)
    _por_i = {r.get("i"): r for r in resolvido}
    for _f in sorted((job / "resolvido").glob("b*.json")):
        try:
            _r = json.loads(_f.read_text(encoding="utf-8"))
        except Exception:
            continue
        _arq = _r.get("arquivo")
        if _arq and not Path(_arq).exists():
            continue  # asset condenado/apagado — não ressuscita
        _r.setdefault("tipo_final", _r.get("tipo"))  # jsons por-beat não carregam tipo_final
        _por_i[_r.get("i")] = _r
    _MIDIA = (".mp4", ".webm", ".mov", ".jpg", ".jpeg", ".png", ".webp")
    resolvido = []
    for _k in sorted(_por_i):
        _r = _por_i[_k]
        _arq = str(_r.get("arquivo") or "")
        if _arq.lower().endswith(_MIDIA) and not Path(_arq).exists():
            continue  # entrada BASE apontando pra condenado (auditor 27/07: fantasma b158)
        resolvido.append(_r)
    plano = json.loads(Path(a.plano).read_text(encoding="utf-8"))
    _pi = {r.get("i"): r for r in resolvido}
    _n_an = 0
    for _b in plano.get("beats", []):   # ANIMAÇÕES vêm do plano (não passam pelo executor)
        if _b.get("tipo") == "animacao" and _b["i"] not in _pi:
            _pi[_b["i"]] = {**_b, "status": "ok", "tipo_final": "animacao",
                            "arquivo": None, "tier": 0}
            _n_an += 1
    if _n_an:
        resolvido = [_pi[k] for k in sorted(_pi)]
        print(f"animações do plano injetadas [v5]: {_n_an}")
    secoes = plano.get("secoes", [])
    plano_por_i = {pb["i"]: pb for pb in plano.get("beats", [])}  # resolvido NÃO carrega 'texto'

    # R-64 [F1] (QA Piter 22/07): capítulo cinematográfico NÃO é default universal —
    # o NICHO decide via style_card: cinematic (card CHAPTER NN) | minimal (linha overlay) | none
    chapter_style = "cinematic"
    sc_path = job / "style_card.json"
    if sc_path.exists():
        try:
            chapter_style = json.loads(sc_path.read_text(encoding="utf-8")).get("chapter_style", "cinematic")
        except Exception:
            pass
    print(f"chapter_style [R-64]: {chapter_style}")
    try:
        _SC = json.loads(sc_path.read_text(encoding="utf-8")) if sc_path.exists() else {}
    except Exception:
        _SC = {}
    set_style(_SC)
    # R-111: chaves de produto do nicho (anúncio "Number N, the X" exige o produto na tela)
    _DESAMB = [k.lower() for k in (_SC.get("desambiguacao") or {})]
    _ANN111 = re.compile(r"\bnumber\s+(one|two|three|four|five|\d)\b[.,:]?\s", re.I)

    def _eh_anuncio(texto):
        return bool(texto) and bool(_ANN111.search(texto)) \
            and any(k in texto.lower() for k in _DESAMB)

    # R-107 [F1]: tema tipográfico do NICHO assado no bundle do job (tema_atual.ts gerado)
    fonte_tema = "impact"
    if sc_path.exists():
        try:
            fonte_tema = json.loads(sc_path.read_text(encoding="utf-8")).get("fonte_tema", "impact")
        except Exception:
            pass
    tema_ts = REMOTION_PUB.parent / "src" / "tema_atual.ts"
    tema_ts.write_text(
        "/* GERADO PELO MONTADOR a partir de style_card.fonte_tema — NÃO editar na mão. */\n"
        f'export const TEMA_JOB = "{fonte_tema}";\n', encoding="utf-8")
    print(f"fonte_tema [R-107]: {fonte_tema}")

    dest = REMOTION_PUB / "jobs" / a.nome
    (dest / "assets").mkdir(parents=True, exist_ok=True)
    shutil.copy2(a.audio, dest / "audio.mp3")

    def _rw(v):
        if isinstance(v, str) and ("\\assets\\" in v or "/assets/" in v) and Path(v).exists():
            tgt = dest / "assets" / Path(v).name
            if not tgt.exists() or Path(v).stat().st_mtime > tgt.stat().st_mtime:
                shutil.copy2(v, tgt)
            return f"jobs/{a.nome}/assets/{Path(v).name}"
        if isinstance(v, list):
            return [_rw(x) for x in v]
        return v

    def _sec_de(r):
        return next((s for s in secoes if s.get("i") == r.get("secao")), None)

    # R-108 [F1] (QA tenis 23/07): STT quebra NOMES DE MARCA ('ACS Gel Nimbus', 'Animbus',
    # 'The 88') e isso ia pra TELA — correções por job no style_card.correcoes_stt
    _CORR = {}
    if sc_path.exists():
        try:
            _CORR = json.loads(sc_path.read_text(encoding="utf-8")).get("correcoes_stt", {})
        except Exception:
            pass

    def _corr(s):
        for k, v in _CORR.items():
            s = s.replace(k, v)
        return s

    # R-96 [F1] (spec Piter): a linha do título de seção NUNCA reaparece como texto de outro beat
    titulos_secao = {(s.get("titulo") or "").strip().lower() for s in secoes if s.get("titulo")}

    # ---- PASS FINAL REGISTRY-ONLY: quota+cooldown+duração GLOBAIS; NENHUM default renderiza ----
    beats_out, n_copy = [], 0
    quotas, last_use = {}, {}
    n_chapter = 0
    secoes_com_chapter = set()
    anos_usados = set()  # R-27: overlay de ano 1x por ano distinto
    ano_pendente = None  # R-27: carry — ano visto num beat sem src espera o próximo footage
    stats = {"registry_ok": 0, "repick": 0, "resgate_texto": 0, "demote_footage": 0}
    anterior_foi_texto = False  # R-109: nunca 2 animações de texto seguidas
    SEED = sum(ord(c) for c in a.nome) * 100003

    # ---- ORÇAMENTO DE TEXTO (QA Piter 22/07: 28% do tempo em texto = exagero) ----
    # Teto: 12% do vídeo em texto-family. Placa discreta (lower-third/tag/footnote/ticker
    # sobre footage) conta meio peso. Estourou -> beat vira REUSO de footage da seção.
    dur_total = max((r["t_fim"] for r in resolvido), default=0)
    _tb = 0.12
    if sc_path.exists():
        try:
            _tb = json.loads(sc_path.read_text(encoding="utf-8")).get("texto_budget", 0.12)
        except Exception:
            pass
    BUDGET_TEXTO = _tb * dur_total
    tempo_texto = 0.0
    _PLACAS = ("Ovl03", "Ovl04", "Ovl05", "Ovl09")

    # VidRush 24/07: anotações de DADO sobre footage não são "texto" (não contam
    # no orçamento nem no R-109 — são a versão viva do corner-badge deles)
    ANOTA_OVL = {"Ovl11_SpecBadge", "Ovl12_GiantStat", "Ovl13_PriceTag"}

    def _eh_texto(comp):
        return bool(comp) and (comp.startswith("Texto") or comp.startswith("Ovl")) \
            and comp not in ANOTA_OVL

    def _peso_texto(comp):
        return 0.5 if comp.startswith(_PLACAS) else 1.0

    # VidRush 24/07 (continuidade de ASSUNTO): pool de reuso é por ENTIDADE do beat
    # (chave da desambiguacao no texto do plano), não por seção — footage do produto X
    # NUNCA ilustra o produto Y (era assim que Adidas caía no beat do New Balance).
    _res_busca = {r0["i"]: str(r0.get("busca") or "") for r0 in resolvido}

    def _assunto_de(i):
        # assunto = chave da desambiguacao no texto do plano OU na BUSCA do resolvido
        # (24/07: dono com frase genérica mas busca 'Hoka Bondi' emprestava footage
        # de Hoka pro bg da seção do Nimbus — a marca mora na busca, não só na frase)
        t0 = ((plano_por_i.get(i, {}) or {}).get("texto") or "") + " " + _res_busca.get(i, "")
        tl0 = t0.lower()
        for k in _DESAMB:
            if k in tl0:
                return k
        return None  # genérico

    assunto_por_i = {r0["i"]: _assunto_de(r0["i"]) for r0 in resolvido}

    # pool de footage por assunto (src, tier, watermark) — para demote de texto excedente
    pool_ass, pool_uso = {}, {}
    for r0 in resolvido:
        # R-56 [F1]: demote só reusa VÍDEO (movimento disfarça); imagem ESTÁTICA = 1x absoluto
        if r0.get("arquivo") and r0.get("tipo_final") in ("stock", "footage_video") \
                and str(r0["arquivo"]).lower().endswith((".mp4", ".webm", ".mov")):
            chave = assunto_por_i.get(r0["i"]) or f"sec{r0.get('secao', 0)}"
            pool_ass.setdefault(chave, []).append(
                (Path(r0["arquivo"]).name, r0.get("tier", 1), bool(r0.get("watermark")), r0["i"]))

    pool_poss = {}  # asset -> TODAS as posições em que aparece (original + reusos)
    for r0 in resolvido:
        if r0.get("arquivo"):
            pool_poss.setdefault(Path(r0["arquivo"]).name, []).append(r0["i"])

    def _demote_footage(b, r, relax=False):
        """Beat de texto excedente vira b-roll. Fase 1: pool do MESMO assunto, gap>=6.
        Fase 2 (relax): pool global gap>=3 — mas produto-A NUNCA pega footage de produto-B.
        Cap = 1 reuso (2 aparições) sempre."""
        meu_ass = assunto_por_i.get(r["i"]) or f"sec{r.get('secao', 0)}"
        fases = [(pool_ass.get(meu_ass, []), 6)]
        if relax or not fases[0][0]:
            fases.append(([x for v in pool_ass.values() for x in v], 3 if relax else 6))
        for cand, gap_min in fases:
            for nome_arq, tier, wm, orig_i in sorted(cand, key=lambda x: (pool_uso.get(x[0], 0), -abs(x[3] - r["i"]))):
                cand_ass = assunto_por_i.get(orig_i)
                if cand_ass and cand_ass != assunto_por_i.get(r["i"]):
                    continue  # footage de OUTRO produto nomeado — nunca
                poss = pool_poss.get(nome_arq, [])
                # cap = 2 APARIÇÕES TOTAIS (originais do resolvido + reusos) — R-56
                if len(poss) >= 2 or pool_uso.get(nome_arq, 0) >= 1 \
                        or (poss and min(abs(p - r["i"]) for p in poss) < gap_min):
                    continue
                pool_uso[nome_arq] = pool_uso.get(nome_arq, 0) + 1
                pool_poss.setdefault(nome_arq, []).append(r["i"])
                # 01/08 (QA cobras): num "Top 5" com chapter_style CINEMATIC os 5 títulos
                # foram criados (chapters=5) e comidos aqui pelo demote de orçamento —
                # o vídeo foi ao ar sem UM capítulo sequer. Capítulo é ESTRUTURA da
                # narrativa, não enfeite de texto: quem cede o tempo é o resto.
                if b.get("_chapter") or b.get("componente") == "ChapterTitle":
                    print(f"  [R-64] capítulo i={r['i']} protegido do demote de orçamento")
                    return False
                b["tipo"], b["tier"], b["watermark"] = "stock", tier, wm
                b["src"] = f"jobs/{a.nome}/assets/{nome_arq}"
                b.pop("componente", None), b.pop("props", None)
                stats["demote_footage"] += 1
                return True
        return False

    # R-56 (QA tenis 23/07): foto DENTRO de props escapava do controle de reuso — a mesma
    # imagem aparecia como src de um beat E dentro do Img de outro. Bookkeeping unificado.
    def _imgs_props(p):
        out = []
        for v in (p or {}).values():
            for x in ([v] if isinstance(v, str) else v if isinstance(v, list) else []):
                if isinstance(x, str) and x.lower().endswith((".jpg", ".jpeg", ".png")):
                    out.append(Path(x).name)
        return out

    usados_static = set()
    for r0 in resolvido:
        a0 = str(r0.get("arquivo") or "")
        if a0.lower().endswith((".jpg", ".jpeg", ".png")):
            usados_static.add(Path(a0).name)

    # R-109 lookahead: capítulo 'minimal' vira Ovl02 (família texto) em posição FIXA —
    # logo é o beat ANTERIOR que não pode aceitar texto. Simula quais beats serão capítulo
    # (mesmas condições do branch abaixo: 1º ChapterTitle da seção, fora do hook).
    pre_chapter = set()
    if chapter_style == "minimal":
        _seen_sec, _prev_i = set(), None
        for r0 in resolvido:
            if r0.get("componente") == "ChapterTitle" and float(r0["t_ini"]) >= 15.0 \
                    and r0.get("secao") not in _seen_sec:
                _seen_sec.add(r0.get("secao"))
                if _prev_i is not None:
                    pre_chapter.add(_prev_i)
            _prev_i = r0["i"]

    for r in resolvido:
        if r.get("secao") == 900:  # BANCO DE NICHO: alimenta os pools, NUNCA vira beat
            src_b = Path(r.get("arquivo") or "")
            if src_b.exists():
                tgt_b = dest / "assets" / src_b.name
                if not tgt_b.exists() or src_b.stat().st_mtime > tgt_b.stat().st_mtime:
                    shutil.copy2(src_b, tgt_b)
            continue
        b = {"i": r["i"], "t_ini": r["t_ini"], "t_fim": r["t_fim"], "tipo": r["tipo_final"],
             "tier": r.get("tier", 0), "watermark": bool(r.get("watermark")), "secao": r.get("secao", 0)}
        if r.get("arquivo"):
            src = Path(r["arquivo"])
            if src.exists():
                tgt = dest / "assets" / src.name
                if not tgt.exists() or src.stat().st_mtime > tgt.stat().st_mtime:
                    shutil.copy2(src, tgt)  # mtime: asset RE-GERADO com mesmo nome substitui o velho
                    n_copy += 1
                b["src"] = f"jobs/{a.nome}/assets/{src.name}"
                if "__produto" in src.name:
                    # R-111: anúncio de produto NUNCA é engolido pelo ajuste de overlap
                    # (QA 23/07: Clifton dividia o intervalo com o capítulo e sumia)
                    b["_min_dur"] = 2.5
                    # G5 VidRush 24/07: anúncio = foto do produto + RANK+NOME por cima
                    tx0 = _corr((plano_por_i.get(r["i"], {}) or {}).get("texto") or "")
                    tl0 = tx0.lower()
                    _ORD = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
                            "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10}
                    m_rk = re.search(r"number\s+(one|two|three|four|five|six|seven|eight|nine|ten|\d+)", tl0)
                    rk = (_ORD.get(m_rk.group(1)) if m_rk and m_rk.group(1) in _ORD
                          else int(m_rk.group(1)) if m_rk and m_rk.group(1).isdigit() else None)
                    chave_m = next((k for k in (_SC.get("desambiguacao") or {}) if k.lower() in tl0), "")
                    # título do anúncio: titulos_anuncio do style_card > valor da desambiguação
                    modelo = (_SC.get("titulos_anuncio") or {}).get(chave_m) \
                        or (_SC.get("desambiguacao") or {}).get(chave_m, "")
                    modelo = re.sub(r"\s+(running shoe|road bike|hybrid bike|bike|shoe)$", "", modelo, flags=re.I).strip()
                    if modelo:
                        b["tipo"] = "animacao"
                        b["componente"] = "Img21_ProductAnnounce"
                        b["props"] = {"images": [b.pop("src")],
                                      "title": corte((f"#{rk} " if rk else "") + modelo, 40)}
                        usados_static.add(src.name)
                        stats["R111_announce"] = stats.get("R111_announce", 0) + 1
            else:
                b["tipo"] = "animacao"  # arquivo sumiu -> registry decide (nunca DisplayText fixo)

        # COLD-OPEN QUOTE [Piter 27/07, estoico]: citação de ABERTURA (texto entre
        # aspas nos primeiros ~25s) = Typewriter + SFX de typewriter — a exceção
        # consagrada ao sem-texto-no-hook (a autoridade fala antes de ser nomeada)
        _tx_cq = _corr((plano_por_i.get(r["i"], {}) or {}).get("texto") or "").strip()
        if float(r["t_ini"]) < 25.0 and _tx_cq.startswith('"') and not b.get("componente"):
            tx_q = corte(humanizar(_tx_cq.strip('"').strip()), 90)
            if len(tx_q) >= 8:
                b.pop("src", None)
                b["tipo"] = "animacao"
                b["componente"] = "Texto01_Typewriter"
                b["props"] = {"text": tx_q, "kicker": ""}
                b["_cold_quote"] = True
                stats["cold_quote"] = stats.get("cold_quote", 0) + 1

        if b["tipo"] == "animacao" and "componente" not in b:
            dur = float(r["t_fim"]) - float(r["t_ini"])
            comp, props = r.get("componente"), r.get("props_final")
            hook = float(r["t_ini"]) < 15.0  # R-15/R-16 [F1]: primeiros 15s = só classe visual forte
            pb = plano_por_i.get(r["i"], {})
            texto_b = _corr(pb.get("texto") or "")  # R-108
            dados_b_raw = r.get("dados") or pb.get("dados") or {}
            dados_b = json.loads(_corr(json.dumps(dados_b_raw, ensure_ascii=False)))  # R-108 nos dados
            anuncio = _eh_anuncio(texto_b)  # R-111: anúncio de produto — nunca texto/pool genérico

            # P1 (QA Piter 24/07 ×3): beat-MARCADOR de seção (texto == título) NUNCA é
            # conteúdo — vira ChapterTitle e cai no tratamento R-64 do nicho
            tx_marc = re.sub(r"\s*\([\d,\s]+\)\s*$", "", texto_b).strip().lower()
            if tx_marc and tx_marc in {re.sub(r"\s*\([\d,\s]+\)\s*$", "", t).strip() for t in titulos_secao}:
                comp = "ChapterTitle"

            # ChapterTitle estrutural: nº = ordem REAL, título = Stage 1, 1 POR SEÇÃO —
            # FORMA decidida pelo chapter_style do nicho (R-64)
            if comp == "ChapterTitle" and hook:
                comp, props = None, None  # R-15 [F1]: Chapter no hook = vetado -> re-pick forte
                stats["R15_hook"] = stats.get("R15_hook", 0) + 1
            if comp == "ChapterTitle" and chapter_style == "none":
                comp, props = None, None  # nicho sem capítulos -> beat comum (re-pick)
            if comp == "ChapterTitle" and r.get("secao") not in secoes_com_chapter:
                secoes_com_chapter.add(r.get("secao"))
                n_chapter += 1
                titulo = (_sec_de(r) or {}).get("titulo") or (r.get("dados") or {}).get("title") or ""
                # P1: "(5, 4, 3)" é anotação interna do roteiro — NUNCA vai pra tela
                titulo = re.sub(r"\s*\([\d,\s]+\)\s*$", "", str(titulo)).strip() or str(titulo)
                if chapter_style == "minimal":
                    # linha discreta sobre footage do tema (sem card CHAPTER NN full-screen)
                    b["componente"] = "Ovl02_SubchapterLine"
                    b["props"] = {"text": corte(humanizar(str(titulo)), 60), "kicker": "", "dim": 0.45}
                    b["_min_dur"] = 2.0
                    b["_chapter"] = True  # sweep R-109: capítulo nunca é demovido/removido
                    quotas["Ovl02_SubchapterLine"] = quotas.get("Ovl02_SubchapterLine", 0) + 1
                    tempo_texto += dur * 0.5  # capítulo minimal CONTA no orçamento (meio peso)
                else:
                    b["componente"] = "ChapterTitle"
                    b["props"] = {"title": corte(humanizar(str(titulo)), 40), "chapterNumber": n_chapter, "subtitle": ""}
                    b["_min_dur"] = 3.0
                    b["_chapter"] = True  # 01/08: faltava aqui — só o ramo minimal marcava,
                    # e no cinematic o sweep R-109/R-62 comia os capítulos (ver abaixo)
                    quotas["ChapterTitle"] = quotas.get("ChapterTitle", 0) + 1
            else:
                if comp == "ChapterTitle":
                    comp, props = None, None  # capítulo DUPLICADO na seção -> vira beat comum

                imgs = []
                if isinstance(props, dict):
                    if isinstance(props.get("images"), list):
                        imgs = [x for x in props["images"] if isinstance(x, str) and x != "__IMG__"]
                    else:  # chaves de imagem única (CharacterCard usa characterImage — QA 22/07)
                        for k_img in ("imagem", "characterImage", "image", "articleImage"):
                            if isinstance(props.get(k_img), str) and props[k_img] != "__IMG__":
                                imgs = [props[k_img]]
                                break

                info = REG_INFO.get(comp)
                props_novos = None
                if props and info and comp not in DEPRECATED and dur >= info.get("min_dur", 0):
                    # RE-CONSTRÓI pelo builder ATUAL (props antigos podem carregar texto cru pré-fix)
                    props_novos = rebuild(comp, dados_b, texto_b, imgs)
                # R-26: DADO FORTE nunca fica em texto — mesmo texto VÁLIDO é rejeitado
                # (auditor 22/07: beats de estratégia 'dado' passavam porque o rebuild de
                # texto dava props válidos e o R-26 só rodava no caminho de re-pick)
                if props_novos and _eh_texto(comp) and pb.get("estrategia") == "dado":
                    nums_pre = [n for n in _nums_do_texto(texto_b)
                                if not (n.isdigit() and 1300 <= int(n) <= 2099)]
                    if len(nums_pre) >= 2 or len(_dic5(dados_b).get("values") or []) >= 2:
                        props_novos = None  # cai pro re-pick, onde o R-26 crava o chart

                # R-109 (Piter 23/07): NUNCA 2 animações de texto seguidas — nem antes
                # de um capítulo minimal (Ovl02), cuja posição é fixa (lookahead)
                # R-111: anúncio de produto TAMBÉM nunca fica em texto
                if props_novos and _eh_texto(comp) and (anterior_foi_texto or r["i"] in pre_chapter or anuncio):
                    props_novos = None
                    stats['R109_seq'] = stats.get('R109_seq', 0) + 1
                # R-56 (QA tenis 23/07): imagem ESTÁTICA dentro de props conta reuso como src
                if props_novos and any(x in usados_static for x in _imgs_props(props_novos)):
                    props_novos = None
                    stats["R56_img"] = stats.get("R56_img", 0) + 1

                # R-16 [F1]: texto no HOOK NUNCA — incondicional (QA bikes 25/07: demote
                # falhou e o Ovl14 ficou no hook); o fluxo abaixo acha o substituto
                if props_novos and _eh_texto(comp) and hook:
                    _demote_footage(b, r, relax=True)
                    props_novos = None
                    stats["R16_hook"] = stats.get("R16_hook", 0) + 1
                # texto (mesmo válido) respeita o ORÇAMENTO: estourou -> vira b-roll da seção
                if props_novos and _eh_texto(comp) and \
                        tempo_texto + dur * _peso_texto(comp) > BUDGET_TEXTO and _demote_footage(b, r, relax=True):
                    props_novos = None
                elif props_novos:
                    quotas[comp] = quotas.get(comp, 0) + 1
                    last_use[comp] = r["i"]
                    b["componente"], b["props"] = comp, props_novos
                    usados_static.update(_imgs_props(props_novos))
                    if _eh_texto(comp):
                        tempo_texto += dur * _peso_texto(comp)
                    stats["registry_ok"] += 1
                if not props_novos and "src" not in b:
                    feito = None
                    # R-26 [F1] DADO DE OURO (QA seniors 22/07: 15% vs 34% virou ticker de rodapé):
                    # beat com 2+ números ancorados = chart OBRIGATÓRIO — ganha tempo (stretch 3s)
                    # e ignora cooldown; dado forte NUNCA degrada pra frase.
                    nums_b = [n for n in _nums_do_texto(texto_b) if not (1300 <= int(n.replace(",", "") or 0) <= 2099)] \
                        if texto_b else []
                    if len(nums_b) >= 2 or len(_dic5(dados_b).get("values") or []) >= 2:
                        res26 = escolher("chart", dados_b, texto_b, SEED + r["i"] * 31, quotas,
                                         imgs=imgs, last_use=last_use, beat_i=r["i"],
                                         dur=max(dur, 3.0), cooldown=0)
                        if res26 and hook and _eh_texto(res26[0]):
                            res26 = None  # R-16: nem o dado de ouro põe TEXTO no hook
                        if res26:
                            b["componente"], b["props"] = res26[0], res26[1]
                            b["_min_dur"] = 3.0
                            stats["R26_dado"] = stats.get("R26_dado", 0) + 1
                            feito = res26
                    cadeia_b = CADEIA.get(natureza_do_beat(r), ["texto_full", "texto_overlay"])
                    if hook or anterior_foi_texto or r["i"] in pre_chapter or anuncio:  # R-16/R-109/R-111
                        cadeia_b = [x for x in cadeia_b if x not in ("texto_full", "texto_overlay")] or ["imagem"]
                    if not feito:  # R-26 já pode ter cravado o chart do dado forte
                        for j, n2 in enumerate(cadeia_b):
                            res = escolher(n2, dados_b, texto_b, SEED + r["i"] * 31 + j * 7,
                                           quotas, imgs=imgs, last_use=last_use, beat_i=r["i"], dur=dur)
                            if res and any(x in usados_static for x in _imgs_props(res[1])):
                                continue  # R-56: imagem estática já usada em outro beat
                            if res:
                                feito = res
                                break
                        if feito and hook and _eh_texto(feito[0]):
                            feito = None  # R-16: texto NUNCA no hook (nem via natureza 'chart' — Ovl14)
                        if feito and _eh_texto(feito[0]) and len(nums_b) >= 2:
                            feito = None  # R-26: dado-forte não vira texto NEM pelo repick (27/07)
                        if feito and _eh_texto(feito[0]) and \
                                tempo_texto + dur * _peso_texto(feito[0]) > BUDGET_TEXTO and _demote_footage(b, r, relax=True):
                            feito = None
                        elif feito:
                            b["componente"], b["props"] = feito[0], feito[1]
                            usados_static.update(_imgs_props(feito[1]))
                            if _eh_texto(feito[0]):
                                tempo_texto += dur * _peso_texto(feito[0])
                            stats["repick"] += 1
                    if not feito and "src" not in b:
                        # R-62: estouro de orçamento também relaxa o demote (pool global) —
                        # senão o resgate empilha texto EXATAMENTE quando já há texto demais.
                        # R-111: anúncio de produto NÃO demove pra pool genérico (marca errada!)
                        if not anuncio and (hook or anterior_foi_texto or r["i"] in pre_chapter
                                or tempo_texto > BUDGET_TEXTO) and _demote_footage(b, r, relax=True):
                            pass  # R-16/R-62/R-109: virou b-roll
                        elif not anuncio and (anterior_foi_texto or r["i"] in pre_chapter) and beats_out:
                            # R-109 último caso (pool esgotado): NUNCA emenda outro card de
                            # texto — o beat FUNDE no anterior (1 animação só, mais longa)
                            b["_merge_prev"] = True
                            stats["R109_merge"] = stats.get("R109_merge", 0) + 1
                        elif len([n for n in _nums_do_texto(texto_b)
                                  if not (1300 <= int(n.replace(",", "") or 0) <= 2099)]) >= 2:
                            # R-26: dado-forte NUNCA vira placa de resgate — chart forçado,
                            # b-roll, ou FUNDE no vizinho; texto jamais (auditor 27/07)
                            res26b = escolher("chart", dados_b, texto_b, SEED + r["i"] * 37, quotas,
                                              imgs=imgs, last_use=last_use, beat_i=r["i"],
                                              dur=max(dur, 3.0), cooldown=0)
                            if res26b and not (hook and _eh_texto(res26b[0])):
                                b["componente"], b["props"] = res26b[0], res26b[1]
                                b["_min_dur"] = 3.0
                                stats["R26_dado"] = stats.get("R26_dado", 0) + 1
                            elif _demote_footage(b, r, relax=True):
                                pass
                            else:
                                b["_merge_prev"] = True
                                stats["R26_merge"] = stats.get("R26_merge", 0) + 1
                        else:
                            # resgate: overlay curto HUMANIZADO (nunca transcrição crua, nunca default)
                            tx = frase_de_tela(texto_b, max_p=10) or frase_forcada(texto_b)
                            if not tx:
                                tx = (_sec_de(r) or {}).get("titulo") or "…"
                            ops = [("Ovl06_CenterPunch", 0.55), ("Ovl09_TickerCaption", 0.3),
                                   ("Ovl03_LowerThird", 0.0), ("Ovl04_FootnotePill", 0.0),
                                   ("Ovl05_CornerTag", 0.0), ("Ovl02_SubchapterLine", 0.45)]
                            op = min(ops, key=lambda o: (quotas.get(o[0], 0), (SEED + r["i"] + hash(o[0])) % 97))
                            quotas[op[0]] = quotas.get(op[0], 0) + 1  # resgate também conta quota (variedade)
                            b["componente"], b["props"] = op[0], {"text": corte(tx, 90), "kicker": "", "dim": op[1]}
                            tempo_texto += dur * _peso_texto(op[0])
                            stats["resgate_texto"] += 1
            # G1 (VidRush 24/07): dado único NUNCA em card escuro quando há footage no job
            # pra servir de fundo — card vira overlay equivalente (contrato unificado);
            # se o pass de bg falhar, o último-caso reverte pro card (simetria = nunca preto)
            c_g1 = b.get("componente")
            if c_g1 in SWAP_TO_OVL and any(
                    n.lower().endswith((".mp4", ".webm", ".mov")) for n in pool_poss):
                b["componente"] = SWAP_TO_OVL[c_g1]
                stats["G1_ovl"] = stats.get("G1_ovl", 0) + 1

            # R-96: texto duplicando título de seção (fora da marcação de capítulo) -> b-roll
            # P1/R-96 estendido: título de seção em QUALQUER prop visível (não só text)
            tx96 = " | ".join(str((b.get("props") or {}).get(k) or "")
                              for k in ("text", "title", "label", "kicker")).strip().lower()
            if tx96 and any(t and t in tx96 for t in titulos_secao) and b.get("componente") != "Ovl02_SubchapterLine":
                if _demote_footage(b, r, relax=True):
                    stats["R96_dup"] = stats.get("R96_dup", 0) + 1
            b["props"] = {k: _rw(v) for k, v in (b.get("props") or {}).items()}

        # R-27 [F1] (QA Piter 22/07, ref. VidRush): ANO falado -> overlay de DATA gigante
        # sobre footage NÍTIDO. Com CARRY: ano detectado num beat sem src (ex.: o hook virou
        # animação) aplica no PRÓXIMO beat de footage — ainda dentro da mesma frase narrada.
        tb27 = (plano_por_i.get(r["i"], {}) or {}).get("texto") or ""
        anos27 = [n for n in _nums_do_texto(tb27[:45]) if n.isdigit() and 1300 <= int(n) <= 2099]
        if b.get("src") and b["tipo"] in ("footage_video", "footage_imagem", "stock"):
            alvo27 = anos27 or ([ano_pendente] if ano_pendente else [])
            if alvo27 and alvo27[0] not in anos_usados:
                anos_usados.add(alvo27[0])
                ano_pendente = None
                b["tipo"] = "animacao"
                b["componente"] = "Ovl10_NumberBadge"
                b["props"] = {"text": alvo27[0], "kicker": "", "dim": 0.2}
                b["bg"], b["bg_nitido"] = b.pop("src"), True
                stats["R27_ano"] = stats.get("R27_ano", 0) + 1
        elif anos27 and anos27[0] not in anos_usados:
            ano_pendente = anos27[0]
        if b.pop("_merge_prev", False) and beats_out:
            beats_out[-1]["t_fim"] = max(beats_out[-1]["t_fim"], b["t_fim"])
            # anterior_foi_texto NÃO muda: o card anterior é o que segue na tela
        else:
            # ano sobre footage NÍTIDO (R-27) lê como footage, não como card de texto
            anterior_foi_texto = b["tipo"] == "animacao" and _eh_texto(b.get("componente") or "") \
                and not b.get("bg_nitido")
            beats_out.append(b)

    # ---- duração mínima sem buraco: ajusta sobreposição e SÓ ENTÃO estica o card
    # (senão o push encolhe o capítulo de volta — bug do v1: Chapter de <1s) ----
    beats_out.sort(key=lambda x: (x["t_ini"], x["i"]))
    ajustados = []
    for b in beats_out:
        if ajustados and b["t_ini"] < ajustados[-1]["t_fim"]:
            b["t_ini"] = ajustados[-1]["t_fim"]
        md = b.pop("_min_dur", None)
        if md and (b["t_fim"] - b["t_ini"]) < md:
            b["t_fim"] = round(b["t_ini"] + md, 2)  # card manda: rouba do vizinho seguinte
        if b["t_fim"] - b["t_ini"] >= 0.5:
            ajustados.append(b)
        elif ajustados and b["t_fim"] > ajustados[-1]["t_fim"]:
            ajustados[-1]["t_fim"] = b["t_fim"]  # engolido: vizinho cobre (sem buraco preto)
    beats_out = ajustados
    print(f"registry-pass [R-81]: ok={stats['registry_ok']} repick={stats['repick']} resgate[R-62]={stats['resgate_texto']} "
          f"demote[R-56/62]={stats['demote_footage']} hook[R-15/16]={stats.get('R15_hook', 0) + stats.get('R16_hook', 0)} "
          f"| chapters={n_chapter} | texto={tempo_texto:.0f}s/{BUDGET_TEXTO:.0f}s [R-62]")

    # ---- OVERLAYS ganham FUNDO do tema (imagem da mesma seção, blur+dark no Montagem) ----
    OVERLAYS = {"NumberCountOverlay", "DisplayText", "OneWordCallout", "BulletPointOverlay",
                "SingleSentenceTextSlide", "TextReveal",
                # almoxarifado 2.0: overlays de texto + gráficos overlay (fundo do tema atrás)
                "Ovl01_ChapterBig", "Ovl02_SubchapterLine", "Ovl03_LowerThird", "Ovl04_FootnotePill",
                "Ovl05_CornerTag", "Ovl06_CenterPunch", "Ovl07_QuoteAttribution", "Ovl08_SideNote",
                "Ovl09_TickerCaption", "Ovl10_NumberBadge",
                "Ovl11_SpecBadge", "Ovl12_GiantStat", "Ovl13_PriceTag", "Ovl14_PillVerdict",
                "Lst02_SidePanelList",
                "Graf14_OvlCounterPunch", "Graf15_OvlStatCorner", "Graf16_OvlProgressBar"}
    por_sec = {}  # chave = ASSUNTO (VidRush 24/07: bg também respeita continuidade de entidade)
    bg_dono = {}  # src -> assunto do dono
    for b in beats_out:
        # R-56: imagem estática é 1 USO TOTAL — nunca vira bg de overlay (QA 23/07:
        # foto de produto do beat 19 reapareceu borrada atrás do overlay do beat 55)
        if b.get("src") and b["tipo"] in ("stock", "footage_video", "footage_imagem") \
                and str(b["src"]).lower().endswith((".mp4", ".webm", ".mov")):
            chave_b = assunto_por_i.get(b["i"]) or f"sec{b['secao']}"
            por_sec.setdefault(chave_b, []).append(b["src"])
            bg_dono[b["src"]] = assunto_por_i.get(b["i"])
    # BANCO DE NICHO também serve de bg (genérico, sem dono de assunto)
    for r0 in resolvido:
        if r0.get("secao") == 900 and str(r0.get("arquivo") or "").lower().endswith(".mp4"):
            por_sec.setdefault("banco", []).append(f"jobs/{a.nome}/assets/{Path(r0['arquivo']).name}")
    # bg dos overlays com o MESMO guard R-56 do demote (auditor 22/07: rot cega repetia
    # o mesmo fundo em beats colados — 15 violações que nenhuma decupagem tinha visto)
    bg_uso, bg_poss = {}, {}
    for b in beats_out:
        # seed com src E bg (27/07: o Ovl10 do R-27 já carrega bg antes do bg pass —
        # sem contá-lo, outro overlay pegava o mesmo arquivo e formava trio de 3 usos)
        for cand0 in filter(None, [b.get("src"), b.get("bg")]):
            bg_poss.setdefault(cand0, []).append(b["i"])
            bg_uso[cand0] = bg_uso.get(cand0, 0) + 1
    for b in beats_out:
        if b["tipo"] == "animacao" and b.get("componente") in OVERLAYS and not b.get("bg"):
            # fase 1: MESMO assunto com gap 6; fase 2: pool global com gap 3 (preqa 23/07:
            # overlay de CANTO sem bg = 90% do frame preto — pior que reusar fundo)
            meu_ass_bg = assunto_por_i.get(b["i"]) or f"sec{b['secao']}"
            # fase 0 = BANCO DE NICHO (27/07 "MUITO repetido"): fundo vem de material
            # que NUNCA apareceu nítido — só cai no reuso se o banco secar
            for pool_cand, gap_bg in [(por_sec.get("banco") or [], 1),
                                      (por_sec.get(meu_ass_bg) or [], 6),
                                      ([s for v in por_sec.values() for s in v], 3)]:
                if b.get("bg"):
                    break
                for cand in sorted(set(pool_cand), key=lambda s: (bg_uso.get(s, 0),
                                                                  -min([abs(p - b["i"]) for p in bg_poss.get(s, [])] or [99]))):
                    if bg_dono.get(cand) and bg_dono[cand] != assunto_por_i.get(b["i"]):
                        continue  # bg de OUTRO produto nomeado — nunca (nem borrado)
                    poss = bg_poss.get(cand, [])
                    # cap = 2 POSIÇÕES TOTAIS (src + bgs) — 27/07: dois overlays pegavam
                    # o mesmo bg e formavam trio [0, 23, dono] que o auditor derrubava
                    if bg_uso.get(cand, 0) >= 2 or len(poss) >= 2 \
                            or (poss and min(abs(p - b["i"]) for p in poss) < gap_bg):
                        continue
                    b["bg"] = cand
                    bg_uso[cand] = bg_uso.get(cand, 0) + 1
                    bg_poss.setdefault(cand, []).append(b["i"])
                    # anotação de DADO (VidRush): footage por trás fica NÍTIDO, não borrado
                    if (b.get("componente") or "") in ANOTA_OVL:
                        b["bg_nitido"] = True
                    break
            if not b.get("bg"):
                # último caso: placa sem fundo NUNCA — vira card FULL equivalente (fundo próprio)
                _SWAP_GRAF = {"Graf14_OvlCounterPunch": "Graf01_CounterGlow",
                              "Graf15_OvlStatCorner": "Graf10_BigStatCard",
                              "Graf16_OvlProgressBar": "Graf03_DonutPercent"}
                c_atual = b.get("componente") or ""
                tx_swap = str((b.get("props") or {}).get("text") or "").strip()
                if c_atual in _SWAP_GRAF:
                    b["componente"] = _SWAP_GRAF[c_atual]  # contrato unificado: mesmos props
                    b["_full_ok"] = True  # fallback LEGÍTIMO (sem bg) — auditor G1 não flagra
                    stats["bg_swap_full"] = stats.get("bg_swap_full", 0) + 1
                elif c_atual in ANOTA_OVL:
                    # anotação sem footage: vira BigStatCard com o mesmo número
                    num_sw = re.sub(r"[^\d.]", "", tx_swap)
                    if num_sw:
                        b["componente"] = "Graf10_BigStatCard"
                        b["props"] = {"title": corte(str((b.get("props") or {}).get("kicker") or ""), 44),
                                      "values": [float(num_sw)], "suffix": ""}
                        b["_full_ok"] = True
                        stats["bg_swap_full"] = stats.get("bg_swap_full", 0) + 1
                elif tx_swap:
                    b["componente"] = "Texto05_BoxedKicker" if (b["i"] % 2) else "Texto04_EditorialSerif"
                    b["props"] = {"text": corte(tx_swap, 90), "kicker": ""}
                    stats["bg_swap_full"] = stats.get("bg_swap_full", 0) + 1

    # bookkeeping UNIFICADO (bg conta como aparição) — ANTES de rebalance/duo/sweep,
    # senão o demote reusa arquivo que já é fundo de overlay (tenis2: b073 em [0,60,73])
    for b in beats_out:
        if isinstance(b.get("bg"), str) and b["bg"]:
            n_arq = Path(b["bg"]).name
            pool_uso[n_arq] = pool_uso.get(n_arq, 0) + 1
            pool_poss.setdefault(n_arq, []).append(b["i"])

    # ---- R-106 [F1] (Piter 22/07): DINAMISMO DUO — min 2, máx 3 animações de par
    # (2 imagens OU 2 vídeos) por vídeo. Sorteio deu menos? Injeta duo de VÍDEO com
    # pares do próprio job (respeitando cap/gap R-56 via bg_uso/bg_poss dos overlays).
    _DUOS_IMG = ("Img04_", "Img05_", "Img15_", "Img17_")
    _DUOS_VID = ("Duo01_SplitVideos", "Duo02_SequentialPush", "Duo03_PipReveal")
    n_duos = sum(1 for b in beats_out if (b.get("componente") or "").startswith(_DUOS_IMG + _DUOS_VID))
    pos_duos = [b["i"] for b in beats_out if (b.get("componente") or "").startswith(_DUOS_IMG + _DUOS_VID)]
    if n_duos < 2:
        cand_duo = [b for b in beats_out
                    if b.get("src") and b["tipo"] in ("stock", "footage_video")
                    and str(b["src"]).lower().endswith(".mp4")
                    and (b["t_fim"] - b["t_ini"]) >= 4.0 and b["t_ini"] >= 15.0
                    and not b.get("watermark")]
        vids_pool = [b2["src"] for b2 in beats_out
                     if b2.get("src") and str(b2["src"]).lower().endswith(".mp4") and not b2.get("watermark")]
        rng_duo = 0
        for b in cand_duo:
            if n_duos >= 2:
                break
            # duos ESPALHADOS: nunca a <10 beats de outro duo (QA mesa: caíram adjacentes 4/5)
            if pos_duos and min(abs(p - b["i"]) for p in pos_duos) < 10:
                continue
            # par: vídeo de OUTRO beat, longe deste (gap>=6 de qualquer aparição), cap 2 usos
            par = None
            for cand in vids_pool:
                if cand == b["src"]:
                    continue
                poss = bg_poss.get(cand, [])
                if bg_uso.get(cand, 0) >= 2 or (poss and min(abs(p - b["i"]) for p in poss) < 6):
                    continue
                par = cand
                break
            if not par:
                continue
            comp_duo = _DUOS_VID[rng_duo % len(_DUOS_VID)]
            rng_duo += 1
            bg_uso[par] = bg_uso.get(par, 0) + 1
            bg_poss.setdefault(par, []).append(b["i"])
            b["tipo"] = "animacao"
            b["componente"] = comp_duo
            b["props"] = {"videos": [b.pop("src"), par]}
            n_duos += 1
            pos_duos.append(b["i"])
            stats["R106_duo"] = stats.get("R106_duo", 0) + 1

    # R-106: MÁXIMO 3 duos — excedente vira single (auditor 27/07: 4 duos = ruído)
    _todos_duos = [b for b in beats_out if (b.get("componente") or "").startswith(_DUOS_IMG + _DUOS_VID)]
    for b in _todos_duos[3:]:
        c_d = b.get("componente") or ""
        if c_d.startswith(_DUOS_IMG):
            imgs_d = (b.get("props") or {}).get("images") or []
            if imgs_d:
                b["componente"], b["props"] = "Img01_KenBurnsCine", {"images": imgs_d[:1]}
        else:
            vids_d = (b.get("props") or {}).get("videos") or []
            if vids_d:
                b["tipo"], b["src"] = "stock", vids_d[0]
                b.pop("componente", None), b.pop("props", None)
        stats["R106_trim"] = stats.get("R106_trim", 0) + 1

    # ---- bookkeeping pré-sweep: pares de DUO contam como aparição (bg já registrado) ----
    for b in beats_out:
        for u in ((b.get("props") or {}).get("videos") or []):
            if isinstance(u, str) and u:
                n_arq = Path(u).name
                pool_uso[n_arq] = pool_uso.get(n_arq, 0) + 1
                pool_poss.setdefault(n_arq, []).append(b["i"])

    # ---- SWEEP FINAL R-109 (timeline DEFINITIVA): o tracker do loop vê a ordem da
    # lista, mas o ajuste de sobreposição pode ENGOLIR o beat separador (tenis 23/07:
    # demote do 46 tinha overlap total com o capítulo 45 e sumiu — capítulo colou no
    # Texto05 do 47). Aqui todos os passes já rodaram: a invariante é garantida. ----
    def _txt109(b):
        return b["tipo"] == "animacao" and _eh_texto(b.get("componente") or "") \
            and not b.get("bg_nitido")
    k = 1
    while k < len(beats_out):
        a2, b2 = beats_out[k - 1], beats_out[k]
        if _txt109(a2) and _txt109(b2):
            # capítulo é intocável — o par flexível é o outro
            alvo = a2 if (b2.get("_chapter") and not a2.get("_chapter")) else b2
            outro = b2 if alvo is a2 else a2
            if _demote_footage(alvo, alvo, relax=True):
                alvo.pop("bg", None), alvo.pop("bg_nitido", None)
                stats["R109_sweep"] = stats.get("R109_sweep", 0) + 1
            else:
                outro["t_ini"] = min(outro["t_ini"], alvo["t_ini"])
                outro["t_fim"] = max(outro["t_fim"], alvo["t_fim"])
                beats_out.remove(alvo)
                stats["R109_sweep"] = stats.get("R109_sweep", 0) + 1
                continue  # reavalia o novo par na mesma posição
        k += 1
    for b in beats_out:
        b.pop("_chapter", None)

    # ---- REBALANCE FINAL DE ORÇAMENTO [R-62] (PÓS-sweep: merges esticam texto) —
    # reconta na régua do auditor e demove os últimos textos até caber ----
    def _texto_total():
        tot = 0.0
        for b2 in beats_out:
            c2 = b2.get("componente") or ""
            if b2["tipo"] != "animacao" or not _eh_texto(c2) or b2.get("bg_nitido"):
                continue
            tot += (b2["t_fim"] - b2["t_ini"]) * (0.5 if c2.startswith(("Ovl02", "Ovl03", "Ovl04", "Ovl05", "Ovl09")) else 1.0)
        return tot

    teto62 = _tb * dur_total * 1.10  # folga menor que a do auditor (1.15) = margem de segurança
    # 01/08 (QA cobras): "capítulo intocável" só valia pro estilo MINIMAL (Ovl02). No
    # CINEMATIC o capítulo é ChapterTitle — entrava na lista de sacrifício e os 5 títulos
    # do "Top 5" foram os PRIMEIROS a morrer (texto 70s/74s, demote=23, chapters=5 criados
    # e 0 na tela). O capítulo é ESTRUTURA, não enfeite: quem cede é o resto do texto.
    for b in sorted([x for x in beats_out if x["tipo"] == "animacao" and _eh_texto(x.get("componente") or "")
                     and "Ovl02" not in (x.get("componente") or "")
                     and (x.get("componente") or "") != "ChapterTitle"],
                    key=lambda x: -x["t_ini"]):  # sacrifica do FIM pro começo; capítulo intocável
        if _texto_total() <= teto62:
            break
        if _demote_footage(b, b, relax=True):
            b.pop("bg", None), b.pop("bg_nitido", None)
            stats["R62_final"] = stats.get("R62_final", 0) + 1
        else:
            # pool seco: FUNDE no vizinho de footage — o footage ganha o tempo do texto
            # (se passar de 6s, o split logo abaixo divide em 2 planos — VidRush puro)
            idx62 = beats_out.index(b)
            if idx62 > 0 and beats_out[idx62 - 1].get("src"):
                beats_out[idx62 - 1]["t_fim"] = max(beats_out[idx62 - 1]["t_fim"], b["t_fim"])
                beats_out.remove(b)
                stats["R62_merge"] = stats.get("R62_merge", 0) + 1
            elif idx62 + 1 < len(beats_out) and beats_out[idx62 + 1].get("src"):
                beats_out[idx62 + 1]["t_ini"] = min(beats_out[idx62 + 1]["t_ini"], b["t_ini"])
                beats_out.remove(b)
                stats["R62_merge"] = stats.get("R62_merge", 0) + 1

    # ---- R-72b: REPETIÇÃO VIRA OVERLAY (02/08, decisão do Piter) ----
    # Antes: clipe repetido era trocado por outro footage — caro, e em nicho local
    # simplesmente não há outro. Agora o repetido FICA, mas a 2ª aparição em diante
    # ganha um overlay por cima: a tela muda, o olho não registra como repetição, e
    # não se gasta uma busca. É o mesmo padrão do R-27 (ano vira NumberBadge sobre o
    # próprio clipe), aplicado ao problema de reuso.
    # ⚠️ ORDEM IMPORTA — roda DEPOIS do rebalance R-62, de propósito (produção em
    # série, 02/08). Antes ele rodava ANTES: inflava o orçamento de texto (98s num
    # teto de 89s) e o corte automático desfazia de forma imprevisível, podendo
    # derrubar TEXTO INFORMATIVO bom para caber overlay de disfarce. Aqui ele só
    # consome a FOLGA que sobrou — nunca causa estouro, por construção, e não
    # precisa de `texto_budget` ajustado a mão por job (parâmetro por job não
    # serializa: em 12 vídeos/dia ninguém decide isso, e vira lixo acumulado).
    # Vídeo com pouco texto quebra muitas repetições; vídeo carregado não quebra
    # nenhuma — e nos dois casos nada de bom é cortado.
    _OVL_ROT = ["Ovl04_FootnotePill", "Ovl05_CornerTag", "Ovl09_TickerCaption",
                "Ovl03_LowerThird"]
    _visto_src = {}
    _n72b = 0
    _folga72 = teto62 - _texto_total()
    for b in beats_out:
        s = b.get("src")
        if not s or b.get("componente"):
            continue
        _visto_src[s] = _visto_src.get(s, 0) + 1
        if _visto_src[s] < 2:
            continue                      # 1ª aparição vai limpa
        _custo = (b["t_fim"] - b["t_ini"]) * 0.5   # overlay conta meio peso (R-62)
        if _custo > _folga72:
            continue                      # sem folga: repete limpo, que é o estado antigo
        tx72 = frase_de_tela(_corr((plano_por_i.get(b["i"], {}) or {}).get("texto") or ""))
        if not tx72 or len(tx72) < 8:
            continue
        _folga72 -= _custo
        comp72 = _OVL_ROT[(_visto_src[s] - 2) % len(_OVL_ROT)]
        b["tipo"] = "animacao"
        b["componente"] = comp72
        b["props"] = {"text": corte(humanizar(tx72), 60), "kicker": "",
                      "dim": _OVL_DIM_M.get(comp72, 0.0)}
        b["bg"], b["bg_nitido"] = b.pop("src"), True
        _n72b += 1
    # repetição é SINTOMA de falta de material: mede e reporta sempre, mesmo quando
    # o overlay disfarça. Sem isso, "ampliar as fontes" vira decisão por impressão.
    _rep_total = sum(v - 1 for v in _visto_src.values() if v > 1)
    if _rep_total or _n72b:
        print(f"R-72b: {_rep_total} reuso(s) de clipe | {_n72b} disfarçado(s) com overlay "
              f"| {_rep_total - _n72b} sem folga de orçamento")
        stats["R72b_overlay"] = _n72b
        stats["R72b_reuso"] = _rep_total

    # ---- SPLIT DE PLANO (VidRush 24/07): footage >6s vira 2 planos (deles: ~4s/plano) —
    # 2º segmento do MESMO asset com offset e tratamento distinto (zoom/tint/p&b) ----
    def _dur_src(nome_arq):
        try:
            p = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                "-of", "csv=p=0", str(dest / "assets" / nome_arq)],
                               capture_output=True, text=True, timeout=20)
            return float((p.stdout or "0").strip() or 0)
        except Exception:
            return 0.0

    _cache_dur, novos = {}, []
    for b in beats_out:
        d_b = b["t_fim"] - b["t_ini"]
        s_b = str(b.get("src") or "")
        # ESTILO v2 [§5.2]: HOOK = 2 minutos hipnóticos — planos >4s são divididos
        lim_split = 4.0 if (_SC.get("estilo") in ("v2", "v5") and b["t_ini"] < 120.0) else 6.0
        if b["tipo"] in ("stock", "footage_video") and s_b.lower().endswith((".mp4", ".webm", ".mov")) \
                and d_b > lim_split:
            nome_arq = Path(s_b).name
            if nome_arq not in _cache_dur:
                _cache_dur[nome_arq] = _dur_src(nome_arq)
            sd = _cache_dur[nome_arq]
            meio = round(b["t_ini"] + d_b / 2, 2)
            seg2_dur = b["t_fim"] - meio
            off = round(max(0.0, min(d_b / 2, sd - seg2_dur - 0.2)), 2) if sd > 2 else 0.0
            seg2 = {**b, "i": b["i"] + 900, "t_ini": meio, "off_s": off if off >= 1.0 else 0.0,
                    "trato": ("zoom", "tint", "pb")[b["i"] % 3], "_seg": 2}
            novos += [{**b, "t_fim": meio}, seg2]
            stats["split"] = stats.get("split", 0) + 1
        else:
            novos.append(b)
    beats_out = novos

    # ---- ESTILO v2 [REGRAS_VDM §5.3]: CAMADA DE ÁUDIO — trilha por momento da
    # seção + whoosh nos cortes de seção + stinger nos anúncios + typewriter ----
    audio_plan = None
    if _SC.get("estilo") in ("v2", "v5"):
        ACERVO = Path(r"F:/Canal Dark/Aplicativo de Edição/banco-videos/_acervo_equipe")
        (dest / "audio_assets").mkdir(exist_ok=True)

        def _copia_audio(rel_acervo, sub):
            src_a = ACERVO / sub / rel_acervo
            nome_a = rel_acervo.replace("/", "_")
            dst_a = dest / "audio_assets" / nome_a
            if src_a.exists() and not dst_a.exists():
                shutil.copy2(src_a, dst_a)
            return f"jobs/{a.nome}/audio_assets/{nome_a}" if src_a.exists() else None

        audio_plan = {"trilhas": [], "sfx": []}
        try:
            tr_cat = json.loads((ACERVO / "Trilhas sonoras/documentario/catalogo_trilhas.json")
                                .read_text(encoding="utf-8"))
            n_sec = len(secoes)
            usadas_tr = set()
            for idx, s in enumerate(secoes):
                mo = "hook" if idx == 0 else "revelacao" if idx == n_sec - 1 else \
                    ("build", "frio", "epico", "nostalgia")[(idx - 1) % 4]
                ops = [f for f in tr_cat.get(mo, []) if f not in usadas_tr] or tr_cat.get(mo, [])
                if not ops:
                    continue
                arq_t = ops[(SEED + s["i"] * 13) % len(ops)]
                usadas_tr.add(arq_t)
                rel = _copia_audio(arq_t, "Trilhas sonoras/documentario")
                if rel:
                    audio_plan["trilhas"].append({"arquivo": rel, "t_ini": s["t_ini"],
                                                  "t_fim": s["t_fim"], "vol": 0.08})
            sfx_man = json.loads((ACERVO / "sfx/manifesto.json").read_text(encoding="utf-8"))["sfx"]
            por_fam = {}
            for x in sfx_man:
                por_fam.setdefault(x["familia"], []).append(x)
            usados_sfx = set()  # 28/07: anti-repetição TAMBÉM nos sfx (stinger dark 2x no estoico)

            def _add_sfx(fam, t, vol, kseed=0, contem="", dur_max=None):
                ops = [x for x in por_fam.get(fam, []) if contem in x["arquivo"]]
                if not ops or t < 0:
                    return
                livres = [x for x in ops if x["arquivo"] not in usados_sfx] or ops
                x = livres[(SEED + kseed) % len(livres)]
                usados_sfx.add(x["arquivo"])
                rel = _copia_audio(x["arquivo"], "sfx")
                if rel:
                    d_s = float(x.get("duracao_s") or 1.5)
                    # COERÊNCIA (Piter 27/07): SFX morre JUNTO com a animação — nunca vaza
                    if dur_max:
                        d_s = min(d_s, dur_max)
                    audio_plan["sfx"].append({"arquivo": rel, "t": round(t, 2), "vol": vol,
                                              "dur": round(d_s, 2)})

            # 28/07: whoosh genérico do corte saiu daqui — as TRANSITIONS do acervo (bloco FX
            # abaixo) trazem o próprio sfx_par; whoosh vira fallback dentro do FX
            for b in beats_out:
                c2 = b.get("componente") or ""
                if c2 == "Img21_ProductAnnounce":
                    _add_sfx("stinger", b["t_ini"], 0.28, kseed=b["i"])
                elif c2.startswith("Texto01"):
                    # typewriter digita ~55% do beat — o SFX acompanha e PARA com a animação
                    _add_sfx("foley", b["t_ini"] + 0.1, 0.20, kseed=b["i"], contem="typewriter",
                             dur_max=max(0.8, (b["t_fim"] - b["t_ini"]) * 0.55))
            print(f"audio_plan [v2]: {len(audio_plan['trilhas'])} trilhas + {len(audio_plan['sfx'])} sfx")
        except Exception as e_au:
            print(f"audio_plan FALHOU ({e_au}) — v2 sem áudio extra")
            audio_plan = None

    # ---- ESTILO v2.1 (28/07): OVERLAYS de textura + TRANSITIONS do acervo da equipe ----
    # Overlays: hook contínuo (janelas rotativas) + abertura de cada seção. Transitions:
    # 1 por corte de seção, pool = receitas implementadas no Remotion + inks (veil vídeo),
    # cada uma com o SEU sfx_par. Anti-repetição ABSOLUTA (usados até esgotar) [REGRAS_VDM §4].
    fx_overlays, fx_trans = [], []
    if _SC.get("estilo") in ("v2", "v5"):
        try:
            ACERVO_FX = Path(r"F:/Canal Dark/Aplicativo de Edição/banco-videos/_acervo_equipe")
            (dest / "fx_assets").mkdir(exist_ok=True)

            def _copia_fx(rel_acervo, sub):
                src_f = ACERVO_FX / sub / rel_acervo
                nome_f = rel_acervo.replace("/", "_")
                dst_f = dest / "fx_assets" / nome_f
                if src_f.exists() and not dst_f.exists():
                    shutil.copy2(src_f, dst_f)
                return f"jobs/{a.nome}/fx_assets/{nome_f}" if src_f.exists() else None

            # --- overlays de textura ---
            ov_man = json.loads((ACERVO_FX / "overlays/manifesto.json").read_text(encoding="utf-8"))["overlays"]
            fams_ov = _SC.get("overlay_familias") or ["film", "dust", "particles", "lightleak",
                                                      "bokeh", "fog", "smoke", "rays", "embers",
                                                      "flare", "fireflies"]
            pool_ov = [o for o in ov_man if o["categoria"] in fams_ov and o.get("arquivo")
                       and o.get("modo") in ("screen", "multiply") and o.get("duracao_s")]
            usados_ov = set()

            def _pega_ov(kseed):
                if not pool_ov:
                    return None
                livres = [o for o in pool_ov if o["id"] not in usados_ov] or pool_ov
                o = livres[(SEED + kseed) % len(livres)]
                usados_ov.add(o["id"])
                return o

            def _janela_ov(t0, t1, op, kseed):
                o = _pega_ov(kseed)
                if not o:
                    return
                rel = _copia_fx(o["arquivo"], "overlays")
                if rel:
                    fx_overlays.append({"arquivo": rel, "t_ini": round(t0, 2), "t_fim": round(t1, 2),
                                        "modo": o["modo"], "op": op, "dur_s": o["duracao_s"]})

            if secoes:
                s0 = secoes[0]  # HOOK [§5.2]: textura contínua, trocando a cada ~26s
                t = s0["t_ini"]
                k = 0
                while t < s0["t_fim"] - 4:
                    fim_j = min(t + 26.0, s0["t_fim"])
                    _janela_ov(t, fim_j, 0.26, k * 13)
                    t = fim_j
                    k += 1
                for idx, s in enumerate(secoes[1:], start=1):  # abertura de seção: 6s de textura
                    if s["t_fim"] - s["t_ini"] >= 8:
                        _janela_ov(s["t_ini"], s["t_ini"] + 6.0, 0.30, 100 + idx * 17)

            # --- transitions nos cortes de seção ---
            tr_man = json.loads((ACERVO_FX / "transitions/manifesto.json").read_text(encoding="utf-8"))["transitions"]
            RECEITAS_OK = {"zoom_whammy": "zoom_whammy", "deslizar_esquerda": "deslizar_esquerda",
                           "deslizar_baixo": "deslizar_baixo", "tremor": "tremor",
                           "sacudir_ii": "sacudir", "gire_cw_ii": "gire_cw",
                           "flash_branco": "flash_branco", "flash_crescente": "flash_crescente",
                           "esmaecer_preto": "esmaecer_preto", "desvanecer_difuso": "blur_dip",
                           "travessao_blur": "blur_dip", "suave": "suave"}
            TRANSFORMS = {"zoom_whammy", "deslizar_esquerda", "deslizar_baixo", "tremor",
                          "sacudir", "gire_cw"}
            fams_tr = _SC.get("trans_familias") or ["ink", "receita"]  # glitchburst/vhs só por opt-in
            pool_tr = []
            for tx in tr_man:
                if tx["categoria"] == "ink" and "ink" in fams_tr and tx.get("arquivo"):
                    pool_tr.append({"id": tx["id"], "tipo": "veil_video", "arquivo": tx["arquivo"],
                                    "pico_s": tx.get("pico_s") or 1.0, "dur_s": tx.get("duracao_s") or 4.0,
                                    "sfx": tx.get("sfx_par")})
                elif tx["categoria"] == "receita" and "receita" in fams_tr \
                        and tx.get("descritor") in RECEITAS_OK:
                    pool_tr.append({"id": tx["id"], "tipo": RECEITAS_OK[tx["descritor"]],
                                    "sfx": tx.get("sfx_par")})
            usados_tr_fx = set()
            dur_sfx = {x["arquivo"]: float(x.get("duracao_s") or 1.5) for x in
                       (json.loads((ACERVO_FX / "sfx/manifesto.json").read_text(encoding="utf-8"))["sfx"])}
            for idx, s in enumerate(secoes[1:], start=1):
                if not pool_tr:
                    break
                livres = [x for x in pool_tr if x["id"] not in usados_tr_fx] or pool_tr
                tx = livres[(SEED + idx * 11) % len(livres)]
                usados_tr_fx.add(tx["id"])
                t_corte = s["t_ini"]  # nome != corte() — sombrear a função quebrou o cold-open (28/07)
                ent = {"t": round(t_corte, 2), "tipo": tx["tipo"]}
                if tx["tipo"] == "veil_video":
                    rel_v = _copia_fx(tx["arquivo"], "transitions")
                    if not rel_v:
                        continue
                    ent["arquivo"] = rel_v
                    ent["pico_s"] = tx["pico_s"]
                    ent["dur_s"] = tx["dur_s"]
                elif tx["tipo"] in TRANSFORMS:
                    # transform entra no PRIMEIRO beat da seção (wrapper no Remotion)
                    alvo = min((b for b in beats_out if b["t_ini"] >= t_corte - 0.1),
                               key=lambda b: b["t_ini"], default=None)
                    if alvo is not None:
                        alvo["trans_in"] = {"tipo": tx["tipo"]}
                fx_trans.append(ent)
                # sfx pareado da transição (fallback: whoosh genérico da rotação)
                if audio_plan is not None:
                    if tx.get("sfx"):
                        rel_s = _copia_audio(tx["sfx"].split("sfx/", 1)[-1], "sfx")
                        if rel_s:
                            d_par = min(dur_sfx.get(tx["sfx"].split("sfx/", 1)[-1], 1.5),
                                        4.0 if tx["tipo"] == "veil_video" else 2.5)
                            lead = 1.2 if tx["tipo"] == "veil_video" else 0.35
                            audio_plan["sfx"].append({"arquivo": rel_s, "t": round(t_corte - lead, 2),
                                                      "vol": 0.30, "dur": round(d_par, 2)})
                    else:
                        _add_sfx("whoosh", t_corte - 0.45, 0.30, kseed=idx * 7)
            print(f"fx [v2.1]: {len(fx_overlays)} overlays de textura + {len(fx_trans)} transitions "
                  f"({len(usados_ov)} arquivos ov distintos, {len(usados_tr_fx)} trans distintas)")
        except Exception as e_fx:
            print(f"fx FALHOU ({e_fx}) — v2 sem overlays/transitions; whoosh genérico nos cortes")
            fx_overlays, fx_trans = [], []
            if audio_plan is not None:
                for idx, s in enumerate(secoes[1:], start=1):
                    _add_sfx("whoosh", s["t_ini"] - 0.45, 0.30, kseed=idx * 7)

    # ---- v5 (31/07 bis): GAP de TIMELINE nunca vira tela preta ----
    # O montador DESCARTA beat sem asset -> sobra buraco de TEMPO (25 gaps / 298s no
    # 1º vídeo de cobras = 62% de tela preta). Aqui os gaps viram beats novos servidos
    # pelo BANCO DE NICHO, em rodízio e sem repetir o vizinho.
    # pool = banco de nicho (uso 0) + TODO mp4 já resolvido (uso 1) — com 62 gaps e só
    # 25 clipes de banco o R-56 (3+ usos) estourava; o pool maior distribui
    _bnc = [r["arquivo"] for r in resolvido
            if r.get("secao") == 900 and str(r.get("arquivo") or "").lower().endswith(".mp4")
            and Path(r.get("arquivo") or "").exists()]
    # usos REAIS na timeline (src E bg; split/bg fazem o mesmo asset aparecer 2x).
    # Vale pro BANCO também — clipe de banco usado como bg de overlay (R-27) já tem
    # uso e zerá-lo estourava o R-56 no preenchimento.
    _na_timeline = {}
    for b in beats_out:
        for ch in ("src", "bg"):
            v = str(b.get(ch) or "")
            if v.lower().endswith(".mp4"):
                _na_timeline[Path(v).name] = _na_timeline.get(Path(v).name, 0) + 1
    for r in resolvido:  # amplia o pool com os mp4 já resolvidos (não-banco)
        arq = str(r.get("arquivo") or "")
        if r.get("secao") != 900 and arq.lower().endswith(".mp4") and Path(arq).exists():
            _bnc.append(arq)
    _usos_g = {a: _na_timeline.get(Path(a).name, 0) for a in _bnc}
    if _bnc and beats_out:
        beats_ord = sorted(beats_out, key=lambda x: x["t_ini"])
        dur_alvo = max(b["t_fim"] for b in beats_ord)
        novos_gap, ant_t, ult_a, k_gap = [], 0.0, None, 0
        limites = [(b["t_ini"], b["t_fim"], b.get("secao", 0)) for b in beats_ord] + \
                  [(dur_alvo, dur_alvo, beats_ord[-1].get("secao", 0))]
        for t_i, t_f, sec_g in limites:
            if t_i - ant_t > 0.4:                    # gap real
                ini_g = ant_t
                while ini_g < t_i - 0.2:             # fatia em pedaços de <= 6s
                    fim_g = min(ini_g + 6.0, t_i)
                    # sempre o MENOS usado (desempate determinístico) e nunca o vizinho
                    ops = sorted((a for a in _bnc if a != ult_a and _usos_g.get(a, 0) < 2),
                                 key=lambda x: (_usos_g.get(x, 0), x))
                    if not ops:  # pool saturado: aceita quem tiver menos uso (R-56 cap 2)
                        ops = sorted((a for a in _bnc if a != ult_a),
                                     key=lambda x: (_usos_g.get(x, 0), x))
                    esc = ops[0] if ops else _bnc[0]
                    _usos_g[esc] = _usos_g.get(esc, 0) + 1
                    dst = dest / "assets" / Path(esc).name
                    if not dst.exists():
                        shutil.copy2(esc, dst)
                    novos_gap.append({"i": 7000 + k_gap, "t_ini": round(ini_g, 2),
                                      "t_fim": round(fim_g, 2), "tipo": "stock",
                                      "secao": sec_g, "tier": 1, "watermark": False,
                                      "src": f"jobs/{a.nome}/assets/{Path(esc).name}",
                                      "props": {}, "_do_banco": True})
                    ult_a = esc
                    k_gap += 1
                    ini_g = fim_g
            ant_t = max(ant_t, t_f)
        if novos_gap:
            beats_out.extend(novos_gap)
            print(f"gaps preenchidos [v5]: {len(novos_gap)} beats do banco "
                  f"({sum(b['t_fim']-b['t_ini'] for b in novos_gap):.0f}s de tela preta eliminados)")

    # ---- v5 (31/07): BURACO NUNCA VIRA TELA PRETA ----
    # beat sem asset é preenchido com clipe do BANCO DE NICHO (secao 900), em rodízio
    # e sem repetir vizinho — metade do 1º vídeo de cobras ficou preta por falta disso
    _banco5 = [r["arquivo"] for r in resolvido
               if r.get("secao") == 900 and str(r.get("arquivo") or "").lower().endswith(".mp4")
               and Path(r.get("arquivo") or "").exists()]
    if _banco5:
        n_pre5, ult5 = 0, None
        for b in sorted(beats_out, key=lambda x: x["t_ini"]):
            if b.get("componente") or b.get("src") or b.get("tipo") == "parallax":
                continue
            ops5 = [a for a in _banco5 if a != ult5] or _banco5
            esc5 = ops5[(SEED + b["i"] * 5) % len(ops5)]
            dst5 = dest / "assets" / Path(esc5).name
            if not dst5.exists():
                shutil.copy2(esc5, dst5)
            b["src"] = f"jobs/{a.nome}/assets/{Path(esc5).name}"
            b["tier"] = b.get("tier") or 1
            b["_do_banco"] = True
            ult5 = esc5
            n_pre5 += 1
        if n_pre5:
            print(f"buracos preenchidos [v5]: {n_pre5} beats com clipe do banco de nicho")

    # ---- GATES DE CONTEÚDO (29/07, prints do Piter) ----
    # G1: badge/stat SEM dado não renderiza scaffolding — Img18 com title vazio virava
    # um risco âmbar órfão sobre a foto. Vira foto hero limpa (Img01).
    for b in beats_out:
        if b.get("componente") == "Img18_PhotoStatBadge":
            pr18 = b.get("props") or {}
            if not (pr18.get("title") or "").strip():
                b["componente"] = "Img01_KenBurnsCine"
                stats["gate_img18"] = stats.get("gate_img18", 0) + 1
    # G2: card de TEXTO nunca corta no meio da frase ("Asia and Europe are" sublinhando
    # "are"). Completa com o texto dos beats seguintes; se não der (dado forte/limite),
    # apara palavras penduradas e fecha com reticências.
    _PENDURADAS = {"are", "is", "was", "were", "and", "or", "the", "a", "an", "of",
                   "to", "in", "on", "at", "for", "with", "that", "this", "it", "as"}
    for b in beats_out:
        c9 = b.get("componente") or ""
        pr9 = b.get("props") or {}
        tx9 = (pr9.get("text") or "").strip()
        if not (c9.startswith("Texto") and tx9) or re.search(r"[.!?…\"”']\s*$", tx9):
            continue
        extra9 = []
        for j9 in range(b["i"] + 1, b["i"] + 4):
            nx9 = ((plano_por_i.get(j9) or {}).get("texto") or "").strip()
            if not nx9:
                break
            extra9.append(nx9)
            if re.search(r"[.!?…]", nx9):
                break
        cand9 = " ".join([tx9] + extra9)
        m9 = re.search(r"^(.{%d,}?[.!?…])" % len(tx9), cand9)
        ext9 = m9.group(1)[len(tx9):] if m9 else ""
        if m9 and len(m9.group(1)) <= 120 and len(_nums_do_texto(ext9)) < 2:
            pr9["text"] = humanizar(m9.group(1))  # frase completa INTEIRA — corte() aqui recriava o corte cego
        else:  # sem extensão segura: apara penduradas e fecha
            palavras9 = tx9.rstrip(",;: ").split()
            while palavras9 and palavras9[-1].lower().strip(",;:") in _PENDURADAS:
                palavras9.pop()
            if palavras9:
                pr9["text"] = " ".join(palavras9).rstrip(",;: ") + "…"
        b["props"] = pr9
        stats["frase_completa"] = stats.get("frase_completa", 0) + 1

    # ---- MASCOTE (28/07, opção por style_card): personagem overlay do canal.
    # style_card["mascote"] = {"banco": "<pasta com index_mascote.json>", "cada": [2,3]}
    # Entra a cada 2-3 beats LIVRES (footage sem componente, >=2.2s, fora do cold-open),
    # pose casada com o TEXTO do trecho (funcao warn/explain/...), lado e zoom alternam.
    masc_cfg = _SC.get("mascote") or {}
    n_masc = 0
    if masc_cfg.get("banco"):
        try:
            mb = Path(masc_cfg["banco"])
            ix_m = json.loads((mb / "index_mascote.json").read_text(encoding="utf-8"))
            poses_m = [{**v, "key": k} for k, v in ix_m.get("itens", {}).items()
                       if (mb / v["file"]).exists()]
            if poses_m:
                (dest / "mascote").mkdir(exist_ok=True)
                # 29/07 (Piter): padrão cíclico [aparições seguidas, folga] => "2 sim, 2 não"
                pad_m = masc_cfg.get("padrao") or [2, 2]
                ciclo_m = max(1, pad_m[0] + pad_m[1])
                alturas_m = masc_cfg.get("alturas") or [0.82, 0.64]  # perto/longe (zoom variável)

                def _funcao_do_texto(tx):
                    t = (tx or "").lower()
                    if any(w in t for w in ("never", "don't", "do not", "warning", "danger",
                                            "mistake", "wrong", "avoid", "worst", "fail")):
                        return "warn"
                    if any(w in t for w in ("because", "science", "study", "research", "how ",
                                            "why ", "means", "brain", "body", "practice")):
                        return "explain"
                    return None

                k_livre = 0  # posição no ciclo de beats livres: [0..pad[0]) = COM mascote
                ult_pose = None
                for b in sorted(beats_out, key=lambda x: x["t_ini"]):
                    if b.get("tipo") not in ("stock", "footage_video") or b.get("componente") \
                            or b.get("_seg") or b["t_ini"] < 20 or (b["t_fim"] - b["t_ini"]) < 2.2:
                        continue
                    no_ar = (k_livre % ciclo_m) < pad_m[0]
                    k_livre += 1
                    if not no_ar:
                        continue
                    tx_b = (plano_por_i.get(b["i"]) or {}).get("texto")
                    fn = _funcao_do_texto(tx_b)
                    cand = [p for p in poses_m if p.get("funcao") == fn and p["key"] != ult_pose] \
                        or [p for p in poses_m if p["key"] != ult_pose] or poses_m
                    p = cand[(SEED + b["i"] * 7) % len(cand)]
                    ult_pose = p["key"]
                    if not (dest / "mascote" / p["file"]).exists():
                        shutil.copy2(mb / p["file"], dest / "mascote" / p["file"])
                    b["mascote"] = {"img": f"jobs/{a.nome}/mascote/{p['file']}",
                                    "lado": ("right", "left")[n_masc % 2],
                                    "altura": alturas_m[n_masc % len(alturas_m)],
                                    "pose": p.get("pose")}
                    n_masc += 1
                print(f"mascote [{ix_m.get('nome', '?')}]: {n_masc} entradas "
                      f"({len(poses_m)} poses no banco)")
        except Exception as e_m:
            print(f"mascote FALHOU ({e_m}) — seguindo sem personagem")

    # ---- AVATAR DO CANAL (v3, 29/07): apresentador consistente gerado no Flow/VEO.
    # style_card["avatar"] = {"banco": "<pasta keep>", "persona": "Clara",
    #                         "ilhas": {"1": "clip.mp4", ...}}  (seção -> clipe aprovado)
    # Ilha = abertura da seção: beats LIVRES consecutivos viram UM beat tipo "avatar"
    # full-frame com ÁUDIO NATIVO do clipe; a narração ducka ali (Montagem.tsx).
    # Clipes vêm APENAS do keep/ (rubric do curador VEO) — nunca da pasta bruta.
    av_cfg = _SC.get("avatar") or {}
    avatar_ilhas = []
    if av_cfg.get("banco") and av_cfg.get("ilhas"):
        try:
            ab = Path(av_cfg["banco"])
            (dest / "avatar").mkdir(exist_ok=True)
            for sec_s, arq_av in sorted(av_cfg["ilhas"].items(), key=lambda x: int(x[0])):
                src_av = ab / arq_av
                s_av = next((s for s in secoes if s["i"] == int(sec_s)), None)
                if not src_av.exists() or not s_av:
                    print(f"avatar: ilha seção {sec_s} pulada (clipe ou seção ausente)")
                    continue
                try:
                    d_clip = float(subprocess.run(
                        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
                         "-of", "csv=p=0", str(src_av)],
                        capture_output=True, text=True, timeout=30).stdout.strip() or 8)
                except Exception:
                    d_clip = 8.0
                # 29/07: ilha absorve QUALQUER beat consecutivo que caiba INTEIRO na
                # janela do clipe (só livres dava ilha de 3s e cortava a fala em 8s).
                # 1º beat precisa ser livre; parcial não entra (sem encolher animação).
                cadeia_av = []
                for b in sorted(beats_out, key=lambda x: x["t_ini"]):
                    if b["t_ini"] < s_av["t_ini"] - 0.1 or b.get("_seg"):
                        continue
                    livre_av = b.get("tipo") in ("stock", "footage_video") \
                        and not b.get("componente")
                    if not cadeia_av:
                        if livre_av:
                            cadeia_av.append(b)
                        continue
                    if abs(b["t_ini"] - cadeia_av[-1]["t_fim"]) < 0.05 \
                            and (b["t_fim"] - cadeia_av[0]["t_ini"]) <= d_clip + 0.3:
                        cadeia_av.append(b)
                    else:
                        break
                if not cadeia_av:
                    print(f"avatar: seção {sec_s} sem beat livre — ilha pulada")
                    continue
                t0_av = cadeia_av[0]["t_ini"]
                t1_av = round(cadeia_av[-1]["t_fim"], 2)
                if not (dest / "avatar" / src_av.name).exists():
                    shutil.copy2(src_av, dest / "avatar" / src_av.name)
                b0 = cadeia_av[0]
                for bx in cadeia_av[1:]:
                    beats_out.remove(bx)  # absorvido INTEIRO pela ilha
                b0.pop("mascote", None)
                b0.update({"tipo": "avatar", "src": f"jobs/{a.nome}/avatar/{src_av.name}",
                           "t_fim": t1_av, "componente": None, "props": {}, "bg": None})
                avatar_ilhas.append({"t_ini": round(t0_av, 2), "t_fim": t1_av})
                print(f"avatar [{av_cfg.get('persona', '?')}]: ilha seção {sec_s} "
                      f"{t0_av:.1f}-{t1_av:.1f}s ({src_av.name})")
        except Exception as e_av:
            print(f"avatar FALHOU ({e_av}) — sem ilhas de apresentador")
            avatar_ilhas = []

    # ---- v5 F2: PLANO DE BLOCOS + TRANSIÇÕES NATIVAS (sobreposição viva) ----
    # Seções agrupadas em blocos de ~2; corte ENTRE blocos é sempre SECO (permite
    # render por blocos + concat). Cortes de seção DENTRO do bloco ganham transição
    # nativa: o último beat da seção que sai é ESTENDIDO e anima por cima do beat
    # que entra (fade | slidePush | blurCut) — conteúdo VIVO dos dois lados.
    blocos_v5, trans_v5 = [], []
    if _SC.get("estilo") == "v5" and secoes:
        TRANS_TIPOS = ["fade", "slidePush", "blurCut"]
        TRANS_F = 14  # frames de sobreposição (~0.47s)
        por_bloco = 2
        for bi in range(0, len(secoes), por_bloco):
            grupo = secoes[bi:bi + por_bloco]
            blocos_v5.append({"t_ini": grupo[0]["t_ini"], "t_fim": grupo[-1]["t_fim"]})
            for s_in in grupo[1:]:  # cortes INTERNOS do bloco
                t_corte5 = s_in["t_ini"]
                tipo5 = TRANS_TIPOS[(SEED + int(t_corte5)) % len(TRANS_TIPOS)]
                # tolerância 1.2s: com buracos na timeline o fim do beat raramente
                # bate exatamente no corte da seção (0 transições no 1º teste, 31/07)
                saindo = min((b for b in beats_out if abs(b["t_fim"] - t_corte5) < 1.2),
                             key=lambda b: abs(b["t_fim"] - t_corte5), default=None)
                if saindo is not None:
                    saindo["trans_out"] = {"tipo": tipo5, "dur_f": TRANS_F}
                    trans_v5.append({"t": round(t_corte5, 2), "tipo": tipo5, "dur_f": TRANS_F})
        print(f"blocos [v5]: {len(blocos_v5)} blocos | {len(trans_v5)} transições nativas")

        # ---- v5 F3: efeito CSS por beat — GRADE consistente por seção (rotação
        # anti-repetição) + ANIMADO no hook (lightLeak) e na seção final (glowPulse)
        GRADES5 = ["tealOrange", "duotone", "silverGrade", "warmGrade", "coldGrade", "vignette"]
        usadas_g5 = set()
        accent5 = (_SC.get("paleta") or ["#f59e0b"])[0]
        for idx5, s5 in enumerate(secoes):
            livres_g = [g for g in GRADES5 if g not in usadas_g5] or GRADES5
            grade5 = livres_g[(SEED + idx5 * 7) % len(livres_g)]
            usadas_g5.add(grade5)
            alvo_fx = [b for b in beats_out
                       if s5["t_ini"] - 0.1 <= b["t_ini"] < s5["t_fim"]
                       and b.get("tipo") in ("stock", "footage_video", "footage_imagem",
                                             "ilustracao", "parallax")]
            for b in alvo_fx:
                b["fx_img"] = {"tipo": grade5, "accent": accent5}
            anim5 = "lightLeak" if idx5 == 0 else ("glowPulse" if idx5 == len(secoes) - 1 else None)
            if anim5:  # os 2 primeiros beats do momento ganham o animado no lugar da grade
                for b in alvo_fx[:2]:
                    b["fx_img"] = {"tipo": anim5, "accent": accent5}
        print(f"fx_img [v5]: {len(usadas_g5)} grades distintas + animados hook/final")

        # ---- v5 F4: Ken Burns SEMÂNTICO nas imagens (11 tipos por natureza do beat)
        KB_NAT = {"produto": ["productShot", "detailShot", "punchZoom"],
                  "epoca": ["archiveShot", "zoomOutReveal", "steadyDrift"],
                  "acao": ["actionShot", "smoothZoomPan", "punchZoom"],
                  "paisagem": ["smoothZoomPan", "focusPan", "verticalPan"],
                  "generico": ["steadyDrift", "smoothZoomPan", "rotateZoom", "zoomOutReveal"]}

        def _nat_beat5(b):
            tx = ((plano_por_i.get(b["i"]) or {}).get("busca") or "").lower()
            if any(w in tx for w in ("product", "shoe", "bike", "car", "tool", "gear")):
                return "produto"
            if any(w in tx for w in ("ancient", "historical", "archive", "vintage", "roman",
                                     "greek", "manuscript", "engraving")):
                return "epoca"
            if any(w in tx for w in ("running", "action", "moving", "training", "storm", "battle")):
                return "acao"
            if any(w in tx for w in ("landscape", "aerial", "mountain", "ocean", "sky", "ruins", "city")):
                return "paisagem"
            return "generico"

        n_kb5 = 0
        for b in beats_out:
            src5 = (b.get("src") or "")
            eh_img5 = src5 and not src5.lower().endswith((".mp4", ".webm", ".mov"))
            if eh_img5 and not b.get("componente"):
                ops_kb = KB_NAT[_nat_beat5(b)]
                b["kb"] = ops_kb[(SEED + b["i"] * 3) % len(ops_kb)]
                n_kb5 += 1
        print(f"kb [v5]: {n_kb5} imagens com Ken Burns semântico")

        # ---- v5 F5: KARAOKÊ opcional (style_card {"karaoke": true}) — timing
        # proporcional por palavra dentro da janela do beat (frames locais)
        if _SC.get("karaoke"):
            n_k5 = 0
            for b in beats_out:
                tx5 = ((plano_por_i.get(b["i"]) or {}).get("texto") or "").strip()
                if not tx5 or b.get("componente") or b.get("_seg"):
                    continue
                pal5 = tx5.split()
                durF5 = max(1, round((b["t_fim"] - b["t_ini"]) * 30))
                b["captionWords"] = [{"word": w, "startFrame": round(i * durF5 / len(pal5))}
                                     for i, w in enumerate(pal5)]
                n_k5 += 1
            print(f"karaoke [v5]: {n_k5} beats legendados")

    dur = max(x["t_fim"] for x in beats_out) + 0.5
    mont = {"fps": 30, "width": 1920, "height": 1080, "dur_s": round(dur, 2),
            "audio": f"jobs/{a.nome}/audio.mp3",
            "secoes": [{"i": s["i"], "t_ini": s["t_ini"], "t_fim": s["t_fim"],
                        "wash": s.get("wash", "none"), "titulo": s.get("titulo", "")} for s in secoes],
            "estilo": _SC.get("estilo", "v1"),
            "beats": beats_out}
    if audio_plan and (audio_plan["trilhas"] or audio_plan["sfx"]):
        mont["audio_plan"] = audio_plan
    if fx_overlays:
        mont["fx_overlays"] = fx_overlays
    if fx_trans:
        mont["fx_trans"] = fx_trans
    if avatar_ilhas:
        mont["avatar_ilhas"] = avatar_ilhas
    if blocos_v5:
        mont["blocos"] = blocos_v5
    if trans_v5:
        mont["trans_v5"] = trans_v5
    (dest / "montagem.json").write_text(json.dumps(mont, ensure_ascii=False), encoding="utf-8")
    print(f"montagem: {len(beats_out)} beats | {dur:.1f}s | assets copiados: {n_copy} -> {dest}")


if __name__ == "__main__":
    main()
