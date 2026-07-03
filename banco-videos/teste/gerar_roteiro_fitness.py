"""Gerador de roteiro — nicho FITNESS/ESPIRITUAL (Shaolin/calistenia instrucional).
Fluxo multi-agente: arquiteto (premissa + atribui foco/reps aos 6 exercícios DA biblioteca de animação)
-> intro -> exercício×6 -> fecho. Exercícios TRAVADOS no set animável (cobertura garantida das animações).
Alvo ~15min. Uso: python gerar_roteiro_fitness.py "Tema" [slug]
"""
import json
import os
import re
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
TESTE = Path(r"F:/Canal Dark/Aplicativo de Edição/banco-videos/teste")
ROTEIROS = TESTE / "roteiros"
from gemini_api import gemini_text

# exercícios = chaves do ExerciseAnim.tsx (garante que toda demo tem animação)
EXERCICIOS = [
    ("squat", "Deep Squat"), ("pushup", "Push-Up"), ("plank", "Plank"),
    ("legraise", "Leg Raise"), ("lunge", "Forward Lunge"), ("horse", "Horse Stance (Mǎbù)"),
]

BIBLIA = (
    "VOICE & STYLE (follow strictly): direct, second person ('you'), grounded and motivating, like a calm Shaolin "
    "master who is also a practical coach. Mix the SPIRITUAL (discipline, breath, presence, the body as a temple) "
    "with the PRACTICAL (clear how-to, form, reps). Confident, energetic but never hype-y or fake. Use concrete cues "
    "the listener can feel (feet rooted, spine long, breath through the nose). Short punchy lines + flowing ones. "
    "This text is READ ALOUD by TTS: NEVER use asterisks, markdown, emojis, headers, or any symbol — plain spoken "
    "sentences only. Be CONCISE, no padding. Write flowing PROSE only."
)


def _limpar_tts(t):
    if not t:
        return t
    t = re.sub(r"[*_`#>]+", "", t)
    for a, b in [("'", "'"), ("'", "'"), (""", '"'), (""", '"'), ("—", " - "), ("–", " - "), ("…", "...")]:
        t = t.replace(a, b)
    return re.sub(r"[ \t]{2,}", " ", t).strip()


def _llm(prompt, timeout=160):
    for _ in range(2):
        t = gemini_text(prompt + "\n\n" + BIBLIA, timeout)
        if t and len(t.strip()) > 100:
            return _limpar_tts(t)
        time.sleep(2)
    return _limpar_tts(t or "")


# fallback caso o LLM falhe — os 6 exercícios são fixos de qualquer forma
DEFAULT_EX = [
    {"nome": "Deep Squat", "reps": "x 20", "fixes": "weak legs, stiff hips, poor posture", "angle": "Root yourself like a mountain"},
    {"nome": "Push-Up", "reps": "x 15", "fixes": "weak chest and arms, collapsed shoulders", "angle": "Push the earth away with control"},
    {"nome": "Plank", "reps": "45s", "fixes": "a weak core and an aching lower back", "angle": "Stillness is its own kind of strength"},
    {"nome": "Leg Raise", "reps": "x 15", "fixes": "a soft midsection and weak hip flexors", "angle": "Lift with control, never momentum"},
    {"nome": "Forward Lunge", "reps": "x 12 / side", "fixes": "imbalance, weak knees, instability", "angle": "Every step is a moving meditation"},
    {"nome": "Horse Stance (Mǎbù)", "reps": "60s", "fixes": "no foundation and a restless, scattered mind", "angle": "The stance that forges the warrior"},
]


def arquiteto(tema):
    lista = ", ".join(n for _, n in EXERCICIOS)
    p = (f"You are the architect of a faceless Shaolin/calisthenics fitness video. TITLE: {tema}. "
         f"The video teaches EXACTLY these 6 bodyweight exercises, in this order: {lista}. "
         f"For EACH, give: nome (EXACTLY as given), fixes (the real weakness/problem it fixes, 1 short line), "
         f"reps (e.g. 'x 15' or '45s'), angle (a 1-line Shaolin spiritual+practical teaching hook). "
         f"Return ONLY a strict JSON ARRAY of 6 objects [{{nome, fixes, reps, angle}}], double-quoted, no trailing "
         f"commas, no markdown.")
    from gemini_api import gemini_arr
    arr = gemini_arr(p, 120) or []
    arr = [e for e in arr if isinstance(e, dict) and e.get("nome")]
    if len(arr) >= 6:
        return arr[:6]
    print(f"  arquiteto retornou {len(arr)} — usando fallback DEFAULT_EX")
    return DEFAULT_EX


def intro(tema):
    p = (f"Write the OPENING of the script (before the exercises), about 320-400 words, 3-4 paragraphs. TITLE: {tema}. "
         f"Flow: (1) a hook that grabs — the body holds the answer to most of your problems and you have neglected it; "
         f"(2) the Shaolin framing — for centuries the monks built unbreakable bodies and calm, focused minds with "
         f"nothing but their own bodyweight, breath, and relentless discipline; (3) promise 6 simple bodyweight "
         f"exercises that fix 95 percent of what holds you back, each simple but harder than it looks. Write ONLY the prose.")
    return _llm(p)


def exercicio(tema, ex, i, n):
    p = (f"Write section for EXERCISE {i} of {n}: {ex['nome']} ({ex['reps']}). About 240-300 words, 2-3 paragraphs. "
         f"It FIXES: {ex['fixes']}. Teaching angle: {ex['angle']}. Flow: (a) start with the exercise NAME on its own "
         f"line; (b) what weakness/problem most people have that this fixes; (c) HOW to do it - clear form cues and "
         f"breathing, like a coach; (d) the Shaolin/spiritual point (discipline, presence, the body as training "
         f"ground for the mind); (e) end with the rep target ({ex['reps']}). TITLE of video: {tema}. "
         f"Write ONLY the prose, beginning with the exercise name line.")
    return _llm(p)


def fecho(tema, nomes):
    p = (f"Write the CLOSING, about 200-260 words. TITLE: {tema}. Flow: (1) tie the 6 exercises into a daily practice "
         f"({', '.join(nomes)}) - consistency over intensity, the monk's way; (2) the deeper point: training the body "
         f"is training the will, and a disciplined body builds a calm, unshakeable mind; (3) a short, memorable "
         f"call to start today. Write ONLY the prose.")
    return _llm(p)


def main():
    if len(sys.argv) < 2:
        print('uso: python gerar_roteiro_fitness.py "Tema" [slug]'); return
    tema = sys.argv[1]
    slug = sys.argv[2] if len(sys.argv) > 2 else re.sub(r"[^a-z0-9]+", "_", tema.lower())[:40].strip("_")
    ROTEIROS.mkdir(parents=True, exist_ok=True)
    print(f"=== Roteiro FITNESS: '{tema}' | 6 exercícios | slug={slug} ===")
    t0 = time.time()
    exs = arquiteto(tema)[:6]
    n = len(exs)
    for e in exs:
        print("   -", e.get("nome"), "|", e.get("reps"), "|", e.get("fixes", "")[:50])
    print("[intro]..."); blocos = [intro(tema)]
    for i, e in enumerate(exs, 1):
        print(f"[exercício {i}/{n}] {e.get('nome')}")
        blocos.append(exercicio(tema, e, i, n))
    print("[fecho]..."); blocos.append(fecho(tema, [e.get("nome") for e in exs]))
    roteiro = "\n\n".join(b for b in blocos if b)
    dest = ROTEIROS / f"fit_{slug}.txt"
    dest.write_text(roteiro, encoding="utf-8")
    (ROTEIROS / f"fit_{slug}.blueprint.json").write_text(json.dumps(exs, ensure_ascii=False, indent=2), encoding="utf-8")
    pal = len(roteiro.split())
    print(f"\nOK -> {dest}\npalavras: {pal} | ~min @150wpm: {round(pal/150,1)} | tempo: {round(time.time()-t0)}s")


if __name__ == "__main__":
    main()
