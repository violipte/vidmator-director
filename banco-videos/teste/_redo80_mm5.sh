#!/bin/bash
# REDO com balanco ~80% video / 20% imagem + fix ICC nas imagens.
# Enriquecimento (pessoas/efeitos/musica/mapas) JA esta na timeline.json e e preservado pelo resolver.
export PYTHONUNBUFFERED=1
T="F:/Canal Dark/Aplicativo de Edição/banco-videos/teste"
R="F:/Canal Dark/Aplicativo de Edição/remotion"
ts(){ date +%s; }
stage(){ echo "@@@ $1 @ $(date +%H:%M:%S)"; }

cd "$T"
A=$(ts); stage resolver; python resolver_cascata.py 2>&1 | tail -8; echo "   resolver: $(( $(ts)-A ))s"

echo "=== ratio video/imagem apos resolver ==="
python -c "import json,collections; c=json.load(open('timeline.json',encoding='utf-8'))['cenas']; t=collections.Counter(x.get('media_tipo','?') for x in c); v=t.get('video',0); i=t.get('imagem',0); tot=v+i or 1; print('video=%d (%.0f%%) | imagem=%d (%.0f%%)'%(v,100*v/tot,i,100*i/tot)); print('niveis:',dict(collections.Counter(x.get(chr(110)+'ivel','?') for x in c)))"

A=$(ts); stage preparar; cd "$R"; python preparar_render.py 2>&1 | tail -4; echo "   preparar: $(( $(ts)-A ))s"

# infografico/ilustracao ainda quebram o render (renderer nao endurecido) -> remove desta render
python -c "
import json
tl=json.load(open('timeline_render.json',encoding='utf-8'))
n=sum(1 for c in tl['cenas'] if c.get('infografico') or c.get('ilustracao'))
for c in tl['cenas']: c['infografico']=None; c['ilustracao']=None
json.dump(tl, open('timeline_render.json','w',encoding='utf-8'), ensure_ascii=False, indent=2)
print('strip infografico/ilustracao:', n, 'cenas')
"

A=$(ts); stage render; RENDER_OUT=memento_mori_5passos.mp4 RENDER_CONCURRENCY=10 node render-broll.mjs; RC=$?; echo "   render: $(( $(ts)-A ))s (exit $RC)"
echo "   EncodingError (deve ser 0 agora): $(grep -c EncodingError "$T/_redo80_mm5.log" 2>/dev/null || echo '?')"
if [ $RC -eq 0 ] && [ -f "out/memento_mori_5passos.mp4" ]; then
  mkdir -p "D:/Meu Drive/canal_dark_videos"
  mv -f "out/memento_mori_5passos.mp4" "D:/Meu Drive/canal_dark_videos/" && echo "   -> Drive OK"
else
  echo "   !!! render falhou (exit $RC)"
fi
echo "@@@ FIM @ $(date +%H:%M:%S)"
