import sys
sys.path.insert(0, r"F:/Canal Dark/Aplicativo de Edição/video-automator")
from pathlib import Path
from narrator_chatterbox import narrar_chatterbox
texto = Path("roteiro_en.txt").read_text(encoding="utf-8").strip()
r = narrar_chatterbox(texto, r"F:/Canal Dark/CapCut/CapCut Materials/Vozes/Bill EN.MP3",
    "poc5_mysteries", pasta=r"F:/Canal Dark/Aplicativo de Edição/banco-videos/teste",
    exaggeration=0.45, cfg_weight=0.5)
print("ok:", r.get("ok"), "| audio:", r.get("audio_local"), "| erro:", r.get("erro"))
