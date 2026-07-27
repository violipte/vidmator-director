#!/bin/bash
# Inclui/atualiza os DOCS de design no grafo (extração SEMÂNTICA via Gemini).
# Complementa _grafo.sh (que é só código/AST). Idempotente: build_merge substitui os nós do doc.
# Requer: openai instalado no graphify_venv (já feito) + chave Gemini no credentials.json.
cd "F:/Canal Dark/Aplicativo de Edição" || exit 1
GXPY="F:/Canal Dark/graphify_venv/Scripts/python.exe"
GX="F:/Canal Dark/graphify_venv/Scripts/graphify.exe"
export GEMINI_API_KEY=$(python -c "import json;print(next((c['api_key'] for c in json.load(open('video-automator/credentials.json',encoding='utf-8')) if c.get('provedor')=='gemini' and c.get('api_key')),''))" 2>/dev/null)
export GRAPHIFY_GEMINI_MODEL=gemini-2.5-flash
"$GXPY" - <<'PY'
import json
from pathlib import Path
from graphify.llm import extract_corpus_parallel
from graphify.build import build_merge
from graphify.cluster import cluster
from graphify.export import to_json
ROOT = "F:/Canal Dark/Aplicativo de Edição"
# docs de design a incluir no grafo (adicione novos aqui)
DOCS = ["VIDMATOR_ACERVO.md", "REGRAS_NICHOS.md", "ARSENAL_NICHOS.md"]
docs = [Path(ROOT)/d for d in DOCS if (Path(ROOT)/d).exists()]
sem = extract_corpus_parallel(docs, backend="gemini")
print("docs semantico:", len(sem.get('nodes', [])), "nos,", len(sem.get('edges', [])), "edges")
G = build_merge([sem], graph_path="graphify-out/graph.json", root=ROOT, directed=False)
comms = cluster(G)
to_json(G, comms, "graphify-out/graph.json")
print("grafo:", G.number_of_nodes(), "nos,", G.number_of_edges(), "edges,", len(comms), "comunidades")
PY
"$GX" export html >/dev/null 2>&1 && echo "graph.html atualizado -> graphify-out/graph.html"
