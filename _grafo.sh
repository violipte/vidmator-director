#!/bin/bash
# Atualiza o grafo do projeto (AST local, sem LLM, custo zero). Rode antes de mexer em código.
"F:/Canal Dark/graphify_venv/Scripts/graphify.exe" update "F:/Canal Dark/Aplicativo de Edição" --no-cluster
echo "consultar: graphify explain \"Nome\" | graphify path \"A\" \"B\" (--graph graphify-out/graph.json)"
