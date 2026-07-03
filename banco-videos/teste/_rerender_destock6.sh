#!/bin/bash
# Re-render SO render (timeline_render.json ja pronto: SFX + destock + infografico/ilustracao).
# concurrency 6: o destock (scale+translate+rotate por frame) saturou o compositor no 10 -> crash no 70%.
export PYTHONUNBUFFERED=1
R="F:/Canal Dark/Aplicativo de Edição/remotion"
cd "$R"
rm -rf _tmp/puppeteer_dev_chrome_profile-* 2>/dev/null   # limpa perfis orfaos do crash
echo "@@@ render @ $(date +%H:%M:%S)"
A=$(date +%s)
RENDER_OUT=memento_mori_5passos.mp4 RENDER_CONCURRENCY=6 node render-broll.mjs; RC=$?
echo "   render: $(( $(date +%s)-A ))s (exit $RC)"
if [ $RC -eq 0 ] && [ -f "out/memento_mori_5passos.mp4" ]; then
  mkdir -p "D:/Meu Drive/canal_dark_videos"
  mv -f "out/memento_mori_5passos.mp4" "D:/Meu Drive/canal_dark_videos/" && echo "   -> Drive OK"
else
  echo "   !!! render falhou (exit $RC)"
fi
echo "@@@ FIM @ $(date +%H:%M:%S)"
