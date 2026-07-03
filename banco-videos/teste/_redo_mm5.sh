#!/bin/bash
# REDO completo do memento_mori_5passos com as correcoes:
#  - green-screen filtrado + 4 chaves Pexels + vies imagem+KenBurns (resolver)
#  - enriquecimento re-rodado com Gemini OK (pessoas/topicos/efeitos/datas/mapas)
# Narracao/whisper/montar reaproveitados (timeline.json ja tem as 189 cenas).
export PYTHONUNBUFFERED=1
T="F:/Canal Dark/Aplicativo de Edição/banco-videos/teste"
R="F:/Canal Dark/Aplicativo de Edição/remotion"
IDX="F:/Canal Dark/Aplicativo de Edição/banco-videos/_cache_stock/index_cascata.json"
ts(){ date +%s; }
stage(){ echo "@@@ $1 @ $(date +%H:%M:%S)"; }
cd "$T"
# cache fresh: forca re-resolver tudo com a logica nova
[ -f "$IDX" ] && mv "$IDX" "$IDX.bak" && echo "index_cascata resetado (backup .bak)"
A=$(ts); stage resolver;   python resolver_cascata.py 2>&1 | tail -10; echo "   resolver: $(( $(ts)-A ))s"
A=$(ts); stage mapas;      python detectar_mapas.py   2>&1 | tail -2;  echo "   mapas: $(( $(ts)-A ))s"
A=$(ts); stage pessoas;    python pessoas.py          2>&1 | tail -2;  echo "   pessoas: $(( $(ts)-A ))s"
A=$(ts); stage datas;      python datas.py            2>&1 | tail -2;  echo "   datas: $(( $(ts)-A ))s"
A=$(ts); stage topicos;    python topicos.py          2>&1 | tail -2;  echo "   topicos: $(( $(ts)-A ))s"
A=$(ts); stage trilha;     python trilha.py           2>&1 | tail -2;  echo "   trilha: $(( $(ts)-A ))s"
A=$(ts); stage efeitos;    python efeitos.py          2>&1 | tail -2;  echo "   efeitos: $(( $(ts)-A ))s"
A=$(ts); stage fontes;     python fontes.py           2>&1 | tail -2;  echo "   fontes: $(( $(ts)-A ))s"
A=$(ts); stage imagens;    python imagens.py          2>&1 | tail -2;  echo "   imagens: $(( $(ts)-A ))s"
A=$(ts); stage ilustrar;   python ilustrar.py         2>&1 | tail -2;  echo "   ilustrar: $(( $(ts)-A ))s"
# resumo do enriquecimento ANTES de gastar 22min de render
echo "=== ENRIQUECIMENTO (verificacao) ==="
python -c "import json,collections; tl=json.load(open('timeline.json',encoding='utf-8')); c=tl['cenas']; print('niveis:',dict(collections.Counter(x.get(chr(110)+'ivel','?') for x in c))); print('tipos:',dict(collections.Counter(x.get('media_tipo','?') for x in c))); print('mood:',dict(collections.Counter(x.get('mood','?') for x in c))); print('pessoas:',len(tl.get('pessoas',[])),'| topicos:',len(tl.get('topicos',[])),'| mapas:',len(tl.get('mapas',[])),'| datas:',len(tl.get('datas',[])),'| imagens:',len(tl.get('imagens',[])))"
A=$(ts); stage preparar;   cd "$R"; python preparar_render.py 2>&1 | tail -3; echo "   preparar: $(( $(ts)-A ))s"
A=$(ts); stage render;     RENDER_OUT=memento_mori_5passos.mp4 RENDER_CONCURRENCY=10 node render-broll.mjs; RC=$?; echo "   render: $(( $(ts)-A ))s (exit $RC)"
if [ $RC -eq 0 ] && [ -f "out/memento_mori_5passos.mp4" ]; then
  mkdir -p "D:/Meu Drive/canal_dark_videos"
  mv -f "out/memento_mori_5passos.mp4" "D:/Meu Drive/canal_dark_videos/" && echo "   -> Drive OK"
else
  echo "   !!! render falhou (exit $RC)"
fi
echo "@@@ REDO FIM @ $(date +%H:%M:%S)"
