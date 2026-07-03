#!/bin/bash
# Continua a produção do memento_mori_5passos a partir do RESOLVER (narração/whisper/montar já feitos).
# Cronometra cada etapa (imprime HH:MM:SS antes de cada uma + dura no fim).
export PYTHONUNBUFFERED=1
T="F:/Canal Dark/Aplicativo de Edição/banco-videos/teste"; R="F:/Canal Dark/Aplicativo de Edição/remotion"
ts(){ date +%s; }
stage(){ echo "@@@ $1 @ $(date +%H:%M:%S)"; }
cd "$T"
A=$(ts); stage resolver;   python resolver_cascata.py 2>&1 | tail -3; echo "   resolver: $(( $(ts)-A ))s"
A=$(ts); stage mapas;      python detectar_mapas.py   2>&1 | tail -2; echo "   mapas: $(( $(ts)-A ))s"
A=$(ts); stage pessoas;    python pessoas.py          2>&1 | tail -2; echo "   pessoas: $(( $(ts)-A ))s"
A=$(ts); stage datas;      python datas.py            2>&1 | tail -2; echo "   datas: $(( $(ts)-A ))s"
A=$(ts); stage topicos;    python topicos.py          2>&1 | tail -2; echo "   topicos: $(( $(ts)-A ))s"
A=$(ts); stage trilha;     python trilha.py           2>&1 | tail -2; echo "   trilha: $(( $(ts)-A ))s"
A=$(ts); stage efeitos;    python efeitos.py          2>&1 | tail -2; echo "   efeitos: $(( $(ts)-A ))s"
A=$(ts); stage fontes;     python fontes.py           2>&1 | tail -2; echo "   fontes: $(( $(ts)-A ))s"
A=$(ts); stage imagens;    python imagens.py          2>&1 | tail -2; echo "   imagens: $(( $(ts)-A ))s"
A=$(ts); stage ilustrar;   python ilustrar.py         2>&1 | tail -2; echo "   ilustrar: $(( $(ts)-A ))s"
A=$(ts); stage preparar;   cd "$R"; python preparar_render.py 2>&1 | tail -3; echo "   preparar: $(( $(ts)-A ))s"
A=$(ts); stage render;     RENDER_OUT=memento_mori_5passos.mp4 node render-broll.mjs; echo "   render: $(( $(ts)-A ))s"
mkdir -p "D:/Meu Drive/canal_dark_videos"; mv "out/memento_mori_5passos.mp4" "D:/Meu Drive/canal_dark_videos/" && echo "   -> Drive"
echo "@@@ CONT OK @ $(date +%H:%M:%S)"
