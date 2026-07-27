# -*- coding: utf-8 -*-
"""DIRETOR / Beat-Planner — Stage 1+2 (o cérebro do VidMator).
Roteiro narrado (transcript com timestamps) -> plano_beats.json:
  Stage 1: SECTIONS  — divide em capítulos + color-wash por seção (LLM)
  Stage 2: BEAT PLAN — por seção, cada trecho vira beats com estratégia/tipo/
           dados/busca/fallback (LLM), seguindo as 5 regras da VidRush
           (DECUPAGEM_VIDRUSH.md) e o schema de ARQUITETURA_DIRETOR.md.

Uso:
  python diretor.py --transcript "<transcript_timed.txt>" [--out plano_beats.json] [--teto web]

Validação de ouro: rodar no roteiro REAL da Hilux e comparar com a decupagem.
"""
import argparse
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).parent))
from gemini_api import gemini_arr  # rotação 8 chaves + fallback GPT/Claude + reparo JSON

# ---------- catálogo de componentes (as 54 + montagem) por finalidade ----------
COMPONENTES = {
    "charts": ["PercentageBarChart", "PieChart", "LineChart", "GrowingBarChart", "BarChartComparison",
               "CirclePercent", "NumberCountOverlay", "StockChart", "PollSurveyBar"],
    "mapas": ["MultiCountryOutline", "SatelliteDrawPath", "MapRoute", "SatelliteLocationPin",
              "RegionLocationText", "CountryCharacterMap"],
    "texto": ["SentenceHighlight", "TextReveal", "TitleDescription", "QuoteCard", "ChapterTitle",
              "DisplayText", "DateLocationOverlay", "CaptionTextOverlay", "DualImpactSentence",
              "SingleSentenceTextSlide", "OneWordCallout", "BulletPointOverlay"],
    "pessoas": ["CharacterCard", "CharacterKeyword", "ObjectTitle", "NodeHierarchy", "SubjectTitleCard",
                "DetectiveBoard", "InstagramConversation", "PriceCallOut", "ObjectDualStat"],
    "imagens": ["TwoImageComparison", "ThreeImageReveal", "FourImageSlideshow", "MultiImageCutText",
                "DualImageOnGrid", "SplitScreenComparison", "FourImageCaptionGrid", "FiveTextListicle",
                "BeforeAfterArrow", "ImageTextAnnotation", "WebsiteScreenshotReveal", "ArticleNewsCard",
                "LogoFlagGrid", "ImageCallout", "PaperMovingTransparentObject", "IconGrid", "IconLabels"],
    "montagem": ["FramedGridMontage"],
}
TODOS_COMP = {c for grupo in COMPONENTES.values() for c in grupo}
TIPOS = {"footage_video", "footage_imagem", "ilustracao", "animacao", "stock"}
ESTRATEGIAS = {"literal", "entidade", "dado", "peca", "abstrato", "atmosferico"}
WASHES = ["none", "teal", "amarelo", "vermelho", "dourado", "azul_frio"]


# ---------- parse do transcript ([MM:SS] texto por linha) ----------
def parse_transcript(path):
    segs = []
    for ln in Path(path).read_text(encoding="utf-8").splitlines():
        m = re.match(r"\[(\d+):(\d{2})\]\s*(.+)", ln.strip())
        if not m:
            continue
        t = int(m.group(1)) * 60 + int(m.group(2))
        txt = m.group(3).strip()
        # descarta alucinação de outro/silêncio (www., Thanks for watching)
        if re.search(r"www\.|thanks for watching", txt, re.I):
            continue
        segs.append({"t": float(t), "texto": txt})
    # end = start do próximo (último ganha +6s)
    for i, s in enumerate(segs):
        s["t_fim"] = segs[i + 1]["t"] if i + 1 < len(segs) else s["t"] + 6.0
    return segs


# ---------- Stage 1: SECTIONS ----------
def stage1_sections(segs):
    dur_total = segs[-1]["t_fim"]
    linhas = "\n".join(f"[{int(s['t'])//60:02d}:{int(s['t'])%60:02d}] {s['texto']}" for s in segs)
    prompt = (
        "You are a documentary video editor. Split this narration into 5-9 STRUCTURAL SECTIONS "
        "(cold open, framework/thesis, then thematic chapters, counterpoint, conclusion). "
        f"TOTAL DURATION = {int(dur_total)} seconds — every t_ini/t_fim MUST be within 0-{int(dur_total)}; "
        "use the [MM:SS] stamps of the lines (convert to seconds), NEVER invent times beyond the last line. "
        "For EACH section return a JSON object: i (int, 0-based), titulo (short English title), "
        "t_ini (seconds, int), t_fim (seconds, int), wash (one of: " + ", ".join(WASHES) + " — a color "
        "mood for the section; vary them; use 'none' for cold open), title_card (bool — true if the "
        "section deserves an on-screen chapter card; cold open/conclusion = false). "
        "Sections must cover the whole narration contiguously, no gaps/overlaps. "
        "Return ONLY a JSON array.\n\nNARRATION:\n" + linhas
    )
    arr = gemini_arr(prompt, timeout=150)
    if not arr:
        raise RuntimeError("Stage 1 falhou (LLM sem resposta)")
    secs = []
    for s in arr:
        try:
            t0, t1 = float(s["t_ini"]), float(s["t_fim"])
        except Exception:
            continue
        if t0 >= dur_total:          # seção alucinada além do fim -> descarta
            continue
        t1 = min(t1, dur_total)      # clamp no fim real
        if t1 <= t0:
            continue
        secs.append({"i": int(s.get("i", len(secs))), "titulo": str(s["titulo"])[:60],
                     "t_ini": t0, "t_fim": t1,
                     "wash": s.get("wash") if s.get("wash") in WASHES else "none",
                     "title_card": bool(s.get("title_card"))})
    secs.sort(key=lambda x: x["t_ini"])
    # costura: sem buracos/sobreposição; última seção fecha no fim real
    for i, s in enumerate(secs):
        s["i"] = i
        if i + 1 < len(secs):
            s["t_fim"] = secs[i + 1]["t_ini"]
    if secs:
        secs[-1]["t_fim"] = dur_total
    # seção gigante (>210s) = LLM não subdividiu -> quebra no meio em 2 (mantém wash/título + " II")
    quebradas = []
    for s in secs:
        if s["t_fim"] - s["t_ini"] > 210:
            meio = round((s["t_ini"] + s["t_fim"]) / 2)
            quebradas.append({**s, "t_fim": float(meio)})
            quebradas.append({**s, "titulo": s["titulo"] + " II", "t_ini": float(meio), "title_card": False})
        else:
            quebradas.append(s)
    for i, s in enumerate(quebradas):
        s["i"] = i
    return quebradas


# ---------- Stage 2: BEAT PLAN (por seção) ----------
_REGRAS = """STRATEGY RULES (how a documentary line becomes a visual — follow strictly):
- literal: the line describes a FILMABLE action/object (a test, an engine, driving, war footage) -> tipo footage_video (or footage_imagem for static/historical). busca = specific English search query. strict=true ONLY if the exact model/brand must be visible.
- entidade: the line NAMES a place/person/org/route -> tipo animacao with a map/label/card component (mapas: MapRoute, MultiCountryOutline, SatelliteLocationPin, RegionLocationText; person: CharacterCard/SubjectTitleCard; org list: LogoFlagGrid). dados = the names/coords/values to display. For a NAMED PERSON, dados MUST use the key "name" (e.g. {"name": "Jeff Galloway", "title": "Olympian"}) — "name" triggers the real-portrait pipeline; "title" alone does NOT.
- dado: the line contains NUMBERS/statistics/comparisons -> tipo animacao with a chart (BarChartComparison for X vs Y, LineChart for trend, GrowingBarChart for growth over years, NumberCountOverlay for a single big number, PercentageBarChart/CirclePercent for percentages). dados = the actual numbers/labels FROM THE LINE. NEVER assign ChapterTitle (or any title card) to a data beat — if dados carry values/labels, the beat is a CHART, period.
- peca: the line discusses a mechanical COMPONENT/engineering detail -> tipo ilustracao (technical diagram/cutaway/blueprint, service-manual style). busca = English description of the diagram to generate/find.
- abstrato: conceptual line with nothing filmable ("engineers managed", "philosophy of...") -> tipo stock, BUT busca MUST be atmospheric b-roll OF THE VIDEO'S SUBJECT/NICHE (subject + mood, e.g. "vintage harley engine chrome detail moody workshop"). NEVER a literal visualization of the concept — no "person listening", "lecture hall", "old wisdom document", "abstract concept X". Stock engines take those literally and return garbage.
- atmosferico: breathing room / transition -> tipo footage_video or stock (landscape/mood). busca = mood query.
QUOTES: if the line quotes/attributes a claim to a named person -> animacao QuoteCard (dados = quote + author).
DATA FIDELITY (CRITICAL): NEVER invent numbers, countries, percentages or labels — copy them EXACTLY from the
narration line. If the line has no number, do NOT use a number component. Never write placeholder text like
"(example)". Omit dados fields you cannot ground in the text.
ORDINALS ARE NOT DATA: idiomatic/ordinal numbers ("the number one enemy", "one thing", "rule two",
"number five" in a countdown) are NOT statistics — estrategia must NOT be 'dado' for them and they never
get a chart. Only measured quantities (percentages, counts, weights, years, comparisons) are data.
VARIETY: do not use the same componente more than 3 times per section — rotate equivalents.
TARGET MIX (VidRush reference — steer toward it): ~45% footage, ~20% ilustracao, ~15% animacao, ~20% stock.
Prefer 'literal'+footage whenever the line mentions the vehicle, its parts in action, terrain, or events —
'abstrato'+stock is a LAST resort for truly unfilmable concepts, not a default.
FALLBACK (mandatory for every footage/ilustracao/stock beat): array of 1-2 alternatives, e.g. ["animacao:NumberCountOverlay","atmosferico"] — the chain used if footage fails the vision gate. Animacao beats need no fallback."""


def stage2_beats(segs, secao, use_start):
    linhas = "\n".join(f"({s['t']:.0f}-{s['t_fim']:.0f}s) {s['texto']}" for s in segs)
    comp_list = json.dumps(COMPONENTES)
    prompt = (
        "You are the DIRECTOR of a faceless documentary video (VidRush style). For the narration lines "
        "below (section: '" + secao["titulo"] + "'), produce the VISUAL BEAT PLAN. Each narration line "
        "becomes 1-3 beats (a beat = one visual, 3-8s). Beats must tile each line's time range "
        "contiguously (use the given second ranges; do not invent times outside them).\n\n"
        + _REGRAS + "\n\n"
        "AVAILABLE COMPONENTS (use EXACT names for componente): " + comp_list + "\n\n"
        "Return ONLY a JSON array of beats: {t_ini (s,int), t_fim (s,int), texto (short excerpt of the "
        "line), estrategia (literal|entidade|dado|peca|abstrato|atmosferico), tipo (footage_video|"
        "footage_imagem|ilustracao|animacao|stock), componente (exact name or null), dados (object or "
        "null — REAL values from the narration), busca (English query or null), strict (bool), "
        "entidades (object or null: lugar/pessoa/org/numero), fallback (array of strings, [] for animacao)}.\n\n"
        "NARRATION LINES:\n" + linhas
    )
    arr = gemini_arr(prompt, timeout=200)
    if not arr:
        return []
    beats = []
    for b in arr:
        try:
            t0, t1 = float(b["t_ini"]), float(b["t_fim"])
        except Exception:
            continue
        if t1 <= t0:
            continue
        tipo = b.get("tipo") if b.get("tipo") in TIPOS else "stock"
        estr = b.get("estrategia") if b.get("estrategia") in ESTRATEGIAS else "abstrato"
        comp = b.get("componente")
        if comp is not None and comp not in TODOS_COMP:
            comp = None
        if tipo == "animacao" and comp is None:
            comp = "DisplayText"  # animacao sem componente válido -> texto simples
        fb = b.get("fallback") or []
        if tipo in ("footage_video", "footage_imagem", "ilustracao", "stock") and not fb:
            fb = ["animacao:DisplayText", "atmosferico"]
        beats.append({
            "t_ini": round(t0, 2), "t_fim": round(t1, 2), "dur": round(t1 - t0, 2),
            "texto": str(b.get("texto", ""))[:160],
            "estrategia": estr, "tipo": tipo, "componente": comp,
            "dados": b.get("dados"), "busca": b.get("busca"),
            "strict": bool(b.get("strict")), "entidades": b.get("entidades"),
            "fallback": fb,
        })
    beats.sort(key=lambda x: x["t_ini"])
    return beats


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--transcript", required=True)
    ap.add_argument("--out", default="")
    ap.add_argument("--teto", default="web", choices=["stock", "cc_pd", "web"])
    a = ap.parse_args()

    segs = parse_transcript(a.transcript)
    print(f"transcript: {len(segs)} segmentos ({segs[0]['t']:.0f}s -> {segs[-1]['t_fim']:.0f}s)")

    print("=== Stage 1: sections ===")
    secs = stage1_sections(segs)
    for s in secs:
        print(f"  [{s['i']}] {s['titulo']}  {s['t_ini']:.0f}-{s['t_fim']:.0f}s  wash={s['wash']}  card={s['title_card']}")

    print("=== Stage 2: beat plan (por seção) ===")
    all_beats = []
    for sec in secs:
        seg_sec = [s for s in segs if sec["t_ini"] <= s["t"] < sec["t_fim"]]
        if not seg_sec:
            continue
        beats = stage2_beats(seg_sec, sec, sec["t_ini"])
        for b in beats:
            b["secao"] = sec["i"]
            b["tier_teto"] = a.teto
            b["tratamento"] = {"wash": sec["wash"]}
        # title card da seção vira um beat próprio no início
        if sec["title_card"] and beats:
            all_beats.append({
                "t_ini": sec["t_ini"], "t_fim": min(sec["t_ini"] + 3.0, beats[0]["t_ini"] + 3.0),
                "dur": 3.0, "texto": sec["titulo"], "estrategia": "entidade", "tipo": "animacao",
                "componente": "ChapterTitle", "dados": {"title": sec["titulo"], "number": sec["i"]},
                "busca": None, "strict": False, "entidades": None, "fallback": [],
                "secao": sec["i"], "tier_teto": a.teto, "tratamento": {"wash": sec["wash"]},
            })
        all_beats.extend(beats)
        print(f"  seção {sec['i']} ({sec['titulo']}): {len(beats)} beats")

    for i, b in enumerate(all_beats):
        b["i"] = i

    out = Path(a.out) if a.out else Path(a.transcript).parent / "plano_beats.json"
    out.write_text(json.dumps({"secoes": secs, "beats": all_beats}, ensure_ascii=False, indent=2), encoding="utf-8")

    # ---- resumo / mix ----
    n = len(all_beats) or 1
    mix = {}
    for b in all_beats:
        mix[b["tipo"]] = mix.get(b["tipo"], 0) + 1
    print(f"\n=== PLANO: {len(all_beats)} beats, {len(secs)} seções -> {out} ===")
    for t, c in sorted(mix.items(), key=lambda x: -x[1]):
        print(f"  {t:16} {c:4}  ({100*c/n:.0f}%)")
    fv = mix.get("footage_video", 0) + mix.get("footage_imagem", 0)
    an = mix.get("animacao", 0)
    il = mix.get("ilustracao", 0)
    st = mix.get("stock", 0)
    print(f"  [VidRush alvo ≈ footage 45% | ilustração 20% | animação 15% | stock 20%]")
    print(f"  [este plano  ≈ footage {100*fv//n}% | ilustração {100*il//n}% | animação {100*an//n}% | stock {100*st//n}%]")


if __name__ == "__main__":
    main()
