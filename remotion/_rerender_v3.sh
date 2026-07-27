#!/bin/bash
export PYTHONUNBUFFERED=1; export NICHO=documentario
T="F:/Canal Dark/Aplicativo de Edição/banco-videos/teste"; R="F:/Canal Dark/Aplicativo de Edição/remotion"
ts(){ date +%s; }
cd "$T"
A=$(ts); echo "@@@ pessoas @ $(date +%H:%M:%S)"; python pessoas.py 2>&1 | tail -8; echo "  pessoas: $(($(ts)-A))s"
A=$(ts); echo "@@@ ilustrar @ $(date +%H:%M:%S)"; python ilustrar.py 2>&1 | tail -3; echo "  ilustrar: $(($(ts)-A))s"
echo "@@@ check:"; python -c "import json;tl=json.load(open('timeline.json',encoding='utf-8'));print('  pessoas=',len(tl.get('pessoas',[])),'| ilustracoes=',sum(1 for c in tl['cenas'] if c.get('ilustracao')))"
A=$(ts); echo "@@@ preparar @ $(date +%H:%M:%S)"; cd "$R"; python preparar_render.py 2>&1 | tail -3; echo "  preparar: $(($(ts)-A))s"
A=$(ts); ok=0
for att in 1 2 3 4 5 6; do
  echo "@@@ render v3 tentativa $att @ $(date +%H:%M:%S)"
  RENDER_OUT=documentario_dday_v3.mp4 RENDER_CHUNKS=6 RENDER_CONCURRENCY=10 node render-broll.mjs
  RC=$?; [ $RC -eq 0 ] && { ok=1; break; }; echo "  falhou -> retoma"; sleep 5
done
echo "  render: $(($(ts)-A))s"
if [ $ok -eq 1 ] && [ -f "out/documentario_dday_v3.mp4" ]; then
  mv -f "out/documentario_dday_v3.mp4" "D:/Meu Drive/canal_dark_videos/" && echo "  -> Drive OK"
else echo "  !!! render falhou"; fi
echo "@@@ FIM @ $(date +%H:%M:%S)"
