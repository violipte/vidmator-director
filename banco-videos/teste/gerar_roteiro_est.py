"""GERADOR DE ROTEIRO — nicho ESTOICISMO (estilo "memento mori 5 passos", eng. reversa do roteiro aprovado).
Fluxo multi-agente: ARQUITETO (blueprint) -> INTRO -> PASSO×N (5-7) -> FECHO -> monta.
Testável SEM gerar vídeo. Vira pipeline do Automator depois (Fase 2).

Uso: python gerar_roteiro_est.py "Tema/Título do vídeo" [slug] [n_passos]
  ex: python gerar_roteiro_est.py "Amor Fati: Loving Your Fate" amor_fati 6
"""
import json
import random
import re
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
TESTE = Path(r"F:/Canal Dark/Aplicativo de Edição/banco-videos/teste")
ROTEIROS = TESTE / "roteiros"
from gemini_api import gemini_text

# ---- BÍBLIA DE ESTILO (compartilhada por todos os agentes — a "voz" do canal) ----
BIBLIA = (
    "VOICE & STYLE (follow strictly): "
    "Second person, speaking directly to ONE viewer ('you'). Intimate, urgent yet calm, cinematic. "
    "Mix short punchy declaratives with longer flowing sentences; use rhythm via anaphora and parallelism "
    "(e.g. 'Full of X. Full of Y. Full of Z.'). Use rhetorical questions that implicate the viewer. "
    "Ground every abstraction in concrete, sensory images (the phone before feet touch the floor; coffee tasting "
    "better; graveyards full of unwritten books). Cite REAL Stoics with vivid specifics (Marcus Aurelius ruling the "
    "largest empire; Seneca the richest man in Rome; Epictetus born a slave). Sprinkle authentic Latin terms where "
    "they fit (Memento Mori, premeditatio malorum, amor fati, the dichotomy of control). Use the reframe pattern "
    "'This is not meant to X. It is meant to Y.' Dark-but-uplifting: confront a hard truth, then turn it into freedom. "
    "NO filler, NO 'in conclusion', NO meta narration, NO numbered lists. Write flowing PROSE only — no headers, "
    "no bullets, no stage directions, no markdown. "
    "This text will be READ ALOUD by a text-to-speech voice: NEVER use asterisks (*), underscores, quotation marks "
    "for emphasis, or any symbol — write plain spoken sentences only. Be CONCISE: every sentence must earn its place, "
    "do NOT pad or repeat ideas to fill space."
)


def _limpar_tts(t):
    """Remove markdown/símbolos que o TTS leria errado + normaliza para ASCII falável."""
    if not t:
        return t
    t = re.sub(r"[*_`#>]+", "", t)                       # markdown
    for a, b in [("’", "'"), ("‘", "'"), ("“", '"'), ("”", '"'),
                 ("—", " - "), ("–", " - "), ("…", "..."), (" ", " ")]:
        t = t.replace(a, b)
    t = re.sub(r"[ \t]{2,}", " ", t)
    return t.strip()


def _llm(prompt, timeout=200):
    for _ in range(2):
        t = gemini_text(prompt + "\n\n" + BIBLIA, timeout)
        if t and len(t.strip()) > 120:
            return _limpar_tts(t)
        time.sleep(2)
    return _limpar_tts(t or "")


def arquiteto(tema, n):
    p = (f"You are the architect of a faceless YouTube video script in the STOIC 'dark philosophy' style. "
         f"TOPIC: {tema}. Design the blueprint. Return ONLY a JSON object with keys: "
         f"hook (one-sentence blunt, confronting cold-open idea aimed at 'you'), "
         f"concept (the core Stoic idea, with a Latin term if natural), "
         f"stoics (array of 2-4 real Stoics to feature, each as 'Name — one vivid specific fact'), "
         f"passos (array of EXACTLY {n} objects, each with: titulo = an imperative one-line step title in the EXACT "
         f"format 'Step one. <imperative instruction>.' (use the spelled-out ordinal), and foco = one line naming "
         f"the concrete daily practice it teaches). The {n} steps must each be DISTINCT, build as a journey, each "
         f"emphasizing a DIFFERENT Stoic and a DIFFERENT concrete practice. Return ONLY the JSON.")
    raw = gemini_text(p, 150) or ""
    a, b = raw.find("{"), raw.rfind("}")
    try:
        o = json.loads(raw[a:b + 1])
        if o.get("passos"):
            return o
    except Exception as e:
        print("  arquiteto JSON falhou:", str(e)[:60])
    return None


def intro(tema, bp, n):
    p = (f"Write the OPENING of the script (everything BEFORE the steps), about 700-820 words, in 5-6 paragraphs. "
         f"TOPIC: {tema}. Flow: (1) a blunt universal cold-open hook spoken to 'you' [{bp['hook']}]; "
         f"(2) introduce the Stoic concept [{bp['concept']}] and name-drop the authorities ({'; '.join(bp['stoics'])}) "
         f"with vivid specifics; (3) turn it on the viewer with rhetorical questions about how they waste their days; "
         f"(4) paint the cost of denial with concrete imagery; (5) the liberating paradox; (6) a transition that "
         f"PROMISES '{n} practical steps' the viewer can use starting today, and warns each is simple but harder than "
         f"it sounds. Write ONLY the prose.")
    return _llm(p)


def passo(tema, bp, ps, i, n, outras):
    stoic = bp["stoics"][(i - 1) % len(bp["stoics"])]
    p = (f"Write STEP {i} of {n} of the script. TITLE: '{ps['titulo']}'. FOCUS: {ps['foco']}. "
         f"About 430-510 words, 3-4 paragraphs. Internal flow: (a) start with the title line on its own line; "
         f"(b) how most people fail at this; (c) weave in this Stoic and their teaching: {stoic} (add a Latin term "
         f"if authentic); (d) the reframe (why it FREES you); (e) a CONCRETE second-person application that starts "
         f"like 'Here is how you apply it.' with specific, doable actions; (f) a deepening twist or emotional beat. "
         f"Do NOT repeat points covered by the OTHER steps: {outras}. TOPIC: {tema}. "
         f"Write ONLY the prose, beginning with the title line exactly as given.")
    return _llm(p)


def fecho(tema, bp, titulos):
    p = (f"Write the CLOSING of the script, about 360-440 words. TOPIC: {tema}. Flow: (1) a synthesis image (e.g. "
         f"'let death become your advisor'); (2) a crescendo on the beautiful paradox — you will die, everything "
         f"turns to dust, AND YET you get to be alive right now, the rarest gift; (3) a rapid imperative RECAP of the "
         f"steps in order, one clause each: {titulos}; (4) a memorable two-line sign-off built on the core concept "
         f"[{bp['concept']}]. Write ONLY the prose.")
    return _llm(p)


def main():
    if len(sys.argv) < 2:
        print('uso: python gerar_roteiro_est.py "Tema" [slug] [n_passos]'); return
    tema = sys.argv[1]
    slug = sys.argv[2] if len(sys.argv) > 2 else re.sub(r"[^a-z0-9]+", "_", tema.lower())[:40].strip("_")
    n = int(sys.argv[3]) if len(sys.argv) > 3 else random.randint(5, 7)
    ROTEIROS.mkdir(parents=True, exist_ok=True)
    print(f"=== Roteiro EST: '{tema}' | {n} passos | slug={slug} ===")

    t0 = time.time()
    bp = arquiteto(tema, n)
    if not bp:
        print("FALHOU no arquiteto."); return
    n = len(bp["passos"])
    print(f"[arquiteto] {n} passos:")
    for ps in bp["passos"]:
        print("   -", ps["titulo"])

    print("[intro]..."); blocos = [intro(tema, bp, n)]
    titulos = [ps["titulo"] for ps in bp["passos"]]
    for i, ps in enumerate(bp["passos"], 1):
        print(f"[passo {i}/{n}] {ps['titulo'][:50]}...")
        outras = " | ".join(t for j, t in enumerate(titulos, 1) if j != i)
        blocos.append(passo(tema, bp, ps, i, n, outras))
    print("[fecho]..."); blocos.append(fecho(tema, bp, " ; ".join(titulos)))

    roteiro = "\n\n".join(b for b in blocos if b)
    dest = ROTEIROS / f"est_{slug}.txt"
    dest.write_text(roteiro, encoding="utf-8")
    pal = len(roteiro.split())
    # blueprint ao lado (auditoria/depuração)
    (ROTEIROS / f"est_{slug}.blueprint.json").write_text(json.dumps(bp, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nOK -> {dest}")
    print(f"palavras: {pal} | ~min @150wpm: {round(pal/150,1)} | tempo: {round(time.time()-t0)}s")


if __name__ == "__main__":
    main()
