#!/bin/bash
# Render v6: CTA de YouTube (like/subscribe/bell) + tudo do v5. Chunks resilientes + retry.
export PYTHONUNBUFFERED=1
R="F:/Canal Dark/Aplicativo de Edição/remotion"
cd "$R"
rm -rf _tmp/puppeteer_dev_chrome_profile-* 2>/dev/null
echo "@@@ preparar @ $(date +%H:%M:%S)"; python preparar_render.py 2>&1 | tail -2
A=$(date +%s); ok=0
for attempt in 1 2 3 4 5 6 7 8; do
  echo "@@@ tentativa $attempt @ $(date +%H:%M:%S)"
  RENDER_OUT=memento_mori_5passos_v6_cta.mp4 RENDER_CHUNKS=6 RENDER_CONCURRENCY=10 node render-broll.mjs
  RC=$?
  if [ $RC -eq 0 ]; then ok=1; break; fi
  echo "   tentativa $attempt falhou (exit $RC) -> retoma em 5s"; sleep 5
done
echo "   total: $(( $(date +%s)-A ))s"
if [ $ok -eq 1 ] && [ -f "out/memento_mori_5passos_v6_cta.mp4" ]; then
  mkdir -p "D:/Meu Drive/canal_dark_videos"
  mv -f "out/memento_mori_5passos_v6_cta.mp4" "D:/Meu Drive/canal_dark_videos/" && echo "   -> Drive OK"
else echo "   !!! falhou"; fi
echo "@@@ FIM @ $(date +%H:%M:%S)"
