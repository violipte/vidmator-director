# -*- coding: utf-8 -*-
"""MODO 100% VEO/NANO BANANA (v3-gen, 29/07) — gera o LOTE de prompts do plano.

Para cada beat de vídeo (footage_video/stock) => prompt VEO 3.1 (8s, cinematic,
mood do style_card). Para cada beat de imagem (ilustracao/footage_imagem) =>
prompt Nano Banana. Saída: <job>/veo_lote.json + veo_lote.md (pra colar no Flow).

O download deve ser salvo como bNNN.mp4 / bNNN.jpg (o veo_ingest.py casa por nome).

Uso: python veo_lote.py --job <dir> --plano plano.json [--secao N] [--max N]
"""
import argparse
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

REGRAS_V = ("Cinematic, photorealistic, natural motion. No captions, no subtitles, "
            "no on-screen text, no logos, no watermarks, no people talking to camera.")
REGRAS_I = ("Photorealistic still, cinematic composition, natural light. "
            "No text, no logos, no watermarks.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--job", required=True)
    ap.add_argument("--plano", required=True)
    ap.add_argument("--secao", type=int, default=None, help="limita a uma seção")
    ap.add_argument("--max", type=int, default=0, help="limita o nº de prompts (piloto)")
    a = ap.parse_args()

    job = Path(a.job)
    plano = json.loads(Path(a.plano).read_text(encoding="utf-8"))
    sc = {}
    if (job / "style_card.json").exists():
        sc = json.loads((job / "style_card.json").read_text(encoding="utf-8"))
    mood = ", ".join(sc.get("mood_words") or [])
    lote = []
    for b in plano.get("beats", []):
        if a.secao is not None and b.get("secao") != a.secao:
            continue
        busca = (b.get("busca") or "").replace(" OR ", ", ")
        if not busca:
            continue
        base_b = {"i": b["i"], "t_ini": b.get("t_ini", 0), "t_fim": b.get("t_fim", 0),
                  "secao": b.get("secao", 0)}
        if b.get("tipo") in ("footage_video", "stock"):
            lote.append({**base_b, "tipo": "video", "arquivo": f"b{b['i']:03d}.mp4",
                         "prompt": f"{busca}. Mood: {mood}. {REGRAS_V}"})
        elif b.get("tipo") in ("ilustracao", "footage_imagem"):
            lote.append({**base_b, "tipo": "imagem", "arquivo": f"b{b['i']:03d}.jpg",
                         "prompt": f"{busca}. Mood: {mood}. {REGRAS_I}"})
        if a.max and len(lote) >= a.max:
            break
    (job / "veo_lote.json").write_text(json.dumps(lote, ensure_ascii=False, indent=1),
                                       encoding="utf-8")
    md = [f"# Lote VEO/Nano — {job.name} ({len(lote)} gerações, 0 créditos)", ""]
    for x in lote:
        md += [f"## {x['arquivo']} ({x['tipo']})", "```", x["prompt"], "```", ""]
    (job / "veo_lote.md").write_text("\n".join(md), encoding="utf-8")
    nv = sum(1 for x in lote if x["tipo"] == "video")
    print(f"lote: {len(lote)} prompts ({nv} VEO + {len(lote) - nv} Nano) -> {job / 'veo_lote.json'}")


if __name__ == "__main__":
    main()
