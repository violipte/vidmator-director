# -*- coding: utf-8 -*-
"""BUSCA DE IMAGEM REAL na web (R-105) — para ILUSTRAÇÃO TÉCNICA: em vez de gerar por IA,
achar a imagem que JÁ EXISTE (diagrama de manual, anatomia de livro, cutaway) e tratá-la
pela régua de TIER: fonte web/desconhecida = T3 = máscara pesada na montagem.
Decisão Piter 22/07: "quero uma imagem que realmente se aproxime do que seria gerado
pela IA; copyright entra na classificação de tier como o resto do footage".

Fonte: Bing Images (scrape do murl, sem API key). Gate Vision valida DEPOIS — aqui só
busca+download. Uso standalone: python imagens_web.py "knee joint anatomy diagram"
"""
import json
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"}

# Piter 22/07: "não quero banco de stock" — previews watermarkados desses domínios NUNCA
DOMINIOS_BANIDOS = ("shutterstock", "alamy", "dreamstime", "istockphoto", "gettyimages",
                    "123rf", "depositphotos", "ftcdn", "adobe", "bigstock", "vectorstock",
                    "stockphoto", "fotolia", "canstockphoto")


def _dominio_ok(u):
    return not any(d in u.lower() for d in DOMINIOS_BANIDOS)


def _ddg(query, n):
    """DuckDuckGo images via lib `ddgs` (handshake vqd mantido pela lib)."""
    from ddgs import DDGS
    urls = []
    with DDGS() as d:
        for it in d.images(query, max_results=n * 3):
            u = (it.get("image") or "")
            try:
                w = int(it.get("width") or 0)  # ddgs às vezes devolve width como string
            except Exception:
                w = 0
            if u.lower().split("?")[0].endswith((".jpg", ".jpeg", ".png")) and u not in urls \
                    and _dominio_ok(u) and w >= 640:
                urls.append(u)
            if len(urls) >= n:
                break
    return urls


def _bing(query, n):
    q = urllib.parse.quote(query)
    html = urllib.request.urlopen(urllib.request.Request(
        f"https://www.bing.com/images/search?q={q}&form=HDRSC2&first=1", headers=UA), timeout=25).read().decode("utf-8", "ignore")
    urls = []
    # resultados vêm como links com mediaurl=<URL url-encoded>
    for m in re.finditer(r"mediaurl=([^&\"']+)", html):
        u = urllib.parse.unquote(m.group(1))
        if u.lower().split("?")[0].endswith((".jpg", ".jpeg", ".png")) and u not in urls and _dominio_ok(u):
            urls.append(u)
        if len(urls) >= n:
            break
    return urls


def buscar_imagens_web(query, n=8):
    """URLs de imagens reais da web: DDG (JSON estável) com fallback Bing."""
    for fonte in (_ddg, _bing):
        try:
            urls = fonte(query, n)
            if urls:
                return urls
        except Exception as e:
            print(f"  [imagens_web] {fonte.__name__} falhou: {str(e)[:60]}")
    return []


def baixar_imagem(url, dest, min_kb=25):
    try:
        data = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=25).read()
        if len(data) < min_kb * 1024:
            return False
        if not (data[:2] == b"\xff\xd8" or data[:8] == b"\x89PNG\r\n\x1a\n"):
            return False
        Path(dest).write_bytes(data)
        return True
    except Exception:
        return False


if __name__ == "__main__":
    q = sys.argv[1] if len(sys.argv) > 1 else "V-twin engine cutaway diagram"
    urls = buscar_imagens_web(q)
    print(json.dumps(urls[:8], indent=1))
    print(f"{len(urls)} candidatas")
