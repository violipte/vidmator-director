#!/usr/bin/env bash
set -e
export PYTHONUNBUFFERED=1
TESTE="F:/Canal Dark/Aplicativo de Edição/banco-videos/teste"
REM="F:/Canal Dark/Aplicativo de Edição/remotion"

echo "===== 0/4 LIMPA banco antigo ====="
rm -f "$TESTE/_arquivo_tema"/tema_*.mp4 "$TESTE/_arquivo_tema/catalogo.json" || true

echo "===== 1/4 BANCO DE ARQUIVO (rápido: metadata, cap docs, -u) ====="
cd "$TESTE" && python -u banco_arquivo_tema.py

echo "===== 2/4 RESOLVER (cap de reuso por janela) ====="
cd "$TESTE" && python -u resolver_cascata.py

echo "===== 3/4 PREPARAR RENDER ====="
cd "$REM" && python -u preparar_render.py

echo "===== 4/4 RENDER ====="
cd "$REM" && node render-broll.mjs

echo "===== CHAIN OK ====="
