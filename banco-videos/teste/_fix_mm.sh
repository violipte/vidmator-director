#!/bin/bash
set -e
export PYTHONUNBUFFERED=1
T="F:/Canal Dark/Aplicativo de Edição/banco-videos/teste"; R="F:/Canal Dark/Aplicativo de Edição/remotion"
cd "$T"
echo "### topicos ###"; python topicos.py 2>&1 | tail -9
echo "### pessoas ###"; python pessoas.py 2>&1 | tail -7
echo "### trilha ###"; python trilha.py 2>&1 | tail -9
echo "### preparar ###"; cd "$R" && python preparar_render.py 2>&1 | tail -6
echo "### render ###"; RENDER_OUT=memento_mori.mp4 node render-broll.mjs
echo "### FIX OK ###"
