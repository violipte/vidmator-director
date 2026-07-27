"""Escolhe a citação REAL do cold-open typewriter a partir do roteiro_en.txt (tema do vídeo).
Saída: coldopen.json = {"quote": "...", "author": "..."} em TESTE/. Fallback por nicho se o LLM falhar.
Uso: python coldopen_quote.py   (NICHO no env; lê roteiro_en.txt)
"""
import json
import os
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
TESTE = Path(r"F:/Canal Dark/Aplicativo de Edição/banco-videos/teste")
from gemini_api import gemini_text

# fallback por nicho: citação REAL segura caso o LLM falhe (nunca deixa o vídeo sem cold-open)
FALLBACK = {
    "ttm": {"quote": "The body keeps the score.", "author": "Bessel van der Kolk"},
    "estoicismo": {"quote": "Be silent for the most part, or say only what is necessary, and in few words.",
                   "author": "Epictetus"},
    "survival": {"quote": "By failing to prepare, you are preparing to fail.", "author": "Benjamin Franklin"},
    "documentario": {"quote": "Those who cannot remember the past are condemned to repeat it.",
                     "author": "George Santayana"},
    "default": {"quote": "Knowing yourself is the beginning of all wisdom.", "author": "Aristotle"},
}


def main():
    nicho = (os.environ.get("NICHO") or "default").lower()
    rot = (TESTE / "roteiro_en.txt").read_text(encoding="utf-8")[:1800]
    p = (f"For a faceless video whose narration begins: \"{rot}\" ... choose ONE real, VERIFIABLE, correctly "
         f"attributed quote that fits the theme (philosopher, mystic, poet, or researcher relevant to the topic). "
         f"The quote MUST be genuine and the attribution correct — if unsure, prefer a very famous safe quote. "
         f"Under 160 characters. Return ONLY a JSON object {{\"quote\": \"...\", \"author\": \"...\"}}.")
    out = gemini_text(p, 60) or ""
    a, b = out.find("{"), out.rfind("}")
    q = {}
    try:
        o = json.loads(out[a:b + 1])
        if o.get("quote") and o.get("author") and len(str(o["quote"])) < 200:
            q = {"quote": str(o["quote"]).strip().strip('"'), "author": str(o["author"]).strip()}
    except Exception:
        pass
    if not q:
        q = FALLBACK.get(nicho, FALLBACK["default"])
        print(f"LLM falhou -> fallback do nicho {nicho}")
    (TESTE / "coldopen.json").write_text(json.dumps(q, ensure_ascii=False), encoding="utf-8")
    print(f'coldopen: "{q["quote"][:70]}" - {q["author"]}')


if __name__ == "__main__":
    main()
