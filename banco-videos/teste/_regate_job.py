# -*- coding: utf-8 -*-
"""Re-gate BATCH de todos os vídeos de um job com o gate atual (6 frames, duração
inteira) — pega assets aprovados por gates antigos (2 frames) que carregam caption/
vlogger em trechos tardios. Uso: python _regate_job.py <job_dir>"""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).parent))
import executor_beats as ex

job = Path(sys.argv[1])
sc = json.loads((job / "style_card.json").read_text(encoding="utf-8")) if (job / "style_card.json").exists() else {}
ancora = sc.get("assunto_ancora", "the video subject")
tmp = job / "_tmp" / "_regate"
tmp.mkdir(parents=True, exist_ok=True)

condenados = []
vids = sorted((job / "assets").glob("*.mp4"))
print(f"re-gate: {len(vids)} vídeos do job")
for v in vids:
    beat_fake = {"busca": ancora, "i": 999,
                 "_sec_ctx": ("Judge ONLY hard defects: burned-in captions/subtitles/step labels, "
                              "tutorial UI, channel branding, a person talking/presenting to camera, "
                              "news anchor. Content topic mismatch is NOT a reason to reject here.")}
    g = ex.gate_video(v, beat_fake, tmp)
    flags = [f for f in g.get("flags", []) if f not in ("sem-resposta-vision",)]
    ok = g.get("ok") or (not g.get("raw", {}).get("talking_head") and not g.get("raw", {}).get("text_card")
                         and not g.get("raw", {}).get("watermark_visible"))
    if not ok:
        condenados.append((v.name, ",".join(flags) or g.get("reason", "")[:50]))
        print(f"  CONDENA {v.name}: {flags} {g.get('reason', '')[:60]}")
print(f"\n=== {len(condenados)} condenados de {len(vids)} ===")
(job / "_regate_resultado.json").write_text(json.dumps(condenados, ensure_ascii=False, indent=1), encoding="utf-8")
