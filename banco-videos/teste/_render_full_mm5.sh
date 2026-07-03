#!/bin/bash
# Render COM infografico/ilustracao ATIVOS (renderer endurecido: txt()/num() + ErrorBoundary <Safe> + CardVs rico).
# Footage 80/20 + enriquecimento ja na timeline.json. NAO faz strip.
export PYTHONUNBUFFERED=1
R="F:/Canal Dark/Aplicativo de Edição/remotion"
cd "$R"
echo "@@@ preparar @ $(date +%H:%M:%S)"
A=$(date +%s); python preparar_render.py 2>&1 | tail -4; echo "   preparar: $(( $(date +%s)-A ))s"
python -c "import json; tl=json.load(open('timeline_render.json',encoding='utf-8')); print('   render json: infografico=%d ilustracao=%d (ATIVOS)'%(sum(1 for c in tl['cenas'] if c.get('infografico')),sum(1 for c in tl['cenas'] if c.get('ilustracao'))))"
echo "@@@ render @ $(date +%H:%M:%S)"
A=$(date +%s)
RENDER_OUT=memento_mori_5passos.mp4 RENDER_CONCURRENCY=10 node render-broll.mjs; RC=$?
echo "   render: $(( $(date +%s)-A ))s (exit $RC)"
echo "   React#31 no log: $(grep -c '#31' "$R/_render_full_mm5_node.log" 2>/dev/null || echo 'n/a')"
if [ $RC -eq 0 ] && [ -f "out/memento_mori_5passos.mp4" ]; then
  mkdir -p "D:/Meu Drive/canal_dark_videos"
  mv -f "out/memento_mori_5passos.mp4" "D:/Meu Drive/canal_dark_videos/" && echo "   -> Drive OK"
else
  echo "   !!! render falhou (exit $RC)"
fi
echo "@@@ FIM @ $(date +%H:%M:%S)"
