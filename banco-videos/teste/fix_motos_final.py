"""Patch final do vídeo de motos:
  - corrige o nome do modelo nos overlays (whisper ouve 'MT zero seven' como 'MT-DO7')
  - garante SFX OFF em todas as cenas (nicho A limpo; ilustrar pode reativar whoosh)
"""
import json, re, sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
TL = Path(r"F:/Canal Dark/Aplicativo de Edição/banco-videos/teste/timeline.json")

_pat = re.compile(r"MT[\s\-]*[DdOo0]{1,2}7")  # MT-DO7, MTDO7, MT DO7, MTO7, MT-D07...


def fix(s):
    s = _pat.sub("MT-07", s)
    for bad in ("MT zero seven", "Mt zero seven", "mt zero seven"):
        s = s.replace(bad, "MT-07")
    return s


def walk(o):
    if isinstance(o, dict):
        return {k: walk(v) for k, v in o.items()}
    if isinstance(o, list):
        return [walk(v) for v in o]
    if isinstance(o, str):
        return fix(o)
    return o


tl = json.load(open(TL, encoding="utf-8"))
tl = walk(tl)
for c in tl.get("cenas", []):
    c["sfx"] = False
json.dump(tl, open(TL, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("OK: nomes corrigidos (MT-07) + sfx off em todas as cenas")
