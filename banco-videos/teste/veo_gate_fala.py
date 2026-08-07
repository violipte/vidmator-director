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


def escolher(job, pasta_zip, limite=10):
    """Escolhe o take do host PELA FALA, não pelo título (06/08).

    Por que: o "Baixar projeto" re-carimba TODOS os arquivos com a hora do DOWNLOAD,
    então dentro de um mesmo zip as gerações antiga e nova do mesmo prompt têm o
    mesmo carimbo e se distinguem só por um sufixo `_2`, `_3` sem significado. Não
    há como saber pelo NOME qual é a nova — e o casamento serviu duas vezes um take
    velho, que o gate flagrou dizendo a frase ANTIGA.

    A fala é a identidade real do take: transcrever os candidatos e ficar com o que
    diz a frase pedida resolve sem depender de título nem de carimbo.
    """
    import shutil
    from veo_zip import _tokens, _PESSOA_TITULO, _SIN_PESSOA

    job = Path(job)
    sc = json.loads((job / "style_card.json").read_text(encoding="utf-8"))
    av = sc.get("avatar") or {}
    banco = Path(av.get("banco") or (job / "assets"))
    plano = json.loads((job / "_avatar_plan.json").read_text(encoding="utf-8"))
    arquivos = [f for f in Path(pasta_zip).rglob("*")
                if f.is_file() and f.suffix.lower() in (".mp4", ".webm", ".mov")]
    achados = 0
    for it in plano:
        pedido = ""
        for ilha in (av.get("ilhas") or {}).values():
            if isinstance(ilha, dict) and ilha.get("clip") == it["arquivo"]:
                pedido = (ilha.get("fala") or ilha.get("dub") or "").strip()
        if not pedido:
            continue
        ti = _tokens(it.get("prompt", ""), pessoa=True)
        cands = []
        for f in arquivos:
            tf = _tokens(f.name)
            if not (tf & _PESSOA_TITULO):
                continue
            acao = tf - _SIN_PESSOA - _PESSOA_TITULO
            if not (acao & ti):
                continue
            cands.append((len(tf & ti) / max(1, len(tf)), f))
        cands.sort(key=lambda x: -x[0])
        print(f"\n{it['arquivo']}: {len(cands)} candidato(s) — ouvindo até achar a fala")
        for sim, f in cands[:limite]:
            dito = transcrever_take(f)
            ok, motivo = avaliar(dito, pedido)
            print(f"   {'ACHEI  ' if ok else 'não    '} {f.name[:46]:<48} {motivo[:44]}")
            if ok:
                shutil.copy2(f, banco / it["arquivo"])
                achados += 1
                break
    print(f"\n{achados}/{sum(1 for x in plano)} take(s) escolhidos pela fala")
    return achados


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--job", required=True)
    ap.add_argument("--apagar", action="store_true",
                    help="apaga os reprovados pra o ciclo regerar")
    ap.add_argument("--dub-fallback", action="store_true",
                    help="ÚLTIMO RECURSO, e SÓ com aval do Piter: a ilha vira DUBLADA. "
                         "07/08 — eu apliquei isto por conta própria no vídeo da África "
                         "e o host abriu com voz dublada quando o pedido era o VEO "
                         "falando de verdade. O padrão é REGERAR até passar (--apagar).")
    ap.add_argument("--escolher", default="",
                    help="pasta do zip: escolhe o take PELA FALA entre os candidatos")
    a = ap.parse_args()
    if a.escolher:
        escolher(a.job, a.escolher)
        return 0

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
    if a.dub_fallback and reprovados:
        # DECISÃO POR TAKE, NÃO POR VÍDEO (06/08). O VEO obedece a fala em uns slots
        # e improvisa em outros — o CTA do meio saiu perfeito enquanto o hook errou 5
        # vezes seguidas. Insistir é sorteio; desistir do áudio nativo no vídeo todo
        # joga fora o que funcionou. Então: quem passou fica NATIVO (lábios batem),
        # quem não passou vira DUBLADO (voz clonada por cima do take mudo do próprio
        # host). O vídeo sempre fecha, com a melhor opção disponível em cada ponto.
        sc2 = json.loads((job / "style_card.json").read_text(encoding="utf-8"))
        nomes = {c.name for c in reprovados}
        n = 0
        for sec, ilha in (sc2.get("avatar", {}).get("ilhas") or {}).items():
            if isinstance(ilha, dict) and ilha.get("clip") in nomes:
                ilha["dub"] = ilha.get("fala") or ilha.get("dub") or ""
                n += 1
        (job / "style_card.json").write_text(json.dumps(sc2, ensure_ascii=False, indent=1),
                                             encoding="utf-8")
        print(f"{n} ilha(s) marcada(s) pra DUBLAGEM (o take fica, a voz vem do clone)")
        print("   rode: python gerar_dub_avatar.py --job <job>")
    elif a.apagar:
        for c in reprovados:
            c.unlink(missing_ok=True)
        print(f"{len(reprovados)} take(s) apagado(s) — o ciclo regera na próxima rodada")
    else:
        print(f"{len(reprovados)} reprovado(s) (use --apagar pra mandar regerar)")
    return len(reprovados)


if __name__ == "__main__":
    sys.exit(0 if main() == 0 else 1)
