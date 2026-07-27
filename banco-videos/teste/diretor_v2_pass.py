# -*- coding: utf-8 -*-
"""DIRETOR v2 — pass de INTELIGÊNCIA DE ANIMAÇÃO sobre o plano (esquema Piter 20/07):
1. Todo beat de animação é RE-SORTEADO no registry (random com ID + seed + quota) — mata repetição.
2. Builder valida os dados; inválido -> outro ID; nada sustenta -> cadeia de natureza.
3. Injeta ANIMAÇÕES DE IMAGEM (VidRush): parte dos beats stock/atmosférico vira
   TwoImageComparison/ThreeImageReveal/... com slots que o executor preenche com T2/T1 reais.
Uso: python diretor_v2_pass.py --plano plano_beats.json --out plano_v2.json [--seed 7]
"""
import argparse
import json
import random
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).parent))
from acervo_registry import escolher, NATUREZAS  # noqa

# cadeia de fallback entre naturezas quando os dados não sustentam a preferida
# QA Piter 21/07: IMAGEM antes de texto — "mais imagens com animação, menos animação de texto"
# R-24 (QA seniors 22/07): DADO NUNCA VIRA FOTO — chart sem "imagem" na cadeia
# (beat de 15% virou polaroid de pista com '5' + caption 'Runners Died')
CADEIA = {"mapa": ["mapa", "imagem", "texto_full", "texto_overlay"],
          "chart": ["chart", "texto_full", "texto_overlay"],
          "pessoa": ["pessoa", "imagem", "texto_full", "texto_overlay"],
          "imagem": ["imagem", "texto_overlay"],
          "texto_full": ["texto_full", "texto_overlay"],
          "texto_overlay": ["texto_overlay", "texto_full"]}


def natureza_do_beat(b):
    d = b.get("dados") or {}
    comp = b.get("componente") or ""
    if any(k in d for k in ("regions", "countries", "start_location", "location")) or "Map" in comp or comp in ("RegionLocationText", "MultiCountryOutline"):
        return "mapa"
    if b.get("estrategia") == "dado" or any(k in d for k in ("number", "values", "percentage", "data")) or "Chart" in comp or comp in ("NumberCountOverlay", "CirclePercent", "PollSurveyBar"):
        return "chart"
    if any(k in d for k in ("quote",)):
        return "texto_full"
    if any(k in d for k in ("name",)) and b.get("estrategia") == "entidade":
        return "pessoa"
    if comp in ("ChapterTitle",):
        return "texto_full"
    if any(k in d for k in ("points", "bullets")):
        return "texto_overlay"
    return "texto_full"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plano", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--taxa_imagem", type=float, default=0.45, help="fração de stock não-estrito que vira animação de imagem (0.22→0.45 QA Piter 21/07)")
    a = ap.parse_args()

    plano = json.loads(Path(a.plano).read_text(encoding="utf-8"))
    beats = plano["beats"]
    quotas = {}
    last_use = {}  # comp -> último beat i (cooldown de vizinhança)
    stats = {"repick": 0, "img_anim": 0, "cadeia": 0, "mantidos": 0}

    for b in beats:
        seed = a.seed * 100003 + b["i"]
        rng = random.Random(seed)

        # ChapterTitle de seção é estrutural: mantém — MAS só se for título de verdade.
        # QA seniors 22/07: o LLM marcou ChapterTitle num beat de DADO (15% vs 34% com
        # labels/values perfeitos) e o "mantém" cego protegeu o erro -> dado virou rodapé.
        d0 = b.get("dados") or {}
        if b.get("componente") == "ChapterTitle" and d0.get("title") \
                and b.get("estrategia") != "dado" and not d0.get("values"):
            quotas["ChapterTitle"] = quotas.get("ChapterTitle", 0) + 1
            stats["mantidos"] += 1
            continue

        # 3) injeção de ANIMAÇÃO DE IMAGEM em stock/atmosférico não-estrito
        if b.get("tipo") == "stock" and not b.get("strict") and rng.random() < a.taxa_imagem:
            r = escolher("imagem", b.get("dados"), b.get("texto"), seed, quotas, max_uso=3,
                         last_use=last_use, beat_i=b["i"])
            if r:
                comp, _, n_imgs = r
                b["tipo"] = "animacao"
                b["componente"], b["img_slots"] = comp, n_imgs
                b.pop("props", None)
                stats["img_anim"] += 1
                continue

        if b.get("tipo") != "animacao":
            continue

        # 1)+2) re-sorteio com ID/quota/validação pra TODO beat de animação
        nat = natureza_do_beat(b)
        feito = False
        for j, n in enumerate(CADEIA.get(nat, ["texto_full", "texto_overlay"])):
            r = escolher(n, b.get("dados"), b.get("texto"), seed + j, quotas,
                         max_uso=(3 if n in ("texto_overlay", "texto_full") else 2),
                         last_use=last_use, beat_i=b["i"])
            if r:
                comp, props, n_imgs = r
                b["componente"] = comp
                if n_imgs > 0:
                    b["img_slots"] = n_imgs
                    b.pop("props_final", None)
                    # R-25 [F1] (QA seniors 22/07): pessoa NOMEADA ganha FOTO REAL —
                    # busca vira retrato da pessoa (Commons tem figuras públicas em CC)
                    nome_p = (b.get("dados") or {}).get("name")
                    if comp in ("CharacterCard", "CharacterKeyword") and nome_p:
                        b["busca"] = f"{nome_p} portrait photo"
                else:
                    b["props_final"] = props
                stats["repick" if j == 0 else "cadeia"] += 1
                feito = True
                break
        if not feito:  # nada sustenta -> texto simples SORTEADO (nunca vazio/default, nunca sempre o mesmo)
            tx = (b.get("texto") or "").strip()[:80] or "…"
            op = rng.choice([("Ovl06_CenterPunch", {"text": tx, "dim": 0.55}),
                             ("Texto04_EditorialSerif", {"text": tx[:90]}),
                             ("Ovl09_TickerCaption", {"text": tx[:70], "dim": 0.3})])
            b["componente"], b["props_final"] = op

    Path(a.out).write_text(json.dumps(plano, ensure_ascii=False, indent=1), encoding="utf-8")
    uso = {}
    for b in beats:
        if b.get("tipo") == "animacao":
            uso[b.get("componente")] = uso.get(b.get("componente"), 0) + 1
    print(f"v2: repick={stats['repick']} cadeia={stats['cadeia']} img_anim={stats['img_anim']} mantidos={stats['mantidos']}")
    print("uso por componente:", dict(sorted(uso.items(), key=lambda x: -x[1])))
    print("componentes distintos:", len(uso), "->", a.out)


if __name__ == "__main__":
    main()
