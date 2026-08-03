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
import re
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


# SearXNG self-hosted (container `searxng`, porta 8080) — metabuscador que agrega
# Google/Bing/Brave/DDG numa consulta só. É a fonte MAIS FARTA que temos: "jararaca
# cobra" devolve 187 imagens e 88 vídeos, contra 6-12 do ddgs. `ok=None` = ainda não
# testado; ao primeiro erro vira False e para de ser consultado (sem isso, container
# parado custaria um timeout por beat na curadoria inteira).
_SEARX = {"url": os.environ.get("SEARXNG_URL", "http://localhost:8080"), "ok": None}


def _searxng(query, categoria, n):
    if _SEARX["ok"] is False or not _SEARX["url"]:
        return []
    try:
        r = httpx.get(f"{_SEARX['url'].rstrip('/')}/search", params={
            "q": query[:100], "categories": categoria, "format": "json"},
            headers=_UA, timeout=20)
        if r.status_code != 200:
            _SEARX["ok"] = False
            return []
        _SEARX["ok"] = True
        return r.json().get("results", [])[:n]
    except Exception:
        _SEARX["ok"] = False   # container fora do ar: não insiste beat a beat
        return []


def searxng_img(query, n=6):
    return [{"url": x["img_src"], "source": "searxng",
             "meta": (x.get("title") or "")[:80],
             "id": f"sx_{abs(hash(x['img_src'])) % 10**10}"}
            for x in _searxng(query, "images", n * 3)
            if x.get("img_src", "").startswith("http")
            and not any(d in x["img_src"].lower() for d in _DOM_MARCADOS)][:n]


def searxng_video(query, n=4):
    """Vídeo pelo metabuscador — mais estável que o backend `videos` do ddgs (que vive
    caindo). Devolve URL de PÁGINA; quem baixa é o yt-dlp."""
    out = []
    for x in _searxng(query, "videos", n * 4):
        u = x.get("url") or ""
        # Dailymotion FORA: o yt-dlp exige impersonation e no Windows+Python 3.14 não
        # há wheel de curl_cffi com isso compilado ("none of these impersonate targets
        # are available") — 100% de falha. É 11% do pool; YouTube (83%) cobre.
        if not re.search(r"youtube\.com/watch|youtu\.be/|vimeo\.com/\d+", u):
            continue
        out.append({"url": u, "source": "searxng_video", "_via": "ytdlp", "tier": 3,
                    "thumb": x.get("thumbnail") or None,
                    "meta": (x.get("title") or "")[:80],
                    "id": f"sxv_{abs(hash(u)) % 10**10}"})
        if len(out) >= n:
            break
    return out


# bancos que entregam a foto MARCADA (a marca some só pagando) — o Vision até veta por
# "watermark", mas cada candidato desses é uma vaga de pool e uma chamada de gate à toa
_DOM_MARCADOS = ("alamy.", "shutterstock.", "dreamstime.", "123rf.", "gettyimages.",
                 "istockphoto.", "depositphotos.", "agefotostock.", "stockphoto",
                 "premium-photo", "canstockphoto.", "vectorstock.", "zoonar.",
                 "vecteezy.", "/previews/", "watermark", "shutterstock",
                 "stock.adobe.", "ftcdn.net", "lookaside.")


def web_img(query, n=6):
    """Busca web ABERTA (ddgs — open source, sem servidor e sem key).

    01/08: é a fonte que faltava pro nicho LOCAL. O Piter mostrou por print que o
    Google acha jararaca/coral de sobra, mas Pexels & cia não têm fauna brasileira —
    o pool ficava só com stock genérico e esquema técnico. Sem infra: o SearXNG
    self-hosted (`searxng_img`) entra por cima quando a instância estiver de pé."""
    try:
        out = []
        for x in _ddgs_tentar("images", query, n * 6):  # a blacklist come metade
            u = x.get("image") or ""
            if not u.startswith("http") or any(d in u.lower() for d in _DOM_MARCADOS):
                continue
            out.append({"url": u, "source": "web", "meta": (x.get("title") or "")[:80],
                        "id": f"web_{abs(hash(u)) % 10**10}"})
            if len(out) >= n:
                break
        return out
    except Exception:
        return []


# só padrão de post que É VÍDEO: o /p/ do Instagram também é foto/carrossel e o
# yt-dlp morre com "There is no video in this post"; o vídeo do FB precisa do ID
# numérico (a URL com slug sozinho dá 404)
_PAD_POST = {"tiktok.com": r"/video/\d+",
             "instagram.com": r"/(reel|tv)/[\w-]+",
             "facebook.com": r"/videos?/[^/]+/\d+"}


def _ddgs_tentar(metodo, query, max_results, tentativas=3):
    """O ddgs LEVANTA `No results found` em vez de devolver lista vazia — e falha de
    forma intermitente quando os backends rate-limitam (numa curadoria de 70+ beats
    isso acontece o tempo todo). Retry curto com backoff; lista vazia é resposta
    legítima, não erro que derruba o beat."""
    import random
    import time
    try:
        from ddgs import DDGS
    except ImportError:
        return []
    for t in range(tentativas):
        try:
            return list(getattr(DDGS(), metodo)(query[:100], max_results=max_results))
        except Exception as e:
            if "no results" in str(e).lower() and t == tentativas - 1:
                return []
            time.sleep(1.5 * (t + 1) + random.random())
    return []


def web_video(query, n=4):
    """Vídeo por BUSCA WEB (não só nos 3 bancos de stock).

    01/08: o print do Piter mostrava TikTok/Facebook/Instagram cheios de material de
    fauna BR que Pexels & cia não têm. A busca devolve a URL da PÁGINA; quem baixa é
    o yt-dlp (`_via: ytdlp`). NÃO julgar pelo thumb: TikTok/Reels é gente falando pra
    câmera e o rosto costuma aparecer só depois do 1º frame — o veredito real sai do
    gate v4 com 6 frames DEPOIS do download (regra dura: nada de criador falando)."""
    out, vistos = [], set()
    for c in searxng_video(query, n):   # metabuscador primeiro: mais farto e estável
        vistos.add(c["url"])
        out.append(c)
    if len(out) >= n:
        return out
    for x in _ddgs_tentar("videos", query, n * 3):
        u = x.get("content") or ""
        if not u.startswith("http") or u in vistos:
            continue
        vistos.add(u)
        out.append({"url": u, "source": "web_video", "_via": "ytdlp", "tier": 3,
                    "thumb": (x.get("images") or {}).get("medium"),
                    "meta": (x.get("title") or "")[:80],
                    "id": f"wv_{abs(hash(u)) % 10**10}"})
        if len(out) >= n:
            break
    if out:
        return out
    # o backend de VÍDEO do ddgs cai com frequência (devolve 0 enquanto text/images
    # respondem) — nesse caso a busca textual acha o mesmo material
    for x in _ddgs_tentar("text", f"site:youtube.com {query[:80]}", n * 3):
        u = x.get("href") or ""
        if not re.search(r"youtube\.com/watch\?v=|youtu\.be/", u) or u in vistos:
            continue
        vistos.add(u)
        out.append({"url": u, "source": "web_video", "_via": "ytdlp", "tier": 3,
                    "thumb": None, "meta": (x.get("title") or "")[:80],
                    "id": f"wv_{abs(hash(u)) % 10**10}"})
        if len(out) >= n:
            break
    return out


def social_video(query, n=4, redes=("tiktok.com", "instagram.com", "facebook.com"),
                 query_local=""):
    """Posts de TikTok/Instagram/Facebook (yt-dlp suporta os três).

    A busca por `site:` devolve MUITA página de agregação (/discover/, /popular/) —
    só entra o que casa com o padrão de POST de verdade. E o material de nicho LOCAL
    está indexado no IDIOMA LOCAL: `site:tiktok.com brazilian venomous snake` devolve
    zero post, `site:tiktok.com jararaca cobra` devolve 18. Por isso `query_local`
    (a âncora traduzida 1x por job) é tentada JUNTO com a query em inglês."""
    out, vistos = [], set()
    consultas = [q for q in (query_local, query) if q and q.strip()]
    for rede in redes:
        pad = _PAD_POST.get(rede)
        for consulta in consultas:
            for x in _ddgs_tentar("text", f"site:{rede} {consulta[:80]}", 10):
                h = x.get("href") or ""
                if not pad or not re.search(pad, h) or h in vistos:
                    continue
                vistos.add(h)
                out.append({"url": h, "source": rede.split(".")[0], "_via": "ytdlp",
                            "tier": 3, "thumb": None,
                            "meta": (x.get("title") or "")[:80],
                            "id": f"sv_{abs(hash(h)) % 10**10}"})
                if len([o for o in out if o["source"] == rede.split(".")[0]]) >= n:
                    break
            if len([o for o in out if o["source"] == rede.split(".")[0]]) >= n:
                break  # já tem o bastante desta rede: não gasta a 2ª consulta
    return out


def coletar_imagens(query, n_por_fonte=3, usados=None):
    """Todas as fontes de imagem em paralelo -> candidatos dedupados."""
    from concurrent.futures import ThreadPoolExecutor
    usados = usados or set()
    with ThreadPoolExecutor(max_workers=5) as ex5:
        futs = [ex5.submit(f, query, n_por_fonte) for f in
                (pixabay_img, unsplash_img, openverse_img, searxng_img, web_img)]
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
