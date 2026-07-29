# -*- coding: utf-8 -*-
"""AVATAR v3 (29/07) — gera os PROMPTS do Flow/VEO pros slots de apresentador.

O style_card define a persona e onde o avatar entra; este script pega a LINHA
EXATA do roteiro em cada slot e monta o prompt @Personagem pro Flow (VEO 3.1,
fala nativa + lip-sync). Saída: <job>/avatar_prompts.md — é rodar no Flow
(veo_flow/FLOW_MAP.md), baixar, passar no `python veo_flow/curador.py` e apontar
os aprovados no style_card["avatar"]["ilhas"].

style_card["avatar"]:
  "persona":      "Marcus"
  "persona_desc": "a wise elderly stoic philosopher with a short gray beard, ..."
  "cenas":        {"default": "in a candlelit stone study", "3": "on a rooftop at dawn"}
  "slots":        [1, 3, 6]     (seções onde o avatar abre falando)

Uso: python avatar_prompts.py --job <dir> --plano plano.json
"""
import argparse
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")


def linha_do_slot(plano, sec_i, max_palavras=22):
    """Frase(s) iniciais da seção — o que o avatar VAI FALAR (~8s ≈ 20-24 palavras)."""
    beats = [b for b in plano.get("beats", []) if b.get("secao") == sec_i and b.get("texto")]
    beats.sort(key=lambda b: b.get("t_ini", 0))
    palavras = []
    for b in beats:
        palavras += b["texto"].split()
        if len(palavras) >= max_palavras:
            break
    frase = " ".join(palavras[:max_palavras + 6])
    m = re.search(r"^(.*?[.!?])(?:\s|$)", frase)  # fecha na 1ª pontuação depois do mínimo
    if m and len(m.group(1).split()) >= 6:
        return m.group(1)
    return " ".join(palavras[:max_palavras]).rstrip(",;: ") + "."


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--job", required=True)
    ap.add_argument("--plano", required=True)
    a = ap.parse_args()

    job = Path(a.job)
    plano = json.loads(Path(a.plano).read_text(encoding="utf-8"))
    sc = json.loads((job / "style_card.json").read_text(encoding="utf-8"))
    av = sc.get("avatar") or {}
    nome = av.get("persona") or "Presenter"
    desc = av.get("persona_desc") or "a charismatic presenter"
    cenas = av.get("cenas") or {}
    slots = av.get("slots") or [s.get("i") for s in plano.get("secoes", [])[1:4]]

    titulos = {s.get("i"): s.get("titulo", "") for s in plano.get("secoes", [])}
    linhas = [f"# Prompts de AVATAR — {nome} ({job.name})",
              "",
              "Fluxo: Flow (VEO 3.1, modelo *Lower Priority*, 8s) → baixar → "
              "`python veo_flow/curador.py \"<pasta>\"` → aprovados no "
              "`style_card[\"avatar\"][\"ilhas\"]` = {\"<seção>\": \"<arquivo>\"}.",
              "",
              f"**Persona-mãe** (gerar 1x, salvar como personagem `@{nome}` no Flow):",
              f"> Cinematic portrait, {desc}. Neutral standing pose, looking at camera, "
              f"full body visible, soft key light. No text, no logos.",
              ""]
    for s_i in slots:
        fala = linha_do_slot(plano, int(s_i))
        cena = cenas.get(str(s_i)) or cenas.get("default") or "in a fitting scene for the topic"
        linhas += [f"## Seção {s_i} — {titulos.get(int(s_i), '')}",
                   f"```",
                   f"Cinematic medium shot, @{nome} {cena}. {nome} looks straight at the "
                   f"camera and says, in English: \"{fala}\" Natural hand gestures, subtle "
                   f"slow push-in, shallow depth of field, warm cinematic grade. "
                   f"No captions, no subtitles, no on-screen text.",
                   f"```",
                   ""]
    out = job / "avatar_prompts.md"
    out.write_text("\n".join(linhas), encoding="utf-8")
    print(f"{len(slots)} prompts -> {out}")


if __name__ == "__main__":
    main()
