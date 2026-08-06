# -*- coding: utf-8 -*-
"""GATE DE FALA DO HOST (06/08) — blindagem do áudio nativo do VEO.

Piter, 06/08: "precisamos BLINDAR a parte do avatar falando de verdade pelo VEO".
A dublagem resolve o áudio mas mata o sincronismo labial, e há nichos onde o host
falando de verdade é o formato. Então o take volta a ser gerado COM fala — e passa
por este gate antes de entrar no vídeo.

O que o gate pega (tudo visto em produção hoje):
  1. LIXO NO FIM — o VEO pronuncia o nome do chip depois da frase:
        pedido:  "...subscribe and ring the bell."
        take:    "...subscribe and ring the bell. TraviSero."
  2. FALA TROCADA — o casamento por título pôs a fala do CTA no slot da ABERTURA:
        pedido:  "Everyone here fears the wrong animal..."
        take:    "Two left, and they get worse. Subscribe so you don't miss it."
  3. FALA TRUNCADA — a frase não termina (o VEO não coube nos 8s).

Regra escolhida pelo Piter: REGERA SEMPRE QUE HOUVER SUJEIRA — nada de aparar e
aceitar. Take entregue nunca tem corte no fim.

Uso:
  python veo_gate_fala.py --job <dir>               # confere os takes do plano
  python veo_gate_fala.py --job <dir> --apagar      # apaga os reprovados (o ciclo regera)
"""
import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, r"F:/Canal Dark/Aplicativo de Edição/video-automator")
sys.stdout.reconfigure(encoding="utf-8")


def _norm(s):
    """Compara SOM, não ortografia: minúsculas, sem pontuação, espaços colapsados."""
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", " ", str(s).lower())).strip()


def _palavras(s):
    return _norm(s).split()


def transcrever_take(mp4):
    """STT do áudio do clipe -> texto corrido."""
    from transcriber import transcrever
    with tempfile.TemporaryDirectory() as td:
        wav = Path(td) / "take.wav"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(mp4),
                        "-vn", "-ac", "1", "-ar", "16000", str(wav)],
                       capture_output=True, timeout=180)
        if not wav.exists():
            return ""
        srt = transcrever(str(wav), idioma="en")
        return " ".join(l.strip() for l in open(srt, encoding="utf-8", errors="ignore")
                        if l.strip() and "-->" not in l and not l.strip().isdigit())


def avaliar(dito, pedido):
    """(ok, motivo). Três defeitos, três diagnósticos distintos.

    A CAUDA é medida pelo que vem DEPOIS da última palavra pedida — não por
    diferença de tamanho. Contar "palavras a mais" no total deixava o nome do chip
    passar, porque o STT come palavras no meio e o saldo fechava (a 1ª versão deste
    gate aprovou os dois takes que tinham "Travis Arewa" no fim)."""
    pd, dt = _palavras(pedido), _palavras(dito)
    if not dt:
        return False, "sem fala no take"
    # casa as palavras do pedido em ORDEM e guarda onde a última bateu
    i, fim_pedido = 0, -1
    for k, w in enumerate(dt):
        if i < len(pd) and w == pd[i]:
            i += 1
            fim_pedido = k
    cobertura = i / max(1, len(pd))
    # dt é um PREFIXO do pedido? então é truncamento, não troca
    if cobertura < 0.92:
        prefixo = all(w in pd for w in dt[:max(1, len(dt) // 2)])
        rot = "TRUNCADA" if prefixo else "TROCADA"
        return False, f"fala {rot} ({cobertura:.0%} do texto pedido): {dito[:66]!r}"
    cauda = dt[fim_pedido + 1:]
    if cauda:
        return False, f"LIXO no fim ({len(cauda)} palavra(s)): …{' '.join(cauda)[:44]!r}"
    return True, "ok"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--job", required=True)
    ap.add_argument("--apagar", action="store_true",
                    help="apaga os reprovados pra o ciclo regerar")
    a = ap.parse_args()

    job = Path(a.job)
    sc = json.loads((job / "style_card.json").read_text(encoding="utf-8"))
    av = sc.get("avatar") or {}
    banco = Path(av.get("banco") or (job / "assets"))
    reprovados = []
    for sec, ilha in (av.get("ilhas") or {}).items():
        if not isinstance(ilha, dict):
            continue
        pedido = (ilha.get("fala") or ilha.get("dub") or "").strip()
        if not pedido:
            continue
        clipe = banco / ilha["clip"]
        if not clipe.exists():
            print(f"  {ilha['clip']}: ausente")
            continue
        dito = transcrever_take(clipe)
        ok, motivo = avaliar(dito, pedido)
        print(f"  {'PASSA ' if ok else 'REPROVA'} {ilha['clip']:<20} {motivo}")
        if not ok:
            reprovados.append(clipe)
    if a.apagar:
        for c in reprovados:
            c.unlink(missing_ok=True)
        print(f"{len(reprovados)} take(s) apagado(s) — o ciclo regera na próxima rodada")
    else:
        print(f"{len(reprovados)} reprovado(s) (use --apagar pra mandar regerar)")
    return len(reprovados)


if __name__ == "__main__":
    sys.exit(0 if main() == 0 else 1)
