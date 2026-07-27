"""Ingesta o acervo do MASCOTE (imagens fundo verde) -> recorta (rembg) -> PNG alpha + índice de poses.
Cada imagem: {pose, emocao, funcao, desc} via GPT Vision. O pass mascote.py escolhe a pose pelo beat.

Uso: python indexar_mascote.py "<pasta_fonte>" [--banco <pasta_destino>] [--nome galo]
Idempotente: re-roda só o que falta (por nome de arquivo).
"""
import base64
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
TESTE = Path(r"F:/Canal Dark/Aplicativo de Edição/banco-videos/teste")
CREDS = Path(r"F:/Canal Dark/Aplicativo de Edição/video-automator/credentials.json")
GPT_KEY = next((c["api_key"] for c in json.load(open(CREDS, encoding="utf-8"))
                if c.get("provedor") == "gpt" and c.get("api_key")), "")

try:
    import onnxruntime  # noqa: F401
    from rembg import remove as _rembg
    _REMBG_OK = True
except Exception:
    _REMBG_OK = False


def _vision(prompt, img_path):
    b64 = base64.b64encode(Path(img_path).read_bytes()).decode()
    mime = "image/png" if str(img_path).lower().endswith(".png") else "image/jpeg"
    body = json.dumps({"model": "gpt-4o-mini", "max_completion_tokens": 300,
                       "messages": [{"role": "user", "content": [
                           {"type": "text", "text": prompt},
                           {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}", "detail": "low"}}]}]}).encode()
    for _ in range(3):
        try:
            r = urllib.request.urlopen(urllib.request.Request(
                "https://api.openai.com/v1/chat/completions", data=body,
                headers={"Content-Type": "application/json", "Authorization": f"Bearer {GPT_KEY}"}, method="POST"), timeout=60)
            return json.loads(r.read())["choices"][0]["message"]["content"]
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(3); continue
            return None
        except Exception:
            time.sleep(1); continue
    return None


def tag_pose(img_path):
    p = ("This is a cartoon mascot character (a veteran rooster) in a specific pose/expression, used as a video "
         "overlay. Return ONLY JSON {pose, emocao, funcao, desc}. "
         "pose = 2-4 word physical pose (e.g. 'pointing at viewer', 'reading map', 'arms crossed'). "
         "emocao = one of: warning/angry/confident/curious/shocked/happy/serious/nostalgic/alert. "
         "funcao = when a narrator would use it, one of: warn/explain/teach/react/story/greet/action. "
         "desc = 5-10 word description of what he's doing.")
    out = _vision(p, img_path)
    if not out:
        return None
    a, b = out.find("{"), out.rfind("}")
    try:
        o = json.loads(out[a:b + 1])
        return {"pose": str(o.get("pose", ""))[:40], "emocao": str(o.get("emocao", ""))[:16],
                "funcao": str(o.get("funcao", ""))[:12], "desc": str(o.get("desc", ""))[:80]}
    except Exception:
        return None


def recortar(src, dest):
    """Recorte rembg + DESPILL de verde (rembg deixa halo esverdeado na borda do chroma).
    1) rembg tira o fundo; 2) pixels fortemente verdes restantes -> transparentes;
    3) verde moderado (spill na borda) -> dessaturado (g = max(r,b))."""
    from PIL import Image
    import io
    import numpy as np
    raw = Path(src).read_bytes()
    if _REMBG_OK:
        im = Image.open(io.BytesIO(_rembg(raw))).convert("RGBA")
    else:
        im = Image.open(io.BytesIO(raw)).convert("RGBA")
    a = np.array(im).astype(np.int16)
    r, g, b, al = a[..., 0], a[..., 1], a[..., 2], a[..., 3]
    mx = np.maximum(r, b)
    verde_forte = (g > 100) & (g > mx * 1.35)          # fundo/halo verde puro -> some
    spill = (g > mx) & ~verde_forte                     # borda contaminada -> despill
    al[verde_forte] = 0
    gg = g.copy()
    gg[spill] = mx[spill]
    a[..., 1] = gg
    a[..., 3] = al
    Image.fromarray(a.astype(np.uint8), "RGBA").save(dest, "PNG")
    return Path(dest).exists()


def main():
    if len(sys.argv) < 2:
        print('uso: python indexar_mascote.py "<pasta_fonte>" [--banco <dest>] [--nome galo]'); return
    fonte = Path(sys.argv[1])
    banco = Path(r"F:/Canal Dark/Aplicativo de Edição/banco-videos/mascote_galo")
    nome = "galo"
    for i, a in enumerate(sys.argv):
        if a == "--banco" and i + 1 < len(sys.argv):
            banco = Path(sys.argv[i + 1])
        if a == "--nome" and i + 1 < len(sys.argv):
            nome = sys.argv[i + 1]
    banco.mkdir(parents=True, exist_ok=True)
    idx_path = banco / "index_mascote.json"
    idx = json.load(open(idx_path, encoding="utf-8")) if idx_path.exists() else {"nome": nome, "itens": {}}

    fontes = sorted([p for p in fonte.iterdir() if p.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp")])
    print(f"=== Mascote '{nome}': {len(fontes)} imagens em {fonte} | {len(idx['itens'])} já no banco ===")
    novos = 0
    for i, src in enumerate(fontes):
        key = src.stem[:60]
        if key in idx["itens"] and (banco / idx["itens"][key]["file"]).exists():
            continue
        dest = banco / f"{nome}_{key}.png"
        if not recortar(src, dest):
            print(f"  ✗ recorte falhou: {src.name}"); continue
        tags = tag_pose(src) or {"pose": "", "emocao": "", "funcao": "", "desc": ""}
        idx["itens"][key] = {"file": dest.name, **tags}
        novos += 1
        print(f"  ✓ {dest.name} | {tags['funcao']}/{tags['emocao']} | {tags['pose']}")
    json.dump(idx, open(idx_path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"=== {novos} novos -> {banco} | índice: {len(idx['itens'])} poses ===")


if __name__ == "__main__":
    main()
