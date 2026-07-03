"""Transcreve a narração com faster-whisper word-level timestamps.
Roda no venv chatterbox (CUDA). Saída: words.json [{word, start, end}].
"""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

MP3 = Path(r"F:/Canal Dark/Aplicativo de Edição/banco-videos/teste/narracao_joanne.mp3")
OUT = Path(r"F:/Canal Dark/Aplicativo de Edição/banco-videos/teste/words.json")

from faster_whisper import WhisperModel

device, compute = "cuda", "float16"
try:
    model = WhisperModel("base", device=device, compute_type=compute)
except Exception as e:
    print(f"CUDA falhou ({e}); caindo pra CPU")
    model = WhisperModel("base", device="cpu", compute_type="int8")

print("Transcrevendo (word-level)...")
segments, info = model.transcribe(str(MP3), language="en", word_timestamps=True, vad_filter=False)

words = []
for seg in segments:
    for w in (seg.words or []):
        words.append({"word": w.word.strip(), "start": round(w.start, 3), "end": round(w.end, 3)})

OUT.write_text(json.dumps(words, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"OK {len(words)} palavras -> {OUT}")
if words:
    print(f"  primeira: {words[0]}")
    print(f"  última:   {words[-1]}")
