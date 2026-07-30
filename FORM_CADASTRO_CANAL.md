# 📋 FORMULÁRIO DE CADASTRO DE CANAL — Automator + VidMator

> ⚠️ **SUPERADO (28/07/2026):** o formulário canônico agora é a aba **Cadastro Canal** do automator
> (`http://85.239.243.215:8500/v2/cadastro-canal`) — podado pelo Piter (19 obrigatórias) e com campos novos
> (tempo do hook, estilo de abertura). Este MD ficou como rascunho histórico da 1ª versão.

> Preencha e me devolva. Com isso eu gero: coluna no grid de Temas (VPS), `templates.json` (1 template POR canal — nome único), pipeline, style_card (se VidMator), correções de pronúncia, e o checklist de debut.
> **Legenda:** 🔴 = obrigatória pro debut · ⚪ = opcional (tem default sensato — deixe em branco pra aceitar)

---

## 1. IDENTIDADE

**1.1** 🔴 Nome do canal (como aparece no YouTube):
**1.2** 🔴 Handle/@ desejado:
**1.3** 🔴 Idioma do conteúdo: `[ ] EN  [ ] PT  [ ] DE  [ ] ES  [ ] outro: ___`
**1.4** 🔴 País/público-alvo (ex.: EUA 45+, BR geral):
**1.5** 🔴 Posicionamento em 1 frase ("canal de ___ que ___ para ___"):
**1.6** ⚪ Pertence a qual rede/família de canais? (irmão de qual canal existente?):
**1.7** ⚪ Canal-modelo/referência (link de 1-3 canais que definem o alvo de qualidade):

## 2. NICHO & CONTEÚDO

**2.1** 🔴 Nicho principal:
**2.2** ⚪ Subnichos permitidos (rotação):
**2.3** 🔴 É nicho de PRODUTO/MODELO (tipo A — carros, bikes, tênis)? `[ ] sim  [ ] não`
   → se sim: b-roll travado no modelo exato (Commons vetado), regras de REGRAS_NICHOS.md aplicam.
**2.4** 🔴 Temas-semente: liste **10 títulos/temas** pra primeira leva:
**2.5** 🔴 Temas/abordagens PROIBIDOS neste canal (além do guardrail fixo de child safety, que já vale pra TODOS):
**2.6** ⚪ Autoridades/figuras citáveis do nicho (pra quotes e ilustração de pessoas):
**2.7** ⚪ Palavras/termos BANIDOS no roteiro (ex. do estoico: hustle, mindset, alpha...):

## 3. FORMATO DO VÍDEO

**3.1** 🔴 Motor de edição: `[ ] simples (automator clássico: imagens+zoom)  [ ] vidmator (edição dinâmica)  [ ] híbrido`
**3.2** 🔴 Se vidmator/híbrido — estilo: `[ ] v1 (aprovado, limpo)  [ ] v2 (trilha por momento + SFX + overlays/transitions do acervo)`
**3.3** 🔴 Tier de footage do CANAL: `[ ] T1 só stock  [ ] T2 +CC/domínio público  [ ] T3 web completo`
**3.4** 🔴 Duração-alvo do roteiro: `[ ] ~8k chars (~8-10min)  [ ] ~13k (12-15min)  [ ] ~23-26k (20-30min, alvo Luna)  [ ] outro: ___`
**3.5** ⚪ Estrutura de roteiro (default = a do nicho: TTM ensaio somático / VidRush framework numerado / doc-histórias):
**3.6** ⚪ Shorts também? `[ ] não  [ ] sim, __ por semana (fonte: cortes do long / VEO Flow)`

## 4. VOZ & NARRAÇÃO

**4.1** 🔴 Voz: `[ ] clonar voz nova (me mande ref .mp3/.wav 1-3min limpa)  [ ] usar voz existente: ___ (ex.: George, Brian)`
**4.2** 🔴 Provider: `[ ] chatterbox (local, pool)  [ ] minimax_clone  [ ] inworld  [ ] ai33`
**4.3** ⚪ Ajustes: speed (default 0.95): ___ | pitch (default 0): ___
**4.4** ⚪ Palavras que o STT/narração erra no seu nicho (viram `correcoes_stt`/`substituicoes` — ex.: "epic tetus"→"Epictetus"):

## 5. VISUAL

**5.1** 🔴 Paleta (2 cores hex ou descreva o mood — ex.: dourado/pedra, teal/preto):
**5.2** ⚪ Fonte-tema: `[ ] serif (clássico/história)  [ ] sans (moderno/tech)  [ ] default do motor`
**5.3** 🔴 Fundo (motor simples): `[ ] banco de imagens — pasta/tema: ___  [ ] video loop — arquivo: ___  [ ] n/a (vidmator resolve)`
**5.4** ⚪ Legenda queimada? `[ ] sim, estilo __ (1-5)  [ ] não`
**5.5** ⚪ Estilo de thumb (referência ou descrição):
**5.6** ⚪ Marca d'água/moldura do canal? `[ ] não  [ ] sim: ___`

## 6. ÁUDIO

**6.1** 🔴 Trilha: `[ ] acervo da equipe por momento (v2, automático)  [ ] pasta fixa no Drive: ___  [ ] arquivo único: ___`
**6.2** ⚪ Volume trilha (default 0.08 v2 / padrão do template simples): ___
**6.3** ⚪ SFX/whoosh/transitions (v2)? `[ ] sim (default)  [ ] reduzido  [ ] não`

## 7. MONETIZAÇÃO & CTA

**7.1** 🔴 Tem produto/eBook pra pitch? `[ ] sim  [ ] não`
   → se sim: nome do produto: ___ | link_destino: ___
   → **se sim, o pitch é OBRIGATÓRIO em todo vídeo** (3 gates de código, falha ruidoso — padrão TTM).
**7.2** ⚪ CTA subscribe (overlay green screen): `[ ] default (30s, 8s, a cada 300s)  [ ] custom: ___  [ ] não`
**7.3** ⚪ Comentário fixado padrão (com link?):
**7.4** ⚪ Afiliados/links extras na descrição:

## 8. INFRA & CONTAS

**8.1** 🔴 Conta Google do canal: `[ ] já existe (email: ___)  [ ] preciso criar` *(criação de conta/login é contigo — eu não crio contas nem manuseio senhas; te passo o passo-a-passo do debut)*
**8.2** 🔴 Proxy: `[ ] alocar um dos 16 SOCKS5 livres (registro no Supabase)  [ ] novo proxy dedicado`
   → regra fixa: canal logado SEMPRE no seu próprio proxy.
**8.3** ⚪ OAuth de upload (drive-to-youtube) já feito? `[ ] sim  [ ] não — fazer no debut`
**8.4** 🔴 Coluna no grid de Temas: `[ ] nova coluna (posição: ___)  [ ] substituir coluna existente: ___`
**8.5** 🔴 Recebe temas do coringa? `[ ] sim — MAS só com regra de nicho própria preenchida (lição ENO: sem regra própria, clona o vizinho)  [ ] não (curadoria manual)`
   → se sim, regra de nicho (1-3 frases que definem o que É e o que NÃO É tema deste canal):

## 9. DEBUT & CADÊNCIA

**9.1** 🔴 Data-alvo do debut:
**9.2** 🔴 Vídeos prontos no lançamento: `[ ] 1  [ ] 3 (recomendado)  [ ] 5+`
**9.3** 🔴 Cadência pós-debut: `[ ] 1/dia  [ ] 3/semana  [ ] outro: ___`
**9.4** ⚪ Horário de publicação (timezone do público):
**9.5** ⚪ Descrição do canal (ou eu escrevo a partir do 1.5):
**9.6** ⚪ Playlists iniciais:

---

## O QUE EU GERO COM ISSO (não precisa preencher)

| Saída | Alimentado por |
|---|---|
| Coluna no grid (VPS `/api/temas`, MERGE) | 1.1, 8.4, 8.5 + ids abaixo |
| `templates.json` — template único do canal | 1.3, 3.x, 4.x, 5.x, 6.x, 7.x, 8.2 |
| Pipeline (etapas/ordem, Luna se espiritual) | 3.1, 3.4, 1.3 |
| style_card VidMator (paleta, desambiguação, queries_banco, banned_terms, correcoes_stt) | 2.6, 2.7, 4.4, 5.1, 5.2 |
| Regra de nicho no coringa | 8.5 |
| 10 temas na agenda + roteiros da 1ª leva | 2.4, 9.1-9.3 |
| Checklist de debut (arte, descrição, OAuth, proxy, 1º upload agendado) | 9.x, 8.x |

**Guardrails fixos que NÃO são pergunta** (valem pra todo canal): child safety absoluto (nenhum tema/clipe com criança em risco); áudio 0% em footage; identidades fictícias em social; retrato de pessoa real só com fonte nomeada; sem claims médicos "cura"; tier desconhecido ⇒ tratar como T3.
