# SKILL DO DIRETOR — a inteligência de edição do VidMator

> Destilado das batalhas do job HARLEY (21-22/07/2026). Cada regra aqui existe porque a
> violação dela apareceu num vídeo renderizado. Onde cada regra mora no código está no §7.

---

## 1. Princípio central: o LLM DESCREVE, o código ESCOLHE

O LLM (Stage 2) **nunca escolhe componente**. Ele entrega por beat:
- **natureza** do que o trecho pede (`mapa | chart | imagem | texto_full | texto_overlay | pessoa`)
- **dados REAIS extraídos do roteiro** (números copiados literalmente, países citados, coordenadas, citações com autor)
- **estratégia** (literal | entidade | dado | peca | abstrato | atmosferico) e **busca** de footage

Quem transforma isso em animação é o **registry** (`acervo_registry.py`): sorteio por ID
dentro da natureza elegível, com seed determinística por job. Isso mata o vício do LLM de
repetir os mesmos 3 componentes e garante que TODA validação roda em código testável.

## 2. As três peneiras do sorteio (`escolher()`)

Toda variação do almoxarifado passa por três filtros, nesta ordem:

1. **Elegibilidade de DADOS (builder):** cada variação tem um builder que valida se os
   dados do beat sustentam o componente. Inválido → recusa → próxima variação.
   - Mapa: país resolvido no atlas (continente = rejeitado), coordenada real ou gazetteer
   - Chart: número **ancorado no que o narrador FALA** (ver §4)
   - Imagem: N slots preenchidos com fotos reais aprovadas no gate
   - Img14 (TitleCutout): exige palavra-título de 4-14 chars (a palavra É a arte)
2. **Elegibilidade de DURAÇÃO (`min_dur`):** card pesado não entra em beat curto.
   Chapter/mapa/chart ≥ 3s · social/séries ≥ 3.5-4s · overlay leve ≥ 1s.
   (Origem: Chapter 03 de <1s que sumia antes do texto aparecer.)
3. **Anti-repetição:** quota por vídeo (`max_uso` — assinatura 1×, comum 2×, discreta 3-4×)
   + **cooldown de vizinhança** (mesma variação nunca a <8 beats da última vez)
   + peso pró-menos-usada. O vídeo circula o almoxarifado inteiro naturalmente.

## 3. REGRA DE FERRO: nenhum default de exemplo renderiza. NUNCA.

Já vazou 3 vezes por 3 caminhos diferentes. Todos fechados:
- **Builder retorna None** sem dados completos (não "faz o possível") → re-sorteio.
- **`mapear_props` do montador MORREU** (era a fonte do "Toyota Hilux 90%/78%",
  Tehran→Dubai, "SUBJECT"). O pass final do montador re-valida TODO beat de animação
  pelo registry — inclusive fallbacks do executor, que agora emitem `componente: None`.
- **Componente TSX não pode ter default de exemplo** (o "HILUX" do Img14 era default
  hardcoded no React). Sem prop real → `return null`, e o registry nunca deixa chegar lá.

## 4. Números: só o que o narrador FALA

- Ancoragem contra o texto do STT com **números por extenso** ("forty-five percent" → 45,
  "ninety thousand" → 90.000, ano "nineteen eighty three" → 1983).
- Pontuação FECHA o número ("nineteen twenty, seventeen" = 1920 + 17, nunca 1937).
- Valor nos `dados` do LLM que não bate com o áudio = **rejeitado** (o LLM inventa
  tendências tipo `[50, 70, 90]` para "sales curved upward" — sem número no áudio, sem chart).
- Ano falado não ganha vírgula de milhar (2003, não "2,003").

## 5. Texto de tela ≠ transcrição

Texto full-screen é **frase de impacto**, não legenda do que o narrador está dizendo.
- `humanizar()`: números por extenso→dígitos, siglas soltas coladas ("w l a"→"WLA"),
  capitalização.
- `frase_de_tela()`: corte APENAS em fronteira de cláusula/sentença, 3-12 palavras;
  não coube → **recusa** (cai pra overlay curto ou outra natureza). Nunca "...in the wo".
- Último recurso (`frase_forcada`): ≤8 palavras + "...", nunca terminando em stopword.
- ChapterTitle: número = ordem real de exibição, título = Stage 1, **1 por seção**, ≥3s
  (o stretch roda DEPOIS do ajuste de sobreposição, senão o vizinho re-encolhe o card).

## 6. Buscas de footage: o assunto do NICHO, nunca o conceito

A maior fonte de lixo visual: o stock **literaliza metáforas**.
- "unyielding determination" → cara remando na academia
- "old wisdom document" → página de Bíblia
- "person listening eyes closed" → homem de headphone
- "business school lecture" → estudante fazendo prova
Regra (no prompt do Stage 2 e vigiada na auditoria): estratégia **abstrato** ⇒ busca
**atmosférica do assunto do vídeo** (assunto + mood: "vintage harley engine chrome detail
moody workshop"), JAMAIS o conceito. E:
- **Marca ambígua desambigua**: "Indian" (marca) trouxe motos da Índia → "Indian CHIEF
  1940s american classic".
- Gate Vision **estrito em tudo** (stock incluso, `gate_loose=False`); slots de imagem
  amarram a query no subject do beat.
- Vetos permanentes do gate/nicho: criança, talking-head/criador falando pra câmera,
  marca concorrente legível, screen-recording com caption, texto de review legível,
  watermark central, abstrato/blur.

## 7. Onde cada regra mora

| Regra | Arquivo : função |
|---|---|
| Sorteio ID+quota+cooldown+duração | `acervo_registry.py : escolher()` |
| Builders com validação por variação | `acervo_registry.py : R[]` (builders) |
| Ancoragem números por extenso | `acervo_registry.py : _nums_do_texto/_anc` |
| Humanização/frase de tela | `acervo_registry.py : humanizar/frase_de_tela` |
| Gazetteer (coords reais, nunca inventadas) | `acervo_registry.py : GAZ/_gaz` |
| Geo-validação dos mapas (atlas+continente) | `mapas/AcervoMapas.tsx : resolverPais/validarGeo` |
| Re-pick global + injeção de imagem | `diretor_v2_pass.py` (CADEIA imagem-antes-de-texto, taxa_imagem 0.45) |
| Pass final registry-only + Chapter + durações | `montador.py : main()` (usa texto/dados do PLANO — resolvido não carrega `texto`) |
| Copy de assets por mtime (re-gerado substitui) | `montador.py : copy/_rw` |
| Fallback sem escolha de componente | `executor_beats.py : aplicar_fallback` (`componente: None`) |
| Regra do abstrato no prompt | `diretor.py : ~linha 128` |

## 8. QA: decupagem até secar (parte do fluxo, não opcional)

1. Renderizou → `python decupar.py video.mp4` → ler TODAS as contact sheets (vídeo
   INTEIRO — varrer só o começo deixou 15 beats podres passarem).
2. Cada frame ruim → mapear ao beat (timestamps da MESMA montagem renderizada) → achar a
   **causa raiz** (busca? gate? builder? default?) → corrigir a causa, não o sintoma.
3. Condenar: deletar `resolvido/bNNN.json` + `assets/bNNN__*` → executor resumível refaz
   só esses → montador → render → **decupar de novo**. Repetir até secar.
4. Só entrega o que passou na decupagem limpa. Iterações do Harley: 4 rounds, ~30 beats.

## 9. Balanço visual (régua VidRush, ajustada pelo Piter)

- Alvo: ~45% footage · ~20% ilustração técnica · ~15-20% animação · ~20% stock.
- Dentro das animações: **imagem > texto** (cadeia tenta imagem primeiro; cada variação
  de texto no máx. 1×; texto full-screen é raro e de impacto).
- **ORÇAMENTO DE TEXTO (QA Piter 22/07): máx. 12% do TEMPO do vídeo em texto-family.**
  Placa discreta sobre footage (lower-third/tag/footnote/ticker) conta meio peso.
  Estourou o teto → o beat vira **b-roll reusado da própria seção** (asset já baixado),
  com cap 2× por asset e **≥6 beats de distância de QUALQUER aparição** (original ou
  reuso — o guard checa TODAS as posições, não a última). Medido no Harley: 28%→12%.
- Footage nicho TIPO A: modelo exato, Commons vetado pra b-roll, tiers T2→T3→T1 com
  máscara por tier, áudio 0%, no-repeat no vídeo.
