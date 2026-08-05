# -*- coding: utf-8 -*-
"""INGEST do 'Baixar projeto' do Flow (05/08, ideia do Piter).

Muda o fluxo de raiz. Hoje o driver, PARA CADA clipe: abre /edit/, lê o prompt na
página, volta ao grid, faz hover, acha o ⋮, clica Baixar. São ~6 interações de UI
por clipe — e é aí que o lote de 98 morre: popup na frente, card fora da viewport,
botão que saiu do lugar. Nenhum desses erros tem a ver com gerar vídeo.

O Flow tem **"Baixar projeto"**: um zip com tudo. Então:
    gerar tudo (sem baixar nada)  ->  1 clique  ->  casar os arquivos AQUI.

O nome do arquivo é o TÍTULO que o Flow deriva do prompt — não a ordem de geração
(o timestamp é o do download, igual pra todos). Mas o título carrega as palavras do
prompt, e é isso que casa:
    "Caiman_slips_behind_jungle_foliage_202608051245.mp4"
    <- "Long shot of a large caiman as it slips quickly behind dense jungle foliage"

Uso: python veo_zip.py --zip <pasta descompactada> --lote <veo_lote.json> \
         --out <job>/assets [--aplicar]
Sem --aplicar só mostra o que faria (o casamento é por similaridade: conferir antes).
"""
import argparse
import json
import re
import shutil
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

STOP = {"the", "a", "an", "of", "in", "on", "at", "with", "and", "or", "for", "to",
        "as", "its", "it", "into", "from", "over", "under", "shot", "close", "wide",
        "medium", "long", "up", "light", "lens", "feel", "slow", "static", "tripod",
        "camera", "documentary", "cinematic", "look", "35mm", "depth", "field",
        "shallow", "frame", "clean", "no", "subtitles", "captions", "text"}


def _tokens(s):
    s = re.sub(r"_?\d{10,}(_\d+)?$", "", str(s))          # timestamp do download
    s = re.sub(r"\.(mp4|jpe?g|png|webm|mov)$", "", s, flags=re.I)
    s = s.replace("…", " ").replace("_", " ")
    return {w for w in re.findall(r"[a-zA-Z]{3,}", s.lower()) if w not in STOP}


def casar(arquivos, lote):
    """Casamento GULOSO pelo melhor par global: o arquivo mais parecido com o prompt
    mais parecido vence primeiro, e ambos saem do jogo. Guloso simples erra quando
    dois prompts dividem palavras ('caiman ...' x2); resolver pelo melhor par global
    primeiro reduz isso sem precisar de algoritmo húngaro."""
    pares = []
    for f in arquivos:
        tf = _tokens(f.name)
        # 05/08: MÍDIA tem que bater com o TIPO do item. Depois da reclassificação
        # por movimento, um beat que virou .jpg pode ter um VÍDEO antigo no zip com o
        # mesmo prompt — copiar mp4 pra dentro de bNNN.jpg é o golpe do "jpg com
        # ftypisom dentro" de novo (já nos custou ~90 créditos e um passe inteiro).
        kind_f = "video" if f.suffix.lower() in (".mp4", ".webm", ".mov") else "imagem"
        for it in lote:
            if it.get("tipo") and it["tipo"] != kind_f:
                continue
            ti = _tokens(it.get("prompt", ""))
            if not tf or not ti:
                continue
            inter = len(tf & ti)
            if not inter:
                continue
            # COBERTURA DO TÍTULO, não Jaccard: o título do Flow tem ~5 palavras e o
            # prompt dirigido tem ~60 (lente, luz, movimento, grading). Jaccard divide
            # pela união e afunda todo mundo pra ~0.10 — inútil pra ranquear. O que
            # importa é: das palavras do TÍTULO, quantas o prompt contém?
            pares.append((inter / len(tf), inter, f, it))
    pares.sort(key=lambda x: (-x[0], -x[1]))
    usados_f, usados_i, casados = set(), set(), []
    for sim, inter, f, it in pares:
        if f.name in usados_f or it["arquivo"] in usados_i:
            continue
        usados_f.add(f.name)
        usados_i.add(it["arquivo"])
        casados.append((f, it, sim, inter))
    sobra_f = [f for f in arquivos if f.name not in usados_f]
    sobra_i = [it for it in lote if it["arquivo"] not in usados_i]
    return casados, sobra_f, sobra_i


def aplicar(pasta, lote, out, min_sim=0.6, copiar=True):
    """Casa os arquivos de `pasta` com os itens do lote e copia os confiáveis pra
    `out` como bNNN.*. Devolve (n_copiados, casados, sobra_f, sobra_i). É a função
    que o ciclo por coleção usa a cada rodada — o CLI abaixo é só o dry-run manual."""
    pasta = Path(pasta)
    arquivos = [f for f in pasta.rglob("*") if f.is_file()
                and f.suffix.lower() in (".mp4", ".jpg", ".jpeg", ".png", ".webm", ".mov")]
    casados, sobra_f, sobra_i = casar(arquivos, lote)
    n = 0
    out = Path(out)
    for f, it, sim, inter in casados:
        if sim < min_sim:
            continue
        if copiar:
            out.mkdir(parents=True, exist_ok=True)
            destino = out / it["arquivo"]
            if not destino.exists():
                shutil.copy2(f, destino)
        n += 1
    return n, casados, sobra_f, sobra_i


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--zip", required=True, help="pasta com o projeto descompactado")
    ap.add_argument("--lote", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--aplicar", action="store_true", help="copia de fato (default: só mostra)")
    ap.add_argument("--min-sim", type=float, default=0.12)
    a = ap.parse_args()

    pasta = Path(a.zip)
    arquivos = [f for f in pasta.rglob("*") if f.is_file()
                and f.suffix.lower() in (".mp4", ".jpg", ".jpeg", ".png", ".webm", ".mov")]
    lote = json.loads(Path(a.lote).read_text(encoding="utf-8"))
    out = Path(a.out)
    print(f"{len(arquivos)} arquivos no zip | {len(lote)} itens no lote")

    casados, sobra_f, sobra_i = casar(arquivos, lote)
    ok = fraco = 0
    for f, it, sim, inter in sorted(casados, key=lambda x: -x[2]):
        marca = "OK " if sim >= a.min_sim else "?? "
        if sim >= a.min_sim:
            ok += 1
        else:
            fraco += 1
        print(f"  {marca}{sim:.2f} ({inter}) {f.name[:48]:<50} -> {it['arquivo']}")
        if a.aplicar and sim >= a.min_sim:
            out.mkdir(parents=True, exist_ok=True)
            shutil.copy2(f, out / it["arquivo"])
    print(f"\ncasados >= {a.min_sim}: {ok} | fracos: {fraco} | "
          f"arquivos sem par: {len(sobra_f)} | itens sem arquivo: {len(sobra_i)}")
    if sobra_f:
        print("sem par:", [f.name[:44] for f in sobra_f][:6])
    if not a.aplicar:
        print("\n(dry-run — rode com --aplicar pra copiar)")


if __name__ == "__main__":
    main()
