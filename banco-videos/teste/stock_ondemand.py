"""Resolvedor de STOCK ON-DEMAND. Para cada cena com stock_query:
  cache local (hash da query)?  -> reusa
  senão: Pexels busca 6 -> Gemini Vision escolhe o melhor poster -> baixa vencedor -> cacheia

Preenche clip_path / clip_dur no timeline.json. NÃO monta banco no Drive: cache local em F:.
Roda com `python` (precisa Pillow). Idempotente; dedup por query.
"""
import base64
import hashlib
import io
import json
import re
import sys
import time
import urllib.request
import urllib.parse
import urllib.error
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

TESTE = Path(r"F:/Canal Dark/Aplicativo de Edição/banco-videos/teste")
TIMELINE = TESTE / "timeline.json"
CACHE = Path(r"F:/Canal Dark/Aplicativo de Edição/banco-videos/_cache_stock")
INDEX = CACHE / "index.json"
CONFIG = Path(r"F:/Canal Dark/Aplicativo de Edição/video-automator/config.json")
CREDS = Path(r"F:/Canal Dark/Aplicativo de Edição/video-automator/credentials.json")

PEX = json.load(open(CONFIG, encoding="utf-8"))["pexels_api_key"]
GKEYS = [c["api_key"] for c in json.load(open(CREDS, encoding="utf-8"))
         if c.get("provedor") == "gemini" and c.get("api_key")]
UA = {"User-Agent": "Mozilla/5.0"}
TARGET_W = 1920


def qhash(q):
    return hashlib.md5(q.strip().lower().encode()).hexdigest()[:12]


def pexels(q, n=6):
    url = f"https://api.pexels.com/videos/search?query={urllib.parse.quote(q)}&per_page={n}&orientation=landscape&size=medium"
    req = urllib.request.Request(url, headers={"Authorization": PEX, **UA})
    return json.loads(urllib.request.urlopen(req, timeout=30).read()).get("videos", [])


def pick_file(v):
    files = [f for f in v.get("video_files", []) if f.get("file_type") == "video/mp4"]
    if not files:
        return None
    files.sort(key=lambda f: abs((f.get("width") or 0) - TARGET_W) + (0 if (f.get("width") or 0) <= TARGET_W else 5000))
    return files[0]


def vision_pick(beat, vids):
    """Gemini Vision escolhe o índice do melhor poster. Retorna idx (0..n-1)."""
    posters = []
    for v in vids:
        try:
            raw = urllib.request.urlopen(urllib.request.Request(v["image"], headers=UA), timeout=25).read()
            from PIL import Image
            im = Image.open(io.BytesIO(raw)).convert("RGB").resize((512, 288))
            b = io.BytesIO(); im.save(b, "JPEG")
            posters.append(base64.b64encode(b.getvalue()).decode())
        except Exception:
            posters.append(None)
    valid = [i for i, p in enumerate(posters) if p]
    if not valid:
        return 0
    parts = [{"text": f"These are stock video thumbnails (index 0..{len(posters)-1}). For the documentary narration beat: "
              f"'{beat}', pick the index whose MOOD and CONTENT fit best (cinematic, on-topic; avoid bright/cheerful/"
              f"watermarked/text-heavy/off-topic). Return ONLY JSON: " + '{"best":<index>}'}]
    for p in posters:
        if p:
            parts.append({"inline_data": {"mime_type": "image/jpeg", "data": p}})
    body = json.dumps({"contents": [{"parts": parts}]}).encode()
    for attempt in range(len(GKEYS) * 2):
        k = GKEYS[attempt % len(GKEYS)]
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={k}"
            req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
            with urllib.request.urlopen(req, timeout=90) as r:
                resp = json.loads(r.read())
            txt = re.sub(r"^```(?:json)?|```$", "", resp["candidates"][0]["content"]["parts"][0]["text"].strip(), flags=re.M).strip()
            idx = int(json.loads(txt).get("best", valid[0]))
            return idx if idx in valid else valid[0]
        except urllib.error.HTTPError as e:
            if e.code in (429, 503):
                time.sleep(1.5); continue
            break
        except Exception:
            time.sleep(1.0); continue
    return valid[0]


def resolve(query, index):
    """Retorna (clip_path, dur). Usa cache; senão busca+vision+baixa."""
    h = qhash(query)
    if h in index:
        return index[h]["file"], index[h]["dur"]
    dest = CACHE / f"{h}.mp4"
    # busca (com 1 fallback amplo)
    vids = []
    for q in (query, " ".join(query.split()[-2:])):
        try:
            vids = pexels(q)
        except Exception as e:
            print(f"    pexels erro: {str(e)[:40]}")
        if vids:
            break
    if not vids:
        return None, 0
    best = vision_pick(query, vids)
    v = vids[best]
    vf = pick_file(v)
    if not vf:
        return None, 0
    try:
        data = urllib.request.urlopen(urllib.request.Request(vf["link"], headers=UA), timeout=180).read()
        dest.write_bytes(data)
    except Exception as e:
        print(f"    download falhou: {str(e)[:40]}")
        return None, 0
    dur = v.get("duration", 6) or 6
    index[h] = {"query": query, "file": str(dest).replace("\\", "/"), "dur": dur, "pexels_id": v.get("id")}
    INDEX.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")
    return index[h]["file"], dur


def main():
    CACHE.mkdir(parents=True, exist_ok=True)
    index = json.load(open(INDEX, encoding="utf-8")) if INDEX.exists() else {}
    tl = json.load(open(TIMELINE, encoding="utf-8"))
    cenas = tl["cenas"]
    pend = [c for c in cenas if not c.get("clip_path") and c.get("stock_query")]
    print(f"=== Stock on-demand: {len(pend)}/{len(cenas)} cenas a resolver (cache: {len(index)}) ===")

    hits = miss = 0
    for c in cenas:
        if c.get("clip_path") or not c.get("stock_query"):
            continue
        q = c["stock_query"]
        cached = qhash(q) in index
        path, dur = resolve(q, index)
        if not path:
            print(f"  [{c['idx']:>2}] SEM CLIP p/ '{q[:42]}'")
            continue
        c["clip_path"] = path
        c["clip_dur"] = dur
        hits += cached
        miss += (not cached)
        print(f"  [{c['idx']:>2}] {'cache' if cached else 'novo  '} {q[:46]}")

    json.dump(tl, open(TIMELINE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    semclip = sum(1 for c in cenas if not c.get("clip_path"))
    print(f"\nOK: {miss} baixados, {hits} do cache | {semclip} sem clip | cache total: {len(index)}")


if __name__ == "__main__":
    main()
