# DECUPAGEM VIDRUSH v2 — A LÓGICA DO EDITOR

**Amostra:** 14 vídeos, 5 nichos (bikes, caminhões, plantas, pesca, fazenda), 24/07/2026.
Fonte: `banco-videos/_vidrush_ref/` (mp4 + `_<nome>_sheets/` + `_metricas.json`).
Foco: estrutura de edição e ilustração — o nicho é irrelevante, a lógica se repete.

## 1. Ritmo (métrica dura, scene-detect)

| grupo | cortes/min | plano médio | plano mediano |
|---|---|---|---|
| bikes | 17.3-20.0 | 3.4-4.1s | 3.3-3.7s |
| caminhões | 15.1-17.6 | 4.0-4.6s | 3.9-4.1s |
| pesca | 16.1 | 4.1-4.2s | 3.8-4.1s |
| fazenda | 15.2-16.2 | 4.3-4.4s | 3.9-4.2s |
| plantas | 12.0-13.9 | 4.6-5.2s | 4.4-4.8s |

**Assinatura: ~16 cortes/min, plano de ~4s** (nicho contemplativo cai pra ~12.5/min, ~5s).
Nosso beat de 3-5s JÁ BATE com o ritmo — o gap não é ritmo, é linguagem.

## 2. A REGRA-MÃE do editor

> **Texto NUNCA aparece sozinho. Dado NUNCA troca de cena. Todo elemento gráfico
> entra POR CIMA da imagem que já está contando a história.**

Nosso Diretor faz o oposto em dado único: corta pra um card escuro full-screen
(Graf01/Graf10) e depois volta. O VidRush mantém o footage e ANOTA sobre ele.

## 3. Gatilho → escolha visual (o manual do editor)

| A narração... | O editor mostra... | Exemplos vistos |
|---|---|---|
| diz UM número/spec | **corner badge** `VALOR • UNIDADE` sobre o footage corrente | `9+1 • BEARINGS`, `17 • LBS DRAG`, `700 • BIKES RECALLED`, `6 • OUNCES` |
| diz um número DRAMÁTICO | **número gigante** centro/lateral sobre o footage (dim leve) | `1.7`, `12.3`, `10.8`, `15-20K`, `12` |
| diz PREÇO | **cifra estilizada grande** ou pill preta sobre produto | `$770 RETAIL` (vermelho), `$7Thousand`, `$450` pill, `$850 STARTING PRICE`, `$8–$18` box |
| anuncia ITEM da lista | **rank+nome+apelido de 2-3 palavras POR CIMA do footage/foto do produto** (forma A, condensed bold) OU **pill colorida com nome + caixa fina com veredito de 1 linha** (forma B) | A: `#8 KASTKING CENTRON: BACKUP WORKHORSE`, `#10 2026 DOMANE+ ALR`, `#7 MADONE SLR FLAGSHIP TRIMS` · B: `MS 170 5` + "Tempting at ≈$200, but it chokes under storm loads", `Intl. ProStar (2010-2014) 1` + "Cheap to Buy, Catastrophic to Own" |
| compara N itens com números | **bar chart em card CLARO** (branco/creme, barras coloridas) — único caso de "card de dado" | `Bearing Count (<$50 Reels)`, `Field-Tested Lifespan (yrs)` |
| lista razões/critérios | **checklist manuscrito** em card de nota (✓s) OU **painel lateral com bullets** ao lado do footage (split ~60/40) | `CENTRON: BUDGET BENCHMARK`, `WHY CEYMAR C-10 WINS`, `EGR Failure Modes`, `Compliance and Market Risks` |
| explica mecânica/anatomia | **render/foto do produto com CALLOUTS** (setas + labels) ou macro real anotado; às vezes PiP (diagrama + vídeo real juntos) | `Bolts/Chainring/Crank Arm` no render 3D, `PEAK POWER / DRY WEIGHT` no PNG recortado, `EFI SYSTEM` na macro |
| compara 2-3 produtos visualmente | **collage/prancha**: polaroids/cards com labels sobre fundo texturizado | `MS 271 50.2 CC` vs `MS 291 PREMIUM`, pranchas da fazenda 0:15/4:45/5:33 |
| fala de lugar/origem | **mapa satélite com rota amarela** + pin | fábrica em Weihai, rota Taiwan |
| cita documento/prova | **documento real em close** com tags de anotação | invoice com `0 months`/`Out of warranty`, print de loja online |
| frase de opinião forte | **frase itálica serif em pill** no canto inferior, sobre footage | "Mechanical simplicity traded for a legal nightmare" |

## 4. Regras de fundo e moldura

- Card nunca é gradiente liso: fundo ESCURO TEXTURIZADO (papel/grid fino/topográfico) ou CLARO (creme/grid caderno) — 2 famílias por vídeo.
- Collages usam "objetos colados": polaroid com borda, label vermelho/pill, leve rotação.
- Footage às vezes vira janela pequena sobre fundo texturizado (não sempre full-frame).
- Acentos: trechos em P&B, tints de cor (vermelho), transições com textura/wipe rápido.
- Caption contínua embaixo (template pesca) é opcional por nicho; fazenda/caminhões usam pouco.
- B-roll: macro de produto pesada, fábrica/oficina, ação; caminhões mistura beauty-shots gerados por IA sem disfarce.
- CTA deles = bloco com apresentador + banner/QR (não copiar o talking head; nosso equivalente é o bloco de CTA do canal).

## 5. Gap → implementação (mapeado no nosso acervo)

| # | Gap | Ação | Status acervo |
|---|---|---|---|
| G1 | Dado único vira card escuro (nosso) em vez de overlay no footage | Diretor/montador: dado único ⇒ SEMPRE overlay (Ovl10/Graf14-16 c/ bg nítido); Graf01/02/10 full só sem footage disponível | temos os Ovl/Graf overlay — inverter preferência |
| G2 | Badge `VALOR • UNIDADE` | novo Ovl11_SpecBadge (canto, formato `9+1 • BEARINGS`) | novo (fácil) |
| G3 | Número gigante sobre footage | novo Ovl12_GiantStat (número 200px+ semi-transparente, sub-linha) | novo (fácil) |
| G4 | Preço estilizado | novo Ovl13_PriceTag (cifra grande / pill preta) | novo (fácil) |
| G5 | Anúncio forma A: rank+nome sobre foto do produto | ProductAnnounce: usa a foto do R-111 + texto condensed por cima (não foto limpa) | evoluir R-111 |
| G6 | Anúncio forma B: pill + veredito 1 linha | Ovl14_PillVerdict (pill colorida nome + caixa fina one-liner) | novo (fácil) |
| G7 | Checklist manuscrito / painel lateral | Soc/Txt novos: NoteChecklist + SidePanelList (split footage+painel) | novo (médio) |
| G8 | Gráfico multi-valor em card CLARO | variante clara dos Graf05/07/12 (fundo creme, barras coloridas) | variante (fácil) |
| G9 | Callouts em produto | ProductCallouts (imagem + 2-4 setas/labels) | novo (médio) |
| G10 | Collage/prancha comparativa | CollageCompare (2-3 polaroids + labels, fundo texturizado) | novo (médio) |
| G11 | Fundo texturizado nos cards | trocar gradiente liso por textura papel/grid nos cards e T3 | Montagem/CSS (fácil) |
| G12 | Frase editorial itálica | Ovl15_EditorialQuote (itálica serif em pill inferior) | novo (fácil) |
| G13 | Caption contínua opcional | trilha de caption por style_card (`captions: true`) | Montagem (médio) |
| G14 | Acentos P&B/tint + wipe texturizado | filtros por beat (montador sorteia 1-2 por seção) + transição | Montagem (médio) |

**Prioridade sugerida (impacto × esforço):** G1 (só regra!) → G2/G3/G4/G6 (overlays novos fáceis, matam a "cara de card genérico") → G5 (anúncio nota 10) → G8/G11 → G7/G9/G10 → G12/G13/G14.

## 6. O que JÁ estamos fazendo igual

- Ritmo de corte (~4s/plano) ✓
- Mapa satélite com rota ✓ (Director-integrado)
- Ilustração técnica de manual (R-105 web) ✓
- Produto exato no anúncio (R-111 — falta só o TEXTO por cima, G5) ✓
- Charts para comparação multi-valor ✓ (falta versão clara, G8)
- Mix footage macro/fábrica/ação via cascata ✓
