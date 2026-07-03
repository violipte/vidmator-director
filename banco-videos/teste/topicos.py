"""Pass ADITIVO: segmenta o roteiro em TÓPICOS (capítulos/blocos coerentes) com
timestamp de fronteira + mood dominante. Base para: glitch só na fronteira de
tópico, e corte seco de trilha por tópico. Escreve 'topicos' no timeline.json.
"""
import json
import re
import subprocess
import sys
import urllib.request
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

TESTE = Path(r"F:/Canal Dark/Aplicativo de Edição/banco-videos/teste")
ROTEIRO = TESTE / "roteiro_en.txt"
WORDS = TESTE / "words.json"
TIMELINE = TESTE / "timeline.json"
CREDS = Path(r"F:/Canal Dark/Aplicativo de Edição/video-automator/credentials.json")
MOODS = {"tense", "dark", "mysterious", "somber", "neutral"}


def norm(s):
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def _parse_arr(txt):
    a, b = txt.find("["), txt.rfind("]")
    if a >= 0 and b > a:
        try:
            return json.loads(txt[a:b + 1])
        except Exception:
            return None
    return None


def _prompt(roteiro):
    return (
        "Segment this documentary narration into its main TOPICS (coherent chapters/sections — e.g. each "
        "distinct case, person, or theme is its own topic; the intro is its own topic). Aim for 3 to 7 topics. "
        "For EACH return: titulo (a SHORT title), trecho (the exact 3 to 6 consecutive words FROM THE SCRIPT "
        "that START the topic, verbatim), mood (the dominant mood of the topic: one of tense, dark, mysterious, "
        "somber, neutral). Return ONLY a JSON array of objects with keys titulo, trecho, mood, in script order. "
        "Script: " + roteiro.replace(chr(34), "").replace("\n", " ")
    )


def gemini(roteiro):
    from gemini_api import gemini_arr
    arr = gemini_arr(_prompt(roteiro), 180)   # API (8 chaves) + retry se JSON vier corrompido -> CLI fallback
    return arr if arr is not None else []


def localizar(trecho, words):
    alvo = [norm(t) for t in (trecho or "").split() if norm(t)]
    if not alvo or not words:
        return None
    wn = [norm(w["word"]) for w in words]
    for i in range(len(wn) - len(alvo) + 1):
        if wn[i:i + len(alvo)] == alvo:
            return round(words[i]["start"], 2)
    fortes = [t for t in alvo if len(t) >= 4]
    for i, w in enumerate(wn):
        if fortes and w == fortes[0]:
            return round(words[i]["start"], 2)
    return None


def main():
    roteiro = ROTEIRO.read_text(encoding="utf-8")
    words = json.load(open(WORDS, encoding="utf-8")) if WORDS.exists() else []
    tl = json.load(open(TIMELINE, encoding="utf-8"))
    dur = tl.get("duracao", words[-1]["end"] if words else 0)

    print("=== Segmentação de tópicos ===")
    segs = gemini(roteiro)
    topicos = []
    for i, s in enumerate(segs):
        ini = 0.0 if i == 0 else localizar(s.get("trecho"), words)
        if ini is None:
            continue
        mood = (s.get("mood") or "neutral").strip().lower()
        topicos.append({"inicio": round(ini, 2), "titulo": s.get("titulo", f"Tópico {i+1}"),
                        "mood": mood if mood in MOODS else "neutral"})
    # ordena, dedup, calcula fim
    topicos.sort(key=lambda t: t["inicio"])
    uniq = []
    for t in topicos:
        if uniq and t["inicio"] - uniq[-1]["inicio"] < 6:
            continue
        uniq.append(t)
    for i, t in enumerate(uniq):
        t["fim"] = round(uniq[i + 1]["inicio"], 2) if i < len(uniq) - 1 else round(dur, 2)

    tl["topicos"] = uniq
    json.dump(tl, open(TIMELINE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"OK: {len(uniq)} tópicos")
    for t in uniq:
        print(f"  {t['inicio']:>6.1f}-{t['fim']:>6.1f}s  [{t['mood']:<10}] {t['titulo']}")


if __name__ == "__main__":
    main()
