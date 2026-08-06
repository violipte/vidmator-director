# -*- coding: utf-8 -*-
"""GERAÇÃO PARALELA no Flow — um driver por PERFIL, cada um com sua fatia do lote.

Pedido do Piter (02/08): "DEVEMOS poder rodar mais de um perfil ao mesmo tempo,
cada um com seu fluxo". Não havia impedimento técnico — cada perfil é um
`user_data_dir` independente, ou seja, N navegadores separados, N sessões Google,
N filas do Flow. Faltava só quem dividisse o trabalho.

Aqui: pergunta ao monitor quais perfis estão LIVRES, corta o lote em N fatias e
dispara um `veo_driver` por perfil, em paralelo. Cada processo tem seu Chrome, seu
projeto no Flow e seus créditos — nada é compartilhado, então não há disputa.

Vazão: N perfis ≈ N× (a geração é dominada por espera do servidor, não por CPU).

Uso:
  python veo_paralelo.py --lote <job>/_gerar.json --out <job>/assets --tipo imagem
  python veo_paralelo.py ... --max-perfis 2     # limita quantos usar
"""
import argparse
import json
import subprocess
import sys
import threading
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
AQUI = Path(__file__).resolve().parent
VEO_PY = Path(r"F:/Canal Dark/veo_venv/Scripts/python.exe")
PERFIS_PY = Path(r"F:/Canal Dark/Aplicativo de Edição/veo_flow/perfis.py")


def perfis_livres():
    """Todos os perfis LIVRES e logados (não só o primeiro)."""
    sys.path.insert(0, str(PERFIS_PY.parent))
    try:
        from perfis import status
        return [s["caminho"] for s in status() if not s["ocupado"] and s["logado"]]
    except Exception as e:
        print(f"!! monitor de perfis indisponível ({type(e).__name__})")
        return []


def fatiar(itens, n):
    """Distribui em ROUND-ROBIN, não em blocos: se um perfil cair no meio, o
    prejuízo fica espalhado pelo lote em vez de matar um trecho inteiro do vídeo."""
    fatias = [[] for _ in range(n)]
    for k, it in enumerate(itens):
        fatias[k % n].append(it)
    return [f for f in fatias if f]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lote", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--tipo", default="imagem", choices=["video", "imagem"])
    ap.add_argument("--regen", type=int, default=1)
    ap.add_argument("--max-perfis", type=int, default=0, help="0 = todos os livres")
    ap.add_argument("--dirigir", default="")
    a = ap.parse_args()

    itens = json.loads(Path(a.lote).read_text(encoding="utf-8"))
    if not itens:
        print("lote vazio")
        return
    livres = perfis_livres()
    if a.max_perfis > 0:
        livres = livres[:a.max_perfis]
    if not livres:
        print("!! nenhum perfil LIVRE e logado — veo_flow/perfis.py mostra o estado")
        return

    fatias = fatiar(itens, len(livres))
    print(f"{len(itens)} item(ns) em {len(fatias)} perfil(is) paralelo(s):")
    tmp = Path(a.lote).parent
    procs = []
    for k, (perfil, fatia) in enumerate(zip(livres, fatias)):
        lote_k = tmp / f"_gerar_p{k}.json"
        lote_k.write_text(json.dumps(fatia, ensure_ascii=False, indent=1), encoding="utf-8")
        cmd = [str(VEO_PY), str(AQUI / "veo_driver.py"), "--lote", str(lote_k),
               "--out", a.out, "--tipo", a.tipo, "--regen", str(a.regen),
               "--perfil", perfil]
        if a.dirigir:
            cmd += ["--dirigir", a.dirigir]
        print(f"  [{k}] {Path(perfil).name:<26} {len(fatia)} item(ns)")
        procs.append((k, subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                          stderr=subprocess.STDOUT, text=True,
                                          encoding="utf-8", errors="replace")))

    def _drenar(k, p):
        """Prefixa a saída com o índice do perfil — sem isso os logs de N drivers
        se misturam e não dá pra saber qual travou."""
        for linha in p.stdout:
            t = linha.rstrip()
            if t and not t.startswith("  - [pid"):
                print(f"[{k}] {t}", flush=True)

    ts = [threading.Thread(target=_drenar, args=(k, p), daemon=True) for k, p in procs]
    for t in ts:
        t.start()
    codigos = [(k, p.wait()) for k, p in procs]
    for t in ts:
        t.join(timeout=5)
    print("\n=== paralelo: " + " | ".join(f"[{k}] exit={c}" for k, c in codigos) + " ===")


if __name__ == "__main__":
    main()
