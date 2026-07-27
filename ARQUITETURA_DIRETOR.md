# Arquitetura do DIRETOR / Beat-Planner — o cérebro do VidMator

O Diretor transforma **roteiro → vídeo montado**, decidindo POR BEAT o que mostrar e como. Calibrado pela decupagem VidRush (`DECUPAGEM_VIDRUSH.md`). Resolve a preocupação central: *"e se não achar footage ideal?"* → **ele ilustra** (nunca força footage errado, nunca deixa vazio).

---

## VISÃO GERAL (fluxo)

```
Roteiro (texto) + Narração (áudio)
        │
        ▼
[STAGE 0] Narração → segments com timestamps  (STT: já temos)
        │
        ▼
[STAGE 1] SECTIONS  — LLM divide em capítulos + color-wash por seção
        │
        ▼
[STAGE 2] BEAT PLAN — LLM: cada segmento → beats c/ estratégia/tipo/dados/fallback  ← O CÉREBRO
        │
        ▼
[STAGE 3] RESOLUÇÃO — por beat (paralelo):
          footage → resolver T2→T3→T1 + Gate Vision → achou? usa : FALLBACK→ilustra
          ilustração → gera IA (seedream) / componente técnico + Gate
          animação → componente do acervo + preenche dados
          stock → Pexels + Gate
          (cada asset carrega o tier real → StandardClip aplica máscara)
        │
        ▼
[STAGE 4] MONTAGEM — Remotion: beats+assets+tratamento sincronizados c/ narração + transições
        │
        ▼
      Vídeo
```

## STAGE 0 — Narração + timestamps  *(já temos)*
STT (Grok/Whisper) → `segments[]` com `{start, end, text}`. É a GRADE temporal: cada beat se ancora aqui.

## STAGE 1 — SECTIONS (pass estrutural, LLM)
Divide o roteiro nas seções do modelo VidRush (cold-open, framework, escala, frota, casos, evolução, vulnerabilidades, conclusão). Por seção: título (→ title card), **color-wash** (teal/amarelo/vermelho/dourado), faixa de tempo.

```json
{ "i": 4, "titulo": "Fleet & Humanitarian", "t_ini": 230.0, "t_fim": 288.0,
  "wash": "teal", "title_card": true }
```

## STAGE 2 — BEAT PLAN (o cérebro, LLM)
Para cada segmento de narração cria 1+ beats. **Classifica a estratégia** (as 5+1 regras da VidRush), **extrai o ilustrável**, define tipo + fallback + tratamento.

### Schema do BEAT
```json
{
  "i": 58,
  "secao": 4,
  "t_ini": 288.0, "t_fim": 292.5, "dur": 4.5,
  "texto": "WFP logs show these trucks maintain 92 percent operational uptime vs 84 percent...",

  "estrategia": "dado",          // literal | entidade | dado | peca | abstrato | atmosferico
  "tipo": "animacao",            // footage_video | footage_imagem | ilustracao | animacao | stock
  "componente": "BarChartComparison",   // se animacao/ilustracao
  "dados": { "left_label": "Hilux", "left": 92, "right_label": "Outros", "right": 84, "unit": "%" },
  "busca": null,                 // se footage: query
  "strict": false,               // exige o modelo exato? (Tipo A)

  "entidades": { "numero": "92%", "org": "WFP", "lugar": "Horn of Africa" },
  "tier_teto": "web",            // herda do canal
  "tratamento": { "frame": "framed_grid", "overlays": ["particulas"], "wash": "teal" },

  "fallback": [                  // 👈 O CORAÇÃO — se o primário falhar, desce a cadeia
    "animacao:NumberCountOverlay",
    "atmosferico"
  ]
}
```

### Mapa estratégia → tipo primário → fallback
| Estratégia (regra VidRush) | Gatilho no roteiro | Tipo primário | Fallback |
|---|---|---|---|
| **literal** | ação/objeto filmável (teste, motor, off-road) | `footage_video` | → ilustração do assunto → atmosférico |
| **entidade** | lugar/pessoa/org nomeada | `animacao` (MapRoute/globo, name label, LogoFlagGrid) | → card de texto |
| **dado** | número/estatística | `animacao` (chart/gauge) | → NumberCountOverlay |
| **peca** | componente/engenharia | `ilustracao` (blueprint/cutaway/diagrama) | → footage de peça → foto |
| **abstrato** | conceito ("engenheiros decidiram") | `stock` (Pexels) | → texto/atmosférico |
| **atmosferico** | respiro/transição | `footage`/`stock` (paisagem) | → color plate |

## STAGE 3 — RESOLUÇÃO (por beat, paralelo) — reusa TUDO que já construímos
1. **footage** → `resolver_cascata` (T2→T3→T1, dentro do teto) → baixa candidato → **Gate Vision** (relevância do beat + child + talking-head + watermark→crop). Achou clean? usa. **Reprovou/não achou após N tentativas → cai pro `fallback[0]`** (tipicamente ilustração/animação). **É aqui que "footage errado" nunca acontece.**
2. **ilustração** → gera por IA (ai33 seedream `/v1i` ou Together) com prompt derivado do beat (ex.: *"exploded technical diagram of a Toyota Hilux leaf spring, service-manual style, white background, labeled"*) → Gate Vision. *(Preenche nosso GAP dos 20% de ilustração técnica.)*
3. **animação** → pega o componente do acervo (das 54) e preenche com `dados`. Sem sourcing, sem risco.
4. **stock** → Pexels + Gate.
- Cada asset final carrega o **tier real** → `StandardClip` aplica a máscara do tier (frame + N overlays + wash da seção + crop).

## STAGE 4 — MONTAGEM (Remotion)
`beats[]` + assets + tratamentos → timeline sincronizada aos timestamps da narração. Transições entre beats (do acervo do amigo). Legendas opcionais. Mix de áudio (narração + trilha + SFX). = o motor Remotino que já temos (BrollTest/Director), escalado p/ 200+ beats.

---

## POR QUE ISSO RESOLVE A PARIDADE
- **Roteiro foda + footage certo:** o beat-planner extrai o ilustrável e o resolver+gate acham o footage específico. **Se não achar, o fallback ILUSTRA** — exatamente como a VidRush faz com "Battle of Fada 1986" (vira mapa+card, não footage forçado).
- **Reusa tudo que construímos:** tiers, gate Vision, 54 animações, máscaras, resolver — o Diretor é a cola.
- **Fecha os 2 buracos:** o cérebro (este doc) + a ilustração técnica (Stage 3.2 via IA).

## ORDEM DE CONSTRUÇÃO
1. **`diretor.py` — Stage 1+2** (sections + beat plan via LLM) → produz `plano_beats.json`. **Testável isolado** (rodar no roteiro da Hilux e comparar com a decupagem real).
2. **Stage 3 wiring** — plugar resolver+gate+acervo por tipo, com a cadeia de fallback.
3. **Ilustração IA** (Stage 3.2) — gerador de diagrama técnico + gate.
4. **Stage 4** — montador Remotion dirigido pelo `plano_beats.json`.

> Validação de ouro: rodar o Stage 1+2 no roteiro REAL da Hilux (temos em `transcript.txt`) e comparar o plano de beats gerado com a decupagem real (`DECUPAGEM_VIDRUSH.md`). Se o Diretor "reinventar" o vídeo VidRush a partir do roteiro, está calibrado.
