#!/bin/bash
export NICHO=motos
T="F:/Canal Dark/Aplicativo de Edição/banco-videos/teste"
R="F:/Canal Dark/Aplicativo de Edição/remotion"
CB="F:/Canal Dark/chatterbox-test/venv/Scripts/python.exe"
cd "$T"
cp roteiro_motos.txt roteiro_en.txt
cp poc_motos.mp3 narracao_joanne.mp3
echo "### whisper ###"; "$CB" transcrever_words.py 2>&1 | tail -1
echo "### montar ###"; python montar_timeline.py 2>&1 | tail -1
python -c "import json;tl=json.load(open('timeline.json',encoding='utf-8'));tl['nicho']='motos';json.dump(tl,open('timeline.json','w',encoding='utf-8'),ensure_ascii=False,indent=2)"
echo "### cascata ###"; python resolver_cascata.py 2>&1 | tail -1
python detectar_mapas.py 2>&1 | tail -1; python pessoas.py 2>&1 | tail -1; python datas.py 2>&1 | tail -1
echo "### topicos/trilha/efeitos/imagens/ilustrar ###"
python topicos.py 2>&1 | tail -1; python trilha.py 2>&1 | tail -1; python efeitos.py 2>&1 | tail -1
python imagens.py 2>&1 | tail -1; python ilustrar.py 2>&1 | tail -1
cd "$R"
echo "### preparar_render ###"; python preparar_render.py 2>&1 | tail -1
echo "### RENDER ###"; node render-broll.mjs 2>&1 | tail -1
echo "### -> DRIVE ###"; cp out/broll_test.mp4 "/d/Meu Drive/top5_motos_daily_USA.mp4" && echo "DRIVE OK: top5_motos_daily_USA.mp4"
cd "$T"
cp _bak_wwii_roteiro.txt roteiro_en.txt; cp _bak_wwii_words.json words.json; cp _bak_wwii_timeline.json timeline.json; cp poc_wwii.mp3 narracao_joanne.mp3
echo "### WWII restaurado | REGEN DONE ###"
