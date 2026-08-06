# -*- coding: utf-8 -*-
"""SONDA DA COLEÇÃO (06/08, pedido do Piter) — entrar de verdade, provar, sair.

Contexto: o ciclo entrou na coleção (URL `/collection/<id>` confirmada) e mesmo
assim as gerações caíram na RAIZ do projeto. Antes de mexer em geração, esta sonda
responde uma pergunta de cada vez, SEM GERAR NADA:

  1. abre o projeto do canal            -> prova: URL + título na tela
  2. cria (ou acha) a coleção            -> prova: card no grid
  3. ENTRA na coleção                    -> prova: URL + cabeçalho + barra de prompt
  4. espera e RE-CHECA                   -> pega redirect tardio do SPA (hidratação)
  5. sai da coleção                      -> prova: voltou pro projeto

Cada passo grava screenshot em <veo_flow>/_sonda/ e imprime PASSOU/FALHOU.

Uso:  "F:/Canal Dark/veo_venv/Scripts/python.exe" veo_sonda_colecao.py \
          --canal AMZ --colecao SONDA-06-08 [--manter]
(--manter deixa o browser aberto no fim pra inspeção manual)
"""
import argparse
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, r"F:/Canal Dark/Aplicativo de Edição/veo_flow")
sys.stdout.reconfigure(encoding="utf-8")

import flow_driver as fd                                    # noqa: E402
from veo_colecao import projeto_do_canal, criar_colecao, _label_da_colecao  # noqa: E402

SHOTS = Path(r"F:/Canal Dark/Aplicativo de Edição/veo_flow/_sonda")


def _shot(page, nome):
    SHOTS.mkdir(parents=True, exist_ok=True)
    p = SHOTS / f"{nome}.png"
    try:
        page.screenshot(path=str(p))
        print(f"      [shot] {p.name}")
    except Exception as e:
        print(f"      [shot falhou: {e}]")


def _ok(cond, msg):
    print(f"   {'PASSOU ' if cond else 'FALHOU '} {msg}")
    return bool(cond)


def _titulo_na_tela(page, esperado=""):
    """O nome do contexto atual (topo esquerdo). O Flow NÃO usa h1/h2 aqui — a v1
    da sonda deu falso-negativo por isso (o print mostrava 'SONDA-06-08' na tela
    enquanto o teste dizia FALHOU). Procura o texto esperado em qualquer elemento
    da faixa superior e, sem esperado, devolve o 1º texto curto do topo."""
    if esperado:
        try:
            el = page.get_by_text(esperado, exact=True).first
            if el.count() and el.is_visible(timeout=1500):
                cx = el.bounding_box()
                if cx and cx["y"] < 120:
                    return esperado
        except Exception:
            pass
    try:
        for el in page.locator("body *").all()[:400]:
            bb = el.bounding_box()
            if not bb or bb["y"] > 90 or bb["x"] > 500 or bb["width"] > 420:
                continue
            t = (el.inner_text(timeout=300) or "").strip()
            if 2 <= len(t) <= 60 and "\n" not in t:
                return t
    except Exception:
        pass
    return ""


def _conta_cards(page):
    """Quantos cards de mídia a vista atual mostra (grid virtualizado: aproximado)."""
    for sel in ('video', 'img[src*="blob"]', '[role="button"] img', 'img'):
        try:
            n = page.locator(sel).count()
            if n:
                return n
        except Exception:
            pass
    return 0


def sondar(canal, nome_col, manter=False, gerar=False):
    reg = projeto_do_canal(canal) or {}
    proj = reg.get("projeto")
    if not proj:
        print(f"canal {canal} sem projeto registrado — abortando")
        return False
    print(f"=== SONDA {canal} / coleção '{nome_col}' — NENHUMA GERAÇÃO ===\n")
    pw, ctx, page = fd.abrir(headless=False)
    passos = {}
    try:
        # ---- 1. PROJETO ----------------------------------------------------
        print("1) abrir o projeto do canal")
        page.goto(f"{fd.BASE}/project/{proj}", wait_until="domcontentloaded")
        fd._pausa(2.5, 3.5)
        fd.dispensar_avisos(page)
        passos["projeto"] = _ok(f"/project/{proj}" in page.url, f"URL do projeto ({page.url[-46:]})")
        print(f"      título na tela: '{_titulo_na_tela(page)}'")
        _shot(page, "1_projeto")

        # ---- 2. COLEÇÃO EXISTE? --------------------------------------------
        print("\n2) achar ou criar a coleção")
        lab, box = _label_da_colecao(page, nome_col)
        if not box:
            print("      não existe — criando")
            criar_colecao(page, nome_col)
            fd._pausa(2.0, 3.0)
            lab, box = _label_da_colecao(page, nome_col)
        passos["card"] = _ok(bool(box), f"card '{nome_col}' presente no grid")
        if box:
            print(f"      card em x={box['x']:.0f} y={box['y']:.0f} "
                  f"{box['width']:.0f}x{box['height']:.0f}")
        _shot(page, "2_card")

        # ---- 3. ENTRAR ------------------------------------------------------
        print("\n3) ENTRAR na coleção (clique no meio do card)")
        if box:
            page.mouse.click(box["x"] + box["width"] / 2, box["y"] - 80)
            try:
                page.wait_for_url(re.compile(r"/collection/[0-9a-f-]{16,}"), timeout=30_000)
            except Exception:
                page.mouse.click(box["x"] + box["width"] / 2,
                                 box["y"] + box["height"] / 2)
                try:
                    page.wait_for_url(re.compile(r"/collection/[0-9a-f-]{16,}"), timeout=30_000)
                except Exception:
                    pass
        fd._pausa(2.0, 3.0)
        url_dentro = page.url
        cid_col = url_dentro.split("/collection/")[-1][:36]
        passos["entrou"] = _ok("/collection/" in url_dentro, f"URL virou coleção ({url_dentro[-46:]})")
        tit = _titulo_na_tela(page, nome_col)
        print(f"      título na tela: '{tit}'")
        passos["cabecalho"] = _ok(nome_col.lower() in (tit or "").lower(),
                                  f"cabeçalho mostra '{nome_col}'  <- prova de que a VIEW mudou")
        # a barra de prompt existe aqui dentro?
        try:
            cx = page.locator('[contenteditable="true"]').first
            tem_barra = cx.count() > 0 and cx.is_visible(timeout=3000)
        except Exception:
            tem_barra = False
        passos["barra"] = _ok(tem_barra, "barra de prompt VISÍVEL dentro da coleção")
        _shot(page, "3_dentro")

        # ---- 4. RE-CHECAR (redirect tardio) ---------------------------------
        print("\n4) esperar 12s e re-checar (SPA às vezes volta sozinho)")
        time.sleep(12)
        url_depois = page.url
        passos["ficou"] = _ok(url_depois == url_dentro,
                              f"continua na coleção depois de 12s ({url_depois[-46:]})")
        if url_depois != url_dentro:
            print(f"      !! REDIRECT: {url_dentro[-40:]} -> {url_depois[-40:]}")
        print(f"      título na tela agora: '{_titulo_na_tela(page, nome_col)}'")
        _shot(page, "4_recheque")

        # ---- 5. SAIR --------------------------------------------------------
        print("\n5) sair da coleção (voltar pro projeto)")
        page.goto(f"{fd.BASE}/project/{proj}", wait_until="domcontentloaded")
        fd._pausa(2.0, 3.0)
        passos["saiu"] = _ok("/collection/" not in page.url, "voltou pro projeto")
        _shot(page, "5_saiu")

        # ---- 6. UMA geração de teste: ONDE ela cai? -------------------------
        if gerar:
            print("\n6) gerar UMA imagem DENTRO da coleção e ver onde ela cai")
            page.goto(f"{fd.BASE}/project/{proj}/collection/{cid_col}",
                      wait_until="domcontentloaded")
            fd._pausa(2.5, 3.5)
            fd.dispensar_avisos(page)
            fd.garantir_modo(page, "imagem")
            n_antes = _conta_cards(page)
            print(f"      cards na coleção ANTES: {n_antes}")
            fd.enviar_prompt(page, "A single plain grey ceramic mug centered on a white "
                                   "studio background, soft even light, product photo")
            print("      enviado — esperando 80s")
            time.sleep(80)
            page.reload(wait_until="domcontentloaded")
            fd._pausa(3.5, 4.5)
            n_col = _conta_cards(page)
            print(f"      cards na coleção DEPOIS: {n_col}")
            passos["gerou_na_colecao"] = _ok(n_col > n_antes,
                                             "a geração APARECE dentro da coleção")
            _shot(page, "6_dentro_apos_gerar")
            page.goto(f"{fd.BASE}/project/{proj}", wait_until="domcontentloaded")
            fd._pausa(3.5, 4.5)
            print(f"      cards na RAIZ do projeto: {_conta_cards(page)}")
            _shot(page, "6_raiz_apos_gerar")

        print("\n=== RESUMO ===")
        for k, v in passos.items():
            print(f"   {k:<10} {'ok' if v else 'FALHOU'}")
        return all(passos.values())
    finally:
        if manter:
            input("\n[--manter] browser aberto — ENTER pra fechar... ")
        ctx.close()
        pw.stop()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--canal", required=True)
    ap.add_argument("--colecao", required=True)
    ap.add_argument("--manter", action="store_true")
    ap.add_argument("--gerar", action="store_true",
                    help="passo 6: gera UMA imagem (Nano Banana, 0 crédito) pra ver onde cai")
    a = ap.parse_args()
    sondar(a.canal, a.colecao, manter=a.manter, gerar=a.gerar)
