import sys
sys.path.insert(0, r"F:/Canal Dark/Aplicativo de Edição/video-automator")
from pathlib import Path
from narrator_chatterbox import narrar_chatterbox

JOB = Path(r"F:/Canal Dark/Aplicativo de Edição/banco-videos/_job_tubaroes")
texto = (JOB / "roteiro_en.txt").read_text(encoding="utf-8").strip()
# ARQUITETURA DE 2 TRILHAS (06/08): este roteiro NÃO contém a intro do host nem os
# CTAs — eles são falados pelo próprio avatar, com áudio nativo do VEO, e a ilha
# ACRESCENTA tempo ao vídeo. A narração aqui é só o corpo.
r = narrar_chatterbox(texto, r"F:/Canal Dark/Aplicativo de Edição/veo_flow/vozes_ref/voz_AMZ.wav",
                      "narr_tubaroes", pasta=str(JOB),
                      exaggeration=0.45, cfg_weight=0.5)
print("ok:", r.get("ok"), "| audio:", r.get("audio_local"), "| erro:", r.get("erro"))
