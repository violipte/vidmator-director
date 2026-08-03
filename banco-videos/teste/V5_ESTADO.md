# VidMator v5 — ESTADO COMPLETO (31/07/2026)

> Doc de continuidade. A v5 está **COMPLETA (F1-F6), testada e commitada**
> (commits `91fb259..3d86d27`+). Rollback total: tag git **`v4-estavel`**.

## Isolamento (inegociável — pedido do Piter)
- v5 = SÓ arquivos novos: `*5.py` em `banco-videos/teste/` + `remotion/src/compositions/v5/`
  + composição **`Montagem5`** (registro ADITIVO no `Root.tsx`, único toque compartilhado)
  + `_render_v5base.mjs` (template; driver clona trocando "v5base" pelo job).
- v1-v4 INTOCADAS e rodáveis a qualquer momento. NÃO editar `montador.py`/`Montagem.tsx`
  pra features v5 — sempre nos forks `montador5.py`/`Montagem5.tsx`.

## Cadeia v5 (como rodar)
```
python curador5.py --job <dir> --plano <plano.json> [--workers 4] [--resume]
python rodar_producao5.py --job <dir> --plano <plano.json> --audio <mp3> --nome <job>_mont
```
`rodar_producao5` = montador5 → goldens → auditor → NVENC<5% → ÁUDIO (WAV, passada única
via `mjs --audio`) → blocos de vídeo (checkpoint em `out/_<job>/blocos/blkNN.mp4`, pula
prontos) → normalize cfr30 `-an` → concat `-c:v copy` → mux AAC → cópia protegida.
Job v5 = style_card `"estilo": "v5"` (superset do v2: audio_plan/fx/mascote/avatar herdados).

## Features (todas validadas em render no job `_job_v5teste`)
| F | O quê | Onde | Como liga |
|---|---|---|---|
| F1 | Parallax 2.5D (fundo/meio/frente, 14 movimentos, overscan, esteira infinita) | `Parallax3Scene5.tsx` + `parallax5.py` | beat `{"tipo":"parallax","props":{fundo,meio,frente,mov,tam,pos,posv,velbg,velinout}}` |
| F2 | Transições VIVAS (fade/slidePush/blurCut — saída anima por cima do entrante) + blocos | `TransOutWrap` no Montagem5 + montador5 (blocos ~2 seções, fronteira = corte seco) | automático no estilo v5 |
| F3 | 10 imageEffects CSS (grades tealOrange/duotone/silver/warm/cold/vignette + filmGrain/lightLeak/glowPulse/flashBurst) | `ImageEffects5.tsx` | montador5: grade por seção c/ rotação; lightLeak hook, glowPulse final |
| F4 | Ken Burns semântico (11 tipos) | `KenBurnsPro5.tsx` | montador5 escolhe por natureza da busca (produto/epoca/acao/paisagem/generico) |
| F5 | Karaokê word-by-word | `Karaoke5.tsx` | style_card `{"karaoke": true}` (timing proporcional por beat) |
| F6 | Footage novo | `fontes5.py` + `gate5.py` + `curador5.py` | automático no curador5 |

## F6 — lógica de footage (absorvida do dark-content-studio do amigo)
- **Queries estratificadas** (determinísticas): fiel / +close-up detail / +wide shot / keywords.
- **Pool multi-fonte** paralelo SEM download: vídeo = **Pexels (key nossa) + Coverr + Pixabay(dormant)**;
  imagem = **Openverse (CC, sem key) + Pixabay/Unsplash(dormant) + SearXNG(opcional via env)**.
- **gate5 batch**: 1 chamada Vision pro pool inteiro → cada candidato ganha `score` 0-10
  (régua "ilustraria esse tópico exato num documentário", threshold 8) + `vetos`
  (talking_head/child/watermark/burned_text/crash/brand — **veto ANULA o score**, proteção v4).
- Melhor ≥8 vence; **só o vencedor reivindica a URL** (perdedores liberados pro pool).
- Download + normaliza 1080p30 + dedup visual (`ex._e_dup_visual`) + `resolvido/bNNN.json`.
- **Fallback = resolver v4 intacto** (pexels/yt com todos os gates do executor).
- Provado: beat real "stormy ocean waves" → Coverr score 10 end-to-end.

## Decisões do Piter (31/07)
- Keys: **SÓ Pexels** (+Coverr que ele criou: no credentials do automator, `provedor: coverr`).
  Pixabay/Unsplash ADIADOS (providers dormentes, retornam [] sem key).
- **Together SEM créditos de propósito** — geração de imagem = **Nano Banana via Flow (0 créditos)**
  (`veo_driver.py --tipo imagem`, projeto Flow de imagens `0261804d-...`).
- T3 continua ancorado em footage REAL (real>TV>celular>stock, máscaras pesadas, áudio 0%);
  parallax = fatia de ILUSTRAÇÃO do mix; 100% VEO (v3-gen) = modo opcional à parte.

## Gotchas aprendidos
- Prompt de camada parallax: NUNCA "silhouette" (o modelo desenha silhueta literal);
  meio/frente = "on a pure solid white background, complete subject" → rembg recorta.
- `Easing` precisa estar no import do remotion no Montagem5 (fork não tinha).
- Coverr: mp4 = `https://cdn.coverr.co/videos/<base_filename>/1080p.mp4` (hits não trazem urls).
- montador main: nunca criar variável `corte` (sombreia a função `corte()`).
- Job de teste: `_job_v5teste` + `remotion/public/jobs/v5teste_mont/` (montagem manual).

## ⚠️ CORREÇÃO 31/07 (Piter) — v5 SOMA, NUNCA SUBSTITUI
Erro cometido no 1º vídeo (cobras): o `curador5` tentava o pool NOVO (stock: Pexels/
Coverr/Pixabay) ANTES da cascata v4 — resultado: stock genérico com score 8 vencia e o
**YouTube (footage REAL, carro-chefe do T3) nunca era consultado**. Saíram tênis/prédio/
diagrama no lugar de cobra. **CORRIGIDO**: ordem = cascata v4 primeiro (YouTube+gates),
fontes novas como ADIÇÃO onde o v4 não acha.
**Regra permanente:** toda feature absorvida de fora ENTRA SOMANDO à hierarquia T3
(real > TV > celular > stock). Nunca reordenar/substituir o que já funciona.
Idioma das buscas: **EN mantido** (o Google acha material de sobra em EN — validado pelo
Piter com print). O que falta é GAMA de fontes, não idioma.


## 🔧 CORREÇÕES 31/07 rodada 2 (QA Piter no vídeo de cobras) — commit 4251c14
Três causas raiz achadas e corrigidas. Montagem final: **140 beats, cobertura 100%,
26 componentes, mesa VERDE** (antes: 69 beats, 38% de cobertura, 4 componentes).

1. **ANIMAÇÕES SUMIAM DA MONTAGEM** (a mais grave). `montador5` itera sobre
   `resolvido`, mas beat de ANIMAÇÃO não passa pelo executor (não precisa de asset)
   -> as 46 animações do plano — **21 delas de TEXTO/OVERLAY, que nem imagem pedem** —
   nunca chegavam. Fix: injetar do plano logo após ler o plano (`_pi`/`_n_an`).
   Efeito: 4 -> 26 componentes, texto 4s -> 58s, 5 ChapterTitles, mapa/gráfico/quote.
2. **TELA PRETA = GAP DE TIMELINE, não beat sem asset.** O montador DESCARTA beat sem
   asset e sobra buraco de TEMPO (25 gaps / 298s = 62% do vídeo). Fix: gaps viram
   beats novos servidos pelo acervo (fatias <=6s), rodízio pelo MENOS USADO com
   contagem REAL de usos (src E bg — split/bg contam 2x) e cap do R-56.
3. **GATE julgava a FRASE, não a CENA.** Rubric reescrito: o modelo é o MONTADOR do
   documentário, recebe `{tema}` (assunto do filme) + `{desc}` (linha narrada) +
   `{ctx}`; plano que só ilustra a frase mas é estranho ao filme cai pra 3-5.
   **Agnóstico de nicho** (sem exemplo hardcoded — a regra é incidental x assunto).
   + âncora do tema em TODA query + gate de LUMINÂNCIA (clipe escuro não vai ao ar).
+ `acervo_registry._s`, `montador5` e `auditar_montagem` tolerantes a `dados` vindo
  como LISTA do LLM (estourava AttributeError no meio do pass).

## 🔧 CORREÇÕES 01/08 rodada 3 (QA do render com animações) — commit e51b5bb
Vídeo renderizado e decupado por mim. 4 defeitos que IAM AO AR:

1. **Citação assinada por pessoa INEXISTENTE.** Roteiro: "The doctor in Minas
   Gerais"; o STT ouviu **"Nasgerice"** e o diretor extraiu como entidade PESSOA →
   QuoteCard final assinado por ela. O diretor trabalha sobre a TRANSCRIÇÃO (precisa
   dela pro timing) e nome próprio é o que o STT mais erra. Fix: `acervo_registry.
   set_roteiro()` + `_autor_confiavel()` — só assina se o nome está LITERAL no
   roteiro; senão card sem assinatura. `montador5 --roteiro` (auto-detecta
   `<job>/roteiro*.txt`). ⚠️ o `roteiro_en.txt` DO JOB tinha só o hook (897 B) — o
   completo estava em `teste/`; passar `--roteiro` explícito é o certo.
2. **Os 5 ChapterTitle do "Top 5" nunca chegavam à tela** (log dizia `chapters=5`).
   A proteção "capítulo intocável" só cobria `chapter_style=minimal` (Ovl02); no
   **cinematic** o `ChapterTitle` entrava na lista de sacrifício do orçamento de
   texto — e como o corte vai do FIM pro começo, os títulos morriam primeiro.
   Protegido nos 3 pontos (demote, sweep R-109, rebalance R-62). 26 → 31 componentes.
3. **`veil_video` = a "fumaça" que o Piter reclamou.** Tocava o clipe de tinta
   INTEIRO (`dur_s` 11s) com opacity fixa 0.9 em `multiply`, começando `pico_s` (8s)
   antes do corte: o auge alinhava no corte (certo) mas SEM envelope de saída a tinta
   FICAVA — borrão preto peludo por segundos, engoliu os capítulos 01 e 04. Agora é
   wipe de **1.4s** (corte no meio), seek alinhando o auge, envelope 0→0.85→0.
4. **`limpar_disco.py` (PROD) matou o 1º render**: apagou `remotion/out` (com a pasta
   `blocos/` = checkpoint) no meio. O guard dele (`_remotion_ativo`) só olha
   `remotion/_tmp` e job v5 usa `_tmp_<job>` → produção invisível. Fix nosso:
   `rodar_producao5.heartbeat_antilimpeza()`. **PENDENTE em PROD** (aval do Piter):
   o guard deveria varrer `_tmp*`. Agrava quando F: > 85% (limpeza em LOOP).

⚠️ **A montagem NÃO é determinística** (o rodízio de bg troca 17 beats entre duas
montagens do mesmo job). Por isso existe `rodar_producao5 --sem-montar`: para patch
cirúrgico no `montagem.json` + re-render de UM bloco sem invalidar os checkpoints.

**Entregue:** `_job_cobras/cobras_final.mp4` (495s, 140 beats, 31 componentes,
70 clipes distintos, preqa 6 flags R-72 = 3%). Versões anteriores guardadas no job
(`cobras_v1_sem_capitulos.mp4`, `cobras_v2_veu_ruim.mp4`) para comparação.

### O que ainda incomoda (próxima frente)
- 4 clipes com 3+ usos e ~4 planos estranhos ao tema: falta MATERIAL, não regra.
  Ampliar a gama (SearXNG self-hosted + yt-dlp em TikTok/Instagram/Facebook) é o
  próximo passo real — nicho local (fauna BR) vive nessas fontes.
- Preferir IMAGEM boa a VÍDEO ruim: hoje o beat de vídeo com nota baixa ganha do
  slot de imagem que ilustraria melhor. Deve virar regra no curador.

## 🔎 PESQUISADOR (01/08) — o que ESTÁ e o que NÃO está funcionando
| Fonte | Busca | Baixa | Obs |
|---|---|---|---|
| `web_img` (ddgs, imagem) | ✅ | ✅ | **maior ganho**: traz reptile-database/snakeradar/sciencephoto (nicho local) |
| `web_video` (ddgs → yt-dlp) | ✅ | ✅ | backend "videos" do ddgs cai → fallback `site:youtube.com` |
| TikTok | ✅ | ✅ | end-to-end provado (1 aprovado + 1 barrado pelo gate) |
| Instagram | ⚠️ | ⚠️ | só `/reel/` e `/tv/` (o `/p/` é foto); raro na busca |
| Facebook | ✅ | ❌ | yt-dlp não baixa (login) |
| SearXNG self-hosted | ❌ | — | Docker não sobe: sockets órfãos no kernel, **precisa reboot**. Já deixei `EnableDockerAI=false` (era ele que travava). O `ddgs` cobre o papel enquanto isso. |

**Regras que valem pro material web/social:** gate PESADO obrigatório (6 frames pela
duração inteira, nunca o thumb — talking-head só aparece depois do 1º frame) +
`tier=3` (máscara pesada) + áudio 0% + proxy do pool (não queimar IP).
**Idioma:** buscas gerais em EN (decisão do Piter); busca SOCIAL usa a âncora
traduzida 1x por job (`ancora_local()`) — `site:tiktok.com brazilian venomous snake`
devolve 0 posts, `jararaca cobra` devolve 18.

⚠️ **`ddgs` LEVANTA exceção** (`No results found`) em vez de devolver lista vazia, e
rate-limita: `_ddgs_tentar()` faz retry, e web/social só rodam na 1ª query do beat.
⚠️ **Luna é modelo de RACIOCÍNIO**: `max_completion_tokens` cobre reasoning + saída.
Com 60 ele pensa e devolve content VAZIO (`finish_reason=length`). Usar ≥400.

## 📚 FONTES — antes/depois (02/08) — commits 73b113d, c9b1cb7

**Como voltar atrás, do mais fino ao mais grosso:**
1. `FONTES_OFF=inaturalist,gbif python curador5.py ...` — desliga UMA fonte que
   esteja poluindo, sem reverter commit e sem perder as outras.
2. `git reset --hard v5-fontes-base` — volta ao estado ANTES de iNat/Wikimedia/
   Archive/GBIF (tag criada exatamente pra isso).
3. `git reset --hard v4-estavel` — abandona a v5 inteira.

| | ANTES (baseline: vídeo de cobras, 01/08) | DEPOIS |
|---|---|---|
| imagem | Pexels · Openverse · SearXNG · web | + **iNaturalist** · **Wikimedia** · **Archive** · **GBIF** |
| vídeo | Pexels · Coverr · YouTube · TikTok/IG/FB | (inalterado) |
| nicho local | 70 clipes distintos, **4 com 3+ usos**, diagrama de DPOC e sinapse num vídeo de cobra | a medir no próximo job |

**Baseline a bater** (vídeo `_job_cobras`, medido): 140 beats · 70 clipes distintos ·
4 com 3+ usos · 31 componentes · preqa 6 flags R-72 (3%).

### Gotchas caros desta rodada
- **iNaturalist casa qualquer coisa**: tem nome científico pra tudo. `"harley
  davidson"` trouxe *Ibatia harleyi* (uma planta) e `"venomous"` trouxe uma naja
  pelo nome popular "venomous king" — os dois iam pro vídeo. Defesa: só aceita se
  `matched_term` == termo buscado (plural tolerado) + `rank_level <= 30`. Garimpo
  da query fica **OFF** por padrão; liga com `entidades.especie` (menção pontual em
  roteiro que não é de natureza) ou `style_card.taxonomico`.
- **Wikimedia dá 403 por httpx** ("respect our robot policy") mesmo com UA
  descritivo e com UA de curl; por **urllib** responde 200 — é fingerprint do
  cliente, não IP. O provider delega pro `commons_list` do executor v4.
- **Licença por substring reprova licença boa**: `"nc"`/`"nd"` casam dentro de
  `"and"`, `"unported"`. Usar borda de palavra.
- **A alavanca de alcance é a escada taxonômica, não a licença**: espécie 183 →
  gênero 1.927 → ordem 45.258 (medido). Soltar país/research grade não muda nada.

### Decisão pendente do Piter — ShareAlike
Há **inconsistência** hoje: travei o iNaturalist em `cc0+cc-by` (SA fora, porque
ShareAlike obrigaria licenciar o vídeo inteiro como SA), mas o **Commons do v4 já
traz CC-BY-SA** há tempos (`executor_beats:111` dá T2 pra ele) — e o Wikimedia novo
herda isso. Ou aceita SA nos dois, ou exclui nos dois. Não decidi sozinho.

## Pendências / próximos passos
1. **Re-rodar o vídeo das cobras** com a ordem corrigida (job `_job_cobras` pronto:
   roteiro/narração/transcript/plano/banco 25 clipes já feitos — é só `curador5 --resume`
   depois de apagar os resolvidos de stock genérico) e validar por decupagem.
2. **Ampliar a GAMA de fontes** (pedido do Piter): ligar busca web (SearXNG self-hosted,
   grátis) e estender o yt-dlp a TikTok/Instagram/Facebook (ele suporta) — no MESMO
   batch-score, somando ao YouTube. Nicho local (fauna BR) vive nessas fontes.
3. **Buracos → banco de nicho**: montador5 deve preencher beat sem asset com clipe do
   banco (secao 900) em vez de deixar tela PRETA (metade do vídeo de cobras ficou preta).
4. **1º vídeo COMPLETO na v5** (cadeia inteira num roteiro real — estoico ou novo).
2. Diretor ainda não emite beats `parallax` (hoje só manual/montador) — integrar no
   diretor/registry quando o Piter aprovar o visual em vídeo real.
3. Karaokê: upgrade p/ word-timings reais do STT (hoje proporcional).
4. Famílias no banco (absorção do modelador do amigo, aprovada) — trocar queries_banco
   flat por 4-6 famílias com regra de estilo única (vale pro banco Pexels E pro veo_lote).
5. Tasks antigas: #22 curador_imagens, #23 animador, #24 mesa 3-funcionários.
