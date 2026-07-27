# Decupagem VidRush — "Why the Toyota Hilux is the World's Most Unkillable Vehicle"

Análise da gravação de tela do **editor VidRush** (projeto Hilux). 13:49 de gravação; **conteúdo real = 0:00–10:54** (narração) + outro/música. 1280×720. Fonte: `C:\Users\Piter Piter\Videos\2026-07-19 10-05-10_decup\` (55 beats detectados + `transcript_timed.txt`).

> Método: `decupar.py` (cortes de cena → contact sheets) + OpenAI Whisper (roteiro com timestamps). Cruzei os dois.

---

## 1. O QUE É — e por que tem qualidade

Documentário-explicador **faceless** de ~11 min sobre a durabilidade da Hilux. Tom institucional/jornalístico (cita muito ONU/WFP, Cruz Vermelha). **A qualidade vem 70% do ROTEIRO, 30% da edição.** O footage SERVE o roteiro — nunca o contrário.

## 2. ARQUITETURA DO ROTEIRO (a espinha)

Estrutura clássica de "video-essay" com **framework** que dá rewatchability:

| Seção | Tempo | Conteúdo | Craft |
|---|---|---|---|
| **Cold open** | 0:00–0:30 | "Jogaram de um prédio de 4 andares, afogaram no mar, atearam fogo. Ligou de primeira." → "A pergunta real é se ele MERECEU o título" | Tricolon punchy + vira PERGUNTA cética (não hype) |
| **Framework** | 0:30–2:12 | Recapitula o teste Top Gear + define **6 dimensões**: durabilidade, reparabilidade, serviceability global, sobrevivência extrema, valor de revenda, uptime | Dá ROADMAP → estrutura o vídeo todo |
| **Escala/Produção** | 2:12–3:50 | 18M unidades; hubs Tailândia/Durban/UAE | Números + geografia |
| **Frota/Humanitário** | 3:50–4:48 | WFP/Cruz Vermelha; 92% vs 84% uptime | Autoridade institucional + stat |
| **Estudos de caso** | 4:48–6:40 | John Miller (fazendeiro, 650k km), Dr. Elena Kovalev (Antártica), Coronel Abdel-Kader (Chade, 400 "technicals") | HISTÓRIAS humanas com nomes |
| **Evolução/História** | 6:41–9:12 | Geração a geração (N10→N180), engenharia conservadora | Espinha técnica cronológica |
| **Vulnerabilidades** | 9:12–10:30 | Common-rail, ECU single-point-of-failure, DPF, 4-star NCAP | BALANÇO (não é só elogio → credibilidade) |
| **Conclusão** | 10:30–10:54 | "180 mercados… simplicidade mecânica supera complexidade digital" → "engenharia se mede em décadas, não em model years" | Aforismo forte de fechamento |

**Craft que garante qualidade:** cold-open tricolon → tese cética → framework numerado → dados específicos (18M, pico 820k em 2020, 92%/84%, 130kW@3600rpm, 4-star NCAP) → personagens nomeados → deep-dive cronológico → **contraponto honesto** → aforismo final. É jornalismo, não anúncio.

## 3. PACING & DENSIDADE

- **~1.200 palavras / ~11 min = ~109 wpm** (pausado, documental — MUITO espaço pro visual respirar).
- **Detectei 55 cortes GRANDES**, mas a timeline mostra **muito mais sub-cortes** (a seção técnica no meio é a mais densa). Estimativa real: **~150–220 beats visuais**, média **3–5s**, com holds longos em hero/atmosférico.
- Regra prática: **cada frase da narração = 1–3 beats visuais**. A narração é lenta pra caber a densidade visual.

## 4. LÓGICA DE FOOTAGE — como ele ESCOLHE (o ouro)

Cada beat do roteiro vira visual por uma de 5 lógicas (confirmado no cruzamento):

1. **ENTIDADE nomeada → gráfico de entidade.** Cita Tailândia/Durban/UAE → **globo com callouts de local** (#012 @2:42, EXATO). Cita John Miller → **label de nome "JOHN"** (#024 @4:47). Cita o Coronel → **card com a citação literal** (#030 @6:16). "Hilux Evolution" → **card de capítulo** (#032 @6:41).
2. **CONCEITO/dado → animação de dados.** Stats → **line chart** (#008 @2:01), **dyno readout** (RPM/HP/Torque, #038 @8:43). Framework "6 dimensões" → lista/ícones.
3. **LITERAL → footage real do assunto.** Teste Top Gear → footage real do Top Gear (#001). Motor → engine bays. Guerra → "technicals" armadas (#028). Antártica → expedição na neve (#026).
4. **PEÇA/engenharia → ilustração técnica.** Blueprint do pickup (#005), cutaway do câmbio (#013), diagrama de manual da caixa de direção (#035/#040), feixe de molas no branco (#033), bicos injetores ×4 (#046). **Uso PESADO de diagrama técnico** — é a assinatura da seção de engenharia.
5. **ABSTRATO → stock genérico.** "Engenheiros gerenciaram a evolução" → **pessoas de terno numa mesa** (#042/#043, stock corporativo).
6. **RESPIRO → atmosférico.** Galpão no deserto (#000), árvore seca (#018), porto (#014), pôr-do-sol (#054).

## 5. ONDE ELE BUSCA (fontes → nossos tiers)

| Tipo de asset | Fonte provável | Nosso tier |
|---|---|---|
| Top Gear, crash test, field-repair, expedição, walkaround de revenda | **YouTube (Standard/copyright)** | **T3** (mascarado) |
| Fotos de gerações antigas, press/arquivo | Web/press/Commons | **T2/T3** |
| Pessoas corporativas, atmosférico (porto, deserto, pôr-do-sol) | **Stock** (Pexels/Storyblocks) | **T1** |
| Blueprint, cutaway, diagrama de manual | **Ilustração** (manual de serviço / vetor / render) | acervo/gráfico |
| Line chart, dyno, globo+callouts, cards de texto/capítulo | **Animação gerada** | acervo (nossas 54) |

**Conclusão-chave:** VidRush NÃO é 100% footage. É **~45% footage real (muito T3 mascarado) + ~20% ilustração técnica + ~15% animação de dados/mapa/texto + ~20% stock/atmosférico.** A camada de ilustração+animação (35%) é o que **reduz dependência de footage arriscado** E dá o ar "premium/documentário".

## 6. TRATAMENTOS / MÁSCARAS observados (batem com o nosso pool)

- **Frame + grid** em perspectiva (#011, #017, #021, #028, #037, #051) — MUITO usado. = nosso `framed_grid`.
- **Blur-bg-fill** (#053 pickup nítido + fundo borrado). = nosso `blur_bg_fill`.
- **Color wash** (teal #002/#013, amarelo #048, vermelho #022, dourado tail, rosa #029) — mood por seção.
- **Vinheta + desaturação** (#023, #047), **partículas/embers** (tail dourado).
- **Mesmo footage, 2 tratamentos** (#050 D-4D limpo → #051 D-4D no grid) — reusa reenquadrando.
- **Doodle/sketch no grid** (#037).

## 7. O QUE ISSO MUDA PRA NÓS (calibração)

1. **Roteiro é o núcleo.** Precisamos de um pipeline de roteiro nesse nível: cold-open tricolon → tese → **framework numerado** → dados reais → personagens nomeados → deep-dive → contraponto honesto → aforismo. Sem isso, footage bom não salva.
2. **Modelo de 15 min recalibrado:** ~**1.600–1.750 palavras** (não 2.000+; pace ~109 wpm) · **~200–260 beats** · mix **≈ 45% footage / 20% ilustração técnica / 15% animação dados-mapa-texto / 20% stock-atmosférico** (revisar nosso 40/30/30 → o naco de ilustração técnica é maior do que prevíamos).
3. **Acervo prioritário:** o que a VidRush mais usa e nós temos fraco → **ilustração técnica** (blueprint/cutaway/diagrama de manial), **globo+callouts de local**, **card de capítulo**, **card de citação/fato**, **dyno/telemetria**. Vários já existem (Map*, ChapterTitle, ArticleNewsCard, charts) — falta o **diagrama técnico/cutaway**.
4. **Gate + tiers validados:** a estratégia (T3 mascarado pesado + gate Vision + ilustração pra aliviar footage) é LITERALMENTE o que a VidRush faz. Estamos no caminho certo.
5. **Máscaras:** `framed_grid` é o carro-chefe deles (usar bastante); color-wash por seção é um padrão a adicionar (wash por capítulo).
