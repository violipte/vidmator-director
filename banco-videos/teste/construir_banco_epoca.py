"""Constrói o BANCO DE ÉPOCA (footage archive real, domínio público) p/ o nicho documentário.
Pipeline: busca Commons (vídeo PD) -> baixa o filme -> SEGMENTA em clipes ~5s -> Gemini Vision VETA
(rejeita marca d'água/timecode/talking-head/título/moderno) -> tagueia -> salva no Drive + catálogo.

Uso: python construir_banco_epoca.py [n_filmes]   (default 4 p/ seed)
"""
import base64
import json
import shutil
import subprocess
import sys
import urllib.parse
import urllib.request
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
TESTE = Path(r"F:/Canal Dark/Aplicativo de Edição/banco-videos/teste")
TMP = Path(r"F:/Canal Dark/Aplicativo de Edição/banco-videos/_epoca_tmp")
BANCO = Path(r"D:/Meu Drive/canal_dark_footage_epoca")
CATALOGO = BANCO / "catalogo.json"
CREDS = Path(r"F:/Canal Dark/Aplicativo de Edição/video-automator/credentials.json")
UA = {"User-Agent": "CanalDark/1.0 (research; pitermoreiraviolim@gmail.com)"}
GKEYS = [c["api_key"] for c in json.load(open(CREDS, encoding="utf-8")) if c.get("provedor") == "gemini" and c.get("api_key")]
import itertools
_ROT = itertools.count()
SAFETY = [{"category": c, "threshold": "BLOCK_NONE"} for c in
          ("HARM_CATEGORY_HARASSMENT", "HARM_CATEGORY_HATE_SPEECH", "HARM_CATEGORY_SEXUALLY_EXPLICIT", "HARM_CATEGORY_DANGEROUS_CONTENT")]

# queries CURADAS p/ fontes limpas PD (gov US = sem marca d'água); evita re-uploads marcados
# ESCOPO MISTO (2026-07-02, nicho DOC = histórias reais dramáticas): guerra + desastres + crime + época geral
QUERIES = [
    # guerra (base original)
    "World War II Office of War Information", "Normandy invasion 1944 US Army",
    "World War II US Signal Corps", "D-Day 1944 archival", "World War II Pacific Navy footage",
    "World War II tanks armor combat", "World War II infantry troops marching",
    "World War II aircraft bombers", "World War II warships fleet", "World War II London Blitz",
    "World War II North Africa campaign", "World War II liberation Paris 1944",
    "United States Army Air Forces footage", "World War II artillery battle",
    "World War I trench warfare footage", "Korean War combat footage archival",
    # desastres / eventos dramáticos
    "Hindenburg disaster 1937 newsreel", "San Francisco earthquake 1906 footage",
    "Titanic 1912 newsreel footage", "flood disaster newsreel 1930s",
    "hurricane damage newsreel archival", "fire disaster newsreel 1940s",
    "shipwreck rescue newsreel archival", "train wreck newsreel footage",
    # crime / lei / era da depressão
    "prohibition era newsreel footage", "police raid newsreel 1930s",
    "Great Depression newsreel footage", "gangster era newsreel archival",
    "courtroom trial newsreel footage", "prison newsreel footage archival",
    # vida de época / biografia (contexto)
    "1920s city street footage", "1930s daily life newsreel", "1940s home front footage",
    "1950s americana newsreel", "immigration Ellis Island footage", "factory workers newsreel archival",
    "universal newsreel 1940s", "universal newsreel 1950s",
]
# títulos a PULAR (talking-head / marcas conhecidas / não-B-roll)
SKIP_TITULO = ["oral history", "interview", "trailer", "lecture", "periscopefilm", "ina.fr",
               "remarks", "ceremony", "commemorat", "speech", "press conference"]


def _api_vision(prompt, jpg):
    b64 = base64.b64encode(jpg.read_bytes()).decode()
    body = json.dumps({"contents": [{"parts": [{"text": prompt}, {"inline_data": {"mime_type": "image/jpeg", "data": b64}}]}],
                       "safetySettings": SAFETY}).encode()
    for _ in range(len(GKEYS)):
        k = GKEYS[next(_ROT) % len(GKEYS)]
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={k}"
            r = urllib.request.urlopen(urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST"), timeout=60)
            return json.loads(r.read())["candidates"][0]["content"]["parts"][0]["text"]
        except urllib.error.HTTPError as e:
            if e.code in (429, 503):
                continue
            return None
        except Exception:
            continue
    return None


GPT_KEY = next((c["api_key"] for c in json.load(open(CREDS, encoding="utf-8"))
                if c.get("provedor") == "gpt" and c.get("api_key")), "")


def _api_vision_gpt(prompt, jpg):
    """GPT vision (gpt-4o-mini, detail:low ~$0.0005/img) — sem o gargalo de 20rpm do Gemini free.
    Retorna texto ou None (chamador RE-TENTA; nunca tratar falha de API como rejeição)."""
    import time as _t
    b64 = base64.b64encode(jpg.read_bytes()).decode()
    body = json.dumps({"model": "gpt-4o-mini", "max_completion_tokens": 300,
                       "messages": [{"role": "user", "content": [
                           {"type": "text", "text": prompt},
                           {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}", "detail": "low"}}]}]}).encode()
    for _ in range(3):
        try:
            r = urllib.request.urlopen(urllib.request.Request(
                "https://api.openai.com/v1/chat/completions", data=body,
                headers={"Content-Type": "application/json", "Authorization": f"Bearer {GPT_KEY}"}, method="POST"), timeout=60)
            return json.loads(r.read())["choices"][0]["message"]["content"]
        except urllib.error.HTTPError as e:
            if e.code == 429:
                _t.sleep(3); continue
            return None
        except Exception:
            _t.sleep(1); continue
    return None


def vet(jpg):
    """Vision: clipe é B-roll archival LIMPO? Retorna (keep, desc, era) ou (False,'','').
    GPT por default (Gemini free = 20rpm -> 429 em massa virava rejeição silenciosa e perdia clipe bom)."""
    p = ("This is ONE frame from a video clip meant as B-roll for a HISTORICAL documentary (wars, disasters, crimes, "
         "biographies, daily life 1900s-1970s). Return ONLY a JSON object {keep, desc, era}. keep=true ONLY if it is "
         "GENUINE archival/period footage of real historical scenes (soldiers, ships, planes, cities, crowds, fires, "
         "wreckage, police, courtrooms, factories, streets, events) with: NO watermark, NO burned-in timecode or text "
         "overlay, NO on-screen lecturer/host/talking-head, NO title/intro card, NO modern content, AND the scene "
         "must be CLEAR and recognizable (reject blurry motion-transitions, abstract blobs, near-black or washed-out frames). "
         "desc=3-6 word scene description. era=visible year/decade or ''.")
    out = _api_vision_gpt(p, jpg) if GPT_KEY else _api_vision(p, jpg)
    if not out:
        print("      (vet: API falhou 3x — pulando sem rejeitar)")
        return False, "", ""
    a, b = out.find("{"), out.rfind("}")
    if a < 0 or b <= a:
        return False, "", ""
    try:
        o = json.loads(out[a:b + 1])
        return bool(o.get("keep")), str(o.get("desc", ""))[:50], str(o.get("era", ""))[:12]
    except Exception:
        return False, "", ""


def commons_busca(q, n=6):
    url = ("https://commons.wikimedia.org/w/api.php?action=query&format=json&generator=search"
           "&gsrsearch=" + urllib.parse.quote("filetype:video " + q) + f"&gsrnamespace=6&gsrlimit={n}"
           "&prop=imageinfo&iiprop=url|mime|size")
    d = json.loads(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40).read())
    out = []
    for p in ((d.get("query") or {}).get("pages", {}) or {}).values():
        ii = (p.get("imageinfo") or [{}])[0]
        t = p.get("title", "")
        mb = int(ii.get("size", 0)) / 1024 / 1024
        if (ii.get("mime", "").startswith("video") and 3 < mb < 130
                and not any(s in t.lower() for s in SKIP_TITULO)):
            out.append({"titulo": t, "url": ii.get("url"), "mb": round(mb, 1)})
    return out


def baixar(url, dest):
    dest.write_bytes(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=240).read())


def segmentos(film, base, n=6, dur=5):
    """Extrai n clipes de `dur`s espaçados (pula 10% das bordas) -> mp4 1080h. Retorna paths."""
    d = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(film)],
                       capture_output=True, text=True).stdout.strip()
    try:
        total = float(d)
    except Exception:
        return []
    if total < 20:
        return []
    ini, fim = total * 0.1, total * 0.9
    clips = []
    for i in range(n):
        t = ini + (fim - ini) * i / max(n - 1, 1)
        out = TMP / f"{base}_seg{i}.mp4"
        r = subprocess.run(["ffmpeg", "-y", "-ss", str(round(t, 1)), "-t", str(dur), "-i", str(film),
                            "-vf", "scale=-2:1080", "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "23", str(out)],
                           capture_output=True)
        if out.exists() and out.stat().st_size > 20000:
            clips.append(out)
    return clips


def main():
    n_filmes = int(sys.argv[1]) if len(sys.argv) > 1 else 4
    TMP.mkdir(parents=True, exist_ok=True)
    BANCO.mkdir(parents=True, exist_ok=True)
    catalogo = json.load(open(CATALOGO, encoding="utf-8")) if CATALOGO.exists() else []
    vistos = {c.get("fonte") for c in catalogo}
    filmes = []
    for q in QUERIES:
        for f in commons_busca(q):
            if f["url"] not in vistos and f["titulo"] not in [x["titulo"] for x in filmes]:
                filmes.append(f)
    filmes = filmes[:n_filmes]
    print(f"=== Banco de época: processando {len(filmes)} filmes ===")
    kept = 0
    for fi, f in enumerate(filmes):
        print(f"\n[{fi+1}/{len(filmes)}] {f['titulo']} ({f['mb']}MB)")
        film = TMP / f"film_{fi}.webm"
        try:
            baixar(f["url"], film)
        except Exception as e:
            print("  download falhou:", str(e)[:50]); continue
        clips = segmentos(film, f"f{fi}")
        print(f"  {len(clips)} segmentos -> vetando...")
        for ci, clip in enumerate(clips):
            jpg = TMP / f"f{fi}_{ci}.jpg"
            subprocess.run(["ffmpeg", "-y", "-ss", "2", "-i", str(clip), "-frames:v", "1", "-q:v", "3", str(jpg)], capture_output=True)
            if not jpg.exists():
                continue
            keep, desc, era = vet(jpg)
            if keep:
                era_dir = BANCO / (era.strip() or "wwii")
                era_dir.mkdir(parents=True, exist_ok=True)
                dest = era_dir / f"epoca_{fi}_{ci}.mp4"
                shutil.move(str(clip), str(dest))   # F:->D: (cross-drive, os.replace não serve)
                catalogo.append({"id": dest.stem, "file": str(dest).replace("\\", "/"), "desc": desc,
                                 "era": era or "wwii", "fonte": f["url"], "titulo": f["titulo"][:60]})
                kept += 1
                print(f"    ✓ seg{ci}: {desc} [{era}]")
            else:
                print(f"    ✗ seg{ci} rejeitado")
            jpg.unlink(missing_ok=True)
        film.unlink(missing_ok=True)
    json.dump(catalogo, open(CATALOGO, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    # limpa temp
    for x in TMP.glob("*"):
        x.unlink(missing_ok=True)
    print(f"\n=== {kept} clipes APROVADOS -> {BANCO} | catálogo: {len(catalogo)} total ===")


if __name__ == "__main__":
    main()
