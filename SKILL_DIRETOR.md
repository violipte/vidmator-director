# SKILL DO DIRETOR v2 — a inteligência de edição do VidMator

Herda todas as cicatrizes do v1 (job HARLEY, 21-22/07/2026) e adiciona a camada que faltava: **intenção**. O v1 era o porteiro — impedia o erro. O v2 é o diretor — persegue o acerto, sem abrir mão de nenhum veto do v1. (v1 preservado em `SKILL_DIRETOR_v1.md`.)

**Convenção nova:** toda regra tem ID (`R-xx`). Logs de auditoria, re-pick e pré-QA citam IDs ("beat 14 rejeitado por R-21"). Regra sem ID não existe. Regra nascida de bug carrega a origem entre parênteses.

**Status de implementação:** regras marcadas `[F1]` estão implementadas (Fase 1, 22/07); `[F2]`/`[F3]`/`[F4]` são fases planejadas; sem marca = herdada do v1, já em produção.

---

## 0. Glossário (para agente novo não alucinar termo)

- **beat**: unidade mínima da montagem, delimitada por timestamps do STT
- **natureza**: classe do que o beat pede (mapa | chart | imagem | texto_full | texto_overlay | pessoa)
- **acervo / almoxarifado**: conjunto de variações de componentes registradas no `acervo_registry.py`
- **decupar**: gerar contact sheets do render (`decupar.py`) e varrer frame a frame
- **condenar**: deletar `resolvido/bNNN.json` + `assets/bNNN__*` para o executor resumível refazer só aquele beat
- **style card**: JSON por job com identidade visual do nicho (ver §9)
- **demote**: beat de texto excedente do orçamento (§11) convertido em b-roll reusado da seção

---

## 1. Princípio central: o LLM DESCREVE, o código ESCOLHE

**R-01** — O LLM (Stage 2) nunca escolhe componente. Ele entrega por beat:
1. **natureza** do que o trecho pede
2. **dados REAIS** extraídos do roteiro (números copiados literalmente, países citados, coordenadas, citações com autor)
3. **estratégia** (literal | entidade | dado | peca | abstrato | atmosferico) e busca de footage
4. **`[F3]` energia**: 1-5, quanta força visual o momento pede
5. **`[F3]` funcao_narrativa**: `hook | setup | desenvolvimento | virada | climax | respiro | cta`

Quem transforma isso em animação é o registry: **seleção por score determinístico** (§4), com seed por job. Isso mata o vício do LLM de repetir os mesmos 3 componentes e garante que TODA validação roda em código testável.

**R-02 `[F3]`** — energia e funcao_narrativa são *descrição*, não escolha: o LLM diz o que o momento É; o código decide o que ele GANHA. Se o LLM omitir os campos, o pass infere defaults conservadores (energia 2, desenvolvimento) e loga o buraco — nunca bloqueia o pipeline por metadado narrativo faltante.

---

## 2. O vídeo é um ARCO, não uma fila de beats `[F3]`

O v1 não tinha uma única regra que olhasse o vídeo inteiro. Estas olham:

**R-10 — Validação da curva**: antes do re-pick, o pass monta a curva de energia do vídeo e valida a forma:
- curva flat (variância ~0) = suspeita → loga warning e força variação via bonus posicional
- existe exatamente 1 clímax por vídeo (energia 5); mais de um = o LLM está inflacionando → rebaixar os excedentes. **EMENDA 22/07: o clímax NÃO é inferido "pelo áudio" (inferência alucinável) — ele é DECLARADO pelo Stage 1**: a seção `virada/revelação` do modelo VidRush já existe na estrutura de seções; o pass apenas valida que a energia 5 caiu DENTRO dela e rebaixa energias 5 fora dela.
- vídeo sem nenhum `respiro` após o minuto 1 = fadiga garantida → o pass promove o beat de menor energia de cada bloco de ~60s a respiro

**R-11 — Pós-clímax pede respiro**: o beat seguinte ao clímax não aceita card pesado nem texto full-screen. Footage segurando, overlay no máximo. O impacto precisa de espaço pra assentar.

**R-12 — Regra do 4º beat**: 3 beats consecutivos de energia ≥4 forçam o 4º a componente leve (score de componentes pesados zerado nesse beat). Densidade sem alívio vira ruído.

**R-13 — Abertura de seção tem peso**: o primeiro beat após um ChapterTitle recebe bonus para classe visual forte (footage TIPO A ou animação-assinatura). Seção que abre com overlay tímido morre na largada.

**R-14 — Escalada por seção**: dentro de uma seção, a energia média do último terço deve ser ≥ à do primeiro. Seção que desinfla é sinal de roteiro fraco naquele trecho — logar para o Stage 1 (warning-only), não maquiar na edição.

---

## 3. Hook (0–15s) e fechamento: os dois momentos que não perdoam

Retenção vive no hook e a decisão de like/subscribe vive no fim. Regras próprias:

**R-15 `[F1]`** — Beat 0 NUNCA é ChapterTitle, texto full-screen ou overlay leve. O vídeo abre com imagem forte (footage TIPO A, animação-assinatura ou imagem com slots reais).

**R-16 `[F1]`** — Todos os beats dentro dos primeiros 15s só aceitam classe visual forte. Overlay leve tem score zerado no hook; texto excedente no hook vira demote de VÍDEO (nunca card).

**R-17 `[F2]`** — O beat de maior energia do hook recebe o componente de maior peso ainda disponível no acervo (bonus posicional máximo). O melhor cartucho abre o jogo.

**R-18 `[F2]`** — Nenhum componente usado no hook repete antes do minuto 2 (cooldown estendido). O hook define a assinatura visual; queimá-la cedo barateia o vídeo.

**R-19 `[F2]` — Fechamento circular**: a seção de CTA/encerramento ganha bonus para REUSAR o componente-assinatura do hook (mesma variação, dados novos). Esta é a ÚNICA exceção legítima ao cooldown de vizinhança — e é intencional, não sorteio: callback visual fecha o arco.

---

## 4. Seleção por SCORE determinístico (o sorteio puro morre na F2)

Um diretor não sorteia — escolhe o que serve o beat. Mas escolha em código, testável e reproduzível:

```
score(variação, beat) =
    fit_dados        # ELIMINATÓRIO: builder valida ou score = 0
  + fit_duracao      # ELIMINATÓRIO: fora de [min_dur, max_dur] = 0
  + bonus_posicional # hook, clímax, abertura de seção, fechamento (§2-3)  [F2]
  + novidade         # pró-menos-usada + penalidade de vizinhança
```

**R-20** — Elegibilidade de DADOS continua binária e eliminatória, exatamente como no v1:
- Mapa: país resolvido no atlas (continente = rejeitado), coordenada real ou gazetteer
- Chart: número ancorado no que o narrador FALA (§6)
- Imagem: N slots preenchidos com fotos reais aprovadas no gate
- Img14 (TitleCutout): palavra-título de 4-14 chars (a palavra É a arte)

**R-21 `[F1]`** — Elegibilidade de DURAÇÃO agora tem teto: `min_dur` do v1 mantido (Chapter/mapa/chart ≥3s · social/séries ≥3.5-4s · overlay leve ≥1s) **+ `max_dur` novo**: overlay leve ≤4s; card de texto full ≤5s; beat de animação >6s exige componente composto (footage + overlay, que o montador já monta via bg) ou split do beat `[F3]`. Overlay parado 9s na tela é tão podre quanto Chapter de <1s. (`max_dur` NÃO se aplica a footage — clipe longo é normal e bom.)

**R-22 `[F2]`** — Anti-repetição vira TERMO DE SCORE, não veto binário: cooldown de vizinhança (<8 beats) é penalidade forte mas superável pelo bonus do R-19. **Exceção dura que continua veto**: quota `max_uso` por vídeo (assinatura 1×, comum 2×, discreta 3-4×) — quota estourada = score 0, sem negociação.

**R-23** — Desempate: seed determinística por job. Mesmo job, mesmo plano → mesma montagem, sempre. Reprodutibilidade é sagrada para o QA (§12).

**R-24 `[F1]` — DADO NUNCA VIRA FOTO** (QA seniors 22/07: "15% dos corredores morreram" virou polaroid de pista com '5' pintado + caption 'Runners Died' — comunicação DESTRUÍDA). A cadeia do chart não contém a natureza imagem: dado sem chart válido cai para TEXTO, nunca para foto literal do número.

**R-26 `[F1]` — DADO DE OURO: comparação ancorada = chart OBRIGATÓRIO** (QA seniors 22/07: "15% vs 34%" — o dado central do vídeo — virou frase de rodapé. Autópsia: o LLM entregou labels/values PERFEITOS; morreu por 3 bugs empilhados — `float("15%")` explodia no builder, o LLM marcou ChapterTitle e o "mantém estrutural" do pass protegeu o erro). Regra: beat com 2+ números ancorados → chart comparativo com prioridade máxima: ignora cooldown, ganha stretch de 3s (como Chapter). Dado forte NUNCA degrada pra texto. Builders sanitizam valores (`"15%"→15.0`); ChapterTitle só é "mantido" se NÃO tiver cara de dado.

**R-27 `[F1]` — Ano falado = DATA na tela** (QA seniors 22/07, ref. direta VidRush: "In 1984..." abrindo o vídeo sem overlay de data). Beat de footage cujo texto abre com ano (inclusive POR EXTENSO no STT — "nineteen eighty four") → overlay `Ovl10_NumberBadge` com o ano GIGANTE sobre o PRÓPRIO footage, nítido (`bg_nitido`: brightness 0.62, sem blur — o blur escuro padrão é para texto, data pede o footage visível). 1× por ano distinto por vídeo.

**R-25 `[F1]` — Pessoa NOMEADA ganha ROSTO** (QA seniors 22/07: Jeff Galloway citado sem foto). Beat de entidade com `dados.name` → natureza pessoa → CharacterCard com busca `"<nome> portrait photo"` (Commons tem figuras públicas em CC); a âncora do nicho NÃO entra em busca de retrato. O prompt do Stage 2 exige a chave `name` para pessoa (só `title` não dispara o fluxo).

---

## 5. REGRA DE FERRO: nenhum default de exemplo renderiza. NUNCA.

Inalterada do v1 — vazou 3 vezes por 3 caminhos, todos fechados:

**R-30** — Builder retorna `None` sem dados completos (não "faz o possível") → re-seleção.
**R-31** — `mapear_props` do montador MORREU (era a fonte do "Toyota Hilux 90%/78%", Tehran→Dubai, "SUBJECT"). O pass final re-valida TODO beat de animação pelo registry — inclusive fallbacks do executor, que emitem `componente: None`.
**R-32** — Componente TSX não pode ter default de exemplo (o "HILUX" do Img14 era hardcoded no React). Sem prop real → `return null`, e o registry nunca deixa chegar lá. Vale pra CONTEÚDO EDITORIAL também (QA tenis 23/07: "Lorem factum est" no corpo do jornal, kicker "The Motor Chronicle" num vídeo de tênis): tudo que tem sabor de nicho vem do `style_card` (`jornal_ficticio`) ou dos props — builder `_soc_news` exige sentença FECHADA (termina em .!?) ou recusa.

---

## 6. Números: só o que o narrador FALA

Inalterada do v1:

**R-35** — Ancoragem contra o texto do STT com números por extenso ("forty-five percent" → 45, "ninety thousand" → 90.000, "nineteen eighty three" → 1983).
**R-36** — Pontuação FECHA o número ("nineteen twenty, seventeen" = 1920 + 17, nunca 1937).
**R-37** — Valor nos dados do LLM que não bate com o áudio = rejeitado (o LLM inventa tendências tipo [50, 70, 90] para "sales curved upward" — sem número no áudio, sem chart).
**R-38** — Ano falado não ganha vírgula de milhar (2003, não "2,003").

---

## 7. Texto de tela ≠ transcrição

Herdada do v1, com o teto do R-21 aplicado:

**R-39a** — Texto full-screen é frase de impacto, não legenda. `humanizar()`: números por extenso→dígitos, siglas soltas coladas ("w l a"→"WLA"), capitalização.
**R-39b** — `frase_de_tela()`: corte APENAS em fronteira de cláusula/sentença, 3-12 palavras; não coube → recusa (cai pra overlay curto ou outra natureza). Nunca "...in the wo".
**R-39c** — Último recurso (`frase_forcada`): ≤8 palavras + "...", nunca terminando em stopword.
**R-39d** — ChapterTitle: número = ordem real de exibição, título = Stage 1, 1 por seção, ≥3s (stretch roda DEPOIS do ajuste de sobreposição, senão o vizinho re-encolhe o card).

---

**R-96 `[F1]` — Título de seção não reaparece** (spec Piter, implementado no job tenis 23/07): a linha do título de capítulo NUNCA vira texto de outro beat — duplicata detectada no montador → demote pra b-roll.

**R-108 `[F1]` — Correções de STT por job** (QA tenis 23/07: "ACS Gel Nimbus", "Animbus", "The 88" IAM PRA TELA num vídeo de produto): `style_card.correcoes_stt` = dicionário aplicado ao texto do beat na ENTRADA do montador — cobre builders, resgates e R-26/27. Nomes de marca/modelo do nicho SEMPRE ganham entradas no dicionário junto com a desambiguação de busca. Aplica-se TAMBÉM aos `dados` do plano (labels/títulos de gráfico carregam o mesmo erro de STT).

**R-109 `[F1]` — Nunca 2 animações de texto adjacentes** (Piter 23/07: "3 animações de texto seguidas sem sentido nenhum e com frames bem rápidos"): na TIMELINE FINAL, animação da família texto (Texto*/Ovl* sem `bg_nitido`) nunca encosta em outra. Enforcement em camadas no montador: (1) tracker no loop rejeita texto após texto — inclui LOOKAHEAD para capítulo minimal (posição do capítulo é fixa; quem cede é o beat anterior); (2) pool esgotado → o beat FUNDE no anterior (1 animação mais longa, nunca um segundo card); (3) SWEEP FINAL na timeline pós-ajuste — porque o ajuste de sobreposição pode ENGOLIR o beat separador (beat com overlap total desaparece e cola dois textos que o tracker via como separados). O sweep demove o par flexível pra b-roll (capítulo é intocável) ou funde. Auditor tem a invariante A-seq espelhada. Corolário aprendido: bookkeeping de reuso é UM só — usos de `bg` e de duo contam como aparição do arquivo antes do sweep, senão o demote do sweep reusa um vídeo que já é fundo de overlay (R-56 estourava em [0,47,73]).

**R-111 `[F1]` — Anúncio de produto = PRODUTO NA TELA** (QA tenis v2 23/07: "Number four, the ASICS Gel Nimbus" virou card de texto; NB 880 tocou footage de Adidas; Clifton foi ENGOLIDO pelo overlap do capítulo): beat cujo texto casa `number N` + chave da `desambiguacao` é ANÚNCIO. Executor resolve FOTO DO PRODUTO exato (web, T3, gate EXACT) antes de qualquer coisa; montador bloqueia texto/pool genérico nesses beats e dá `_min_dur` 2.5s (o ajuste de overlap nunca o engole); auditor exige `__produto` no src E acusa anúncio AUSENTE da montagem. Corolário: TODO modelo do vídeo precisa de chave na `desambiguacao` ("880", "eight eighty" — o STT fala por extenso).

**R-32b — Default de dado FAKE no TSX é o pior default** (QA tenis v2: card mostrou "18" quando a narração dizia 25 — o componente Graf10 tinha `values : [8,10,12,15,18]` hardcoded e o array default ROUBOU a cena do valor real; Graf07 tinha até anos falsos 2017+): componente de gráfico sem dados reais/labels casados = `return null`. NUNCA arrays de exemplo. Seis componentes limpos (Graf07/08/09/10/11/12).

**R-39c — Truncação é por PALAVRA, sempre** (QA tenis v2: "Flagship Com", kicker "RULES FOR CHOOSING RUNNING"): `corte(s, n)` corta na última fronteira de palavra e limpa pontuação pendurada — aplicado em todos os slices visíveis de título/kicker/texto (builders + montador). `frase_de_tela` prefere a cláusula pós-`:` ("...this list: Rule one: cushioning" → "Rule one: cushioning").

**R-21b — Animação ASSENTA em ~0.9s** (QA tenis v2: contador flagrado no meio — "3" de 5): count-up/odometer/donut assentam em ≤26 frames; o número certo domina o tempo de tela. Animação que não termina dentro do beat é bug de componente, não de duração.

**R-56b — BG de overlay é SÓ vídeo** (QA tenis v2: foto de produto do beat 19 reapareceu borrada de fundo no beat 55): imagem estática = 1 uso TOTAL (src OU props OU bg — bookkeeping único); o pool de bg do montador só aceita .mp4/.webm/.mov.

**R-64b — Moldura T3 varia** (Piter: "gradiente de fundo sempre igual... máscara de imagem igual todas as outras"): 4 paletas escuras (por seção) × 3 formatos de quadro (por beat, determinístico) no ClipT3 do Montagem.

**R-112 `[F1]` — REGRA-MÃE VidRush: dado anota o footage, nunca troca de cena** (decupagem de 14 vídeos, 24/07 — `DECUPAGEM_VIDRUSH_EDITOR.md`): dado ÚNICO em card escuro full-screen é PROIBIDO quando o job tem footage — `SWAP_TO_OVL` troca Graf01/02/03/10 pelo overlay equivalente (Graf14/15/16) e o pass de bg dá o fundo; sem bg possível, o último-caso reverte (simetria = nunca frame preto). Pack novo: `Ovl11_SpecBadge` (`17 • LBS DRAG`), `Ovl12_GiantStat`, `Ovl13_PriceTag`, `Ovl14_PillVerdict`, `Lst01_NoteChecklist`, `Lst02_SidePanelList`, `Img21_ProductAnnounce` (anúncio = foto do produto + rank+nome POR CIMA), `Img22_ProductCallouts`, `Img23_CollageCompare`. Ovl11-13 são ANOTAÇÃO (não contam como texto no R-62/R-109; bg fica NÍTIDO). Auditor: invariante A-G1.

**R-113 `[F1]` — Split de plano** (VidRush: ~16 cortes/min, plano ~4s): beat de footage >6s vira 2 planos do MESMO asset — 2º segmento com offset (ffprobe) e tratamento distinto (zoom/tint/p&b), `i+900`, flag `_seg` (auditor não conta como reuso). Charts comparativos (Graf05/07/12) agora em card CLARO creme com barras coloridas; Graf13 sem série real = null.

**R-114 `[F1]` — Continuidade de assunto**: pool de demote e de bg é por ENTIDADE (chave da desambiguacao no texto do plano), não por seção — footage/bg do produto A NUNCA ilustra o produto B, nem borrado (era a raiz do Adidas-no-NB).

**R-110 `[F1]` — Dado é quantidade medida, nunca ordinal** (QA tenis 23/07: "the number one enemy" virou Donut de 1%): no prompt do Stage 2, números idiomáticos/ordinais ("number one enemy", "rule two", countdown "number five") NÃO são estatística — estratégia nunca é `dado`. Guarda de código nos builders: `_graf_pct` exige "percent"/"%" FALADO no texto e valor >1; `_graf_uni` rejeita valor <4 sem chave de porcentagem; suffix só da whitelist curta (%, k, m, kg...) — unidade longa ("generations") vai pro título, nunca truncada no número.

## 8. Cortes ancorados no STT `[F4]` (o VidRush é tanto QUANDO corta quanto O QUE mostra)

Pré-requisito (confirmado): o Grok STT já devolve timestamps por PALAVRA — o transcriber agrupa em segments; basta persistir as words no transcript.

**R-40 — Snap de fronteira**: todo início/fim de beat snapa na fronteira de palavra do STT mais próxima (±120ms). Corte no meio de palavra é o "...in the wo" da montagem.
**R-41 — Corte na pausa**: havendo pausa do narrador (>250ms) dentro da janela de snap, o corte prefere a pausa à fronteira de palavra. Corte respirado > corte cirúrgico.
**R-42 — Respiro pós-dado**: número forte falado (o mesmo que ancora um chart) → o beat segura ≥1s após a palavra do número antes de cortar. Dado que corta em cima de si mesmo não registra.
**R-43 — Sem corte duplo**: dois cortes a <700ms um do outro só se AMBOS os beats forem energia ≥4 (rajada intencional de clímax). Fora disso, mesclar ou re-snapar.

---

## 9. Style card por job + buscas de footage `[F1]`

A maior fonte de lixo visual continua sendo o stock literalizando metáforas. O v1 combatia com exemplos no prompt; o v2 combate com DADOS versionáveis.

**R-50 — `style_card.json` por job** (Stage 1 gera, todo o pipeline consome):
```json
{
  "paleta": ["#f59e0b", "#0d1420"],
  "mood_words": ["moody", "chrome", "workshop", "vintage"],
  "assunto_ancora": "harley davidson motorcycle",
  "banned_terms": ["determination", "wisdom", "success", "journey"],
  "desambiguacao": {"Indian": "Indian CHIEF 1940s american classic"}
}
```

**R-51 — Template de query obrigatório**: `[assunto_ancora] + [substantivo visual CONCRETO] + [mood_word]`. Ex.: "vintage harley engine chrome detail moody workshop". Substantivo abstrato em query = rejeição na auditoria — por LISTA (`banned_terms`), não por exemplo em prosa de prompt.

**R-52 — estratégia `abstrato` ⇒ busca atmosférica do ASSUNTO do vídeo, JAMAIS do conceito** ("unyielding determination" → cara remando na academia; "old wisdom document" → página de Bíblia; "person listening eyes closed" → homem de headphone; "business school lecture" → estudante fazendo prova. Todos reais, todos vetados).

**R-53 — Marca ambígua passa pelo dicionário `desambiguacao` ANTES de qualquer busca** ("Indian" trouxe motos da Índia).

**R-105 `[F1]` — Ilustração REAL antes de gerada** (decisão Piter 22/07): a cascata da `peca` começa por **imagem que JÁ EXISTE na web** (diagrama de manual, figura de paper, prancha de livro — o que a IA tenta imitar): busca DDG/Bing (`imagens_web.py`) com **domínios de banco de stock BANIDOS na origem** (shutterstock/alamy/dreamstime/etc — preview watermarkado nunca) → gate Vision → **tier T3 = máscara PESADA** (frame+grid+crop interno 1.28 no Montagem). Licença desconhecida entra na régua de tier como qualquer footage. Geração por IA (T0) vira ÚLTIMO recurso. Blacklist/no-repeat por URL.

**R-54 — Vetos permanentes do gate/nicho** (inalterados): criança, talking-head/criador falando pra câmera, marca concorrente legível, screen-recording com caption, texto de review legível, watermark central, abstrato/blur. Gate Vision estrito em tudo, stock incluso (`gate_loose=False`); slots de imagem amarram a query no subject do beat.

**R-54b — O gate julga o clipe INTEIRO, não a abertura** (QA tenis 23/07: gate amostrava só os primeiros 4s; clipe de review abre com b-roll de pernas e o YouTuber fala pra câmera aos 10s+ — o beat toca QUALQUER offset do arquivo, e o talking-head vetado foi pro corte 2×): `_frames_de_video` amostra 6 frames nos centros de 6 janelas iguais da duração TOTAL (ffprobe). Um frame ruim em qualquer ponto = clipe fora. Corolário do R-105/T3: vídeo de canal de review é o candidato MAIS provável a ter talking-head escondido no meio.

**R-54c — Marca/modelo nomeado exige a marca EXATA visível** (QA tenis 23/07: Adizero da Adidas ilustrando "Hoka Bondi"): b-roll adjacente só vale pra assunto GENÉRICO; quando o subject nomeia marca/modelo, produto de outra marca = `subject_match=false` no prompt do gate.

---

## 10. Gate Vision: de porteiro a curador

**R-55 `[F-futura]` — Ranking dos aprovados**: pass/fail continua (nada reprovado passa), mas com N candidatos aprovados, o slot vai pro MELHOR, não pro primeiro: `rank = relevância ao subject do beat + nitidez/qualidade técnica`. **EMENDA 22/07 — custo REAL declarado: hoje o gate tem early-exit (para no 1º aprovado, MAX_CAND=6). Ranquear exige baixar e avaliar TODOS os candidatos ⇒ ~2-3× mais chamadas Vision e mais downloads nos beats de footage.** Não é "custo zero". Implementar quando houver folga de API — e quem re-otimizar o early-exit de volta DEVE desligar o R-55 explicitamente no log, não silenciosamente.

**R-56 `[F1]` — No-repeat de asset, com a exceção do demote**: **EMENDA 22/07** — o R-56 original ("nenhum arquivo 2× no vídeo") COLIDE com o orçamento de texto (§11): o demote-para-b-roll REUSA assets deliberadamente e é ele que segura o texto em 12%. Síntese (que também resolve a pintura estática 3× vista na decupagem do v4):
- **Imagem ESTÁTICA (jpg/png): no-repeat ABSOLUTO** — 1 aparição por vídeo, sem exceção (repetição de imagem parada é sempre perceptível).
- **VÍDEO (mp4): base é 1 aparição; o DEMOTE pode reusar até 2×**, com ≥6 beats de distância de QUALQUER aparição (movimento disfarça o reuso).

---

## 11. Balanço visual: régua COM endereço e COM janela

Alvo global (régua VidRush ajustada pelo Piter): **~45% footage · ~20% ilustração técnica · ~15-20% animação · ~20% stock**.

**R-60 `[F3]` — Janela deslizante (SOFT)**: a quota é medida em janelas de 60s, não só no total. Nenhuma janela desvia mais que ±15pp do alvo de footage. **Enforcement SOFT: desvio gera re-pick preferencial e warning — nunca hard-fail** (seção com sourcing pobre não pode travar o pipeline). 45% globais concentrados no primeiro terço passam na régua velha e matam o segundo ato — agora não passam despercebidos.

**R-61** — Enforcement declarado: quem força é o `diretor_v2_pass.py` (CADEIA imagem-antes-de-texto, `taxa_imagem 0.45`) + `montador.py` (orçamento de texto). Régua sem enforcement é aspiração, não regra.

**R-62** — Dentro das animações: imagem > texto (cadeia tenta imagem primeiro); cada variação de texto no máx. 1×; texto full-screen é raro e de impacto. **ORÇAMENTO DE TEXTO: máx. 12% do TEMPO do vídeo em texto-family** (placa discreta = meio peso); excedente vira demote (§10 R-56). Medido no Harley: 28%→12%.

**R-106 `[F1]` — DINAMISMO DUO: min 2, máx 3 por vídeo** (Piter 22/07): animações de PAR — 2 imagens (Img04/05/15/17) ou **2 vídeos** (acervo novo `duo/AcervoDuo.tsx`: Duo01_SplitVideos tela dividida · Duo02_SequentialPush um empurra o outro · Duo03_PipReveal janela flutuante). O sorteio natural conta; faltou → o montador INJETA duo de vídeo com pares do próprio job (cap/gap R-56 respeitados, sem watermark, fora do hook, dur≥4s), **espalhados ≥10 beats entre si** (mesa pegou 2 adjacentes na 1ª rodada). Auditor valida 2≤duos≤3.

**R-63** — Footage nicho TIPO A (inalterado): modelo exato, Commons vetado pra b-roll, tiers T2→T3→T1 com máscara por tier, áudio 0%, no-repeat no vídeo.

**R-64 `[F1]` — Capítulo é ESTILO do nicho, não default universal** (QA seniors 22/07: card "CHAPTER 03" a cada prática num listicle de saúde = mecânico). `style_card.chapter_style`: `cinematic` (card CHAPTER NN — documentário tipo Harley) | `minimal` (linha discreta sobre footage — listicle/saúde) | `none` (sem marcação — o beat vira comum). Ausente = cinematic.

---

## 12. QA em duas camadas: pré-checagem automática + decupagem até secar

A decupagem humana continua sendo o gate final — mas 15 beats podres passaram no HARLEY porque o olho cansou varrendo o que uma máquina pegaria de graça.

**Camada 1 `[F1]` — Pré-QA em código (`preqa.py`, roda pós-render, ANTES de qualquer olho humano):**
- **R-70** — OCR nos frames × lista de strings de default conhecidas ("SUBJECT", "HILUX", nomes de props de exemplo) + texto terminando em fragmento sem fronteira de palavra (OCR condicional à disponibilidade de engine local; sem engine, loga "R-70 indisponível" — nunca finge que checou)
- **R-71** — Detector de frame preto/estático no MEIO do beat (variância de pixel ~0; primeiro frame de entrada de texto é escuro por design — o sample é no midpoint)
- **R-72** — Diff perceptual (phash) entre os frames-medianos de todos os beats: pega duplicata que o R-56 deixou escapar por caminho novo e reuso colado
- Qualquer flag da camada 1 → beat condenado automaticamente, ANTES da decupagem humana.

**Camada 0 `[F1]` — O RENDER NUNCA É O LABORATÓRIO (a arrumação de 22/07):**
- **R-76 — Auditoria de montagem BLOQUEANTE**: `auditar_montagem.py` valida TODA regra R-xx testável sobre a montagem.json em segundos, ANTES do render. Vermelho = não renderiza. (1ª rodada real: 19 violações numa montagem que ia pro render — incluindo uma CLASSE nova de bug, o bg dos overlays repetindo assets colados, que nenhuma decupagem havia pego.)
- **R-77 — Golden tests**: `test_regras.py` guarda o bug EXATO que originou cada regra (float("15%"), 'nineteen twenty, seventeen'≠1937, ChapterTitle-de-dado, Img14 sem título, 'one day/two' ancorando...). Roda em <1s. Falhou = regressão = não renderiza. (1ª rodada pegou a duplicata de `_nums_do_texto` que SOBRESCREVIA silenciosamente o parser correto — toda a ancoragem rodou bugada por um dia inteiro sem nenhum sintoma visível no código.)
- **Fluxo obrigatório**: montador → goldens → auditoria → *só então* render → preqa → decupagem. Ciclo de correção passa de ~30 min (render+decupagem) para ~10 segundos.
- `texto_budget` por nicho no style_card (doc 0.12; instrucional denso 0.16); instrução com números pequenos ("run 1 to 3 minutes") pode ser placa — estatística (values≥2 ou núm≥10) não.

**Camada 2 — Decupagem humana (inalterada do v1):**
- **R-73** — Renderizou → `python decupar.py video.mp4` → ler TODAS as contact sheets (vídeo INTEIRO — varrer só o começo deixou 15 beats podres passarem).
- **R-74** — Cada frame ruim → mapear ao beat (timestamps da MESMA montagem renderizada) → causa raiz (busca? gate? builder? default? regra R-xx?) → corrigir a CAUSA, não o sintoma.
- **R-75** — Condenar → executor resumível refaz só esses → montador → render → decupar de novo. Repetir até secar. Só entrega o que passou na decupagem limpa.

---

## 13. Métricas de saúde do pipeline

O HARLEY custou 4 rounds e ~30 beats condenados. Sem métrica, todo job vai custar isso.

**R-80** — Alvo de saúde: <10% de beats condenados no round 1. Entre 10-15%: iterar normal. >15%: PARAR — o problema é sistêmico (regra furada, prompt do Stage 2 degradado, gate frouxo), achar a causa antes de queimar renders.

**R-81 `[F1]`** — Log por causa-raiz com ID de regra: toda condenação registra qual R-xx falhou (ou "regra inexistente" — que é o gatilho pra escrever uma nova). A regra que mais rejeita no pass é candidata a virar validação mais cedo no funil (mais barato rejeitar no builder que no render).

**R-82** — Toda regra nova nasce de decupagem: regra sem vídeo renderizado que a justifique é especulação. Ao criar, registrar o job de origem no ID.

---

## 14. Onde cada regra mora

| Regra | ID | Arquivo : função |
|---|---|---|
| LLM descreve (natureza+dados+estratégia+energia+funcao) | R-01, R-02 | `diretor.py` : prompt Stage 2 |
| Validação da curva / respiro / 4º beat | R-10–R-14 | `diretor_v2_pass.py` : pass narrativo `[F3]` |
| Hook blindado (beat 0 + primeiros 15s) | R-15, R-16 | `montador.py` : pass final (guard de hook) `[F1]` |
| Melhor cartucho / cooldown de hook / fechamento circular | R-17–R-19 | `acervo_registry.py` : `escolher()` (score) `[F2]` |
| Score determinístico | R-20–R-23 | `acervo_registry.py` : `escolher()` `[F2]` |
| Builders com validação por variação | R-20, R-30 | `acervo_registry.py` : `R[]` (builders) |
| min_dur + max_dur | R-21 | `acervo_registry.py` : `escolher()` `[F1]` |
| Pass final registry-only + fallback `componente: None` | R-31 | `montador.py` : `main()` · `executor_beats.py` : `aplicar_fallback` |
| Sem default em TSX (`return null`) | R-32 | componentes React do acervo |
| Ancoragem números por extenso | R-35–R-38 | `acervo_registry.py` : `_nums_do_texto/_anc` |
| Humanização / frase de tela / ChapterTitle | R-39a–d | `acervo_registry.py` · `montador.py` |
| Snap de corte no STT / pausa / respiro pós-dado | R-40–R-43 | `montador.py` : ajuste de fronteiras `[F4]` |
| style_card.json / sanitização de busca / banned_terms | R-50–R-53 | `style_card.json` no job · `executor_beats.py` : `_sanitizar_busca` `[F1]` |
| Vetos do gate / gate estrito | R-54 | gate Vision (`gate_loose=False`) |
| Ranking de aprovados | R-55 | gate Vision : pós-aprovação `[F-futura]` |
| No-repeat: estática 1× / vídeo 2× só via demote | R-56 | `montador.py` : `_demote_footage` `[F1]` |
| Janela deslizante (soft) + cadeia imagem + orçamento de texto | R-60–R-62 | `diretor_v2_pass.py` · `montador.py` |
| Footage TIPO A | R-63 | pipeline de footage |
| Pré-QA automático (OCR/estático/diff) | R-70–R-72 | `preqa.py` `[F1]` |
| Decupagem humana até secar | R-73–R-75 | `decupar.py` + fluxo manual |
| Métricas de saúde / log por R-xx | R-80–R-82 | logs do pass + preqa |
| Gazetteer (coords reais, nunca inventadas) | — | `acervo_registry.py` : `GAZ/_gaz` |
| Geo-validação dos mapas (atlas+continente) | — | `mapas/AcervoMapas.tsx` : `resolverPais/validarGeo` |
| Copy de assets por mtime | — | `montador.py` : `copy/_rw` |

---

## Apêndice: o que mudou do v1 → v2 (mapa rápido)

| v1 | v2 |
|---|---|
| Sorteio com peso pró-menos-usada | Score determinístico (fit + posição + novidade), seed só desempata |
| Regras 100% por beat | Camada de arco: energia, funcao_narrativa, curva validada |
| Hook sem regra | R-15–R-19 (hook blindado + fechamento circular) |
| Cooldown como veto binário | Cooldown como penalidade; única exceção deliberada: R-19 |
| min_dur só | min_dur + max_dur + composto/split para beat longo |
| Corte onde o beat caiu | Snap no STT, pausa preferida, respiro pós-dado |
| Mood em exemplo de prompt | style_card.json versionável + banned_terms por lista |
| Gate pass/fail | Gate pass/fail + ranking dos aprovados (custo real declarado) |
| Régua visual global sem endereço | Quota por janela de 60s (soft), enforcement declarado no pass |
| QA 100% olho humano | Pré-QA automático (OCR/estático/diff) + decupagem humana |
| Sem métrica | <10% condenados no round 1; log de causa-raiz por R-xx |
| Reuso de asset ad-hoc no demote | R-56: estática 1× absoluto · vídeo 2× só via demote, ≥6 beats |
