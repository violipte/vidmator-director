# -*- coding: utf-8 -*-
"""AUDITOR DE MONTAGEM (R-76) — valida TODA regra R-xx testável sobre a montagem.json,
ANTES de qualquer render. O render deixa de ser laboratório: bug de decisão aparece
aqui, em segundos, não em 20 minutos de GPU.

Uso: python auditar_montagem.py <montagem.json> <plano.json> [--budget 0.12]
Exit 0 = verde (pode renderizar). Exit 1 = violações listadas por R-xx.
"""
import argparse
import json
import re
import sys
from pathlib import Path

def _dic_a(d):
    """dados do LLM podem vir como LISTA — normaliza (31/07)."""
    if isinstance(d, (list, tuple)):
        d = next((x for x in d if isinstance(x, dict)), None)
    return d if isinstance(d, dict) else {}


sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).parent))
from acervo_registry import DEPRECATED, _nums_do_texto  # noqa

_PEDIDOS = {}   # i -> componente pedido pelo diretor (carregado do plano)


def _pedido_do_diretor(i, comp):
    return _PEDIDOS.get(i) == comp

PUB = Path(r"F:/Canal Dark/Aplicativo de Edição/remotion/public")
ESTRUTURAIS = {"ChapterTitle", "QuoteCard", "CharacterCard", "CharacterKeyword", "NodeHierarchy",
               "LineChart", "LogoFlagGrid", "SentenceHighlight", "SubjectTitleCard",
               # 02/08 (arquitetura Piter): legados que o DIRETOR pede e o COMP_MAP
               # da v5 renderiza — deprecado saiu do sorteio, não do vocabulário
               "NumberCountOverlay", "MultiCountryOutline", "MapRoute", "SatelliteLocationPin",
               "RegionLocationText", "DualImpactSentence", "BulletPointOverlay", "TextReveal",
               "SingleSentenceTextSlide", "OneWordCallout", "BarChartComparison",
               "YtCta", "SubscribeBellPulse", "SubscribeMinimal", "CtaBannerSlim"}
PREFIXOS_OK = ("Texto", "Ovl", "Graf", "Img", "Soc", "Map", "Duo", "Lst")
ANOTA_OVL = {"Ovl11_SpecBadge", "Ovl12_GiantStat", "Ovl13_PriceTag"}  # anotação de dado, não texto


def eh_texto(c):
    return bool(c) and (c.startswith("Texto") or c.startswith("Ovl")) and c not in ANOTA_OVL


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("montagem")
    ap.add_argument("plano")
    ap.add_argument("--budget", type=float, default=0.12)
    a = ap.parse_args()

    m = json.loads(Path(a.montagem).read_text(encoding="utf-8"))
    plano = json.loads(Path(a.plano).read_text(encoding="utf-8"))
    # teto de texto por NICHO (style_card.texto_budget; doc 0.12, instrucional denso 0.16)
    job_guess = re.search(r"jobs/([a-z0-9_]+)_mont", a.montagem.replace(chr(92), "/"))
    desamb = []
    if job_guess:
        sc_p = Path(r"F:/Canal Dark/Aplicativo de Edição/banco-videos") / f"_job_{job_guess.group(1)}" / "style_card.json"
        if sc_p.exists():
            try:
                _sc = json.loads(sc_p.read_text(encoding="utf-8"))
                a.budget = _sc.get("texto_budget", a.budget)
                desamb = [k.lower() for k in (_sc.get("desambiguacao") or {})]
            except Exception:
                pass
    _PEDIDOS.update({b.get("i"): b.get("componente") for b in plano.get("beats", [])
                     if b.get("componente")})
    ptxt = {b["i"]: (b.get("texto") or "") for b in plano.get("beats", [])}
    pdad = {b["i"]: (b.get("dados") or {}) for b in plano.get("beats", [])}
    pest = {b["i"]: b.get("estrategia") for b in plano.get("beats", [])}
    beats = m["beats"]
    V = []  # (Rxx, beat, msg)

    # ---- A1/A2 [R-30/31]: componentes válidos, nunca deprecated, props sãos ----
    for b in beats:
        c = b.get("componente")
        if b["tipo"] == "animacao":
            if not c:
                V.append(("R-31", b["i"], "beat de animação sem componente"))
                continue
            if c in DEPRECATED and not _pedido_do_diretor(b["i"], c):
                # 02/08 (arquitetura Piter): DEPRECATED tira do SORTEIO, não do
                # vocabulário do DIRETOR. Se o plano pediu o componente, renderizar
                # é honrar o pedido — violação seria só se veio do re-pick.
                V.append(("R-31", b["i"], f"componente DEPRECATED via re-pick: {c}"))
            elif not (c in ESTRUTURAIS or c.startswith(PREFIXOS_OK)):
                V.append(("R-31", b["i"], f"componente fora do COMP_MAP: {c}"))
            props = b.get("props") or {}
            if "__IMG__" in json.dumps(props):
                V.append(("R-30", b["i"], f"{c} com slot __IMG__ não resolvido"))
            for k in ("text", "title"):
                v = props.get(k)
                if isinstance(v, str) and len(v) >= 88 and v[-1].isalnum() and not v.endswith("..."):
                    V.append(("R-39b", b["i"], f"{c}.{k} suspeito de corte cego: '...{v[-25:]}'"))

    # ---- A3 [R-26]: ESTATÍSTICA nunca em texto-family. Instrução com números pequenos
    # ('run 1 to 3 minutes') pode ser placa — critério: dados com values>=2 OU núm >=10 ----
    for b in beats:
        if b["tipo"] != "animacao":
            continue
        if pest.get(b["i"]) == "dado" and eh_texto(b.get("componente")):
            d = pdad.get(b["i"]) or {}
            nums = [n for n in _nums_do_texto(ptxt.get(b["i"], "")) if not (n.isdigit() and 1300 <= int(n) <= 2099)]
            estatistica = len(_dic_a(d).get("values") or []) >= 2 or any(n.isdigit() and int(n) >= 10 for n in nums)
            if len(nums) >= 2 and estatistica:
                V.append(("R-26", b["i"], f"DADO ({nums[:3]}) degradado pra {b['componente']}"))

    # ---- A4 [R-27]: 1º ano distinto falado tem overlay de data (com carry) ----
    anos_falados, anos_na_tela = [], set()
    for b in beats:
        tb = ptxt.get(b["i"], "")[:45]
        for n in _nums_do_texto(tb):
            if n.isdigit() and 1300 <= int(n) <= 2099 and n not in anos_falados:
                anos_falados.append(n)
        if b.get("componente") == "Ovl10_NumberBadge":
            t = str((b.get("props") or {}).get("text") or "")
            if t.isdigit():
                anos_na_tela.add(t)
    if anos_falados and anos_falados[0] not in anos_na_tela:
        V.append(("R-27", "-", f"1º ano falado ({anos_falados[0]}) SEM overlay de data"))

    # ---- A5 [R-25]: pessoa nomeada = foto real ou nada ----
    for b in beats:
        nome = _dic_a(pdad.get(b["i"])).get("name")
        c = b.get("componente") or ""
        if c == "CharacterCard":
            img = (b.get("props") or {}).get("characterImage") or ""
            if not img or not (PUB / img).exists():
                V.append(("R-25", b["i"], f"CharacterCard '{nome}' sem foto real resolvida"))

    # ---- A6 [R-62]: orçamento de texto (mesma régua do montador: ano/data sobre footage
    # NÃO é texto; capítulo minimal e placas discretas = meio peso) ----
    _PLACAS = ("Ovl02", "Ovl03", "Ovl04", "Ovl05", "Ovl09")
    t_txt = 0.0
    for b in beats:
        c = b.get("componente") or ""
        if b["tipo"] != "animacao" or not eh_texto(c):
            continue
        if b.get("bg_nitido"):
            continue  # R-27: data sobre footage
        t_txt += (b["t_fim"] - b["t_ini"]) * (0.5 if c.startswith(_PLACAS) else 1.0)
    if t_txt > a.budget * m["dur_s"] * 1.15:
        V.append(("R-62", "-", f"texto {t_txt:.0f}s > {a.budget:.0%}+15% de {m['dur_s']:.0f}s"))

    # ---- A7 [R-56]: reuso — estática 1x, vídeo <=2 com gap >=6. Conta TAMBÉM imagens
    # dentro de props (QA tenis 23/07: mesma foto como src de um beat e Img de outro) ----
    pos = {}
    for b in beats:
        if b.get("_seg"):
            continue  # split de plano (VidRush): 2º segmento do MESMO asset é intencional
        chaves = set()
        if b.get("src"):
            chaves.add(b["src"])
        if b.get("bg"):
            chaves.add(b["bg"])
        for v in (b.get("props") or {}).values():
            for x in ([v] if isinstance(v, str) else v if isinstance(v, list) else []):
                if isinstance(x, str) and x.startswith("jobs/") \
                        and x.lower().endswith((".jpg", ".jpeg", ".png")):
                    chaves.add(x)
        for s in chaves:
            pos.setdefault(s, []).append(b["i"])
    for s, ps in pos.items():
        est = s.lower().endswith((".jpg", ".jpeg", ".png"))
        if est and len(ps) > 1:
            V.append(("R-56", ps[1], f"imagem ESTÁTICA repetida: {s[-30:]} em {ps}"))
        elif len(ps) > 2:
            V.append(("R-56", ps[2], f"vídeo 3+ usos: {s[-30:]} em {ps}"))
        elif len(ps) == 2 and (ps[1] - ps[0]) < 6:
            V.append(("R-56", ps[1], f"reuso colado (<6 beats): {s[-30:]} em {ps}"))

    # ---- A-R111 (Piter 23/07): anúncio "Number N, the X" mostra O PRODUTO —
    # nunca card de texto, nunca stock/footage genérico (Adidas no beat do NB!) ----
    _ANN = re.compile(r"\bnumber\s+(one|two|three|four|five|\d)\b[.,:]?\s", re.I)
    mont_is = {b["i"] for b in beats}
    for i2, t2 in ptxt.items():
        if t2 and _ANN.search(t2) and any(k in t2.lower() for k in desamb) and i2 not in mont_is:
            V.append(("R-111", i2, "anúncio de produto SUMIU da montagem (engolido no overlap)"))
    for b in beats:
        t = ptxt.get(b["i"], "")
        if not (t and _ANN.search(t) and any(k in t.lower() for k in desamb)):
            continue
        c = b.get("componente") or ""
        tem_produto = "__produto" in (b.get("src") or "") or any(
            isinstance(x, str) and "__produto" in x
            for v in (b.get("props") or {}).values()
            for x in ([v] if isinstance(v, str) else v if isinstance(v, list) else []))
        if eh_texto(c):
            V.append(("R-111", b["i"], f"anúncio de produto em TEXTO: {c}"))
        elif not tem_produto:
            V.append(("R-111", b["i"], f"anúncio sem foto do produto: {b['tipo']}/{c or (b.get('src') or '')[-25:]}"))

    # ---- A-G1 (VidRush 24/07): dado ÚNICO nunca em card escuro se há footage no job ----
    _CARDS_UNI = {"Graf01_CounterGlow", "Graf02_Odometer", "Graf03_DonutPercent", "Graf10_BigStatCard"}
    tem_video = any(str(b.get("src") or "").lower().endswith((".mp4", ".webm", ".mov")) for b in beats)
    if tem_video:
        for b in beats:
            if (b.get("componente") or "") in _CARDS_UNI and not b.get("_full_ok"):
                V.append(("G1", b["i"], f"dado único em CARD escuro ({b['componente']}) com footage disponível"))

    # ---- A-seq [R-109] (Piter 23/07): NUNCA 2 animações de texto adjacentes
    # (ano sobre footage nítido [R-27] lê como footage — não conta) ----
    ant = None
    for b in beats:
        c = b.get("componente") or ""
        eh = b["tipo"] == "animacao" and eh_texto(c) and not b.get("bg_nitido")
        if eh and ant:
            V.append(("R-109", b["i"], f"texto seguido de texto: {ant} -> {c}"))
        ant = c if eh else None

    # ---- A-duo [R-106]: dinamismo — min 2, máx 3 animações de PAR (2 imgs ou 2 vídeos) ----
    _DUOS = ("Img04_", "Img05_", "Img15_", "Img17_", "Duo01_", "Duo02_", "Duo03_")
    n_duos = sum(1 for b in beats if (b.get("componente") or "").startswith(_DUOS))
    if n_duos < 2:
        V.append(("R-106", "-", f"só {n_duos} animação(ões) de duo (mínimo 2)"))
    elif n_duos > 3:
        V.append(("R-106", "-", f"{n_duos} duos (máximo 3) — excesso vira ruído"))

    # ---- A8 [R-15/16]: hook limpo ----
    for b in beats:
        if b["t_ini"] < 15 and b["tipo"] == "animacao":
            c = b.get("componente") or ""
            if c == "ChapterTitle" or (eh_texto(c) and c != "Ovl10_NumberBadge"
                                       and not b.get("_cold_quote")):
                V.append(("R-15/16", b["i"], f"hook com {c}"))

    # ---- A9: refs existem ----
    for b in beats:
        for r in filter(None, [b.get("src"), b.get("bg")]):
            if not (PUB / r).exists():
                V.append(("REF", b["i"], f"arquivo ausente: {r[-40:]}"))
        for v in (b.get("props") or {}).values():
            for x in ([v] if isinstance(v, str) else v if isinstance(v, list) else []):
                if isinstance(x, str) and x.startswith("jobs/") and not (PUB / x).exists():
                    V.append(("REF", b["i"], f"prop ausente: {x[-40:]}"))

    # ---- veredito ----
    print(f"auditoria [R-76]: {len(beats)} beats | texto {t_txt:.0f}s/{m['dur_s']:.0f}s | "
          f"anos falados: {anos_falados[:4]} | na tela: {sorted(anos_na_tela)}")
    if not V:
        print("VERDE — todas as invariantes R-xx ok. Liberado pra render.")
        return 0
    print(f"\nVERMELHO — {len(V)} violação(ões):")
    for rid, i, msg in V:
        print(f"  [{rid}] beat {i}: {msg}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
