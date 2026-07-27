# Regras de Edição por Nicho — B-roll, SFX, Música, Efeitos

> Documento-fonte pra calibrar cada nicho. Nasceu do teste "Top 5 Motos" que expôs os erros abaixo.
> Objetivo: o b-roll ILUSTRA o assunto, nunca casa palavra solta; e cada nicho tem estética própria.

---

## ⛔ PRINCÍPIO 0 — Nunca casar palavra literal (regra UNIVERSAL)

O resolver deve entender o **ASSUNTO do vídeo**, não caçar palavras da frase. Erros reais do teste de moto:

| Falou | Apareceu (ERRADO) | Devia aparecer |
|---|---|---|
| "**bike**" (= moto) | bicicleta 🚲 | a moto |
| "**horsepower**" | corrida de cavalos 🐎 | motor/aceleração da moto |
| "**run**" (= rodar/funcionar) | 2 corredores 🏃 | a moto ligando/rodando |

**Regra:** toda query de b-roll é **enquadrada pelo assunto global do vídeo**. Num vídeo de moto, todo termo ambíguo resolve PRA MOTO. A query nunca é a palavra crua — é `<assunto/produto> + <tipo de plano>`.

---

## 🎯 TIPOLOGIA DE NICHO (define a ESTRATÉGIA de footage)

### TIPO A — PRODUTO / VEÍCULO (moto, carro, caminhão, bike, peças, acessórios, gadget, tech, review)
**REGRA DE OURO: mostrar O PRODUTO ESPECÍFICO citado, em todas as formas. Variação mínima fora dele.**
- Falou **Honda Rebel 500** → TODO o b-roll daquele bloco é a **Honda Rebel 500**: parada, rodando, o motor DELA, o painel DELA, detalhes DELA, ela sendo pilotada.
- Vai mostrar o motor? **O motor dela.** Condução? **Ela sendo pilotada.** Nem que sejam imagens "aleatórias" dela — mas TÊM que ser DELA.
- ❌ Proibido: stock genérico de "moto", OUTROS modelos, semântica solta.
- **Fontes (nesta ordem):** YouTube CC (reviews/footage do modelo exato) → imagens do produto (Commons/fabricante/press) → banco por modelo. Stock genérico só como último respiro de transição.
- Cada bloco = um modelo → **trava o bloco inteiro no modelo** (por tempo/menção; não por palavra da frase).

> ⚠️ **VETAR AS IMAGENS (obrigatório).** A busca full-text do Commons/stock por "Kawasaki Ninja 400" devolve **imagens FROUXAS** — outras marcas, motos mistas, pôster de expo. No 1º build de motos, o bloco da Ninja mostrou uma Suzuki porque a pasta `ninja400/` tinha 2 intrusas. **Toda imagem de modelo passa por gate visual** (Gemini Vision "é EXATAMENTE o modelo X?" ou contact-sheet + olho) ANTES de entrar; descarta o que não for claramente o modelo. Validar só a 1ª imagem da pasta NÃO basta.

### TIPO B — DOCUMENTÁRIO / MISTÉRIO (dark, true crime, história, ciência, geopolítica, guerra)
- B-roll atmosférico **semântico** OK (névoa, rua noturna, oceano) + **mídia de entidade**: pessoa→PersonCard, lugar→mapa/satélite, caso→foto PD, dado→infográfico.

### TIPO C — REFLEXIVO (estoicismo, filosofia)
- Atmosfera (estátuas, ruínas, natureza, tempestade) + quotes. Sem mostrar "produto".

---

## 🔊 SFX — regra geral (o teste teve SFX ESTOURADO)

- SFX é **TEMPERO**: volume BAIXO, nunca estourado. Os estouros do teste (28s, 1:02) = **erro de volume**.
- Cada papel de SFX tem **teto de volume** e só entra em momento certo:
  - transição de movimento (whoosh): baixo, só em whip/slide fortes
  - glitch/static: só em fronteira de TÓPICO, baixo
  - digitação/página (ASMR): bem baixo
- **Nicho A (review):** SFX **mínimo e limpo** (talvez só um "click" leve na troca de moto). Nada de glitch pesado.

---

## 🎭 MÁSCARAS DE EDIÇÃO — footage de LICENÇA PADRÃO (YouTube não-CC) — OBRIGATÓRIO

> Footage CC dos modelos exatos NÃO existe (confirmado). Quando clipar **Standard License** do YouTube
> (áudio 100% removido — regra absoluta), TODO clipe passa por este tratamento p/ reduzir risco de Content-ID/flag.
> O 1º build de movimento (out atual) foi FULL-FRAME cru, sem máscara e com repetição → **fora destas regras; refazer**.

**Duração**
- Máx **3–5s** por clipe.

**Composição em QUADRO (nunca o vídeo inteiro / full-frame cru)**
- O clipe entra dentro de um **frame/moldura** (janela), não ocupando a tela cheia crua.

**Camadas de máscara — SEMPRE mais de uma, todas em opacidade BAIXA**
- máscara(s) de **ajuste leve** (cor/exposição/curva);
- overlay de **chiado/ruído** (static/grain);
- **faixas/scanlines**;
- qualquer outro leve por cima.
- Nunca uma camada só — combinar ≥2, todas baixa opacidade.

**Marca d'água**
- na **lateral / topo / base** → **CROP** (corta a marca);
- no **centro/meio** → **NÃO USAR** (arriscado);
- mesmo cortando, ainda aplicar as máscaras acima.

**Anti-repetição**
- **NÃO repetir o mesmo clipe** ao longo do vídeo (repetição levanta flag). Cada clipe 1× (ou espaçado ao máximo, com variação).

**Implementação (próxima sessão):** criar componente Remotion tipo `StandardClip` (moldura + ajuste + grain/scanline/chiado low-opacity + crop configurável) e refazer `integrate_broll.py` p/ (a) enquadrar, (b) aplicar máscaras, (c) crop de marca-d'água por clipe, (d) excluir clipe com marca central, (e) 1 uso por clipe (baixar mais segmentos p/ cobrir 38 cenas sem repetir).
Inventário de marca-d'água do banco atual: `rebel500_v5`=texto grande (já descartado); `cb500x_v0`=barra "SouthernHonda.com" (base→crop); `mt07_*`=selo "MotorCycleTube.net" (canto inf. dir.→crop); rebel v0-v4 / ninja / sv650 = limpos.

---

## 🛡️ FONTES / COMPLIANCE — TIERS de risco de IP (DEFINIÇÃO FECHADA, Piter 2026-07-17)

> Cada canal/formato escolhe o **TETO de tier permitido** (`fonte_compliance`). O resolver busca do tier
> mais baixo pro mais alto ATÉ o teto; **cada clipe carrega o tier REAL de onde veio** e leva a máscara
> DAQUELE tier (não a do canal). Nomenclatura: **Tier 1 = LOW = `stock`** · **Tier 2 = MEDIUM = `cc_pd`** · **Tier 3 = HIGH = `web`**.

### Classificação — como uma FONTE cai em cada tier
- **Tier 1 (LOW):** banco PRÓPRIO (filmado / gerado por IA\*) · stock livre sem atribuição (Pexels, Pixabay, Storyblocks) · **CC0 / Domínio Público VERIFICADO**. (\*IA tipo VEO = T1, mas sujeita ao ToS da ferramenta.)
- **Tier 2 (MEDIUM):** **CC-BY / CC-BY-SA** (exige crédito) · Wikimedia Commons (default) · YouTube **licença CC** · PD "provável" de arquivo/gov não 100% confirmado.
- **Tier 3 (HIGH):** **YouTube Standard License** · web sem licença clara · filme/TV/notícia com copyright · **licença desconhecida/indeterminada**.
- **🔑 REGRA DE OURO: na dúvida, SOBE o tier.** Licença indeterminada ⇒ Tier 3. Commons = T2 por default (só cai pra T1 se CC0/PD confirmado). *(A fazer: medir o VOLUME de "licença desconhecida" que apareceria — decidir se compensa o T3 ou buscar alternativa T1/T2.)*

### Download por tier
| Tier | Áudio | Cap duração | Reuso no MESMO vídeo | Marca-d'água |
|---|---|---|---|---|
| **1 LOW** | **0% (mudo)** † | sem cap | **evitar** (máx. qualidade) | — |
| **2 MEDIUM** | **0% (mudo)** | **≤ 8s** | **evitar** | crop se houver + registrar atribuição (CC-BY) |
| **3 HIGH** | **0% (mudo) — regra absoluta** | **≤ 5s (duro)** | **PROIBIDO (1 uso/clipe)** | **crop obrigatório**; marca no CENTRO ⇒ descarta o clipe |

† **Áudio 0% em TODOS os tiers por padrão** (Piter 2026-07-17): usamos **SFX próprios + trilha própria**, o áudio original NUNCA é necessário. Só rever se um dia decidirmos diferente.
- **No-repeat é GERAL** (todos os tiers) pra manter qualidade máxima — baixar +segmentos pra cobrir as cenas sem repetir. No **T3 é regra DURA**.

### Máscaras por tier — receita de composição (TODO tier tem overlay; detalhe em `VIDMATOR_ACERVO.md §5.1`)
- **Tier 1:** **full-frame** + **≥1 overlay atmosférico** (faíscas/foguinho/vagalumes/partículas/chiado leve…) + overlay de texto qnd aplicável. Nada de footage cru pelado.
- **Tier 2:** **frame blur-bg** + **2 overlays** (mix) + texto qnd aplicável + pode entrar em **animação de imagem/vídeo do catálogo**; crop se houver watermark.
- **Tier 3:** **NUNCA full-frame** → **frame menor + grid de fundo** (`framed_grid`) + **3 overlays** + texto qnd aplicável + animação do catálogo + crop + no-repeat. **⚠️ TRABALHAR PESADO AQUI + TESTAR** (prioridade: T3 não pode comprometer o canal).
- **⚖️ Balanço:** T2/T3 têm clipes curtos e sem reuso (precisam de +footage) → **compensar ilustrando com animações de dados/mapas/gráficos/texto** (acervo das 54), pra depender menos de footage arriscado. O acervo de animações é parte da compliance.

### Guardrails (valem SEMPRE, ortogonais ao tier)
1. **Áudio 0%** universal (acima).
2. **Máscara REDUZ risco, NÃO elimina.** **Ordem de busca do resolver = T2 → T3 → T1** (Piter 2026-07-17): **T2** (CC) é específico + mais limpo → 1ª escolha; **T3** (copyright, mascarado pesado) quando T2 não cobre o assunto exato; **T1** (stock) é o MAIS SEGURO mas o MAIS GENÉRICO → **fica por último (filler)**. T3 continua decisão consciente de IP. *(Não é parecer jurídico — framework operacional de risco.)*
3. **🚨 CHILD SAFETY (primordial):** **nenhum clipe com criança** — exceção só se o NICHO específico exigir, e **NUNCA criança em risco/vitimada** (em hipótese alguma, nenhum canal). Vale pra clipe de footage, não só pro tema. Ver `feedback_yt_child_safety`.
4. **🚫 SÓ O OBJETO — nada de criador/pessoa falando pra câmera** (Piter 2026-07-17): rejeitar clipe com **talking-head de vlogger** (rosto de terceiro se dirigindo à câmera). Aceitar só footage **do objeto/assunto em ação** (a moto, a peça, a mão fazendo o serviço). **Exceção: entrevista de TV** (broadcast, com cara de arquivo). Motivo: rosto de 3º = muito mais identificável/atribuível (risco) + quebra o faceless. *(Achado do teste Harley: 3 clipes T3 eram YouTuber falando na loja → excluídos.)*
5. **Gate VISUAL (Vision) — OBRIGATÓRIO, não opcional** (provado no teste Harley 2026-07-17). Roda em QUALQUER tier, ANTES do asset entrar, e reprova por: **(a) relevância/assunto** (é o modelo/objeto certo? — pega stock frouxo: "battery"→scooter, "spark plug"→patente errada), **(b) child-safety** (#3), **(c) talking-head** (#4). Sem ele, entra lixo/copyright/conteúdo impróprio em qualquer tier. **Web-image scrape cru = PROIBIDO** (devolveu nudez/possíveis menores + copyright no teste).

### Implementação (motor / Diretor)
- knob **`fonte_compliance`** (`stock`|`cc_pd`|`web`) = **teto de risco** por canal → define o conjunto permitido (web={T1,T2,T3} · cc_pd={T1,T2} · stock={T1}). Exposto na aba VidMator (seção Fontes/Compliance).
- resolver busca na ordem **T2 → T3 → T1** (dentro do permitido) **até cobrir o beat** — ex.: teto `cc_pd` ⇒ T2 → T1 (pula T3). Clipe carrega o tier REAL → `StandardClip` aplica a máscara do tier.
- **MIX-ALVO da timeline (Piter 2026-07-17): ~40% vídeo · 30% imagem · 30% animação** (acervo das 54). A prioridade T2→T3→T1 vale pros **70% de footage** (vídeo+imagem); os **30% de animação** (dados/mapas/gráficos/texto) são a camada compliance-safe que reduz dependência de footage arriscado.
- **T3 ⇒ força `StandardClip`** (não há como usar T3 sem máscara).

---

## 📋 REGRAS POR NICHO

| Nicho | Tipo | Footage | SFX | Música | Efeitos | Fontes |
|---|---|---|---|---|---|---|
| **Automotivo/moto/carro** | A | **produto-locked** (o modelo, em tudo) | mínimo/limpo | rock/upbeat/energético | quase nenhum (só reveal) | impact/bold |
| **True crime** | B | foto PD do caso + stock sombrio | tensão sutil | dark bank | red/CRT seletivo | serif ou impact |
| **Estoicismo** | C | atmosfera sacra (estátua/ruína) | quase zero | gregoriano/sacro/suspense | mínimo | serif |
| **Geopolítica** | B | mapas + satélite + dados | limpo | orquestral tenso | mínimo | clean/impact |
| **Guerra** | B | arquivo + mapas c/ movimento | impacto pontual | épico | vintage seletivo | serif |
| **Ciência** | B | stock + IA + dados | limpo | wonder/cósmico | mínimo | clean |
| **Dark/mistério** | B | stock atmosférico + entidade | tensão | dark bank | CRT/wash seletivo | serif |

---

## 🛠️ COMO ISSO VIRA SISTEMA (implementação)

1. **Query com contexto (montar_timeline / resolver):** a query recebe o **assunto global** + o **produto do tópico**. Ex: em vez de `run`, gera `Honda Rebel 500 engine start` / `Honda Rebel 500 riding city`. Regra anti-literal embutida.
2. **Resolver TIPO A (produto-locked):** para nicho automotivo, prioriza **YouTube CC do modelo** + **imagens do modelo**; **suprime stock genérico** e outros modelos. O modelo vem do tópico (`topicos.py`).
3. **Preset por nicho** define: `tipo` (A/B/C), tetos de volume de SFX, banco de música, intensidade de efeito, fonte. (Hoje o `presets.json` já existe — falta o campo `tipo` e as regras de footage/SFX.)
4. **Banco de música por nicho** (como já fizemos no estoicismo): automotivo precisa de banco próprio (upbeat/rock), não o dark.

---

## ✅ CHECKLIST antes de publicar (qualquer nicho)
- [ ] B-roll ILUSTRA o assunto (nenhum keyword literal fora de contexto)?
- [ ] Nicho A: é o PRODUTO certo em todos os planos?
- [ ] SFX baixo, sem estouro?
- [ ] Música no tom do nicho?
- [ ] Nomes/números certos nos overlays (não usar transcrição crua do whisper p/ modelos)?

> 🤖 **AUTOMATIZAR como passo de QA (inspirado no "Double-checking content" do VidRush).** O Director deve
> **assistir o próprio vídeo antes de publicar**: `decupar.py` fatia o MP4 renderizado em frames/contact-sheets →
> Vision roda este checklist por bloco (assunto/modelo casa? marca-d'água no centro? SFX estourado? CTA presente?
> nome/número certo? clipe repetido?) e **falha ruidoso ANTES da entrega**. Foi a falta disso que deixou passar
> Suzuki no bloco da Ninja + marca-d'água + SFX no vídeo de motos (conferido na mão só depois). Candidato a
> `verificar.py` na pipeline, logo após o render.
