# -*- coding: utf-8 -*-
"""FORCED ALIGNMENT do ROTEIRO (02/08) — timestamp por PALAVRA, sem transcrever.

Duas dores, uma solução:

1. KARAOKÊ. O `Karaoke5.tsx` distribui as palavras proporcionalmente à duração do
   beat — chuta. Com alinhamento real cada palavra acende no instante em que é dita.

2. NOME PRÓPRIO INVENTADO (o bug do "Nasgerice"). O diretor trabalha sobre a
   TRANSCRIÇÃO porque precisa do timing, e o STT erra justamente nome próprio: o
   roteiro dizia "The doctor in Minas Gerais" e o STT ouviu "Nasgerice", que virou
   uma PESSOA e assinou uma citação no vídeo publicado. Alinhamento forçado inverte
   a lógica: o texto é o ROTEIRO (verdade), o áudio só diz QUANDO cada palavra cai.
   Nome próprio não tem como sair errado — ele nunca é adivinhado.

Não é STT: não descobre o que foi dito, ele ancora no tempo o que já sabemos.
WhisperX faria isso, mas exige ctranslate2==4.4.0, sem build pra Python 3.14 —
o torchaudio tem `forced_align` nativo e já estava no venv por causa do CLIP.

Uso (no clip_venv):
  clip_venv/Scripts/python.exe alinhar_roteiro.py --audio narr.mp3 --roteiro r.txt \
      [--saida palavras.json]
Saída: [{"palavra": "the", "t_ini": 0.32, "t_fim": 0.44}, ...]
"""
import argparse
import json
import re
import sys
import unicodedata


def _normalizar(texto):
    """MMS_FA usa alfabeto latino minúsculo sem pontuação. Devolve (tokens, original)
    para o JSON sair com a palavra COMO ESTÁ NO ROTEIRO (maiúscula, acento)."""
    palavras = [w for w in re.findall(r"[^\s]+", texto) if any(c.isalnum() for c in w)]
    saida = []
    for w in palavras:
        base = unicodedata.normalize("NFKD", w).encode("ascii", "ignore").decode()
        base = re.sub(r"[^a-zA-Z']", "", base).lower()
        if base:
            saida.append((base, w))
    return saida


def _carregar_audio(caminho, sr_alvo):
    """MP3/WAV -> tensor mono no sample rate do aligner, via ffmpeg + stdlib.
    `torchaudio.load` na 2.11 exige TorchCodec; ffmpeg já é dependência de toda a
    pipeline e faz decode + mono + resample numa passada só."""
    import subprocess
    import tempfile
    import wave
    import numpy as np
    import torch
    with tempfile.TemporaryDirectory() as td:
        wav = f"{td}/a.wav"
        subprocess.run(["ffmpeg", "-nostdin", "-y", "-loglevel", "error", "-i", str(caminho),
                        "-ac", "1", "-ar", str(sr_alvo), "-c:a", "pcm_s16le", wav],
                       check=True, capture_output=True, timeout=900)
        with wave.open(wav, "rb") as w:
            bruto = w.readframes(w.getnframes())
    amostras = np.frombuffer(bruto, dtype=np.int16).astype(np.float32) / 32768.0
    return torch.from_numpy(amostras).unsqueeze(0)


def alinhar(audio, roteiro_txt):
    import torch
    import torchaudio
    from torchaudio.pipelines import MMS_FA as bundle

    pares = _normalizar(roteiro_txt)
    if not pares:
        return []
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    modelo = bundle.get_model().to(dev)
    tokenizer, aligner = bundle.get_tokenizer(), bundle.get_aligner()

    onda = _carregar_audio(audio, bundle.sample_rate)
    with torch.inference_mode():
        emissao, _ = modelo(onda.to(dev))
        spans = aligner(emissao[0], tokenizer([p[0] for p in pares]))
    # razão quadro->segundo: a emissão é subamostrada em relação ao áudio
    seg_por_quadro = onda.shape[1] / bundle.sample_rate / emissao.shape[1]
    return [{"palavra": pares[i][1],
             "t_ini": round(sp[0].start * seg_por_quadro, 3),
             "t_fim": round(sp[-1].end * seg_por_quadro, 3)}
            for i, sp in enumerate(spans) if sp]


def montar_transcript(palavras, max_palavras=14):
    """Linhas `[M:SS] texto` — o MESMO formato que o `diretor.py` já consome, mas com
    o texto do ROTEIRO e os tempos reais. Plug-and-play: o diretor não muda, só passa
    a receber uma entrada em que nome próprio não pode estar errado.
    (No transcript do STT das cobras, "Minas Gerais" saiu certo aos 0:03 e virou
    "Nasgerice" aos 8:10 — erro INTERMITENTE, que é pior de caçar que erro fixo.)
    Quebra em fim de frase; se a frase for longa, corta no limite de palavras."""
    linhas, buf, t0 = [], [], None
    for w in palavras:
        if t0 is None:
            t0 = w["t_ini"]
        buf.append(w["palavra"])
        fim_frase = w["palavra"].rstrip('"\'').endswith((".", "!", "?"))
        if fim_frase or len(buf) >= max_palavras:
            linhas.append(f"[{int(t0) // 60}:{int(t0) % 60:02d}] " + " ".join(buf))
            buf, t0 = [], None
    if buf:
        linhas.append(f"[{int(t0 or 0) // 60}:{int(t0 or 0) % 60:02d}] " + " ".join(buf))
    return "\n".join(linhas) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--audio", required=True)
    ap.add_argument("--roteiro", required=True)
    ap.add_argument("--saida", default="")
    ap.add_argument("--transcript", default="", help="gera [M:SS] pro diretor")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    from pathlib import Path
    palavras = alinhar(a.audio, Path(a.roteiro).read_text(encoding="utf-8", errors="ignore"))
    if a.transcript:
        Path(a.transcript).write_text(montar_transcript(palavras), encoding="utf-8")
        print(f"transcript alinhado ({len(palavras)} palavras) -> {a.transcript}")
    if a.saida:
        Path(a.saida).write_text(json.dumps(palavras, ensure_ascii=False), encoding="utf-8")
        print(f"{len(palavras)} palavras alinhadas -> {a.saida}")
    if not (a.saida or a.transcript):
        print(json.dumps(palavras[:40], ensure_ascii=False))


if __name__ == "__main__":
    main()
