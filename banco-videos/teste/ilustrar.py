"""Pass ADITIVO: o Gemini (CLI primário, API fallback) escolhe e PREENCHE um
recurso ilustrativo (icone/grafico/card) para cenas SEM overlay, conforme o
conteúdo da fala. Niche-agnóstico. Não mexe em texto/infográfico/mapa existentes.

Sincroniza aparece_em à fala. Escreve o campo 'ilustracao' nas cenas do timeline.json.
"""
import json
import re
import subprocess
import sys
import urllib.request
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

TESTE = Path(r"F:/Canal Dark/Aplicativo de Edição/banco-videos/teste")
TIMELINE = TESTE / "timeline.json"
WORDS = TESTE / "words.json"
CATALOGO = Path(r"D:/Meu Drive/canal_dark_footage_stock/catalogo.json")
CREDS = Path(r"F:/Canal Dark/Aplicativo de Edição/video-automator/credentials.json")

ICON_KEYS = "ideia, mente, saude, dinheiro, tempo, crescimento, pessoas, meta, seguranca, risco, lancamento, atencao"


def norm(s):
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def _parse_arr(txt):
    a, b = txt.find("["), txt.rfind("]")
    if a >= 0 and b > a:
        try:
            return json.loads(txt[a:b + 1])
        except Exception:
            return None
    return None


def _lang(cenas):
    """Idioma das falas (marcadores distintivos; default English). Evita o Gemini cair em PT."""
    t = " ".join(c.get("texto", "") for c in cenas).lower()
    if any(ch in t for ch in "ãõ") or "ção" in t or " não " in t or " você " in t or " uma " in t:
        return "Portuguese"
    if "ñ" in t or "¿" in t or " está " in t or " qué " in t or " los " in t:
        return "Spanish"
    if any(ch in t for ch in "äöüß") or " und " in t or " der " in t or " ein " in t:
        return "German"
    return "English"


def _prompt(cenas):
    linhas = "  ".join(
        f"[{c['idx']}] SAYS: {c['texto'].replace(chr(34), '')} | FOOTAGE SHOWS: {c.get('footage', '?').replace(chr(34), '')}"
        for c in cenas)
    lang = _lang(cenas)
    return (
        f"LANGUAGE RULE (CRITICAL): write EVERY piece of output text (titulo, sub, legenda, label, termo, autor, "
        f"passos...) STRICTLY in {lang}. Never translate to another language. "
        "You are the illustrative editor of a video (ANY niche). Each scene ALREADY plays B-roll FOOTAGE (described). "
        "Add an animated illustrative element ONLY when it ADDS information the footage does NOT already show: "
        "abstract ideas the camera cannot film, DATA/statistics, comparisons, processes, named facts, definitions. "
        "If the footage already depicts what is being said (e.g. SAYS meditation and FOOTAGE SHOWS a person meditating, "
        "or SAYS stars and FOOTAGE SHOWS a starry sky), return null — do NOT add a redundant icon. "
        "Prefer graficos and cards (they explain) over icones. Make them count: most should be tamanho grande. "
        "Whenever a scene states a NUMBER, statistic, count, figure, date-quantity or a NAMED LIST, you SHOULD add a "
        "grafico (for numbers) or card (for lists/facts) — these are high value, this topic is data-rich. "
        "Aim for roughly 1 in 3 eligible scenes; never two consecutive. For any list, include ONLY items literally "
        "spoken in that line (never invent or guess extra names). "
        "Return ONLY a JSON array. Each item has keys scene (the number) and ilustracao (an object or null). "
        "The ilustracao object has tipo (icone, grafico or card), pos (left, right, center or lower) and "
        "tamanho (grande or medio; prefer grande). "
        "If tipo is icone: add nome (one of: " + ICON_KEYS + ") that matches a CONCEPT named in the scene, and "
        "legenda (1 to 2 words). Use icone when a concrete idea/object/feeling is mentioned. "
        "If tipo is grafico: use it ONLY when the scene states a NUMBER, statistic, comparison or trend. Add "
        "chart (bar, line, donut, stat, comparison or progress) and dados. dados by chart: bar uses valores (a "
        "list where each item has label and valor) plus destaque (index of the highlighted bar); line uses "
        "valores (a list of numbers); donut uses valor (0 to 100) and label; stat uses valor (a number), sufixo "
        "(like M, %, x or empty) and label; comparison uses a and b (each with label and valor); progress uses "
        "valor (0 to 100) and label. Use the REAL numbers and words from the narration. "
        "If tipo is card: add variante (lowerthird, quote, definition, steps, beforeafter or vs) and conteudo. "
        "conteudo by variante: lowerthird uses titulo and sub; quote uses texto and autor; definition uses termo "
        "and texto; steps uses passos (a list of 3 to 4 short labels); beforeafter uses antes and depois; vs uses "
        "a and b. Keep all text SHORT. CRITICAL: the element MUST be grounded in the EXACT words/facts of that "
        "scene's line — never invent a thematic concept or define a word that is NOT spoken in the line. A "
        "definition is only allowed when a specific TERM is actually said and benefits from being defined. When "
        "in doubt, return null. Write all text in the SAME LANGUAGE as the lines. Scenes: " + linhas
    )


def gemini(cenas):
    from gemini_api import gemini_arr
    arr = gemini_arr(_prompt(cenas), 200)   # API (8 chaves) + retry/repair se JSON corrompido -> CLI fallback
    return arr if arr is not None else []


def anchor(c, words, spec):
    """aparece_em: gráfico sincroniza no 1º número falado; resto, início + 0.4s."""
    sw = [w for w in words if w["start"] >= c["inicio"] - 0.05 and w["start"] < c["fim"]]
    if spec.get("tipo") == "grafico":
        for w in sw:
            if any(ch.isdigit() for ch in w["word"]):
                return round(max(c["inicio"], w["start"] - 0.3), 2)
    return round(c["inicio"] + 0.4, 2)


def in_window(c, segs, dur_default):
    """True se a cena sobrepõe qualquer segmento (mapa/pessoa/data)."""
    for s in segs:
        if c["inicio"] < s["inicio"] + s.get("dur", dur_default) and c["fim"] > s["inicio"]:
            return True
    return False


def main():
    tl = json.load(open(TIMELINE, encoding="utf-8"))
    words = json.load(open(WORDS, encoding="utf-8")) if WORDS.exists() else []
    mapas = tl.get("mapas") or []
    pessoas = tl.get("pessoas") or []
    datas = tl.get("datas") or []
    by_idx = {c["idx"]: c for c in tl["cenas"]}

    # descrição do footage de cada cena (pra evitar ilustração redundante)
    cat_desc = {}
    if CATALOGO.exists():
        for cl in json.load(open(CATALOGO, encoding="utf-8")):
            cat_desc[cl["id"]] = cl.get("descricao_visual", "")
    for c in tl["cenas"]:
        # on-demand: o stock_query já descreve o footage; senão usa o catálogo
        c["footage"] = c.get("stock_query") or cat_desc.get(c.get("clip_id"), "")

    # elegíveis: sem texto/infográfico e fora de janela de mapa/pessoa/data (evita overlap)
    elig = [c for c in tl["cenas"]
            if not c.get("texto_impacto") and not c.get("infografico")
            and not in_window(c, mapas, 5.5) and not in_window(c, pessoas, 3.6) and not in_window(c, datas, 2.6)]
    print(f"=== ilustrar: {len(elig)}/{len(tl['cenas'])} cenas elegíveis ===")
    gen = gemini(elig)
    by_scene = {int(o["scene"]): o.get("ilustracao") for o in gen if "scene" in o}

    # limpa ilustrações de runs anteriores (este pass é o ÚNICO dono do campo) -> sem card stale
    for c in tl["cenas"]:
        c.pop("ilustracao", None)
    add = 0
    for idx, spec in by_scene.items():
        c = by_idx.get(idx)
        if not c or not spec or not isinstance(spec, dict) or not spec.get("tipo"):
            continue
        # não-adjacente: pula se vizinho já tem qualquer overlay
        prev, nxt = by_idx.get(idx - 1), by_idx.get(idx + 1)
        busy = lambda x: x and (x.get("texto_impacto") or x.get("infografico") or x.get("ilustracao"))
        if busy(prev) or busy(nxt):
            continue
        c["ilustracao"] = spec
        c["aparece_em"] = anchor(c, words, spec)
        add += 1

    for c in tl["cenas"]:
        c.pop("footage", None)  # campo temporário, não persiste
    json.dump(tl, open(TIMELINE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"OK: +{add} ilustrações")
    for c in tl["cenas"]:
        il = c.get("ilustracao")
        if il:
            det = il.get("nome") or il.get("chart") or il.get("variante")
            print(f"  {c['inicio']:>6.1f}s  {il['tipo']:<8} {det:<12} pos={il.get('pos')}  «{c['texto'][:42]}»")


if __name__ == "__main__":
    main()
