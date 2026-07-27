# -*- coding: utf-8 -*-
"""ILUSTRADOR — gera ilustração TÉCNICA via Together AI (google/gemini-3-pro-image).
Cobre o tipo `ilustracao` do plano de beats (diagramas/cutaways/blueprints estilo
manual de serviço — o naco de ~20% que a VidRush usa e não temos como filmar).

Uso como módulo:  from ilustrador import ilustrar
  ilustrar("Toyota 1GD diesel engine cutaway", dest, estilo="manual")
Uso CLI (teste):  python ilustrador.py "common rail diesel system diagram" out.png

Key: credentials.json (provedor "together", gitignored). NUNCA hardcodar.
Cloudflare da Together bloqueia UA de bot -> SEMPRE User-Agent de browser.
"""
import base64
import json
import sys
import time
from pathlib import Path

import httpx

sys.stdout.reconfigure(encoding="utf-8")
_CREDS = Path(r"F:/Canal Dark/Aplicativo de Edição/video-automator/credentials.json")
URL = "https://api.together.xyz/v1/images/generations"

# Bake-off 2026-07-19 (5 modelos × 3 estilos, mesmos prompts): o TEXTO decide (decisão Piter).
#   gpt-image-2  = único com rótulos LEGÍVEIS/corretos ("1. Valve Cover") -> estilos com texto
#   imagen-4.0-fast = composição excelente por $0.02, mas rótulos gibberish -> estilos sem texto
#   flash-3.1-lite (NB2 Lite, $0.069) = 2º melhor geral -> FALLBACK dos dois primários
#   descartados: flash-2.5 (typos), gemini-3-pro (6.7x preço, sem vantagem)
MODEL_POR_ESTILO = {
    "manual":    "openai/gpt-image-2",      # $0.053 — callouts/labels precisam de texto real
    "blueprint": "google/imagen-4.0-fast",  # $0.020 — cotas são micro-texto decorativo
    "cutaway":   "google/imagen-4.0-fast",  # $0.020 — sem texto, realismo ótimo
}
MODEL_DEFAULT = "google/imagen-4.0-fast"
MODEL_FALLBACK = "google/flash-image-3.1-lite"  # NB2 Lite — entra se o primário falhar


def _key():
    try:
        return next(c["api_key"] for c in json.load(open(_CREDS, encoding="utf-8"))
                    if c.get("provedor") == "together" and c.get("api_key"))
    except Exception:
        return None


# estilos de ilustração técnica (ref. decupagem VidRush: manual branco, blueprint, cutaway)
ESTILOS = {
    "manual":    "Technical service-manual illustration, clean vector line art with subtle shading, "
                 "labeled callout lines, pure white background, engineering-drawing style. ",
    "blueprint": "Engineering blueprint, white technical line art on dark navy-blue background, "
                 "orthographic views, thin construction lines and dimension marks. ",
    "cutaway":   "Detailed technical cutaway illustration, cross-section view revealing internal parts, "
                 "muted realistic colors on neutral light background, industrial documentary style. ",
}
_SUFFIX = " No watermark, no brand logos, no text paragraphs, high detail, 16:9 composition."


def _gerar_com(model, prompt, dest, key, tentativas=3):
    """Uma rodada de geração num modelo específico. True/False."""
    body = {"model": model, "prompt": prompt, "width": 1920, "height": 1080,
            "response_format": "b64_json"}  # sem "n": modelos google não suportam
    hdr = {"Authorization": "Bearer " + key, "Content-Type": "application/json",
           "User-Agent": "Mozilla/5.0"}
    for t in range(tentativas):
        try:
            r = httpx.post(URL, headers=hdr, json=body, timeout=300)  # gpt-image-2 é lento (>180s sob carga)
            if r.status_code == 200:
                d = r.json()["data"][0]
                if d.get("b64_json"):
                    raw = base64.b64decode(d["b64_json"])
                elif d.get("url"):
                    raw = httpx.get(d["url"], headers={"User-Agent": "Mozilla/5.0"}, timeout=120).content
                else:
                    print(f"[ilustrador] {model}: resposta sem imagem"); return False
                Path(dest).write_bytes(raw)
                return Path(dest).stat().st_size > 20000
            # dimensões não suportadas -> tenta sem width/height (default do modelo)
            if r.status_code == 400 and "width" in body:
                body.pop("width", None); body.pop("height", None)
                continue
            if r.status_code in (429, 503, 502):
                time.sleep(4 * (t + 1)); continue
            print(f"[ilustrador] {model} HTTP {r.status_code}: {r.text[:160]}")
            return False
        except Exception as e:
            print(f"[ilustrador] {model} erro: {str(e)[:100]}")
            time.sleep(3)
    return False


def ilustrar(assunto, dest, estilo="manual", tentativas=3, model=None):
    """Gera a ilustração e salva em `dest`. Primário por estilo (bake-off) -> NB2 Lite fallback."""
    key = _key()
    if not key:
        print("[ilustrador] sem key together"); return False
    prompt = ESTILOS.get(estilo, ESTILOS["manual"]) + assunto.strip() + _SUFFIX
    primario = model or MODEL_POR_ESTILO.get(estilo, MODEL_DEFAULT)
    cadeia = [primario] + ([MODEL_FALLBACK] if MODEL_FALLBACK != primario else [])
    for m in cadeia:
        if _gerar_com(m, prompt, dest, key, tentativas):
            if m != primario:
                print(f"[ilustrador] fallback usado: {m}")
            return True
    return False


def pad_169(src, dest=None):
    """Modelo devolve 1024x1024 fixo -> estica o canvas p/ 1920x1080 preenchendo com a cor
    do fundo (média dos 4 cantos). Fundo liso (branco/navy) = emenda invisível."""
    from PIL import Image
    im = Image.open(src).convert("RGB")
    w, h = im.size
    px = [im.getpixel(p) for p in ((2, 2), (w - 3, 2), (2, h - 3), (w - 3, h - 3))]
    bg = tuple(sum(c[i] for c in px) // 4 for i in range(3))
    alvo_h = 1080
    im = im.resize((int(w * alvo_h / h), alvo_h), Image.LANCZOS)
    canvas = Image.new("RGB", (1920, 1080), bg)
    canvas.paste(im, ((1920 - im.width) // 2, 0))
    canvas.save(dest or src, quality=95)
    return dest or src


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__); sys.exit(1)
    assunto, dest = sys.argv[1], sys.argv[2]
    estilo = sys.argv[3] if len(sys.argv) > 3 else "manual"
    ok = ilustrar(assunto, dest, estilo)
    print("OK ->" if ok else "FALHOU", dest)
