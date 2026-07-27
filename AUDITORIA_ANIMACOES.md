# Auditoria de Qualidade — Animações VidMator (2026-07-17)

Auditoria **pelo código-fonte** dos 48 componentes não-mapa (mapas já refeitos, ficam fora). Nota 1–5 de qualidade visual provável. Foco pedido: imagem, vídeo, elementos, texto.

> **Legenda:** 5 = referência (produção pro) · 4 = sólido, nit pontual · 3 = funciona mas genérico · 2 = fraco · 1 = placeholder.

## 🔴 TIER 1 — REFAZER (nota 1–2, placeholder/genérico demais)
| Componente | Nota | Problema | Fix |
|---|---|---|---|
| IconLabels | 1 | EMOJI (⛽🚚🚀) é o conteúdo dominante — choca com o dark, ignora accent | SVG real (lucide/heroicons) tingido no accent via `<Img staticFile>` ou inline |
| IconGrid | 2 | Mesmo emoji dentro dos círculos (o losango animado é bom, mas o emoji mata) | Ícone SVG stroke=accent dentro de cada círculo |
| LogoFlagGrid | 2 | Não tem suporte a imagem — "logo" = disco `hsl()` com a 1ª letra. Nunca mostra marca/bandeira real | Add prop `image` + `<Img staticFile>`; disco+inicial só fallback |
| InstagramConversation | 2 | Avatar = blob de gradiente; sem timestamps, sem chrome do IG, username hardcoded | Avatar real + timestamp/"Seen" + gradiente IG + username via prop |
| CaptionTextOverlay | 2 | Legenda numa pill + 1 risquinho; sem hierarquia, sem accent, sem reveal | Split por palavras com pop-in stagger + keyword no accent |
| DisplayText | 2 | Nameplate de 1 elemento; refém total do footage atrás | Eyebrow MONO uppercase accent + reveal por letra/máscara |

## 🟡 TIER 2 — MELHORAR (nota 3, genéricas)
| Componente | Nota | Problema | Fix |
|---|---|---|---|
| GrowingBarChart | 3 | Barras chapadas, sem gridlines nem escala Y | Gradiente nas barras + gridlines + labels de valor |
| LineChart | 3 | Eixo Y sem escala/labels; sem legenda de série | Ticks no eixo Y + label na ponta de cada linha |
| BulletPointOverlay | 3 | Lista sem hierarquia (bullets iguais), sem título/keyword | Heading no topo + 1 keyword/accent por bullet |
| SingleSentenceTextSlide | 3 | 1 linha, slide-em-bloco, sem highlight interno | Reveal palavra-a-palavra + keyword no accent |
| DualImpactSentence | 3 | 2 linhas do mesmo tamanho — hierarquia nula; só fade | 2ª linha maior/bolder + reveal palavra-a-palavra |
| DateLocationOverlay | 3 | Lower-third utilitário, sem fonte de caráter | Data em MONO/typewriter + eyebrow + anim de glifos |
| TitleDescription | 3 | Card previsível, estático (só a barra enche) | Reveal por palavra no título + watermark decorativo |
| NodeHierarchy | 3 | Fotos ligadas por linha SEM rótulos → não comunica hierarquia | Rótulo nome/relação sob cada nó + N nós |
| SubjectTitleCard | 3 | Só tipografia, zero âncora visual; kicker hardcoded | Kicker via prop + retrato/textura de época ao fundo |
| MultiImageCutText | 3 | O efeito "cut text" NÃO existe (título só flutua sobre a foto) | `background-clip:text` / SVG mask — texto recorta a imagem |
| FiveTextListicle | 3 | Numeração pequena acima da foto, não o numeral gigante de listicle | Numeral 120px+ sobreposto + entrada mais espaçada |
| ArticleNewsCard | 3 | Card escuro genérico, sem cara de recorte de jornal | Papel claro + masthead/dateline + fio de coluna + halftone |

## 🟢 TIER 3 — nota 4 (sólidas, nits — batch de fixes rápidos)
NumberCountOverlay, BarChartComparison, StockChart, PieChart · OneWordCallout, CircleHighlight, PollSurveyBar, ObjectDualStat · SentenceHighlight, QuoteCard, TextReveal · ObjectTitle, CharacterKeyword · FourImageSlideshow, ThreeImageReveal, TwoImageComparison, DualImageOnGrid · PaperMovingTransparentObject, ImageCallout, ImageTextAnnotation, BeforeAfterArrow

**Nits recorrentes (fix transversal):**
- **Auto-fit/clamp de texto** — títulos/keywords estouram em strings longas (TextReveal, QuoteCard, CharacterKeyword, ObjectTitle, TitleDescription…).
- **Contraste de overlay** — texto sobre footage sem scrim escuro atrás (OneWordCallout, DisplayText, CaptionTextOverlay).
- **Bug da linha-líder** — em ImageCallout + ImageTextAnnotation a linha termina no CENTRO da caixa (a caixa tampa a ponta). Terminar na borda.
- **Ken-burns/vida** — imagens congelam após a entrada (TwoImageComparison, DualImageOnGrid, ThreeImageReveal).

## ⭐ TIER 4 — nota 5 (referência, mexer só se sobrar tempo)
PercentageBarChart · CirclePercent · PriceCallOut · ChapterTitle · CharacterCard · DetectiveBoard · SplitScreenComparison · FourImageCaptionGrid · WebsiteScreenshotReveal

---

## Achados transversais (maior alavancagem)
1. **3 casos de placeholder por emoji/inicial** (IconLabels, IconGrid, LogoFlagGrid) → precisam de **asset real** (set de ícones SVG + suporte a `image` no grid). Fix de maior impacto visual.
2. **Zero kinetic typography palavra-a-palavra** em todo o acervo — o mais perto é o sweep do SentenceHighlight. Um **helper compartilhado de reveal por palavra** levanta 6+ componentes de texto de uma vez.
3. **Assinatura repetitiva**: "1-2 blocos de texto + 1 barra accent que enche" aparece em 8/10 dos de texto → vira cara de template. Diversificar.
4. **Auto-fit de texto** compartilhado resolve overflow em ~5 componentes.

## Plano de refino (ordem)
1. **Helpers compartilhados** (maior alavancagem): `KineticText` (reveal por palavra) + `useAutoFit` (clamp de fonte) + `ScrimPlate` (fundo de proteção p/ overlay) + set de **ícones SVG** inline.
2. **Tier 1** (6 piores) — refazer com os helpers + assets reais.
3. **Tier 2** (12 genéricas) — aplicar hierarquia/kinetic/gridlines.
4. **Tier 3** (nits) — batch: auto-fit, scrim, bug da linha-líder, ken-burns.
5. Tier 4 fica como está.

> Verificação visual (render de stills) pendente de GPU livre (PROD renderizando agora). Edições de código podem começar; confirmo cada uma no render assim que a PROD liberar.
