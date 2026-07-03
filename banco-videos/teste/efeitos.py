"""Pass ADITIVO: o Gemini marca o HUMOR de cada cena (tenso/frio/nostalgia/
revelacao/misterioso/neutro). O BrollTest mapeia humor -> efeito (wash de cor,
CRT/VHS, static, glitch). SELETIVO: a maioria é 'neutro' (descanso visual);
só os momentos fortes ganham efeito. Escreve 'mood' nas cenas do timeline.json.
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
CREDS = Path(r"F:/Canal Dark/Aplicativo de Edição/video-automator/credentials.json")
MOODS = {"tenso", "frio", "nostalgia", "revelacao", "misterioso", "neutro"}
MOOD_DESC = {
    "tenso": "tenso (tension/violence/danger -> red wash)",
    "frio": "frio (death/cold/fear -> cold blue)",
    "nostalgia": "nostalgia (the past/old/archival -> CRT VHS look)",
    "revelacao": "revelacao (a shocking reveal/hard fact -> glitch flash)",
    "misterioso": "misterioso (eerie/supernatural/unknown -> subtle CRT)",
}


def _prompt(cenas, pool, intensidade):
    linhas = "  ".join(f"[{c['idx']}] {c['texto'].replace(chr(34), '')}" for c in cenas)
    opts = ", ".join(MOOD_DESC[m] for m in pool if m in MOOD_DESC)
    pct = round(intensidade * 100)
    return (
        "You are the colorist of a premium video (niche-tuned). Tag each scene with ONE mood that drives a visual effect. "
        "Allowed moods for THIS niche: " + opts + ", neutro (calm/explaining -> NO effect). "
        f"BE SELECTIVE: aim for AT MOST ~{pct}% non-neutro (the rest neutro), avoid long runs of the same mood. "
        "Match the mood to what the line evokes. Return ONLY a JSON array of objects with keys scene and mood. Scenes: " + linhas
    )


def gemini(cenas, pool, intensidade):
    from gemini_api import gemini_arr
    arr = gemini_arr(_prompt(cenas, pool, intensidade), 180)
    return arr if arr is not None else []


def main():
    from preset import carregar
    tl = json.load(open(TIMELINE, encoding="utf-8"))
    cenas = tl["cenas"]
    P = carregar(tl)
    pool = [m for m in P.get("moods_pool", []) if m in MOOD_DESC] or list(MOOD_DESC)
    poolset = set(pool) | {"neutro"}
    intensidade = float(P.get("efeito_intensidade", 0.4))
    print(f"  preset nicho={P['_nicho']} | moods={pool} | intensidade~{intensidade}")
    by_idx = {c["idx"]: c for c in cenas}
    res = gemini(cenas, pool, intensidade)
    for o in res:
        c = by_idx.get(o.get("scene"))
        m = (o.get("mood") or "neutro").strip().lower()
        if c and m in MOODS:
            c["mood"] = m if m in poolset else "neutro"   # mood fora do nicho -> neutro
    for c in cenas:
        c.setdefault("mood", "neutro")
    # CAP de intensidade: se passou do alvo, derruba o excedente (espalhado) p/ neutro
    limite = max(1, round(intensidade * len(cenas)))
    fortes = [c for c in cenas if c.get("mood") != "neutro"]
    if len(fortes) > limite:
        manter = set(id(fortes[round(i * (len(fortes) - 1) / (limite - 1))]) for i in range(limite)) if limite > 1 else {id(fortes[0])}
        for c in fortes:
            if id(c) not in manter:
                c["mood"] = "neutro"
    n = sum(1 for c in cenas if c.get("mood") != "neutro")
    json.dump(tl, open(TIMELINE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    from collections import Counter
    dist = Counter(c.get("mood") for c in cenas)
    print(f"OK: {n} cenas com efeito | distribuição: {dict(dist)}")


if __name__ == "__main__":
    main()
