# -*- coding: utf-8 -*-
"""DUBLAGEM DOS TAKES DO HOST (06/08) — a fala do avatar sai do Chatterbox, não do VEO.

Por que existe (prova do 1º corte da Austrália, STT dos takes crus):
    av_hook      -> "...Subscribe so you don't miss it. Travis Arewa."
    av_cta_final -> "...subscribe and ring the bell. TraviSero."
"Travis Arewa"/"TraviSero" é o VEO PRONUNCIANDO O NOME DO CHIP (Travesseiro). Mesmo
com o nome fora do texto do prompt, o gerador de áudio lê o nome do personagem em voz
alta. E o casamento por título ainda pôs a fala do CTA dentro do slot da ABERTURA.

Gerando o take MUDO e dublando aqui: texto exato, nome nunca falado, e a voz do host
passa a ser a MESMA da narração (mesmo clone) em vez de só parecida.

Lê as ilhas do style_card (`avatar.ilhas[secao].dub`) e grava `<banco>/av_*.wav`.
O montador acha o .wav pelo nome do clipe e monta a ilha com ele.

Uso: python gerar_dub_avatar.py --job <dir>
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, r"F:/Canal Dark/Aplicativo de Edição/video-automator")
sys.stdout.reconfigure(encoding="utf-8")
from narrator_chatterbox import narrar_chatterbox  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--job", required=True)
    ap.add_argument("--forcar", action="store_true", help="regera mesmo se o wav existir")
    a = ap.parse_args()

    job = Path(a.job)
    sc = json.loads((job / "style_card.json").read_text(encoding="utf-8"))
    av = sc.get("avatar") or {}
    banco = Path(av.get("banco") or (job / "assets"))
    voz = av.get("voz_ref")
    if not voz:
        from veo_personagem import personagem_do_canal
        voz = (personagem_do_canal(sc.get("canal") or "") or {}).get("voz_ref")
    if not voz or not Path(voz).exists():
        print(f"!! voz de referência ausente ({voz}) — sem dublagem")
        return
    print(f"voz de referência: {Path(voz).name}")

    feitos = 0
    for sec, ilha in (av.get("ilhas") or {}).items():
        if not isinstance(ilha, dict):
            continue
        texto = (ilha.get("dub") or "").strip()
        if not texto:
            continue
        nome = Path(ilha["clip"]).stem
        wav = banco / f"{nome}.wav"
        if wav.exists() and not a.forcar:
            print(f"  {wav.name}: já existe (use --forcar pra refazer)")
            continue
        r = narrar_chatterbox(texto, str(voz), nome, pasta=str(banco),
                              exaggeration=0.5, cfg_weight=0.5)
        if not r.get("ok"):
            print(f"  !! {nome}: {r.get('erro')}")
            continue
        # o chatterbox entrega mp3; a montagem aceita os dois, mas padroniza no nome
        saida = Path(r.get("audio_local") or "")
        if saida.exists() and saida.suffix.lower() != ".wav":
            import subprocess
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(saida),
                            "-ar", "44100", "-ac", "2", str(wav)],
                           capture_output=True, timeout=180)
        print(f"  {wav.name}: {texto[:56]!r}")
        feitos += 1
    print(f"dublagem: {feitos} arquivo(s) gerado(s) em {banco}")


if __name__ == "__main__":
    main()
