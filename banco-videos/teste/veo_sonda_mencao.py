# -*- coding: utf-8 -*-
"""SONDA DA MENÇÃO (06/08) — o que EXATAMENTE fica no campo depois do chip.

Motivo: com o host renomeado, os takes começaram a ser descartados pela guarda
"nome em texto puro". O log mostra que a opção é achada e o chip entra — então a
suspeita é que a guarda esteja contando errado (o chip pode render o nome mais de
uma vez no inner_text: rótulo acessível + visível). Já errei duas vezes hoje
medindo em vez de olhar, então esta sonda só OLHA:

  entra na coleção -> digita corpo + @nome -> escolhe a opção -> Incluir no comando
  -> imprime o inner_text CRU, o HTML do campo e quantas vezes o nome aparece
  -> tira print. NÃO ENVIA (não aperta Enter).

Uso: "F:/Canal Dark/veo_venv/Scripts/python.exe" veo_sonda_mencao.py --canal AMZ \
         --colecao 06-08-26
"""
import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, r"F:/Canal Dark/Aplicativo de Edição/veo_flow")
sys.stdout.reconfigure(encoding="utf-8")

import flow_driver as fd                                          # noqa: E402
from veo_colecao import abrir_colecao                             # noqa: E402
from veo_personagem import personagem_do_canal                    # noqa: E402
from veo_sonda_colecao import _shot                               # noqa: E402


def sondar(canal, colecao):
    ficha = personagem_do_canal(canal)
    nome = ficha["nome"]
    corpo = ("stands facing the lens in the australian bushland, speaking naturally, "
             "static tripod 35mm")
    print(f"=== SONDA DA MENÇÃO — @{nome} (NÃO envia) ===\n")
    pw, ctx, page = fd.abrir(headless=False)
    try:
        from veo_colecao import projeto_do_canal
        proj = (projeto_do_canal(canal) or {}).get("projeto")
        page.goto(f"{fd.BASE}/project/{proj}", wait_until="domcontentloaded")
        fd._pausa(5, 8)
        fd.dispensar_avisos(page)
        fd.garantir_modo(page, "video")
        abrir_colecao(page, canal, colecao, criar_se_faltar=False)
        fd.dispensar_avisos(page)
        cx = page.locator('[contenteditable="true"]').first
        cx.click()
        fd._pausa(0.3, 0.6)
        page.keyboard.insert_text(corpo)
        fd._pausa(0.5, 0.9)

        for corte in sorted({3, 6, len(nome)}):
            page.keyboard.type(" @" + nome[:corte] if corte == 3 else nome[3:corte],
                               delay=130)
            fd._pausa(1.6, 2.2)
            ops = page.locator('[role="option"]')
            n = ops.count()
            print(f"digitado '@{nome[:corte]}': {n} opções")
            for i in range(min(n, 6)):
                try:
                    print(f"    [{i}] {ops.nth(i).inner_text(timeout=800)[:60]!r}")
                except Exception:
                    pass
            alvo = ops.filter(has_text=re.compile(re.escape(nome), re.I)).filter(
                has_text=re.compile("Personagem|Character", re.I))
            if alvo.count():
                print(f"  -> opção de PERSONAGEM encontrada com '{nome[:corte]}'")
                _shot(page, "m1_lista")
                alvo.first.click()
                fd._pausa(1.0, 1.6)
                _shot(page, "m2_detalhe")
                inc = page.get_by_role("button",
                                       name=re.compile("Incluir no comando|Include", re.I))
                print(f"  botão 'Incluir no comando': {inc.count()}")
                if inc.count():
                    inc.first.click()
                    fd._pausa(1.2, 1.8)
                break

        _shot(page, "m3_campo_apos_chip")
        txt = cx.inner_text(timeout=3000) or ""
        html = cx.inner_html(timeout=3000) or ""
        print("\n--- inner_text CRU do campo ---")
        print(repr(txt[:400]))
        print(f"\nocorrências de '{nome}' no inner_text: "
              f"{len(re.findall(re.escape(nome), txt, re.I))}")
        print("\n--- inner_html (500 chars) ---")
        print(html[:500])
        print("\nNÃO enviei (sem Enter). Confira o print m3_campo_apos_chip.png")
    finally:
        ctx.close()
        pw.stop()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--canal", required=True)
    ap.add_argument("--colecao", required=True)
    a = ap.parse_args()
    sondar(a.canal, a.colecao)
