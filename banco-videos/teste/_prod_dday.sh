#!/bin/bash
# Produção completa do documentário D-Day: narração -> passes (NICHO=documentario, usa banco de época) -> render.
export PYTHONUNBUFFERED=1
export NICHO=documentario
T="F:/Canal Dark/Aplicativo de Edição/banco-videos/teste"; R="F:/Canal Dark/Aplicativo de Edição/remotion"
CBPY="F:/Canal Dark/chatterbox-test/venv/Scripts/python.exe"
VOZ="F:/Canal Dark/CapCut/CapCut Materials/Vozes/george_pcc_channel.mp3"
ts(){ date +%s; }; stage(){ echo "@@@ $1 @ $(date +%H:%M:%S)"; }
cd "$T"; cp roteiros/documentario_dday.txt roteiro_en.txt
A=$(ts); stage narracao; "$CBPY" narrar_job.py "$VOZ" poc_dday 2>&1 | tail -2; cp poc_dday.mp3 narracao_joanne.mp3; echo "  narracao: $(( $(ts)-A ))s"
A=$(ts); stage whisper;  "$CBPY" transcrever_words.py 2>&1 | tail -2; echo "  whisper: $(( $(ts)-A ))s"
for p in montar_timeline resolver_cascata epoca detectar_mapas pessoas datas topicos trilha efeitos fontes imagens ilustrar apresentar; do
  A=$(ts); stage $p; python $p.py 2>&1 | tail -2; echo "  $p: $(( $(ts)-A ))s"
done
A=$(ts); stage preparar; cd "$R"; python preparar_render.py 2>&1 | tail -3; echo "  preparar: $(( $(ts)-A ))s"
A=$(ts); ok=0
for att in 1 2 3 4 5 6; do
  echo "@@@ render tentativa $att @ $(date +%H:%M:%S)"
  RENDER_OUT=documentario_dday_v1.mp4 RENDER_CHUNKS=6 RENDER_CONCURRENCY=10 node render-broll.mjs
  RC=$?; [ $RC -eq 0 ] && { ok=1; break; }; echo "  falhou -> retoma"; sleep 5
done
echo "  render: $(( $(ts)-A ))s"
if [ $ok -eq 1 ] && [ -f "out/documentario_dday_v1.mp4" ]; then
  mkdir -p "D:/Meu Drive/canal_dark_videos"; mv -f "out/documentario_dday_v1.mp4" "D:/Meu Drive/canal_dark_videos/" && echo "  -> Drive OK"
else echo "  !!! render falhou"; fi
echo "@@@ FIM @ $(date +%H:%M:%S)"
