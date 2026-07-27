# VidMator — Acervo & Formatos (Design + Backlog de referências VidRush)

> Documento-mestre. Junta TODAS as ideias/referências que o Piter vem passando (estudo do VidRush + visão)
> pra organizarmos depois. **Vou anexando cada nova referência aqui.** Regras detalhadas em `REGRAS_NICHOS.md`.
> Última atualização: 2026-07-15.

---

## 1. VISÃO (Piter + amigo)
- **VidMator dividido por FORMATO, não por nicho.** O formato é o que o template do canal escolhe.
- Base = um **POOL de opções de edição por CATEGORIA** (imagens/vídeos/personagens/modelos/transições/overlays/SFX). **Cada opção tem uma PROBABILIDADE** de aparecer, dependente do formato.
- Um **FORMATO** = composição *probabilística* dessas opções que se juntam de forma lógica → vídeo ultra-dinâmico. Quanto mais opções no pool, mais dinâmico.
- **Arquitetura de CONTAINER plugável:** cada estilo/opção é um "plug"; adicionar um novo (inclusive modelo futuro) NÃO quebra código — o sistema reconhece e disponibiliza.
- Canal/nicho → aponta pra um formato → o Director sorteia por cena. Ex.: formato *documentário* serve doc + curiosidades; *estoicismo* serve psicologia + filosofia; *top-rank* serve vários nichos.
- **Aba VidMator = "CapCut interno":** navegar o acervo com **preview em GIF** por categoria e montar formatos.
- **Referência = VidRush:** assinar o plano simples, ver o pool deles, trazer pro nosso + criar variações próprias.

### 1.1 ARQUITETURA EM 3 CAMADAS (confirmada pelo Piter, 2026-07-15)
1. **ACERVO (criado)** — TODAS as ~199 animações/containers **construídas e parametrizadas** (data-driven). Adaptar a cada uso = só **mudar os dados/props**. Acervo vasto, criado e disponível.
2. **FORMATO / "modelo geral" (config)** — define **QUAIS** opções do acervo entram e com que **PROBABILIDADE** (o pool por formato/nicho).
3. **DIRETOR (runtime)** — **escolhe por CONTEXTO**, dentro do que o formato permite, cena a cena.
⇒ **Construir o acervo é investimento único**; formatos + escolha ficam por cima, baratos. Cada container nasce **niche-agnostic por props** (como `StatReveal`/`VintageAngled`) — é só replicar o padrão pras 199.

---

## 1.5 OS 2 PILARES DO PODER (VidRush) — e nossa prioridade
O que faz o VidRush ser potência (Piter, 2026-07-15):
1. **ANIMAÇÕES** — a parte **MAIS COMPLEXA** do editor e o **maior diferencial**. É onde nasce o dinamismo.
   ⇒ **TOP PRIORIDADE** de construção: Transições cena→cena (§4.5, ~26) + Animações Enter/Exit por elemento
   (§4.4, 14) + o **sistema enter+exit sorteado por probabilidade** do formato. É o maior volume E o maior salto de qualidade.
2. **FOOTAGE da internet inteira + COERÊNCIA** — buscar footage em QUALQUER fonte **e** montar um vídeo que
   faz sentido com a fala. ⇒ nosso lado: tiers de fonte (§4.2, incl. Web crawling) + `resolver_cascata`; e a
   **COERÊNCIA** = TIPO A/produto-lock + regra anti-palavra-literal + gates Vision + auto-QA (§4.3).
   *"Coerência" = o footage casa com o ASSUNTO, não com a palavra solta.*

**Ordem de ataque sugerida das animações:** mecânicas primeiro (wipes/iris/clock via `clip-path`, flips via
`rotate3d`, luz via overlay/flash) → depois as orgânicas (paper tear/cut, ink, brush — precisam de máscara/textura).

---

## 2. ABA VidMator (estado atual)
- ✅ No ar em `/v2/vidmator` (React frontend2 → deploy via scp; ver `project_automator_infra` na memória).
- Sub-abas por categoria: **Imagens · Vídeos · Personagens · Modelos · Transições · Overlays · SFX · Formatos**.
- Cada opção = card com **slot de preview 16:9** (GIF entra na Fase 2).
- v1 = leitura; editar/persistir de volta (presets etc.) = etapa futura.

---

## 3. ACERVO POR CATEGORIA (o que já existe no Director + o que falta)
| Categoria | Já temos | Novos / a fazer |
|---|---|---|
| **Imagens** | 8 apresentações (`PresentationGallery`: Lupa/Spotlight/Split/Grid/Polaroid/Film-VHS/Parallax/Reveal) + Ken Burns | ✅ **VintageAngled** (feito) |
| **Dados/Infográficos** | `CardsStructure` / `DataViz` (timeline, gráficos) | ✅ **StatReveal** (feito); restilizar timeline p/ look Harley; **SpecCard** (folha técnica) |
| **Vídeos** | Loop mudo (OffthreadVideo), `ArchiveClip`, `EditMask` (Standard License) | **StandardClip** (moldura+máscaras+crop) |
| **Personagens** | `PersonCard`, `Mascot` (Galo) | **Modelos** = a definir (2D/palitinho/raccoon) |
| **Transições** (cena A→B) | Crossfade, Slide-h, WhipPan, SmoothZoom (~4) | **~20 novas** (ver 4.5) |
| **Animações** (enter/exit do elemento) | fade/slide/scale/zoom/glitch/filmburn | **flip/float/gaussian-blur** + formalizar bounce/snap/swipe (ver 4.4) |
| **Overlays** | MoodOverlay (red/cold/CRT/glitch/TVstatic), LightLeak, LightRays, Aurora, Particles, Stars, Period | — |
| **SFX** | whoosh, riser, glitch, typing, paper, click, cta_ding (`SfxSampler`) | — |

**Componentes vivem em:** `remotion/src/compositions/*.tsx` + registrados no `remotion/src/Root.tsx` (catálogo previewável).
**Preview de container:** `remotion/render_still.mjs` (renderStill 1 frame, bundle isolado).

---

## 4. REFERÊNCIAS VidRush CAPTURADAS

### 4.1 Formato "Harley/VidRush" — 5 padrões de IMAGEM/elemento dinâmico
1. **Foto antiga P&B**, zoom + **rotação leve (15–20°)** → 🆕 `VintageAngled` ✅ **feito**
2. **Imagem rica do produto** (motor, não-stock) → 🎯 princípio **TIPO A** (produto-locked). Bônus: "spec sheet" (esquema técnico + specs numa folha inclinada) = candidato a **`SpecCard`**
3. **Stat "76% MORE HORSEPOWER"** — degradê âmbar/preto, **fonte typewriter**, número entra com **zoom-out** sincronizado à fala → 🆕 `StatReveal` ✅ **feito** (niche-agnostic: value/label/sub/accent)
4. **Infográfico de etapas/timeline** ("Four Engines, Four Decades") → ✅ temos (`CardsStructure`/`DataViz`) — **restilizar** p/ typewriter+âmbar
5. **Foto com transição + leve movimento** (não estática) → ✅ temos base (Polaroid/Film/Parallax + Ken Burns)

**DNA visual do formato Harley:** paleta **âmbar/laranja sobre preto**, **fonte typewriter**, tudo entrando com **movimento sincronizado ao roteiro**.

### 4.2 Compliance / Fontes (preset escolhido logo no início — MUITO importante)
3 tiers por risco (formaliza a decisão CC-vs-qualquer-licença que fizemos na mão no motos):
| Tier VidRush | Risco | Nossa fonte | Regra |
|---|---|---|---|
| Commercial Stock (Storyblocks) | baixo | **Pexels** (free) | livre |
| CC & Public Domain | médio | **Commons + Pexels + YT só-CC** | atribuição quando exigida — **DEFAULT** |
| General Web Crawling | alto | **YT qualquer licença (áudio 0%) + web** | você assume risco → **obriga Máscaras/EditMask** |
- Vira knob **`fonte_compliance`** (`stock`|`cc_pd`|`web`) por canal/formato → liga/desliga níveis do `resolver_cascata` + gate do `clipar_youtube`. Tier Web ⇒ força `StandardClip`.

### 4.3 Pipeline criativa + QA (sequência do VidRush)
`Preparing voiceover → Creating voiceover → Syncing audio → **Planning visuals** → **Double-checking content** → **Making visuals** → Finalizing`
- ✅ Temos tudo MENOS o **"Double-checking content"**.
- 🆕 **`verificar.py` = passo de auto-QA:** o Director **assiste o próprio MP4** (via `decupar.py` + Vision) e roda a **Checklist** ANTES de publicar (assunto/modelo casa? marca-d'água? SFX estourado? CTA? nome/número? clipe repetido?). Foi a falta disso que deixou passar Suzuki no bloco da Ninja + marca-d'água + SFX no motos.
- **Plan ≠ Render** (passos separados) valida o desenho do nosso **motor** (Fase 3): o formato planeja a composição/probabilidades, depois renderiza.
- VidRush é **beeem lento** (nuvem, geração por cena). Nosso **local + cache + Remotion** é vantagem de velocidade — copiamos a *disciplina de QA*, não a lentidão.

### 4.4 Animações ENTER / EXIT (por elemento/slide) — VidRush tem 14
`None · Fade · Slide · Scale · Bounce · Flip · Zoom · Slide · Snap · Glitch · Swipe · Float · Film Burn · Gaussian Blur`
- ✅ temos: fade/slide/scale/zoom/glitch/film-burn · ⚠️ parciais: bounce/snap/swipe · 🆕 novos: **flip, float, gaussian-blur**
- **Upgrade estrutural:** cada elemento tem **`enter` + `exit`** próprios (paleta), sorteados por probabilidade do formato. Hoje nosso `transicao` só faz entrada, quase sempre crossfade.

### 4.5 TRANSIÇÕES cena→cena — VidRush tem ~26
`Zoom · Fade · Wipe Up/Right/Left/Down · Clock Wipe · Iris · Slide Up/Down/Left/Right · Sliding Pan · Whip Pan · Flip Vertical/Horizontal/Up/Left · Paper Tear · Paper Cut · Ink · Brush · Lens Flare · Fast Light Flick · Film Burn · Glitch`
- ✅ temos ~4 (Crossfade/Slide-h/WhipPan/SmoothZoom) + glitch/filmburn como efeito.
- 🆕 **~20 novas** — mecânicas no Remotino: wipes/iris/clock = `clip-path`; flips = `rotate3d`; luz = overlay/flash; **orgânicas (paper tear/cut, ink, brush) precisam de máscara/textura** (deixar por último).

### 4.6 SCENE TEMPLATES (animações COMPOSTAS, data-driven) — categorizadas por USO
> Classe **diferente** das transições/enter-exit (atômicas): são **cenas inteiras montáveis**, com **campos
> editáveis** (conteúdo) e **entrada sequencial/simulada** (elementos aparecem 1 a 1 como se fosse ao vivo).
> VidRush organiza por **CATEGORIA de uso** (Reaction / Product Review / Demonstration / …) → mapeia direto no
> nosso conceito de **FORMATO/nicho**. **VidRush tem ~199 animações no total** ⇒ catalogar incremental e
> **priorizar por relevância pros nossos nichos** (NÃO construir as 199).

| Template | Categoria | O que faz | Campos editáveis | Assets | Status |
|---|---|---|---|---|---|
| **YouTube Comments** | Reaction | cards de comentário entram 1 a 1 (slide/fade) | username, texto, likes × N | — | 🆕 novo (fácil: cards + entrada sequencial) |
| **Transparent Image Comparison** | Product Review | 2 produtos (esq/dir) PNG transparente sobre **fundo de papel amassado ANIMADO (gif)** + centro "BETTER THAN?"/seta; entra up/down slide | produto esq, produto dir, text line 1/2, direção da seta, texto-ou-ícone | PNG transparente (rembg) + textura papel animada | 🆕 novo — **ótimo p/ automotivo/produto** |
| **Instagram Conversation** | Demonstration | chat/DM entra com zoom-in; mensagens aparecem 1 a 1 como conversa real | avatar, nome, msgs incoming/outgoing × N | avatar | 🆕 novo (bom p/ demo/tech) |
| **Rival Versus Split** | Documentary | 2 cabeças recortadas (PNG transparente P&B) + labels + linha vermelha diagonal de "versus" sobre grid | img esq/dir, label esq/dir | **recorte transparente (rembg)** | 🆕 — ótimo p/ doc/geopolítica/comparação |
| **Dual Impact Sentence** | Documentary | 2 frases de impacto aparecem em sequência sobre gradiente escuro | frase 1, frase 2, duração | — | 🆕 (variante de texto; temos WordByWordReveal/Typewriter) |
| **Video to Image Overlay** | Documentary | imagem central (borda rasgada) desce em slide-down sobre VÍDEO de fundo com chiado/ruído | imagem, vídeo de fundo | moldura rasgada + **EditMask(noise)** | 🆕 (combina peças que já temos) |
| **Two Transparent Image Overlay** | Tutorials | 2 pessoas recortadas entram em slide + blur de fundo; fundo = imagem OU vídeo | img esq/dir, fundo (img/vídeo) | **recorte transparente (rembg)** | 🆕 |
| **Three Image Reveal** | Documentary | começa com a foto do MEIO em tela cheia e dá zoom-out até revelar as 3 emolduradas | 3 image URLs | — | 🆕 |
| **Teasing What's Next** | Story Time | listicle: imagens emolduradas + números de posição (#1..N); anima do #N de volta ao #1 (teaser) | imagens × N, image count, números de posição | moldura + tag de número | 🆕 — ótimo p/ top-N/listicle |
| **YouTube CTA** | CTA | barra like/dislike/subscribe/bell | — | — | ✅ **JÁ TEMOS** (`YtCta`/`SubscribeBellPulse`/`SubscribeMinimal`) |
| **Split Screen (labels)** | Comparison/Doc | split-screen de 2 imagens com labels + posição do texto configurável | label esq/dir, posição texto, img esq/dir | — | 🆕 (variante de comparação) |
| **Price Call Out** | Product/Stat | valor + moeda + descritor num card sobre a cena | price, currency, descriptor | — | 🆕 = **variante do `StatReveal`** (só + moeda) |
| **Layered Reveal (transitioning)** | Documentary | objeto principal + textos (main/sub/1º/2º) + cutouts esq/dir revelam em camadas | main obj, textos, obj esq/dir | **recorte transparente (rembg)** | 🆕 |
| **Image Sequence Slideshow** | Slideshow | imagens em frames arredondados deslizando sobre **fundo de papel quadriculado branco**; Enter/Exit por elemento + toggle noise | imagens × N, animação enter/exit, panel-wave | — | ⚠️ combinatório — novidade = **fundo grid-paper + panel-wave noise** |
| **Double Image Annotation** | Comparison/Doc | 2 retratos emoldurados + títulos, sobre **fundo cinza com silhueta suave** | img esq/dir, título esq/dir | — | ⚠️ variante dual-portrait — novidade = **fundo cinza-silhueta** |
| **Percentage Bar Chart** | Data/Stat | barra vertical enche até X% + título + número % grande (glow âmbar), fundo grid | título, percentual, (cor?) *[inferido]* | — | 🆕 data-viz (parente de `StatReveal`/`DataViz`) |
| **Paper Moving Transparent Object** | Documentary | objeto recortado sobre **fundo de papel em movimento** | objeto (img), fundo *[inferido]* | recorte (rembg) + paper-bg | 🆕 (usa primitivas paper-bg + cutout) |

> **Input da decupagem (Piter, 2026-07-16):** foco na **trilha de ANIMAÇÕES** (nome do container) **+ painel Content** (Piter achou como mostrar) **+ preview**. **IGNORAR** narração/legenda e footage (independentes, não têm relação com a animação). ⇒ confirmo **nome + CAMPOS customizáveis exatos (= props) + mecânica + timing** — catálogo 100% confirmado, sem inferir. Dica: Content mostrando os campos da animação selecionada + nomes da trilha inteiros.
>
> **Como decupar (validado no LOTE 1):** `python decupar.py "<video>"` → contact-sheets (mapa, 480px) + `frames/`. O texto no sheet é pequeno → puxar **frames FULL-RES** (`ffmpeg -ss <t> -i <video> -frames:v 1`) nos timecodes: aí o **Content (campos)** E os **nomes da trilha** ficam legíveis. A animação **selecionada = borda branca** no container (casa nome↔Content↔preview). A trilha mostra vários nomes por frame ⇒ **poucos frames full-res = todos os nomes**.

**DECUPAGEM — LOTE 1** (`2026-07-16 15-56-17.mp4`, 11min, tema Hilux) — **~37 templates, CAMPOS EXATOS** lidos (full-res, 49 frames):

*DADOS / CHARTS / NÚMEROS*
- `Percentage Bar Chart Animation` — **Title Text · Bottom Text · Percentage Value** (barra vertical enche até X%)
- `Pie Chart Animation` — **Title · Number of Slices · Equal Distribution(toggle) · Highlighted Slice Value · Slice 1-5 Value · Highlight Label**
- `Bar Chart Comparison` — **Chart Title · Company Logo** (+ título/valores; 2 barras, ex. Hilux 92% vs Other 84%)
- `Object + Dual Stat` — **Object Image(cutout) · Left Big Number · Left Label · Right Big Number · Right Label** (ex. 60 TONS / 9.4 METERS)
- `Price Call Out` — **Price Amount · Currency · Descriptor Text** · `Number Count Overlay` · `One Word Callout Overlay`

*MAPAS / GEO*
- `Multi Country Outline And Text Animation` — **Countries to Highlight[+Add] · Country Statistics/Values[+Add]**
- `City/Satellite Map (Draw Path)` — **Animation Style(Draw Path) · Animation Direction · Camera Effect(Subtle 3D)** + label local ("Fada, Chad 1986")
- `Map Route (Draw Path)` — **Start/End Point Name · Start/End Latitude · Start/End Longitude** (Tehran→Dubai)

*TEXTO*
- `Sentence Highlight Text Overlay` — **Paragraphs[+Add] · Highlights[+Add]** (destaca frases sequencialmente)
- `Text Reveal` — **Main Text · Secondary Text · Final Label** · `Title + Description` — **Title · Description**
- `Quote Card` — **Quote Text · Name · Title** · `Chapter Title` — **Title · Chapter Number · Subtitle**
- `Display Text` (Display Text) · `Date/Location Overlay` (**Overlay Text**) · `Bullet Point Overlay` · `Caption Text Overlay` · `Article Zoom`

*PESSOAS / PERSONAGEM*
- `Character Card` — **Character Image · Title · Subtitle** · `Character + Keyword` — **Character Image · Keyword**
- `Object + Title` — **Object Image · Title** · `Node/Hierarchy` — **Top Node Image URL · Bottom Node 1/2/3 Image URL**
- `Instagram Conversation` — **Incoming/Outgoing Message 1-3**

*IMAGEM / COMPARAÇÃO / REVEAL*
- `Two Image Comparison` — **Title Text · Left/Right Image** · `Three Image Reveal` — **First/Second/Third Image** · `Four Image Slideshow` — **First-Fourth Image**
- `Multi-Image Cut Text (Winners)` — **First-Fourth Image URL + Title (cada)** (2-0 / Brazil Win / Portugal / Argentina)
- `Dual Image on Grid` — **Left Label · Right Label** (2 imgs no papel quadriculado) · `Icon Grid (Virtuous Circle)` — **Main Text · Top/Right/Bottom/Left Icon**
- `Icon + Labels` — **Icon 1-3 · Labels[+Add]** · `4-Image Caption Grid` — **Show Text(toggle) · First-Fourth Image Caption** · `5-Text Listicle` — **Text (+5 imgs FIRST-FIFTH)**
- `Before/After Arrow Image` — **Before Image · After Image** · `Image And Text Annotation` (imagem + labels ancorados: Ladder-Frame/Thick Gusset/Weld Beads)
- `Website Screenshot Reveal` — **website URL (public, no paywall/CAPTCHA)** → túnel/perspectiva
- Família callout: `Image Callout` · `Image Highlight Overlay` · `Callout Overlay` · `Arrow Animation Graphic` · `(Transparent) Image Arc Lines` · `Paper Moving Transparent Object`

*CONTROLE:* `Enter/Exit` por elemento (Settings → Panel wave / Sound Volume + as 14 animações) — aplicável a qualquer mídia.

**~37 templates com campos exatos.** Recorrências que confirmam as primitivas: **recorte/Object Image (rembg) em ~8** · charts/números em ~6 · mapas Draw Path em 3 · overlays texto/callout em ~10. ⇒ compositor + primitivas cobre a grande maioria. **Muitos caem nos nossos nichos:** Multi Country/Map Route/Satellite (geopolítica·doc) · Image Annotation/Object Dual Stat (produto·tech) · Pie/Bar/Percentage/Number (stats) · Character Card/Quote (história) · Winners (esporte).

**DECUPAGEM — LOTE 2** (`2026-07-16 19-33-00.mp4`, 8min) — **~14 NOVOS** (campos exatos, dedup vs Lote 1):
- *Charts/Dados:* `Line Chart` — **Number of Lines · Data Points · Chart Title · X Axis Type · Start/End Value · Y Axis Type · Chart Pattern** · `Growing Bar Chart` — **Title · Final Bar Year · Final Bar Text** · `Circle Percent (Donut)` — **Title Content · Circle Percent** · `Stock Chart Animation` · `Poll/Survey Bar` — **Question · Highlighted Keyword · Primary/Secondary segment label · Primary Percentage · Source Text**
- *Pessoas/História:* `Subject Title Card` — **First/Second Subject Title · SubTitle** · `Country + Character Map` — **Country Name · Name · Title · Character Image** (Elizabeth I + mapa UK) · **`Detective/Evidence Board`** — Left/Right Image + Titles (corkboard + barbante vermelho + pins) → **TRUE CRIME** 🔥
- *Mapa/Geo:* `Satellite Location Pin` — **Latitude · Longitude · Location Name · Location Sub Title** · `Region/Location Text` — **Country Name · Region Name · Text**
- *Imagem/outros:* `Split-screen Comparison` — **Left/Right Image** (+ `Rotating Split Screen`) · `Circle Highlight (Draw Circle)` — círculo vermelho + label na parte · `Article/News Card` — **Article Image · Article Text · Highlight Text · Image Caption** · `Logo/Flag Grid` — até 6 itens (Flag Mode/Logo Domain/Image/Text) · `Single Sentence Text Slide`
- *Repetem do L1:* Chapter Title · Image And Text Annotation · Character Card · background media.

**Acumulado L1+L2 ≈ 50 templates com campos exatos.** Novos destaques por nicho: **Detective Board** (true crime) · suite de charts **Line/Growing Bar/Circle/Stock + Poll** (dados/opinião) · **Country+Character Map / Satellite Pin** (geopolítica·história) · **Article Card** (doc) · **Circle Highlight** (produto·tech).

**Insight (reforçado):** categorias de uso agora = Reaction · Product Review · Demonstration · **Documentary** · Tutorials · **Story Time** · CTA. **Nem tudo é novo:** `YouTube CTA` **já temos**; `Price Call Out` = `StatReveal` + moeda; `Split Screen` = layout de comparação já mapeado → *isso confirma a tese combinatorial:* dos 13 templates, quase todos reduzem a `[cutout/imagem-emoldurada] + [label/texto/número] + [entrada slide/zoom/blur] + [fundo grid/blur/vídeo-ruído] + [card/moeda opcional]`. **Primitiva recorrente: RECORTE TRANSPARENTE (PNG alpha) — já temos via `rembg`.** ⇒ construir **as primitivas + um compositor** resolve dezenas por recombinação; poucos são realmente únicos. *`PersonCard`/`CardsStructure`/`ProductCTA`/`StatReveal`/`YtCta` já são a base.*

### 4.7 PRIMITIVAS DO COMPOSITOR (o alvo REAL de construção)
> Os scene templates se decompõem nestas peças. Construir **as primitivas + um compositor (layout+slots)** cobre a maioria dos ~199 por recombinação. Cada template = `layout` + `slots` (preenchidos com primitivas) + `entrada por elemento` + `fundo`.

- **Cutouts / imagens:** recorte transparente PNG (**rembg — já temos**) · imagem emoldurada (frame arredondado · rasgado · grid amarelo · polaroid) · retrato com título
- **Texto:** label com underline · frase de impacto (sequencial) · número/posição (#N, listicle) · **stat/price** (com moeda) → `StatReveal`
- **Entradas Enter/Exit (14, POR ELEMENTO):** none·fade·slide·scale·bounce·flip·zoom·snap·glitch·swipe·float·filmburn·gaussianblur
- **Fundos:** grid-paper branco · gradiente escuro/âmbar · **cinza-silhueta** · blur (imagem/vídeo) · vídeo com ruído · grid preto
- **Overlays/treatment:** **panel-wave noise** · scanline/grão (`EditMask`) · vinheta · linha "versus" (divisor)
- **Layouts (o compositor):** single · split (2) · trio · grid/listicle (N + números) · versus (divisor) · chat/DM · comentários sequenciais

⇒ **Poucos templates são realmente únicos**; a maioria é `layout × primitivas`. Já temos base: `rembg`, `StatReveal`, `EditMask`, `PersonCard`, `CardsStructure`, `YtCta`.

**⭐ VARIANTES = DINAMISMO (princípio do Piter):** ter MUITAS variantes (mesmo layout, mas fundos/entradas/tratamentos diferentes) é o que **evita repetir o mesmo estilo** em toda imagem, todo vídeo e todo nicho — crítico numa rede de canais em escala. A combinatória (`layout × primitiva × fundo × entrada × tratamento`) **GERA centenas de variantes barato** → pool rico. O motor então: **sorteia por probabilidade do formato/nicho** (cada nicho com seu sabor) **+ regra de NÃO-REPETIR** (por vídeo e por nicho, a mesma dos clipes). ⇒ construir variantes **NÃO é desperdício — é o motor da variedade**; a combinatória só barateia.

---

## 5. MÁSCARAS de edição — footage Standard License (detalhe em `REGRAS_NICHOS.md §Máscaras`)
Obrigatório quando o tier de fonte = Web: clipe **3–5s**, **em quadro** (não full-frame), **≥2 máscaras low-opacity** (ajuste + grão/chiado + scanlines), **crop de marca-d'água** (centro = não usar), **sem repetir clipe**. → componente `StandardClip` a construir.

**Estilo de "quadro" DEFAULT (ref. VidRush, ex. do Piter 2026-07-16):** vídeo no **CENTRO** + **o MESMO vídeo ao fundo em BLUR/ampliado** (preenche a tela) + **overlay de partículas** + grão. Faz o clipe de 4s (copyright) parecer INTENCIONAL e transforma bastante (enquadramento + blur-bg + partículas). Reaproveita o próprio clipe; usa peças que já temos (blur, `ParticlesDrift`, grão). ⇒ default forte do `StandardClip` (melhor que moldura dura).

**Estilo "FRAME + GRID em PERSPECTIVA" (ref. VidRush, ex. do Piter 2026-07-16):** clipe dentro de uma **moldura arredondada** (borda + sombra) flutuando sobre um **fundo de grid/malha em perspectiva** (curvado, dark, tipo wireframe). Alternativa ao blur-bg-fill: em vez de repetir o próprio vídeo borrado atrás, usa um **fundo neutro estilizado (grid)** — mesmo efeito de "não full-frame" + parece intencional. ⇒ 2º estilo do `StandardClip` (o Director sorteia blur-bg vs grid). Peças: moldura CSS + grid SVG em perspectiva + partículas/fagulhas + grão.

**⚡ TAMBÉM É UM CONTAINER DE MONTAGEM (importante p/ o motor):** o exemplo do Piter tem **5 sub-clipes de 1–2s cada DENTRO da mesma moldura** — a moldura+grid ficam FIXAS e os clipes trocam rápido por baixo (corte seco). Isso **queima vários b-rolls curtos num único "beat"** mantendo continuidade visual pela moldura. Vira o componente **`FramedGridMontage`** (props: `clips[]`, `clipDuration` ~30–60f, `border`, `gridColor`, sparks on/off). Também serve como padrão de "montagem rápida" fora do contexto de máscara (ex.: sequência de provas/eventos). ⇒ construir junto do `StandardClip`.

**INTENSIDADE POR TIER (Piter, 2026-07-16):**
- **Stock (baixo)** → sem tratamento obrigatório (stock livre ok); grade leve opcional; full-frame liberado.
- **CC & PD (médio)** → LEVE: grade + 1 máscara sutil (grão/vinheta).
- **Web / ALTO risco (MÁXIMO)** → **≤5s (cap duro)** · **blur-bg-fill** (não full-frame) · **≥3 máscaras low-opacity** (grade + grão + scanline/chiado + partículas/leak) · **crop de marca-d'água** (centro=não usar) · **NÃO repetir o clip**.
- **Speed/mirror** = OFF por default (opcional; mirror quebra texto/placas). **Marca d'água** = crop MANUAL por parâmetro (marcar na decupagem); auto-detect = melhoria futura.

### 5.1 POOL DE MÁSCARAS + SELEÇÃO POR TIER (schema do MOTOR — Piter 2026-07-17)
**Princípio:** as máscaras **NÃO são fixas por vídeo**. São um **POOL** do qual o Director **sorteia por clipe**; o **tier de risco** (`fonte_compliance`) decide o que é **proibido / opcional / obrigatório** e os **caps estruturais**. Isso dá variedade (não repete o mesmo tratamento) e blinda o footage de alto risco.

> **TODO tier leva ALGUMA máscara/overlay** (Piter 2026-07-17) — nada de footage cru pelado, nem no T1. Sobe a intensidade conforme o risco.

**POOL (ingredientes):**
- **Frame style** (enquadramento, 1 por tier): `full_frame` (T1) · `blur_bg_fill` (✅ built — T2) · `framed_grid` (✅ `FramedGridMontage` — frame menor + grid, T3)
- **Overlays atmosféricos comuns** (o "tempero" reutilizável — conta pra "camada de N overlays"): `faiscas`/embers · `foguinho`/fire 🆕 · `vagalumes`/fireflies · `particulas` (✅ `ParticlesDrift`) · `chiado_leve` (✅ `TVStatic` low-op) · `light_leak` (✅ `LightLeak`) · `aurora`/`stars` (✅)
- **Overlay de texto** — em qualquer tier, **quando aplicável** (título/label/dado sobre o clipe).
- **Animação de imagem/vídeo do catálogo** — o footage do T2/T3 também pode entrar num container do acervo (comparison, slideshow, grid…) em vez de só frame, pra mais dinamismo.
- **Finalização** (sempre leve, não conta como overlay): `grao` (grain.png) · `vinheta` · `grade`.
- **Estruturais** (por regra): `cap_duracao` · `crop_marca_dagua` (centro=não usar) · `no_repeat` · `speed_mirror` (OFF default).

> **Definição fechada dos tiers (classificação + download) = `REGRAS_NICHOS.md §85`.** Aqui é a política de MÁSCARA. **Áudio 0% em TODOS os tiers** · **No-repeat GERAL** (dura no `web`).

**POLÍTICA POR TIER (receita de composição):**

| Tier (`fonte_compliance`) | Frame style | Overlays atmosféricos | Texto | Anim. img/vídeo (catálogo) | Cap | No-repeat | Crop |
|---|---|---|---|---|---|---|---|
| **1** `stock` LOW | `full_frame` | **≥1** | qnd aplicável | — | — | evitar | — |
| **2** `cc_pd` MEDIUM | `blur_bg_fill` | **2** (mix) | qnd aplicável | sim | ≤8s | evitar | se houver + atribuição |
| **3** `web` HIGH | `framed_grid` (frame menor + grid) — **NUNCA full-frame** | **3** | qnd aplicável | sim | **≤5s (duro)** | **PROIBIDO (1×)** | **obrigatório** |

**⚖️ BALANÇO footage × animação (Piter 2026-07-17):** como T2/T3 têm clipes CURTOS (≤8s/≤5s) e sem reuso, precisam de MAIS footage — o que enriquece o vídeo, mas aumenta exposição. Pra equilibrar, **ilustrar bastante com animações de DADOS / MAPAS / GRÁFICOS / TEXTO** (o acervo das 54) → o vídeo fica dinâmico dependendo MENOS de footage de imagem/vídeo (principalmente o arriscado). O acervo de animações **é** parte da estratégia de compliance, não só estética.
- **MIX-ALVO da timeline: ~40% vídeo · 30% imagem · 30% animação.** Os 30% de animação são a camada compliance-safe.
- **Ordem de busca do footage (vídeo E imagem) = T2 → T3 → T1** (`REGRAS_NICHOS §85`): T2 (CC, específico+limpo) → T3 (copyright, mascarado) → T1 (stock, seguro mas **genérico** → filler). Cada clipe carrega o tier real e leva a máscara dele. Validado no teste Hilux (2026-07-17): termômetro de licença→tier apurado (CC→T2, Standard→T3).

**ALGORITMO (StandardClip/Director, por clipe de footage):**
1. Lê o tier do clipe → carrega a receita (frame style fixo + nº de overlays).
2. Aplica o **frame style** do tier (T1 full_frame · T2 blur_bg · T3 framed_grid).
3. Sorteia **N overlays atmosféricos distintos** (N = 1/2/3 por tier), **evitando repetir a combinação em clipes vizinhos** (variedade).
4. Aplica **finalização** leve (grão/vinheta) + **overlay de texto** se o beat tiver rótulo/dado.
5. Aplica **estruturais**: corta em `cap_duracao`, marca `no_repeat`, aplica `crop_marca_dagua`.
6. Alternativa/extra: o footage pode entrar num **container de animação de imagem/vídeo** do catálogo (comparison, slideshow, grid…) em vez de só frame. Se o beat pede montagem → `FramedGridMontage` empacota vários sub-clipes curtos.

**Schema (materializa como `fonte_compliance` no preset/canal quando o MOTOR nascer):**
```json
{
  "pool": {
    "frame_styles": ["full_frame", "blur_bg_fill", "framed_grid"],
    "overlays_atmosfericos": ["faiscas", "foguinho", "vagalumes", "particulas", "chiado_leve", "light_leak", "aurora_stars"],
    "finalizacao": ["grao", "vinheta", "grade"],
    "estruturais": ["cap_duracao", "crop_marca_dagua", "no_repeat", "speed_mirror"]
  },
  "audio_mute": true,
  "no_repeat_global": true,
  "tiers": {
    "stock": { "tier": 1, "frame": "full_frame",   "overlays": 1, "texto": "if_applicable", "anim_catalogo": false, "cap_s": null, "no_repeat": "soft", "watermark_crop": false },
    "cc_pd": { "tier": 2, "frame": "blur_bg_fill",  "overlays": 2, "texto": "if_applicable", "anim_catalogo": true,  "cap_s": 8,    "no_repeat": "soft", "watermark_crop": "if_present" },
    "web":   { "tier": 3, "frame": "framed_grid",   "overlays": 3, "texto": "if_applicable", "anim_catalogo": true,  "cap_s": 5,    "no_repeat": "hard", "watermark_crop": true }
  }
}
```
> **Todo tier tem overlay** (T1 já leva ≥1). `audio_mute` + `no_repeat` valem em todos (`soft`=evitar / `hard`=proibido 1×). Pesos por nicho sobrescrevem (ex.: automotivo Tipo A quer o produto limpo → prioriza `full_frame`/menos overlay mesmo subindo tier). Máscaras reduzem risco, **não eliminam**. **Licença desconhecida ⇒ Tier 3.** **Balanço:** compensar footage curto/arriscado com animações de dados/mapas/gráficos/texto.

**Overlays/Transitions capturados junto (p/ o acervo dessas categorias, fase pós-animações):**
- `Fire/Embers Overlay` (fagulhas subindo, blend screen) — 🆕 **novo** (temos LightLeak/Particles/Stars/Aurora, falta FOGO).
- `Glitch Transition` (RGB-shift + scanline entre clipes) — temos `GlitchFlash` (flash de fronteira) → **estender p/ transição A→B**.
- `TV Static/Noise` (chiado de antena) — ✅ temos `TVStatic` (visual); chiado = SFX (banco).

---

## 6. BACKLOG DE CONSTRUÇÃO (o que virar código)

> **ORDEM DE TRABALHO (Piter, 2026-07-16):** (1) **ANIMAÇÕES / scene templates** primeiro — catalogar via decupagem por LOTE (Lote 1 feito, campos exatos) até fechar as ~199; DEPOIS (2) **Transitions** (§4.5) → (3) **Overlays** → (4) **SFX** — montar o acervo dessas 3 (mesmo método de decupagem; já parcialmente mapeadas + temos componentes). Só então o (5) **MOTOR** (probabilidade/compositor). Fase 2 (GIF previews) roda em paralelo conforme cada peça nasce.

- [x] `StatReveal` (dado typewriter + zoom-out)
- [x] `VintageAngled` (foto P&B angulada)
- [ ] **Biblioteca de Transições** (~20: wipes/iris/clock/flips/luz; orgânicas por último) + `TransitionGallery`
- [ ] **Animações Enter/Exit** (flip/float/gaussian-blur + formalizar bounce/snap/swipe) + sistema enter+exit por elemento
- [ ] **`verificar.py`** (auto-QA / "double-check" antes de publicar)
- [ ] **`fonte_compliance`** (knob + seletor na aba VidMator + wiring no resolver/clipar)
- [ ] **`StandardClip`** (máscaras p/ footage Web) + refazer `integrate_broll.py` (1-uso-por-clipe)
- [ ] `SpecCard` (folha técnica) · restilizar timeline p/ look Harley · categoria **Modelos** (2D/palitinho)
- [x] **Scene Templates / ANIMAÇÕES — 54 CONSTRUÍDOS (2026-07-16)** via fleet de 7 agentes → `remotion/src/compositions/*.tsx`, todos props niche-agnostic (defaults), registrados no `Root.tsx` (composition id = nome). Bundle compila, 54/54 stills OK (galeria `out/_gallery/`, contact-sheets no scratch). Cobre charts (Pie/Line/Growing/Bar/Circle/Stock/Percentage/Number), stats/callouts (Price/DualStat/Poll/OneWord/Icon×2/CircleHighlight/Bullet), mapas (MultiCountry/DrawPath/Route/Pin/Region/CountryChar), texto (SentenceHighlight/Reveal/Title/Quote/Chapter/Display/Date/Caption/DualImpact/Slide), pessoas (Character×3/Node/Subject/**Detective**/Chat), imagem (Two/Three/Four/CutText/Grid/Split/CaptionGrid/5Text/BeforeAfter/Annotation/Website/Article/Logo/Callout/Paper). Spec em `remotion/_ACERVO_SPEC.md`; preview via `remotion/render_gallery.mjs`. **FALTA (fase MOTOR):** wirar no BrollTest/passes p/ o Director escolher + passar props do timeline; e o motion frame-perfect por peça (refinar no uso).
- [ ] **Fase 2:** gerar GIF de cada opção → card do acervo (começar pelo `PresentationGallery`)
- [ ] **Fase 3 (MOTOR):** schema de formato (probabilidade por container) + registry plugável + wiring no template do canal
- [ ] banco de música rock/upbeat (motos) — pendência do vídeo de motos

---

## 7. DECISÕES ABERTAS / DÚVIDAS
- **"Modelos"** = o que exatamente? (estilo 2D/palitinho/raccoon? personagem de canal?)
- editar/persistir presets pela aba (precisa endpoint/fonte compartilhada)
- estrutura de formato: quantos formatos-base começar? (documentário, top-rank, 2D, estoicismo…)

---

## 8. PESO / PERFORMANCE (decisão, 2026-07-15)
Pergunta do Piter: adicionar animações + previews pesa o Automator? **Não, se feito certo.**
- **Animações NÃO pesam.** Vivem no **Director/Remotion (worker local)**, não no `video-automator` (FastAPI/VPS). No render **só as usadas na cena renderizam** — 199 registradas ≠ 199 renderizadas (`Root.tsx` = catálogo). Mais TIPOS no pool não aumentam custo/frame (o Diretor pega uns poucos/cena; gargalo de render = `mixBlendMode`+decode, não nº de opções). Bundle cresce desprezível.
- **Previews = único vetor de peso, mitigável:** NÃO usar GIF *eager* (gordo, ~2-5MB cada). Usar **MP4/WebM curto + pequeno + LAZY-LOAD (só ao aparecer/hover) + servido estático** (fora do bundle JS). Aba abre instantânea; previews sob demanda. São **conveniência** — não afetam produção; no pior caso, só o load da aba VidMator.
- **Runtime do Automator (Python/pipeline/VPS) intocado.**

---

## 9. INSIGHTS DE ENGENHARIA — VidRush (prompt-inject do Piter, 2026-07-16)
VidRush explicou a própria arquitetura: pipeline multi-agente sobre **1 JSON de estado (fonte da verdade + contrato)**; orquestrador com **escrita única + registro imutável/auditável**; **validador de densidade** (aritmética: nº de pontos do roteiro = esperado, senão ABORTA antes de gastar compute); roteirista emite **segmentos JSON** `{id, narração, duração, keywords visuais}`; **moderação** (difamação/trademark); narração ElevenLabs → **duração real = timeline mestra**; footage por **embeddings + similaridade** (Pexels/Pixabay); editor FFmpeg alinha aos tempos; **determinismo** (temp 0 + hash SHA-256 → vídeo byte-idêntico).

**JÁ FAZEMOS (valida nosso design):** JSON = fonte da verdade (`timeline.json`/`timeline_render.json`); narração→timeline mestra; cache de footage.

**UPGRADES (por dor nossa):**
1. **Validador de densidade/estrutura PRE-FLIGHT (fail-fast, barato):** checar aritmeticamente nº de itens (top-N) + beats obrigatórios (CTA) ANTES de TTS/render; aborta se off. Teria pego o motos + CTA faltando. Complementa `verificar.py`, mas ANTES.
2. **Orquestrador single-writer + estado isolado/auditável:** cura a colisão do `timeline.json` compartilhado (2 Claudes; render clobbado). Ação: **isolar o estado dos PASSES por job** (hoje só o render é isolado via JOB) ou serializar escrita.
3. **Visual keywords no roteirista + matching por EMBEDDING** (não keyword literal): antídoto do bike→bicicleta / horsepower→cavalo. Decidir a keyword visual *junto com a fala* + casar por similaridade semântica.
4. **Pass de moderação** (difamação/trademark) antes de renderizar — review de produto (marcas) + true crime.
5. **Determinismo:** temp LLM 0 + hash do estado → skip de re-render idêntico (já temos skip parcial "já renderizado").

---

## Cross-refs
- `REGRAS_NICHOS.md` — tipologia A/B/C, footage por nicho, máscaras, compliance, checklist
- memória `project_automator_infra.md` — topologia do automator + acervo + deploy do frontend
- `remotion/src/Root.tsx` + `remotion/src/compositions/*.tsx` — os containers
- `video-automator/VIDMATOR_INTEGRATION.md` — integração do MOTOR (simples/vidmator) no automator
