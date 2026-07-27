#!/bin/bash
export PYTHONUNBUFFERED=1; export NICHO=documentario
R="F:/Canal Dark/Aplicativo de Edição/remotion"; ts(){ date +%s; }
cd "$R"
A=$(ts); echo "@@@ preparar @ $(date +%H:%M:%S)"; python preparar_render.py 2>&1 | tail -4; echo "  preparar: $(($(ts)-A))s"
echo "@@@ check render json: glitch_topico + sfx + pessoas"
python -c "import json;rj=json.load(open('timeline_render.json',encoding='utf-8'));print('  glitch_topico=',rj.get('glitch_topico'),'| sfx.glitch=',rj.get('sfx_roles',{}).get('glitch'),'| pessoas=',len(rj.get('pessoas',[])),'| periodo=',rj.get('periodo'))"
A=$(ts); ok=0
for att in 1 2 3 4 5 6; do
  echo "@@@ render v4 tentativa $att @ $(date +%H:%M:%S)"
  RENDER_OUT=documentario_dday_v4.mp4 RENDER_CHUNKS=6 RENDER_CONCURRENCY=10 node render-broll.mjs
  RC=$?; [ $RC -eq 0 ] && { ok=1; break; }; echo "  falhou -> retoma"; sleep 5
done
echo "  render: $(($(ts)-A))s"
if [ $ok -eq 1 ] && [ -f "out/documentario_dday_v4.mp4" ]; then
  mv -f "out/documentario_dday_v4.mp4" "D:/Meu Drive/canal_dark_videos/" && echo "  -> Drive OK"
else echo "  !!! render falhou"; fi
echo "@@@ FIM @ $(date +%H:%M:%S)"
