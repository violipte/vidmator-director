# -*- coding: utf-8 -*-
"""PARALLAX 2.5D (v5) — gera as CAMADAS de uma cena parallax e recorta.

fundo  -> imagem cheia (ilustrador, pad 16:9)
meio   -> gerado "isolated on pure white background" -> rembg -> PNG alpha
frente -> idem (sujeito principal)

Uso:
  python parallax5.py --job <dir> --nome cena01 \
      --fundo "stormy sky at dusk over the Aegean" \
      --meio "greek temple ruins on a rocky hill, complete silhouette" \
      --frente "marble statue of a stoic philosopher, full body" \
      [--estilo "ancient greek, muted gold and stone, cinematic"]

Saída: <job>/parallax/<nome>_fundo.png|_meio.png|_frente.png (meio/frente com alpha)
"""
import argparse
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).parent))
# usa o MOTOR do ilustrador (Together, API pura) mas com prompt cinematográfico próprio —
# os ESTILOS do ilustrador são de manual técnico, errados pra camada de parallax
from ilustrador import _gerar_com, _key, pad_169, MODEL_DEFAULT, MODEL_FALLBACK  # noqa

SUFIXO_RECORTE = (", isolated on a pure solid white background, the complete subject fully "
                  "visible, nothing cropped at the edges, no shadows on the background")
SUFIXO_COMUM = " Cinematic illustration, high detail, no watermark, no logos, no text."


def _gerar(prompt, dest):
    key = _key()
    if not key:
        raise SystemExit("[parallax5] sem key together no credentials.json")
    for m in [MODEL_DEFAULT, MODEL_FALLBACK]:
        if _gerar_com(m, prompt + SUFIXO_COMUM, str(dest), key):
            return True
    raise SystemExit(f"[parallax5] geração FALHOU: {prompt[:60]}...")


def _recortar(src, dest):
    """rembg + alpha — mesmo motor do mascote (fundo branco recorta limpo)."""
    from rembg import remove as _rembg
    from PIL import Image
    img = Image.open(src).convert("RGBA")
    out = _rembg(img)
    out.save(dest)
    return dest


def gerar_camadas(job, nome, fundo=None, meio=None, frente=None, estilo=""):
    pasta = Path(job) / "parallax"
    pasta.mkdir(parents=True, exist_ok=True)
    est = f", {estilo}" if estilo else ""
    saida = {}
    if fundo:
        f_png = pasta / f"{nome}_fundo.png"
        if not f_png.exists():
            _gerar(f"{fundo}{est}, wide 16:9 background plate, no main subject", f_png)
            pad_169(str(f_png))
        saida["fundo"] = str(f_png)
    if meio:
        m_raw = pasta / f"{nome}_meio_raw.png"
        m_png = pasta / f"{nome}_meio.png"
        if not m_png.exists():
            _gerar(f"{meio}{est}{SUFIXO_RECORTE}", m_raw)
            _recortar(m_raw, m_png)
        saida["meio"] = str(m_png)
    if frente:
        s_raw = pasta / f"{nome}_frente_raw.png"
        s_png = pasta / f"{nome}_frente.png"
        if not s_png.exists():
            _gerar(f"{frente}{est}{SUFIXO_RECORTE}", s_raw)
            _recortar(s_raw, s_png)
        saida["frente"] = str(s_png)
    return saida


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--job", required=True)
    ap.add_argument("--nome", required=True)
    ap.add_argument("--fundo", default=None)
    ap.add_argument("--meio", default=None)
    ap.add_argument("--frente", default=None)
    ap.add_argument("--estilo", default="")
    a = ap.parse_args()
    saida = gerar_camadas(a.job, a.nome, a.fundo, a.meio, a.frente, a.estilo)
    for k, v in saida.items():
        print(f"  {k}: {v}")
    print(f"parallax [{a.nome}]: {len(saida)} camadas")


if __name__ == "__main__":
    main()
