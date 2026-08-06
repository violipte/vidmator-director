import sys
sys.path.insert(0, r"F:/Canal Dark/Aplicativo de Edição/video-automator")
from pathlib import Path
from narrator_chatterbox import narrar_chatterbox

JOB = Path(r"F:/Canal Dark/Aplicativo de Edição/banco-videos/_job_australia")
texto = (JOB / "roteiro_en.txt").read_text(encoding="utf-8").strip()
# voz do proprio host (clone da voz do avatar) — mesma identidade sonora do canal
r = narrar_chatterbox(texto, r"F:/Canal Dark/Aplicativo de Edição/veo_flow/vozes_ref/voz_AMZ.wav",
                      "narr_australia", pasta=str(JOB),
                      exaggeration=0.45, cfg_weight=0.5)
print("ok:", r.get("ok"), "| audio:", r.get("audio_local"), "| erro:", r.get("erro"))
