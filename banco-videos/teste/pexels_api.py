"""Pexels com rotação de N chaves + retry no 429 (mesmo padrão do gemini_api.py).

Chaves lidas (dedup, nesta ordem):
  1. credentials.json -> entradas com provedor == "pexels"  (igual às 8 do Gemini)
  2. config.json      -> "pexels_api_keys" (lista)
  3. config.json      -> "pexels_api_key"  (única, legado)

Com várias chaves, o limite de ~200 req/h vira 200*N/h -> some o gargalo dos vídeos longos.
"""
import itertools
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

_CFG = Path(r"F:/Canal Dark/Aplicativo de Edição/video-automator/config.json")
_CRE = Path(r"F:/Canal Dark/Aplicativo de Edição/video-automator/credentials.json")
_UA = {"User-Agent": "Mozilla/5.0"}


def _load_keys():
    ks = []
    try:
        cr = json.load(open(_CRE, encoding="utf-8"))
        ks += [e["api_key"] for e in cr if e.get("provedor") == "pexels" and e.get("api_key")]
    except Exception:
        pass
    try:
        c = json.load(open(_CFG, encoding="utf-8"))
        v = c.get("pexels_api_keys")
        if isinstance(v, list):
            ks += [k for k in v if k]
        if c.get("pexels_api_key"):
            ks.append(c["pexels_api_key"])
    except Exception:
        pass
    seen, out = set(), []
    for k in ks:
        k = (k or "").strip()
        if k and k not in seen:
            seen.add(k); out.append(k)
    return out


KEYS = _load_keys()
_ROT = itertools.count()


def search(q, kind="videos", n=6, timeout=30):
    """Busca no Pexels rotacionando chaves; em 429/503 tenta a próxima. Lista (videos/photos) ou []."""
    if not KEYS:
        return []
    path = "videos/search" if kind == "videos" else "v1/search"
    url = (f"https://api.pexels.com/{path}?query={urllib.parse.quote(q)}"
           f"&per_page={n}&orientation=landscape&size=medium")
    tries = max(len(KEYS), 2)
    for _ in range(tries):
        key = KEYS[next(_ROT) % len(KEYS)]
        try:
            req = urllib.request.Request(url, headers={"Authorization": key, **_UA})
            d = json.loads(urllib.request.urlopen(req, timeout=timeout).read())
            return (d.get("videos") if kind == "videos" else d.get("photos")) or []
        except urllib.error.HTTPError as e:
            if e.code in (429, 503):      # rate-limit/sobrecarga -> próxima chave
                time.sleep(0.4); continue
            return []                     # 400/404 etc = query ruim, trocar chave não ajuda
        except Exception:
            time.sleep(0.3); continue
    return []
