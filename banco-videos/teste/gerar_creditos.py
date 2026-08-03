# -*- coding: utf-8 -*-
"""CRÉDITOS do job (02/08) — bloco pronto pra descrição do vídeo.

CC-BY e CC-BY-SA são livres para uso comercial MAS exigem atribuição. Sem o crédito
a licença está sendo violada — mesmo o material sendo "grátis". Com iNaturalist,
Wikimedia, Flickr e GBIF no pool isso deixou de ser detalhe: no job amazônico, 39
dos 112 assets exigem crédito.

Lê `resolvido/b*.json` (o curador propaga `atribuicao`/`licenca`) e escreve
CREDITOS.txt no job, deduplicado e ordenado.

Uso: python gerar_creditos.py --job <dir>
"""
import argparse
import json
import sys
from collections import OrderedDict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

# quem NÃO exige atribuição: licença de stock já cobre no termo de uso
SEM_CREDITO = {"pexels", "coverr", "pixabay", "unsplash"}


def coletar(job):
    creditos, fontes = OrderedDict(), set()
    for f in sorted(Path(job, "resolvido").glob("b*.json")):
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        fonte = (d.get("fonte") or "").lower()
        if fonte:
            fontes.add(fonte)
        att = (d.get("atribuicao") or "").strip()
        if not att or fonte in SEM_CREDITO:
            continue
        lic = (d.get("licenca") or "").strip()
        taxon = (d.get("taxon") or "").strip()
        chave = f"{att}|{lic}"
        if chave not in creditos:
            creditos[chave] = {"att": att, "lic": lic, "taxon": taxon, "fonte": fonte}
    return creditos, fontes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--job", required=True)
    a = ap.parse_args()
    job = Path(a.job)
    creditos, fontes = coletar(job)
    linhas = ["IMAGE CREDITS", ""]
    if creditos:
        linhas.append("Photographs used under Creative Commons licences:")
        for c in creditos.values():
            taxon = f" — {c['taxon']}" if c["taxon"] else ""
            lic = f" [{c['lic'].upper()}]" if c["lic"] else ""
            linhas.append(f"  {c['att']}{taxon}{lic}")
        linhas.append("")
    if fontes:
        linhas.append("Sources: " + ", ".join(sorted(fontes)))
    saida = job / "CREDITOS.txt"
    saida.write_text("\n".join(linhas) + "\n", encoding="utf-8")
    print(f"{len(creditos)} crédito(s) obrigatório(s) -> {saida}")
    if not creditos:
        print("  (nenhum asset exige atribuição neste job)")


if __name__ == "__main__":
    main()
