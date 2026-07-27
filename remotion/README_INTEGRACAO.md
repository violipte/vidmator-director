# Remotion — Editor de Overlays do Video Automator

Projeto Remotion (open source) usado como **gerador de overlays/transições** que entram no pipeline FFmpeg do `video-automator/`.

## Arquitetura

```
remotion/                    <- este projeto (Node + React + TypeScript)
  src/
    index.ts                 entry point
    Root.tsx                 registra Compositions
    compositions/
      CtaCard.tsx            overlay CTA animado (exemplo)
      [futuro: LowerThird, Intro, Outro, TransitionFade...]
  out/                       saída dos renders (MP4 com alpha)

video-automator/             <- pipeline atual (Python + FFmpeg + NVENC)
  engine.py                  carrega overlays do remotion/out/ via -i
                             e compõe no final via overlay/concat filter
```

## Por que separado

- FFmpeg+NVENC continua sendo o render principal (15min pra vídeo de 40min na 5070 Ti)
- Remotion não é apto pra vídeos longos (puppeteer = 5-30× mais lento)
- Mas Remotion é **superior** pra layout/animação de elementos curtos (CTA, intro, transição)
- **Pre-render 1 vez, reusa infinito** — custo de Remotion é amortizado

## Comandos

```bash
npm run dev      # Remotion Studio (preview hot-reload em http://localhost:3000)
npm run build    # Bundle pra render headless
npx remotion render CtaCard out/cta_default.mov  # render direto
```

Config (`remotion.config.ts`) já está setado pra **ProRes 4444 + yuva444p10le**, que preserva alpha channel. O FFmpeg do video-automator vai consumir esses .mov como input com transparência.

## Próximos passos

1. Validar o Studio rodando (`npm run dev`)
2. Render do CtaCard de exemplo
3. Pipeline de pre-render em batch (script que renderiza todas as Compositions e salva em `out/`)
4. Integrar com `engine.py`: trocar o overlay CTA atual (green screen estático) pelo novo (alpha)
5. Próximas Compositions: Intro 5s por canal, Outro com inscreva-se, transição entre Ken Burns

## Trade-offs aceitos

- 2 stacks (Node + Python) — manutenção dobrada nas peças que se conectam
- Sync manual: se mudar moldura no template do automator, precisa atualizar Composition aqui
