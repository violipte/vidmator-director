#!/bin/bash
export PYTHONUNBUFFERED=1; export NICHO=documentario
T="F:/Canal Dark/Aplicativo de Edição/banco-videos/teste"; R="F:/Canal Dark/Aplicativo de Edição/remotion"
ts(){ date +%s; }
cd "$T"; echo "@@@ epoca (re) @ $(date +%H:%M:%S)"; python epoca.py 2>&1 | tail -2
echo "@@@ niveis pós-epoca:"; python -c "import json,collections;tl=json.load(open('timeline.json',encoding='utf-8'));print(dict(collections.Counter(x.get('nivel','?') for x in tl['cenas'])))"
A=$(ts); echo "@@@ preparar @ $(date +%H:%M:%S)"; cd "$R"; python preparar_render.py 2>&1 | tail -3; echo "  preparar: $(( $(ts)-A ))s"
A=$(ts); ok=0
for att in 1 2 3 4 5 6; do
  echo "@@@ render v2 tentativa $att @ $(date +%H:%M:%S)"
  RENDER_OUT=documentario_dday_v2.mp4 RENDER_CHUNKS=6 RENDER_CONCURRENCY=10 node render-broll.mjs
  RC=$?; [ $RC -eq 0 ] && { ok=1; break; }; echo "  falhou -> retoma"; sleep 5
done
echo "  render: $(( $(ts)-A ))s"
if [ $ok -eq 1 ] && [ -f "out/documentario_dday_v2.mp4" ]; then
  mv -f "out/documentario_dday_v2.mp4" "D:/Meu Drive/canal_dark_videos/" && echo "  -> Drive OK"
else echo "  !!! render falhou"; fi
echo "@@@ FIM @ $(date +%H:%M:%S)"
