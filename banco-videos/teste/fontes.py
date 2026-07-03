"""Pass do Director: escolhe o TEMA DE FONTE por NICHE/tom do roteiro (Gemini CLI).
Grava timeline['fonte_tema'] in {serif|impact|typewriter|clean}. Niche-agnóstico.

Uso: python fontes.py   (lê roteiro_en.txt; atualiza timeline.json)
"""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
TESTE = Path(r"F:/Canal Dark/Aplicativo de Edição/banco-videos/teste")
ROTEIRO = TESTE / "roteiro_en.txt"
TIMELINE = TESTE / "timeline.json"
TEMAS = {"serif", "impact", "typewriter", "clean"}


def escolher_tema(roteiro):
    prompt = (
        "Read this documentary narration and pick the BEST on-screen FONT THEME for its niche and tone. "
        "Choose exactly one of: "
        "serif (history, classic, philosophy, biography, somber/epic — elegant) | "
        "impact (true crime shocking, breaking news, sensational, bold/punchy) | "
        "typewriter (mystery, investigation, conspiracy, unsolved case, noir/dossier feel) | "
        "clean (modern, tech, science, business, self-help, explainer). "
        "Return ONLY a JSON object with one field tema whose value is one of those four words. Script: "
        + roteiro.replace(chr(34), "").replace("\n", " ")[:6000])
    from gemini_api import gemini_text   # cascata Gemini -> GPT-5 -> Claude
    out = gemini_text(prompt, 120)
    a, b = out.find("{"), out.rfind("}")
    if a >= 0 and b > a:
        try:
            t = str(json.loads(out[a:b + 1]).get("tema", "")).lower().strip()
            if t in TEMAS:
                return t
        except Exception:
            pass
    return "serif"  # fallback seguro


def main():
    tl = json.load(open(TIMELINE, encoding="utf-8"))
    from preset import carregar
    P = carregar(tl)
    hint = P.get("fonte_hint")
    if hint in TEMAS:
        tema = hint
        print(f"  preset nicho={P['_nicho']} -> fonte {tema} (hint do preset)")
    else:
        tema = escolher_tema(ROTEIRO.read_text(encoding="utf-8"))
    tl["fonte_tema"] = tema
    json.dump(tl, open(TIMELINE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"OK -> fonte_tema = {tema}")


if __name__ == "__main__":
    main()
