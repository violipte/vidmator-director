# Google Flow — mapa do fluxo (VEO 3.1) para o driver Playwright

Mapeado ao vivo em 2026-07-15 (conta **Ultra**), via Chrome logado.
URL base: `https://labs.google/fx/pt/tools/flow`

## Sessão / login (crítico)
- **Reusar perfil Chrome persistente** (login manual 1x). NÃO automatizar login Google (2FA/detecção).
- Perfil: `C:\Users\Piter Piter\AppData\Local\Google\Chrome\User Data`
- Playwright: `launch_persistent_context(user_data_dir=..., channel="chrome", headless=False)`.

## Home
- URL: `/fx/pt/tools/flow`
- Projetos existentes: `a[href*="/tools/flow/project/<uuid>"]`
- Criar: botão **"Novo projeto"**.

## Editor do projeto
- URL: `/fx/pt/tools/flow/project/<projId>`
- Sidebar: Todas as mídias · Imagens · Personagens · Cenas · Ferramentas · Lixeira · Fechar
- Grid de mídia: cada item = `a[href*="/edit/<mediaId>"]`
- Barra de prompt (rodapé): textbox "O que você quer criar?" + botão "+" (anexar imagem p/ frames) + toggle "Agente" + **botão seletor de modelo** + botão **enviar (seta →)**.

## Seletor de modelo (popup) — o botão mostra o estado atual (ex. "Veo 3.1 - Fast" / "Nano Banana 2 x2")
- Abas: **Imagem** | **Vídeo**
- (Vídeo) sub-modos: **Frames** (imagem→vídeo, first/last) | **Elementos** (ingredients)
- Aspecto (vídeo): **9:16** | **16:9**
- Saídas: **1x | x2 | x3 | x4**
- Modelo (dropdown): Omni Flash · Veo 3.1 - Lite · **Veo 3.1 - Fast** · Veo 3.1 - Quality · Veo 3.1 - Lite [Lower Priority]  (todos COM áudio)
- Duração: **4s | 6s | 8s**
- Custo exibido: "A geração vai usar N créditos" — ex.: Veo 3.1 Fast · 8s · x2 = **20 créd (10/clipe)**; imagem Nano Banana = **0 créd**.
- Seletores preferidos: `role=tab[name="Vídeo"]`, `role=tab[name="16:9"]`, `role=tab[name="8s"]`, botão de modelo por texto, item de dropdown por texto "Veo 3.1 - Fast".

## Gerar
1. (1ª vez) abrir seletor → aba Vídeo → escolher modelo/aspecto/dur/saídas (persiste entre gerações).
2. Preencher o textbox do prompt.
3. Clicar a seta enviar (→).

## Conclusão da geração — CONFIRMADO (2026-07-27, 1 gen real)
- Ao enviar, surge um CARD no grid com badge de progresso **"N%"** (4% → 100%) e a seção **"Vídeos"** aparece na sidebar.
- CONCLUÍDO quando: o badge "N%" some e o card vira vídeo (thumbnail + botão play + legenda auto-gerada). O card vira `a[href*="/edit/<mediaId>"]`.
- Sinal robusto p/ Playwright: aguardar o card virar `a[href*="/edit/"]` (ou o elemento de "%" sumir). Tempo VEO 3.1 Fast 8s ≈ **1–2 min**.
- ⚠️ **reCAPTCHA Enterprise** ativo (visto na rede: `recaptcha/enterprise`) — bot-detection real, reforça o risco de ToS.

## Download de um clipe — CONFIRMADO
- **Rota A (grid):** HOVER no card → aparecem ❤️ / ↻ / **⋮** no topo-direito → clicar **⋮** → menu com item **"Baixar"** (+ Reutilizar comando, Adicionar ao cenário, Incluir no comando, Renomear, Compartilhar, Publicar no YouTube, Definir capa, Mover p/ lixeira).
  - Playwright: abrir o ⋮ e `page.get_by_role("menuitem", name="Baixar").click()` dentro de `with page.expect_download() as di:` → `di.value.save_as(dest)`.
- **Rota B (detalhe):** clicar no card → `/edit/<mediaId>` → barra superior tem **⬇️ download** também.
- O card mostra só o poster; o mp4 real carrega no play/baixar. `expect_download` é o caminho mais simples e robusto.

## Riscos / boas práticas
- ToS/detecção: pacing humano (delays), perfil real, headful, sem rajada.
- Seletores: preferir `get_by_role`/`get_by_text` + padrões de href; evitar classes hasheadas do build.
