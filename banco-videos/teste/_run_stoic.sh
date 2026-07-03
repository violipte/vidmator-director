#!/bin/bash
set -e
export PYTHONUNBUFFERED=1
TESTE="F:/Canal Dark/Aplicativo de Edição/banco-videos/teste"
REMO="F:/Canal Dark/Aplicativo de Edição/remotion"
CBPY="F:/Canal Dark/chatterbox-test/venv/Scripts/python.exe"
cd "$TESTE"

echo "### 1 narração george_pcc (Chatterbox/CUDA) ###"
"$CBPY" _gen_stoic.py
cp poc_stoic.mp3 narracao_joanne.mp3

echo "### 2 whisper (transcrição por palavra) ###"
"$CBPY" transcrever_words.py 2>&1 | tail -3
echo "### 3 montar_timeline (stock_query) ###"
python montar_timeline.py 2>&1 | tail -4
echo "### 4 resolver em cascata (50/50 img/vídeo, época via Commons) ###"
python resolver_cascata.py 2>&1 | tail -6
echo "### 5 detectar_mapas ###"
python detectar_mapas.py 2>&1 | tail -4
echo "### 6 pessoas (Marco Aurélio/Epicteto/Sêneca) ###"
python pessoas.py 2>&1 | tail -6
echo "### 7 datas ###"
python datas.py 2>&1 | tail -4
echo "### 8 topicos ###"
python topicos.py 2>&1 | tail -6
echo "### 9 trilha ###"
python trilha.py 2>&1 | tail -6
echo "### 10 efeitos (humor) ###"
python efeitos.py 2>&1 | tail -3
echo "### 11 fontes (niche -> tema) ###"
python fontes.py 2>&1 | tail -2
echo "### 12 imagens PD ###"
python imagens.py 2>&1 | tail -4
echo "### 13 ilustrar ###"
python ilustrar.py 2>&1 | tail -4
echo "### 14 preparar_render ###"
cd "$REMO" && python preparar_render.py 2>&1 | tail -6
echo "### 15 render ###"
cd "$REMO" && node render-broll.mjs
echo "### STOIC DONE ###"
