# PENDENTES DE QA — corrigir ANTES do próximo vídeo (não regenerar o atual)

## P0-JARDIM v7 (27/07) — AINDA os 2 pontos; diagnóstico atualizado
v7 RETIDA: 1:58 "SQUARE METER" (6ª volta do canal!) e 2:28 "Before" seguem.
1. Ban de canal falhou MESMO carregado no curador ⇒ DEBUGAR o que o yt_search
   retorna de fato em e['channel']/e['uploader'] (suspeita: None em resultados de
   ytsearchN ⇒ filtro nunca casa). Fix robusto: após o DOWNLOAD, checar canal via
   yt-dlp --print channel do ID e rejeitar ali (pós-download, dado confiável).
2. Crop de caption é de UM instante (ss=2) ⇒ "Before" aparece depois. Fix: crops
   topo/rodapé em 3 instantes (2s, meio, fim) OU DEFINITIVO: pip install
   pytesseract + engine → OCR determinístico no gate e no preqa (R-70 liga).
3. Beats afetados: 36/51 (luva-estufa SQUARE METER) e crisântemos ~2:28 (b0??).
   Condenar manualmente após fix, cadeia, spot-check 1:58/2:28, entrega.

## P0-JARDIM (27/07) — 2 fixes pra fechar o vídeo (v6 RETIDA, quase limpa)
Restam SÓ 2 captions pequenas (1:58 "SQUARE METER" em luva-estufa; 2:28 "Before"
nos crisântemos). Causas EXATAS:
1. `CANAIS_BAN` só é carregado no main() do executor_beats — o CURADOR chama os
   resolvers direto e o set fica vazio ⇒ mover o load de blacklist+canais_banidos
   pra uma função `carregar_bans(job)` chamada pelos DOIS (curador já carrega a
   blacklist local; adicionar canais).
2. Vision não enxerga caption PEQUENA em frame 384px ⇒ no gate_video, além dos 6
   frames, mandar 2 CROPS ampliados das faixas topo/rodapé (onde captions vivem)
   OU instalar pytesseract e ativar o R-70 (OCR) no preqa E no gate.
Depois: re-gate batch de novo (_regate_job.py), re-cura beats 36/51 + crisântemos,
mesa, render v7, spot-check 1:58/2:28/2:51, entrega. Arquivos v6 prontos em
_job_jardim/jardim_full_v6.mp4.

## P0 — URGENTE (bikes v2 REPROVADO na minha verificação, 25/07 — NÃO ENTREGUE)
Re-cura dos 8 beats condenados substituiu lixo por lixo: CCTV de ACIDENTE de moto
(7s), OUTRA moto POV Yamaha (14s — passou APESAR da cláusula nova!), praia vazia
na seção Domane (98s), mulher de cafeteria 2× (201/221s). Só 1 gate_reject na
re-cura inteira ⇒ SUSPEITA FORTE: **gate FAIL-OPEN** quando o Vision está
indisponível/quota (gate_retry devolve "sem-resposta-vision" e o chamador aprova?).
AÇÃO: (1) auditar vision_gate.gate()/gate_retry/resolver_* — indisponível = REJEITA
(fail-closed) com log ruidoso; (2) condenar os 4 novos assets ruins (mapear em
bikes_full_v2 nos ts 5/7/14/98/201/221); (3) re-curar com gate comprovadamente
ATIVO (teste sintético antes: frame de moto TEM que ser rejeitado); (4) mesa,
render v3, decupagem completa; só entregar com o corte limpo.
Arquivo pronto (NÃO entregue): banco-videos/_job_bikes/bikes_full_v2.mp4

## Da QA do Piter no VIDMATOR_TENIS2_v1 (24/07)

**P1 — [R-115] Contador "3 rules" durante narração do "top 5" (beat 4, 14-17s).**
Causa raiz: beat MARCADOR de seção (texto == título da seção, vindo do Stage 1) passou
pelo fluxo normal e virou Graf14; o LLM mandou `number:1` (nº da seção), a âncora
rejeitou, e o fallback `_num(t)` do `_graf_uni` minerou o "3" do PRÓPRIO TÍTULO.
Fix (2 camadas):
1. Montador: beat cujo `texto_b` está em `titulos_secao` NUNCA entra em natureza de
   dado/chart — ou vira tratamento de capítulo (Ovl02/minimal) ou demote pra footage.
   O número de um título de seção não é dado (extensão do R-110).
2. R-96 estendido: checar `props.title`/`label`/`kicker` além de `props.text`
   (título de seção vazou como title do Graf14).
Golden: `_graf_uni(dados_secao, "Why Shoes Matter Now: The 3 Rules", [])` com
texto==título → o montador não pode deixar chegar no builder; auditor flagra
qualquer props contendo título de seção fora de Ovl02/ChapterTitle.

**P1b — MESMO BUG, segunda cara: card serif "Top Picks: Practical Support (5, 4, 3)"
full-screen na hora do anúncio do NB 880.** O marcador da seção 3 não veio marcado
como ChapterTitle → não entrou no ramo de capítulo → fluxo comum aceitou o título
como frase → Texto04 escuro full. FIX ÚNICO pros dois: detectar marcador por
`texto_b in titulos_secao` (independente do componente) e FORÇAR o tratamento de
capítulo do R-64 (minimal=Ovl02 sobre footage). E limpar `\s*\([\d,\s]+\)$` do
título exibido — "(5, 4, 3)" é anotação interna do roteiro, nunca vai pra tela.
Auditor: NENHUM beat fora de Ovl02/ChapterTitle pode ter título de seção em
QUALQUER prop (text/title/label/kicker).

## Estruturais já reconhecidos (fila F-B)

**P1c — terceira ocorrência do MESMO bug:** marcador da seção 4 ("Top Picks: Maximal
Cushioning & Ease (2, 1)") como card full (brackets/stamp) na hora do "Number 2, the
Hoka". Confirma: TODOS os 4 marcadores de seção do plano vazaram pro fluxo de
conteúdo — o fix do P1 resolve os 4 de uma vez. Auditor DEVE varrer todos os props.

**P2 — F-B: contexto de BLOCO no Stage 2 + executor.** Beat de busca genérica dentro
da seção de um produto precisa herdar o assunto da seção (gate com contexto: "seção
do Nimbus — rejeitar marca concorrente legível"). O fix da busca (24/07) cobriu o
POOL/bg; falta a origem (fetch do próprio beat).
CASO CONFIRMADO (QA Piter, tenis2): beat 34 (121s, seção Nimbus) reusou o arquivo do
beat 73 — clipe CNBC da fábrica da ON (logo On gigante + watermark CNBC). Dono tinha
busca genérica ⇒ assunto genérico ⇒ passou no filtro. REFINAMENTO OBRIGATÓRIO:
(a) demote/bg pra beat de PRODUTO só aceita footage do MESMO produto — genérico
NUNCA entra em seção de produto sem re-gate com contexto de marca;
(b) fetch de beat genérico DENTRO de seção de produto ganha no subject do gate:
"reject if any competing shoe brand logo is clearly legible";
(c) watermark CNBC passou sem crop — rever gate watermark em T3 news.
CASO 2 (QA Piter): seção do Bondi (~3:48) com tênis branco fashion genérico (Pexels,
"dad shoe" de mulher jovem — nem é de corrida, nem é Hoka, nem é sênior). Regra
final do P2: em seção de PRODUTO, footage genérico só entra se (i) não mostrar
NENHUM tênis identificável de outro modelo/estética conflitante OU (ii) for do
próprio produto. "Tênis visível ≠ produto da seção" = REJEITA no gate com contexto.
CASO 3 (QA Piter): o MESMO clipe On/CNBC (b073__T3__yt_73O81rxazoQ) usado 2× —
src no beat 34 + bg de overlay em outro ponto. Ação na rodada de fixes: blacklist
`73O81rxazoQ` no _job_tenis2 (mata os 2 usos) + marca fora da lista NUNCA passa.

**P3 — Timing dos marcadores de seção.** O marcador do Stage 1 entra ~2-3s ANTES da
narração da seção começar (beat 4 em 14-17s, narração da seção ~17s+). Snap do
marcador pro início REAL da primeira frase da seção (R-40/STT words).

**P4 — Gramática de anúncio forma B.** Ovl14_PillVerdict registrado mas nunca
sorteado (announce sempre usa Img21). Alternar A/B por seção pra variedade VidRush.
