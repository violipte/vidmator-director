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


# ---------------------------------------------------------------- iNaturalist
# Acervo de ciência cidadã: a foto JÁ foi identificada como a espécie X por
# especialistas humanos (research grade). Para beat que nomeia um ser vivo isso é
# verdade documental, não palpite de Vision — o gate de RELEVÂNCIA pode ser pulado
# (os de DEFEITO não). Sem key; API pública.
#
# LICENÇA (trava dura, decisão 02/08): só `cc0` e `cc-by`.
#   - cc0    -> T1 (sem obrigação, igual PD do Commons em executor_beats:111)
#   - cc-by  -> T2 (exige crédito na descrição — vem pronto em `atribuicao`)
#   - cc-by-sa  FORA: ShareAlike obrigaria licenciar o VÍDEO INTEIRO como SA.
#   - *-nc/*-nd FORA: NC proíbe uso comercial (canal monetizado É comercial) e ND
#     proíbe derivada — Ken Burns + crop 16:9 + grade É obra derivada.
#   NC/ND não viram T3: T3 mitiga risco de IP com máscara, e máscara não conserta
#   licença. Se não pode, não entra.
_INAT = "https://api.inaturalist.org/v1"
_INAT_LIC = "cc0,cc-by"
_INAT_TIER = {"cc0": 1, "cc-by": 2}
_INAT_STOP = {"the", "a", "an", "of", "in", "on", "at", "with", "and", "or", "for", "to",
              "close", "up", "shot", "wide", "detail", "macro", "moody", "cinematic",
              "brazilian", "brazil", "wild", "wildlife", "nature", "footage", "video"}


def _inat_norm(s):
    """normaliza pra comparar termo x matched_term (plural simples tolerado)."""
    s = " ".join((s or "").lower().split())
    return s[:-1] if s.endswith("s") else s


def _inat_taxon(termo):
    """nome (comum ou científico, PT ou EN) -> taxon do iNaturalist, ou None.

    ⚠️ O iNat tem nome científico pra TUDO, então busca frouxa sempre casa alguma
    coisa: 'harley' casou `Harleya` (uma planta) e 'venomous' casou `venomous king`
    (uma naja das Filipinas) — os dois iam parar no vídeo. A defesa é o campo
    `matched_term`: só vale se o que casou FOR o termo buscado (plural tolerado:
    'coral snake' x 'Coral Snakes'). Prefixo de epíteto científico não passa.
    rank_level > 30 também cai fora: 'snake' -> Serpentes ilustra qualquer cobra
    do planeta, o que é o oposto de precisão."""
    try:
        r = httpx.get(f"{_INAT}/taxa/autocomplete", params={"q": termo[:60], "per_page": 5},
                      headers=_UA, timeout=20)
        alvo = _inat_norm(termo)
        cands = [t for t in (r.json().get("results") or [])
                 if t.get("rank_level") and t["rank_level"] <= 30 and t.get("ancestor_ids")
                 and _inat_norm(t.get("matched_term")) == alvo]
        if not cands:
            return None
        return sorted(cands, key=lambda t: (t["rank_level"], -t.get("observations_count", 0)))[0]
    except Exception:
        return None


def _inat_escada(taxon, strict=False):
    """P1 espécie -> P2 gênero -> P3 subfamília/família (ancestor_ids sobe a árvore).
    strict=True (beat destaca A espécie) trava em P1. Nunca sobe além de 3 degraus
    nem toca os ancestrais de topo (reino/filo/classe) — 'Animalia' não ilustra nada."""
    ids = taxon.get("ancestor_ids") or []
    if not ids:
        return [taxon["id"]]
    if strict:
        return [ids[-1]]
    return [ids[i] for i in range(len(ids) - 1, max(len(ids) - 4, 5), -1)]


def inaturalist_img(query, n=6, strict=False, termo=None, garimpar=False):
    """Fotos de ser vivo identificadas por especialistas.

    `termo`    = nome explícito do bicho/planta (vem de entidades.especie do diretor).
    `garimpar` = sem termo, vasculha as palavras da própria busca. **Default OFF**:
      mesmo com o filtro de matched_term, um vídeo de moto com "eagle" no nome de um
      modelo casaria a ave — e uma águia entraria na montagem. Só ligue quando o
      style_card marcar nicho taxonômico (fauna/flora), onde palavra de bicho na
      busca É o assunto. Com `termo` explícito funciona sempre, inclusive pra menção
      pontual dentro de um roteiro que não é de natureza."""
    tx = _inat_taxon(termo) if termo else None
    if not tx and garimpar:
        for w in [w for w in re.findall(r"[A-Za-zÀ-ÿ]{4,}", query or "")
                  if w.lower() not in _INAT_STOP][:4]:
            tx = _inat_taxon(w)
            if tx:
                break
    if not tx:
        return []
    out, vistos = [], set()
    for degrau, tid in enumerate(_inat_escada(tx, strict), start=1):
        if len(out) >= n:
            break
        try:
            r = httpx.get(f"{_INAT}/observations", params={
                "taxon_id": tid, "photos": "true", "photo_license": _INAT_LIC,
                "quality_grade": "research", "order_by": "votes",
                "per_page": min(30, n * 4)}, headers=_UA, timeout=25)
            if r.status_code != 200:
                continue
            for o in r.json().get("results") or []:
                for p in (o.get("photos") or [])[:1]:
                    lic = (p.get("license_code") or "").lower()
                    dim = p.get("original_dimensions") or {}
                    url = (p.get("url") or "").replace("square", "original")
                    # foto de naturalista costuma ser vertical/quadrada: em 16:9 vira
                    # crop agressivo ou barra lateral — exige paisagem com folga
                    if lic not in _INAT_TIER or not url or url in vistos:
                        continue
                    if dim.get("width", 0) < 1200 or dim.get("width", 0) <= dim.get("height", 1):
                        continue
                    vistos.add(url)
                    out.append({"url": url, "source": "inaturalist",
                                "id": f"inat_{p.get('id')}", "thumb": p.get("url"),
                                "meta": (o.get("place_guess") or "")[:60],
                                "tier": _INAT_TIER[lic], "licenca": lic,
                                "atribuicao": (p.get("attribution") or "")[:120],
                                "taxon": tx.get("name"), "taxon_rank": tx.get("rank"),
                                "degrau": f"P{degrau}",
                                # P1 = a espécie exata, verificada por humano: relevância
                                # já provada. P2/P3 sobem na árvore -> Vision decide.
                                "gate_relevancia": degrau > 1})
                if len(out) >= n:
                    break          # corta o loop de OBSERVAÇÕES, não só o de fotos
        except Exception:
            continue
    return out


# ------------------------------------------------- INTERRUPTOR POR FONTE (02/08)
# "vamos separando o antes e o depois, caso algo dê ruim voltamos ao que era" (Piter).
# Rollback de código = tag git `v5-fontes-base`. Isto aqui é o bisturi: desliga UMA
# fonte que esteja poluindo sem perder as outras e sem reverter commit.
#   FONTES_OFF=archive,gbif  python curador5.py ...
FONTES_OFF = {s.strip().lower() for s in os.environ.get("FONTES_OFF", "").split(",") if s.strip()}


def _off(nome):
    return nome in FONTES_OFF


# ---------------------------------------------------------- Wikimedia Commons
def wikimedia_img(query, n=4):
    """Commons via API de busca. O executor v4 já consulta Commons na cascata dele;
    aqui ele entra no MESMO batch-score, disputando com as outras fontes.
    Tier pela licença, igual executor_beats:111 (PD/CC0 -> T1, resto CC -> T2)."""
    if _off("wikimedia"):
        return []
    # ⚠️ 403 "Please respect our robot policy" ao chamar com httpx — inclusive com
    # User-Agent descritivo e com UA de curl. O MESMO endpoint responde 200 via
    # urllib (é fingerprint do cliente, não bloqueio de IP). Como o executor v4 já
    # tem `commons_list` em urllib, funcionando e com a regra de tier consagrada
    # (PD/CC0 -> T1, resto CC -> T2), delegamos em vez de manter dois acessos.
    try:
        import executor_beats as _ex  # tardio: evita ciclo de import
        out = []
        for u, lic, tier in _ex.commons_list(query[:80], n=n * 2):
            low = (lic or "").lower()
            # bordas de palavra: "nc"/"nd" como substring casariam dentro de "and",
            # "unported" etc. e reprovariam licença boa
            if re.search(r"\bnc\b|\bnd\b|non[- ]?commercial|no[- ]?deriv|"
                         r"fair use|non-free", low):
                continue
            out.append({"url": u, "source": "wikimedia",
                        "id": f"wm_{abs(hash(u)) % 10**10}",
                        "meta": u.rsplit("/", 1)[-1][:70], "tier": tier,
                        "licenca": (lic or "")[:24],
                        "atribuicao": f"Wikimedia Commons ({lic})"})
            if len(out) >= n:
                break
        return out
    except Exception:
        return []


# --------------------------------------------------------------- GBIF (fauna)
def gbif_img(query, n=4):
    """Ocorrências com foto de museus/herbários/coleções — complementa o iNaturalist
    (mesma lógica taxonômica, acervo diferente). Só entra com termo de ser vivo, pela
    mesma razão do iNat: busca frouxa casa nome científico de qualquer coisa."""
    if _off("gbif") or not query:
        return []
    try:
        r = httpx.get("https://api.gbif.org/v1/occurrence/search", params={
            "q": query[:60], "mediaType": "StillImage", "limit": n * 3},
            headers=_UA, timeout=25)
        out = []
        for o in r.json().get("results") or []:
            lic = (o.get("license") or "").lower()
            # GBIF devolve a URL da licença: só cc0/by (mesma trava do iNat)
            if not ("zero" in lic or "publicdomain" in lic
                    or ("/by/" in lic and "nc" not in lic and "nd" not in lic)):
                continue
            for m in (o.get("media") or [])[:1]:
                u = m.get("identifier")
                if not u:
                    continue
                out.append({"url": u, "source": "gbif",
                            "id": f"gb_{abs(hash(u)) % 10**10}",
                            "meta": (o.get("scientificName") or "")[:60],
                            "tier": 1 if ("zero" in lic or "publicdomain" in lic) else 2,
                            "licenca": "cc0" if "zero" in lic else "cc-by",
                            "atribuicao": (m.get("rightsHolder") or o.get("recordedBy") or "")[:120],
                            "taxon": (o.get("scientificName") or "")[:60], "degrau": "P1",
                            "gate_relevancia": True})  # GBIF não tem o consenso do iNat
            if len(out) >= n:
                break
        return out
    except Exception:
        return []


# ------------------------------------------------------- Flickr via gallery-dl
# gallery-dl é o par do yt-dlp para IMAGEM (centenas de sites). Aqui ele entra pelo
# Flickr, que tem acervo enorme de natureza/lugares E filtro de licença na própria
# busca: license=4(CC-BY),9(CC0),10(PD) — SA(5) fora, mesma trava do iNaturalist.
# ⚠️ CUSTA CARO (~10-20s: ele negocia uma API key a cada chamada). Por isso só entra
# na 1ª rodada de queries, igual ao social_video.
_GDL_LIC = "4,9,10"


def flickr_img(query, n=4, timeout=45):
    if _off("flickr") or not query:
        return []
    import subprocess
    url = ("https://www.flickr.com/search/?text="
           + re.sub(r"\s+", "+", query.strip()[:70]) + f"&license={_GDL_LIC}")
    try:
        # pede 3x: ~metade do Flickr é vertical/pequena (scan de livro antigo,
        # figura de paper) e cai no filtro de paisagem logo abaixo
        r = subprocess.run([sys.executable, "-m", "gallery_dl", "-j",
                            "--range", f"1-{max(6, n * 3)}", url],
                           capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=timeout)
        txt = r.stdout or ""
        i = txt.find("[")           # a linha "[flickr][info] ..." vem antes do JSON
        if i < 0:
            return []
        out = []
        for it in json.loads(txt[i:]):
            # mensagens do gallery-dl: [3, url, meta] é a de arquivo
            if not (isinstance(it, list) and len(it) >= 3 and isinstance(it[1], str)):
                continue
            m = it[2] if isinstance(it[2], dict) else {}
            larg, alt = m.get("width") or 0, m.get("height") or 0
            if larg < 1200 or larg <= alt:      # 16:9 exige paisagem com folga
                continue
            dono = (m.get("owner") or {}).get("username") or "Flickr"
            out.append({"url": it[1], "source": "flickr",
                        "id": f"fl_{m.get('id') or abs(hash(it[1])) % 10**10}",
                        "meta": (m.get("title") or "")[:60],
                        # a busca filtra 4/9/10 mas o metadata não diz QUAL: assume a
                        # mais exigente das três (CC-BY = crédito obrigatório)
                        "tier": 2, "licenca": "cc-by/cc0/pd",
                        "atribuicao": f"(c) {dono} via Flickr (CC)"})
            if len(out) >= n:
                break
        return out
    except Exception:
        return []


# ------------------------------------------------------------ Internet Archive
def archive_img(query, n=4):
    """Acervo histórico (domínio público) — o que resolve beat de ÉPOCA, que stock
    não tem. ⚠️ VÍDEO do archive segue DESLIGADO (decisão anterior: instável); aqui
    é só imagem."""
    if _off("archive"):
        return []
    try:
        r = httpx.get("https://archive.org/advancedsearch.php", params={
            "q": f'{query[:70]} AND mediatype:image', "fl[]": "identifier",
            "rows": n * 2, "output": "json"}, headers=_UA, timeout=25)
        out = []
        for d in ((r.json().get("response") or {}).get("docs") or []):
            ident = d.get("identifier")
            if not ident:
                continue
            out.append({"url": f"https://archive.org/services/img/{ident}",
                        "source": "archive", "id": f"ia_{ident[:16]}",
                        "meta": ident[:60], "tier": 1, "licenca": "public domain",
                        "atribuicao": f"Internet Archive / {ident[:40]}"})
            if len(out) >= n:
                break
        return out
    except Exception:
        return []


def coletar_imagens(query, n_por_fonte=3, usados=None, especie=None, taxonomico=False,
                    strict=False, rodada=0):
    """Todas as fontes de imagem em paralelo -> candidatos dedupados.
    `especie`/`taxonomico` ligam o iNaturalist (ver inaturalist_img).
    `rodada` > 0 pula as fontes CARAS (Flickr/gallery-dl negocia API key)."""
    from concurrent.futures import ThreadPoolExecutor
    usados = usados or set()
    with ThreadPoolExecutor(max_workers=8) as ex5:
        futs = [ex5.submit(f, query, n_por_fonte) for f in
                (pixabay_img, unsplash_img, openverse_img, searxng_img, web_img,
                 wikimedia_img, archive_img)]
        futs.append(ex5.submit(inaturalist_img, query, n_por_fonte, strict, especie,
                               taxonomico))
        # GBIF só entende nome CIENTÍFICO ('jararaca'=0, 'Bothrops jararaca'=1) —
        # o autocomplete do iNat é justamente o tradutor comum->científico
        if especie or taxonomico:
            _tx = _inat_taxon(especie) if especie else None
            futs.append(ex5.submit(gbif_img, (_tx or {}).get("name") or especie or query,
                                   n_por_fonte))
        if rodada == 0:   # Flickr custa subprocess: só na 1ª rodada de queries
            # busca do Flickr é AND: 'venomous snake fangs close up' = 0 resultados,
            # 'jararaca' = 2. Manda o alvo, não a frase inteira.
            _q_fl = especie or " ".join(
                [w for w in re.findall(r"[A-Za-zÀ-ÿ]{3,}", query or "")
                 if w.lower() not in _INAT_STOP][:3])
            futs.append(ex5.submit(flickr_img, _q_fl or query, n_por_fonte))
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
