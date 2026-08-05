# -*- coding: utf-8 -*-
"""ENCARREGADO DA PRODUÇÃO no Flow (04/08, pedido do Piter).

Por que existe: o lote de 98 gerou 9 clipes e ficou **3h30 pendurado** sem baixar
nada. Quem percebeu foi o Piter, olhando a tela. Um lote longo não pode depender de
alguém olhando — precisa de um encarregado que saiba dizer se travou, pare, e retome
de onde parou.

COMO ELE DECIDE SE TRAVOU: pela contagem de arquivos PRONTOS no disco, não pelo log.
Log de driver de browser mente (buferiza, enche de ruído do Playwright, e o processo
segue "vivo" enquanto espera um clique pra sempre). Arquivo no disco é fato.

CICLO a cada travamento:
  1. mata o driver E o Chrome do perfil (senão a próxima rodada não abre o browser)
  2. roda `--so-baixar`: RESGATA o que o Flow já gerou e nós já PAGAMOS
  3. reinicia a geração só do que falta (o driver pula todo arquivo que já existe)
Para quando: completou tudo, estourou --max-reinicios, ou duas rodadas seguidas não
avançaram NADA (sinal de problema real — rate limit, sessão, crédito — que reiniciar
não resolve; insistir só queima tempo).

Uso:
  "F:/Canal Dark/veo_venv/Scripts/python.exe" veo_supervisor.py \
      --lote <job>/veo_lote.json --out <job>/assets --tipo video [--fila 5]
"""
import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
AQUI = Path(__file__).parent
PY_VENV = Path(r"F:/Canal Dark/veo_venv/Scripts/python.exe")


def _log(msg, arq=None):
    linha = f"[{time.strftime('%H:%M:%S')}] {msg}"
    print(linha, flush=True)
    if arq:
        with open(arq, "a", encoding="utf-8") as f:
            f.write(linha + "\n")


def matar_tudo():
    """Driver + Chrome do perfil do Flow. O Chrome PRECISA morrer junto: se ficar
    segurando o user_data_dir, a rodada seguinte abre 'em uma sessão existente' e
    o Playwright perde o controle da página."""
    ps = ("Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | "
          "Where-Object { $_.CommandLine -like '*veo_driver*' } | "
          "ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }; "
          "Get-CimInstance Win32_Process -Filter \"Name='chrome.exe'\" | "
          "Where-Object { $_.CommandLine -like '*veo_flow\\chrome_profile*' } | "
          "ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }")
    subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                   capture_output=True, timeout=120)
    time.sleep(5)


def prontos(out, alvos):
    return sum(1 for a in alvos if (out / a).exists())


def rodar(cmd, out, alvos, paciencia_s, log_arq, rotulo):
    """Roda o driver vigiando o DISCO. Devolve (status, novos)."""
    base = prontos(out, alvos)
    proc = subprocess.Popen(cmd, stdout=open(log_arq, "a", encoding="utf-8"),
                            stderr=subprocess.STDOUT)
    ultimo, t_ultimo = base, time.time()
    while True:
        time.sleep(20)
        if proc.poll() is not None:
            return ("fim", prontos(out, alvos) - base)
        n = prontos(out, alvos)
        if n > ultimo:
            _log(f"  {rotulo}: {n}/{len(alvos)} prontos", log_arq)
            ultimo, t_ultimo = n, time.time()
        elif time.time() - t_ultimo > paciencia_s:
            _log(f"!! TRAVOU: {int(paciencia_s/60)} min sem arquivo novo "
                 f"(parado em {n}/{len(alvos)})", log_arq)
            try:
                proc.kill()
            except Exception:
                pass
            return ("travou", n - base)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lote", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--tipo", default="video", choices=["video", "imagem"])
    ap.add_argument("--fila", type=int, default=5)
    ap.add_argument("--proj", default=None)
    ap.add_argument("--paciencia", type=int, default=10, help="min sem arquivo novo = travou")
    ap.add_argument("--max-reinicios", type=int, default=8)
    a = ap.parse_args()

    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    lote = json.loads(Path(a.lote).read_text(encoding="utf-8"))
    alvos = [x.get("arquivo") or x.get("dest") for x in lote
             if (x.get("tipo") or "video") == a.tipo]
    log_arq = out.parent / f"_supervisor_{a.tipo}.log"
    _log(f"=== ENCARREGADO: {len(alvos)} {a.tipo}s | paciência {a.paciencia}min | "
         f"até {a.max_reinicios} reinícios ===", log_arq)

    comum = [str(PY_VENV), "-u", str(AQUI / "veo_driver.py"), "--lote", a.lote,
             "--out", a.out, "--tipo", a.tipo, "--sem-config"]
    if a.proj:
        comum += ["--proj", a.proj]

    parados = 0
    for tentativa in range(1, a.max_reinicios + 2):
        falta = len(alvos) - prontos(out, alvos)
        if falta <= 0:
            _log(f"=== COMPLETO: {len(alvos)}/{len(alvos)} ===", log_arq)
            return
        _log(f"--- rodada {tentativa}: faltam {falta} ---", log_arq)

        # 1) RESGATE: o que o Flow já gerou e nós já pagamos vem antes de gerar mais
        matar_tudo()
        st, novos = rodar(comum + ["--so-baixar", "--regen", "0"], out, alvos,
                          a.paciencia * 60, log_arq, "resgate")
        if novos:
            _log(f"  resgatados do Flow: {novos}", log_arq)
        if prontos(out, alvos) >= len(alvos):
            _log(f"=== COMPLETO: {len(alvos)}/{len(alvos)} ===", log_arq)
            return

        # 2) GERAÇÃO do que falta
        matar_tudo()
        st2, novos2 = rodar(comum + ["--fila", str(a.fila), "--regen", "1",
                                     "--sem-progresso", str(a.paciencia)],
                            out, alvos, a.paciencia * 60, log_arq, "geração")
        _log(f"  rodada {tentativa}: {st2}, +{novos2} clipes", log_arq)

        # duas rodadas seguidas sem avançar nada = problema que reiniciar não cura
        parados = parados + 1 if (novos + novos2) == 0 else 0
        if parados >= 2:
            _log("!!! DUAS rodadas sem NENHUM avanço — parando. Causa provável: "
                 "sessão do Flow expirada, crédito, ou rate limit. Confira a tela.",
                 log_arq)
            break
    matar_tudo()
    _log(f"=== FIM: {prontos(out, alvos)}/{len(alvos)} {a.tipo}s ===", log_arq)


if __name__ == "__main__":
    main()
