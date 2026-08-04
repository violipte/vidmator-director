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

## Avatar do canal (personagem) e a VOZ ÚNICA

`style_card["avatar"] = {escopo, nome, voz, descricao, fala_intro}` — ver
`veo_personagem.py`. `escopo: canal` cria o host UMA vez e reusa em todo vídeo
(identidade); `video` cria por vídeo; `nenhum` = faceless. Registro em
`veo_flow/personagens.json`. **Na geração, basta `@Nome` no prompt** (ex.: `@Russel`).
Fluxo de criação na interface: `veo_flow/FLOW_MAP.md` › PERSONAGENS.

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

## Gate no que foi gerado (`--regen N`, default 1)

Material generativo era a única coisa da pipeline que entrava **sem checagem**, embora
o modelo erre à sua maneira: escreve texto mesmo mandado não escrever, mão com seis
dedos, gente encarando a lente. Agora passa pelos **mesmos 6 frames** do footage real
(`vision_gate.gate`); reprovado é apagado, volta pro fim da fila e é **re-gerado** até
`--regen` vezes. Provado: `veo_mulher_falando.mp4` → `['talking-head']`.

⚠️ **Custo:** com `--regen 1`, um lote de 100 pode virar 200 gerações. Nano Banana é
0 crédito (não importa); VEO custa — use `--regen 0` se quiser conservador.

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
