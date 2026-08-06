#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""flow_driver.py — driver Playwright do Google Flow (VEO 3.1), SEM API paga.

Dirige o site labs.google/fx/tools/flow reusando uma SESSÃO LOGADA num perfil
Chrome dedicado (login manual 1x). Baseado no mapa em veo_flow/FLOW_MAP.md.

FASES PRONTAS:  login · abrir/criar projeto · configurar vídeo (modelo/aspecto/
                duração/saídas) · enviar prompt.
STUBS (a confirmar com 1 clipe real):  esperar conclusão · baixar o mp4.

Uso:
  python flow_driver.py login
      -> abre o browser; você loga 1x na conta Google Ultra; a sessão persiste.
  python flow_driver.py gen "a red fox running through snow, cinematic" \
      [--modelo "Veo 3.1 - Fast"] [--dur 8s] [--aspecto 16:9] [--saidas x2] [--proj <projId>]

Requer: veo_venv (Playwright 1.61 + Chrome instalado).
Rodar com:  "F:/Canal Dark/veo_venv/Scripts/python.exe" flow_driver.py ...
"""
import argparse
import re
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

sys.stdout.reconfigure(encoding="utf-8")

# ---- config ----
AQUI = Path(__file__).resolve().parent
PROFILE_DIR = AQUI / "chrome_profile"      # perfil dedicado (login 1x, isolado do Chrome pessoal)
DOWNLOADS = AQUI / "downloads"             # onde os mp4 caem
BASE = "https://labs.google/fx/pt/tools/flow"
UI_TIMEOUT = 60_000                        # ms p/ elementos de UI
GEN_TIMEOUT = 8 * 60                       # s p/ a geração de vídeo terminar (VEO é lento)

# regex do texto do botão seletor de modelo (muda conforme o estado)
MODELO_BTN_RE = re.compile(r"(Veo|Banana|Omni|V[íi]deo|Imagem)", re.I)


# ---- infra ----
def _limpar_saida_suja():
    """Tira o "Restaurar páginas? O Chrome não foi encerrado corretamente" (05/08).

    O supervisor mata o Chrome à força (é a única forma quando o Playwright está
    preso), e o Chrome guarda isso nas Preferences pra mostrar a bolha no próximo
    boot. Ela nasce no CANTO SUPERIOR DIREITO — em cima dos botões do Flow —, ou
    seja, é mais um candidato a roubar clique, como o popup de anúncio. Marcar a
    saída como limpa antes de abrir resolve na origem."""
    import json as _j
    for pref in (PROFILE_DIR / "Default" / "Preferences", PROFILE_DIR / "Preferences"):
        try:
            if not pref.exists():
                continue
            d = _j.loads(pref.read_text(encoding="utf-8", errors="ignore"))
            perfil = d.setdefault("profile", {})
            if perfil.get("exit_type") == "Normal" and perfil.get("exited_cleanly") is True:
                continue
            perfil["exit_type"] = "Normal"
            perfil["exited_cleanly"] = True
            pref.write_text(_j.dumps(d), encoding="utf-8")
        except Exception:
            pass


def abrir(headless=False, perfil=None):
    """Abre o contexto persistente no Chrome instalado. Retorna (pw, ctx, page).

    `perfil` (02/08): permite usar OUTRA conta Google. Sem ele, pergunta ao
    `perfis.py` qual está LIVRE — o perfil ocupado por uma janela do Piter fazia o
    Playwright cair em "Abrindo em uma sessão de navegador existente" e gerar ZERO
    imagens sem erro claro (travou a fila de 5 gaps). Se nenhum está livre, segue
    no padrão e o erro aparece explícito."""
    global PROFILE_DIR
    if perfil:
        PROFILE_DIR = Path(perfil)
    else:
        try:
            sys.path.insert(0, str(AQUI))
            from perfis import primeiro_livre
            _liv = primeiro_livre()
            if _liv:
                PROFILE_DIR = Path(_liv)
                print(f"perfil livre: {PROFILE_DIR.name}")
            else:
                print("!! nenhum perfil LIVRE — o Chrome do Flow está aberto? "
                      "(veo_flow/perfis.py mostra o estado)")
        except Exception:
            pass
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    DOWNLOADS.mkdir(parents=True, exist_ok=True)
    _limpar_saida_suja()
    pw = sync_playwright().start()
    ctx = pw.chromium.launch_persistent_context(
        user_data_dir=str(PROFILE_DIR),
        channel="chrome",                  # usa o Google Chrome do sistema (não baixa chromium)
        headless=headless,
        accept_downloads=True,
        viewport={"width": 1920, "height": 1080},
        args=["--disable-blink-features=AutomationControlled",   # reduz sinais óbvios de automação
              "--hide-crash-restore-bubble",   # cinto/suspensório do _limpar_saida_suja
              "--no-first-run", "--no-default-browser-check"],
    )
    page = ctx.pages[0] if ctx.pages else ctx.new_page()
    page.set_default_timeout(UI_TIMEOUT)
    return pw, ctx, page


def _pausa(a=0.6, b=1.4):
    """Pacing humano leve entre ações (anti-detecção básica)."""
    import random
    time.sleep(random.uniform(a, b))  # noqa: S311  (não-cripto, só timing)


# ---- comandos ----
def cmd_login():
    """Abre o Flow p/ o usuário logar 1x. A sessão fica salva no PROFILE_DIR."""
    pw, ctx, page = abrir(headless=False)
    page.goto(BASE, wait_until="domcontentloaded")
    print("=== LOGIN ===")
    print("Faça login na tua conta Google (Ultra) NESTA janela do Chrome.")
    print("Quando o Flow carregar logado (aparecer 'Novo projeto' / badge ULTRA),")
    input("volte aqui e aperte ENTER pra salvar a sessão e fechar... ")
    ctx.close(); pw.stop()
    print(f"OK — sessão salva em {PROFILE_DIR}")


def _abrir_projeto(page, proj_id=None):
    """Abre um projeto existente (proj_id) ou cria um novo."""
    if proj_id:
        page.goto(f"{BASE}/project/{proj_id}", wait_until="domcontentloaded")
    else:
        page.goto(BASE, wait_until="domcontentloaded")
        _pausa()
        page.get_by_role("button", name=re.compile("Novo projeto", re.I)).click()
    page.wait_for_url(re.compile(r"/project/[0-9a-f-]+"), timeout=UI_TIMEOUT)
    _pausa()
    print(f"  projeto: {page.url.split('/project/')[-1][:36]}")


def _seletor_modelo_btn(page):
    """O botão da barra de prompt que abre o popup de modelo/config."""
    # está no rodapé, mostra o estado atual (ex.: 'Veo 3.1 - Fast' / 'Vídeo · 8s x2' / 'Nano Banana 2 x2')
    return page.get_by_role("button").filter(has_text=MODELO_BTN_RE).last


MODELO_VIDEO = "Veo 3.1 - Lite [Lower Priority]"   # padrão do canal (Piter 04/08)
MODELO_IMAGEM = "Nano Banana 2"                    # 0 créditos — imagem NUNCA no VEO


def dispensar_avisos(page):
    """Popups de ANÚNCIO do Flow ("Tools Community Gallery is Live!" etc.) bloqueiam
    a UI e derrubam o driver. Solução já provada em PROD (`video-automator/thumb_gen/
    thumb_nano.py`, visto 31/07 e 04/08) — trazida pra cá porque o Google solta um
    aviso novo a cada feature e QUALQUER driver do Flow precisa disso.

    Forte suspeita de ser a causa do lote de 98 ter ficado 3h30 pendurado: um popup
    aparece no meio do lote, todo clique seguinte cai nele, e o driver espera pra
    sempre. Best-effort e silencioso: nunca derruba o lote."""
    try:
        page.keyboard.press("Escape")
        _pausa(0.2, 0.4)
    except Exception:
        pass
    # 06/08: "Fechar"/"Close" casa TAMBÉM com a seta de VOLTAR da coleção — clicar
    # nela devolvia a página pro projeto no meio do lote (a guarda `garantir_dentro`
    # vinha re-entrando a cada rajada por causa disto). Botão de navegação fica de
    # fora: só dispensa o que está dentro de um diálogo/overlay.
    url_antes = page.url
    for pat in (r"Comece j[aá]", r"Come[cç]ar", r"Got it", r"Entendi", r"Start",
                r"Dismiss", r"Continuar", r"Fechar", r"Close", r"^OK$"):
        try:
            b = page.get_by_role("button", name=re.compile(pat, re.I)).first
            if pat in (r"Fechar", r"Close"):
                # aceita só se estiver DENTRO de um dialog/alertdialog
                em_dialogo = page.get_by_role("dialog").locator(
                    f'button:has-text("{pat}")').count() or page.get_by_role(
                    "alertdialog").locator(f'button:has-text("{pat}")').count()
                if not em_dialogo:
                    continue
            if b.is_visible(timeout=700):
                b.click(timeout=2000)
                print(f"  aviso do Flow dispensado (~/{pat}/)")
                _pausa(0.3, 0.6)
        except Exception:
            pass
    if page.url != url_antes:
        print(f"  !! dispensar_avisos NAVEGOU ({url_antes[-30:]} -> {page.url[-30:]})")


def modo_atual(page):
    """Lê o botão do rodapé, que mostra o estado: 'Vídeo · 8s crop_16_9 x1' ou
    '🍌 Nano Banana 2 x2'. Devolve ('video'|'imagem'|'?', texto_lido)."""
    try:
        txt = _seletor_modelo_btn(page).inner_text(timeout=8000).replace("\n", " ")
    except Exception:
        return "?", ""
    if re.search(r"nano\s*banana|imagem", txt, re.I):
        return "imagem", txt
    if re.search(r"v[ií]deo|veo|\d+\s*s\b", txt, re.I):
        return "video", txt
    return "?", txt


def garantir_modo(page, tipo, modelo=None, aspecto="16:9", dur="8s", saidas="x1"):
    """TRAVA ANTES DE GERAR (04/08, pedido do Piter). A config do modelo PERSISTE por
    projeto e errá-la custa dinheiro nos dois sentidos, já aconteceu duas vezes hoje:
      • lote de VÍDEO rodou como IMAGEM (o seletor estava em Nano Banana) e ainda por
        cima desenhou a legenda da fala no quadro;
      • passe de IMAGEM rodou como VÍDEO (seletor em Veo) — ~90 créditos num trabalho
        que no Nano Banana é 0.
    Confere, corrige se preciso, CONFERE DE NOVO e falha alto se não bater. Gerar no
    modelo errado é pior que não gerar."""
    alvo_modelo = modelo or (MODELO_VIDEO if tipo == "video" else MODELO_IMAGEM)
    dispensar_avisos(page)      # popup na frente do seletor = leitura errada do modo
    atual, txt = modo_atual(page)
    if atual == tipo:
        print(f"  modo OK: {tipo} ({txt.strip()[:44]})")
        return True
    print(f"  modo era '{atual}' ({txt.strip()[:40]}) — trocando para {tipo}...")
    if tipo == "video":
        configurar_video(page, alvo_modelo, aspecto, dur, saidas)
    else:
        configurar_imagem(page, alvo_modelo, aspecto)
    atual2, txt2 = modo_atual(page)
    if atual2 != tipo:
        raise RuntimeError(f"NÃO consegui pôr o Flow em '{tipo}' (está '{atual2}': "
                           f"{txt2.strip()[:60]}). Abortando ANTES de gerar no modelo "
                           f"errado — conserte na tela e rode de novo.")
    print(f"  modo confirmado: {tipo} ({txt2.strip()[:44]})")
    return True


def configurar_imagem(page, modelo=MODELO_IMAGEM, aspecto="16:9"):
    """Aba Imagem + Nano Banana (0 créditos)."""
    _seletor_modelo_btn(page).click()
    _pausa()
    _tab(page, "Imagem").click()
    _pausa(0.3, 0.7)
    try:
        page.get_by_role("button", name=re.compile(r"Nano|Banana|Imagen|Omni", re.I)).first.click()
        _pausa(0.3, 0.7)
        page.get_by_text(re.compile(re.escape(modelo), re.I)).first.click()
        _pausa(0.3, 0.7)
    except Exception:
        print(f"  (dropdown de modelo de imagem não abriu — usando o atual)")
    try:
        _tab(page, aspecto).click()
    except Exception:
        pass
    for _ in range(3):
        page.keyboard.press("Escape")
        _pausa(0.3, 0.6)
        if not page.locator("[data-radix-popper-content-wrapper]").count():
            break
    _pausa(0.3, 0.7)


def _tab(page, alvo):
    """04/08: os tabs do Flow têm o nome do ÍCONE material colado no texto —
    'videocam\\nVídeo', 'crop_16_9\\n16:9'. Com `name=..., exact=True` NADA casava:
    configurar_video estourava TimeoutError, o driver seguia com 'config pulada' e a
    geração saía no modelo que estivesse selecionado. Foi assim que um lote de VÍDEO
    saiu como IMAGEM do Nano Banana — e, pior, imagem de alguém FALANDO vira legenda
    DESENHADA no quadro. Casar por substring resolve a classe toda."""
    return page.get_by_role("tab", name=re.compile(re.escape(alvo), re.I)).first


def configurar_video(page, modelo="Veo 3.1 - Fast", aspecto="16:9", dur="8s", saidas="x2"):
    """Abre o popup e seta Vídeo + modelo + aspecto + duração + saídas."""
    _seletor_modelo_btn(page).click()
    _pausa()
    _tab(page, "Vídeo").click()                                    # aba Vídeo
    _pausa(0.3, 0.7)
    # modelo: abre o dropdown (botão mostra o modelo atual) e escolhe pelo texto
    page.get_by_role("button", name=re.compile(r"Veo|Omni", re.I)).first.click()
    _pausa(0.3, 0.7)
    page.get_by_text(re.compile(re.escape(modelo), re.I)).first.click()
    _pausa(0.3, 0.7)
    _tab(page, aspecto).click()                                    # 9:16 | 16:9
    _tab(page, dur).click()                                        # 4s | 6s | 8s
    _tab(page, saidas).click()                                     # 1x | x2 | x3 | x4
    # lê o custo exibido (ex.: 'A geração vai usar 20 créditos')
    try:
        custo = page.get_by_text(re.compile(r"cr[ée]ditos")).inner_text(timeout=3000)
        print(f"  config: {modelo} · {aspecto} · {dur} · {saidas}  ({custo.strip()})")
    except PWTimeout:
        print(f"  config: {modelo} · {aspecto} · {dur} · {saidas}")
    # 04/08: UM Escape não bastava — o popper do Radix ficava montado e "intercepts
    # pointer events", travando o clique seguinte (o envio do prompt). Fecha o
    # dropdown E o popup, e confirma que o overlay sumiu antes de devolver o controle.
    for _ in range(3):
        page.keyboard.press("Escape")
        _pausa(0.3, 0.6)
        if not page.locator("[data-radix-popper-content-wrapper]").count():
            break
    else:
        try:  # ainda montado: clica numa área morta pra dispensar
            page.mouse.click(page.viewport_size["width"] - 30, 300)
        except Exception:
            pass
    _pausa(0.3, 0.7)


def enviar_prompt(page, prompt, exigir_mencao=False):
    """Escreve o prompt e dispara a geração."""
    # 05/08 (sonda): a barra de prompt virou um CONTENTEDITABLE sem placeholder —
    # get_by_placeholder("quer criar") não acha mais nada. O contenteditable é único
    # na página; placeholder e textbox.last ficam de reserva pra UIs antigas.
    cx = page.locator('[contenteditable="true"]').first
    try:
        if not cx.count():
            cx = page.get_by_placeholder(re.compile("quer criar", re.I))
        cx.wait_for(timeout=5000)
    except PWTimeout:
        cx = page.get_by_role("textbox").last
    cx.click()
    _pausa(0.2, 0.5)
    m = re.match(r"\s*@(\w[\w-]*)\s*(.*)", prompt, re.S)
    if m:
        # MENÇÃO DE PERSONAGEM — fluxo SONDADO na UI real (05/08, screenshots):
        #   1. o CORPO entra por insert_text (atômico, ZERO eventos de tecla — nada
        #      de autocomplete disparando no meio; foi digitação de corpo que caiu
        #      na busca do painel duas vezes);
        #   2. " @Rus" digitado no FIM abre o painel de recursos com filtro "Rus";
        #   3. a opção certa é [role=option] com o NOME **e** "Personagem" — o
        #      filtro tb devolve mídias ("Rusted machete..." apareceu junto);
        #   4. clicar na opção SÓ ABRE O DETALHE — o chip entra no botão
        #      **"Incluir no comando"** (era o passo que faltava em 3 tentativas);
        #   5. verificação: dialog fechado E corpo ainda no campo; falhou => Escape,
        #      limpa, reenvia SEM personagem avisando alto (nunca trava o lote).
        nome, resto = m.group(1), m.group(2).strip()
        cx.click()
        _pausa(0.3, 0.6)
        page.keyboard.insert_text(resto)
        _pausa(0.5, 0.9)
        page.keyboard.type(" @" + nome[:3], delay=140)
        _pausa(1.6, 2.4)
        ok_mencao = False
        try:
            op = page.locator('[role="option"]').filter(
                has_text=re.compile(re.escape(nome), re.I)).filter(
                has_text=re.compile("Personagem|Character", re.I))
            if not op.count():   # fallback: opção só com o nome exato
                op = page.locator('[role="option"]').filter(
                    has_text=re.compile(rf"^{re.escape(nome)}", re.I))
            if op.count():
                op.first.click()
                _pausa(0.9, 1.5)
                inc = page.get_by_role("button",
                                       name=re.compile("Incluir no comando|Include", re.I))
                if inc.count():
                    inc.first.click()
                    _pausa(0.9, 1.5)
                    ok_mencao = not page.locator('[role="dialog"]').count()
        except Exception:
            ok_mencao = False
        if ok_mencao:
            # 05/08 (print do Piter): o "Incluir no comando" deixa o NOME em TEXTO
            # puro no fim do prompt, além do chip — e nome literal dispara a
            # política de "pessoa famosa" (o cta_final caiu 3x nisso). O chip é um
            # nó à parte e sobrevive ao delete-por-palavra; o texto residual sai.
            try:
                for _ in range(2):
                    txt = (cx.inner_text(timeout=2000) or "").strip()
                    if re.search(rf"{re.escape(nome)}\s*$", txt, re.I):
                        page.keyboard.press("End")
                        page.keyboard.press("Control+Backspace")
                        _pausa(0.2, 0.4)
                    else:
                        break
                print(f"  resíduo do nome removido do texto (só o chip fica)")
            except Exception:
                pass
        corpo_ok = False
        try:
            corpo_ok = resto[:25].lower() in (cx.inner_text(timeout=3000) or "").lower()
        except Exception:
            pass
        if not ok_mencao or not corpo_ok:
            page.keyboard.press("Escape")
            _pausa(0.4, 0.7)
            cx.click()
            page.keyboard.press("Control+A")
            page.keyboard.press("Delete")
            if exigir_mencao:
                # 05/08 (QA Piter: hook do v2 saiu um CARA GENÉRICO): take de AVATAR
                # sem chip NÃO É ENVIADO — gerar sem identidade desperdiça a geração
                # e engana o casamento. Fica pra próxima rodada tentar de novo.
                print(f"  !! menção @{nome} não confirmada — take de avatar NÃO enviado")
                return False
            page.keyboard.insert_text(resto)
            print(f"  !! menção @{nome} não confirmada — take SEM personagem")
        else:
            print(f"  menção @{nome}: chip incluído no comando")
        _pausa(0.4, 0.9)
        cx.press("Enter")
        print(f"  prompt enviado: {prompt[:60]}...")
        return True
        # 04/08 (QA Piter: "não puxou o personagem"): `fill()` COLA o texto de uma vez
        # e não dispara os eventos de teclado que abrem o autocomplete de menção — o
        # "@Russel" virava texto literal e o clipe saía com outro rosto. Menção tem de
        # ser DIGITADA e a sugestão ESCOLHIDA da lista pra virar referência de verdade.
        nome, resto = m.group(1), m.group(2)
        # digita só o GATILHO (@ + 3 letras) e deixa a lista completar: o Flow NÃO
        # substitui o texto já digitado pelo chip — digitar o nome inteiro deixaria
        # "@Russel" literal grudado no chip (visto no print do Piter 04/08).
        cx.type("@" + nome[:3], delay=110)
        _pausa(1.2, 2.0)
        escolhido = False
        for _tent in range(2):
            for sel in (f'[role="option"]:has-text("{nome}")',
                        f'[role="menuitem"]:has-text("{nome}")',
                        f'li:has-text("{nome}")'):
                try:
                    op = page.locator(sel).first
                    if op.count() and op.is_visible():
                        op.click()
                        escolhido = True
                        break
                except Exception:
                    continue
            if not escolhido:   # linhas do painel de recursos são divs sem role
                try:
                    op = page.get_by_text(re.compile(rf"^{re.escape(nome)}$", re.I)).first
                    if op.count() and op.is_visible():
                        op.click()
                        escolhido = True
                except Exception:
                    pass
            if escolhido:
                break
            _pausa(1.0, 1.6)
        # 05/08 (print do Piter): o Enter ÀS CEGAS abria o PAINEL DE BUSCA de
        # recursos e o resto do prompt era digitado DENTRO DA BUSCA — saiu lixo
        # tipo "...are @Rusalmost never..." e o envio nunca acontecia. Agora:
        # menção não confirmada => Escape, limpa o campo e manda SEM personagem
        # (avisando alto) — take ruim se regenera; painel travado trava o lote.
        painel = page.get_by_text(re.compile("Nenhum resultado|Pesquisar recursos", re.I))
        painel_aberto = False
        try:
            painel_aberto = painel.count() > 0 and painel.first.is_visible()
        except Exception:
            pass
        if not escolhido or painel_aberto:
            page.keyboard.press("Escape")
            _pausa(0.4, 0.8)
            cx.click()
            page.keyboard.press("Control+A")
            page.keyboard.press("Delete")
            print(f"  !! menção @{nome} NÃO confirmada — enviando SEM personagem")
            cx.type(resto.strip(), delay=6)
        else:
            print(f"  menção @{nome}: escolhida da lista")
            cx.type(" " + resto.strip(), delay=6)
    else:
        cx.fill(prompt)
    _pausa(0.4, 0.9)
    cx.press("Enter")               # submit primário (fallback: clicar a seta →)
    print(f"  prompt enviado: {prompt[:60]}...")


def esperar_e_baixar(page, out_dir=DOWNLOADS):
    """STUB — a CONFIRMAR na 1ª geração real.

    Plano (2 sinais de conclusão a validar ao vivo):
      A) DOM: novo card de vídeo aparece no grid com botão play.
      B) rede: resposta com a URL do mp4 (page.on('response') filtrando video/mp4).
    Download (2 rotas):
      1) abrir o card -> tela de detalhe -> clicar ⬇️  com page.expect_download().
      2) pegar a URL do mp4 da rede e baixar direto (mais robusto).
    """
    print("  [STUB] esperar conclusão + baixar — confirmar com 1 clipe real (ver FLOW_MAP.md).")
    # esqueleto da rota por rede (a ativar quando validarmos o padrão de URL):
    # mp4s = []
    # page.on("response", lambda r: mp4s.append(r.url) if ".mp4" in r.url else None)
    # t0 = time.time()
    # while time.time() - t0 < GEN_TIMEOUT and not mp4s:
    #     time.sleep(3)
    # ... baixar mp4s[-1] ...
    return None


def cmd_gen(args):
    pw, ctx, page = abrir(headless=False)
    try:
        # sanidade de login
        page.goto(BASE, wait_until="domcontentloaded")
        if page.get_by_role("button", name=re.compile("Fazer login|Sign in", re.I)).count():
            print("NÃO logado. Rode primeiro:  python flow_driver.py login")
            return
        _abrir_projeto(page, args.proj)
        configurar_video(page, args.modelo, args.aspecto, args.dur, args.saidas)
        enviar_prompt(page, args.prompt)
        esperar_e_baixar(page)
        print("\nOK (geração disparada). Download = stub até validarmos com 1 clipe.")
        if args.hold:
            input("ENTER pra fechar o browser... ")
    finally:
        ctx.close(); pw.stop()


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("login")
    g = sub.add_parser("gen")
    g.add_argument("prompt")
    g.add_argument("--modelo", default="Veo 3.1 - Fast")
    g.add_argument("--aspecto", default="16:9", choices=["16:9", "9:16"])
    g.add_argument("--dur", default="8s", choices=["4s", "6s", "8s"])
    g.add_argument("--saidas", default="x2", choices=["1x", "x2", "x3", "x4"])
    g.add_argument("--proj", default=None, help="projId existente (senão cria novo)")
    g.add_argument("--hold", action="store_true", help="não fecha o browser no fim")
    a = ap.parse_args()

    if a.cmd == "login":
        cmd_login()
    elif a.cmd == "gen":
        cmd_gen(a)


if __name__ == "__main__":
    main()
