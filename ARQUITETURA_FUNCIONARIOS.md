# ARQUITETURA DE FUNCIONÁRIOS — pipeline em 3 passes especialistas (25/07)

Decisão do Piter (24/07, após QA do tenis2): o modelo beat-a-beat falhou em contexto.
Separar em FUNCIONÁRIOS, cada um dono de UM problema, em SEQUÊNCIA:

## Funcionário 1 — CURADOR DE IMAGENS (`curador_imagens.py`)
Roda primeiro. Visão GLOBAL do vídeo (plano + style_card + lista completa de produtos).
- Resolve TODAS as necessidades de imagem de uma vez: fotos de produto (R-111, uma
  por anúncio), ilustrações técnicas (R-105 web→IA), imagens pra collage/duo/callouts.
- Gate com contexto completo: lista dos 5 produtos, seção de cada beat, marcas banidas.
- Output: `curadoria_imagens.json` (need → arquivo aprovado) + assets no job.
- NUNCA baixa por beat isolado: agrupa por PRODUTO/ASSUNTO e distribui.

## Funcionário 2 — CURADOR DE FOOTAGE (`curador_footage.py`)
Roda segundo. Trabalha POR SEÇÃO, nunca por beat solto.
- Pra cada seção: assunto (produto ou tema), orçamento de clipes (n beats de vídeo
  + 2-3 EXCEDENTES pra bg/duo/split/reserva) e regras da seção.
- REGRA DURA de seção de produto: todo clipe mostra O produto OU é brand-neutro
  ("a shoe is visible but NOT the section's product → reject"; marca fora da lista
  do vídeo NUNCA passa, em nenhuma seção).
- Gate recebe: seção, produto da seção, lista de produtos do vídeo, vetos (talking
  head, criança, esporte errado, watermark central).
- Output: `curadoria_footage.json` (beat → arquivo + pool_excedente por seção).

## Funcionário 3 — ANIMADOR (`animador.py`, evolução do montador)
Roda por último, com o footage TRAVADO. Não baixa nada, não improvisa nada.
- Marca capítulos: beats-marcadores (texto == título de seção) SEMPRE viram o
  tratamento R-64 do nicho, com "(5, 4, 3)" limpo. Nunca entram no fluxo de conteúdo.
- Anota o footage (regra-mãe VidRush): badges/preço/número gigante/pill sobre os
  clipes correntes (Ovl11-14, Graf14-16 bg nítido).
- Animações de imagem: anúncio Img21 (foto+rank+nome), collage, callouts — com as
  imagens do Funcionário 1.
- Animações de vídeo: duos, splits (>6s → 2 planos com tratamento), transições.
- Orçamento de texto, R-109, quotas, reuso — tudo aqui, com a mesa (goldens+auditor)
  travando o render.
- Se falta material: reporta BURACO (mesa VERMELHO com o beat e o que falta) — o
  funcionário responsável roda de novo. NUNCA tapa com texto/asset aleatório.

## Por que isso mata as classes de erro da QA
- P1 (marcador de seção virando slide): o Animador é DONO dos marcadores — nunca
  chegam no fluxo de conteúdo.
- P2 (marca errada na seção): o Curador de Footage trabalha por seção com a regra
  dura — On/UA/Adidas nem entram no pool.
- Resgates/demotes cegos: substituídos por pool EXCEDENTE curado por seção.
- "Tudo junto de forma porca": animação é camada final sobre footage travado,
  como no editor do VidRush.

## Reuso do que já existe
- Busca/download/gate: `imagens_web.py`, pex_search, yt de `executor_beats.py`.
- Registry/builders/goldens/auditor/preqa/decupar: mantidos (mesa continua).
- `executor_beats.py` NÃO morre de uma vez: os curadores nascem dele (refactor).
- PENDENTES_QA.md P1-P4 ficam automaticamente cobertos pela nova arquitetura.

## Ordem de implementação
1. `curador_footage.py` (o coração — seção+regra dura+excedente)
2. `curador_imagens.py` (produtos/ilustrações/collages globais)
3. `animador.py` (montador enxuto: capítulos, anotações, animações, mesa)
4. Mesa nova: auditor ganha invariantes de seção (marca do arquivo vs seção)
5. Teste: re-produzir o top-tênis do zero com os 3 funcionários
