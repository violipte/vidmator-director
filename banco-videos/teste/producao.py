"""Runner de PRODUÇÃO em lote (sequencial, robusto): fila de roteiros -> N vídeos, sem babá.
Cada job: narração (Chatterbox/voz) -> pipeline completo -> render -> out/<nome>.mp4.
Continue-on-error (um roteiro ruim não derruba o lote). Resumo no fim.

Uso: python producao.py [producao_jobs.json]
  jobs.json = [{"nome": "stay_silent", "roteiro": "roteiros/stay_silent.txt", "voz": "george"}]

(Overlap paralelo passes(i+1)||render(i) é o próximo incremento — exige isolar o input do render por job.)
"""
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
TESTE = Path(r"F:/Canal Dark/Aplicativo de Edição/banco-videos/teste")
REMO = Path(r"F:/Canal Dark/Aplicativo de Edição/remotion")
VIDEOS_OUT = Path(r"D:/Meu Drive/canal_dark_videos")  # vídeos prontos -> Drive (não enche o out/ local)
CBPY = r"F:/Canal Dark/chatterbox-test/venv/Scripts/python.exe"  # venv Chatterbox (CUDA): narração+whisper
PY = "python"   # 3.14 (tem rembg) — passes
NODE = "node"

VOICES = {
    "george": r"F:/Canal Dark/CapCut/CapCut Materials/Vozes/george_pcc_channel.mp3",
}

# (label, interpreter, script, cwd) — passes na ordem do _run_stoic.sh (sem narração/whisper, tratados à parte)
PASSES = [
    ("montar_timeline", PY, "montar_timeline.py", TESTE),
    ("resolver_cascata", PY, "resolver_cascata.py", TESTE),
    ("epoca", PY, "epoca.py", TESTE),
    ("detectar_mapas", PY, "detectar_mapas.py", TESTE),
    ("pessoas", PY, "pessoas.py", TESTE),
    ("datas", PY, "datas.py", TESTE),
    ("topicos", PY, "topicos.py", TESTE),
    ("trilha", PY, "trilha.py", TESTE),
    ("efeitos", PY, "efeitos.py", TESTE),
    ("fontes", PY, "fontes.py", TESTE),
    ("imagens", PY, "imagens.py", TESTE),
    ("ilustrar", PY, "ilustrar.py", TESTE),
    ("apresentar", PY, "apresentar.py", TESTE),
    ("produto_cta", PY, "produto_cta.py", TESTE),
    ("mascote", PY, "mascote.py", TESTE),
    ("analisar_cenas", PY, "analisar_cenas.py", TESTE),
    ("ambiencia", PY, "ambiencia.py", TESTE),
    ("foley", PY, "foley.py", TESTE),
    ("personagens", PY, "personagens.py", TESTE),
]


def run(label, interp, script, cwd, extra_env=None, timeout=1800):
    env = {**os.environ, **(extra_env or {}), "PYTHONUNBUFFERED": "1"}
    t0 = time.time()
    r = subprocess.run([interp, script], cwd=str(cwd), env=env,
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
    dt = time.time() - t0
    tail = (r.stdout or "").strip().splitlines()[-1:] or [""]
    if r.returncode != 0:
        err = (r.stderr or "").strip().splitlines()[-3:]
        raise RuntimeError(f"{label} falhou (exit {r.returncode}) em {dt:.0f}s: {' | '.join(err)[:200]}")
    print(f"    [{label}] ok {dt:.0f}s  {tail[0][:60]}")


def render(nome, timeout=1800):
    env = {**os.environ, "RENDER_OUT": f"{nome}.mp4", "PYTHONUNBUFFERED": "1"}
    t0 = time.time()
    r = subprocess.run([NODE, "render-broll.mjs"], cwd=str(REMO), env=env,
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
    if r.returncode != 0:
        raise RuntimeError(f"render falhou (exit {r.returncode}): {(r.stderr or '')[-200:]}")
    # move o vídeo pronto pro Drive (mantém o out/ local limpo)
    local = REMO / "out" / f"{nome}.mp4"
    try:
        VIDEOS_OUT.mkdir(parents=True, exist_ok=True)
        shutil.move(str(local), str(VIDEOS_OUT / f"{nome}.mp4"))
        destino = f"{VIDEOS_OUT}/{nome}.mp4"
    except Exception as e:
        destino = f"out/{nome}.mp4 (Drive falhou: {str(e)[:50]})"
    print(f"    [render] ok {time.time()-t0:.0f}s -> {destino}")


def fazer_job(job):
    nome = job["nome"]
    voz = VOICES.get(job.get("voz", "george"))
    if not voz or not Path(voz).exists():
        raise RuntimeError(f"voz inválida: {job.get('voz')}")
    rot = Path(job["roteiro"])
    rot = rot if rot.is_absolute() else TESTE / rot
    if not rot.exists():
        raise RuntimeError(f"roteiro não encontrado: {rot}")
    shutil.copy2(rot, TESTE / "roteiro_en.txt")

    # narração: reusa mp3 existente se job["narracao"] for dado (pula Chatterbox), senão narra
    reuse = job.get("narracao")
    if reuse:
        src = Path(reuse) if Path(reuse).is_absolute() else TESTE / reuse
        if not src.exists():
            raise RuntimeError(f"narração reusada não encontrada: {src}")
        shutil.copy2(src, TESTE / "narracao_joanne.mp3")
        print(f"    [narração] reusada: {src.name}")
    else:
        print(f"  narração ({job.get('voz')}, Chatterbox)...")
        t0 = time.time()
        rn = subprocess.run([CBPY, "narrar_job.py", voz, f"poc_{nome}"], cwd=str(TESTE),
                            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=2400)
        if rn.returncode != 0:
            det = ((rn.stdout or "") + " || " + (rn.stderr or "")).strip()[-300:]
            raise RuntimeError(f"narração falhou: {det}")
        shutil.copy2(TESTE / f"poc_{nome}.mp3", TESTE / "narracao_joanne.mp3")
        print(f"    [narração] ok {time.time()-t0:.0f}s")

    run("whisper", CBPY, "transcrever_words.py", TESTE, timeout=1200)
    for label, interp, script, cwd in PASSES:
        run(label, interp, script, cwd)
    run("preparar", PY, "preparar_render.py", REMO)
    render(nome)


def main():
    cfg = Path(sys.argv[1]) if len(sys.argv) > 1 else TESTE / "producao_jobs.json"
    jobs = json.load(open(cfg, encoding="utf-8"))
    print(f"=== PRODUÇÃO: {len(jobs)} jobs ===")
    res = []
    for i, job in enumerate(jobs, 1):
        nome = job.get("nome", f"job{i}")
        print(f"\n[{i}/{len(jobs)}] {nome}")
        t0 = time.time()
        try:
            fazer_job(job)
            res.append((nome, "OK", time.time() - t0))
            print(f"  ✓ {nome} pronto em {time.time()-t0:.0f}s")
        except Exception as e:
            res.append((nome, f"FALHOU: {str(e)[:120]}", time.time() - t0))
            print(f"  ✗ {nome} FALHOU: {str(e)[:160]}")
    print("\n=== RESUMO ===")
    for nome, st, dt in res:
        print(f"  {nome:<22} {st:<40} {dt:.0f}s")
    ok = sum(1 for _, s, _ in res if s == "OK")
    print(f"\n{ok}/{len(res)} vídeos OK")


if __name__ == "__main__":
    main()
