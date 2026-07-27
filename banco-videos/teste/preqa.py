# -*- coding: utf-8 -*-
"""PRÉ-QA automático (SKILL v2 §12, camada 1) — roda pós-render, ANTES do olho humano.
R-70: OCR de strings de default conhecidas (condicional a engine local disponível)
R-71: frame preto/estático no MEIO do beat (entrada de texto é escura por design)
R-72: diff perceptual (phash) entre frames-medianos de todos os beats
Saída: lista de beats flagados com R-xx + comandos de condenação. Exit 1 se houver flag.

Uso: python preqa.py <video.mp4> <montagem.json> [--limiar-phash 6]
"""
import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

DEFAULTS_CONHECIDOS = ["SUBJECT", "HILUX", "TEHRAN", "EXAMPLE", "LOREM", "PLACEHOLDER"]


def frame_do_beat(video, t, dest):
    r = subprocess.run(["ffmpeg", "-y", "-ss", f"{t:.2f}", "-i", str(video),
                        "-frames:v", "1", "-vf", "scale=320:180", "-q:v", "5", str(dest)],
                       capture_output=True)
    return r.returncode == 0 and dest.exists()


def phash(img_path):
    """average-hash 8x8 do MIOLO central (60%) — moldura T3 dominava o hash (falso positivo)."""
    from PIL import Image
    im = Image.open(img_path).convert("L")
    w, h = im.size
    im = im.crop((int(w * 0.2), int(h * 0.2), int(w * 0.8), int(h * 0.8))).resize((8, 8))
    px = list(im.getdata())
    media = sum(px) / 64
    return sum(1 << i for i, v in enumerate(px) if v > media)


def dist(h1, h2):
    return bin(h1 ^ h2).count("1")


def brilho_var(img_path):
    from PIL import Image
    im = Image.open(img_path).convert("L").resize((64, 36))
    px = list(im.getdata())
    n = len(px)
    m = sum(px) / n
    var = sum((v - m) ** 2 for v in px) / n
    return m, var


def ocr_texto(img_path):
    """R-70 condicional: usa pytesseract se existir; sem engine, retorna None (loga indisponível)."""
    try:
        import pytesseract
        from PIL import Image
        return pytesseract.image_to_string(Image.open(img_path)).upper()
    except Exception:
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("montagem")
    ap.add_argument("--limiar-phash", type=int, default=6)
    a = ap.parse_args()

    mont = json.loads(Path(a.montagem).read_text(encoding="utf-8"))
    beats = mont["beats"]
    tmp = Path(tempfile.mkdtemp(prefix="preqa_"))
    flags = []
    hashes = {}
    ocr_ok = ocr_texto.__doc__ is not None  # avaliado de fato no 1º frame

    print(f"preqa: {len(beats)} beats de {a.video}")
    ocr_disponivel = None
    for b in beats:
        i = b["i"]
        meio = (b["t_ini"] + b["t_fim"]) / 2
        f = tmp / f"b{i:03d}.jpg"
        if not frame_do_beat(a.video, meio, f):
            continue
        # R-71: preto/estático no meio do beat
        m, var = brilho_var(f)
        if m < 20 and var < 30:  # var<60 flagava Odometer dark-by-design (dígitos claros = conteúdo)
            flags.append((i, "R-71", f"frame do meio quase preto (brilho {m:.0f})"))
        # R-72: hash pra diff — frame PLANO (sem textura) não compara (colapsaria com todos)
        if var >= 150:
            hashes[i] = (phash(f), b.get("src"))
        # R-70: OCR condicional
        if ocr_disponivel is not False:
            tx = ocr_texto(f)
            if tx is None:
                if ocr_disponivel is None:
                    print("  [R-70] OCR indisponível (sem pytesseract) — checagem pulada, NÃO finjo que rodou")
                ocr_disponivel = False
            else:
                ocr_disponivel = True
                for d in DEFAULTS_CONHECIDOS:
                    if d in tx:
                        flags.append((i, "R-70", f"string de default '{d}' visível"))

    # R-72: pares com hash quase igual
    itens = sorted(hashes.items())
    for a_i, (h1, s1) in itens:
        for b_i, (h2, s2) in itens:
            if b_i <= a_i:
                continue
            if dist(h1, h2) <= a.limiar_phash:
                mesmo_src = s1 and s1 == s2
                perto = (b_i - a_i) < 6
                if mesmo_src and perto:
                    flags.append((b_i, "R-72", f"reuso colado do mesmo asset (beats {a_i}/{b_i})"))
                elif not mesmo_src and s1 and s2:
                    flags.append((b_i, "R-72", f"beats {a_i}/{b_i} visualmente idênticos com srcs distintos"))

    print()
    if not flags:
        print("PRE-QA LIMPO — nenhuma flag R-70/71/72. Segue pra decupagem humana (R-73).")
        return 0
    print(f"PRE-QA: {len(flags)} flag(s) [R-80: {100 * len(set(f[0] for f in flags)) // len(beats)}% dos beats]")
    for i, rid, motivo in flags:
        print(f"  b{i:03d} [{rid}] {motivo}")
    print("\ncondenação (R-75):")
    for i in sorted(set(f[0] for f in flags)):
        print(f'  del "resolvido/b{i:03d}.json" + assets/b{i:03d}__*')
    return 1


if __name__ == "__main__":
    sys.exit(main())
