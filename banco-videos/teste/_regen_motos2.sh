#!/bin/bash
# Regen do Top-5 Motos com footage PRODUTO-LOCKED (fotos do modelo exato).
# Isola o render (JOB/OUT/BUNDLE/TMP) e restaura o estado compartilhado ANTES do render.
export NICHO=motos
T="F:/Canal Dark/Aplicativo de Edição/banco-videos/teste"
R="F:/Canal Dark/Aplicativo de Edição/remotion"
CB="F:/Canal Dark/chatterbox-test/venv/Scripts/python.exe"
MUSIC="F:/Canal Dark/Music/background-royalty-free-music-documentary-piano-305672.mp3"
cd "$T"

# 1) snapshot do estado ATUAL (seja WWII ou o que o outro Claude tiver) — restauro isto no fim
cp roteiro_en.txt _bak_now_roteiro.txt
cp words.json _bak_now_words.json
cp timeline.json _bak_now_timeline.json
cp narracao_joanne.mp3 _bak_now_narr.mp3
restore() { cd "$T"; cp _bak_now_roteiro.txt roteiro_en.txt; cp _bak_now_words.json words.json; \
            cp _bak_now_timeline.json timeline.json; cp _bak_now_narr.mp3 narracao_joanne.mp3; \
            echo "### estado compartilhado restaurado ###"; }
trap restore EXIT

# 2) inputs do motos
cp roteiro_motos.txt roteiro_en.txt
cp poc_motos.mp3 narracao_joanne.mp3

# 3) passes (janela curta em que timeline.json = motos)
echo "### whisper ###";  "$CB" transcrever_words.py 2>&1 | tail -1
echo "### montar ###";   python montar_timeline.py 2>&1 | tail -1
python -c "import json;tl=json.load(open('timeline.json',encoding='utf-8'));tl['nicho']='motos';json.dump(tl,open('timeline.json','w',encoding='utf-8'),ensure_ascii=False,indent=2)"
echo "### OVERRIDE footage ###"; python override_motos_footage.py 2>&1 | tail -1
echo "### topicos ###";  python topicos.py 2>&1 | tail -1
echo "### efeitos ###";  python efeitos.py 2>&1 | tail -1
echo "### ilustrar ###"; python ilustrar.py 2>&1 | tail -1
echo "### fix nomes+sfx ###"; python fix_motos_final.py 2>&1 | tail -1

# 4) preparar_render ISOLADO -> timeline_motos2.json + public/jobs/motos2/
cd "$R"
echo "### preparar (JOB=motos2) ###"; JOB=motos2 NICHO=motos python preparar_render.py 2>&1 | tail -3

# 5) troca a trilha zen pela cama neutra de documentário
cp "$MUSIC" "public/jobs/motos2/musica.mp3" && echo "musica -> documentary piano (cama neutra)"

# 6) RESTAURA o estado compartilhado AGORA (render lê o snapshot isolado, não o timeline.json)
restore; trap - EXIT

# 7) render ISOLADO (input/output/bundle/tmp próprios; concurrency moderado p/ dividir GPU)
echo "### RENDER (isolado motos2) ###"
RENDER_TIMELINE=timeline_motos2.json RENDER_OUT=motos2.mp4 \
  REMOTION_BUNDLE=_bundle_motos2 REMOTION_TMP=_tmp_motos2 RENDER_CONCURRENCY=10 \
  node render-broll.mjs 2>&1 | tail -3

# 8) entrega no Drive
if [ -f out/motos2.mp4 ]; then
  cp out/motos2.mp4 "/d/Meu Drive/top5_motos_daily_USA.mp4" && echo "DRIVE OK: top5_motos_daily_USA.mp4"
  ffprobe -v error -show_entries format=duration -of csv=p=0 out/motos2.mp4
else
  echo "ERRO: render nao gerou out/motos2.mp4"
fi

# 9) limpa bundle/tmp isolados
rm -rf "$R/_bundle_motos2" "$R/_tmp_motos2" 2>/dev/null
echo "### MOTOS2 DONE ###"
