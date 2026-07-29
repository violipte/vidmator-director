# -*- coding: utf-8 -*-
"""MODO 100% VEO (v3-gen, 29/07) — ingere os clipes/imagens APROVADOS (keep/) no job.

Casa por NOME (bNNN.mp4/jpg do veo_lote) com o veo_lote.json, copia pro assets
com o padrão do executor (bNNN__T0__veo.<ext>) e escreve resolvido/bNNN.json.
Só aceita o que está em keep/ (rubric do curador VEO = gate).

Uso: python veo_ingest.py --job <dir> --keep <pasta keep>
"""
import argparse
import json
import re
import shutil
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--job", required=True)
    ap.add_argument("--keep", required=True)
    a = ap.parse_args()

    job = Path(a.job)
    keep = Path(a.keep)
    lote = {x["arquivo"]: x for x in json.loads((job / "veo_lote.json").read_text(encoding="utf-8"))}
    (job / "assets").mkdir(exist_ok=True)
    (job / "resolvido").mkdir(exist_ok=True)
    n_ok = 0
    for f in sorted(keep.glob("b*.*")):
        m = re.match(r"^(b\d{3})\.(mp4|jpg|jpeg|png)$", f.name, re.I)
        if not m or f.name not in lote:
            continue
        x = lote[f.name]
        dest = job / "assets" / f"{m.group(1)}__T0__veo.{m.group(2).lower()}"
        if not dest.exists():
            shutil.copy2(f, dest)
        (job / "resolvido" / f"{m.group(1)}.json").write_text(json.dumps({
            "i": x["i"], "t_ini": x.get("t_ini", 0), "t_fim": x.get("t_fim", 0),
            "secao": x.get("secao", 0), "status": "ok", "arquivo": str(dest), "tier": 0,
            "fonte": "veo", "tipo": "stock" if x["tipo"] == "video" else "ilustracao",
            "busca": x["prompt"][:120]}, ensure_ascii=False), encoding="utf-8")
        n_ok += 1
        print(f"  {f.name} -> {dest.name}")
    print(f"ingest: {n_ok} assets VEO/Nano no job (tier 0, fonte veo)")


if __name__ == "__main__":
    main()
