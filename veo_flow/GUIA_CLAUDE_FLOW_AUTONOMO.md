# 🤖 Como conectar o Claude ao Google Flow pra gerar vídeos sozinho

Passo a passo pra deixar o **Claude dirigindo o Google Flow no seu navegador** — ele abre o Flow, configura, escreve os prompts, espera renderizar e baixa os clipes, **sozinho**, enquanto você olha.

> **Como funciona na real:** o Claude **enxerga a sua tela do Chrome e clica/digita como uma pessoa**, usando a extensão oficial *"Claude in Chrome"*. Ele usa a **sua sessão já logada** no Flow (você não passa senha nenhuma pra ele).
> É automação **supervisionada** (você inicia e aprova as ações), não um robô 100% solto — pra isso existe a versão com script, no fim.

---

## O que você precisa

| Item | Detalhe |
|---|---|
| **Plano Claude** | **Pro, Max, Team ou Enterprise** (não funciona no grátis nem com API key) |
| **Claude Code** | instalado no PC (é o app que orquestra) — Windows, macOS ou Linux (**WSL não**) |
| **Extensão** | *"Claude in Chrome"* (Chrome Web Store) |
| **Navegador** | Chrome, Edge, Brave, Arc, Vivaldi ou Opera (Chromium) |
| **Conta do Flow** | Google com acesso ao **Google Flow** (AI Pro ou Ultra) |

---

## Parte 1 — Conectar o Claude ao navegador (uma vez só)

### 1. Instale o Claude Code e faça login
- Instale o **Claude Code** (code.claude.com).
- **Importante:** faça login com a conta **claude.ai** (rode `/login` e escolha claude.ai).
  ⚠️ Com **API key NÃO funciona** — dá erro 403.

### 2. Instale a extensão "Claude in Chrome"
- Abra a Chrome Web Store e instale a extensão **Claude**:
  `https://chromewebstore.google.com/detail/claude/fcoeoabgfenejglbffodgkkbkcdhcgfn`
- Aceite a permissão de **ler e alterar páginas**.

### 3. Ligue a conexão do Chrome no Claude Code
No terminal:
```bash
claude --chrome
```
*(ou, dentro de uma sessão do Claude, digite `/chrome` e escolha "Enabled by default")*
- Vai aparecer um aviso único sobre permissões → **Enter** pra continuar.
- Na primeira ação no navegador, ele pede permissão pra usar o `claude-in-chrome` → **aprove**.

### 4. Confirme que conectou
- No Claude, rode **`/chrome`** → deve mostrar **Status: Enabled** e **Extension: Installed**.
- Deixe o **Chrome aberto** (se fechar o navegador ou o terminal, a conexão cai).

---

## Parte 2 — Logar no Flow

- No mesmo Chrome, abra **https://labs.google/fx/tools/flow** e faça login na conta com **AI Pro/Ultra**.
- É só. O Claude vai usar essa aba logada.

---

## Parte 3 — Mandar o Claude gerar (a instrução mágica)

Cole no Claude uma instrução assim (ajuste os prompts que quiser). **Ela já embute o truque de fazer de graça:**

> **Abra o Google Flow (labs.google/fx/tools/flow) no meu Chrome, crie um Novo projeto e gere estes clipes de vídeo:**
> 1. Aerial drone shot over misty pine mountains at golden dawn, cinematic
> 2. Slow motion ocean waves crashing on volcanic rocks at sunset, cinematic
> 3. Northern lights over a snowy forest at night, cinematic
>
> **Configuração pra cada um:** no seletor de modelo → aba Vídeo → modelo **"Veo 3.1 - Lite [Lower Priority]"** (custa 0 créditos), proporção 16:9, duração 8s, saídas 1x.
> **Dispare os 3 em sequência** (não espere um terminar; o Flow roda ~2 em paralelo). Espere cada card sair de "N%" e virar vídeo.
> **Baixe cada um** pelo menu ⋮ do card → Baixar → **"720p Tamanho original"**.

O Claude então dirige sozinho: cria o projeto, configura o modelo grátis, digita os prompts, acompanha o progresso e baixa os mp4.

### Dica: modo "Plan" pra não aprovar clique por clique
- No modo padrão (**Auto**), o Claude **pede aprovação a cada clique/digitação**.
- Pra um lote grande, use o **modo Plan**: ele mostra o plano, você aprova **uma vez**, e ele executa a sequência sem ficar perguntando.

---

## ⚠️ Ressalvas honestas (leia)

- **Termos do Google:** automatizar o site do Flow pode **violar o ToS do Google** e, no pior caso, arriscar um flag na conta. É a sua conta e o seu conteúdo — a decisão é sua, mas é bom saber. O Flow tem **detecção de bot (reCAPTCHA)** ativa.
- **CAPTCHA / login:** se aparecer um desafio, o Claude **pausa e te pede pra resolver na mão**, depois continua.
- **É supervisionado:** o Claude pode errar um clique se a interface mudar. Fique de olho, principalmente no começo.
- **Não é set-and-forget:** o navegador e o Claude Code precisam ficar abertos durante o processo.
- **Qualidade do grátis:** o "Lite" às vezes tem errinho de movimento — gere vários e fique com os bons.

---

## 🔧 Nível avançado: 100% automático (sem supervisão)

O jeito acima é o Claude **dirigindo o navegador ao vivo**. Pra rodar **sozinho, em lote, sem ninguém olhando**, o caminho é um **script Playwright** que reusa um perfil logado do Chrome — mais robusto pra volume, mas dá mais trabalho pra montar e manter (a UI do Flow muda e quebra os seletores). É o passo seguinte quando o volume justificar.

---

*Feito a partir da doc oficial do "Claude in Chrome" + testes reais no Google Flow (2026). Use com responsabilidade na sua própria conta. 🎥*
