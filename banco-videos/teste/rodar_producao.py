# -*- coding: utf-8 -*-
"""DRIVER DE PRODUÇÃO blindado (27/07) — substitui cadeias de shell.
Motivo: `auditor | tail` engoliu exit code VERMELHO e o render rodou com violação.
Aqui cada etapa é verificada por EXIT CODE em Python; qualquer falha ABORTA:
  1. montador  2. goldens  3. AUDITOR (VERMELHO = para TUDO)
  4. GPU livre (NVENC 0%)  5. render Remotion  6. cópia protegida do MP4
Uso: python rodar_producao.py --job <dir> --plano <plano.json> --audio <mp3> --nome <job_mont>
"""
import argparse
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
TESTE = Path(__file__).parent
REMOTION = Path(r"F:/Canal Dark/Aplicativo de Edição/remotion")


def etapa(nome, cmd, cwd=None, timeout=7200):
    print(f"\n=== [{nome}] ===", flush=True)
    r = subprocess.run(cmd, cwd=cwd or TESTE, timeout=timeout)
    if r.returncode != 0:
        print(f"!!! [{nome}] FALHOU (exit {r.returncode}) — PRODUÇÃO ABORTADA !!!")
        sys.exit(1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--job", required=True)
    ap.add_argument("--plano", required=True)
    ap.add_argument("--audio", required=True)
    ap.add_argument("--nome", required=True)
    ap.add_argument("--saida", default="", help="mp4 final (default: <job>/<nome>_final.mp4)")
    a = ap.parse_args()
    py = sys.executable

    etapa("MONTADOR", [py, "montador.py", "--job", a.job, "--plano", a.plano,
                       "--audio", a.audio, "--nome", a.nome])
    etapa("GOLDENS", [py, "test_regras.py"])
    mont_json = REMOTION / "public" / "jobs" / a.nome / "montagem.json"
    etapa("AUDITOR", [py, "auditar_montagem.py", str(mont_json), a.plano])

    # GPU: NVENC precisa estar livre (PROD compartilha a GPU)
    enc = subprocess.run(["nvidia-smi", "--query-gpu=utilization.encoder", "--format=csv,noheader"],
                         capture_output=True, text=True).stdout.strip().replace("%", "").strip()
    if enc and int(enc) > 5:
        print(f"!!! NVENC em {enc}% (render de outro processo?) — ABORTADO por segurança !!!")
        sys.exit(2)

    # render script por job (clona o template se não existir)
    render_mjs = REMOTION / f"_render_{a.nome.replace('_mont', '')}.mjs"
    if not render_mjs.exists():
        base = (REMOTION / "_render_jardim.mjs").read_text(encoding="utf-8")
        render_mjs.write_text(base.replace("jardim", a.nome.replace("_mont", "")), encoding="utf-8")
    etapa("RENDER", ["node", str(render_mjs)], cwd=REMOTION)

    curto = a.nome.replace("_mont", "")
    origem = REMOTION / "out" / f"_{curto}" / f"{curto}_full.mp4"
    destino = Path(a.saida) if a.saida else Path(a.job) / f"{curto}_final.mp4"
    if not origem.exists():
        print(f"!!! RENDER sem MP4 em {origem} — ABORTADO !!!")
        sys.exit(3)
    import shutil
    shutil.copy2(origem, destino)  # cópia protegida (out/ já foi varrido por limpeza externa)
    print(f"\n=== PRODUÇÃO OK -> {destino} ===")


if __name__ == "__main__":
    main()
