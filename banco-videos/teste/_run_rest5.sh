#!/bin/bash
set -e
TESTE="F:/Canal Dark/Aplicativo de Edição/banco-videos/teste"
REMO="F:/Canal Dark/Aplicativo de Edição/remotion"
CBPY="F:/Canal Dark/chatterbox-test/venv/Scripts/python.exe"
cd "$TESTE"
echo "### narração de trabalho ###"
cp poc_wwii.mp3 narracao_joanne.mp3
echo "### whisper (venv chatterbox) ###"
"$CBPY" transcrever_words.py 2>&1 | tail -3
echo "### montar_timeline (stock_query) ###"
python montar_timeline.py 2>&1 | tail -4
echo "### resolver em cascata (L2 commons -> L3 vídeo -> L4 foto -> L5 genérico) ###"
python resolver_cascata.py 2>&1 | tail -8
echo "### detectar_mapas ###"
python detectar_mapas.py 2>&1 | tail -5
echo "### pessoas ###"
python pessoas.py 2>&1 | tail -7
echo "### datas ###"
python datas.py 2>&1 | tail -6
echo "### topicos (segmentação) ###"
python topicos.py 2>&1 | tail -9
echo "### trilha (música por tópico, corte seco) ###"
python trilha.py 2>&1 | tail -9
echo "### efeitos (humor) ###"
python efeitos.py 2>&1 | tail -3
echo "### imagens PD do caso ###"
python imagens.py 2>&1 | tail -6
echo "### ilustrar (por último, ciente de mapas/pessoas/datas/imagens) ###"
python ilustrar.py 2>&1 | tail -5
echo "### preparar_render ###"
cd "$REMO"
python preparar_render.py 2>&1 | tail -8
echo "### MONTAGEM DONE (render separado) ###"
