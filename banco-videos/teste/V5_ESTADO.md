# VidMator v5 — ESTADO COMPLETO (31/07/2026)

> Doc de continuidade. A v5 está **COMPLETA (F1-F6), testada e commitada**
> (commits `91fb259..3d86d27`+). Rollback total: tag git **`v4-estavel`**.

## Isolamento (inegociável — pedido do Piter)
- v5 = SÓ arquivos novos: `*5.py` em `banco-videos/teste/` + `remotion/src/compositions/v5/`
  + composição **`Montagem5`** (registro ADITIVO no `Root.tsx`, único toque compartilhado)
  + `_render_v5base.mjs` (template; driver clona trocando "v5base" pelo job).
- v1-v4 INTOCADAS e rodáveis a qualquer momento. NÃO editar `montador.py`/`Montagem.tsx`
  pra features v5 — sempre nos forks `montador5.py`/`Montagem5.tsx`.

## Cadeia v5 (como rodar)
```
python curador5.py --job <dir> --plano <plano.json> [--workers 4] [--resume]
python rodar_producao5.py --job <dir> --plano <plano.json> --audio <mp3> --nome <job>_mont
```
`rodar_producao5` = montador5 → goldens → auditor → NVENC<5% → ÁUDIO (WAV, passada única
via `mjs --audio`) → blocos de vídeo (checkpoint em `out/_<job>/blocos/blkNN.mp4`, pula
prontos) → normalize cfr30 `-an` → concat `-c:v copy` → mux AAC → cópia protegida.
Job v5 = style_card `"estilo": "v5"` (superset do v2: audio_plan/fx/mascote/avatar herdados).

## Features (todas validadas em render no job `_job_v5teste`)
| F | O quê | Onde | Como liga |
|---|---|---|---|
| F1 | Parallax 2.5D (fundo/meio/frente, 14 movimentos, overscan, esteira infinita) | `Parallax3Scene5.tsx` + `parallax5.py` | beat `{"tipo":"parallax","props":{fundo,meio,frente,mov,tam,pos,posv,velbg,velinout}}` |
| F2 | Transições VIVAS (fade/slidePush/blurCut — saída anima por cima do entrante) + blocos | `TransOutWrap` no Montagem5 + montador5 (blocos ~2 seções, fronteira = corte seco) | automático no estilo v5 |
| F3 | 10 imageEffects CSS (grades tealOrange/duotone/silver/warm/cold/vignette + filmGrain/lightLeak/glowPulse/flashBurst) | `ImageEffects5.tsx` | montador5: grade por seção c/ rotação; lightLeak hook, glowPulse final |
| F4 | Ken Burns semântico (11 tipos) | `KenBurnsPro5.tsx` | montador5 escolhe por natureza da busca (produto/epoca/acao/paisagem/generico) |
| F5 | Karaokê word-by-word | `Karaoke5.tsx` | style_card `{"karaoke": true}` (timing proporcional por beat) |
| F6 | Footage novo | `fontes5.py` + `gate5.py` + `curador5.py` | automático no curador5 |

## F6 — lógica de footage (absorvida do dark-content-studio do amigo)
- **Queries estratificadas** (determinísticas): fiel / +close-up detail / +wide shot / keywords.
- **Pool multi-fonte** paralelo SEM download: vídeo = **Pexels (key nossa) + Coverr + Pixabay(dormant)**;
  imagem = **Openverse (CC, sem key) + Pixabay/Unsplash(dormant) + SearXNG(opcional via env)**.
- **gate5 batch**: 1 chamada Vision pro pool inteiro → cada candidato ganha `score` 0-10
  (régua "ilustraria esse tópico exato num documentário", threshold 8) + `vetos`
  (talking_head/child/watermark/burned_text/crash/brand — **veto ANULA o score**, proteção v4).
- Melhor ≥8 vence; **só o vencedor reivindica a URL** (perdedores liberados pro pool).
- Download + normaliza 1080p30 + dedup visual (`ex._e_dup_visual`) + `resolvido/bNNN.json`.
- **Fallback = resolver v4 intacto** (pexels/yt com todos os gates do executor).
- Provado: beat real "stormy ocean waves" → Coverr score 10 end-to-end.

## Decisões do Piter (31/07)
- Keys: **SÓ Pexels** (+Coverr que ele criou: no credentials do automator, `provedor: coverr`).
  Pixabay/Unsplash ADIADOS (providers dormentes, retornam [] sem key).
- **Together SEM créditos de propósito** — geração de imagem = **Nano Banana via Flow (0 créditos)**
  (`veo_driver.py --tipo imagem`, projeto Flow de imagens `0261804d-...`).
- T3 continua ancorado em footage REAL (real>TV>celular>stock, máscaras pesadas, áudio 0%);
  parallax = fatia de ILUSTRAÇÃO do mix; 100% VEO (v3-gen) = modo opcional à parte.

## Gotchas aprendidos
- Prompt de camada parallax: NUNCA "silhouette" (o modelo desenha silhueta literal);
  meio/frente = "on a pure solid white background, complete subject" → rembg recorta.
- `Easing` precisa estar no import do remotion no Montagem5 (fork não tinha).
- Coverr: mp4 = `https://cdn.coverr.co/videos/<base_filename>/1080p.mp4` (hits não trazem urls).
- montador main: nunca criar variável `corte` (sombreia a função `corte()`).
- Job de teste: `_job_v5teste` + `remotion/public/jobs/v5teste_mont/` (montagem manual).

## Pendências / próximos passos
1. **1º vídeo COMPLETO na v5** (cadeia inteira num roteiro real — estoico ou novo).
2. Diretor ainda não emite beats `parallax` (hoje só manual/montador) — integrar no
   diretor/registry quando o Piter aprovar o visual em vídeo real.
3. Karaokê: upgrade p/ word-timings reais do STT (hoje proporcional).
4. Famílias no banco (absorção do modelador do amigo, aprovada) — trocar queries_banco
   flat por 4-6 famílias com regra de estilo única (vale pro banco Pexels E pro veo_lote).
5. Tasks antigas: #22 curador_imagens, #23 animador, #24 mesa 3-funcionários.
