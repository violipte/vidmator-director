# -*- coding: utf-8 -*-
"""ADOTAR os assets gerados — o elo que faltava entre gerar e montar (06/08).

O buraco que isto tapa:

    curador/crítico  ->  _gerar.json  ->  veo_driver  ->  assets/bNNN__T1__gen.jpg
                                                                    |
                                                              (ninguém liga)
                                                                    X
    montador  <-  resolvido/bNNN.json  <------------------------------

O driver salva a imagem em `assets/` e para por aí. Quem o montador lê é
`resolvido/bNNN.json`, que continua apontando para o asset ANTIGO — justamente o
que o crítico tinha reprovado. Resultado medido no job amazônico: `b074` e `b075`
foram gerados às 22:57 de 05/08 e a montagem seguiu usando o footage reprovado.
As imagens ficaram órfãs em disco, e nada no processo acusava isso: a fila de
geração some (o arquivo existe!), o crítico vê o resolvido antigo e reprova de
novo, e o ciclo repete gastando geração toda volta.

Por que um passo separado, e não dentro do driver: o driver é do FLOW — ele sabe
de cards e downloads, não de beats. E o mesmo asset pode chegar por outra porta
(geração manual, Together, arquivo que o Piter jogou na pasta). Adotar é sobre o
JOB, então mora com o job.

O reprovado NÃO é apagado: vai para `resolvido/_substituidos/`, porque é a
evidência de por que aquele beat foi regerado.

Uso:
  python adotar_gerados.py --job <dir>          # adota tudo que estiver órfão
  python adotar_gerados.py --job <dir> --dry    # só mostra o que faria
"""
import argparse
import json
import re
import shutil
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

RE_GEN = re.compile(r"^b(\d{3})__T(\d)__gen\.(jpg|jpeg|png)$", re.I)


def adotar(job, dry=False):
    """(adotados, ja_ok, sem_beat) — liga cada assets/bNNN__T*__gen.* ao seu beat."""
    job = Path(job)
    assets, res = job / "assets", job / "resolvido"
    if not assets.exists():
        print(f"job sem assets/: {job}")
        return [], [], []
    plano = _plano(job)
    adotados, ja_ok, sem_beat = [], [], []

    for f in sorted(assets.iterdir()):
        m = RE_GEN.match(f.name)
        if not m:
            continue
        i, tier = int(m.group(1)), int(m.group(2))
        rf = res / f"b{i:03d}.json"
        atual = _ler(rf)
        if str(atual.get("arquivo") or "").endswith(f.name):
            ja_ok.append(f.name)
            continue
        b = plano.get(i)
        if not b and not atual:
            # sem beat no plano E sem resolvido: não dá pra saber a que momento
            # do vídeo isto pertence — adotar seria inventar posição na timeline
            sem_beat.append(f.name)
            continue
        novo = _registro(i, tier, f, b, atual)
        antigo = str(atual.get("arquivo") or "")
        adotados.append((f.name, Path(antigo).name if antigo else "(buraco)"))
        if dry:
            continue
        if antigo and Path(antigo).exists() and Path(antigo).name != f.name:
            # o reprovado é a evidência de por que se gerou — guarda, não apaga
            velhos = res / "_substituidos"
            velhos.mkdir(parents=True, exist_ok=True)
            try:
                shutil.move(antigo, str(velhos / Path(antigo).name))
            except Exception:
                pass
        res.mkdir(parents=True, exist_ok=True)
        rf.write_text(json.dumps(novo, ensure_ascii=False, indent=1), encoding="utf-8")
    return adotados, ja_ok, sem_beat


def _registro(i, tier, f, beat, atual):
    """O resolvido do gerado. Herda o que descreve o BEAT (tempo, seção, busca) e
    troca o que descreve o ASSET (arquivo, fonte, tier)."""
    d = dict(atual) if atual else {}
    b = beat or {}
    d.update({
        "i": i,
        "secao": d.get("secao", b.get("secao")),
        "t_ini": d.get("t_ini", b.get("t_ini")),
        "t_fim": d.get("t_fim", b.get("t_fim")),
        "busca": d.get("busca") or b.get("busca") or "",
        "status": "ok",
        "arquivo": str(f.resolve()),
        "tier": tier,
        "fonte": "gerado",
        "tipo": d.get("tipo") or b.get("tipo") or "gerado",
        "tipo_final": "gerado",
        "midia": "imagem",
        # gerado não tem procedência a creditar, e dizer que tem seria falso no
        # CREDITOS.txt — o campo fica explícito em vez de vazio por omissão
        "atribuicao": "",
        "licenca": "gerado (Nano Banana)",
    })
    d.setdefault("score", 8)
    return d


def _plano(job):
    """{i: beat} do plano do job, para herdar tempo/seção quando o beat era buraco."""
    for p in sorted(job.glob("plano*.json")) + sorted(job.parent.glob("teste/plano*.json")):
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        bs = d.get("beats") if isinstance(d, dict) else d
        if isinstance(bs, list) and bs and isinstance(bs[0], dict) and "i" in bs[0]:
            return {b["i"]: b for b in bs}
    return {}


def _ler(f):
    try:
        return json.loads(f.read_text(encoding="utf-8"))
    except Exception:
        return {}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--job", required=True)
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args()
    ad, ok, sem = adotar(a.job, a.dry)
    for novo, velho in ad:
        print(f"{'[dry] ' if a.dry else ''}adotado {novo}  (substitui {velho})")
    if ok:
        print(f"{len(ok)} já estavam ligados")
    for f in sem:
        print(f"!! {f}: sem beat no plano e sem resolvido — não sei onde encaixa")
    if not ad:
        print("nada a adotar")
    return 0


if __name__ == "__main__":
    sys.exit(main())
