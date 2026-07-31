# -*- coding: utf-8 -*-
"""FONTES DE FOOTAGE v5 (F6) — providers novos absorvidos do dark-content-studio.

Imagem:  pixabay · unsplash · openverse (CC, sem key!) — somam ao pexels do executor
Vídeo:   pixabay_video · coverr — somam ao pexels/yt do executor
Web:     searxng (self-hosted, opcional via SEARXNG_URL)

Todos retornam listas de candidatos {url, source, meta} SEM baixar — a escolha é do
gate5 (batch score). Keys em video-automator/credentials.json (gitignored):
  {"provedor": "pixabay"|"unsplash"|"coverr", "api_key": "..."}
"""
import json
import os
import sys
from pathlib import Path

import httpx

sys.stdout.reconfigure(encoding="utf-8")
_CREDS = Path(r"F:/Canal Dark/Aplicativo de Edição/video-automator/credentials.json")
_UA = {"User-Agent": "Mozilla/5.0"}


def _key5(provedor):
    try:
        return next(c["api_key"] for c in json.loads(_CREDS.read_text(encoding="utf-8"))
                    if c.get("provedor") == provedor and c.get("api_key"))
    except Exception:
        return None


def pixabay_img(query, n=3):
    k = _key5("pixabay")
    if not k:
        return []
    try:
        r = httpx.get("https://pixabay.com/api/", params={
            "key": k, "q": query[:100], "image_type": "photo", "per_page": max(3, n),
            "min_width": 1280, "safesearch": "true"}, headers=_UA, timeout=25)
        return [{"url": h["largeImageURL"], "source": "pixabay", "id": f"pxb_{h['id']}"}
                for h in r.json().get("hits", [])[:n]] if r.status_code == 200 else []
    except Exception:
        return []


def unsplash_img(query, n=3):
    k = _key5("unsplash")
    if not k:
        return []
    try:
        r = httpx.get("https://api.unsplash.com/search/photos", params={
            "query": query[:100], "per_page": n, "orientation": "landscape"},
            headers={**_UA, "Authorization": f"Client-ID {k}"}, timeout=25)
        return [{"url": p["urls"]["regular"], "source": "unsplash", "id": f"uns_{p['id']}"}
                for p in r.json().get("results", [])[:n]] if r.status_code == 200 else []
    except Exception:
        return []


def openverse_img(query, n=3):
    """Creative Commons — SEM key. Encaixa no nosso T2."""
    try:
        r = httpx.get("https://api.openverse.org/v1/images/", params={
            "q": query[:100], "page_size": n, "license_type": "commercial",
            "aspect_ratio": "wide"}, headers=_UA, timeout=25)
        return [{"url": x["url"], "source": "openverse", "id": f"opv_{x['id'][:12]}",
                 "licenca": x.get("license")}
                for x in r.json().get("results", [])[:n] if x.get("url")] if r.status_code == 200 else []
    except Exception:
        return []


def pexels_video(query, n=3):
    """Pexels no POOL v5 (decisão Piter 31/07: Pexels é a key mantida) — usa a
    mesma rotação de keys do executor (pexels_api.KEYS)."""
    try:
        from pexels_api import KEYS as PK
        k = PK[0] if PK else None
        if not k:
            return []
        r = httpx.get("https://api.pexels.com/videos/search", params={
            "query": query[:100], "per_page": max(3, n), "orientation": "landscape"},
            headers={**_UA, "Authorization": k}, timeout=25)
        out = []
        for v in r.json().get("videos", [])[:n]:
            arqs = sorted((f for f in v.get("video_files", []) if f.get("width")),
                          key=lambda f: -f["width"])
            if arqs:
                out.append({"url": arqs[0]["link"], "source": "pexels", "id": f"pexv_{v['id']}",
                            "thumb": v.get("image"), "meta": ""})
        return out if r.status_code == 200 else []
    except Exception:
        return []


def pixabay_video(query, n=3):
    k = _key5("pixabay")
    if not k:
        return []
    try:
        r = httpx.get("https://pixabay.com/api/videos/", params={
            "key": k, "q": query[:100], "per_page": max(3, n), "safesearch": "true"}, headers=_UA, timeout=25)
        out = []
        for h in r.json().get("hits", [])[:n]:
            v = h.get("videos", {}).get("large") or h.get("videos", {}).get("medium") or {}
            if v.get("url"):
                out.append({"url": v["url"], "source": "pixabay_video", "id": f"pxbv_{h['id']}",
                            "thumb": (h.get("videos", {}).get("tiny") or {}).get("thumbnail")
                            or f"https://i.vimeocdn.com/video/{h.get('picture_id', '')}_295x166.jpg",
                            "meta": h.get("tags", "")})
        return out if r.status_code == 200 else []
    except Exception:
        return []


def coverr_video(query, n=3):
    k = _key5("coverr")
    if not k:
        return []
    try:
        r = httpx.get("https://api.coverr.co/videos", params={"query": query[:100], "page_size": n},
                      headers={**_UA, "Authorization": f"Bearer {k}"}, timeout=25)
        out = []
        for h in (r.json().get("hits") or [])[:n]:
            base = h.get("base_filename")
            if base:  # mp4 é derivável do base_filename (detail confirmou o padrão 1080p)
                out.append({"url": f"https://cdn.coverr.co/videos/{base}/1080p.mp4",
                            "source": "coverr", "id": f"cvr_{h.get('id', '')[:12]}",
                            "thumb": h.get("thumbnail"), "meta": h.get("title", "")})
        return out if r.status_code == 200 else []
    except Exception:
        return []


def searxng_img(query, n=5):
    """Busca web GRÁTIS via instância self-hosted (Bing+Brave+DDG). Opcional."""
    base = os.environ.get("SEARXNG_URL", "")
    if not base:
        return []
    try:
        r = httpx.get(f"{base.rstrip('/')}/search", params={
            "q": query[:100], "categories": "images", "format": "json"}, headers=_UA, timeout=25)
        return [{"url": x.get("img_src"), "source": "searxng", "id": f"sx_{abs(hash(x.get('img_src',''))) % 10**10}"}
                for x in r.json().get("results", [])[:n] if x.get("img_src")] if r.status_code == 200 else []
    except Exception:
        return []


def coletar_imagens(query, n_por_fonte=3, usados=None):
    """Todas as fontes de imagem em paralelo -> candidatos dedupados."""
    from concurrent.futures import ThreadPoolExecutor
    usados = usados or set()
    with ThreadPoolExecutor(max_workers=5) as ex5:
        futs = [ex5.submit(f, query, n_por_fonte) for f in
                (pixabay_img, unsplash_img, openverse_img, searxng_img)]
        tudo = [c for fu in futs for c in fu.result()]
    vistos, out = set(usados), []
    for c in tudo:
        if c["url"] not in vistos and c.get("id") not in vistos:
            vistos.add(c["url"])
            out.append(c)
    return out


def coletar_videos(query, n_por_fonte=3, usados=None):
    from concurrent.futures import ThreadPoolExecutor
    usados = usados or set()
    with ThreadPoolExecutor(max_workers=3) as ex5:
        futs = [ex5.submit(f, query, n_por_fonte) for f in (pexels_video, pixabay_video, coverr_video)]
        tudo = [c for fu in futs for c in fu.result()]
    vistos, out = set(usados), []
    for c in tudo:
        if c["url"] not in vistos and c.get("id") not in vistos:
            vistos.add(c["url"])
            out.append(c)
    return out


if __name__ == "__main__":
    q = sys.argv[1] if len(sys.argv) > 1 else "ancient greek temple ruins"
    print("imagens:", [(c["source"], c["id"]) for c in coletar_imagens(q)])
    print("videos:", [(c["source"], c["id"]) for c in coletar_videos(q)])
