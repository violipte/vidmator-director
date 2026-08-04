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


def _baixar_do_grid(page, href, out_path, quer_1080=True):
    """Rota A (a que funciona pra VÍDEO): hover no card do grid -> ⋮ -> Baixar -> 1080p.
    29/07: o botão da página de DETALHE baixa o POSTER (jpeg) — 111 arquivos falsos."""
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
                m1080 = page.get_by_role("menuitem", name=re.compile("1080p", re.I))
                if quer_1080 and m1080.count():
                    m1080.first.click()
                else:
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lote", required=True)
    ap.add_argument("--regen", type=int, default=1,
                    help="re-gerações por item reprovado no gate (0 = aceita como veio)")
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
    ap.add_argument("--so-baixar", action="store_true",
                    help="não gera nada: casa os cards JÁ existentes no projeto e baixa")
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
    fila_itens = [x for x in lote if x["tipo"] == a.tipo and not (out / x["arquivo"]).exists()]
    print(f"=== veo_driver: {len(fila_itens)} {a.tipo}s a gerar | fila {a.fila} | {a.modelo} ===")
    if not fila_itens:
        return

    pw, ctx, page = fd.abrir(headless=False)
    try:
        page.goto(fd.BASE, wait_until="domcontentloaded")
        fd._pausa(1.5, 2.5)
        if page.get_by_role("button", name=re.compile("Fazer login|Sign in", re.I)).count():
            print("!!! chrome_profile NÃO logado — rode: flow_driver.py login !!!")
            return
        fd._abrir_projeto(page, a.proj)
        proj_url = page.url
        time.sleep(6)  # settle: SPA termina de montar a barra de prompt
        page.screenshot(path=str(Path(a.out) / "_debug_projeto.png"))
        # landing "Create with Google Flow" = sessão do perfil dedicado EXPIRADA
        if page.get_by_text(re.compile("Create with Google Flow", re.I)).count():
            print("!!! SESSÃO EXPIRADA no chrome_profile do Playwright.")
            print('!!! Rode 1x e logue na conta Ultra:  '
                  '"F:/Canal Dark/veo_venv/Scripts/python.exe" '
                  '"F:/Canal Dark/Aplicativo de Edição/veo_flow/flow_driver.py" login')
            return
        try:
            if a.sem_config:
                # 04/08: a config PERSISTE por projeto. Reabrir o popup a cada rodada
                # é o passo mais frágil do driver (a UI do Flow muda os rótulos e o
                # popper fica interceptando clique). Com o projeto já configurado na
                # mão, pular aqui é mais seguro que reconfigurar. ⚠️ conferir no
                # rodapé que está em Vídeo — foi assim que um lote saiu como imagem.
                raise RuntimeError("--sem-config")
            fd.configurar_video(page, a.modelo, "16:9", "8s", "1x")
        except Exception as e_cfg:
            # config PERSISTE por projeto — se o popup mudou/travou, segue com a atual
            print(f"  config pulada ({type(e_cfg).__name__}) — usando a config persistida do projeto")
            page.keyboard.press("Escape")
            fd._pausa(0.5, 1.0)

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
        while (feitos + falhas) < len(fila_itens) and time.time() - t0 < a.timeout_total:
            # 1) mantém a fila cheia
            while len(em_voo) < a.fila and i_next < len(fila_itens):
                it = fila_itens[i_next]
                fd.enviar_prompt(page, it["prompt"])
                em_voo.append(it)
                i_next += 1
                fd._pausa(4, 8)
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
                    ok = _baixar_do_grid(page, href, out / it["arquivo"], quer_1080=True)
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
                    print(f"  [{feitos}/{len(fila_itens)}] {it['arquivo']} OK")
                else:
                    falhas += 1
                    print(f"  {it['arquivo']} FALHA no download")
            # 3) heartbeat pro monitor externo
            print(f"  ... voo={len(em_voo)} feitos={feitos} falhas={falhas} "
                  f"t={int(time.time() - t0)}s", flush=True)
        print(f"=== FIM: {feitos} ok, {falhas} falhas, {len(em_voo)} sem card ===")
    except Exception:
        try:
            page.screenshot(path=str(Path(a.out) / "_debug_erro.png"))
            print(f"  screenshot de erro: {Path(a.out) / '_debug_erro.png'}")
        except Exception:
            pass
        raise
    finally:
        ctx.close()
        pw.stop()


if __name__ == "__main__":
    main()
