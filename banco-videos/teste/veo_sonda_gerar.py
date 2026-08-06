# -*- coding: utf-8 -*-
"""SONDA v3 (06/08) — entrar pelo CARD e provar VISUALMENTE onde a geração cai.

As duas sondas anteriores mentiram, cada uma do seu jeito:
  v2  contou `img` da página e somou ícone de barra lateral como card -> PASSOU falso;
  rede  capturou só o beacon do Analytics (que carrega a URL antiga) -> veredito falso.

Esta não interpreta nada: entra pelo CLIQUE no card (a rota direta por URL é
rejeitada pelo Flow), manda UM prompt, espera, e tira PRINT dos dois lugares —
dentro da coleção e na raiz. Quem julga é o olho.

Uso: "F:/Canal Dark/veo_venv/Scripts/python.exe" veo_sonda_gerar.py --canal AMZ \
         --colecao SONDA-06-08
"""
import argparse
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, r"F:/Canal Dark/Aplicativo de Edição/veo_flow")
sys.stdout.reconfigure(encoding="utf-8")

import flow_driver as fd                                          # noqa: E402
from veo_colecao import projeto_do_canal, _label_da_colecao       # noqa: E402
from veo_sonda_colecao import _shot                               # noqa: E402


def sondar(canal, nome_col):
    reg = projeto_do_canal(canal) or {}
    proj = reg.get("projeto")
    print(f"=== SONDA v3 — entrar pelo CARD e gerar 1 imagem ===\n")
    pw, ctx, page = fd.abrir(headless=False)
    try:
        page.goto(f"{fd.BASE}/project/{proj}", wait_until="domcontentloaded")
        fd._pausa(3.0, 4.0)
        fd.dispensar_avisos(page)

        print("0) conferindo o modo AINDA NA RAIZ (o popup expulsa da coleção)")
        fd.garantir_modo(page, "imagem")
        fd._pausa(1.5, 2.5)

        lab, box = _label_da_colecao(page, nome_col)
        if not box:
            print(f"card '{nome_col}' não achado — abortando")
            return
        print(f"1) clicando no card '{nome_col}'")
        page.mouse.click(box["x"] + box["width"] / 2, box["y"] - 80)
        try:
            page.wait_for_url(re.compile(r"/collection/[0-9a-f-]{16,}"), timeout=30_000)
        except Exception:
            page.mouse.click(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
            page.wait_for_url(re.compile(r"/collection/[0-9a-f-]{16,}"), timeout=30_000)
        fd._pausa(2.0, 3.0)
        url_col = page.url
        print(f"   URL: {url_col}")
        if "/collection/" not in url_col:
            print("   !! não entrou — abortando")
            return
        _shot(page, "v3_1_dentro_antes")

        print("2) enviando UM prompt JÁ dentro da coleção (sem tocar no popup)")
        fd.enviar_prompt(page, "A single plain grey ceramic mug centered on a white "
                               "studio background, soft even light, product photo")
        print(f"   URL logo após enviar: {page.url[-52:]}")
        _shot(page, "v3_2_apos_enviar")

        print("3) esperando 90s e olhando os DOIS lugares")
        time.sleep(90)
        page.goto(f"{fd.BASE}/project/{proj}", wait_until="domcontentloaded")
        fd._pausa(3.0, 4.0)
        lab, box = _label_da_colecao(page, nome_col)
        _shot(page, "v3_3_raiz")
        if box:
            page.mouse.click(box["x"] + box["width"] / 2, box["y"] - 80)
            try:
                page.wait_for_url(re.compile(r"/collection/[0-9a-f-]{16,}"), timeout=30_000)
            except Exception:
                pass
            fd._pausa(3.5, 4.5)
        _shot(page, "v3_4_dentro_depois")
        print("\nPRINTS: v3_3_raiz.png (raiz) e v3_4_dentro_depois.png (coleção).")
        print("Se a caneca estiver SÓ na raiz -> gerar dentro da coleção não existe.")
    finally:
        ctx.close()
        pw.stop()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--canal", required=True)
    ap.add_argument("--colecao", required=True)
    a = ap.parse_args()
    sondar(a.canal, a.colecao)
