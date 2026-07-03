#!/bin/bash
# Render em 6 CHUNKS resumíveis + RETRY. Blinda contra queda de energia E FFmpeg 0xC0000142.
# Cada tentativa retoma só os chunks que faltam. timeline_render.json já tem SFX + destock + tudo.
export PYTHONUNBUFFERED=1
R="F:/Canal Dark/Aplicativo de Edição/remotion"
cd "$R"
rm -rf _tmp/puppeteer_dev_chrome_profile-* 2>/dev/null
A=$(date +%s); ok=0
for attempt in 1 2 3 4 5 6 7 8; do
  echo "@@@ tentativa $attempt @ $(date +%H:%M:%S)"
  RENDER_OUT=memento_mori_5passos.mp4 RENDER_CHUNKS=6 RENDER_CONCURRENCY=10 node render-broll.mjs
  RC=$?
  if [ $RC -eq 0 ]; then ok=1; break; fi
  echo "   tentativa $attempt falhou (exit $RC) -> retoma chunks restantes em 5s"
  sleep 5
done
echo "   total: $(( $(date +%s)-A ))s"
if [ $ok -eq 1 ] && [ -f "out/memento_mori_5passos.mp4" ]; then
  mkdir -p "D:/Meu Drive/canal_dark_videos"
  mv -f "out/memento_mori_5passos.mp4" "D:/Meu Drive/canal_dark_videos/" && echo "   -> Drive OK"
else
  echo "   !!! todas as tentativas falharam (chunks prontos ficam salvos em out/_chunks p/ retomar)"
fi
echo "@@@ FIM @ $(date +%H:%M:%S)"
