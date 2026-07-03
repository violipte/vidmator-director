"""Narrador genérico p/ produção em lote: lê roteiro_en.txt e gera o mp3 com a voz dada.
Roda no venv do Chatterbox (CUDA). Uso: python narrar_job.py <voice_ref> <out_name>
"""
import sys
sys.path.insert(0, r"F:/Canal Dark/Aplicativo de Edição/video-automator")
from pathlib import Path
from narrator_chatterbox import narrar_chatterbox

TESTE = r"F:/Canal Dark/Aplicativo de Edição/banco-videos/teste"


def main():
    voice_ref, out_name = sys.argv[1], sys.argv[2]
    texto = Path(TESTE, "roteiro_en.txt").read_text(encoding="utf-8").strip()
    r = narrar_chatterbox(texto, voice_ref, out_name, pasta=TESTE, exaggeration=0.4, cfg_weight=0.5)
    print("ok:", r.get("ok"), "| audio:", r.get("audio_local"), "| erro:", r.get("erro"))
    sys.exit(0 if r.get("ok") else 1)


if __name__ == "__main__":
    main()
