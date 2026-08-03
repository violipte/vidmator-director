# -*- coding: utf-8 -*-
"""CURADOR v5 (F6) — footage com queries ESTRATIFICADAS + pool multi-fonte +
BATCH-SCORE (defeitos v4 anulam + régua 0-10) + escolha do MELHOR do pool.

Fluxo por beat de vídeo:
  1. 4 queries com estratégia (fiel / específica / ângulo-contexto / keywords)
  2. coleta candidatos em paralelo: pixabay_video + coverr (fontes5) — round a round
  3. batch_gate (1 chamada Vision pro pool inteiro): score 0-10 + vetos
  4. melhor >= 8 vence e SÓ ELE é reivindicado (perdedores voltam pro pool global)
  5. download + normaliza 1080p30 + dedup visual (executor) + resolvido/bNNN.json
  6. pool não rendeu? fallback = resolver_stock do executor v4 (pexels+yt intactos)

Uso: python curador5.py --job <dir> --plano plano.json [--workers 4] [--resume]
"""
import argparse
import json
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).parent))
import executor_beats as ex  # noqa — dedup/USED/normalização/fallback v4 (read-only)
import vision_gate as vg  # noqa — amostragem de frames p/ dar nota ao candidato do v4
from curador_footage import secoes_do_plano, ctx_da_secao  # noqa
from fontes5 import coletar_videos, coletar_imagens, web_video, social_video  # noqa
from gate5 import batch_gate, SCORE_THRESHOLD  # noqa

STOPWORDS5 = {"the", "a", "an", "of", "in", "on", "at", "with", "and", "or", "for", "to"}

# hierarquia T3 preservada (regra Piter 31/07): footage REAL vale mais que stock, então
# entra na disputa com vantagem — não com passe livre.
BONUS_TIER = {3: 2, 2: 1, 1: 0}
NOTA_V4_OTIMA = 9  # v4 com plano ótimo fecha o beat sem gastar o pool novo (tempo)
_REDES = ("tiktok.com", "instagram.com", "facebook.com")


def queries_estratificadas(busca, assunto_secao="", ancora=""):
    """4 estratégias + ÂNCORA DO TEMA (31/07, QA Piter: 'ilustra a frase, não a cena').
    Beat isolado buscava 'doctor writing notebook' num vídeo de COBRA e trazia clipe
    genérico. A âncora do style_card entra em TODA query — o assunto do vídeo domina."""
    base = busca.split(" OR ")[0].strip()
    kws = [w for w in re.findall(r"[a-zA-Z]{3,}", busca) if w.lower() not in STOPWORDS5]
    anc = (ancora or "").strip()
    return [
        f"{anc} {base}".strip()[:95],                     # 1 âncora + fiel
        f"{base} close up detail {anc}".strip()[:95],     # 2 específica ancorada
        f"{anc} {' '.join(kws[:3])}".strip()[:95],        # 3 âncora + keywords
        base,                                             # 4 fiel puro (último recurso)
    ]


def _luminancia_ok(mp4, tmp, min_brilho=42):
    """Gate de TELA (31/07): clipe escuro demais NÃO vai ao ar — o Vision aprova
    'é uma cobra' mas não vê que na tela é um borrão preto (frame 7s do vídeo v2).
    Determinístico, sem API: brilho médio de 3 instantes."""
    from PIL import Image, ImageStat
    vals = []
    for ss in ("1", "2.5", "4"):
        o = Path(tmp) / f"lum_{abs(hash(str(mp4) + ss)) % 10**8}.jpg"
        subprocess.run(["ffmpeg", "-nostdin", "-y", "-loglevel", "error", "-ss", ss,
                        "-i", str(mp4), "-frames:v", "1", "-vf", "scale=160:-2", str(o)],
                       capture_output=True, timeout=60)
        if o.exists():
            try:
                vals.append(ImageStat.Stat(Image.open(o).convert("L")).mean[0])
            except Exception:
                pass
            o.unlink(missing_ok=True)
    return (sum(vals) / len(vals)) >= min_brilho if vals else True


def _baixar_normalizar(url, dest_mp4, tmp):
    """Download + normaliza 1920x1080/30fps h264 (padrão do executor)."""
    import httpx
    import threading
    # nome ÚNICO por thread+chamada (WinError 32: dois workers colidiam no mesmo temp)
    bruto = Path(tmp) / f"c5_{threading.get_ident()}_{abs(hash(url)) % 10**8}.mp4"
    try:
        with httpx.stream("GET", url, headers={"User-Agent": "Mozilla/5.0"},
                          timeout=120, follow_redirects=True) as r:
            if r.status_code != 200:
                return False
            with open(bruto, "wb") as f:
                for chunk in r.iter_bytes(1 << 16):
                    f.write(chunk)
        if bruto.stat().st_size < 200_000 or b"ftyp" not in bruto.read_bytes()[:16]:
            return False
        r2 = subprocess.run(["ffmpeg", "-nostdin", "-y", "-loglevel", "error", "-i", str(bruto),
                             "-t", "12", "-vf", "scale=1920:1080:force_original_aspect_ratio=increase,"
                             "crop=1920:1080", "-r", "30", "-an", "-c:v", "libx264", "-preset",
                             "fast", "-crf", "20", "-pix_fmt", "yuv420p", str(dest_mp4)],
                            capture_output=True, timeout=300)
        return r2.returncode == 0 and Path(dest_mp4).exists()
    except Exception:
        return False
    finally:
        try:
            bruto.unlink(missing_ok=True)
        except OSError:
            pass  # Windows pode segurar o handle um instante — o tmp é limpo depois


def _baixar_imagem(url, dest_jpg):
    """Download de imagem + cap de resolução (o executor já tem a regra: original de
    30MP estoura EncodingError no render)."""
    import httpx
    try:
        r = httpx.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=60, follow_redirects=True)
        if r.status_code != 200 or len(r.content) < 8000:
            return False
        Path(dest_jpg).write_bytes(r.content)
        from PIL import Image
        with Image.open(dest_jpg) as im:   # valida que é imagem de verdade
            if min(im.size) < 480:
                Path(dest_jpg).unlink(missing_ok=True)
                return False
        ex._cap_resolucao(Path(dest_jpg))
        return True
    except Exception:
        Path(dest_jpg).unlink(missing_ok=True)
        return False


def ancora_local(ancora_en, idioma="Portuguese (Brazil)"):
    """Traduz a âncora do tema UMA VEZ por job, pra busca em rede social.

    01/08: as buscas do editor são em EN (decisão do Piter — o Google devolve
    material de sobra). Mas rede social de nicho LOCAL é indexada no idioma local:
    `site:tiktok.com brazilian venomous snake` = 0 posts; `jararaca cobra` = 18.
    Uma chamada por job (não por beat) — se falhar, devolve "" e o social busca só
    em EN, sem quebrar nada."""
    import httpx
    if not ancora_en or not vg._OKEY:
        return ""
    try:
        r = httpx.post("https://api.openai.com/v1/chat/completions",
                       headers={"Authorization": "Bearer " + vg._OKEY},
                       # 400, não 60: o Luna é modelo de RACIOCÍNIO e os reasoning
                       # tokens saem deste mesmo orçamento — com 60 ele pensa e
                       # devolve content vazio (finish_reason=length)
                       json={"model": vg._LUNA_MODEL, "max_completion_tokens": 400,
                             "messages": [{"role": "user", "content":
                                           f"Translate to {idioma} the search terms below. "
                                           f"Reply with ONLY the translated terms, no quotes, "
                                           f"no explanation.\n\n{ancora_en}"}]},
                       timeout=60)
        if r.status_code == 200:
            return (r.json()["choices"][0]["message"]["content"] or "").strip()[:80]
    except Exception:
        pass
    return ""


def _baixar_ytdlp(url, dest_mp4, tmp):
    """Baixa post de página (YouTube/TikTok/Reels/FB) via yt-dlp e normaliza 1080p30.
    Usa o MESMO pool de proxy do executor (não queimar IP) e corta em 12s. Vertical
    (TikTok/Reels) vira crop central — o T3 já renderiza em quadro menor."""
    import threading
    bruto = Path(tmp) / f"s5_{threading.get_ident()}_{abs(hash(url)) % 10**8}.%(ext)s"
    _, pargs = ex._yt_args_proxy()
    cmd = ex.YTDLP + pargs + [
        "--no-warnings", "--no-playlist", "--quiet",
        "-f", "best[height<=1080][ext=mp4]/best[ext=mp4]/best",
        "--max-filesize", "120M", "-o", str(bruto), url]
    try:
        r = subprocess.run(cmd, capture_output=True, timeout=300)
        if r.returncode != 0:
            return False
        achados = sorted(Path(tmp).glob(bruto.name.replace(".%(ext)s", ".*")))
        if not achados:
            return False
        src = achados[0]
        r2 = subprocess.run(["ffmpeg", "-nostdin", "-y", "-loglevel", "error", "-i", str(src),
                             "-t", "12", "-vf", "scale=1920:1080:force_original_aspect_ratio=increase,"
                             "crop=1920:1080", "-r", "30", "-an", "-c:v", "libx264", "-preset",
                             "fast", "-crf", "20", "-pix_fmt", "yuv420p", str(dest_mp4)],
                            capture_output=True, timeout=300)
        src.unlink(missing_ok=True)
        return r2.returncode == 0 and Path(dest_mp4).exists()
    except Exception:
        return False


def _gate_pesado_ok(mp4, beat, ctx):
    """Gate v4 COMPLETO (6 frames pela duração inteira) — obrigatório pra material
    social. Regra dura do Piter: NUNCA criador falando pra câmera (máx entrevista de
    TV), nunca criança. O thumb não denuncia isso: no TikTok/Reels o rosto costuma
    entrar depois do 1º frame (mesmo motivo do QA de tênis 23/07)."""
    frames = vg._frames_de_video(mp4, ctx["tmp"], n=6)
    if not frames:
        return False
    g = vg.gate(ex.subject_do_beat(beat), [str(f) for f in frames])
    if not g["ok"]:
        print(f"  b{beat['i']:03d} social REPROVADO {g['flags']}")
    return bool(g["ok"])


def _relatar_duplicatas(ctx):
    """Passe final: near-duplicate por embedding CLIP (02/08).

    O dedup do executor (`_e_dup_visual`, dHash) tem dois furos: varre só `*.mp4`
    (imagem nunca era comparada) e quebra quando o MESMO conteúdo vem de fontes
    diferentes, com crop e compressão distintos. Com 7 fontes no pool isso ficou
    comum — o preqa do vídeo de cobras fechou com 6 flags R-72. Aqui o problema é
    visto ANTES da montagem, não depois de renderizar.
    Só REPORTA (com o comando de condenação pronto): apagar asset no automático
    arrisca esvaziar beat que já foi dado como resolvido."""
    from gate5 import CLIP_PY
    assets = sorted(Path(ctx["assets"]).glob("*.jpg"))
    if not CLIP_PY.exists() or len(assets) < 2:
        return
    try:
        r = subprocess.run([str(CLIP_PY), str(Path(__file__).parent / "clip_rank.py"),
                            "--dedup", "--imgs", *[str(x) for x in assets]],
                           capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=300)
        grupos = json.loads((r.stdout or "").strip().splitlines()[-1])
    except Exception:
        return
    if not grupos:
        print("dedup CLIP: nenhuma imagem repetida no job")
        return
    print(f"!! dedup CLIP: {len(grupos)} grupo(s) de imagem repetida (R-72 antes do render):")
    for g in grupos:
        print("   " + " == ".join(Path(x).name for x in g))
        for extra in g[1:]:   # o 1º fica; os demais são candidatos a re-resolver
            bid = Path(extra).name.split("__")[0]
            print(f'     del "resolvido/{bid}.json" + assets/{bid}__*')


_CORPUS = {"txt": ""}   # tudo que é DITO no vídeo — régua contra espécie inventada


def carregar_corpus(plano):
    _CORPUS["txt"] = " ".join((b.get("texto") or "") for b in plano.get("beats", [])).lower()


def _especie_do_beat(b):
    """entidades.especie do diretor = o ser vivo daquele beat. É o que liga o
    iNaturalist em MENÇÃO PONTUAL (um bicho citado dentro de um roteiro que não é
    de natureza). Aceita rótulos vizinhos porque o prompt do diretor pode variar."""
    e = b.get("entidades")
    if not isinstance(e, dict):
        return None
    for k in ("especie", "taxon", "animal", "planta", "species"):
        v = e.get(k)
        # o LLM às vezes devolve LISTA (`['jaguar','stingray']`) — mesmo problema que
        # `dados` já deu. Pega o 1º: é o sujeito do beat; o resto é contexto.
        if isinstance(v, list):
            v = next((x for x in v if isinstance(x, str) and x.strip()), None)
        if isinstance(v, str) and v.strip():
            # "lion, tiger, leopard" não é UMA espécie — a primeira é a que ilustra
            esp = v.split(",")[0].strip()
            # ⚠️ o diretor ALUCINA espécie: o roteiro amazônico dizia "any big cat" e
            # ele extraiu lion/tiger/leopard, plantando um LEÃO AFRICANO no vídeo.
            # Mas a checagem tem que ser contra o ROTEIRO INTEIRO, não contra a frase
            # do beat: "It is the largest cat in the Americas" fala do jaguar por
            # CORREFERÊNCIA, e o diretor acertou — validar frase a frase barrava 21
            # de 50, quase todos corretos. Regra: a espécie precisa ser dita em algum
            # lugar do vídeo; se não é, o LLM inventou.
            if _CORPUS["txt"] and esp.lower().split()[0] not in _CORPUS["txt"]:
                return None
            return esp
    return None


def resolver_beat5(b, sctx, ctx, usados_urls, ancora="", ancora_pt="", taxonomico=False):
    """Pool multi-fonte + batch score; devolve dict resolvido ou None (=> fallback v4).

    01/08 (QA cobras + pedido do Piter): antes só VÍDEO era coletado aqui — a via de
    IMAGEM (`coletar_imagens`: Openverse/SearXNG/Pixabay/Unsplash) estava importada e
    NUNCA era chamada. Efeito: a imagem nota 9 que ilustrava o bicho não perdia a
    disputa, ela nunca ENTRAVA na disputa, e o beat acabava com vídeo genérico nota 6
    (ou com esquema técnico vindo do fallback v4). Agora vídeo e imagem vão para o
    MESMO batch-score e o melhor vence, seja qual for a mídia."""
    for rodada, q in enumerate(queries_estratificadas(b.get("busca") or "", "", ancora)):
        if not q.strip():
            continue
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=4) as _p:
            f_v = _p.submit(coletar_videos, q, 3, usados_urls)   # stock: Pexels/Coverr/Pixabay
            # imagem: Openverse/web/... + iNaturalist (02/08). O iNat só dispara com
            # espécie explícita do diretor OU nicho taxonômico no style_card — busca
            # frouxa nele casa qualquer coisa ("harley" -> a planta Harleya).
            f_i = _p.submit(coletar_imagens, q, 3, usados_urls, _especie_do_beat(b),
                            taxonomico, bool(b.get("strict")), rodada, ancora)
            # web/social SÓ na 1ª rodada: o ddgs rate-limita, e 70 beats x 4 queries
            # x 4 redes queimaria a cota logo no começo da curadoria
            f_w = _p.submit(web_video, q, 3) if rodada == 0 else None
            f_s = _p.submit(social_video, q, 2, _REDES, ancora_pt) if rodada == 0 else None
            vids = [{**c, "_midia": "video"} for c in (f_v.result() or [])]
            imgs = [{**c, "_midia": "imagem"} for c in (f_i.result() or [])]
            web_v = [{**c, "_midia": "video"} for c in ((f_w.result() if f_w else []) or [])]
            soc = [{**c, "_midia": "video"} for c in ((f_s.result() if f_s else []) or [])]
        # social sem thumb não tem como ser pré-triado por imagem — vai direto pro
        # teste caro (baixar + gate de 6 frames), e só depois dos que têm nota
        cands = vids + imgs + web_v + [c for c in soc if c.get("thumb")]
        sem_thumb = [c for c in soc if not c.get("thumb")]
        if not cands and not sem_thumb:
            continue
        # iNaturalist P1 = a espécie EXATA, identificada por especialista humano
        # (research grade): a relevância já está provada por gente que entende do
        # bicho — mandar pro Vision perguntar "é uma jararaca?" é pagar pra ter uma
        # resposta pior. Pula só o gate de RELEVÂNCIA; os de DEFEITO seguem adiante.
        verificados = [c for c in cands if c.get("source") == "inaturalist"
                       and not c.get("gate_relevancia")]
        # vídeo é julgado pelo THUMB (barato); imagem, por ela mesma
        pool = [{**c, "url": c.get("thumb") or c["url"]}
                for c in cands if c not in verificados]
        notas = batch_gate(pool, b.get("busca") or q, sctx, tema=ancora) if pool else []
        # o pool inteiro disputa por SCORE — imagem 9 ganha de vídeo 6 (regra Piter 01/08).
        # social sem thumb entra no FIM da fila: só é tentado se nada com nota vingou.
        fila = [{**c, "score": 10, "vetos": []} for c in verificados] + \
               [n for n in notas if n["score"] >= 7] + \
               [{**c, "score": 7} for c in sem_thumb]
        for melhor in fila:
            orig = next((c for c in cands + sem_thumb if c["id"] == melhor["id"]), None)
            if not orig:
                continue
            if orig["_midia"] == "video":
                tier_c = int(orig.get("tier") or 1)
                dest = Path(ctx["assets"]) / f"b{b['i']:03d}__T{tier_c}__{orig['id']}.mp4"
                if orig.get("_via") == "ytdlp":
                    if not _baixar_ytdlp(orig["url"], dest, ctx["tmp"]):
                        continue
                    # material da web/social: gate PESADO (6 frames) — talking-head,
                    # criança e marca só aparecem depois do 1º frame
                    if not _gate_pesado_ok(dest, b, ctx):
                        dest.unlink(missing_ok=True)
                        continue
                elif not _baixar_normalizar(orig["url"], dest, ctx["tmp"]):
                    continue
                if not _luminancia_ok(dest, ctx["tmp"]):   # gate de TELA
                    dest.unlink(missing_ok=True)
                    continue
                tipo_final = "stock"
            else:
                # tier da IMAGEM vem da licença (iNat: cc0=T1, cc-by=T2), não fixo
                dest = Path(ctx["assets"]) / f"b{b['i']:03d}__T{int(orig.get('tier') or 1)}__{orig['id']}.jpg"
                if not _baixar_imagem(orig["url"], dest):
                    continue
                tipo_final = "footage_imagem"
            if ex._e_dup_visual(str(dest), ctx):
                dest.unlink(missing_ok=True)
                continue
            usados_urls.add(orig["url"])  # SÓ o vencedor reivindica (demais voltam ao pool)
            return {"i": b["i"], "t_ini": b.get("t_ini", 0), "t_fim": b.get("t_fim", 0),
                    "secao": b.get("secao", 0), "status": "ok", "arquivo": str(dest),
                    "tier": int(orig.get("tier") or 1),  # T3 (web/social) => máscara pesada
                    "fonte": orig["source"], "tipo": tipo_final,
                    "tipo_final": tipo_final, "midia": orig["_midia"],
                    "score": melhor["score"], "busca": q[:120],
                    # CC-BY obriga crédito na descrição do vídeo — sem isso a licença
                    # é violada mesmo sendo "livre". Vira CREDITOS.txt no job.
                    "atribuicao": orig.get("atribuicao", ""),
                    "licenca": orig.get("licenca", ""),
                    "taxon": orig.get("taxon", ""), "degrau": orig.get("degrau", "")}
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--job", required=True)
    ap.add_argument("--plano", required=True)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--resume", action="store_true")
    a = ap.parse_args()

    job = Path(a.job)
    plano = json.loads(Path(a.plano).read_text(encoding="utf-8"))
    carregar_corpus(plano)   # régua contra espécie que o diretor inventou
    sc = json.loads((job / "style_card.json").read_text(encoding="utf-8")) \
        if (job / "style_card.json").exists() else {}
    desamb = sc.get("desambiguacao") or {}
    todos = sorted(set(desamb.values()))
    secs = secoes_do_plano(plano, desamb)
    if not any(s["produto"] for s in secs.values()):
        todos = []  # nicho sem announce => ctx b-roll (fix 27/07)

    ancora5 = sc.get("assunto_ancora") or ""
    # 1 chamada por JOB: rede social de nicho local é indexada no idioma local
    ancora_pt5 = sc.get("assunto_ancora_local") or ancora_local(ancora5)
    # nicho de fauna/flora: libera o iNaturalist a garimpar a própria busca
    # (fora dele, só com entidades.especie explícita — ver inaturalist_img)
    taxo5 = bool(sc.get("taxonomico"))
    if ancora_pt5:
        print(f"âncora local (busca social): '{ancora_pt5}'")
    ctx = {"assets": job / "assets", "tmp": job / "_tmp", "res": job / "resolvido"}
    for d in ctx.values():
        d.mkdir(parents=True, exist_ok=True)
    usados_urls = set()

    tarefas = []
    for s, sec in sorted(secs.items()):
        sctx = ctx_da_secao(sec, todos)
        for b in sec["beats"]:
            # 01/08: ILUSTRACAO entrou aqui. Os 21 beats de "diagram" do plano de cobras
            # (neuromuscular junction, diaphragm paralysis, crotoxin molecule) iam DIRETO
            # pro v4 — sem âncora do tema e sem score — e voltavam com esquema de livro
            # de fisiologia, que não ilustra cobra nenhuma. Agora disputam igual.
            if b.get("tipo") not in ("footage_video", "stock", "ilustracao", "footage_imagem"):
                continue
            jres = ctx["res"] / f"b{b['i']:03d}.json"
            if a.resume and jres.exists():
                continue
            b2 = dict(b)
            b2["_sec_ctx"] = sctx
            tarefas.append((b2, sctx))
    print(f"curador5: {len(tarefas)} beats | âncora='{ancora5}' | v4 primeiro + fontes novas")

    def _nota_do_v4(r4, b2, sctx):
        """Dá ao candidato do v4 uma NOTA na mesma régua do pool novo (0-10 + bônus de
        tier). Vídeo é julgado por 1 frame do meio; imagem, por ela mesma."""
        arq = Path(r4["arquivo"])
        alvo = arq
        if arq.suffix.lower() in (".mp4", ".mov", ".webm"):
            frames = vg._frames_de_video(arq, ctx["tmp"], n=1)
            if not frames:
                return 6  # não deu pra amostrar: assume mediano (não pune o v4 à toa)
            alvo = frames[0]
        notas = batch_gate([{"path": str(alvo), "id": f"v4_{b2['i']}", "source": "v4"}],
                           b2.get("busca") or "", sctx, tema=ancora5)
        n = notas[0]["score"] if notas else -1
        return 6 if n < 0 else n  # gate mudo não condena o que o v4 já aprovou

    def _rodar5(par):
        """01/08 (QA cobras): a ordem "v4 primeiro, v5 só se o v4 falhar" fazia o v5
        NUNCA ser consultado — 38 dos 47 beats foram decididos pelo v4 sozinho, com
        gate BINÁRIO (o primeiro que passa, não o melhor). Era daí que vinham o
        "doctor writing notebook" e os diagramas técnicos num filme sobre cobras.

        Mas inverter a ordem reintroduziria o erro de 31/07 (stock genérico ganhando
        do YouTube real). Então nem uma coisa nem outra: o candidato do v4 entra no
        MESMO batch-score, com BÔNUS DE TIER. A hierarquia T3 continua valendo —
        footage real (T3) leva +2, CC/PD (T2) +1, stock (T1) 0 — mas um plano
        medíocre do v4 (nota 4) não ganha mais de uma foto certa nota 9."""
        b2, sctx = par
        if ancora5 and ancora5.split()[0].lower() not in (b2.get("busca") or "").lower():
            b2 = {**b2, "busca": f"{ancora5} {b2.get('busca') or ''}".strip()[:110]}
        _RESOLVER_V4 = {"footage_video": ex.resolver_footage_video,
                        "footage_imagem": ex.resolver_footage_imagem,
                        "ilustracao": ex.resolver_ilustracao}
        try:
            r4 = _RESOLVER_V4.get(b2.get("tipo"), ex.resolver_stock)(b2, ctx)
        except Exception as e4:
            print(f"  b{b2['i']:03d} v4 erro ({type(e4).__name__})")
            r4 = None
        if not (r4 and r4.get("status") == "ok" and r4.get("arquivo")
                and Path(r4["arquivo"]).exists()):
            r4 = None

        nota4 = -1
        if r4:
            try:
                nota4 = _nota_do_v4(r4, b2, sctx) + BONUS_TIER.get(int(r4.get("tier") or 1), 0)
            except Exception:
                nota4 = 6
            if nota4 >= NOTA_V4_OTIMA:   # v4 achou plano BOM: nem gasta pool novo
                return b2, {**r4, "score": nota4}, "v4"

        try:  # v4 fraco (ou vazio) -> o pool novo disputa a vaga
            r5 = resolver_beat5(b2, sctx, ctx, usados_urls, ancora5, ancora_pt5, taxo5)
        except Exception as e5:
            print(f"  b{b2['i']:03d} v5 erro ({type(e5).__name__})")
            r5 = None
        nota5 = (r5 or {}).get("score", -1)
        if r5 and nota5 > nota4:
            if r4:  # o do v4 perdeu a disputa — não deixa lixo no assets/
                Path(r4["arquivo"]).unlink(missing_ok=True)
            return b2, r5, "v5"
        return b2, ({**r4, "score": nota4} if r4 else None), "v4"

    ok5 = ok4 = falhas = 0
    with ThreadPoolExecutor(max_workers=a.workers) as pool:
        for b2, r, origem in pool.map(_rodar5, tarefas):
            if r and r.get("status") == "ok" and r.get("arquivo"):
                (ctx["res"] / f"b{b2['i']:03d}.json").write_text(
                    json.dumps({**{k: b2.get(k) for k in ("i", "secao", "t_ini", "t_fim", "busca")},
                                **r, "tipo": b2.get("tipo")}, ensure_ascii=False), encoding="utf-8")
                if origem == "v5":
                    ok5 += 1
                else:
                    ok4 += 1
                print(f"  b{b2['i']:03d} OK [{origem}] {Path(r['arquivo']).name[-42:]}")
            else:
                falhas += 1
                print(f"  b{b2['i']:03d} BURACO")
    print(f"=== curador5: {ok5} via fontes novas + {ok4} via fallback v4 | {falhas} buracos ===")
    _relatar_duplicatas(ctx)


if __name__ == "__main__":
    main()
