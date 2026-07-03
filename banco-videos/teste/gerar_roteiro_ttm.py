"""Gerador de roteiro — canal TTM (espiritualidade + saúde/somático).
Fluxo: TEMA -> PREMISSA -> ROTEIRO (EN), seguindo a espinha dorsal de 9 partes
(eng. reversa do exemplo TRE/Modo Deus). Escolhe também a citação real do cold-open.
Output = roteiro narrado em INGLÊS (ttm_<slug>.txt) + meta (premissa + quotes).
Uso: python gerar_roteiro_ttm.py "Theme" [slug]
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

BIBLIA = (
    "VOICE & STYLE (follow strictly): English, second person ('you'). Calm, hypnotic AUTHORITY — a guide revealing an "
    "ancient secret that modern science is only now validating. WEAVE three registers: the MYSTICAL/ancient (real "
    "traditions, hermetic principles, the body as the soul's first translator), the SCIENTIFIC (real named "
    "researchers, real mechanisms), and the PRACTICAL (a concrete, doable protocol). Long immersive flowing sentences "
    "mixed with short declaratives; build awe AND intimacy. Reframe the viewer's problem as a forgotten doorway, not a "
    "flaw. Concrete, sensory, embodied language. Cite only REAL, verifiable people/works. "
    "This is READ ALOUD by TTS: NEVER use asterisks, markdown, headers, emojis or symbols — plain spoken prose only. "
    "No meta narration. Be substantive, not padded. "
    "CRITICAL — open every section with a BOLD DECLARATIVE statement of truth stated as absolute fact, with quiet "
    "authority. NEVER open with a rhetorical question or soft creator hooks like 'you've felt it', 'have you ever', "
    "'what if', 'imagine', 'picture this'. Declare; do not ask."
)

# espinha dorsal: (nome, instrução, palavras-alvo)
SECOES = [
    ("opening", "The FIRST line must be SHORT and ARRESTING — a bold reframe of the theme stated as fact (e.g. for "
     "hips/fear: 'Your hips are not tight. They are afraid.'). Absolutely NO question, NO 'you've felt it'. Then, with "
     "ominous calm authority, implicate the viewer: while they keep doing the obvious wrong thing, name the hidden cost "
     "crystallizing in the body that no ordinary effort can dissolve. Invoke that ancient traditions always knew this, "
     "and name the modern expert who rediscovered it. Build the stakes - what stays frozen if they keep ignoring this - "
     "and end the opening promising not information, but a felt transformation in their own body.", 1000),
    ("mechanism", "Explain the REAL mechanism in the body — what is physically happening (the relevant muscle, fascia, "
     "nervous system), and name the real expert/researcher whose work underpins it. Make the invisible visible.", 430),
    ("ancient_wisdom", "Reveal that ancient traditions always knew this. Weave 3-4 REAL traditions/practices + one "
     "hermetic principle. Frame the modern expert as having REDISCOVERED an ancient language, not invented a technique.", 430),
    ("modern_science", "Show modern science validating it. Name REAL theories/researchers/works that fit (e.g. polyvagal "
     "theory - Stephen Porges; The Body Keeps the Score - Bessel van der Kolk; neuroplasticity; fascia research; "
     "epigenetics). Make the science feel like confirmation of the mystical.", 430),
    ("protocol", "Give the PRACTICAL protocol — what to do INSTEAD, exactly as the theme implies, step by step in clear "
     "phases or cycles. Specific, embodied, doable today. Breath, position, what to feel.", 460),
    ("story", "<<VARIÁVEL: ver STORY_VARIANTS / historia()>>", 400),
    ("obstacle", "Name the cultural conditioning / inner resistance that blocks this (why people keep doing the wrong "
     "thing) + how to transmute that resistance + how to start small and safely.", 380),
    ("integration", "The integration and close: the deeper truth the journey revealed, a SECOND real attributed quote "
     "(somatic pioneer, mystic or poet), and a reframe of the theme's key concept as biological RESTORATION, not "
     "mysticism — a return to an original state.", 380),
    ("cta", "The CTA: invite the viewer to like, subscribe and turn on notifications to grow this somatic wisdom; give "
     "a specific first-person DECLARATION for them to type in the comments; ask them to share; tell them to click the "
     "screen for another video; tie back to the channel's mission.", 200),
]


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
        if t and len(t.strip()) > 100:
            return _limpar_tts(t)
        time.sleep(2)
    return _limpar_tts(t or "")


def premissa(tema):
    p = (f"Write the PREMISE of a faceless somatic-spiritual video. THEME: {tema}. The premise is the DENSE core thesis "
         f"(about 150-200 words, ONE rich paragraph) that distills the ENTIRE video: the hidden truth behind the theme, "
         f"what is really happening in the body, the named mechanism or expert behind it, and the transformation "
         f"promised. It is the seed the whole script grows from. Write ONLY the paragraph, in English.")
    return _llm(p, 150)


def quote(tema):
    p = (f"For a faceless somatic-spiritual video on THEME: {tema}, choose ONE real, VERIFIABLE, correctly attributed "
         f"quote that fits thematically (a philosopher, mystic, poet like Rumi, or somatic pioneer like Peter Levine or "
         f"Bessel van der Kolk). The quote MUST be genuine and the attribution correct. Return ONLY a JSON object "
         f"{{\"quote\": \"...\", \"author\": \"...\"}}.")
    raw = gemini_text(p, 60) or ""
    a, b = raw.find("{"), raw.rfind("}")
    try:
        o = json.loads(raw[a:b + 1])
        return {"quote": _limpar_tts(o.get("quote", "")), "author": str(o.get("author", "")).strip()}
    except Exception:
        return {"quote": "", "author": ""}


def secao(tema, prem, nome, instrucao, palavras):
    p = (f"Write the '{nome}' section of the script. THEME: {tema}. It must be grounded in and grow from this PREMISE: "
         f"\"{prem}\". {instrucao} About {palavras} words. English, flowing prose, no section headers. Write ONLY the prose.")
    return _llm(p)


# --- CTA de produto (soft-sell narrado, cedo no roteiro, ~20%) ---
PRODUTO_FULL = ("Special Guide: Healing in Motion - 22 Somatic Cycles, Release Trauma, "
                "Restore Flow and Return to Creation")
CTA_ANGLES = [
    "Begin by naming the common enemy head-on, like exposing a hidden villain that has been running the viewer's life.",
    "Begin with a beat of deep recognition - describe the exact private frustration the viewer lives with every day.",
    "Begin by revealing WHY everything they have tried so far has quietly failed them.",
    "Begin with a quiet, almost confessional turn toward the viewer, as if sharing something rarely spoken.",
]


# beat 6 (história) VARIÁVEL — pra não repetir "case com personagem nomeado" em TODO vídeo
STORY_VARIANTS = [
    "Tell the transformation story of a NAMED character who lived this - full emotional arc: the silent suffering, the "
    "moment of surrender, the release, the changed life. Specific and human.",
    "Do NOT use a single named person. Paint the COLLECTIVE pattern instead - the kind of person this happens to "
    "('those who carry...', 'the ones who...') as an archetype the viewer recognizes themselves in.",
    "Use a METAPHOR or short parable - from nature, myth, or the body's own logic - that illustrates the "
    "transformation, rather than a personal case study.",
    "Walk the VIEWER through what THEY will notice in their OWN body, session by session - a second-person "
    "experiential arc, not a third-person character.",
    "Tell it through a LINEAGE - practitioners and seekers across cultures and centuries who walked this path - "
    "rather than a single modern character.",
]


def historia(tema, prem):
    import random
    return secao(tema, prem, "transformation", random.choice(STORY_VARIANTS), 400)


def cta_produto(tema, prem):
    import random
    angle = random.choice(CTA_ANGLES)
    p = (f"Write a persuasive SPOKEN mid-video soft-sell (about 200-240 words), woven as natural flowing narration (NOT "
         f"a list, no headers), for THEME: {tema}. Context premise (do NOT restate or echo its phrases - the viewer "
         f"just heard it; bring a FRESH, vivid framing of the problem instead): \"{prem}\". The SOLUTION, RESULTS, "
         f"SOCIAL PROOF and URGENCY are the HEART of this block - spend most words there. Move smoothly through this exact "
         f"arc: (1) PROBLEM - name the common enemy behind the theme, the real villain; (2) RECOGNITION - make the "
         f"viewer feel deeply SEEN, the usual fixes they keep trying that keep failing; (3) SOLUTION - introduce the "
         f"product naturally and by name: '{PRODUTO_FULL}', a special guide built around 22 somatic cycles; "
         f"(4) RESULTS - the concrete shifts it delivers (release stored trauma, restore flow, return to creation); "
         f"(5) SOCIAL PROOF - point them to the REAL transformations people have shared, pinned in the FIRST comment; "
         f"(6) URGENCY - the link is available for a LIMITED TIME only, in that first pinned comment. {angle} "
         f"Warm, grounded, authoritative - it must feel like a trusted guide letting them in on something, NEVER like a "
         f"cheesy or hypey ad. English. Write ONLY the prose.")
    return _llm(p)


CTA_APOS_CHARS = 6500   # CTA de produto entra após o mecanismo (opening~5k + mechanism~2.7k ≈ 7.5k chars, ~8min/~30%)


def montar(tema, prem):
    """Monta os blocos do roteiro na ordem, inserindo o CTA de produto quando acumular ~7-8k chars."""
    blocos, cta_inserido = [], False
    for nome, instr, pal in SECOES:
        print(f"[{nome}]...", flush=True)
        bloco = historia(tema, prem) if nome == "story" else secao(tema, prem, nome, instr, pal)
        blocos.append(bloco)
        if not cta_inserido and nome != "cta" and sum(len(b or "") for b in blocos) >= CTA_APOS_CHARS:
            print("[cta_produto - soft sell ~8min]...", flush=True)
            blocos.append(cta_produto(tema, prem))
            cta_inserido = True
    if not cta_inserido:   # roteiro curto -> insere antes do CTA de engajamento final
        blocos.insert(max(0, len(blocos) - 1), cta_produto(tema, prem))
    return blocos


def main():
    if len(sys.argv) < 2:
        print('uso: python gerar_roteiro_ttm.py "Theme" [slug]'); return
    tema = sys.argv[1]
    slug = sys.argv[2] if len(sys.argv) > 2 else re.sub(r"[^a-z0-9]+", "_", tema.lower())[:42].strip("_")
    ROTEIROS.mkdir(parents=True, exist_ok=True)
    print(f"=== Roteiro TTM: '{tema}' | slug={slug} ===")
    t0 = time.time()

    print("[premissa]...")
    prem = premissa(tema)
    print("  PREMISSA:", prem[:160], "...")
    print("[citação cold-open]...")
    q = quote(tema)
    print(f"  QUOTE: \"{q['quote'][:80]}\" - {q['author']}")

    blocos = montar(tema, prem)

    roteiro = "\n\n".join(b for b in blocos if b)
    dest = ROTEIROS / f"ttm_{slug}.txt"
    dest.write_text(roteiro, encoding="utf-8")
    meta = {"tema": tema, "premissa": prem, "cold_open_quote": q}
    (ROTEIROS / f"ttm_{slug}.meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    pal = len(roteiro.split())
    print(f"\nOK -> {dest}\npalavras: {pal} | ~min @150wpm: {round(pal/150,1)} | tempo: {round(time.time()-t0)}s")
    print("(quotes precisam de verificação — risco de hallucination)")


if __name__ == "__main__":
    main()
