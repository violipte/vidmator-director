# -*- coding: utf-8 -*-
"""MP3 narrado -> transcript_timed.txt ([MM:SS] texto) pro diretor.py.
Usa o transcriber do video-automator (Grok STT primário, Whisper fallback).
Uso: python stt_para_transcript.py <narracao.mp3> <saida.txt>
"""
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"F:/Canal Dark/Aplicativo de Edição/video-automator")
from transcriber import transcrever  # noqa


def srt_para_timed(srt_path, out_path):
    blocos = Path(srt_path).read_text(encoding="utf-8").strip().split("\n\n")
    linhas = []
    for b in blocos:
        ls = [x for x in b.splitlines() if x.strip()]
        if len(ls) < 3:
            continue
        m = re.match(r"(\d+):(\d{2}):(\d{2})[,.]", ls[1])
        if not m:
            continue
        t = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + int(m.group(3))
        texto = " ".join(ls[2:]).strip()
        if texto:
            linhas.append(f"[{t // 60}:{t % 60:02d}] {texto}")
    Path(out_path).write_text("\n".join(linhas), encoding="utf-8")
    return len(linhas)


if __name__ == "__main__":
    mp3, out = sys.argv[1], sys.argv[2]
    srt = transcrever(mp3, idioma="en")
    n = srt_para_timed(srt, out)
    print(f"OK: {n} segmentos -> {out}")
