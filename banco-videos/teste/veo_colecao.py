# -*- coding: utf-8 -*-
"""COLEÇÕES do Flow — 1 projeto por CANAL, 1 coleção por VÍDEO (05/08, Piter).

Por que não um projeto por vídeo: **o personagem vive no PROJETO**. Projeto novo a
cada vídeo mataria o `@Russel` — a identidade do canal. Coleção é "projeto dentro do
projeto": herda os personagens (o `@` continua funcionando) e tem um **"Baixar
coleção"** próprio, que traz só as mídias daquele vídeo.

    PROJETO  = CANAL   (guarda os personagens do host)
      └─ COLEÇÃO = VÍDEO  (nome = data de publicação, ex.: "05-08-26")

UI (ditada pelo Piter, prints 05/08):
  • "+" no topo -> menu: Enviar mídia | **Criar coleção** | Criar personagem | Criar cena
  • entrar = **1 clique no MEIO do card**; a URL vira .../project/<id>/collection/<id>
    (confirmação DETERMINÍSTICA — antes eu "achava" que tinha entrado e seguia no grid)
  • hover no card: ♥ / ⬇ ("Baixar coleção") / ⋮ (Renomear, Mover p/ lixeira)

⚠️ Lição de 05/08: `get_by_role("textbox").last` é a BARRA DE PROMPT. Meu rename
digitou "05-08-26" nela e GEROU UM VÍDEO com a data como prompt. Todo campo de texto
aqui é escolhido excluindo a barra de prompt e a busca, nunca por `.last`.
"""
import json
import re
import sys
import time as _t
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "veo_flow"))
sys.stdout.reconfigure(encoding="utf-8")

REGISTRO = Path(__file__).resolve().parents[2] / "veo_flow" / "projetos.json"


def _fd():
    import flow_driver as fd
    return fd


# ---------- registro canal -> projeto/coleções ----------
def _reg_ler():
    try:
        return json.loads(REGISTRO.read_text(encoding="utf-8"))
    except Exception:
        return {}


def projeto_do_canal(canal):
    return _reg_ler().get(canal)


def registrar_projeto(canal, proj_id, nome=""):
    d = _reg_ler()
    d.setdefault(canal, {})
    d[canal].update({"projeto": proj_id, "nome": nome or d[canal].get("nome") or canal})
    REGISTRO.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    return d[canal]


def registrar_colecao(canal, nome, colecao_id):
    d = _reg_ler()
    d.setdefault(canal, {}).setdefault("colecoes", {})[nome] = colecao_id
    REGISTRO.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")


# ---------- helpers de card ----------
def _label_da_colecao(page, nome):
    """O rótulo do card no grid do projeto. Devolve (locator, box) ou (None, None)."""
    t = page.get_by_text(re.compile(rf"^{re.escape(nome)}$", re.I)).first
    try:
        if not t.count():
            return None, None
        return t, t.bounding_box()
    except Exception:
        return None, None


def _botao_do_card(page, box_label, padrao):
    """Botão (♥/⬇/⋮) do card hoverado: o MAIS PRÓXIMO do rótulo que case o padrão.
    Proximidade em vez de varredura global — foi varredura global que clicou no
    "Ver lixeira" do menu lateral e mandou o driver pra /trash."""
    if not box_label:
        return None
    cx = box_label["x"] + box_label["width"] / 2
    cy = box_label["y"]
    melhor, melhor_d = None, 1e9
    for b in page.locator("button").all():
        try:
            bb = b.bounding_box()
            if not bb or bb["y"] < 60:          # topo do app (Mais/Ajuda/etc.) fora
                continue
            d = abs(bb["x"] - cx) + abs(bb["y"] - cy)
            if d > 480:                          # longe do card = outro contexto
                continue
            rot = (b.get_attribute("aria-label") or "") + " " + (b.inner_text(timeout=250) or "")
            if re.search(padrao, rot, re.I) and d < melhor_d:
                melhor, melhor_d = b, d
        except Exception:
            continue
    return melhor


def _campo_de_renome(page):
    """O input do rename — NUNCA `.last` (é a barra de prompt; ver lição no topo)."""
    for tb in page.get_by_role("textbox").all():
        try:
            ph = (tb.get_attribute("placeholder") or "")
            if re.search(r"quer criar|pesquisar|search", ph, re.I):
                continue
            if tb.is_visible():
                return tb
        except Exception:
            continue
    return None


# ---------- operações ----------
def criar_colecao(page, nome):
    """'+' -> Criar coleção -> renomeia o card 'Coleção sem título' pra `nome`."""
    fd = _fd()
    fd.dispensar_avisos(page)
    bt = page.get_by_role("button", name=re.compile(r"^add$|Adicionar m[íi]dia", re.I))
    if not bt.count():
        raise RuntimeError("botão '+' não encontrado — UI do Flow mudou")
    bt.first.click()
    fd._pausa(0.8, 1.4)
    page.get_by_role("menuitem", name=re.compile("Criar cole[cç][ãa]o", re.I)).first.click()
    fd._pausa(2.0, 3.0)
    if not renomear_colecao(page, "Coleção sem título", nome):
        raise RuntimeError(f"coleção criada mas NÃO renomeada pra '{nome}' — "
                           f"conferir na tela (não sigo pra não gerar lixo)")
    print(f"  coleção criada e renomeada: {nome}")


def renomear_colecao(page, de, para):
    """hover no card -> ⋮ -> Renomear -> digita no CAMPO CERTO -> confirma.
    Só devolve True se o card com o nome novo EXISTIR depois."""
    fd = _fd()
    lab, box = _label_da_colecao(page, de)
    if not box:
        return False
    lab.hover()
    fd._pausa(0.7, 1.1)
    tres = _botao_do_card(page, box, r"more_vert|\bMais\b|More")
    if tres is None:
        return False
    tres.click()
    fd._pausa(0.6, 1.0)
    mi = page.get_by_role("menuitem", name=re.compile("Renomear|Rename", re.I))
    if not mi.count():
        page.keyboard.press("Escape")
        return False
    mi.first.click()
    fd._pausa(0.7, 1.2)
    campo = _campo_de_renome(page)
    if campo is None:
        page.keyboard.press("Escape")
        return False
    campo.click()
    campo.fill(para)
    fd._pausa(0.3, 0.6)
    page.keyboard.press("Enter")     # o campo tem ✓ mas Enter confirma
    fd._pausa(1.2, 2.0)
    lab2, _ = _label_da_colecao(page, para)
    return lab2 is not None


def abrir_colecao(page, canal, nome, criar_se_faltar=True):
    """Entra na coleção. Com id registrado navega DIRETO (zero clique); senão,
    1 clique no MEIO do card + confirmação pela URL `/collection/<id>` (Piter 05/08).
    Devolve o id da coleção."""
    fd = _fd()
    fd.dispensar_avisos(page)
    reg = projeto_do_canal(canal) or {}
    cid = (reg.get("colecoes") or {}).get(nome)
    if cid and reg.get("projeto"):
        page.goto(f"{fd.BASE}/project/{reg['projeto']}/collection/{cid}",
                  wait_until="domcontentloaded")
        fd._pausa(2.0, 3.0)
        # 06/08 (Piter: "está gerando fora da coleção"): a rota direta é REJEITADA
        # pelo Flow — ele redireciona pra raiz do projeto — e a v1 confiava nela sem
        # olhar, imprimindo "coleção (rota direta)" enquanto gerava no lugar errado.
        # Só o clique no card entra de verdade. Conferir SEMPRE, cair no clique.
        if "/collection/" in page.url:
            print(f"  coleção (rota direta): {nome}")
            return cid
        print(f"  !! rota direta rejeitada (caiu em {page.url[-38:]}) — entrando pelo card")
    lab, box = _label_da_colecao(page, nome)
    if not box:
        if not criar_se_faltar:
            return None
        criar_colecao(page, nome)
        lab, box = _label_da_colecao(page, nome)
        if not box:
            raise RuntimeError(f"coleção '{nome}' não apareceu no grid após criar")
    # 1 clique no MEIO do card (o rótulo fica na base; o meio do card é acima dele)
    page.mouse.click(box["x"] + box["width"] / 2, box["y"] - 80)
    try:
        page.wait_for_url(re.compile(r"/collection/[0-9a-f-]{16,}"), timeout=30_000)
    except Exception:
        # clique no rótulo mesmo (card menor que o esperado)
        page.mouse.click(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
        page.wait_for_url(re.compile(r"/collection/[0-9a-f-]{16,}"), timeout=30_000)
    cid = page.url.split("/collection/")[-1][:36]
    registrar_colecao(canal, nome, cid)
    print(f"  dentro da coleção: {nome} ({cid[:8]}…)")
    return cid


def dentro_da_colecao(page, cid=None):
    """A URL tem `/collection/<id>`? Barato e suficiente pra detectar a EXPULSÃO."""
    u = page.url or ""
    return ("/collection/" in u) and (cid is None or cid in u)


def garantir_dentro(page, canal, nome, cid=None):
    """Confere que a página AINDA está na coleção e re-entra se foi expulsa.

    06/08 (Piter: "o sistema consegue verificar se realmente está dentro da coleção
    antes de gerar?"): sim — e precisa, porque a UI expulsa sozinha. O caso provado
    foi o `garantir_modo`: o popup de modelo devolve a página pro projeto, e todos
    os prompts seguintes geravam na RAIZ com a coleção intacta e vazia do lado.
    Chamar isto ANTES de cada rajada custa uma leitura de URL e fecha o buraco."""
    if dentro_da_colecao(page, cid):
        return True
    print(f"  !! fora da coleção ({(page.url or '')[-38:]}) — re-entrando")
    try:
        abrir_colecao(page, canal, nome, criar_se_faltar=False)
    except Exception as e:
        print(f"  !! re-entrada falhou: {e}")
    return dentro_da_colecao(page, cid)


def baixar_projeto(page, canal, dest_zip, timeout_ms=1_200_000):
    """⋮ do TOPO -> "Baixar projeto" -> zip com TUDO (raiz + coleções).

    05/08: o plano A era o "Baixar coleção" no hover do card, mas a aba "Todas as
    mídias" ordena por mídia recente — 70 imagens novas empurram o card da coleção
    pra baixo da dobra e a VIRTUALIZAÇÃO nunca o monta no DOM ("coleção não
    encontrada" com a coleção existindo). O ⋮ do topo está SEMPRE lá (print do
    Piter: menu com "Baixar projeto"). Zip maior, mas o casamento por título +
    guarda de tipo filtra o que não é do lote."""
    fd = _fd()
    reg = projeto_do_canal(canal) or {}
    if reg.get("projeto"):
        page.goto(f"{fd.BASE}/project/{reg['projeto']}", wait_until="domcontentloaded")
        fd._pausa(6, 9)
    fd.dispensar_avisos(page)
    # dois ⋮ no topo (o do título e o "Mais" da direita, que tem o Baixar projeto):
    # pega o MAIS À DIREITA entre os botões da barra (y<70)
    alvo, alvo_x = None, -1
    for b in page.locator("button").all():
        try:
            bb = b.bounding_box()
            if not bb or bb["y"] > 70:
                continue
            rot = (b.get_attribute("aria-label") or "") + " " + (b.inner_text(timeout=250) or "")
            if re.search(r"more_vert|\bMais\b|More", rot, re.I) and bb["x"] > alvo_x:
                alvo, alvo_x = b, bb["x"]
        except Exception:
            continue
    if alvo is None:
        raise RuntimeError("⋮ do topo não encontrado")
    alvo.click()
    fd._pausa(0.8, 1.4)
    mi = page.get_by_role("menuitem", name=re.compile("Baixar projeto|Download project", re.I))
    if not mi.count():
        page.keyboard.press("Escape")
        raise RuntimeError("menuitem 'Baixar projeto' não encontrado")
    with page.expect_download(timeout=timeout_ms) as di:
        mi.first.click()
    di.value.save_as(str(dest_zip))
    print(f"  projeto baixado: {dest_zip}")
    return Path(dest_zip)


def baixar_colecao(page, canal, nome, dest_zip, timeout_ms=900_000):
    """No grid do PROJETO: hover no card -> ⬇ 'Baixar coleção' -> salva o zip.
    Substitui as ~6 interações de UI por clipe por UM download por rodada."""
    fd = _fd()
    reg = projeto_do_canal(canal) or {}
    if reg.get("projeto"):
        page.goto(f"{fd.BASE}/project/{reg['projeto']}", wait_until="domcontentloaded")
    # 05/08: o grid do projeto leva ~8s pra montar — 2s de pausa achava grid VAZIO e
    # o erro dizia "coleção não encontrada" com a coleção existindo. Espera de
    # verdade: revarre por até 40s antes de desistir.
    lab = box = None
    t0 = _t.time()
    while _t.time() - t0 < 40:
        fd.dispensar_avisos(page)
        lab, box = _label_da_colecao(page, nome)
        if box:
            break
        _t.sleep(3)
    if not box:
        raise RuntimeError(f"coleção '{nome}' não encontrada no grid do projeto")
    lab.hover()
    fd._pausa(0.8, 1.3)
    alvo = _botao_do_card(page, box, r"download|Baixar")
    if alvo is None:
        raise RuntimeError("botão 'Baixar coleção' não apareceu no hover")
    with page.expect_download(timeout=timeout_ms) as di:
        alvo.click()
    di.value.save_as(str(dest_zip))
    print(f"  coleção baixada: {dest_zip}")
    return Path(dest_zip)
