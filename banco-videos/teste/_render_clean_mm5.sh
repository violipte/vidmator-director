#!/bin/bash
# Re-render LIMPO: remove infografico+ilustracao (renderer ainda nao robusto p/ valor=texto; nao foram pedidos).
# Mantem TUDO que o usuario pediu: footage 50/50 sem verde, pessoas, mood/efeitos, musica, mapas.
export PYTHONUNBUFFERED=1
R="F:/Canal Dark/Aplicativo de Edição/remotion"
cd "$R"
python -c "
import json
tl=json.load(open('timeline_render.json',encoding='utf-8'))
n=sum(1 for c in tl['cenas'] if c.get('infografico') or c.get('ilustracao'))
for c in tl['cenas']:
    c['infografico']=None; c['ilustracao']=None
json.dump(tl, open('timeline_render.json','w',encoding='utf-8'), ensure_ascii=False, indent=2)
print('strip: %d cenas tinham infografico/ilustracao -> removidos (impacto/texto preservados)' % n)
"
echo "@@@ render @ $(date +%H:%M:%S)"
A=$(date +%s)
RENDER_OUT=memento_mori_5passos.mp4 RENDER_CONCURRENCY=10 node render-broll.mjs; RC=$?
echo "   render: $(( $(date +%s)-A ))s (exit $RC)"
if [ $RC -eq 0 ] && [ -f "out/memento_mori_5passos.mp4" ]; then
  mkdir -p "D:/Meu Drive/canal_dark_videos"
  mv -f "out/memento_mori_5passos.mp4" "D:/Meu Drive/canal_dark_videos/" && echo "   -> Drive OK"
  ls -la "D:/Meu Drive/canal_dark_videos/memento_mori_5passos.mp4" | awk '{print "   ", int($5/1024/1024)" MB"}'
else
  echo "   !!! render falhou (exit $RC)"
fi
echo "@@@ FIM @ $(date +%H:%M:%S)"
