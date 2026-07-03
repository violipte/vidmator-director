#!/bin/bash
R="F:/Canal Dark/Aplicativo de Edição/remotion"; ts(){ date +%s; }
cd "$R"
A=$(ts); echo "@@@ preparar @ $(date +%H:%M:%S)"; python preparar_render.py 2>&1 | tail -4; echo "   preparar: $(( $(ts)-A ))s"
A=$(ts); echo "@@@ render @ $(date +%H:%M:%S)"; RENDER_OUT=memento_mori_5passos.mp4 node render-broll.mjs; echo "   render: $(( $(ts)-A ))s"
mkdir -p "D:/Meu Drive/canal_dark_videos"; mv "out/memento_mori_5passos.mp4" "D:/Meu Drive/canal_dark_videos/" && echo "   -> Drive"
echo "@@@ RENDER OK @ $(date +%H:%M:%S)"
