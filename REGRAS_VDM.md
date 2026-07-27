# NOVAS REGRAS VDM — espinha dorsal da estratégia (Piter, 26/07)

> **ESTILOS DE EDIÇÃO (decisão Piter 27/07):** o motor atual de edição é o
> **ESTILO v1** — validado e APROVADO (jardim ficou "muito bom"); continua em
> produção como formato próprio. As regras deste documento definem o **ESTILO v2**
> — um formato NOVO construído AO LADO do v1, não um substituto. Na arquitetura de
> gerentes-por-formato, v1 e v2 são formatos plugáveis: cada CANAL escolhe qual
> usar na sua identidade (§6). O que é comum aos dois: curadoria por seção, tiers,
> gate com OCR, fontes, mesa/auditoria — os bastidores servem os dois estilos.

> Documento-fonte da nova geração do VidMator. Seções marcadas **[PENDENTE — PITER]**
> serão preenchidas por ele antes da implementação. Nada aqui vira código sem a
> seção correspondente estar fechada.

## 1. Princípios

**#1 — Escala do roteiro.** Roteiros LONGOS como base: 12+ minutos (~8.000
caracteres) como piso de referência, SEM regra fixa de duração — canais T1 e T2
podem (e tendem a) rodar vídeos MAIORES, de 20~30 minutos. Consequência: MUITO
footage e MUITAS animações por vídeo — a construção precisa de volume e variedade
sem repetição, e as regras de anti-repetição escalam com a duração (acervos maiores
importam mais em vídeo longo).

**#2 — Rede de canais com identidade própria.** Vários nichos; dentro deles,
subnichos rodando FORMATOS diferentes por canal. Cada canal tem identidade definida
de antemão: personagem dedicado, estilo de frame (borda do vídeo), fontes
tipográficas e paleta de cores próprias, etc.

**#3 — Diretor por nicho + gerentes por formato.** Um diretor para cada nicho; uma
equipe de gerentes para cada diretor comandando o formato (palitinho, 2D, personagem
recortado com entrada dinâmica, formato com excesso de animação de texto, etc.).

**#4 — Base única, variações livres.** A lógica de construção do vídeo base é a
mesma para todos; as variações garantem que a base trabalhe em qualquer edição sem
parecer mais do mesmo.

**#5 — Plug and play.** Diretores, gerentes e formatos precisam ser plugáveis no
editor base: todo novo nicho ou formato entra facilmente e sai com resultado
satisfatório. Isso garante a qualidade das variações.

## 1b. TIER DO CANAL (teto de risco por canal)

Cada CANAL recebe uma classificação de tier, igual à dos footages — e ela é o TETO
do que a produção daquele canal pode usar:

- **Canal T1** → usa SOMENTE footage T1 (stock).
- **Canal T2** → usa T1 ~ T2 (stock + CC/domínio público).
- **Canal T3** → usa T1 ~ T3 (cascata completa, incluindo web com máscara pesada).

Racional: muitos canais funcionam bem em T1/T2 sem correr o risco do T3. O tier do
canal é definido DE ANTEMÃO na identidade do canal (§6) e o **diretor do
nicho/modelo nasce sabendo o tier do canal** — toda decisão de busca/curadoria
respeita esse teto automaticamente.

> Ponte de implementação (Claude): o pipeline já tem `tier_teto` por beat
> (`--teto stock|cc_pd|web` no diretor + `TETO_N` no executor) — o tier do canal
> vira o valor default desse teto, vindo do style_card/identidade do canal.

## 2. Fontes de footage

### Vídeo
- **Non-stock:** YouTube, TikTok, Meta (Facebook e Instagram), Rumble, Reddit,
  Snapchat, X, Vimeo, Threads, Dailymotion, Bilibili, VK, OK.ru, Niconico,
  Internet Archive, Wikimedia Commons.
- **Stock:** Pexels.

### Imagem
- **Non-stock:** Google Images e Bing Images, Flickr, Reddit, Instagram, Facebook,
  Threads, Pinterest, Tumblr, Imgur, Flickr Commons, Wikimedia Commons, Internet
  Archive, Google Maps (avaliações), printscreen de vídeos, Library of Congress,
  sites oficiais de instituições (governos, universidades, etc.).
- **Stock:** Pexels.

### Hierarquia de ilustração (ordem de preferência)
1. Filmagens REAIS do que está sendo falado
2. Trechos de notícias de TV
3. Vídeos de celular filmados por pessoas comuns
4. Stock footage (por último — serve mais de "cenário")

## 3. Padrões de busca (vídeo)

Combinar o assunto com âncoras de autenticidade:
- `"caught on camera" + assunto`
- `"filmed on phone" + assunto`
- `"cell phone footage" + assunto`
- `"home video" + assunto`
- `"amateur footage" + assunto`
- `"eyewitness video" + assunto`
- `"captured by resident" + assunto`

Com operador de site (exemplos):
- `site:reddit.com "assunto" filmed from backyard`
- `site:youtube.com "assunto" "cell phone footage"`
- `site:x.com "assunto" real`

## 4. Animações

### Texto
Ilustrar: capítulos, tópicos, headlines, descrições, quotes.

### Imagens (FECHADO — Piter 26/07)
- Frame com animações de ENTRADA variáveis.
- Imagem T3 pode ir em tela cheia por NO MÁXIMO 2s.

**Multi-imagem é OBRIGATÓRIO quando o contexto permitir 2+ imagens**, e o CONTEXTO
decide a forma:
1. **Comparação (A vs B):** animação de comparação — objeto A na esquerda, "VS" no
   meio, objeto B na direita.
2. **Antes e Depois:** Before/After — o primeiro entra em FULL SCREEN,
   dinamicamente o segundo entra em full screen, e fecham LADO A LADO.
3. **Várias imagens ilustram bem o trecho:** dupla/multi imagem — as 2 (ou 3, ou 4)
   aparecem na tela AO MESMO TEMPO.

**Máscaras de imagem T3 (variar entre):**
1. Frame central com fundo grid preto e linhas brancas (default atual).
2. BLUR na marca d'água + círculo vermelho ou seta PISCANTE (dinâmica) no ponto de
   maior importância da imagem.
3. Vinheta escura ao redor + ZOOM IN dramático de 2s no ponto de maior importância
   e zoom out de volta pro default.
4. Full screen com passagem RÁPIDA (com blur gaussiano na marca d'água quando houver).

**Overlay de texto em imagem:** toda imagem, independente do tier, PODE (conforme o
contexto) receber overlay de animação de texto que entra de acordo com o trecho.

### Vídeos
Regra dos tiers mantida, mas T3 ganha **3 máscaras diferentes variando** (não só o
fundo em grid):
1. Frame cinemático com BLUR (em vez de faixa preta)
2. Overlay de câmera antiga
3. Frame cinemático com faixa preta
4. (atual) grid em preto com linhas brancas
As máscaras rotacionam — nunca a mesma cara em todo T3 do vídeo.

### Mapas (FECHADO — Piter 26/07)
- TODA menção de localização (país, estado, cidade) vira animação de mapa.
- Escolha ALEATÓRIA entre as variações, SEM REPETIÇÃO no vídeo.
- **Regra absoluta de esgotamento:** se o roteiro menciona locais tantas vezes que
  TODAS as variações se esgotam, aí (e SÓ aí) a repetição é permitida, de forma
  aleatória.
- O acervo pode crescer — mais variações = mais possibilidades.

**Grupo 1 — Localização PONTUAL (cidade/país), 4 variações atuais:**
1. **Radar + minimiza:** mapa ilustrativo com ponto brilhando (estilo radar) no
   local; zoom out minimiza o mapa pra lateral ESQUERDA e mantém imagem aérea ou
   de pontos turísticos de referência do local (1 a 3 imagens; com 2-3, cada uma
   fica 1-2s na tela com transição dinâmica).
2. **Google Maps zoom-in:** imagem de Google Maps em zoom out aproximando em zoom
   in do local; ao chegar, cria ponto de referência, puxa LINHA TRACEJADA até o
   nome do local e 2-3 imagens recortadas do local aparecem na lateral.
3. **Satélite + typewriter:** imagem de satélite (Google Earth) com ponto estilo
   radar e o nome da cidade/local em animação TYPEWRITER (com SFX de typewriter).
4. **Satélite 3D:** variação da 3 com proximidade maior e visão 3D do mapa.

**Grupo 2 — "De um local a outro" (transição/trajeto):**
1. **Trajeto com zoom:** mapa em zoom out com pinpoint na origem e no destino;
   zoom in na origem, linha dinâmica simula o trajeto até o destino; no final,
   zoom out mostrando o trajeto completo.
2. **Voo de avião:** variação da 1 sem zoom in/out — uma FLECHA dinâmica simulando
   voo de avião faz o caminho origem→destino; texto dinâmico com a DISTÂNCIA em
   km/milhas.
- Outras animações de movimento serão adicionadas depois; escolha aleatória como
  no Grupo 1.

### Gráficos (FECHADO — Piter 26/07)
- Gráfico SOMENTE para ESTATÍSTICA: "x em cada y", X%, comparação de quantidades,
  divisões em quantidade ou % — nada além disso (número ordinal/idiomático,
  contagem de lista, número de título NUNCA viram gráfico; reforça o R-110).
- As animações podem ser as já existentes no acervo (Graf01-16).
- Anti-repetição igual aos mapas: sem repetir variação no vídeo, EXCETO se as
  opções se esgotarem (aí repete aleatório).

### Pessoas / Autoridade (FECHADO — Piter 26/07)
- TODA menção a figura de autoridade vira animação de autoridade.
- **A PESSOA PRECISA SER ILUSTRADA — foto dela na tela é OBRIGATÓRIA.** Animação
  de autoridade sem a imagem da pessoa não cumpre a regra: QuoteCard, Ovl07 e
  NodeHierarchy só valem ACOMPANHADOS da foto da pessoa (no próprio card ou
  pareados com CharacterCard/Keyword no mesmo trecho).
- Sem repetição no vídeo, igual às anteriores (exceção de esgotamento).
- **Formas em uso (acervo atual):** CharacterCard (foto + nome + cargo),
  CharacterKeyword (foto + palavra-chave), NodeHierarchy, QuoteCard,
  Ovl07_QuoteAttribution — os 3 últimos condicionados à foto presente.
- Fonte da foto: fonte NOMEADA — Commons (R-25) AMPLIADO pelas fontes oficiais do
  §2 (sites de governos/universidades, Library of Congress, imprensa citável).
  NUNCA stock genérico com nome real (atribuição falsa = proibido).
- Consequência de implementação: os builders de QuoteCard/Ovl07/NodeHierarchy
  ganham slot de foto; o curador de imagens busca retrato para TODA autoridade
  citada no roteiro.

### Datas (FECHADO — Piter 26/07)
- Animações de DATA, com anti-repetição (exceção de esgotamento):
  1. **Ovl10_NumberBadge** — ano gigante sobre footage nítido (motor do R-27)
  2. **Ovl05_CornerTag** — tag de época no canto ("ARCHIVE · 1986")
  3. **DateLocationOverlay** — overlay data+local
- O jornal de época (Soc04) NÃO pertence à família de data → categoria SOCIAL.

### Social (FECHADO — Piter 26/07)
- Categoria própria: **recortes de jornal, sites de notícia, Instagram, X e
  Reddit** = Soc01_InstagramDM, Soc02_RedditPost, Soc03_TweetPost,
  Soc04_Newspaper (época/histórico), Soc05_NewsSite (notícia atual).
- Identidades em social SEMPRE fictícias (regra vigente do canal) e jornal usa o
  `jornal_ficticio` do style_card.

## 5. Lógica do footage

### 5.1 Mix e liberdade criativa (FECHADO — Piter 26/07)

- Canal T3 = trabalho completo: misturar imagens, vídeos e animações de DIFERENTES
  tiers para o vídeo ficar bem editado.
- **FIM da regra de % fixa** (40% vídeo / 30% imagem / 30% animação — descartada).
  O diretor escolhe o footage que melhor se adapta ao trecho, independente de
  proporção. Liberdade criativa aberta = vídeos diferentes entre si, sem cara de
  linha de produção em série (mesmo entre nichos/temas/formatos distintos).

### 5.2 REGRA DO HOOK — primeiros 2 minutos (FECHADO — Piter 26/07)

Vale pra **qualquer nicho, modelo e tier de canal**:

- Os primeiros **2 MINUTOS** são o hook e precisam ser DINÂMICOS: trocas rápidas
  de b-roll em formato HIPNÓTICO — a pessoa fica hipnotizada assistindo.
- No hook, o critério de seleção de footage é AINDA MAIS importante que no resto
  do vídeo.
- O dinamismo é ENTRE FORMATOS: vídeos com animações de texto POR CIMA, imagens
  com animações de entrada, e animações visuais (gráficos, mapas, pessoas —
  QUANDO APLICÁVEL conforme as regras de cada família). Isso dá o acabamento
  elegante/premium.

### 5.3 Camada universal de polimento (FECHADO — Piter 26/07)

Independente do tier, TODOS os canais levam:
- Transições leves com SFX
- Overlays (textura/grão/luz conforme identidade do canal)
- SFX de texto (animações de texto sonorizadas)
- **Trilha sonora dinâmica** que varia conforme o MOMENTO do roteiro
Objetivo: imersão e hipnose — qualidade percebida premium.

**SFX — acervo NOVO (Piter 26/07):** esquecer os SFX atuais do projeto. Entra um
acervo novo selecionado MANUALMENTE por um integrante da equipe, com maior precisão
de qualidade. A implementação da camada §5.3 espera esse acervo (pasta/manifesto a
definir) — nada de reaproveitar os arquivos antigos.

**Mixagem de SFX (Piter 26/07 + 27/07):**
- **SFX morre JUNTO com a animação** (QA do V2EDIT: typewriter continuava depois
  da animação terminar): a duração do SFX é limitada à duração do movimento que
  ele sonoriza (typewriter = janela de digitação ~55% do beat), sempre com
  fade-out — nunca corte seco, nunca vazamento.
- SFX SEMPRE em volume MAIS BAIXO — apoia a narração, nunca compete com ela
  (é tempero, não protagonista).
- O efeito precisa ser COERENTE com a transição/animação que acompanha: whoosh em
  movimento/wipe, typewriter em texto digitado, riser em build-up, stinger em
  revelação, glitch em corte glitch — nunca som genérico em cima de qualquer coisa.
  Base prática: o pareamento `sfx_par` do manifesto de transitions já encode isso;
  para animações, mapear família da animação → família de SFX no motor do animador.

### 5.4 [PENDENTE — PITER] Separação, estruturação e papéis

> Preencher: como a separação e a estruturação acontecem e como cada um
> (diretor, gerente, curadores, animador) faz o seu papel.

- Como o roteiro é dividido em blocos/seções e quem decide o quê:
- O que o Diretor do nicho define vs o que o Gerente do formato define:
- Ordem dos passes (imagens → vídeos → animações?) e contratos entre eles:
- Critérios de aceite por passe (quando um footage "serve"):
- Como um canal novo pluga (arquivo de identidade? style_card estendido?):

## 6. [PENDENTE — PITER] Identidade por canal

> Preencher: campos da identidade (personagem, borda/frame, fontes, paleta,
> trilha, CTA) e onde ficam registrados.

---

## Anexo (Claude) — pontes com o que já existe hoje

*Só referência de implementação; não altera as regras acima.*

- Busca/download multi-fonte: yt-dlp já cobre YouTube, TikTok, Facebook/IG, Rumble,
  Reddit, X, Vimeo, Dailymotion, Bilibili, VK, OK.ru, Niconico e Archive — a cascata
  atual (executor/curador) precisa só de query-builders por fonte + os padrões §3.
- Tiers/gate/máscara: pipeline atual (T0-T3 + gate Vision com contexto de seção) é a
  base; as 3 máscaras novas de T3 entram no `ClipT3` do Montagem (hoje: grid+3 shapes).
- Sem-repetição de mapa/gráfico/autoridade: o registry já tem quotas `max_uso` por
  componente — vira `max_uso=1` nessas famílias + exigência de família diversa.
- Identidade por canal: evolução do `style_card.json` (fontes/paleta/chapter_style já
  existem; faltam personagem, borda, trilha, CTA).
- Plug-and-play: ARQUITETURA_FUNCIONARIOS.md (curadores + animador) é o esqueleto
  onde diretores/gerentes plugam como configuração, não como código novo.
- §4 imagens/mapas: já existem no acervo — Before/After (Img05), split A-vs-B
  (Img04/Duo), grids multi-imagem (Img06/08/20), máscara T3 grid (ClipT3),
  satélite ESRI (pin/zoom/draw-path, MapRoute). NOVOS a construir: máscara T3 c/
  blur+círculo/seta piscante, vinheta+zoom dramático 2s, full-screen rápido c/
  blur gaussiano na marca; mapa "radar+minimiza c/ imagens", "Google Maps zoom-in
  c/ linha tracejada+imagens", satélite 3D, voo-de-avião c/ distância. Overlay "VS"
  central dedicado.
- §5.2 hook de 2min: o hook atual do código é 15s (R-15/16) — precisa virar uma
  JANELA DE HOOK parametrizada (~120s) com ritmo próprio (planos mais curtos,
  alternância obrigatória de formato beat a beat) e critério de gate mais rígido.
- §5.1 fim das %: aposentar o alvo de mix fixo do diretor.py (relatório "VidRush
  alvo ≈ 45/20/15/20") e o texto_budget como TETO vira só guard-rail anti-abuso,
  não meta de proporção.
- §5.3 áudio/polimento — ACERVO DA EQUIPE BAIXADO (26/07) em
  `banco-videos/_acervo_equipe/` (fonte: Drive do Carlos, pasta Assets):
  * `sfx/` 126 itens, manifesto com família/intensidade/duração/pico_dbfs/loop;
  * `transitions/` 35 itens com modo luma, duração, pico_s e SFX PAREADO
    (`sfx_par`/`sfx_alt`) — transição+som já casados pela equipe;
  * `overlays/` 49 itens com modo de blend/loop/res/fps;
  * `Trilhas sonoras/documentario/` 97 trilhas catalogadas POR MOMENTO
    (hook/build/epico/frio/nostalgia/revelacao...) = o mapa direto do
    "trilha dinâmica conforme o momento do roteiro".
  Motor a construir no animador: momento da seção → categoria de trilha; corte de
  seção → transição com pico_s alinhado + sfx_par; animações de texto → SFX de
  texto (foley_typewriter cobre o mapa 3); overlay conforme identidade do canal.
  Técnica mantida: PICO no corte, nunca arquivo cru do zero.
