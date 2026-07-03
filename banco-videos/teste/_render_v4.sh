#!/bin/bash
# Render v4: SFX CORRIGIDO (punch files - swoosh/clímax audível) + tudo do v3.
# Chunks resilientes + retry. Nome versionado (nao sobrescreve).
export PYTHONUNBUFFERED=1
R="F:/Canal Dark/Aplicativo de Edição/remotion"
cd "$R"
rm -f out/_sfxtest*.mp4 out/_sfxonly*.mp4 timeline_muted.json timeline_sfxonly.json 2>/dev/null
rm -rf _tmp/puppeteer_dev_chrome_profile-* 2>/dev/null
echo "@@@ preparar @ $(date +%H:%M:%S)"; python preparar_render.py 2>&1 | tail -3
A=$(date +%s); ok=0
for attempt in 1 2 3 4 5 6 7 8; do
  echo "@@@ tentativa $attempt @ $(date +%H:%M:%S)"
  RENDER_OUT=memento_mori_5passos_v4_sfx-fixed.mp4 RENDER_CHUNKS=6 RENDER_CONCURRENCY=10 node render-broll.mjs
  RC=$?
  if [ $RC -eq 0 ]; then ok=1; break; fi
  echo "   tentativa $attempt falhou (exit $RC) -> retoma em 5s"; sleep 5
done
echo "   total: $(( $(date +%s)-A ))s"
if [ $ok -eq 1 ] && [ -f "out/memento_mori_5passos_v4_sfx-fixed.mp4" ]; then
  mkdir -p "D:/Meu Drive/canal_dark_videos"
  mv -f "out/memento_mori_5passos_v4_sfx-fixed.mp4" "D:/Meu Drive/canal_dark_videos/" && echo "   -> Drive OK"
else echo "   !!! falhou"; fi
echo "@@@ FIM @ $(date +%H:%M:%S)"
