#!/usr/bin/env bash
set -e
export PYTHONUNBUFFERED=1
TESTE="F:/Canal Dark/Aplicativo de Edição/banco-videos/teste"
REM="F:/Canal Dark/Aplicativo de Edição/remotion"

echo "===== 1/3 RESOLVER (cascata revertida: real -> imagem época -> stock) ====="
cd "$TESTE" && python -u resolver_cascata.py

echo "===== 2/3 PREPARAR RENDER ====="
cd "$REM" && python -u preparar_render.py

echo "===== 3/3 RENDER ====="
cd "$REM" && node render-broll.mjs

echo "===== CHAIN OK ====="
