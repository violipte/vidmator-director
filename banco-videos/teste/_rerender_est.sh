#!/bin/bash
# Re-render EST LIMPO: reusa a narração do v3 (Piter: "já serve"), re-roda passes+render com os fixes de hoje
# (riser/whoosh gated em glitch_topico:false) + cold-open typewriter (Epictetus, volume cheio) -> est_stay_silent_v4.
export PYTHONUNBUFFERED=1; export NICHO=estoicismo
export MUSICA_PASTA="D:/Meu Drive/canal_estoicismo_trilhas"
T="F:/Canal Dark/Aplicativo de Edição/banco-videos/teste"; R="F:/Canal Dark/Aplicativo de Edição/remotion"
CBPY="F:/Canal Dark/chatterbox-test/venv/Scripts/python.exe"
ts(){ date +%s; }; stage(){ echo "@@@ $1 @ $(date +%H:%M:%S)"; }
cd "$T"
cp roteiros/est_stay_silent.txt roteiro_en.txt
[ -f poc_est_stay.mp3 ] || { echo "!!! poc_est_stay.mp3 (narração v3) sumiu — ABORT"; exit 1; }
cp poc_est_stay.mp3 narracao_joanne.mp3; echo "narração v3 reusada (sem re-narrar)"
A=$(ts); stage whisper; "$CBPY" transcrever_words.py 2>&1|tail -2; echo "  whisper: $(( $(ts)-A ))s"
for p in montar_timeline resolver_cascata epoca detectar_mapas pessoas datas topicos trilha efeitos fontes imagens ilustrar apresentar; do
  A=$(ts); stage $p; python $p.py 2>&1|tail -2; echo "  $p: $(( $(ts)-A ))s"; done
A=$(ts); stage preparar; cd "$R"; python preparar_render.py 2>&1|tail -3; echo "  preparar: $(( $(ts)-A ))s"
stage limpar-chunks-velhos; rm -f out/_chunks/est_main.part*.mp4 out/est_main.mp4; echo "  chunks est_main antigos removidos"
A=$(ts); ok=0
for att in 1 2 3 4 5 6; do echo "@@@ render main tentativa $att @ $(date +%H:%M:%S)"
  RENDER_OUT=est_main.mp4 RENDER_CHUNKS=8 RENDER_CONCURRENCY=10 node render-broll.mjs; RC=$?
  [ $RC -eq 0 ] && { ok=1; break; }; echo "  falhou->retoma"; sleep 5; done
echo "  render main: $(( $(ts)-A ))s"
[ $ok -eq 1 ] || { echo "!!! render main falhou"; echo "@@@ FIM"; exit 1; }
stage coldopen; COMP_PROPS='{"quote":"Be silent for the most part, or say only what is necessary, and in few words.","author":"Epictetus","cps":20}' node render-comp.mjs TypewriterQuote est_coldopen.mp4 2>&1|tail -2
stage concat
printf "file '$R/out/est_coldopen.mp4'\nfile '$R/out/est_main.mp4'\n" > "$R/out/_cce.txt"
ffmpeg -y -f concat -safe 0 -i "$R/out/_cce.txt" -c copy "$R/out/est_stay_silent_v4.mp4" 2>&1 | tail -3
if [ -f "$R/out/est_stay_silent_v4.mp4" ]; then mv -f "$R/out/est_stay_silent_v4.mp4" "D:/Meu Drive/canal_dark_videos/" && echo "  -> Drive OK"; else echo "  !!! concat falhou"; fi
echo "@@@ FIM @ $(date +%H:%M:%S)"
