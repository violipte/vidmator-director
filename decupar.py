#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""decupar.py — DECUPAGEM assistida por Claude.

Transforma um vídeo em algo que o Claude consegue "ASSISTIR":
  1) detecta CORTES DE CENA (ffmpeg scene score) OU amostra a cada N segundos;
  2) extrai 1 frame por trecho, reduzido;
  3) monta CONTACT SHEETS (grades 4x4) com TIMECODE + nº do shot em cada quadro
     -> o Claude lê poucas imagens e "vê" o vídeo inteiro;
  4) (opcional) extrai o ÁUDIO em 16kHz mono, pronto pra STT (Grok/Whisper);
  5) escreve decupagem.json (trechos + paths) pro Claude anotar shot a shot.

Depois é só pedir: "leia as contact sheets em <out> e me faça a decupagem".

Uso:
  python decupar.py "video.mp4"                 # auto: cenas, senão amostra
  python decupar.py "video.mp4" --modo fixo --intervalo 4
  python decupar.py "video.mp4" --modo cena --limiar 0.30
  python decupar.py "video.mp4" --audio          # + extrai wav 16k pra STT
  python decupar.py "video.mp4" --max 400        # teto de frames (default 400)

Requer: ffmpeg/ffprobe no PATH + Pillow (já usado no projeto).
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

COLS, ROWS = 4, 4            # 16 quadros por contact sheet
TILE_W = 480                 # largura de cada quadro na grade (px)
FONT_CANDS = [r"C:\Windows\Fonts\arialbd.ttf", r"C:\Windows\Fonts\arial.ttf"]


def _run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                          errors="replace", **kw)


def hms(t):
    t = float(t)
    h, r = divmod(int(t), 3600)
    m, s = divmod(r, 60)
    cs = int(round((t - int(t)) * 100))
    return (f"{h}:" if h else "") + f"{m:02d}:{s:02d}.{cs:02d}"


def duracao(video):
    r = _run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
              "-of", "default=nk=1:nw=1", str(video)])
    try:
        return float(r.stdout.strip())
    except ValueError:
        return 0.0


def cortes_de_cena(video, limiar):
    """Retorna lista de timestamps (s) onde há corte de cena (>limiar)."""
    r = _run(["ffmpeg", "-i", str(video), "-vf",
              f"select='gt(scene,{limiar})',showinfo", "-vsync", "vfr",
              "-f", "null", "-"])
    ts = [float(m) for m in re.findall(r"pts_time:([0-9.]+)", r.stderr)]
    return sorted(set(round(t, 2) for t in ts))


def extrair_frame(video, t, dest):
    _run(["ffmpeg", "-ss", f"{t:.2f}", "-i", str(video), "-frames:v", "1",
          "-vf", f"scale={TILE_W}:-1", "-q:v", "3", "-y", str(dest)])
    return dest.exists()


def extrair_audio(video, dest):
    r = _run(["ffmpeg", "-i", str(video), "-vn", "-ac", "1", "-ar", "16000",
              "-y", str(dest)])
    return dest.exists(), r.stderr[-300:]


def montar_sheets(frames, out_dir, video_nome):
    from PIL import Image, ImageDraw, ImageFont
    font = None
    for fc in FONT_CANDS:
        if Path(fc).exists():
            font = ImageFont.truetype(fc, 30)
            break
    font = font or ImageFont.load_default()
    sheets = []
    per = COLS * ROWS
    # descobre altura do tile pelo 1º frame
    tile_h = Image.open(frames[0]["path"]).height if frames else int(TILE_W * 9 / 16)
    pad, lbl = 6, 40
    cell_w, cell_h = TILE_W + pad, tile_h + lbl + pad
    for s in range(0, len(frames), per):
        grupo = frames[s:s + per]
        sheet = Image.new("RGB", (cell_w * COLS + pad, cell_h * ROWS + pad), (17, 17, 20))
        d = ImageDraw.Draw(sheet)
        for k, fr in enumerate(grupo):
            r, c = divmod(k, COLS)
            x, y = pad + c * cell_w, pad + r * cell_h
            try:
                im = Image.open(fr["path"]).convert("RGB")
            except Exception:
                continue
            sheet.paste(im, (x, y + lbl))
            tag = f"#{fr['i']:03d}  {hms(fr['t'])}"
            d.rectangle([x, y, x + TILE_W, y + lbl], fill=(0, 0, 0))
            d.text((x + 6, y + 4), tag, fill=(255, 216, 0), font=font)
        p = out_dir / f"sheet_{s // per + 1:02d}.jpg"
        sheet.save(p, quality=86)
        sheets.append(str(p))
    return sheets


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--modo", choices=["auto", "cena", "fixo"], default="auto")
    ap.add_argument("--intervalo", type=float, default=0, help="s entre frames (modo fixo)")
    ap.add_argument("--limiar", type=float, default=0.30, help="sensibilidade de corte (modo cena)")
    ap.add_argument("--max", type=int, default=400, help="teto de frames")
    ap.add_argument("--audio", action="store_true", help="extrai wav 16k mono pra STT")
    ap.add_argument("--out", default="", help="pasta de saída")
    a = ap.parse_args()

    video = Path(a.video).resolve()
    if not video.exists():
        print(f"ERRO: não achei {video}")
        sys.exit(1)
    out_dir = Path(a.out).resolve() if a.out else video.with_name(video.stem + "_decup")
    frames_dir = out_dir / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)

    dur = duracao(video)
    print(f"=== decupagem: {video.name}  ({hms(dur)}) ===")

    # 1) decide os timestamps
    tempos, origem = [], ""
    if a.modo in ("auto", "cena"):
        cortes = cortes_de_cena(video, a.limiar)
        print(f"  cortes de cena detectados: {len(cortes)}")
        if len(cortes) >= 6 or a.modo == "cena":
            tempos, origem = cortes, "cena"
    if not tempos:  # fixo (ou auto sem cortes)
        n = a.intervalo or max(2.0, round(dur / min(a.max, 48), 1))
        tempos = [round(t, 2) for t in _frange(0.5, dur, n)]
        origem = f"fixo/{n}s"
    if len(tempos) > a.max:  # subamostra respeitando o teto
        passo = len(tempos) / a.max
        tempos = [tempos[int(i * passo)] for i in range(a.max)]
    print(f"  modo={origem} -> {len(tempos)} frames")

    # 2) extrai frames
    frames = []
    for i, t in enumerate(tempos):
        dest = frames_dir / f"f_{i:04d}.jpg"
        if extrair_frame(video, t, dest):
            frames.append({"i": i, "t": t, "path": str(dest)})
        if (i + 1) % 25 == 0:
            print(f"    {i + 1}/{len(tempos)} frames...")
    print(f"  {len(frames)} frames extraídos")

    # 3) contact sheets
    sheets = montar_sheets(frames, out_dir, video.name) if frames else []
    print(f"  {len(sheets)} contact sheet(s) -> {out_dir}")

    # 4) áudio opcional
    audio_path = None
    if a.audio:
        audio_path = out_dir / (video.stem + "_16k.wav")
        ok, err = extrair_audio(video, audio_path)
        print(f"  áudio: {'OK ' + str(audio_path) if ok else 'FALHOU ' + err}")

    # 5) manifesto
    manifesto = {
        "video": str(video), "duracao": round(dur, 2), "origem": origem,
        "n_frames": len(frames), "sheets": sheets,
        "audio_16k": str(audio_path) if audio_path else None,
        "shots": [{"i": f["i"], "t": f["t"], "hms": hms(f["t"]), "frame": f["path"]} for f in frames],
    }
    (out_dir / "decupagem.json").write_text(
        json.dumps(manifesto, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nOK -> {out_dir}\\decupagem.json")
    print(f"Agora peça ao Claude: \"leia as contact sheets em {out_dir} e faça a decupagem\".")


def _frange(ini, fim, passo):
    t = ini
    while t < fim:
        yield t
        t += passo


if __name__ == "__main__":
    main()
