# -*- coding: utf-8 -*-
"""TABELA DE DECISÕES do Diretor — trecho falado x o que aparece na tela x por quê.
A visão que o Piter pediu (22/07): auditar a INTELIGÊNCIA sem assistir o vídeo.

Uso: python tabela_decisoes.py <plano.json> <montagem.json> <saida.md>
"""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")


def resumo_tela(b):
    c = b.get("componente") or ""
    p = b.get("props") or {}
    if b.get("src"):
        nome = Path(b["src"]).name
        fonte = "YouTube T3" if "__T3__" in nome else "Commons T2" if "__T2__" in nome else "stock T1"
        tipo = {"ilustracao": "ILUSTRAÇÃO GERADA"}.get(b["tipo"], f"FOOTAGE {fonte}")
        return f"{tipo}: {nome[-42:]}"
    if b.get("bg_nitido"):
        return f"📅 ANO **{p.get('text')}** gigante sobre o footage ({Path(b.get('bg', '')).name[-30:]})"
    if c.startswith("Graf"):
        vals = p.get("values") or []
        labs = p.get("labels") or []
        par = " vs ".join(f"{l} {v}{p.get('suffix', '')}" for l, v in zip(labs, vals)) if labs \
            else " / ".join(f"{v}{p.get('suffix', '')}" for v in vals)
        return f"📊 {c}: \"{p.get('title', '')}\" — {par}"
    if c.startswith("Map"):
        alvo = ", ".join(p.get("paises") or []) or ", ".join((pt.get("nome") or "?") for pt in (p.get("pontos") or []))
        return f"🗺️ {c}: {alvo}"
    if c == "CharacterCard":
        return f"👤 CharacterCard: {p.get('title')} ({p.get('subtitle', '')[:30]}) + retrato"
    if c.startswith("Img"):
        n = len(p.get("images") or [])
        return f"🖼️ {c}: {n} foto(s) reais"
    if c.startswith("Soc"):
        return f"📰 {c}: \"{(p.get('titulo') or '')[:40]}\""
    if c == "ChapterTitle":
        return f"🎬 CAPÍTULO {p.get('chapterNumber')}: \"{p.get('title')}\""
    if c.startswith(("Texto", "Ovl")):
        return f"✏️ {c}: \"{(p.get('text') or '')[:52]}\""
    return c or "(vazio)"


def origem(b, pb, secoes):
    c = b.get("componente") or ""
    if b.get("bg_nitido"):
        return "R-27: ano falado vira data na tela"
    if c == "Ovl02_SubchapterLine" and any((s.get("titulo") or "") == (b.get("props") or {}).get("text") for s in secoes):
        return "R-64: capítulo (estilo minimal do nicho)"
    if c == "ChapterTitle":
        return "R-64: capítulo (estilo cinematic)"
    if b.get("src") and pb.get("tipo") in ("footage_video", "footage_imagem", "stock"):
        return "busca do LLM + gate Vision"
    if b.get("src") and pb.get("tipo") == "ilustracao":
        return "ilustrador IA (prompt do LLM)"
    if b.get("src"):
        return "demote R-56/62: texto excedente virou b-roll da seção"
    if c and c == pb.get("componente"):
        return "pedido do LLM validado pelo registry"
    if c.startswith("Graf") and pb.get("estrategia") == "dado":
        return "R-26: dado forte cravou chart (re-pick)"
    if pb.get("tipo") in ("footage_video", "stock", "footage_imagem"):
        return "fallback: footage reprovado no gate → registry escolheu animação"
    return "re-pick do registry (dados não sustentavam o pedido original)"


def main():
    plano = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    m = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
    out = Path(sys.argv[3])
    pb_por_i = {b["i"]: b for b in plano["beats"]}
    secoes = m.get("secoes", [])

    linhas = ["# Tabela de decisões do Diretor",
              f"\n{len(m['beats'])} beats | {m['dur_s']:.0f}s | gerada de plano+montagem (o que REALMENTE renderiza)\n",
              "| # | tempo | O QUE O NARRADOR FALA | O QUE APARECE NA TELA | POR QUÊ |",
              "|---|-------|------------------------|------------------------|---------|"]
    for b in m["beats"]:
        pb = pb_por_i.get(b["i"], {})
        tx = (pb.get("texto") or "").replace("|", "/")[:80]
        tela = resumo_tela(b).replace("|", "/")
        why = origem(b, pb, secoes)
        linhas.append(f"| {b['i']} | {b['t_ini']:.0f}-{b['t_fim']:.0f}s | {tx} | {tela} | {why} |")
    out.write_text("\n".join(linhas), encoding="utf-8")
    print(f"{len(m['beats'])} linhas -> {out}")


if __name__ == "__main__":
    main()
