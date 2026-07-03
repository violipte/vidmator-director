#!/bin/bash
# FINALIZA o memento_mori_5passos: footage JA esta bom (108 img/81 video, sem verde, sem reuso).
# Falta so o enriquecimento (Gemini) + render. NAO re-roda resolver.
# TRAVA: se a quota do Gemini ainda estiver morta, aborta ANTES do render (nao gera video sem enriquecimento).
export PYTHONUNBUFFERED=1
T="F:/Canal Dark/Aplicativo de Edição/banco-videos/teste"
R="F:/Canal Dark/Aplicativo de Edição/remotion"
ts(){ date +%s; }
stage(){ echo "@@@ $1 @ $(date +%H:%M:%S)"; }
cd "$T"
: > _gpt_usage.jsonl   # zera o contador de tokens GPT desta run

echo "=== precheck LLM (cascata Gemini -> GPT-5 -> Claude) ==="
python -c "
import sys
from gemini_api import gemini_arr
r = gemini_arr('Return ONLY a JSON array: [{\"ok\":1}]', 60)
if r:
    print('LLM respondendo:', r); sys.exit(0)
print('Nenhum LLM respondeu -> ABORTA'); sys.exit(3)
" || exit 3

A=$(ts); stage mapas;    python detectar_mapas.py 2>&1 | tail -2; echo "   mapas: $(( $(ts)-A ))s"
A=$(ts); stage pessoas;  python pessoas.py        2>&1 | tail -3; echo "   pessoas: $(( $(ts)-A ))s"
A=$(ts); stage datas;    python datas.py          2>&1 | tail -2; echo "   datas: $(( $(ts)-A ))s"
A=$(ts); stage topicos;  python topicos.py        2>&1 | tail -2; echo "   topicos: $(( $(ts)-A ))s"
A=$(ts); stage trilha;   python trilha.py         2>&1 | tail -2; echo "   trilha: $(( $(ts)-A ))s"
A=$(ts); stage efeitos;  python efeitos.py        2>&1 | tail -2; echo "   efeitos: $(( $(ts)-A ))s"
A=$(ts); stage fontes;   python fontes.py         2>&1 | tail -2; echo "   fontes: $(( $(ts)-A ))s"
A=$(ts); stage imagens;  python imagens.py        2>&1 | tail -2; echo "   imagens: $(( $(ts)-A ))s"
A=$(ts); stage ilustrar; python ilustrar.py       2>&1 | tail -2; echo "   ilustrar: $(( $(ts)-A ))s"

echo "=== ENRIQUECIMENTO (verificacao) ==="
python -c "import json,collections; tl=json.load(open('timeline.json',encoding='utf-8')); c=tl['cenas']; print('tipos:',dict(collections.Counter(x.get('media_tipo','?') for x in c))); print('mood:',dict(collections.Counter(x.get('mood','?') for x in c))); print('pessoas:',len(tl.get('pessoas',[])),'| topicos:',len(tl.get('topicos',[])),'| mapas:',len(tl.get('mapas',[])),'| datas:',len(tl.get('datas',[])))"

A=$(ts); stage preparar; cd "$R"; python preparar_render.py 2>&1 | tail -3; echo "   preparar: $(( $(ts)-A ))s"
A=$(ts); stage render;   RENDER_OUT=memento_mori_5passos.mp4 RENDER_CONCURRENCY=10 node render-broll.mjs; RC=$?; echo "   render: $(( $(ts)-A ))s (exit $RC)"
if [ $RC -eq 0 ] && [ -f "out/memento_mori_5passos.mp4" ]; then
  mkdir -p "D:/Meu Drive/canal_dark_videos"
  mv -f "out/memento_mori_5passos.mp4" "D:/Meu Drive/canal_dark_videos/" && echo "   -> Drive OK"
else
  echo "   !!! render falhou (exit $RC)"
fi
echo "=== CUSTO GPT-5 (esta run) ==="
cd "$T"; python -c "
import json
ti=to=n=0
try:
    for ln in open('_gpt_usage.jsonl',encoding='utf-8'):
        d=json.loads(ln); ti+=d.get('in',0); to+=d.get('out',0); n+=1
except FileNotFoundError: pass
IN=1.25/1e6; OUT=10.0/1e6   # GPT-5: 1.25 USD/1M in, 10 USD/1M out (out inclui reasoning)
c=ti*IN+to*OUT
print(f'  chamadas GPT-5: {n} | tokens: {ti} in + {to} out')
print(f'  CUSTO: US\$ {c:.4f}  (~R\$ {c*5.5:.3f} a 5.5)')
"
echo "@@@ FINISH FIM @ $(date +%H:%M:%S)"
