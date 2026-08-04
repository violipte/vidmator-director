# -*- coding: utf-8 -*-
"""VOZ DO AVATAR -> REFERÊNCIA DE CLONE (04/08, pedido do Piter).

Problema: o avatar fala no vídeo com a voz do Flow (ex.: Iapetus) e a NARRAÇÃO é
gerada pelo Chatterbox com outra voz de referência (hoje `Bill EN.MP3`). São duas
pessoas diferentes no mesmo vídeo — o host abre falando e um estranho continua a
história. Some a identidade sonora do canal.

Solução: extrair a fala do próprio take do avatar e usar como `voice_ref` do
Chatterbox. A narração inteira passa a soar como o host.

    python veo_voz.py --clipes <take1.mp4> [take2.mp4 ...] --canal AMZ

O `narrator_chatterbox.narrar_chatterbox(texto, voice_ref, ...)` pede MP3/WAV de
**5-15s**. Um take de 8s rende ~6s de fala: passa, mas 2-3 takes concatenados clonam
melhor.

⚠️ O take de REFERÊNCIA deve ser gerado com ambiente MÍNIMO. Som de rio/insetos
ajuda o clipe e atrapalha o clone — o Chatterbox aprende o ruído junto com a voz.
Para o take de referência, peça "clean voice recording, no ambient sound".
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.stdout.reconfigure(encoding="utf-8")

MIN_S, MAX_S = 5.0, 15.0
DEST = Path(__file__).resolve().parents[2] / "veo_flow" / "vozes_ref"


def _dur(p):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "csv=p=0", str(p)], capture_output=True, text=True)
    try:
        return float((r.stdout or "0").strip())
    except ValueError:
        return 0.0


def extrair(clipes, dest_wav, max_s=MAX_S):
    """Extrai a fala dos clipes, limpa e concatena num WAV mono 24k pro clone.

    A limpeza é conservadora de propósito: highpass tira o ronco do ambiente,
    afftdn reduz chiado e silenceremove corta os buracos entre frases (o Chatterbox
    aproveita melhor 8s de fala contínua que 15s com metade em silêncio). Não uso
    compressor/EQ agressivo — isso alteraria o timbre, que é justamente o que
    queremos preservar."""
    dest_wav = Path(dest_wav)
    dest_wav.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest_wav.parent / "_tmp_voz"
    tmp.mkdir(exist_ok=True)
    partes = []
    for k, c in enumerate(clipes):
        if not Path(c).exists():
            print(f"  !! {c} não existe — pulando")
            continue
        o = tmp / f"p{k:02d}.wav"
        r = subprocess.run(
            ["ffmpeg", "-nostdin", "-y", "-loglevel", "error", "-i", str(c),
             "-vn", "-ac", "1", "-ar", "24000",
             "-af", ("highpass=f=85,afftdn=nf=-22,"
                     "silenceremove=start_periods=1:start_silence=0.2:start_threshold=-42dB:"
                     "stop_periods=-1:stop_silence=0.35:stop_threshold=-42dB,"
                     "loudnorm=I=-18:TP=-2:LRA=9"),
             str(o)], capture_output=True, timeout=300)
        if r.returncode == 0 and o.exists() and _dur(o) > 0.8:
            partes.append(o)
            print(f"  {Path(c).name}: {_dur(o):.1f}s de fala")
        else:
            print(f"  !! falha ao extrair de {Path(c).name}")
    if not partes:
        return None
    lista = tmp / "concat.txt"
    lista.write_text("\n".join(f"file '{p.as_posix()}'" for p in partes) + "\n",
                     encoding="utf-8")
    subprocess.run(["ffmpeg", "-nostdin", "-y", "-loglevel", "error", "-f", "concat",
                    "-safe", "0", "-i", str(lista), "-t", str(max_s), "-c:a", "pcm_s16le",
                    str(dest_wav)], capture_output=True, timeout=300)
    for p in partes + [lista]:
        p.unlink(missing_ok=True)
    d = _dur(dest_wav)
    if d < MIN_S:
        print(f"  !! só {d:.1f}s — o Chatterbox quer {MIN_S:.0f}-{MAX_S:.0f}s. "
              f"Gere mais um take do avatar e rode de novo com os dois.")
    else:
        print(f"  referência pronta: {d:.1f}s -> {dest_wav}")
    return dest_wav if d > 0 else None


def registrar(canal, wav):
    """Aponta a voz_ref do canal no registro de personagens — é de lá que a
    narração vai puxar, em vez do `Bill EN.MP3` genérico."""
    from veo_personagem import _registro_ler, _registro_gravar
    reg = _registro_ler()
    ficha = reg.get(canal) or {"nome": f"host_{canal}", "escopo": "canal"}
    ficha["voz_ref"] = str(Path(wav).resolve())
    reg[canal] = ficha
    _registro_gravar(reg)
    print(f"  canal {canal}: voz_ref registrada")
    return ficha


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--clipes", nargs="+", required=True, help="take(s) do avatar falando")
    ap.add_argument("--canal", required=True)
    ap.add_argument("--saida", default="")
    a = ap.parse_args()
    dest = Path(a.saida) if a.saida else DEST / f"voz_{a.canal}.wav"
    wav = extrair(a.clipes, dest)
    if wav:
        registrar(a.canal, wav)
        print(f"\nUse na narração:\n  narrar_chatterbox(texto, r\"{wav}\", nome, ...)")


if __name__ == "__main__":
    main()
