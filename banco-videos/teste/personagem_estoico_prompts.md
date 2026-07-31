# Personagem "The Stoic" — estátua âncora do nicho estoicismo

> **v4 = ATUAL (2026-07-03): APRESENTADOR de canto.** Conceito final do Piter: a estátua é um
> personagem dinâmico que aparece DE VEZ EM QUANDO NOS CANTOS explicando o tema, expressões
> variando conforme a narração. Busto/meio-corpo, SEM pedestal, falando com o viewer, gesto de
> explicação, 1:1 (recorte de canto). Estilo desenho (v3) mantido.
>
> WIRING FUTURO: topicos.py já dá o mood por trecho → pass escolhe a expressão + camada Remotion
> (canto inferior, pop-in/out) → avatar sincronizado à explicação. Pose #11 (apontando pro lado)
> = a chave: aponta pro card/gráfico na tela.

## PROMPT-BASE v4 (APRESENTADOR — USAR ESTA)

```
Digital illustration of a classical Greek marble statue philosopher as a TALKING presenter character,
waist-up view, no pedestal, actively explaining to the viewer with an expressive hand gesture,
mouth slightly open as if mid-sentence, engaging direct eye contact with the camera,
stylized drawing with clean linework and soft painterly shading, subtle golden accents,
plain dark charcoal background (#1b1d22), 2D illustration character design --ar 1:1
```

Character sheet p/ travar identidade: append `, character expression sheet, grid of 6 different
expressions and gestures, same character`.

## EXPRESSÕES v4 (sprite sheet do apresentador)

| # | Sufixo EN | Momento |
|---|-----------|---------|
| 1 | `, both palms open toward the viewer, explaining calmly` | explicação neutra |
| 2 | `, index finger raised, eyebrows lifted, making a key point` | ponto-chave |
| 3 | `, counting on his fingers, focused expression` | listas/passos |
| 4 | `, hand on chin, one eyebrow raised, questioning look` | pergunta retórica |
| 5 | `, wagging his finger, serious warning expression` | alerta |
| 6 | `, hand on chest, gentle approving nod` | concordância |
| 7 | `, shrugging with both hands up, wry knowing smile` | ironia/paradoxo |
| 8 | `, leaning toward the camera, hand beside his mouth, sharing a secret` | confidência |
| 9 | `, eyes wide, both hands slightly raised in revelation` | insight |
| 10 | `, finger to his lips, calm knowing look` | silêncio |
| 11 | `, pointing to the side with open hand, looking at the viewer` | apontando pro conteúdo |
| 12 | `, arms crossed, satisfied slight smile, confident nod` | conclusão |

---
> **v3 (estilo desenho aprovado, mas poses de estátua-monumento — substituída pela v4 apresentador)**
> Ilustração digital calma: linework limpo + shading suave, expressão serena, dourado sutil, fundo chumbo.
> SEM palavras dramáticas (screaming/anguish/fury = filtro de política do gerador).

## PROMPT-BASE v3 (ilustração — USAR ESTA)

```
Digital illustration of a classical Greek marble statue of a bearded stoic philosopher,
stylized drawing with clean confident linework and soft painterly shading, calm wise expression,
subtle golden accent details on the marble, dark charcoal flat background (#1b1d22),
elegant minimal composition, muted stone tones with warm highlights, 2D illustration art --ar 16:9
```

Variações de estilo (trocar 1ª linha): gravura (`Vintage engraving etching illustration of...`) |
flat (`Minimalist flat vector illustration of...`).

## POSES v3 (calmas)

| # | Sufixo EN | Momento |
|---|-----------|---------|
| 1 | `, resting his chin on his hand, thoughtful gaze` | reflexão |
| 2 | `, arms crossed, serene confident look` | disciplina |
| 3 | `, eyes closed, peaceful expression, head slightly bowed` | aceitação |
| 4 | `, looking up at falling golden leaves, quiet wonder` | amor fati |
| 5 | `, finger to his lips, calm knowing look at the viewer` | silêncio |
| 6 | `, holding a small hourglass, observing it calmly` | tempo/memento mori |
| 7 | `, writing on a scroll, focused and composed` | journaling |
| 8 | `, walking forward with a walking staff, steady pace` | jornada |
| 9 | `, holding a small lantern in the dark, warm light on his face` | sabedoria/guia |
| 10 | `, sitting cross-legged in meditation, floating golden dust` | meditação |
| 11 | `, offering an open hand to the viewer, gentle expression` | ensinar |
| 12 | `, small cracks with golden light on his shoulder, unbothered expression` | resiliência |

---
> **v2 (feedback: dramática demais + block de política — NÃO usar)**
> Avatar dinâmico = drama BARROCO (Bernini/Laocoonte): emoção intensa no rosto, close/meio-corpo,
> ângulo de câmera no prompt, sempre 1 elemento vivo (chuva/brasa/poeira/rachadura dourada).
> NUNCA corpo inteiro frontal. Ver PROMPT-BASE v2 + poses expressivas abaixo (v1 mantida no fim como referência do que NÃO fazer).

## PROMPT-BASE v2 (avatar expressivo)

```
Cinematic close-up portrait of an ancient marble statue of a bearded stoic philosopher,
INTENSELY EXPRESSIVE human face carved in weathered marble in the style of Bernini and Laocoon,
visible emotion in the eyes and brow, cracked marble skin with faint glowing golden veins (kintsugi),
floating dust particles and embers, dramatic low-angle hero shot, deep charcoal background (#1b1d22),
strong cinematic rim lighting, volumetric haze, hyper-detailed 8k, dark epic atmosphere --ar 16:9
```

## POSES v2 (emoção + câmera)

| # | Sufixo EN | Momento |
|---|-----------|---------|
| 1 | `, face contorted in silent anguish, hand gripping his own face, extreme close-up` | dor |
| 2 | `, jaw clenched in cold fury, eyes burning with restraint, tight close-up on face` | raiva controlada |
| 3 | `, single marble tear streaming down cracked cheek, eyes closed, serene grief` | perda/aceitação |
| 4 | `, roaring silently toward the sky, neck tendons straining, rain hitting the marble` | catarse/amor fati |
| 5 | `, finger pressed to lips, piercing eyes staring INTO the camera, shallow depth of field` | silêncio |
| 6 | `, head bowed in shadow, only the eyes catching light looking up at camera, menacing calm` | determinação |
| 7 | `, gripping a skull at eye level, face-to-face confrontation, profile shot` | memento mori |
| 8 | `, half face crumbling into golden fragments blown by wind, calm expression` | impermanência |
| 9 | `, screaming mid-transformation as cracks of light split the marble open` | ruptura |
| 10 | `, weathered hands clasped in front of face, brow furrowed in deep thought, over-shoulder light` | reflexão |
| 11 | `, looking down at his own trembling open hands, expression of quiet devastation` | vulnerabilidade |
| 12 | `, walking out of darkness into light, toga flowing in wind, low angle, embers trailing` | jornada |

---
# (v1 ARQUIVADA — saiu estática/catálogo; não usar)

Entradas dinâmicas do EST: UM personagem consistente (mesma estátua) em poses variadas.
Fluxo: gerar poses → pasta → `indexar_imagens.py --nicho estoicismo` → híbrido no resolver (igual banco TTM).

## PROMPT-BASE (sempre igual — identidade do personagem)

```
Ancient Greco-Roman marble statue of a bearded stoic philosopher, weathered white marble with
subtle cracks and aged patina, short curly hair and full classical beard (Marcus Aurelius style),
draped toga over one shoulder, cinematic studio lighting with strong rim light from the left,
deep charcoal black background (#1b1d22), volumetric haze, photorealistic sculpture photography,
8k detail, dramatic chiaroscuro, dark moody atmosphere --ar 16:9
```

Fundo `#1b1d22` = mesmo do cold-open typewriter (identidade visual) + recorta limpo no rembg.

## POSES (append no fim do prompt-base)

| # | Sufixo EN | Momento da narração |
|---|-----------|---------------------|
| 1 | `, seated in deep contemplation, chin resting on hand, eyes closed` | reflexão |
| 2 | `, standing tall with arms crossed, stern determined gaze` | disciplina |
| 3 | `, head bowed with both hands covering face in grief` | dor/perda |
| 4 | `, one arm raised pointing forward with authority` | comando |
| 5 | `, holding a human skull in one hand, gazing at it calmly` | memento mori |
| 6 | `, index finger raised to lips in silence gesture` | silêncio |
| 7 | `, kneeling on one knee, head down, fist on the ground` | derrota/humildade |
| 8 | `, looking up toward a beam of light, serene expression` | esperança |
| 9 | `, walking forward mid-stride through mist` | jornada |
| 10 | `, statue cracked and partially crumbling, still standing defiant` | adversidade/amor fati |
| 11 | `, hand extended open palm offering, gentle expression` | ensinar |
| 12 | `, seated writing on a scroll with a stylus, focused` | Meditações/journaling |

## Consistência
- Gerar pose 1 primeiro → usar como IMAGEM DE REFERÊNCIA (cref/seed) nas demais.
- ilustrador.py (Together gemini-3-pro-image): UA Mozilla obrigatório, 1024²→pad_169, SEM marca no prompt.
- Variações futuras: close do rosto, meio-corpo, corpo inteiro (mesma pose ×3 enquadramentos).

## Integração (pendente)
1. Poses aprovadas → gerar lote (12 poses × 3 enquadramentos = 36 imgs)
2. Pasta: F:/Canal Dark/Imagens/EST/personagem_estoico/
3. `indexar_imagens.py --nicho estoicismo "<pasta>"` → index_estoicismo_imagens.json
4. preset estoicismo: `fonte_imagens: "hibrido"` → resolver Lb-banco pega por relevância
