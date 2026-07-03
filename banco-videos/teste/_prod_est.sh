#!/bin/bash
# Produção EST (estoicismo): narração george (com RETRY+validação) -> passes -> render.
export PYTHONUNBUFFERED=1; export NICHO=estoicismo
export MUSICA_PASTA="D:/Meu Drive/canal_estoicismo_trilhas"
T="F:/Canal Dark/Aplicativo de Edição/banco-videos/teste"; R="F:/Canal Dark/Aplicativo de Edição/remotion"
CBPY="F:/Canal Dark/chatterbox-test/venv/Scripts/python.exe"
VOZ="F:/Canal Dark/CapCut/CapCut Materials/Vozes/george_pcc_channel.mp3"
ts(){ date +%s; }; stage(){ echo "@@@ $1 @ $(date +%H:%M:%S)"; }
cd "$T"; cp roteiros/est_stay_silent.txt roteiro_en.txt
WORDS=$(wc -w < roteiro_en.txt); MINDUR=$(( WORDS / 4 ))   # piso: ~0.25s/palavra (pega truncamento)
echo "roteiro: $WORDS palavras | narração mínima esperada: ${MINDUR}s"
# --- NARRAÇÃO com retry + validação de duração ---
# PURGA artefatos de runs anteriores: senão um poc_est_stay.mp3 VELHO satisfaz [ -f ] e o driver aceita áudio de outro dia
rm -f poc_est_stay.mp3 poc_est_stay.bad.mp3 narracao_joanne.mp3 words.json
narr_ok=0
for natt in 1 2 3; do
  rm -f poc_est_stay.mp3 poc_est_stay.bad.mp3   # cada tentativa começa limpa: [ -f ] só passa se ESTA tentativa gerou
  A=$(ts); stage "narracao tentativa $natt"
  "$CBPY" narrar_job.py "$VOZ" poc_est_stay 2>&1 | tail -2
  if [ -f poc_est_stay.mp3 ]; then
    D=$(ffprobe -v error -show_entries format=duration -of csv=p=0 poc_est_stay.mp3 2>/dev/null | cut -d. -f1); D=${D:-0}
    if [ "$D" -ge "$MINDUR" ]; then narr_ok=1; cp poc_est_stay.mp3 narracao_joanne.mp3; echo "  narração OK: ${D}s (>= ${MINDUR}s) em $(( $(ts)-A ))s"; break; fi
    echo "  narração CURTA (${D}s < ${MINDUR}s) — Chatterbox travou, retry"; rm -f poc_est_stay.mp3
  else echo "  sem mp3 — retry"; fi
done
[ $narr_ok -eq 1 ] || { echo "!!! narração falhou após 3 tentativas — ABORTANDO (não faço vídeo truncado)"; echo "@@@ FIM @ $(date +%H:%M:%S)"; exit 1; }
A=$(ts); stage whisper; "$CBPY" transcrever_words.py 2>&1 | tail -2; echo "  whisper: $(( $(ts)-A ))s"
for p in montar_timeline resolver_cascata epoca detectar_mapas pessoas datas topicos trilha efeitos fontes imagens ilustrar apresentar; do
  A=$(ts); stage $p; python $p.py 2>&1 | tail -2; echo "  $p: $(( $(ts)-A ))s"
done
A=$(ts); stage preparar; cd "$R"; python preparar_render.py 2>&1 | tail -3; echo "  preparar: $(( $(ts)-A ))s"
# limpa chunks/saída de render anterior (render-broll só checa existsSync -> reusaria chunk velho)
OUTNAME="${1:-est_stay_silent}"
stage limpar-chunks-velhos; rm -f out/_chunks/est_main.part*.mp4 out/est_main.mp4; echo "  chunks antigos removidos"
A=$(ts); ok=0
for att in 1 2 3 4 5 6; do
  echo "@@@ render main tentativa $att @ $(date +%H:%M:%S)"
  RENDER_OUT=est_main.mp4 RENDER_CHUNKS=8 RENDER_CONCURRENCY=10 node render-broll.mjs
  RC=$?; [ $RC -eq 0 ] && { ok=1; break; }; echo "  falhou -> retoma"; sleep 5
done
echo "  render: $(( $(ts)-A ))s"
[ $ok -eq 1 ] || { echo "  !!! render falhou"; echo "@@@ FIM"; exit 1; }
# cold-open typewriter (Epictetus por default; p/ citação por vídeo, passe COMP_PROPS='{"quote":...,"author":...}')
stage coldopen; node render-comp.mjs TypewriterQuote est_coldopen.mp4 2>&1 | tail -2
stage concat
printf "file '$R/out/est_coldopen.mp4'\nfile '$R/out/est_main.mp4'\n" > "$R/out/_cce.txt"
ffmpeg -y -f concat -safe 0 -i "$R/out/_cce.txt" -c copy "$R/out/${OUTNAME}.mp4" 2>&1 | tail -3
if [ -f "$R/out/${OUTNAME}.mp4" ]; then mv -f "$R/out/${OUTNAME}.mp4" "D:/Meu Drive/canal_dark_videos/" && echo "  -> Drive OK: ${OUTNAME}.mp4"; else echo "  !!! concat falhou"; fi
echo "@@@ FIM @ $(date +%H:%M:%S)"
