#!/usr/bin/env bash
set -e
export PYTHONUNBUFFERED=1
TESTE="F:/Canal Dark/Aplicativo de Edição/banco-videos/teste"
REM="F:/Canal Dark/Aplicativo de Edição/remotion"

echo "===== 1/4 FONTES (niche -> tema) ====="
cd "$TESTE" && python -u fontes.py

echo "===== 2/4 OVERRIDE -> typewriter (validar typing+SFX) ====="
cd "$TESTE" && python -u -c "import json; d=json.load(open('timeline.json',encoding='utf-8')); print('niche pick foi:', d.get('fonte_tema')); d['fonte_tema']='typewriter'; json.dump(d,open('timeline.json','w',encoding='utf-8'),ensure_ascii=False,indent=2); print('override -> typewriter')"

echo "===== 3/4 PREPARAR ====="
cd "$REM" && python -u preparar_render.py

echo "===== 4/4 RENDER ====="
cd "$REM" && node render-broll.mjs

echo "===== CHAIN OK ====="
