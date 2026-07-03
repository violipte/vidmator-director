"""Pass ADITIVO: o Gemini escolhe COMO cada imagem se MOVE na tela (template de apresentação),
por contexto da fala. Escreve 'presentacao' {tipo, extras?, foco?} nas cenas de IMAGEM do timeline.json.
Default = kenburns (zoom lento). Seletivo: ~1 em 3 ganha template especial, nunca 2 seguidos.

Templates: lupa | spotlight | polaroid | film | parallax | reveal | split | grid | kenburns.
split/grid precisam de imagens extra -> puxa de cenas-imagem vizinhas; se faltar, cai pra parallax/kenburns.
"""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
TESTE = Path(r"F:/Canal Dark/Aplicativo de Edição/banco-videos/teste")
TIMELINE = TESTE / "timeline.json"
VALID = {"lupa", "spotlight", "polaroid", "film", "parallax", "reveal", "split", "grid", "kenburns"}

TEMPLATE_DESC = {
    "lupa": "lupa (magnifier inspects a detail — documents, faces, maps, clues, 'look closer')",
    "spotlight": "spotlight (darken all but a moving focus — suspense, directing the eye)",
    "polaroid": "polaroid (photo in a polaroid frame that drops in — memory, personal, historical, 'evidence')",
    "film": "film (old film-strip frame w/ jitter — past eras, vintage, found-footage)",
    "parallax": "parallax (pseudo-3D depth zoom — give life to a flat scenic photo)",
    "reveal": "reveal (image revealed grayscale->color by a sweep — dramatic reveal)",
    "split": "split (two images side by side — comparison, before/after, duality/vs)",
    "grid": "grid (2x2 mosaic — a collection, many things, a list)",
}


def _prompt(cenas, pool, freq):
    linhas = "  ".join(f"[{c['idx']}] {c['texto'][:90].replace(chr(34), '')}" for c in cenas)
    opts = " | ".join(TEMPLATE_DESC[t] for t in pool if t in TEMPLATE_DESC)
    um_em = max(2, round(1 / max(freq, 0.05)))
    return (
        "You are the visual editor of a faceless video (niche-tuned). Each scene below shows a STILL IMAGE as B-roll. "
        "Choose HOW each image MOVES, picking a template ONLY when it adds meaning to the words; otherwise 'kenburns' (slow zoom default). "
        "Allowed templates for THIS niche: " + opts + " | kenburns. "
        f"RULES: about 1 in {um_em} scenes gets a NON-kenburns template; the rest kenburns; NEVER two non-kenburns in a row; "
        "split/grid only for genuine comparison/collection lines (rare). Ground every choice in the scene's words. "
        "Return ONLY a JSON array of objects {scene: <the number>, tipo: <one template word>}. Scenes: " + linhas
    )


def main():
    tl = json.load(open(TIMELINE, encoding="utf-8"))
    cenas = tl["cenas"]
    img_cenas = [c for c in cenas if c.get("media_tipo") == "imagem"]
    print(f"=== apresentar: {len(img_cenas)}/{len(cenas)} cenas de imagem ===")
    if not img_cenas:
        print("OK: nenhuma imagem -> nada a fazer")
        return

    from preset import carregar
    from gemini_api import gemini_arr
    P = carregar(tl)
    pool = [t for t in P.get("apresentacao_pool", []) if t in TEMPLATE_DESC] or list(TEMPLATE_DESC)
    poolset = set(pool) | {"kenburns"}
    freq = float(P.get("apresentacao_freq", 0.33))
    print(f"  preset nicho={P['_nicho']} | pool={pool} | freq~{freq}")
    arr = gemini_arr(_prompt(img_cenas, pool, freq), 180) or []
    escolha = {}
    for o in arr:
        try:
            t = str(o.get("tipo", "")).lower().strip()
            if "scene" in o and t in VALID:
                escolha[int(o["scene"])] = t if t in poolset else "kenburns"  # fora do pool do nicho -> kenburns
        except Exception:
            continue

    # clip_ids das cenas-imagem (p/ extras de split/grid; preparar mapeia cid->rel)
    img_ids = [(c["idx"], c.get("clip_id")) for c in img_cenas if c.get("clip_id")]

    def vizinhos(idx, n):
        out = []
        for j, cid in img_ids:
            if j != idx and cid:
                out.append(cid)
            if len(out) >= n:
                break
        return out

    prev_especial = False
    aplicados = 0
    dist = {}
    for c in img_cenas:
        t = escolha.get(c["idx"], "kenburns")
        if t != "kenburns" and prev_especial:   # nunca 2 especiais seguidos
            t = "kenburns"
        extras = None
        if t == "split":
            v = vizinhos(c["idx"], 1)
            if v:
                extras = v
            else:
                t = "parallax"
        elif t == "grid":
            v = vizinhos(c["idx"], 3)
            if len(v) >= 3:
                extras = v
            else:
                t = "kenburns"
        c["presentacao"] = {"tipo": t, "extras": extras}
        prev_especial = t != "kenburns"
        dist[t] = dist.get(t, 0) + 1
        if t != "kenburns":
            aplicados += 1

    json.dump(tl, open(TIMELINE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"OK: {aplicados} cenas com template especial | distribuição: {dist}")


if __name__ == "__main__":
    main()
