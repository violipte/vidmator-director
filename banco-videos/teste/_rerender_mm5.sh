#!/bin/bash
# Re-render SÓ do memento_mori_5passos (upstream todo salvo em timeline_render.json).
# concurrency 10 = margem de segurança contra exaustão de recurso (crash 0xC0000142 anterior).
export PYTHONUNBUFFERED=1
R="F:/Canal Dark/Aplicativo de Edição/remotion"
cd "$R"
echo "@@@ RE-RENDER START @ $(date +%H:%M:%S)"
A=$(date +%s)
RENDER_OUT=memento_mori_5passos.mp4 RENDER_CONCURRENCY=10 node render-broll.mjs
RC=$?
DT=$(( $(date +%s)-A ))
echo "   render: ${DT}s (exit $RC)"
if [ $RC -eq 0 ] && [ -f "out/memento_mori_5passos.mp4" ]; then
  mkdir -p "D:/Meu Drive/canal_dark_videos"
  mv "out/memento_mori_5passos.mp4" "D:/Meu Drive/canal_dark_videos/" && echo "   -> Drive OK"
  ls -la "D:/Meu Drive/canal_dark_videos/memento_mori_5passos.mp4"
else
  echo "   !!! render falhou (exit $RC) — arquivo nao gerado"
fi
echo "@@@ RE-RENDER FIM @ $(date +%H:%M:%S)"
