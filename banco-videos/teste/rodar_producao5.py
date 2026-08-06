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


def heartbeat_antilimpeza():
    """01/08: o `limpar_disco.py` do PROD apagou `remotion/out` NO MEIO da produção
    (a pasta `blocos/` sumiu entre o mkdir e a normalização → render abortado, bloco
    0 perdido). O guard dele (`_remotion_ativo`) só olha `remotion/_tmp`, mas job v5
    usa temp ISOLADO (`_tmp_<job>`) — então o render ficava invisível pra ele.
    Fix do NOSSO lado (sem tocar em PROD): tocar um arquivo em `remotion/_tmp` a cada
    30s enquanto a produção roda; o guard vê mtime < 120s e preserva o `out`."""
    import threading
    import time

    tmp = REMOTION / "_tmp"
    tmp.mkdir(parents=True, exist_ok=True)
    marca = tmp / ".render_v5_ativo"

    def _bater():
        while True:
            try:
                tmp.mkdir(parents=True, exist_ok=True)  # a própria _tmp pode ter sido apagada
                marca.write_text(str(time.time()), encoding="utf-8")
            except OSError:
                pass
            time.sleep(30)

    threading.Thread(target=_bater, daemon=True).start()


def _dur_video(v):
    """Duração do vídeo concatenado — vira o TETO do mux (o vídeo manda, não o áudio)."""
    import subprocess as _sp
    try:
        return float(_sp.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                              "-of", "csv=p=0", str(v)], capture_output=True, text=True,
                             timeout=60).stdout.strip() or 0) or 0
    except Exception:
        return 0


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
    ap.add_argument("--sem-montar", action="store_true",
                    help="usa a montagem.json que já está no disco (patch cirúrgico + "
                         "re-render de bloco: montar de novo troca bgs no rodízio e "
                         "invalidaria os checkpoints dos outros blocos)")
    a = ap.parse_args()
    py = sys.executable
    heartbeat_antilimpeza()

    if not a.sem_montar:
        etapa("MONTADOR", [py, "montador5.py", "--job", a.job, "--plano", a.plano,
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
    curto = a.nome.replace("_mont", "")
    render_mjs = REMOTION / f"_render_{curto}.mjs"
    if not render_mjs.exists():
        base = (REMOTION / "_render_v5base.mjs").read_text(encoding="utf-8")
        render_mjs.write_text(base.replace("v5base", curto), encoding="utf-8")

    # ---- v5 F2: RENDER POR BLOCOS (checkpoint + concat) ----
    # Áudio mixado numa passada única (WAV); blocos de vídeo renderizados um a um
    # (bloco pronto = pulado no resume), normalizados cfr30 sem áudio, concatenados
    # com -c:v copy e muxados com o WAV. Fronteira de bloco = corte seco (montador5).
    import json as _json
    import shutil
    mont5 = _json.loads(mont_json.read_text(encoding="utf-8"))
    blocos = mont5.get("blocos") or [{"t_ini": 0.0, "t_fim": mont5["dur_s"]}]
    outdir = REMOTION / "out" / f"_{curto}"
    ck = outdir / "blocos"
    ck.mkdir(parents=True, exist_ok=True)

    wav = outdir / f"{curto}_audio.wav"
    if not wav.exists():
        etapa("AUDIO (mix único)", ["node", str(render_mjs), "--audio"], cwd=REMOTION)
        if not wav.exists():
            print("!!! passada de áudio não gerou o WAV — ABORTADO !!!")
            sys.exit(4)

    lista = ck / "concat.txt"
    linhas = []
    for i, b in enumerate(blocos):
        norm = ck / f"blk{i:02d}.mp4"
        linhas.append(f"file '{norm.as_posix()}'")
        if norm.exists():
            print(f"  bloco {i}: já pronto (checkpoint)")
            continue
        etapa(f"RENDER bloco {i} ({b['t_ini']:.0f}-{b['t_fim']:.0f}s)",
              ["node", str(render_mjs), str(b["t_ini"]), str(b["t_fim"])], cwd=REMOTION)
        bruto = outdir / f"{curto}_{b['t_ini']}_{b['t_fim']}.mp4"
        if not bruto.exists():  # nome do slice pode formatar float diferente — acha o mais novo
            cand = sorted(outdir.glob(f"{curto}_*.mp4"), key=lambda p: p.stat().st_mtime)
            bruto = cand[-1] if cand else bruto
        n_frames = round((b["t_fim"] - b["t_ini"]) * 30)
        ck.mkdir(parents=True, exist_ok=True)  # defesa: limpeza externa pode ter levado a pasta
        etapa(f"NORMALIZA bloco {i}",
              ["ffmpeg", "-y", "-loglevel", "error", "-i", str(bruto), "-an",
               "-frames:v", str(n_frames), "-c:v", "libx264", "-preset", "medium",
               "-crf", "19", "-fps_mode", "cfr", "-r", "30", "-pix_fmt", "yuv420p", str(norm)])
        bruto.unlink(missing_ok=True)
    lista.write_text("\n".join(linhas) + "\n", encoding="utf-8")

    video_cat = outdir / f"{curto}_video.mp4"
    etapa("CONCAT blocos", ["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
                            "-i", str(lista), "-c:v", "copy", str(video_cat)])
    origem = outdir / f"{curto}_full.mp4"
    # 06/08: `-shortest` TRUNCA O VÍDEO no tamanho do áudio — e desde o modelo de
    # INSERÇÃO o vídeo é legitimamente MAIOR que a narração (narração + takes do
    # host). Na estreia isso comeu os 8,5s finais, levando junto o CTA de
    # encerramento. Agora o VÍDEO manda: o áudio ganha silêncio no fim (`apad`) e o
    # corte é pela duração do vídeo. No modelo antigo os dois têm o mesmo tamanho,
    # então nada muda lá.
    etapa("MUX áudio", ["ffmpeg", "-y", "-loglevel", "error", "-i", str(video_cat), "-i", str(wav),
                        "-map", "0:v:0", "-map", "1:a:0", "-af", "apad",
                        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                        "-fflags", "+shortest", "-max_interleave_delta", "0",
                        "-t", str(_dur_video(video_cat)), str(origem)])

    destino = Path(a.saida) if a.saida else Path(a.job) / f"{curto}_final.mp4"
    if not origem.exists():
        print(f"!!! RENDER sem MP4 em {origem} — ABORTADO !!!")
        sys.exit(3)
    shutil.copy2(origem, destino)  # cópia protegida (out/ já foi varrido por limpeza externa)
    print(f"\n=== PRODUÇÃO OK -> {destino} ===")


if __name__ == "__main__":
    main()
