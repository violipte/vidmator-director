#!/bin/bash
R="F:/Canal Dark/Aplicativo de Edição/remotion"; cd "$R"; ts(){ date +%s; }
A=$(ts); ok=0
for att in 1 2 3 4 5 6; do echo "@@@ render main v2 tentativa $att @ $(date +%H:%M:%S)"
  RENDER_OUT=ttm_main.mp4 RENDER_CHUNKS=8 RENDER_CONCURRENCY=10 node render-broll.mjs; RC=$?
  [ $RC -eq 0 ] && { ok=1; break; }; echo "  falhou->retoma"; sleep 5; done
echo "  render main: $(( $(ts)-A ))s"; [ $ok -eq 1 ] || { echo "!!! render falhou"; exit 1; }
echo "@@@ concat (reusa cold-open existente) @ $(date +%H:%M:%S)"
printf "file 'out/ttm_coldopen.mp4'\nfile 'out/ttm_main.mp4'\n" > out/_cc.txt
ffmpeg -y -f concat -safe 0 -i out/_cc.txt -c copy out/ttm_hips_silent_fear_v2.mp4 2>&1|tail -2
[ -f out/ttm_hips_silent_fear_v2.mp4 ] && mv -f out/ttm_hips_silent_fear_v2.mp4 "D:/Meu Drive/canal_dark_videos/" && echo "  -> Drive OK" || echo "  !!! concat falhou"
echo "@@@ FIM @ $(date +%H:%M:%S)"
