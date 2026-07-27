#!/bin/bash
export PYTHONUNBUFFERED=1; export NICHO=estoicismo
export MUSICA_PASTA="D:/Meu Drive/canal_estoicismo_trilhas"
R="F:/Canal Dark/Aplicativo de Edição/remotion"; ts(){ date +%s; }
cd "$R"
A=$(ts); echo "@@@ preparar @ $(date +%H:%M:%S)"; python preparar_render.py 2>&1 | tail -3; echo "  preparar: $(($(ts)-A))s"
echo "@@@ check: glitch_topico (deve ser False) + sfx.glitch (deve ser [])"
python -c "import json;rj=json.load(open('timeline_render.json',encoding='utf-8'));print('  glitch_topico=',rj.get('glitch_topico'),'| sfx.glitch=',rj.get('sfx_roles',{}).get('glitch'))"
A=$(ts); ok=0
for att in 1 2 3 4 5 6; do
  echo "@@@ render v3 tentativa $att @ $(date +%H:%M:%S)"
  RENDER_OUT=est_stay_silent_v3.mp4 RENDER_CHUNKS=8 RENDER_CONCURRENCY=10 node render-broll.mjs
  RC=$?; [ $RC -eq 0 ] && { ok=1; break; }; echo "  falhou -> retoma"; sleep 5
done
echo "  render: $(($(ts)-A))s"
if [ $ok -eq 1 ] && [ -f "out/est_stay_silent_v3.mp4" ]; then
  mv -f "out/est_stay_silent_v3.mp4" "D:/Meu Drive/canal_dark_videos/" && echo "  -> Drive OK"
else echo "  !!! render falhou"; fi
echo "@@@ FIM @ $(date +%H:%M:%S)"
