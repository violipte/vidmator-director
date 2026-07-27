"""Banco v2: baixa do Pexels -> Drive (D:) + enriquece com Gemini Vision.

Por clip: download -> keyframe (FFmpeg) -> Gemini descreve (descricao/mood/movimento/tags)
-> grava .mp4 em D:/Meu Drive/canal_dark_footage_stock/<categoria>/ + entrada no catálogo.

Categoria = grupo da query (determinística). Idempotente.
Rotaciona as 8 chaves Gemini pra evitar rate limit.
"""
import base64
import json
import subprocess
import sys
import time
import urllib.request
import urllib.parse
import urllib.error
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

BANCO = Path(r"D:/Meu Drive/canal_dark_footage_stock")
CATALOGO = BANCO / "catalogo.json"
TMP = Path(r"F:/Canal Dark/Aplicativo de Edição/banco-videos/_tmp_keyframes")
CONFIG = Path(r"F:/Canal Dark/Aplicativo de Edição/video-automator/config.json")
CREDS = Path(r"F:/Canal Dark/Aplicativo de Edição/video-automator/credentials.json")

POR_CATEGORIA = 50
TARGET_W = 1920

CATEGORIAS = {
    "cosmic": ["nebula", "galaxy", "starry night sky", "aurora borealis", "milky way", "deep space", "cosmos"],
    "nature": ["calm ocean sunset", "mountain sunrise", "clouds timelapse", "forest sunlight", "ocean waves", "rain on window", "fog forest"],
    "human": ["person silhouette sunset", "hands praying", "woman meditating", "person walking alone", "candle flame", "eye closeup"],
    "abstract": ["light rays", "particles floating", "water ripple", "ink in water", "smoke dark", "bokeh lights", "gold light"],
}

PEXELS_KEY = json.load(open(CONFIG, encoding="utf-8"))["pexels_api_key"]
GEMINI_KEYS = [c["api_key"] for c in json.load(open(CREDS, encoding="utf-8"))
               if c.get("provedor") == "gemini" and c.get("api_key")]
_gk = {"i": 0}


def pexels_search(q, per_page):
    url = f"https://api.pexels.com/videos/search?query={urllib.parse.quote(q)}&per_page={per_page}&orientation=landscape&size=medium"
    req = urllib.request.Request(url, headers={"Authorization": PEXELS_KEY, "User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read()).get("videos", [])


def pick_file(v):
    files = [f for f in v.get("video_files", []) if f.get("file_type") == "video/mp4"]
    if not files:
        return None
    files.sort(key=lambda f: abs((f.get("width") or 0) - TARGET_W) + (0 if (f.get("width") or 0) <= TARGET_W else 5000))
    return files[0]


def download(url, dest):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=300) as r:
        dest.write_bytes(r.read())


def keyframe(mp4, dur, out_jpg):
    ss = max(0.5, dur * 0.35)
    subprocess.run(["ffmpeg", "-y", "-ss", str(ss), "-i", str(mp4), "-frames:v", "1",
                    "-vf", "scale=640:-1", str(out_jpg)],
                   capture_output=True)
    return out_jpg.exists()


def gemini_vision(jpg_path):
    """Descreve o frame. Rotaciona chaves; retry em 429. Retorna dict ou None."""
    b64 = base64.b64encode(jpg_path.read_bytes()).decode()
    prompt = (
        "Describe this video frame for a B-roll stock catalog. Return ONLY JSON, no markdown:\n"
        '{"descricao_visual":"short English phrase of what is literally shown",'
        '"mood":"1-2 words (e.g. calm, tense, hopeful, melancholic)",'
        '"movimento":"best guess: estatico | lento | medio | rapido",'
        '"tags":["3-6","keywords"]}'
    )
    body = json.dumps({"contents": [{"parts": [
        {"text": prompt},
        {"inline_data": {"mime_type": "image/jpeg", "data": b64}},
    ]}]}).encode("utf-8")
    for attempt in range(len(GEMINI_KEYS) * 2):
        key = GEMINI_KEYS[_gk["i"] % len(GEMINI_KEYS)]
        _gk["i"] += 1
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={key}"
        try:
            req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
            with urllib.request.urlopen(req, timeout=60) as r:
                resp = json.loads(r.read())
            txt = resp["candidates"][0]["content"]["parts"][0]["text"]
            import re
            txt = re.sub(r"^```(?:json)?|```$", "", txt.strip(), flags=re.MULTILINE).strip()
            return json.loads(txt)
        except urllib.error.HTTPError as e:
            if e.code in (429, 503):
                time.sleep(1.5)
                continue
            return None
        except Exception:
            return None
    return None


def main():
    TMP.mkdir(parents=True, exist_ok=True)
    catalogo = {}
    if CATALOGO.exists():
        for it in json.load(open(CATALOGO, encoding="utf-8")):
            catalogo[it["id"]] = it

    print(f"=== Banco v2 | {POR_CATEGORIA}/categoria | catálogo atual: {len(catalogo)} ===\n")
    for cat, queries in CATEGORIAS.items():
        (BANCO / cat).mkdir(parents=True, exist_ok=True)
        print(f"### {cat} ###")
        vistos, novos = set(), 0
        per_q = max(8, (POR_CATEGORIA // len(queries)) + 4)
        for q in queries:
            if novos >= POR_CATEGORIA:
                break
            try:
                vids = pexels_search(q, per_q)
            except Exception as e:
                print(f"  [{q}] erro busca: {e}")
                continue
            for v in vids:
                if novos >= POR_CATEGORIA:
                    break
                vid = f"pexels_{v['id']}"
                if vid in vistos or vid in catalogo:
                    continue
                vistos.add(vid)
                vf = pick_file(v)
                if not vf:
                    continue
                dest = BANCO / cat / f"{vid}.mp4"
                try:
                    if not dest.exists():
                        download(vf["link"], dest)
                except Exception as e:
                    print(f"  {vid} download falhou: {e}")
                    continue
                # keyframe + enriquecimento (CLI primário, API fallback)
                kf = TMP / f"{vid}.jpg"
                enr = None
                if keyframe(dest, v.get("duration", 5), kf):
                    from enriquecer import descrever
                    enr, _via = descrever(kf)
                    kf.unlink(missing_ok=True)
                catalogo[vid] = {
                    "id": vid, "source": "pexels", "source_url": v.get("url", ""),
                    "author": (v.get("user") or {}).get("name", ""),
                    "arquivo": str(dest).replace("\\", "/"),
                    "categoria": cat, "query": q,
                    "descricao_visual": (enr or {}).get("descricao_visual", q),
                    "mood": (enr or {}).get("mood", ""),
                    "movimento": (enr or {}).get("movimento", ""),
                    "tags": (enr or {}).get("tags", []),
                    "duracao": v.get("duration", 0),
                    "width": vf.get("width", 0), "height": vf.get("height", 0),
                    "enriquecido": bool(enr),
                }
                novos += 1
                flag = "OK" if enr else "sem-vision"
                print(f"  [{novos:>2}/{POR_CATEGORIA}] {vid} ({flag}) {catalogo[vid]['descricao_visual'][:50]}")
                # salva incremental (resiliente a interrupção)
                if novos % 10 == 0:
                    json.dump(list(catalogo.values()), open(CATALOGO, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        print(f"  -> {cat}: {novos} novos\n")

    json.dump(list(catalogo.values()), open(CATALOGO, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    enr_ok = sum(1 for c in catalogo.values() if c.get("enriquecido"))
    print(f"=== DONE === catálogo: {len(catalogo)} clips ({enr_ok} enriquecidos) -> {CATALOGO}")


if __name__ == "__main__":
    main()
