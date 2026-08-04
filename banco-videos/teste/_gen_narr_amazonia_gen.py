# -*- coding: utf-8 -*-
"""Narração do job _job_amazonia_gen com a VOZ DO HOST (Russel).

Diferença pro `_gen_narr_amazonia.py`: em vez do `Bill EN.MP3` genérico, usa a
referência extraída do próprio take do avatar (`veo_voz.py`) — assim o Russel abre
falando e a narração continua na MESMA voz. Cai no Bill só se a referência não
existir ainda, avisando alto.
"""
import sys
from pathlib import Path

sys.path.insert(0, r"F:/Canal Dark/Aplicativo de Edição/video-automator")
sys.path.insert(0, str(Path(__file__).parent))
from narrator_chatterbox import narrar_chatterbox  # noqa
from veo_personagem import personagem_do_canal  # noqa

CANAL = "AMZ"
FALLBACK = r"F:/Canal Dark/CapCut/CapCut Materials/Vozes/Bill EN.MP3"

ficha = personagem_do_canal(CANAL) or {}
voz_ref = ficha.get("voz_ref") or ""
if voz_ref and Path(voz_ref).exists():
    print(f"voz do host: {Path(voz_ref).name} (clonada do avatar {ficha.get('nome')})")
else:
    voz_ref = FALLBACK
    print("!! SEM voz_ref do host — usando o Bill EN genérico. O avatar vai DESTOAR "
          "da narração. Rode antes: python veo_voz.py --clipes <take> --canal AMZ")

job = Path(r"F:/Canal Dark/Aplicativo de Edição/banco-videos/_job_amazonia_gen")
texto = (job / "roteiro_en.txt").read_text(encoding="utf-8").strip()
r = narrar_chatterbox(texto, voz_ref, "narr_amazonia_gen", pasta=str(job),
                      exaggeration=0.45, cfg_weight=0.5)
print("ok:", r.get("ok"), "| audio:", r.get("audio_local"), "| erro:", r.get("erro"))
