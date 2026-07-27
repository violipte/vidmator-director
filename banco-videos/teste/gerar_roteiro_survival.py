"""Gerador de roteiro — canal SURVIVAL SCIENCE (mascote Galo veterano, humor + ciência).
Vídeos curtos: 10-13min (~8-10k chars). Modo --sample gera ~5min (~4.5k chars).
Persona: veterano de guerra rabugento, 1ª pessoa, lições pagas "com o olho".

Uso: python gerar_roteiro_survival.py "Theme" [slug] [--sample]
"""
import json
import re
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
TESTE = Path(r"F:/Canal Dark/Aplicativo de Edição/banco-videos/teste")
ROTEIROS = TESTE / "roteiros"
from gemini_api import gemini_text

# PERSONA (nome provisório "Sarge" — trocar quando o Piter batizar o Galo)
BIBLIA = (
    "VOICE & PERSONA (follow strictly): You are SARGE — a grizzled, one-eyed war-veteran rooster who teaches "
    "survival SCIENCE. First person, talking straight to the viewer ('you', 'listen up', 'rookie'). Gruff, "
    "impatient, darkly funny — but everything you teach is REAL, checkable science (physiology, physics, real "
    "documented cases with names and dates). Short punchy sentences. Military flavor without jargon overload. "
    "Once in a while drop a war-story beat ('I lost this eye learning that lesson' — keep it vague and comic, "
    "never graphic). Mock Hollywood and bad advice mercilessly. ALWAYS land the practical takeaway: what to "
    "actually DO, stated plainly. NEVER invent facts, never give advice that could hurt someone if wrong — when "
    "the science says 'it depends', say it. No weapons instructions, no medical dosing, nothing about children. "
    "This is READ ALOUD by TTS: plain spoken prose only — NO asterisks, markdown, headers, bullets, emojis, or "
    "stage directions. Be tight: every sentence earns its place."
)

SECOES_FULL = [
    ("hook", "COLD-OPEN (~120w): a blunt, confronting opening that names the deadly myth/mistake of this video "
             "and promises the real science. End with a hard one-liner.", 120),
    ("m1", "MYTH/POINT 1 (~330w): state the common belief -> demolish it with the REAL science (mechanism, named "
           "researcher/study or documented case) -> the takeaway ('here is what you do instead').", 330),
    ("m2", "MYTH/POINT 2 (~330w): same structure, different angle. Include one short vague war-story beat.", 330),
    ("m3", "MYTH/POINT 3 (~330w): same structure. Make this the most counterintuitive one.", 330),
    ("m4", "MYTH/POINT 4 (~300w): same structure, escalate stakes.", 300),
    ("m5", "MYTH/POINT 5 (~300w): same structure; the deadliest one, saved for last.", 300),
    ("fecho", "CLOSE (~140w): rapid-fire recap of the takeaways in order, one line each; a final gruff sign-off in "
              "persona; then the engagement beat: subscribe ('fall in'), comment your answer to one sharp question, "
              "and click the video on screen.", 140),
]
SECOES_SAMPLE = [
    ("hook", SECOES_FULL[0][1] + " HARD LIMIT: 80 words maximum.", 80),
    ("m1", SECOES_FULL[1][1] + " HARD LIMIT: 210 words maximum.", 210),
    ("m2", SECOES_FULL[2][1] + " HARD LIMIT: 210 words maximum.", 210),
    ("m3", SECOES_FULL[3][1] + " HARD LIMIT: 210 words maximum.", 210),
    ("fecho", SECOES_FULL[6][1] + " HARD LIMIT: 90 words maximum.", 90),
]   # ≈ 800 palavras = ~5min


def _limpar_tts(t):
    if not t:
        return t
    t = re.sub(r"[*_`#>]+", "", t)
    for a, b in [("'", "'"), ("'", "'"), (""", '"'), (""", '"'), ("—", " - "), ("–", " - "), ("…", "...")]:
        t = t.replace(a, b)
    return re.sub(r"[ \t]{2,}", " ", t).strip()


def _llm(prompt, timeout=170):
    for _ in range(2):
        t = gemini_text(prompt + "\n\n" + BIBLIA, timeout)
        if t and len(t.strip()) > 80:
            return _limpar_tts(t)
        time.sleep(2)
    return _limpar_tts(t or "")


def main():
    if len(sys.argv) < 2:
        print('uso: python gerar_roteiro_survival.py "Theme" [slug] [--sample]'); return
    tema = sys.argv[1]
    sample = "--sample" in sys.argv
    args = [a for a in sys.argv[2:] if not a.startswith("--")]
    slug = args[0] if args else re.sub(r"[^a-z0-9]+", "_", tema.lower())[:40].strip("_")
    secoes = SECOES_SAMPLE if sample else SECOES_FULL
    ROTEIROS.mkdir(parents=True, exist_ok=True)
    print(f"=== Roteiro SURVIVAL: '{tema}' | slug={slug} | {'SAMPLE 5min' if sample else 'full 10-13min'} ===")
    t0 = time.time()
    blocos = []
    for nome, instr, pal in secoes:
        print(f"[{nome}]...", flush=True)
        p = (f"Write the '{nome}' section of a survival-science video script. THEME: {tema}. {instr} "
             f"About {pal} words. Do not repeat ground covered by other sections. Write ONLY the spoken prose.")
        blocos.append(_llm(p))
    rot = "\n\n".join(b for b in blocos if b)
    dest = ROTEIROS / f"srv_{slug}.txt"
    dest.write_text(rot, encoding="utf-8")
    pal = len(rot.split())
    print(f"\nOK -> {dest}\npalavras: {pal} | ~min @150wpm: {round(pal/150,1)} | tempo: {round(time.time()-t0)}s")


if __name__ == "__main__":
    main()
