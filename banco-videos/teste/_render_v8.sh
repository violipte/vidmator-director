#!/bin/bash
# Render v8: PRESET ESTOICISMO (apresentações calmas parallax/reveal/spotlight + efeitos sutis). Chunks + retry.
export PYTHONUNBUFFERED=1
R="F:/Canal Dark/Aplicativo de Edição/remotion"; cd "$R"
rm -rf _tmp/puppeteer_dev_chrome_profile-* 2>/dev/null
echo "@@@ preparar @ $(date +%H:%M:%S)"; python preparar_render.py 2>&1 | tail -2
A=$(date +%s); ok=0
for attempt in 1 2 3 4 5 6 7 8; do
  echo "@@@ tentativa $attempt @ $(date +%H:%M:%S)"
  RENDER_OUT=memento_mori_5passos_v8_estoicismo.mp4 RENDER_CHUNKS=6 RENDER_CONCURRENCY=10 node render-broll.mjs
  RC=$?; [ $RC -eq 0 ] && { ok=1; break; }
  echo "   tentativa $attempt falhou (exit $RC) -> retoma em 5s"; sleep 5
done
echo "   total: $(( $(date +%s)-A ))s"
if [ $ok -eq 1 ] && [ -f "out/memento_mori_5passos_v8_estoicismo.mp4" ]; then
  mkdir -p "D:/Meu Drive/canal_dark_videos"; mv -f "out/memento_mori_5passos_v8_estoicismo.mp4" "D:/Meu Drive/canal_dark_videos/" && echo "   -> Drive OK"
else echo "   !!! falhou"; fi
echo "@@@ FIM @ $(date +%H:%M:%S)"
