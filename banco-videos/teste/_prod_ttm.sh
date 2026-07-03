#!/bin/bash
# Produção TTM (hips/silent fear): narração George (retry+valida) -> passes ttm -> render -> + cold-open Pema.
export PYTHONUNBUFFERED=1; export NICHO=ttm
export MUSICA_PASTA="D:/Meu Drive/canal_estoicismo_trilhas"
T="F:/Canal Dark/Aplicativo de Edição/banco-videos/teste"; R="F:/Canal Dark/Aplicativo de Edição/remotion"
CBPY="F:/Canal Dark/chatterbox-test/venv/Scripts/python.exe"
VOZ="F:/Canal Dark/CapCut/CapCut Materials/Vozes/george_pcc_channel.mp3"
ts(){ date +%s; }; stage(){ echo "@@@ $1 @ $(date +%H:%M:%S)"; }
cd "$T"; cp roteiros/ttm_hips_silent_fear.txt roteiro_en.txt
WORDS=$(wc -w < roteiro_en.txt); MINDUR=$(( WORDS / 4 )); echo "roteiro: $WORDS palavras | narração min ${MINDUR}s"
# PURGA narração/transcrição de runs anteriores: senão um poc_ttm.mp3 VELHO satisfaz [ -f ] e o driver aceita áudio de outro dia
rm -f poc_ttm.mp3 poc_ttm.bad.mp3 narracao_joanne.mp3 words.json
narr_ok=0
for natt in 1 2 3; do
  rm -f poc_ttm.mp3 poc_ttm.bad.mp3   # cada tentativa começa limpa: [ -f poc_ttm.mp3 ] só passa se ESTA tentativa gerou de verdade
  A=$(ts); stage "narracao tentativa $natt"; "$CBPY" narrar_job.py "$VOZ" poc_ttm 2>&1 | tail -2
  if [ -f poc_ttm.mp3 ]; then D=$(ffprobe -v error -show_entries format=duration -of csv=p=0 poc_ttm.mp3 2>/dev/null|cut -d. -f1); D=${D:-0}
    if [ "$D" -ge "$MINDUR" ]; then narr_ok=1; cp poc_ttm.mp3 narracao_joanne.mp3; echo "  narração OK: ${D}s em $(( $(ts)-A ))s"; break; fi
    echo "  curta (${D}s<${MINDUR}s) retry"; rm -f poc_ttm.mp3; fi
done
[ $narr_ok -eq 1 ] || { echo "!!! narração falhou 3x — ABORT"; echo "@@@ FIM"; exit 1; }
A=$(ts); stage whisper; "$CBPY" transcrever_words.py 2>&1|tail -2; echo "  whisper: $(( $(ts)-A ))s"
for p in montar_timeline resolver_cascata epoca detectar_mapas pessoas datas topicos trilha efeitos fontes imagens ilustrar apresentar produto_cta; do
  A=$(ts); stage $p; python $p.py 2>&1|tail -2; echo "  $p: $(( $(ts)-A ))s"; done
A=$(ts); stage preparar; cd "$R"; python preparar_render.py 2>&1|tail -3; echo "  preparar: $(( $(ts)-A ))s"
# GATE DE NEGÓCIO: CTA do eBook é CORE BUSINESS — timeline sem produto_cta = produção ABORTADA (nunca silêncio)
stage gate-produto-cta
python -c "
import json,sys
tl=json.load(open('timeline_render.json',encoding='utf-8'))
sys.exit(0 if tl.get('produto_cta') else 1)
" || { echo '!!! GATE produto_cta: timeline SEM a janela do CTA do eBook — ABORT'; echo '@@@ FIM'; exit 1; }
echo "  gate produto_cta: OK ($(python -c "import json; c=json.load(open('timeline_render.json',encoding='utf-8'))['produto_cta']; print(f\"{c['inicio']:.0f}-{c['fim']:.0f}s\")"))"
# limpa chunks/saída de renders ANTERIORES (render-broll só checa existsSync -> reusaria chunk velho de outro roteiro)
stage limpar-chunks-velhos; rm -f out/_chunks/ttm_main.part*.mp4 out/ttm_main.mp4; echo "  chunks ttm_main antigos removidos"
A=$(ts); ok=0
for att in 1 2 3 4 5 6; do echo "@@@ render main tentativa $att @ $(date +%H:%M:%S)"
  RENDER_OUT=ttm_main.mp4 RENDER_CHUNKS=8 RENDER_CONCURRENCY=10 node render-broll.mjs; RC=$?
  [ $RC -eq 0 ] && { ok=1; break; }; echo "  falhou->retoma"; sleep 5; done
echo "  render main: $(( $(ts)-A ))s"
[ $ok -eq 1 ] || { echo "!!! render main falhou"; echo "@@@ FIM"; exit 1; }
stage coldopen; node render-comp.mjs TypewriterIntro ttm_coldopen.mp4 2>&1|tail -2
stage concat
# paths ABSOLUTOS (relativo falhava "Error opening input file out/_cc.txt") + -c copy (coldopen e main já saem
# do mesmo config Remotion: 1080p/30fps/h264/aac48k -> params idênticos, concat instantâneo e lossless).
printf "file '$R/out/ttm_coldopen.mp4'\nfile '$R/out/ttm_main.mp4'\n" > "$R/out/_cc.txt"
ffmpeg -y -f concat -safe 0 -i "$R/out/_cc.txt" -c copy "$R/out/ttm_hips_silent_fear_v1.mp4" 2>&1 | tail -3
if [ -f "$R/out/ttm_hips_silent_fear_v1.mp4" ]; then mv -f "$R/out/ttm_hips_silent_fear_v1.mp4" "D:/Meu Drive/canal_dark_videos/" && echo "  -> Drive OK"; else echo "  !!! concat falhou"; fi
echo "@@@ FIM @ $(date +%H:%M:%S)"
