#!/bin/bash
# SAMPLE do canal SURVIVAL (Galo veterano): narra (deep_lax placeholder) -> passes (mascote!) -> render -> cold-open.
export PYTHONUNBUFFERED=1; export NICHO=survival
export MUSICA_PASTA="D:/Meu Drive/canal_estoicismo_trilhas"
T="F:/Canal Dark/Aplicativo de Edição/banco-videos/teste"; R="F:/Canal Dark/Aplicativo de Edição/remotion"
CBPY="F:/Canal Dark/chatterbox-test/venv/Scripts/python.exe"
VOZ="F:/Canal Dark/CapCut/CapCut Materials/Vozes/deep_lax.mp3"
ts(){ date +%s; }; stage(){ echo "@@@ $1 @ $(date +%H:%M:%S)"; }
cd "$T"; cp roteiros/srv_myths_sample.txt roteiro_en.txt
WORDS=$(wc -w < roteiro_en.txt); MINDUR=$(( WORDS / 4 )); echo "roteiro: $WORDS palavras | narração min ${MINDUR}s"
rm -f poc_srv.mp3 poc_srv.bad.mp3 narracao_joanne.mp3 words.json
narr_ok=0
for natt in 1 2 3; do
  rm -f poc_srv.mp3 poc_srv.bad.mp3
  A=$(ts); stage "narracao tentativa $natt"; "$CBPY" narrar_job.py "$VOZ" poc_srv 2>&1 | tail -2
  if [ -f poc_srv.mp3 ]; then D=$(ffprobe -v error -show_entries format=duration -of csv=p=0 poc_srv.mp3 2>/dev/null|cut -d. -f1); D=${D:-0}
    if [ "$D" -ge "$MINDUR" ]; then narr_ok=1; cp poc_srv.mp3 narracao_joanne.mp3; echo "  narração OK: ${D}s em $(( $(ts)-A ))s"; break; fi
    echo "  curta (${D}s<${MINDUR}s) retry"; rm -f poc_srv.mp3; fi
done
[ $narr_ok -eq 1 ] || { echo "!!! narração falhou 3x — ABORT"; echo "@@@ FIM"; exit 1; }
A=$(ts); stage whisper; "$CBPY" transcrever_words.py 2>&1|tail -2; echo "  whisper: $(( $(ts)-A ))s"
for p in montar_timeline resolver_cascata epoca detectar_mapas pessoas datas topicos trilha efeitos fontes imagens ilustrar apresentar produto_cta mascote; do
  A=$(ts); stage $p; python $p.py 2>&1|tail -2; echo "  $p: $(( $(ts)-A ))s"; done
A=$(ts); stage preparar; cd "$R"; python preparar_render.py 2>&1|tail -3; echo "  preparar: $(( $(ts)-A ))s"
stage limpar-chunks-velhos; rm -f out/_chunks/srv_sample.part*.mp4 out/srv_sample.mp4; echo "  limpo"
A=$(ts); ok=0
for att in 1 2 3 4 5 6; do echo "@@@ render tentativa $att @ $(date +%H:%M:%S)"
  RENDER_OUT=srv_sample.mp4 RENDER_CHUNKS=4 RENDER_CONCURRENCY=10 node render-broll.mjs; RC=$?
  [ $RC -eq 0 ] && { ok=1; break; }; echo "  falhou->retoma"; sleep 5; done
echo "  render: $(( $(ts)-A ))s"
[ $ok -eq 1 ] || { echo "!!! render falhou"; echo "@@@ FIM"; exit 1; }
stage coldopen
cd "$T" && python coldopen_quote.py && Q=$(cat coldopen.json) && cd "$R"
COMP_PROPS="$Q" node render-comp.mjs TypewriterQuote srv_coldopen.mp4 2>&1|tail -2
stage concat
printf "file '$R/out/srv_coldopen.mp4'\nfile '$R/out/srv_sample.mp4'\n" > "$R/out/_ccs.txt"
ffmpeg -y -f concat -safe 0 -i "$R/out/_ccs.txt" -c copy "$R/out/srv_myths_sample_v1.mp4" 2>&1 | tail -2
if [ -f "$R/out/srv_myths_sample_v1.mp4" ]; then mv -f "$R/out/srv_myths_sample_v1.mp4" "D:/Meu Drive/canal_dark_videos/" && echo "  -> Drive OK"; else echo "  !!! concat falhou"; fi
echo "@@@ FIM @ $(date +%H:%M:%S)"
