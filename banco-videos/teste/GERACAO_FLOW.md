# Geração no Flow (VEO 3.1 / Nano Banana) — manual operacional

> Para quem for **gerar imagem no Nano Banana ou vídeo no VEO**. Estado de 02/08.
> Os guias em `veo_flow/GUIA_*.md` são de SETUP (humano); este é de OPERAÇÃO.

## As duas filas que alimentam o Flow

| Arquivo | Quem escreve | Formato | Quando |
|---|---|---|---|
| `<job>/veo_lote.json` | `veo_lote.py` | `{i, tipo, arquivo, prompt, busca_original}` | canal roda em modo generativo (todo o vídeo) |
| `<job>/_gerar.json` | `curador5.py` | `{i, prompt, dest}` | buraco de curadoria: beat sem asset (02/08) |

O `veo_driver.py` consome **as duas** — `_normalizar_lote()` converte `dest`→`arquivo`
e infere `tipo` pela extensão. Não precisa transformar nada na mão.

## Modo de geração POR CANAL (style_card.json)

```json
"gen_modo":   "video" | "imagem" | "misto",
"gen_estilo": "dark stoic documentary, candlelit marble tones, anamorphic 35mm, muted contrast"
```

- **`video`** — TODO beat vira VEO (canal 100% movimento).
- **`imagem`** — TODO beat vira Nano Banana; quem dá vida é o **Ken Burns semântico
  (F4) e o parallax 2.5D (F1)** do montador. É o modo BARATO: Nano Banana = 0 créditos.
- **`misto`** (padrão) — vídeo para footage, imagem para ilustração.

`gen_estilo` é o que diferencia visualmente um canal do outro. Sem ele, o look é
derivado das `mood_words` — funciona, mas sai genérico. Vale escrever um bom por canal.

## Cadeia

```bash
# 1. lote a partir do plano (modo do style_card, ou --modo pra sobrepor)
python veo_lote.py --job <job> --plano <plano.json> [--modo imagem] [--max 8]

# 2. gerar + baixar no Flow  (SEMPRE o python do veo_venv — playwright mora lá)
"F:/Canal Dark/veo_venv/Scripts/python.exe" veo_driver.py \
    --lote <job>/veo_lote.json --out <job>/assets --tipo imagem --fila 5 --regen 1

# fila da curadoria (buracos), com os prompts passando pelo diretor de fotografia:
"F:/Canal Dark/veo_venv/Scripts/python.exe" veo_driver.py \
    --lote <job>/_gerar.json --out <job>/assets --tipo imagem \
    --dirigir "dark documentary, natural light, 35mm"

# 3. casar os arquivos gerados com os beats
python veo_ingest.py --job <job> ...
```

## O prompt NÃO é a query de busca (01/08)

`veo_prompt.dirigir()` converte o beat numa DIREÇÃO DE CENA — sujeito + ação + luz
com direção + movimento de câmera + lente, com o mood como **grading**, nunca como
objeto no quadro. Antes ia a query de stock crua, e o resultado era:

```
ancient Roman general alone in war tent. Mood: marble statue, candlelight,
ancient ruins, stormy sea, manuscript. No captions, no subtitles, ...
```
— a tenda romana pedindo "stormy sea" junto, e metade do texto em negação (modelo de
vídeo lida mal com "no X"; às vezes produz o X). Agora:
```
Medium shot of an ancient Roman general alone in a war tent, slowly pressing a
stylus into a wax tablet, oil-lamp light falling from frame left across canvas
and worn leather, anamorphic 35mm lens feel with a restrained slow dolly inward,
candlelit marble tones, muted contrast
```

⚠️ O `_gerar.json` da curadoria traz a `busca` CRUA como prompt. Para **Nano Banana**
isso funciona bem (validado pelo Piter: "stacked banana crates warehouse" saiu melhor
que o stock). Para **VEO**, passe `--dirigir "<look do canal>"`.

## Divisão imagem × vídeo (régua do Piter, 05/08)

Quem decide NÃO é o tipo narrativo do beat — é a pergunta: *o movimento simples e
legível do sujeito é a história deste plano?*

- **vídeo**: movimento próprio e SIMPLES (bote, água correndo, um animal se movendo,
  avatar falando).
- **imagem**: composição/textura/objeto/ambiente; esquemas ilustrativos e estruturas
  científicas/biológicas; mapas; e **cenas de movimento COMPLEXO** (vários agentes,
  interação rápida) — gerador de vídeo embola coreografia; still nítido + movimento
  de câmera lê melhor. Still nunca fica parado na tela (Ken Burns/parallax do montador).

Alvo: **~50/50, sem cravar** — harmonia acima de aritmética; na dúvida, imagem.
Overlays e animações de texto seguem por fora (Remotion, na montagem).
Implementação: `veo_prompt.classificar_midia` (LLM batch + fallback por verbos),
aplicada no `veo_lote` em modo misto (`--sem-reclass` desliga).

## Avatar do canal (personagem) e a VOZ ÚNICA

`style_card["avatar"] = {escopo, nome, voz, descricao, fala_intro}` — ver
`veo_personagem.py`. `escopo: canal` cria o host UMA vez e reusa em todo vídeo
(identidade); `video` cria por vídeo; `nenhum` = faceless. Registro em
`veo_flow/personagens.json`. **Na geração, basta `@Nome` no prompt** (ex.: `@Russel`).
Fluxo de criação na interface: `veo_flow/FLOW_MAP.md` › PERSONAGENS.

⚠️ **O nome do personagem existe SÓ no chip do `@`** (Piter 05/08). Nome escrito no
TEXTO do prompt dispara a política de "pessoa famosa" do Google e o take cai — no
corpo, sempre pronome. `montar_prompt_avatar` troca automaticamente. Se um take cair
na política mesmo assim, o ciclo re-tenta com variação de cauda no prompt.

**A voz não pode destoar (regra do Piter 04/08).** O avatar fala com a voz do Flow
(ex.: Iapetus) e a narração sai do Chatterbox com OUTRA voz de referência — dá duas
pessoas diferentes no mesmo vídeo. Então a voz do host vira a referência de clone:

```bash
# 1. extrai a fala do(s) take(s) do avatar, limpa e concatena (5-15s)
python veo_voz.py --clipes <take1.mp4> [take2.mp4] --canal AMZ
# 2. a narração passa a usar essa referência, não o Bill EN.MP3 genérico
#    narrar_chatterbox(texto, r"<veo_flow/vozes_ref/voz_AMZ.wav>", nome, ...)
```

⚠️ O take de REFERÊNCIA deve ser gerado com ambiente MÍNIMO ("clean voice recording,
no ambient sound"): som de rio/insetos melhora o clipe e ATRAPALHA o clone, porque o
Chatterbox aprende o ruído junto com o timbre. Um take de 8s rende ~6-7s de fala —
passa, mas 2-3 takes concatenados clonam melhor.

## COLEÇÕES — o que dá e o que NÃO dá (sondado 06/08)

| pergunta | resposta | como se sabe |
|---|---|---|
| dá pra entrar na coleção? | **sim**, clicando no card | URL `/collection/<id>` + cabeçalho na tela |
| `page.goto` na URL da coleção? | **NÃO** — o Flow redireciona pra raiz | sonda v3; `abrir_colecao` confere e cai no clique |
| dá pra GERAR dentro dela? | **sim** | a caneca de teste ficou dentro (print) |
| o que expulsa da coleção? | `garantir_modo` (popup de modelo) e `dispensar_avisos` (clicava na seta ←) | log da guarda `garantir_dentro` |
| dá pra BAIXAR só a coleção? | **NÃO EXISTE** | menu ⋮ dela = Renomear / Ver lixeira / Excluir |
| então como isolar os vídeos? | pelo **casamento** | título-de-pessoa p/ avatar, ≥3 tokens, guarda de tipo |

⚠️ O carimbo `AAAAMMDDHHMM` no nome do arquivo é a hora do **DOWNLOAD**, não da
geração — o mesmo asset sai com carimbo novo a cada rodada. Não serve pra separar
jobs (apostei nisso e estava errado).

**Ordem obrigatória:** `garantir_modo` na RAIZ → entra pela carta → envia, com
`garantir_dentro` antes de cada rajada.

## AVATAR — doutrina de identidade (05/08, paga a caro)

1. **A única prova de identidade é o log**: take vale como "do host" SÓ se o envio
   registrou `menção @Nome: chip incluído no comando`. Rosto parecido NÃO é prova —
   três clipes de "biólogo genérico de camisa de campo" passaram por Russel em
   verificação visual (minha). Take de avatar sem chip confirmado **não é enviado**
   (`enviar_prompt(exigir_mencao=True)`).
2. **Casamento de slot de avatar exige cobertura ≥0.72** (`veo_zip`). Uma ONÇA
   entrou a 0.5 no slot do host por tokens genéricos ("through/forest").
3. **Nome só no chip** — no texto vira pronome (`montar_prompt_avatar` troca) e o
   driver apaga o resíduo que o "Incluir no comando" deixa. Nome literal no prompt
   = política de "pessoa famosa" (3 recusas até achar isso).
4. **Fala: 80-90 chars / ≤16 palavras** (aprovado): 122 corta, 69 arrasta, 89 natural.
5. **Janela da ilha ≥ duração da fala**: o "frase cortada" do v1 era a ILHA (6.8s)
   cortando fala de 7.1s — o montador estende aparando o beat seguinte (footage) e,
   se for animação, desliza o início dela.
6. **Take silencioso**: áudio pedido POSITIVO ("gentle ambient sounds — birdsong,
   insects...") — negação ("does not speak") derruba o gerador de áudio.
7. Recusa de política → reenvio ganha variação de cauda automática (`_envios.json`).

## Gate no que foi gerado (`--regen N`, default 1)

Material generativo era a única coisa da pipeline que entrava **sem checagem**, embora
o modelo erre à sua maneira: escreve texto mesmo mandado não escrever, mão com seis
dedos, gente encarando a lente. Agora passa pelos **mesmos 6 frames** do footage real
(`vision_gate.gate`); reprovado é apagado, volta pro fim da fila e é **re-gerado** até
`--regen` vezes. Provado: `veo_mulher_falando.mp4` → `['talking-head']`.

⚠️ **Custo:** com `--regen 1`, um lote de 100 pode virar 200 gerações. Nano Banana é
0 crédito (não importa); VEO custa — use `--regen 0` se quiser conservador.

## Projetos do Flow (a config de modelo persiste POR PROJETO)

| Projeto | Uso | Modelo fixo |
|---|---|---|
| `3bfb56aa-8db8-44d4-b47d-532828a6b33b` | VÍDEO (job amazônia + personagem Russel) | Veo 3.1 - Lite [Lower Priority] |
| `335d7ba7-549f-4ddf-aa57-b24b976654a4` | IMAGEM | Nano Banana 2 (0 créditos) |

Separar não é organização, é **economia**: a config persiste por projeto, então um
projeto por tipo elimina a troca de seletor — o passo mais frágil do driver, que já
fez lote de VÍDEO sair como imagem e passe de IMAGEM sair como vídeo (~90 créditos
num trabalho de 0). Mesmo assim, `garantir_modo()` confere antes de CADA lote.

## O ciclo por coleção (`veo_ciclo.py`) — o fluxo ATUAL

```bash
"F:/Canal Dark/veo_venv/Scripts/python.exe" -u veo_ciclo.py     --lote <job>/veo_lote.json --out <job>/assets     --canal AMZ --colecao 05-08-26 --tipo video --fila 4
```
Por rodada: entra na coleção (rota direta pela URL registrada) → **só envia** os
prompts que faltam → espera os badges de % sumirem → **UM "Baixar coleção"** → zip →
casa por título (`veo_zip.aplicar`, cobertura ≥0.6) → gate local; reprovado é apagado
e re-gera na rodada seguinte (até `--regen`; depois vai pro curador/banco). Para com
tudo pronto ou 2 rodadas sem arquivo novo. Idempotente: quem tem arquivo nunca é
re-enviado. Elimina as ~6 interações de UI por clipe do fluxo antigo — era nelas que
o lote de 98 morria. `projetos.json` = registro canal → projeto/coleções.

## O encarregado (`veo_supervisor.py`) — fluxo antigo (por clipe)

```bash
"F:/Canal Dark/veo_venv/Scripts/python.exe" -u veo_supervisor.py     --lote <job>/veo_lote.json --out <job>/assets --tipo video     --fila 4 --paciencia 10 --proj <projeto do tipo>
```
Vigia pela contagem de arquivos NO DISCO (log de driver de browser mente: buferiza e
o processo segue "vivo" esperando um clique). Travou => mata driver+Chrome, roda
`--so-baixar` pra RESGATAR o que já foi gerado e pago, e reinicia só o que falta.
Para sozinho após 2 rodadas sem avanço (sessão/crédito/rate limit não se curam
reiniciando). Log em `<job>/_supervisor_<tipo>.log`.

## Gotchas do Flow

- **Sempre o `veo_venv`** — `playwright` não está no Python principal.
- **Login**: perfil Chrome dedicado. Se aparecer "Create with Google Flow", a sessão
  expirou: `"F:/Canal Dark/veo_venv/Scripts/python.exe" veo_flow/flow_driver.py login`.
- **Nano Banana = 0 créditos** (decisão do Piter: Together fica sem crédito de propósito).
- **Download de VÍDEO só pela rota do GRID** (hover no card → ⋮ → Baixar → 1080p). O
  botão da página de detalhe baixa o **poster jpeg** — já produziu 111 arquivos falsos.
- **Atribuição card→beat**: o driver abre `/edit/<id>` e casa o PROMPT visível com o
  item da fila. Custa 2 navegações por card — é o gargalo conhecido, ainda não atacado.
- **reCAPTCHA Enterprise ativo** no Flow: pacing humano, headful, sem rajada.
- `--so-baixar` recupera cards já gerados no projeto (se o processo morreu no meio).
