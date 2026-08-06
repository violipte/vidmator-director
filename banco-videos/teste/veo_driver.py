# -*- coding: utf-8 -*-
"""VEO DRIVER DE LOTE (v3-gen, 29/07) — roda o veo_lote.json inteiro no Flow, sozinho.

Constrói sobre o veo_flow/flow_driver.py (login/projeto/config/prompt) e fecha os
dois elos que eram stub: ESPERAR conclusão e BAIXAR — com atribuição determinística:
cada card concluído é aberto em /edit/<id>, o PROMPT visível na página é casado com
o item do lote, e o download (1080p Aumentada p/ vídeo) é salvo como bNNN.mp4.

Pipeline em ondas: mantém até --fila gerações simultâneas; baixa conforme conclui.

Uso:
  "F:/Canal Dark/veo_venv/Scripts/python.exe" veo_driver.py --lote <job>/veo_lote.json \
      --out <pasta destino> [--fila 5] [--modelo "Veo 3.1 - Lite [Lower Priority]"] [--proj <id>]
"""
import argparse
import json
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "veo_flow"))
import flow_driver as fd  # noqa — login/abrir/config/prompt do outro Claude (read-only)
from playwright.sync_api import TimeoutError as PWTimeout  # noqa

sys.stdout.reconfigure(encoding="utf-8")


def _cards_edit(page):
    """hrefs dos cards concluídos no grid do projeto."""
    hrefs = set()
    for a in page.locator('a[href*="/edit/"]').all():
        h = a.get_attribute("href") or ""
        if "/edit/" in h:
            hrefs.add(h)
    return hrefs


def _cards_falha(page):
    """Cards que o Flow marcou 'Falha / Ops! Algo deu errado' (05/08, QA Piter).

    Card falhado NUNCA vira `a[href*="/edit/"]` — então o item correspondente ficava
    'em voo' pra SEMPRE e o lote inteiro parava esperando um clipe que não vem. É a
    terceira causa de travamento que achamos hoje, junto com o popup de anúncio e o
    upscale no servidor."""
    try:
        return page.get_by_text(re.compile(r"Ops!|Algo deu errado|Falha", re.I)).count()
    except Exception:
        return 0


def _limpar_falhas(page):
    """Manda os cards falhados pra lixeira: se ficam no grid, são recontados a cada
    volta e o driver acha que 'ainda tem falha nova'.

    ⚠️ 05/08: a 1ª versão varria TODOS os botões por rótulo ("lixeira|excluir") e
    clicava no **"Ver lixeira" do menu LATERAL** — o driver navegava pra /trash, onde
    não há card nenhum, e se perdia sozinho (o Piter viu a tela na lixeira). Agora o
    clique é restrito ao INTERIOR da caixa do card que falhou, e o menu lateral
    (faixa da esquerda) fica fora por construção."""
    n = 0
    try:
        avisos = page.get_by_text(re.compile(r"Ops!|Algo deu errado", re.I))
        for i in range(min(avisos.count(), 6)):
            try:
                cx = avisos.nth(i).bounding_box()
                if not cx or cx["x"] < 220:      # faixa da esquerda = menu, nunca card
                    continue
                # a caixa do card: em volta do aviso, com folga pra pegar o ícone
                x0, x1 = cx["x"] - 260, cx["x"] + cx["width"] + 260
                y0, y1 = cx["y"] - 60, cx["y"] + cx["height"] + 300
                for b in page.locator("button").all():
                    bb = b.bounding_box()
                    if not bb or not (x0 <= bb["x"] <= x1 and y0 <= bb["y"] <= y1):
                        continue
                    rot = (b.get_attribute("aria-label") or "") + " " + (b.inner_text(timeout=300) or "")
                    if re.search(r"delete|excluir|remover|lixeira", rot, re.I):
                        b.click(timeout=3000)
                        n += 1
                        fd._pausa(0.4, 0.8)
                        break
            except Exception:
                continue
    except Exception:
        pass
    return n


def _match_pendente(texto_pagina, pendentes):
    """Casa o prompt visível na página de detalhe com um item do lote."""
    for it in pendentes:
        chave = it["prompt"][:70].strip()
        if chave and chave in texto_pagina:
            return it
    return None


def _carregar_todos_cards(page, max_rodadas=40):
    """Grid é lazy num container interno — roda de mouse até o nº de cards estabilizar."""
    est = 0
    for _ in range(max_rodadas):
        page.mouse.move(660, 400)
        page.mouse.wheel(0, 2600)
        time.sleep(1.0)
        n = len(_cards_edit(page))
        if n == est and n > 0:
            break
        est = n
    return _cards_edit(page)


def _baixar_via_rede(page, href, out_path):
    """Abre o detalhe e captura a URL real do mp4 (src do <video> ou sniff de rede),
    baixando com os cookies do contexto. Rota mais robusta que menus (FLOW_MAP plano B)."""
    url = href if href.startswith("http") else "https://labs.google" + href
    mp4s = []

    def _sniff(r):
        try:
            ct = (r.headers.get("content-type") or "").lower()
            if ".mp4" in r.url or "video/mp4" in ct:
                mp4s.append(r.url)
        except Exception:
            pass

    page.on("response", _sniff)
    try:
        page.goto(url, wait_until="domcontentloaded")
        fd._pausa(1.5, 2.5)
        try:
            page.locator("video").first.click(timeout=5000)  # play força o load
        except Exception:
            pass
        src = None
        t0 = time.time()
        while time.time() - t0 < 25 and not src:
            try:
                s = page.locator("video").first.get_attribute("src", timeout=2000)
                if s and s.startswith("http"):
                    src = s
            except Exception:
                pass
            if not src and mp4s:
                src = mp4s[-1]
            time.sleep(1)
        if not src:
            return False
        resp = page.context.request.get(src, timeout=120_000)
        if resp.ok:
            Path(out_path).write_bytes(resp.body())
            return _eh_mp4(out_path)
        return False
    finally:
        try:
            page.remove_listener("response", _sniff)
        except Exception:
            pass


def _eh_mp4(path):
    try:
        with open(path, "rb") as f:
            head = f.read(12)
        return b"ftyp" in head
    except Exception:
        return False


def _baixar_do_grid(page, href, out_path, quer_1080=False):
    """Rota A (a que funciona pra VÍDEO): hover no card do grid -> ⋮ -> Baixar.
    29/07: o botão da página de DETALHE baixa o POSTER (jpeg) — 111 arquivos falsos.

    ⚠️ 05/08 (QA Piter): "1080p Aumentada" NÃO é download, é UPSCALE NO SERVIDOR do
    Google — o próprio Flow avisa "pode levar alguns minutos. Evite iniciar várias
    tarefas de aumento de resolução". Nós pedíamos isso em TODO clipe com fila 4:
    cada download ficava esperando minutos por um upscale, e a fila estrangulava.
    Forte candidato ao lote que ficou pendurado. Agora o padrão é o download DIRETO
    (720p nativo); o render final é 1080p e o Remotion escala o vídeo inteiro de uma
    vez — muito mais barato que 98 upscales de 8s no servidor."""
    card = page.locator(f'a[href="{href}"]').first
    try:
        card.scroll_into_view_if_needed(timeout=10000)
        fd._pausa(0.4, 0.8)
        card.hover()
        fd._pausa(0.6, 1.0)
        # 30/07: os botões ♥/↻/⋮ NÃO são filhos do <a>, então era clique por coordenada
        # (canto sup-direito do card). 04/08: passou a errar o alvo — os botões ficam
        # RECUADOS da borda (⋮ em x=749 num card que termina em 795; o clique caía em
        # x=773, no vazio) e todo download falhava. Agora acha o botão DE VERDADE pelo
        # aria-label, filtrando os que estão dentro da área do card.
        box = card.bounding_box()
        if not box:
            return False
        btn_mais = None
        for b in page.locator("button").all():
            try:
                bb = b.bounding_box()
                if not bb:
                    continue
                dentro = (box["x"] <= bb["x"] <= box["x"] + box["width"]
                          and box["y"] <= bb["y"] <= box["y"] + box["height"])
                rot = (b.get_attribute("aria-label") or "") + " " + (b.inner_text(timeout=400) or "")
                if dentro and ("more_vert" in rot or "Mais" in rot or "More" in rot):
                    btn_mais = b
            except Exception:
                continue
        if btn_mais is None:
            return False
        with page.expect_download(timeout=150_000) as dl_info:
            btn_mais.click()
            fd._pausa(0.4, 0.8)
            page.get_by_role("menuitem", name=re.compile("^Baixar$|Download", re.I)).first.click()
            fd._pausa(0.4, 0.8)
            try:
                m1080 = page.get_by_role("menuitem", name=re.compile("1080p|Aumentada", re.I))
                if quer_1080 and m1080.count():
                    m1080.first.click()
                else:   # 720p / "Tamanho original": sai na hora, sem upscale no servidor
                    mit = page.get_by_role("menuitem",
                                           name=re.compile("720p|original|Tamanho", re.I))
                    if mit.count():
                        mit.first.click()
            except Exception:
                pass
        dl_info.value.save_as(str(out_path))
        page.keyboard.press("Escape")
        return True
    except Exception:
        try:
            page.keyboard.press("Escape")
        except Exception:
            pass
        return False


def _baixar_do_detalhe(page, out_path, quer_1080=True):
    """Na página /edit/<id>: botão de download -> (1080p Aumentada | direto)."""
    fd._pausa(0.5, 1.0)
    btn = page.get_by_role("button", name=re.compile(r"Baixar|Download", re.I))
    if not btn.count():  # fallback: botão só com ícone — pega por tooltip/aria
        btn = page.locator('button:has(svg)').filter(has_not_text=re.compile(".+"))
    try:
        with page.expect_download(timeout=150_000) as dl_info:
            btn.first.click()
            fd._pausa(0.4, 0.8)
            try:  # submenu de resolução (vídeo); imagem pode baixar direto no 1º clique
                m1080 = page.get_by_role("menuitem", name=re.compile("1080p", re.I))
                if quer_1080 and m1080.count():
                    m1080.first.click()
                else:
                    mit = page.get_by_role("menuitem",
                                           name=re.compile("Baixar|720p|original|PNG|JPG", re.I))
                    if mit.count():
                        mit.first.click()
            except Exception:
                pass
        dl_info.value.save_as(str(out_path))
        return True
    except PWTimeout:
        return False


def _normalizar_lote(lote):
    """Aceita os DOIS formatos de fila que existem hoje:
      • `veo_lote.json`  (modo generativo do canal)  -> {tipo, arquivo, prompt, ...}
      • `_gerar.json`    (buracos da curadoria, 02/08) -> {i, prompt, dest}
    Sem isso o driver quebrava no `x["tipo"]` ao consumir a fila da curadoria."""
    out = []
    for x in lote:
        y = dict(x)
        if not y.get("arquivo") and y.get("dest"):
            y["arquivo"] = y["dest"]
        if not y.get("tipo"):
            y["tipo"] = "imagem" if str(y.get("arquivo", "")).lower().endswith(
                (".jpg", ".jpeg", ".png")) else "video"
        out.append(y)
    return out


def _aprovado(caminho, item, tipo, tmp):
    """GATE NO GERADO (01/08). O clipe do VEO entrava na montagem sem nenhuma
    checagem — enquanto footage de terceiros passa por 3 gates. Mas modelo generativo
    erra à sua maneira: escreve texto na placa mesmo mandado não escrever, inventa mão
    com seis dedos, e às vezes produz alguém encarando/falando pra lente. Mesma régua
    do footage real: 6 frames pela duração inteira (vídeo) ou a própria imagem."""
    import vision_gate as vg
    caminho = Path(caminho)
    if not caminho.exists():
        return False, ["arquivo ausente"]
    frames = [str(caminho)] if tipo == "imagem" else \
        [str(f) for f in vg._frames_de_video(caminho, tmp, n=6)]
    if not frames:
        return True, []          # não deu pra amostrar: não condena por isso
    g = vg.gate(item.get("busca_original") or item.get("prompt", "")[:90], frames)
    flags = list(g.get("flags") or [])
    # 04/08: o vision_gate rejeita por segurança quando a API não responde
    # ("sem-resposta-vision"). Isso é certo pra footage de TERCEIRO (é de graça
    # buscar outro), mas aqui o clipe JÁ FOI GERADO e PAGO — descartar troca um
    # arquivo provavelmente bom por mais uma geração. Gate mudo => fica, com aviso
    # alto pra conferência; só defeito REAL manda re-gerar.
    if "sem-resposta-vision" in flags:
        print(f"  !! {item.get('arquivo')}: Vision fora do ar — MANTIDO sem avaliar "
              f"(conferir na decupagem)")
        return True, ["nao-avaliado"]
    # AVATAR DO CANAL é a única exceção legítima ao veto de talking-head: a regra
    # existe pra barrar CRIADOR DE TERCEIRO falando pra câmera (vlogger, review), e
    # o apresentador do próprio canal é o oposto disso. Marcado item a item — nunca
    # global, senão o veto perde o sentido no resto do vídeo.
    if item.get("avatar"):
        flags = [f for f in flags if f != "talking-head"]
    return (not flags), flags


def _fechar(pw, ctx):
    """Fecha contexto e Playwright sem deixar o erro de um impedir o outro."""
    for f in (getattr(ctx, "close", None), getattr(pw, "stop", None)):
        try:
            if f:
                f()
        except Exception:
            pass


def _sessao_dirigivel(page, fd, a, out):
    """Esta SESSÃO caiu na UI que o driver sabe dirigir? (06/08)

    O Flow sorteia a UI quando o contexto do Chrome sobe, e o bucket vale até
    fechar: mesma conta e mesmo projeto deram UIs diferentes em sessões diferentes.
    A UI nova não tem seletor de modelo, então o driver não a dirige — e como o
    sorteio é por sessão, "escolher um perfil de UI antiga" não existe. Devolver
    False (em vez de estourar) deixa o chamador reabrir e sortear de novo.

    Precisa ENTRAR num projeto: na grade as duas UIs são idênticas.
    """
    try:
        page.goto(fd.BASE, wait_until="domcontentloaded")
        fd._pausa(1.5, 2.5)
        if page.get_by_role("button", name=re.compile("Fazer login|Sign in", re.I)).count():
            print("!!! chrome_profile NÃO logado — rode: flow_driver.py login !!!")
            return None
        proj = a.proj
        if not proj and a.reusar:
            # reusar também evita deixar um "Sessão sem título" vazio por lote
            try:
                href = page.locator('a[href*="/project/"]').first.get_attribute(
                    "href", timeout=12000) or ""
                proj = href.rstrip("/").split("/project/")[-1][:36] or None
                print(f"  reusando projeto existente: {proj}")
            except Exception:
                print("  nenhum projeto para reusar — criando um novo")
        fd._abrir_projeto(page, proj)
        time.sleep(6)   # settle: SPA termina de montar a barra de prompt
        page.screenshot(path=str(Path(out) / "_debug_projeto.png"))
        if page.get_by_role("button").filter(
                has_text=re.compile(r"Veo|Banana|Omni", re.I)).count():
            return True
        if page.get_by_text(re.compile(r"O que você quer fazer|What do you want to",
                                       re.I)).count():
            return False
        return True   # nem seletor nem painel: deixa seguir e falhar com o erro real
    except Exception as e:
        print(f"  sessão não abriu o projeto ({type(e).__name__}) — reabrindo")
        return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lote", required=True)
    ap.add_argument("--regen", type=int, default=1,
                    help="re-gerações por item reprovado no gate (0 = aceita como veio)")
    ap.add_argument("--upscale-1080", action="store_true",
                    help="baixa em '1080p Aumentada' (UPSCALE no servidor do Google: "
                         "minutos por clipe e o Flow pede pra nao paralelizar). "
                         "Default: 720p nativo — o render final ja e' 1080p.")
    ap.add_argument("--sem-progresso", type=int, default=12, metavar="MIN",
                    help="aborta apos N minutos sem NENHUM download novo (watchdog)")
    ap.add_argument("--sem-config", action="store_true",
                    help="nao mexe no seletor de modelo: usa a config ja persistida "
                         "no projeto (o passo mais fragil do driver)")
    ap.add_argument("--dirigir", default="", metavar="ESTILO",
                    help='passa os prompts pelo diretor de fotografia com este look de '
                         'canal, ex: "dark stoic documentary, candlelit, 35mm"')
    ap.add_argument("--out", required=True)
    ap.add_argument("--fila", type=int, default=5)
    ap.add_argument("--modelo", default="Veo 3.1 - Lite [Lower Priority]")
    ap.add_argument("--proj", default=None)
    ap.add_argument("--timeout-total", type=int, default=4 * 3600)
    ap.add_argument("--tipo", default="video", choices=["video", "imagem"])
    ap.add_argument("--perfil", default="",
                    help="perfil Chrome; vazio = o 1º LIVRE (veo_flow/perfis.py)")
    ap.add_argument("--so-baixar", action="store_true",
                    help="não gera nada: casa os cards JÁ existentes no projeto e baixa")
    ap.add_argument("--tentativas-ui", type=int, default=3, dest="tentativas_ui",
                    help="quantas sessões reabrir enquanto o Flow sortear a UI nova")
    ap.add_argument("--reusar", action="store_true",
                    help="abre o projeto EXISTENTE mais recente em vez de criar um "
                         "(evita projeto vazio e a UI nova, que o driver não dirige)")
    ap.add_argument("--forcar", action="store_true",
                    help="regera mesmo com o destino já em disco (arquiva o antigo "
                         "em _rejeitados/) — a rota de reprovação do crítico")
    a = ap.parse_args()

    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    lote = _normalizar_lote(json.loads(Path(a.lote).read_text(encoding="utf-8")))
    if a.dirigir:
        # a fila da curadoria (_gerar.json) traz a `busca` CRUA como prompt — boa pro
        # Nano Banana, fraca pro VEO. Aqui ela passa pelo diretor de fotografia.
        from veo_prompt import dirigir as _dirigir
        alvo = [x for x in lote if x["tipo"] == a.tipo]
        novos = _dirigir([{"busca": x["prompt"], "tipo": x["tipo"]} for x in alvo], a.dirigir)
        for x, p in zip(alvo, novos):
            x["busca_original"], x["prompt"] = x["prompt"], p
        print(f"  prompts dirigidos: {len(novos)}")
    # Destino que já existe é PULADO — é o que torna a fila retomável depois de uma
    # queda. Mas isso também trancava a rota "o crítico reprovou, gere de novo": o
    # b086 do job amazônico voltou um vale ESCOCÊS, e a regeração ancorada não
    # entrava porque o arquivo errado ocupava o lugar. `--forcar` abre essa porta e
    # ARQUIVA o reprovado em vez de sobrescrever — a imagem rejeitada é a evidência
    # de por que o prompt mudou.
    if a.forcar:
        rej = out / "_rejeitados"
        for x in lote:
            velho = out / x["arquivo"]
            if x["tipo"] == a.tipo and velho.exists():
                rej.mkdir(parents=True, exist_ok=True)
                destino = rej / velho.name
                n = 1
                while destino.exists():   # não perde o reprovado anterior
                    destino = rej / f"{velho.stem}_{n}{velho.suffix}"
                    n += 1
                velho.replace(destino)
                print(f"  arquivado: {velho.name} -> _rejeitados/{destino.name}")
    fila_itens = [x for x in lote if x["tipo"] == a.tipo and not (out / x["arquivo"]).exists()]
    print(f"=== veo_driver: {len(fila_itens)} {a.tipo}s a gerar | fila {a.fila} | {a.modelo} ===")
    if not fila_itens:
        return

    # perfil LIVRE (02/08): perfil ocupado fazia o Playwright cair em "sessão de
    # navegador existente" e o lote inteiro sair com 0 imagens, sem erro claro
    # UI NOVA (06/08): o Flow sorteia a UI quando o contexto do Chrome SOBE, e o
    # bucket vale até fechar. A nova não tem seletor de modelo, então o driver não a
    # dirige — e como o sorteio é por sessão, não existe "perfil de UI antiga" para
    # escolher. O que funciona é REABRIR até cair na UI que ele sabe dirigir.
    pw = ctx = page = None
    for _t in range(1, max(1, a.tentativas_ui) + 1):
        pw, ctx, page = fd.abrir(headless=False, perfil=a.perfil or None)
        page.set_default_timeout(45_000)   # nenhum clique espera pra sempre
        _ok = _sessao_dirigivel(page, fd, a, a.out)
        if _ok:
            break
        _fechar(pw, ctx)
        pw = ctx = page = None
        if _ok is None:      # não é sorteio de UI: perfil deslogado, reabrir não cura
            return
        print(f"  UI NOVA nesta sessão ({_t}/{a.tentativas_ui}) — reabrindo o "
              f"navegador para sortear de novo", flush=True)
    if page is None:
        print(f"!!! {a.tentativas_ui} sessões seguidas caíram na UI NOVA do Flow, que não "
              f"tem seletor de modelo. Tente de novo, ou com --tentativas-ui maior.")
        return
    try:
        proj_url = page.url   # o loop de download volta pra cá quando o Flow desvia
        # landing "Create with Google Flow" = sessão do perfil dedicado EXPIRADA
        if page.get_by_text(re.compile("Create with Google Flow", re.I)).count():
            print("!!! SESSÃO EXPIRADA no chrome_profile do Playwright.")
            print('!!! Rode 1x e logue na conta Ultra:  '
                  '"F:/Canal Dark/veo_venv/Scripts/python.exe" '
                  '"F:/Canal Dark/Aplicativo de Edição/veo_flow/flow_driver.py" login')
            return
        # TRAVA DE MODO (04/08): confere SEMPRE, mesmo com --sem-config. A config
        # persiste por projeto, e gerar no modelo errado já custou caro duas vezes
        # hoje (vídeo saindo como imagem; imagem saindo como vídeo a 10 créditos).
        # `--sem-config` agora quer dizer "não reconfigure à toa", nunca "não confira".
        try:
            fd.garantir_modo(page, a.tipo, None if a.sem_config else a.modelo,
                             "16:9", "8s", "1x")
        except Exception as e:
            # PROJETO REUSADO INCOMPATÍVEL (06/08): `--reusar` economiza projeto mas
            # HERDA a configuração dele. Um projeto deixado em modo Omni ("Edite um
            # vídeo com o Omni") não tem sequer a aba "Imagem", então trocar o modo
            # estoura um TimeoutError esperando um tab que aquela tela não oferece.
            # Projeto NOVO nasce limpo — é o fallback certo, e só custa o projeto
            # vazio que o --reusar queria evitar.
            if not (a.reusar and not a.proj):
                raise
            print(f"  projeto reusado não aceita modo {a.tipo} ({type(e).__name__}) — "
                  f"criando um projeto limpo", flush=True)
            fd._abrir_projeto(page, None)
            time.sleep(6)
            proj_url = page.url
            fd.garantir_modo(page, a.tipo, None if a.sem_config else a.modelo,
                             "16:9", "8s", "1x")

        if a.so_baixar:
            em_voo = list(fila_itens)   # tudo pendente de download; nada a gerar
            vistos = set()
            i_next = len(fila_itens)
            n_cards = len(_carregar_todos_cards(page))
            print(f"  grid carregado: {n_cards} cards")
        else:
            em_voo = []           # itens enviados aguardando card
            vistos = _cards_edit(page)   # cards pré-existentes: ignorar
            i_next = 0
        feitos, falhas = 0, 0
        t0 = time.time()
        # WATCHDOG (04/08): o lote de 98 ficou 3h30 PENDURADO sem baixar nada e só o
        # Piter percebeu, olhando a tela. `--timeout-total` (4h) é longo demais pra
        # servir de alarme: um clique preso mata a noite inteira. Aqui, N minutos sem
        # NENHUM progresso => aborta e reporta, com o que já foi baixado preservado.
        t_prog = time.time()
        n_prog = -1
        # ALVO FIXO (06/08): contra `len(fila_itens)`, que CRESCE a cada
        # re-enfileiramento. Um item que falha e volta pra fila fazia o alvo virar 2
        # enquanto feitos+falhas parava em 1 — condição nunca satisfeita, e o driver
        # girava até o watchdog de 12 min matar. Custou 12 min em cada uma das três
        # tentativas do b086 hoje, sempre DEPOIS de já ter desistido do item.
        # Retentativa não é item novo: o alvo é quantos itens ÚNICOS o lote pediu.
        alvo = len(fila_itens)
        while (feitos + falhas) < alvo and time.time() - t0 < a.timeout_total:
            if feitos + falhas != n_prog:
                n_prog, t_prog = feitos + falhas, time.time()
            elif time.time() - t_prog > a.sem_progresso * 60:
                print(f"!!! {a.sem_progresso} min sem progresso (feitos={feitos} "
                      f"falhas={falhas} voo={len(em_voo)}) — ABORTANDO. Os clipes já "
                      f"gerados ficam no Flow: recupere com --so-baixar.", flush=True)
                break
            # 1) mantém a fila cheia
            while len(em_voo) < a.fila and i_next < len(fila_itens):
                it = fila_itens[i_next]
                fd.enviar_prompt(page, it["prompt"])
                em_voo.append(it)
                i_next += 1
                fd._pausa(4, 8)
            # popup de anúncio do Flow aparece a qualquer momento e trava TODO
            # clique seguinte (suspeita nº1 do lote que ficou 3h30 pendurado)
            fd.dispensar_avisos(page)
            # 05/08: um clique errado (ex.: "Ver lixeira" do menu) tirava o driver do
            # projeto e ele NUNCA mais via card — voltar é barato, se perder não é.
            if "/project/" not in page.url or page.url.rstrip("/").endswith("/trash"):
                print(f"  fora do projeto ({page.url[-28:]}) — voltando", flush=True)
                page.goto(proj_url, wait_until="domcontentloaded")
                fd._pausa(1.2, 2.0)
            # 1b) CARDS FALHADOS: o Flow diz "Ops! Algo deu errado" e aquele card
            # nunca vira vídeo. Sem tratar, o item fica em voo pra sempre. Devolve o
            # mais antigo em voo pra fila (até --regen tentativas) e limpa o card.
            n_falha = _cards_falha(page)
            # PRECEDÊNCIA DO CARD CONCLUÍDO (06/08) — a causa raiz do dia inteiro.
            # O sinal de falha do Flow aparece TRANSITORIAMENTE durante a geração e
            # some quando a imagem fica pronta: medido no projeto de teste, onde
            # `_cards_falha` deu >0 durante a geração e 0 depois, com 4 cards prontos
            # no grid. O driver lia esse sinal e DESCARTAVA um item que estava
            # gerando normalmente — "b086: card FALHOU 3x, desisto" enquanto as
            # imagens ficavam no Flow. Custou o dia: três reescritas de prompt e uma
            # caçada a filtro de conteúdo que nunca existiu (o prompt de controle,
            # "a red apple on a wooden table", também "falhou" — e gerou 4 maçãs).
            # Se apareceu card novo desde a última volta, algo CONCLUIU: o resultado
            # manda, o sinal transitório não.
            if n_falha and em_voo and (_cards_edit(page) - vistos):
                print(f"  (sinal de falha ignorado: {len(_cards_edit(page) - vistos)} "
                      f"card(s) novo(s) concluíram)", flush=True)
                n_falha = 0
            if n_falha and em_voo:
                # POR QUE falhou, antes de limpar o card (06/08). O driver contava
                # "falhas=1" e mandava tentar de novo — foi assim que o b120 queimou
                # 13 min em duas contas diferentes sem dizer que o prompt estava
                # sendo RECUSADO. Detector emprestado do flow_driver (Claude do
                # Flow), que já separa ritmo de política: repetir prompt recusado
                # não adianta nunca, e recuar por ritmo é o oposto de re-enfileirar.
                politica = ritmo = False
                try:
                    _txt = (page.inner_text("body", timeout=4000) or "")[:24000]
                    ritmo = fd.erro_de_ritmo(page)
                    politica = bool(fd._ERRO_POLITICA.search(_txt)) and not ritmo
                except Exception:
                    pass
                _limpar_falhas(page)
                it_f = em_voo.pop(0)
                it_f["_falhas"] = it_f.get("_falhas", 0) + 1
                if politica:
                    # recusa de conteúdo não melhora com repetição — para na hora e
                    # mostra o prompt, que é o que precisa ser reescrito
                    falhas += 1
                    print(f"  {it_f['arquivo']}: RECUSADO POR POLÍTICA — o prompt "
                          f"precisa ser reescrito, repetir não resolve", flush=True)
                    print(f"    prompt: {str(it_f.get('prompt'))[:120]}", flush=True)
                elif it_f["_falhas"] <= max(1, a.regen):
                    fila_itens.append(it_f)
                    print(f"  {it_f['arquivo']}: card FALHOU no Flow"
                          f"{' (RITMO)' if ritmo else ''} — re-enfileirado "
                          f"({it_f['_falhas']})", flush=True)
                    if ritmo:   # insistir no mesmo passo só reforça o freio
                        fd._pausa(25, 40)
                else:
                    falhas += 1
                    print(f"  {it_f['arquivo']}: falhou {it_f['_falhas']}x no Flow — "
                          f"desisto. NÃO presuma bloqueio de prompt: confira o projeto no "
                          f"Flow — a imagem pode ter gerado e só o driver não a "
                          f"viu (--so-baixar recupera)", flush=True)
            # 2) procura cards novos concluídos
            if a.so_baixar:  # grid é lazy e o goto reseta o scroll — recarrega tudo
                _carregar_todos_cards(page, max_rodadas=15)
            time.sleep(4 if a.so_baixar else 12)
            novos = _cards_edit(page) - vistos
            if a.so_baixar and not novos:
                sem_progresso = getattr(main, "_sp", 0) + 1
                main._sp = sem_progresso
                if sem_progresso >= 3:
                    break
            else:
                main._sp = 0
            for href in sorted(novos):
                url = href if href.startswith("http") else "https://labs.google" + href
                page.goto(url, wait_until="domcontentloaded")
                fd._pausa(1.2, 2.0)
                corpo = page.locator("body").inner_text(timeout=15000)
                it = _match_pendente(corpo, em_voo)
                page.goto(proj_url, wait_until="domcontentloaded")
                fd._pausa(1.2, 2.0)
                if it is None:
                    vistos.add(href)  # card de outra origem — ignora
                    continue
                # VÍDEO: menu ⋮ do card por coordenada (rota que funciona); fallback rede
                if a.tipo == "video":
                    ok = _baixar_do_grid(page, href, out / it["arquivo"],
                                         quer_1080=a.upscale_1080)
                    if ok and not _eh_mp4(out / it["arquivo"]):
                        (out / it["arquivo"]).unlink(missing_ok=True)
                        ok = False
                    if not ok:
                        ok = _baixar_via_rede(page, href, out / it["arquivo"])
                        if not ok:
                            (out / it["arquivo"]).unlink(missing_ok=True)
                        page.goto(proj_url, wait_until="domcontentloaded")
                        fd._pausa(1.0, 1.6)
                else:
                    page.goto(href if href.startswith("http") else "https://labs.google" + href,
                              wait_until="domcontentloaded")
                    fd._pausa(1.0, 1.6)
                    ok = _baixar_do_detalhe(page, out / it["arquivo"], quer_1080=False)
                    page.goto(proj_url, wait_until="domcontentloaded")
                    fd._pausa(1.0, 1.6)
                vistos.add(href)
                em_voo.remove(it)
                if ok and a.regen >= 0:
                    passou, flags = _aprovado(out / it["arquivo"], it, a.tipo, out / "_tmp")
                    if not passou:
                        (out / it["arquivo"]).unlink(missing_ok=True)
                        it["_tent"] = it.get("_tent", 0) + 1
                        if it["_tent"] <= a.regen:
                            fila_itens.append(it)   # volta pro fim: será re-gerado
                            print(f"  {it['arquivo']} REPROVADO {flags} — re-gerando "
                                  f"({it['_tent']}/{a.regen})")
                        else:
                            falhas += 1
                            print(f"  {it['arquivo']} REPROVADO {flags} — desisto")
                        continue
                if ok:
                    feitos += 1
                    print(f"  [{feitos}/{alvo}] {it['arquivo']} OK")
                else:
                    falhas += 1
                    print(f"  {it['arquivo']} FALHA no download")
            # 3) heartbeat pro monitor externo
            print(f"  ... voo={len(em_voo)} feitos={feitos} falhas={falhas} "
                  f"t={int(time.time() - t0)}s", flush=True)
        print(f"=== FIM: {feitos} ok, {falhas} falhas, {len(em_voo)} sem card ===")
    except Exception as e:
        # NAVEGADOR FECHADO no meio (06/08): janela fechada na mão, crash do Chrome,
        # ou o perfil aberto por outro processo. Vinha como 25 linhas de traceback do
        # Playwright terminando em TargetClosedError, que não diz o que fazer — e o
        # que fazer é específico: os cards já gerados FICAM no Flow, então `--so-baixar`
        # recupera o lote sem gastar geração de novo.
        if "TargetClosed" in type(e).__name__ or "has been closed" in str(e):
            print(f"!!! O navegador FECHOU no meio do lote ({feitos} ok até aqui).")
            print("!!! Os cards já gerados continuam no Flow — recupere sem re-gerar:")
            print(f'!!!   veo_driver.py --lote "{a.lote}" --out "{a.out}" '
                  f'--tipo {a.tipo} --so-baixar --perfil "{a.perfil}"')
            return
        try:
            page.screenshot(path=str(Path(a.out) / "_debug_erro.png"))
            print(f"  screenshot de erro: {Path(a.out) / '_debug_erro.png'}")
        except Exception:
            pass
        raise
    finally:
        _fechar(pw, ctx)


if __name__ == "__main__":
    main()
