#!/bin/bash
export NICHO=motos
TESTE="F:/Canal Dark/Aplicativo de Edição/banco-videos/teste"
REMO="F:/Canal Dark/Aplicativo de Edição/remotion"
CBPY="F:/Canal Dark/chatterbox-test/venv/Scripts/python.exe"
cd "$TESTE"
echo "### narração ###"; cp poc_motos.mp3 narracao_joanne.mp3
echo "### whisper ###"; "$CBPY" transcrever_words.py 2>&1 | tail -3
echo "### montar_timeline ###"; python montar_timeline.py 2>&1 | tail -4
python -c "import json; tl=json.load(open('timeline.json',encoding='utf-8')); tl['nicho']='motos'; json.dump(tl,open('timeline.json','w',encoding='utf-8'),ensure_ascii=False,indent=2); print('nicho=motos setado')"
echo "### resolver_cascata ###"; python resolver_cascata.py 2>&1 | tail -8
echo "### detectar_mapas ###"; python detectar_mapas.py 2>&1 | tail -4
echo "### pessoas ###"; python pessoas.py 2>&1 | tail -5
echo "### datas ###"; python datas.py 2>&1 | tail -4
echo "### topicos ###"; python topicos.py 2>&1 | tail -9
echo "### trilha ###"; python trilha.py 2>&1 | tail -8
echo "### efeitos ###"; python efeitos.py 2>&1 | tail -3
echo "### imagens ###"; python imagens.py 2>&1 | tail -4
echo "### ilustrar ###"; python ilustrar.py 2>&1 | tail -4
echo "### preparar_render ###"; cd "$REMO"; python preparar_render.py 2>&1 | tail -8
echo "### MONTAGEM DONE ###"
