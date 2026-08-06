# -*- coding: utf-8 -*-
"""SONDA DE REDE (06/08) — para ONDE o Flow manda a geração, de verdade.

Por que existe: a URL `/collection/<id>` NÃO é prova. Ela continua na barra
enquanto o app posta no projeto, e contar cards na tela também engana (o grid é
virtualizado e um seletor frouxo conta ícone da barra lateral como card — foi
assim que a sonda v2 deu um PASSOU falso, pego pelo Piter no print).

A única fonte de verdade é a REQUISIÇÃO que sai do navegador quando o prompt é
enviado. Esta sonda entra na coleção, escuta a rede, manda UM prompt (Nano
Banana = 0 crédito) e imprime o corpo da chamada de geração — se o id da coleção
estiver lá, dá pra gerar dentro dela; se não estiver, gerar-dentro-da-coleção
não existe na API e o caminho é gerar e DEPOIS mover.

Uso: "F:/Canal Dark/veo_venv/Scripts/python.exe" veo_sonda_rede.py --canal AMZ \
         --colecao SONDA-06-08
"""
import argparse
import json
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, r"F:/Canal Dark/Aplicativo de Edição/veo_flow")
sys.stdout.reconfigure(encoding="utf-8")

import flow_driver as fd                                          # noqa: E402
from veo_colecao import projeto_do_canal                          # noqa: E402
from veo_sonda_colecao import _shot                               # noqa: E402

SAIDA = Path(r"F:/Canal Dark/Aplicativo de Edição/veo_flow/_sonda")


def sondar(canal, nome_col):
    reg = projeto_do_canal(canal) or {}
    proj, cid = reg.get("projeto"), (reg.get("colecoes") or {}).get(nome_col)
    if not (proj and cid):
        print(f"faltando registro: projeto={proj} colecao={cid}")
        return
    print(f"=== SONDA DE REDE — projeto {proj[:8]}… / coleção {nome_col} ({cid[:8]}…) ===\n")
    pw, ctx, page = fd.abrir(headless=False)
    capturadas = []

    def _ouvir(req):
        if req.method not in ("POST", "PUT", "PATCH"):
            return
        try:
            corpo = req.post_data or ""
        except Exception:
            corpo = ""
        if not corpo:
            return
        # só o que cheira a geração/mídia (evita telemetria)
        if not re.search(r"(generat|create|media|prompt|image|video|asset|workflow)",
                         req.url + corpo[:800], re.I):
            return
        capturadas.append({"url": req.url, "metodo": req.method, "corpo": corpo[:6000]})

    page.on("request", _ouvir)
    try:
        page.goto(f"{fd.BASE}/project/{proj}/collection/{cid}", wait_until="domcontentloaded")
        fd._pausa(3.0, 4.0)
        fd.dispensar_avisos(page)
        print(f"URL: {page.url}")
        fd.garantir_modo(page, "imagem")
        capturadas.clear()                     # descarta o tráfego de abertura
        print("\nescutando a rede e enviando UM prompt...")
        fd.enviar_prompt(page, "A single plain grey ceramic mug centered on a white "
                               "studio background, soft even light, product photo")
        time.sleep(12)

        SAIDA.mkdir(parents=True, exist_ok=True)
        (SAIDA / "rede.json").write_text(json.dumps(capturadas, ensure_ascii=False, indent=1),
                                         encoding="utf-8")
        print(f"\n{len(capturadas)} requisições candidatas -> _sonda/rede.json\n")
        achou_col = False
        for c in capturadas:
            tem_proj = proj in c["corpo"]
            tem_col = cid in c["corpo"]
            achou_col = achou_col or tem_col
            marca = "COLEÇÃO" if tem_col else ("projeto" if tem_proj else "       ")
            print(f"  [{marca}] {c['metodo']} {c['url'][:78]}")
            if tem_proj or tem_col:
                # mostra a vizinhança do id no corpo — é onde o campo aparece
                alvo = cid if tem_col else proj
                i = c["corpo"].find(alvo)
                print(f"      …{c['corpo'][max(0, i - 110):i + 60]}…")
        print("\n=== VEREDITO ===")
        if achou_col:
            print("  o id da COLEÇÃO viaja no corpo da geração -> DÁ pra gerar dentro dela")
        else:
            print("  NENHUMA requisição carrega o id da coleção -> a API não aceita")
            print("  coleção como destino de geração; o caminho é gerar e DEPOIS mover.")
        _shot(page, "7_rede")
    finally:
        ctx.close()
        pw.stop()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--canal", required=True)
    ap.add_argument("--colecao", required=True)
    a = ap.parse_args()
    sondar(a.canal, a.colecao)
