# ACERVO VidMator — SPEC de construção de componentes (LER ANTES)

Você vai criar componentes **Remotion** (React) que replicam animações do VidRush, como **containers niche-agnostic** (props com defaults). Cada um é um `.tsx` em `remotion/src/compositions/`.

## PADRÃO (copie a estrutura destes 2 que já existem e funcionam)
Leia `src/compositions/StatReveal.tsx` e `src/compositions/VintageAngled.tsx` como REFERÊNCIA de estilo/estrutura. Regras:
- `import { AbsoluteFill, Img, interpolate, spring, useCurrentFrame, useVideoConfig, staticFile, Sequence, Easing } from "remotion";`
- Export **NOMEADO**: `export const NomeDoComponente: React.FC<{ ...props }> = ({ ...comDefaults }) => { ... }`
- **TODAS as props têm default** (o componente renderiza sozinho sem props). Props = os CAMPOS que listei por template.
- Canvas 1920×1080. Use `useVideoConfig()` p/ width/height/fps/durationInFrames.
- Entrada com `spring`/`interpolate` sobre `useCurrentFrame()` (pop/fade/scale ~18-26 frames). Números/barras animam via `interpolate(frame,...)`.
- Imagens: `<Img src={staticFile(prop)} .../>`. Sem libs externas (nada de recharts/d3) — charts = SVG ou divs.
- TypeScript válido (sem `any` solto; tipa as props). SEM anotações que quebrem (o projeto compila com esbuild/Remotion).

## DESIGN (tokens — use inline, cohesão entre todos)
- Fundo padrão: quase-preto `#0a0b0f`; variação "grid" = `#0a0b0f` + grade sutil (linhas `rgba(255,255,255,0.05)` a cada ~64px via `repeating-linear-gradient`).
- Accent: prop `accent` default **`"#f59e0b"`** (âmbar). Use p/ destaques/glow.
- Texto: branco `#ffffff`; secundário `#9aa4b2`; dim `#5b6472`.
- Fontes (constantes string): DISPLAY `"'Archivo Black','Impact','Arial Black',sans-serif"` · MONO/typewriter `"'American Typewriter','Courier New',monospace"` · SANS `"'Inter','Segoe UI',sans-serif"`.
- Card/painel: `borderRadius: 16`, fundo `#14161c`, borda `1px solid rgba(255,255,255,0.08)`, `boxShadow: "0 20px 60px rgba(0,0,0,0.6)"`.
- Moldura de imagem: cantos arredondados (12-16), leve borda branca 3-4px OU sem, drop-shadow. Recorte transparente = usar direto (PNG já tem alpha).
- Glow no accent: `textShadow`/`boxShadow` com o accent.

## ASSETS DE AMOSTRA (para defaultProps — use estes caminhos que EXISTEM)
- Retrato/pessoa (PNG recortado, alpha): `"test/people/pessoa_0.png"` (tem pessoa_0..5, darwin.png)
- Produto (foto): `"jobs/motos2/clips/moto0.jpg"` (e moto20.jpg)
- Paisagem/cena: `"test/clips/scene_10.jpg"` (scene_0,1,10,100,101,102...)
- Imagem genérica: `"test/imagens/img_0_0.jpg"`
- Grão (overlay): `"grain.png"` · Mapa: `"test/map_img.jpg"`
Para arrays de imagens, varie entre esses.

## MECÂNICA por template
Cada template abaixo tem: **nome do componente** · **props (campos)** · **o que faz**. Replique a MECÂNICA (entrada sequencial, barra enchendo, número contando, etc.). Se o layout exato for ambíguo, faça uma versão limpa e profissional coerente com o nome.

## SAÍDA (o que você entrega)
1. Escreva cada componente em `src/compositions/<Nome>.tsx` (Write). **NÃO edite `Root.tsx`** (o orquestrador registra). **NÃO rode build.**
2. No fim, retorne um JSON array com: `{ "name": "...", "file": "src/compositions/X.tsx", "durationInFrames": N, "defaultOk": true }` por componente (durationInFrames ~90-150). Nada de prosa longa — só o JSON + 1 linha de status.
