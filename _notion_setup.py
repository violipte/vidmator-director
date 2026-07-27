"""
Notion setup para o projeto Video Automator.
Cria subpagina no Hub "Canal Dark - Hub Claude" + linha na database "Projetos".
"""
import json
import os
import sys
import urllib.request
import urllib.error

NOTION_TOKEN = os.environ.get("NOTION_TOKEN", "")  # exporte NOTION_TOKEN — nunca hardcode (Push Protection 27/07)
HUB_PAGE_ID = "353770cb-b8de-807a-9bb8-f333596477f5"
PROJECTS_DB_ID = "353770cb-b8de-81b7-aa75-d7ecba25a2a3"
NOTION_VERSION = "2022-06-28"
BASE_URL = "https://api.notion.com/v1"

PROJECT_NAME = "Video Automator"
PROJECT_ICON = "🎬"
PROJECT_PATH = "F:\\Canal Dark\\Aplicativo de Edição"


def api(method: str, path: str, body: dict | None = None) -> dict:
    url = f"{BASE_URL}{path}"
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {NOTION_TOKEN}")
    req.add_header("Notion-Version", NOTION_VERSION)
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body_resp = e.read().decode("utf-8", errors="replace")
        print(f"[ERRO {e.code}] {method} {path}", file=sys.stderr)
        print(body_resp, file=sys.stderr)
        raise


# -------- helpers de blocos --------
def rt(text: str, bold: bool = False, code: bool = False, color: str = "default") -> dict:
    annotations = {"bold": bold, "code": code, "color": color}
    return {"type": "text", "text": {"content": text}, "annotations": annotations}


def heading_1(text: str) -> dict:
    return {"object": "block", "type": "heading_1",
            "heading_1": {"rich_text": [rt(text, bold=True)]}}


def heading_2(text: str) -> dict:
    return {"object": "block", "type": "heading_2",
            "heading_2": {"rich_text": [rt(text, bold=True)]}}


def heading_3(text: str) -> dict:
    return {"object": "block", "type": "heading_3",
            "heading_3": {"rich_text": [rt(text, bold=True)]}}


def paragraph(parts) -> dict:
    if isinstance(parts, str):
        parts = [rt(parts)]
    return {"object": "block", "type": "paragraph",
            "paragraph": {"rich_text": parts}}


def bullet(parts) -> dict:
    if isinstance(parts, str):
        parts = [rt(parts)]
    return {"object": "block", "type": "bulleted_list_item",
            "bulleted_list_item": {"rich_text": parts}}


def code_block(text: str, language: str = "json") -> dict:
    return {"object": "block", "type": "code",
            "code": {"rich_text": [rt(text)], "language": language}}


def divider() -> dict:
    return {"object": "block", "type": "divider", "divider": {}}


def callout(parts, emoji: str = "📌", color: str = "default_background") -> dict:
    if isinstance(parts, str):
        parts = [rt(parts)]
    return {"object": "block", "type": "callout",
            "callout": {"rich_text": parts, "icon": {"type": "emoji", "emoji": emoji},
                        "color": color}}


def kv(key: str, value: str, code: bool = False) -> dict:
    return bullet([rt(f"{key}: ", bold=True), rt(value, code=code)])


# -------- conteudo --------
def build_blocks() -> list:
    b = []

    # Callout topo
    b.append(callout(
        [
            rt("Documentacao tecnica completa esta no ", bold=True),
            rt("CLAUDE.md", code=True),
            rt(" local: "),
            rt("F:\\Canal Dark\\Aplicativo de Edição\\video-automator\\CLAUDE.md", code=True),
            rt(" (982 linhas). Esta pagina e um espelho de alto nivel pro Hub."),
        ],
        emoji="📘", color="red_background"
    ))

    # === CONTEXTO TECNICO ===
    b.append(divider())
    b.append(heading_1("Contexto Tecnico"))
    b.append(paragraph(
        "Pipeline local de producao automatizada de videos para YouTube. Substitui Adobe Premiere Pro com Python + FFmpeg. "
        "Produz 12+ videos/dia em 6+ canais (EN/DE/PT/ES) sobre conteudo espiritual (Chosen One / Starseed). "
        "Meta: automacao 100% (script -> narracao -> legenda -> render -> upload futuro)."
    ))
    b.append(heading_3("Stack"))
    b.append(bullet("Python 3.13+ com FastAPI + uvicorn (porta 8500)"))
    b.append(bullet("FFmpeg (NVENC + libx264) - assembly, mixing, subtitle burning"))
    b.append(bullet("OpenCV (cv2) - efeito Ken Burns via warpAffine subpixel"))
    b.append(bullet("faster-whisper (CUDA float16) - transcricao com fallback CPU"))
    b.append(bullet("httpx - cliente HTTP para todas APIs externas"))
    b.append(bullet("psutil + ctypes - prioridade BELOW_NORMAL pros processos FFmpeg"))

    b.append(heading_3("Arquitetura"))
    b.append(bullet([rt("Single-file SPA: ", bold=True), rt("app.py"), rt(" (~7800 linhas) serve dashboard inline (DASHBOARD_HTML string)")]))
    b.append(bullet([rt("Sem banco de dados - tudo JSON ("), rt("templates.json"), rt(", "), rt("pipelines.json"), rt(", "), rt("temas.json"), rt(", etc.)")]))
    b.append(bullet([rt("RTX 3060 local renderiza, VPS coordena (modo "), rt("REMOTE_MODE", code=True), rt(") via "), rt("render_worker.py")]))

    b.append(heading_3("Modulos principais"))
    b.append(bullet([rt("app.py", code=True), rt(" - FastAPI server + UI inline (~7800 linhas)")]))
    b.append(bullet([rt("engine.py", code=True), rt(" - Video assembly (OpenCV Ken Burns + FFmpeg, ~850 linhas)")]))
    b.append(bullet([rt("orchestrator.py", code=True), rt(" - Producao em 3 fases + loop repass (~600 linhas)")]))
    b.append(bullet([rt("scriptwriter.py", code=True), rt(" - LLM pipelines multi-step + credenciais (~680 linhas)")]))
    b.append(bullet([rt("narrator.py", code=True), rt(" - TTS via ai33.pro (ElevenLabs + Minimax) com chunking sequencial")]))
    b.append(bullet([rt("narrator_inworld.py", code=True), rt(" - Fallback TTS (Inworld) automatico em caso de falha primaria")]))
    b.append(bullet([rt("transcriber.py", code=True), rt(" + "), rt("_whisper_subprocess.py", code=True), rt(" - Whisper isolado (crash protection)")]))
    b.append(bullet([rt("render_queue.py", code=True), rt(" - Fila compartilhada auto+manual (1 worker, NVENC limit)")]))
    b.append(bullet([rt("render_worker.py", code=True), rt(" - Worker GPU local que polla VPS")]))

    b.append(heading_3("Caminhos locais"))
    b.append(kv("Pasta raiz", "F:\\Canal Dark\\Aplicativo de Edição", code=True))
    b.append(kv("Codigo", "F:\\Canal Dark\\Aplicativo de Edição\\video-automator\\", code=True))
    b.append(kv("Exports", "F:\\Canal Dark\\Automator Exports\\ (Roteiros/, Narracoes/, Videos/)", code=True))
    b.append(kv("Cache Ken Burns", "video-automator\\cache\\ (.mp4 MD5-keyed)", code=True))
    b.append(kv("Logs pipelines", "video-automator\\logs\\pipeline_{id}_{timestamp}.log", code=True))

    # === CREDENCIAIS ===
    b.append(divider())
    b.append(heading_1("Credenciais & Acessos"))
    b.append(callout(
        "Todas as keys reais estao em config.json e credentials.json (ambos no .gitignore). Os valores aqui sao indicativos pra rapida consulta.",
        emoji="🔐", color="yellow_background"
    ))

    b.append(heading_3("ai33.pro (TTS + Image Gen)"))
    b.append(kv("API key", "sk_z268jlmzh5kbo6hy6hhi495ri81ph6xyi8us6il34in8o976", code=True))
    b.append(kv("Header", "xi-api-key: {api_key}", code=True))
    b.append(kv("Base TTS", "https://api.ai33.pro/v1/ (ElevenLabs) + /v1m/ (Minimax)", code=True))
    b.append(kv("Base Image", "https://api.ai33.pro/v1i/ (bytedance-seedream-4.5)", code=True))

    b.append(heading_3("LLM Providers (credentials.json)"))
    b.append(bullet([rt("Claude API", bold=True), rt(" - Anthropic ($3-15/1M tokens)")]))
    b.append(bullet([rt("Claude CLI", bold=True), rt(" - Max plan, $0 extra (~1000 Sonnet/5h) - principal pra Hooker+Developer")]))
    b.append(bullet([rt("GPT", bold=True), rt(" - OpenAI (paid)")]))
    b.append(bullet([rt("Gemini", bold=True), rt(" - Flash 2.5 free tier (500 RPD) - principal pra Amplifier/Translator")]))

    b.append(heading_3("Render Worker"))
    b.append(kv("Token", "51dd755eb34a2cbdec24917a3afbb236f8b63059e286d0d1aeb8aae633cfabb7", code=True))
    b.append(kv("Header", "Authorization: Bearer {worker_token}", code=True))
    b.append(kv("Config local", "video-automator\\worker_config.json", code=True))

    b.append(heading_3("Link Tracker (innerlink.online)"))
    b.append(kv("URL", "https://innerlink.online", code=True))
    b.append(kv("Auth", "f8thekdc", code=True))

    # === SERVIDOR DE PRODUCAO ===
    b.append(divider())
    b.append(heading_1("Servidor de Producao (VPS)"))
    b.append(kv("IP", "85.239.243.215", code=True))
    b.append(kv("SSH user", "root", code=True))
    b.append(kv("SSH cmd", "ssh root@85.239.243.215", code=True))
    b.append(heading_3("Servicos systemd"))
    b.append(bullet([rt("video-automator", code=True), rt(" - PROD na porta "), rt("8500", code=True), rt(" em "), rt("/opt/video-automator/", code=True)]))
    b.append(bullet([rt("video-automator-dev", code=True), rt(" - DEV na porta "), rt("8501", code=True), rt(" em "), rt("/opt/video-automator-dev/", code=True)]))
    b.append(heading_3("Comandos uteis"))
    b.append(code_block(
        "ssh root@85.239.243.215 systemctl status video-automator\n"
        "ssh root@85.239.243.215 systemctl restart video-automator\n"
        "ssh root@85.239.243.215 journalctl -u video-automator -f\n"
        "ssh root@85.239.243.215 curl -s http://127.0.0.1:8500/api/health",
        language="bash"
    ))

    # === DEPLOY ===
    b.append(divider())
    b.append(heading_1("Deploy"))
    b.append(paragraph([
        rt("Script: ", bold=True), rt("video-automator/deploy.sh", code=True),
        rt(" (Bash, usa scp + ssh systemctl restart)")
    ]))
    b.append(heading_3("Uso"))
    b.append(code_block(
        "# Deploy completo PROD (porta 8500)\n"
        "./deploy.sh\n\n"
        "# Deploy completo DEV (porta 8501)\n"
        "./deploy.sh dev\n\n"
        "# Deploy seletivo (so arquivos especificos)\n"
        "./deploy.sh dev app.py orchestrator.py\n\n"
        "# Default arquivos quando sem args:\n"
        "# app.py orchestrator.py scriptwriter.py narrator.py production_log.py render_queue.py subtitle_fixer.py",
        language="bash"
    ))
    b.append(callout(
        [rt("DEV roda mesmo codigo do PROD - o script edita "), rt("port=8500", code=True), rt(" -> "), rt("port=8501", code=True),
         rt(" via sed apos copiar pra /opt/video-automator-dev. Testar mudancas grandes em DEV primeiro.")],
        emoji="⚠️", color="orange_background"
    ))

    # === ENV / CONFIG ===
    b.append(divider())
    b.append(heading_1("Variaveis de Ambiente & Config"))
    b.append(paragraph([
        rt("O projeto nao usa "), rt(".env", code=True),
        rt(" - tudo via JSON files. Os principais:")
    ]))
    b.append(heading_3("config.json (app)"))
    b.append(code_block(json.dumps({
        "ai33_api_key": "sk_z268jlmzh5kbo6hy6hhi495ri81ph6xyi8us6il34in8o976",
        "supabase_url": "",
        "supabase_key": "",
        "sheets_id": "",
        "sheets_api_key": "",
        "sheets_tab": "Temas",
        "tracker_url": "https://innerlink.online",
        "tracker_auth": "f8thekdc",
        "comment_template": "",
        "render_worker_token": "51dd755eb34a2cbdec24917a3afbb236f8b63059e286d0d1aeb8aae633cfabb7"
    }, indent=2), language="json"))
    b.append(heading_3("worker_config.json (render worker local)"))
    b.append(code_block(json.dumps({
        "vps_url": "http://85.239.243.215:8500",
        "worker_token": "51dd755eb34a2cbdec24917a3afbb236f8b63059e286d0d1aeb8aae633cfabb7",
        "poll_interval": 5,
        "temp_dir": "f:/Canal Dark/Aplicativo de Edição/video-automator/temp",
        "cache_dir": "f:/Canal Dark/Aplicativo de Edição/video-automator/cache",
        "export_base": "F:/Canal Dark/Automator Exports"
    }, indent=2), language="json"))
    b.append(heading_3("Outros JSONs"))
    b.append(bullet([rt("templates.json", code=True), rt(" - configs de template (resolution, voz, moldura, CTA, etc.)")]))
    b.append(bullet([rt("pipelines.json", code=True), rt(" - definicoes de pipeline LLM multi-step")]))
    b.append(bullet([rt("credentials.json", code=True), rt(" - API keys LLM (multi key/provider)")]))
    b.append(bullet([rt("temas.json", code=True), rt(" - estado da grid de temas (canais x datas)")]))
    b.append(bullet([rt("historico.json", code=True), rt(" - historico producao (max 500 entries)")]))
    b.append(bullet([rt("production_state.json", code=True), rt(" + "), rt("estado_batch.json", code=True), rt(" - estado runtime")]))

    # === URLS ===
    b.append(divider())
    b.append(heading_1("URLs de Producao"))
    b.append(kv("PROD", "http://85.239.243.215:8500", code=True))
    b.append(kv("DEV", "http://85.239.243.215:8501", code=True))
    b.append(kv("Local", "http://localhost:8500", code=True))
    b.append(kv("Health", "http://85.239.243.215:8500/api/health", code=True))
    b.append(kv("Tracker (afiliados)", "https://innerlink.online", code=True))

    # === ENDPOINTS API ===
    b.append(divider())
    b.append(heading_1("Endpoints da API (resumo)"))
    b.append(paragraph("Lista completa em CLAUDE.md secao 'API Endpoints Reference'. Principais:"))
    b.append(heading_3("Templates"))
    b.append(bullet([rt("GET/POST/PUT/DELETE ", code=True), rt("/api/templates", code=True)]))
    b.append(heading_3("Producao"))
    b.append(bullet([rt("POST ", code=True), rt("/api/produce", code=True), rt(" - producao individual (transcribe + fix + render)")]))
    b.append(bullet([rt("POST ", code=True), rt("/api/batch", code=True), rt(" + "), rt("GET /api/batch/status", code=True)]))
    b.append(bullet([rt("GET ", code=True), rt("/api/producao-completa/status", code=True), rt(" - poll do orchestrator")]))
    b.append(heading_3("Pipelines / Roteiros"))
    b.append(bullet([rt("POST ", code=True), rt("/api/pipelines/{id}/executar", code=True)]))
    b.append(bullet([rt("POST ", code=True), rt("/api/pipelines/testar-etapa", code=True), rt(" + "), rt("/testar-cadeia", code=True)]))
    b.append(heading_3("Narracao"))
    b.append(bullet([rt("GET ", code=True), rt("/api/narration/voices", code=True), rt(" + "), rt("POST /api/narration/generate", code=True)]))
    b.append(heading_3("Thumbnail AI"))
    b.append(bullet([rt("POST ", code=True), rt("/api/thumbnail/ai/generate-from-template", code=True)]))
    b.append(heading_3("Render Worker (VPS <-> worker local)"))
    b.append(bullet([rt("GET ", code=True), rt("/api/render-worker/next-job", code=True), rt(" - worker polla")]))
    b.append(bullet([rt("GET ", code=True), rt("/api/render-worker/download?path=...", code=True), rt(" - baixa MP3")]))
    b.append(bullet([rt("POST ", code=True), rt("/api/render-worker/complete", code=True), rt(" - reporta fim")]))
    b.append(heading_3("Chat (Claude direto via httpx)"))
    b.append(bullet([rt("POST ", code=True), rt("/api/chat", code=True), rt(" + "), rt("/api/chat/instructions", code=True), rt(" + "), rt("/api/chat/history", code=True)]))

    # === STATUS ATUAL ===
    b.append(divider())
    b.append(heading_1("Status Atual"))
    b.append(callout(
        [rt("PRODUCAO ATIVA", bold=True), rt(" - 12+ videos/dia rodando em 6+ canais (EN/DE/PT/ES). Pipeline core estavel.")],
        emoji="✅", color="green_background"
    ))
    b.append(heading_3("Recentes (concluidos)"))
    b.append(bullet("Inworld TTS fallback automatico apos MAX_NARR_RETRIES=2 do Minimax"))
    b.append(bullet("Voice cloning Inworld - 8 vozes (Arabella, Bill, Brian, Elara, Joanne, Knightley, Scarlet, Valentino)"))
    b.append(bullet("Loop repass (REPASS_MAX=2) - re-processa datas com erro no fim do loop"))
    b.append(bullet("Whisper crash isolation via _whisper_subprocess.py (auto-fallback CPU em segfault cuDNN)"))
    b.append(bullet("Stale render job recovery (WORKER_JOB_TIMEOUT=300s)"))
    b.append(bullet("Thumbnail AI via ai33.pro /v1i (bytedance-seedream-4.5 com prompt pools)"))
    b.append(bullet("Claude CLI como provedor LLM ($0 com Max plan)"))
    b.append(bullet("Modos auto/manual separados (estados independentes, render queue compartilhada)"))

    # === BACKLOG ===
    b.append(divider())
    b.append(heading_1("Backlog"))
    b.append(paragraph([
        rt("Lista completa em "), rt("video-automator/BACKLOG.txt", code=True),
        rt(" + "), rt("BACKLOG_PESQUISA.md", code=True), rt(". Resumo:")
    ]))
    b.append(heading_3("HIGH PRIORITY"))
    b.append(bullet("Sistema de upload (YouTube API, OAuth por canal, proxy, comentarios fixados)"))
    b.append(bullet("Monitor: progresso detalhado de render (count clips, ETA)"))
    b.append(bullet("Narracoes paralelas (Etapa B)"))
    b.append(heading_3("MEDIUM PRIORITY"))
    b.append(bullet("Cloudflare Tunnel ou Tailscale para acesso remoto"))
    b.append(bullet("Notification webhooks (Telegram/Discord)"))
    b.append(bullet("Sticky grid headers (freeze coluna data + linha canal)"))
    b.append(bullet("Painel chat sem bloquear o grid"))
    b.append(heading_3("LOW / FUTURE"))
    b.append(bullet("DaVinci Resolve scripting API para render"))
    b.append(bullet("UI mobile-responsive"))
    b.append(bullet("Dashboard com estatisticas de producao"))
    b.append(bullet("Agente autonomo (monitor.py + Claude scheduled)"))

    # === DECISOES ===
    b.append(divider())
    b.append(heading_1("Decisoes Arquiteturais"))
    b.append(bullet([rt("Single-file SPA: ", bold=True), rt("UI inline em "), rt("app.py", code=True), rt(" como string Python (DASHBOARD_HTML). Sem build frontend. Trade-off: edicao mais cuidadosa do JS dentro de strings (escape de \\n).")]))
    b.append(bullet([rt("Sem DB: ", bold=True), rt("tudo JSON. Simplifica deploy/backup. Limitacoes mitigadas com lock file thread-safe ("), rt("RLock", code=True), rt(") em "), rt("production_log.py")]))
    b.append(bullet([rt("Render queue 1 worker: ", bold=True), rt("RTX 3060 limita a 2 NVENC sessions concorrentes. Render final + Ken Burns clips compartilham GPU - serializar previne OOM.")]))
    b.append(bullet([rt("Modos auto/manual separados: ", bold=True), rt("estados de narracao isolados ("), rt("estado_narracao", code=True), rt(" vs "), rt("estado_narracao_auto", code=True), rt("). Permite operacao manual durante producao automatica.")]))
    b.append(bullet([rt("Inworld como fallback: ", bold=True), rt("evita single point of failure (ai33.pro -> Inworld). Inworld e independente, nao proxy.")]))
    b.append(bullet([rt("Pre-concat de video backgrounds: ", bold=True), rt("normaliza fps + reencoda com libx264 ultrafast antes de assembly final. Resolveu OOM com 200+ inputs (era 21GB RAM).")]))
    b.append(bullet([rt("Metadata stripping: ", bold=True), rt("ffmpeg -map_metadata -1 -fflags +bitexact apos render. Remove fingerprints encoder/timestamp -> previne deteccao YouTube de automacao.")]))
    b.append(bullet([rt("Whisper em subprocess: ", bold=True), rt("CTranslate2 segfaulta em cuDNN. Isolar em subprocess preserva o worker e habilita auto-fallback CPU.")]))
    b.append(bullet([rt("Roteiro source of truth = .txt: ", bold=True), rt("orchestrator usa "), rt("Roteiros/*.txt", code=True), rt(" como unica fonte. Cache em "), rt("temas.json", code=True), rt(" nao e mais consultado como fallback.")]))

    # === HANDOFF ===
    b.append(divider())
    b.append(heading_1("Handoff"))
    b.append(paragraph([
        rt("Para retomar trabalho neste projeto: ", bold=True),
        rt("ler primeiro o "), rt("CLAUDE.md", code=True),
        rt(" local (982 linhas, exaustivo). Ele cobre arquitetura, formulas (font scaling, ease-in-out), todos endpoints, sistema de credenciais, FFmpeg pipelines, etc.")
    ]))
    b.append(heading_3("Setup minimo"))
    b.append(code_block(
        "cd \"F:\\Canal Dark\\Aplicativo de Edição\\video-automator\"\n"
        "pip install fastapi uvicorn httpx opencv-python numpy pillow psutil faster-whisper\n"
        "# Garantir FFmpeg no PATH e CUDA toolkit (faster-whisper GPU)\n"
        "python app.py  # http://localhost:8500",
        language="bash"
    ))
    b.append(heading_3("Workflow tipico"))
    b.append(bullet([rt("Editar "), rt("app.py", code=True), rt(" (backend ou JS inline) -> kill uvicorn -> "), rt("python app.py", code=True)]))
    b.append(bullet([rt("Se mudou JS: extrair pra temp file e validar "), rt("node --check temp/ck.js", code=True)]))
    b.append(bullet([rt("Deploy VPS: "), rt("./deploy.sh dev arquivo.py", code=True), rt(" -> testar -> "), rt("./deploy.sh arquivo.py", code=True)]))
    b.append(heading_3("Pegadinhas"))
    b.append(bullet([rt("JS dentro de string Python: "), rt("\\n", code=True), rt(" precisa ser "), rt("\\\\n", code=True)]))
    b.append(bullet([rt("FFmpeg priority: sempre "), rt("BELOW_NORMAL_PRIORITY_CLASS", code=True), rt(" (psutil ou ctypes fallback)")]))
    b.append(bullet([rt("Cache key inclui effect name -> mudar effect invalida cache automaticamente")]))
    b.append(bullet([rt("PlayResX/Y do ASS = resolucao real do video, nao 288 (default libass)")]))
    b.append(bullet([rt("ai33.pro: 1 narracao por vez (estado_narracao bloqueia concorrencia)")]))
    b.append(bullet([rt("Pipeline single execution: 1 pipeline por vez (estado_execucao global)")]))

    return b


def chunk_blocks(blocks: list, size: int = 90):
    for i in range(0, len(blocks), size):
        yield blocks[i:i + size]


def main():
    blocks = build_blocks()
    print(f"[*] Total de blocos a criar: {len(blocks)}", flush=True)

    # 1) Criar subpagina (apenas com primeiro chunk)
    chunks = list(chunk_blocks(blocks, 90))
    page_body = {
        "parent": {"type": "page_id", "page_id": HUB_PAGE_ID},
        "icon": {"type": "emoji", "emoji": PROJECT_ICON},
        "properties": {
            "title": [{"type": "text", "text": {"content": PROJECT_NAME}}]
        },
        "children": chunks[0],
    }
    print(f"[*] Criando subpagina '{PROJECT_NAME}' no Hub...", flush=True)
    page = api("POST", "/pages", page_body)
    page_id = page["id"]
    page_url = page["url"]
    print(f"[OK] Pagina criada: {page_url}", flush=True)

    # 2) Anexar resto dos blocos via PATCH /blocks/{id}/children
    for idx, chunk in enumerate(chunks[1:], start=2):
        print(f"[*] Anexando chunk {idx}/{len(chunks)} ({len(chunk)} blocos)...", flush=True)
        api("PATCH", f"/blocks/{page_id}/children", {"children": chunk})

    # 3) Adicionar linha na database "Projetos"
    print("[*] Adicionando linha na database 'Projetos'...", flush=True)
    db_row = {
        "parent": {"type": "database_id", "database_id": PROJECTS_DB_ID},
        "icon": {"type": "emoji", "emoji": PROJECT_ICON},
        "properties": {
            "Nome do Projeto": {
                "title": [{"type": "text", "text": {"content": PROJECT_NAME}}]
            },
            "URL Path da Pasta Raiz": {
                "rich_text": [{"type": "text", "text": {"content": PROJECT_PATH}}]
            },
            "Status": {"select": {"name": "Ativo"}},
            "Claude Responsável": {
                "rich_text": [{"type": "text", "text": {"content": "Claude Opus 4.7 (1M)"}}]
            },
            "Última Atividade": {"date": {"start": "2026-05-02"}},
            "Notion": {"url": page_url},
        },
    }
    row = api("POST", "/pages", db_row)
    print(f"[OK] Linha adicionada: {row['url']}", flush=True)

    print("\n=== RESULTADO ===")
    print(f"Subpagina: {page_url}")
    print(f"DB row:    {row['url']}")


if __name__ == "__main__":
    main()
