"""OVERRIDE de footage PRODUTO-LOCKED (nicho automotivo / TIPO A).
Substitui a mídia resolvida pelo resolver por FOTOS DO MODELO EXATO de cada moto.
Regra: cada bloco mostra SÓ a moto daquele bloco (carry-forward pelo texto da cena);
intro e conclusão = montagem dos 5. Nada de stock genérico / palavra literal.
"""
import json, glob, os, sys
from collections import defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
TESTE = Path(r"F:/Canal Dark/Aplicativo de Edição/banco-videos/teste")
FOOT = Path(r"F:/Canal Dark/Aplicativo de Edição/banco-videos/_motos_footage")
TL = TESTE / "timeline.json"

# âncoras únicas por modelo (busca no texto da cena, minúsculo)
ANCHORS = [
    ("rebel500", ["rebel"]),
    ("ninja400", ["ninja", "kawasaki", "399"]),
    ("sv650",    ["sv650", "sv 650", "suzuki", "645"]),
    ("cb500x",   ["cb500x", "cb 500", "cb-500", "500x", "adventure"]),
    ("mt07",     ["yamaha", "mt-07", "mt 07", "mt07", "689", "mt zero seven", "mt-do7", "mtdo7"]),
]
CONCL_CUES = ["subscribe", "comments", "hit like", "tell us", "so there it is", "five motorcycles that"]
KEYS = [k for k, _ in ANCHORS]

pools = {k: sorted(glob.glob(str(FOOT / k / "*.jpg"))) for k in KEYS}
for k, v in pools.items():
    if not v:
        print(f"  AVISO: sem imagens para {k}!")
# montagem = intercala os 5 modelos p/ variedade
montage = []
for i in range(max(len(v) for v in pools.values())):
    for k in KEYS:
        if i < len(pools[k]):
            montage.append(pools[k][i])


def model_for(text, cur):
    t = (text or "").lower()
    if any(c in t for c in CONCL_CUES):
        return "montage"
    for key, kws in ANCHORS:
        if any(kw in t for kw in kws):
            return key
    return cur or "montage"


tl = json.load(open(TL, encoding="utf-8"))
cenas = sorted(tl["cenas"], key=lambda c: c.get("inicio", 0))
cur = None
ctr = defaultdict(int)
dist = defaultdict(int)
for c in cenas:
    m = model_for(c.get("texto", ""), cur)
    if m in pools:
        cur = m
    pool = montage if m == "montage" else pools[m]
    img = pool[ctr[m] % len(pool)]
    ctr[m] += 1
    dur = c.get("fim", 0) - c.get("inicio", 0)
    c["clip_path"] = img.replace("\\", "/")
    c["media_tipo"] = "imagem"
    c["clip_dur"] = round(max(5.0, dur + 0.6), 2)
    c["clip_id"] = f"moto{c['idx']}"
    c["nivel"] = "produto-lock"
    c["real_query"] = m
    c["sfx"] = False               # nicho A: SFX mínimo (whoosh off; estouro era o glitch de tópico)
    if c.get("presentacao"):
        c["presentacao"]["extras"] = None   # sem split/grid neste nicho
    dist[m] += 1

json.dump(tl, open(TL, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("OK override produto-locked:", dict(dist))
