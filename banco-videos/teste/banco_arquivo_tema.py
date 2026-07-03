"""Banco de ARQUIVO do TEMA: dado o roteiro, o Gemini deriva ~8 temas de footage de
época; busca no archive.org (domínio público), extrai segmentos, VERIFICA (Vision: é
footage de época relevante, não talking-head) e descreve. Vira um banco local que o
resolver usa pra casar beats atmosféricos com VÍDEO REAL da época. Reutilizável por tema.

Uso: python banco_arquivo_tema.py   (lê roteiro_en.txt; grava _arquivo_tema/catalogo.json)
"""
import base64
import io
import json
import re
import subprocess
import sys
import urllib.request
import urllib.parse
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
TESTE = Path(r"F:/Canal Dark/Aplicativo de Edição/banco-videos/teste")
ROTEIRO = TESTE / "roteiro_en.txt"
BANK = TESTE / "_arquivo_tema"
CATALOGO = BANK / "catalogo.json"
CREDS = Path(r"F:/Canal Dark/Aplicativo de Edição/video-automator/credentials.json")
UA = {"User-Agent": "Mozilla/5.0"}
GKEYS = [c["api_key"] for c in json.load(open(CREDS, encoding="utf-8"))
         if c.get("provedor") == "gemini" and c.get("api_key")]
SEG_POR_TEMA = 2
SEG_DUR = 5
LUMA_MIN = 10     # rejeita só clipe quase preto (B&W de guerra é escuro)
LUMA_MAX = 240    # rejeita só estourado/lavado (ex.: o "September 1939" branco)
MAX_DL_MB = 90    # não baixa derivados maiores que isso


def luma_media(kf):
    """Luminância média (0-255) do keyframe via downscale 1x1 — sem dependência de PIL."""
    try:
        r = subprocess.run(["ffmpeg", "-v", "error", "-i", str(kf), "-vf", "scale=1:1",
                            "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, timeout=20)
        px = r.stdout[:3]
        if len(px) >= 3:
            return 0.299 * px[0] + 0.587 * px[1] + 0.114 * px[2]
    except Exception:
        pass
    return 128.0


def gemini_cli(prompt, timeout=150):
    try:
        p = subprocess.Popen(f'gemini -p "{prompt}"', shell=True, cwd=str(TESTE),
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace")
        out, _ = p.communicate(timeout=timeout)
        return out or ""
    except subprocess.TimeoutExpired:
        subprocess.run(f"taskkill /F /T /PID {p.pid}", shell=True, capture_output=True)
    except Exception:
        pass
    return ""


def temas_do_roteiro(roteiro):
    prompt = ("Read this documentary narration. Output 8 search queries for PERIOD ARCHIVE FOOTAGE that illustrate "
              "its era and themes. Each query MUST be a SHORT generic filmable SCENE of 2-4 words (e.g. for WWII: "
              "soldiers marching, aerial bombing, tanks advancing, naval battle, bomb shelter, war factory, ruined "
              "city, refugees fleeing). RULES: NO years or dates; NO words like newsreel, archive, footage, film, "
              "or documentary; NO proper place/person names — just the visible action/scene, so generic archive "
              "search finds many matches. Return ONLY a JSON array of 8 query strings. Script: "
              + roteiro.replace(chr(34), "").replace("\n", " "))
    out = gemini_cli(prompt)
    a, b = out.find("["), out.rfind("]")
    if a >= 0 and b > a:
        try:
            return [str(x) for x in json.loads(out[a:b + 1])][:8]
        except Exception:
            pass
    return []


def vision_descreve_valida(jpg_bytes):
    """Vision: é footage de época relevante (não talking-head/slate)? + descrição curta."""
    b64 = base64.b64encode(jpg_bytes).decode()
    parts = [{"text": "This is a frame from archive footage. Return ONLY JSON {\"usavel\": true|false, \"desc\": "
              "\"short English description\"}. usavel=false if it is a talking head/interview, a title card/slate, "
              "text, a logo, or otherwise not usable B-roll. usavel=true if it shows a real scene/action/place."},
             {"inline_data": {"mime_type": "image/jpeg", "data": b64}}]
    body = json.dumps({"contents": [{"parts": parts}]}).encode()
    for attempt in range(len(GKEYS) * 2):
        k = GKEYS[attempt % len(GKEYS)]
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={k}"
            req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
            resp = json.loads(urllib.request.urlopen(req, timeout=90).read())
            txt = re.sub(r"^```(?:json)?|```$", "", resp["candidates"][0]["content"]["parts"][0]["text"].strip(), flags=re.M).strip()
            o = json.loads(txt)
            return bool(o.get("usavel")), (o.get("desc") or "")
        except Exception:
            import time; time.sleep(1.0)
    return False, ""


def _buscar(q):
    u = ("https://archive.org/advancedsearch.php?q=" + urllib.parse.quote(q) +
         "&fl[]=identifier&fl[]=year&sort[]=downloads+desc&rows=8&output=json")
    return json.loads(urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=30).read())["response"]["docs"]


def _parse_length(v):
    """Duração (s) a partir do campo 'length' do metadata (float seg ou H:MM:SS)."""
    if not v:
        return 0.0
    try:
        s = str(v)
        if ":" in s:
            acc = 0.0
            for p in s.split(":"):
                acc = acc * 60 + float(p)
            return acc
        return float(s)
    except Exception:
        return 0.0


def baixar(url, dest, timeout=60):
    """Baixa o arquivo inteiro pro disco (cortes locais são rápidos e confiáveis).
    timeout é por-leitura de socket; arquivo grande lento aborta cedo (archive.org é instável)."""
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r, open(dest, "wb") as f:
            while True:
                chunk = r.read(1 << 16)
                if not chunk:
                    break
                f.write(chunk)
        return dest.exists() and dest.stat().st_size > 20000
    except Exception:
        return False


def dur_local(p):
    try:
        return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)],
                                    capture_output=True, text=True, timeout=20).stdout.strip() or 0)
    except Exception:
        return 0.0


def archive_segmentos(query, idx):
    """Busca archive.org, extrai SEG_POR_TEMA segmentos válidos. Retorna lista de {file, desc}."""
    out = []
    # estrita (PD/coleções de arquivo) -> se vier pouco, afrouxa pra mediatype:movies
    estrita = f"({query}) AND mediatype:movies AND (licenseurl:*publicdomain* OR collection:(prelinger OR moviesandfilms OR newsandpublicaffairs OR flickerway))"
    larga = f"({query}) AND mediatype:movies"
    docs = []
    try:
        docs = _buscar(estrita)
        if len(docs) < 3:
            seen = {d["identifier"] for d in docs}
            docs += [d for d in _buscar(larga) if d["identifier"] not in seen]
    except Exception as e:
        print(f"    busca falhou: {str(e)[:50]}"); return out
    for doc in docs[:4]:   # cap de docs/tema -> builder rápido e bounded
        if len(out) >= SEG_POR_TEMA:
            break
        ident = doc["identifier"]
        tmp = BANK / f"_dl_{idx}.mp4"
        try:
            try:
                meta = json.loads(urllib.request.urlopen(urllib.request.Request(f"https://archive.org/metadata/{ident}", headers=UA), timeout=20).read())
            except Exception:
                print(f"    - metadata timeout ({ident[:24]})"); continue
            mp4s = sorted([f for f in meta.get("files", []) if f.get("name", "").lower().endswith(".mp4") and int(f.get("size", 0)) > 0], key=lambda f: int(f.get("size", 0)))
            if not mp4s:
                print(f"    - sem mp4 ({ident[:24]})"); continue
            mb = int(mp4s[0].get("size", 0)) / 1e6
            if mb > MAX_DL_MB:
                print(f"    - grande demais {mb:.0f}MB ({ident[:24]})"); continue
            url = f"https://archive.org/download/{ident}/" + urllib.parse.quote(mp4s[0]["name"])
            # baixa o derivado pequeno UMA vez -> cortes locais (rápido e confiável)
            if not baixar(url, tmp):
                print(f"    - download falhou {mb:.0f}MB ({ident[:24]})")
                continue
            dur = _parse_length(mp4s[0].get("length")) or dur_local(tmp)
            if dur < 15:
                continue
            for t in [round(dur * 0.3), round(dur * 0.5), round(dur * 0.7)]:
                if len(out) >= SEG_POR_TEMA:
                    break
                kf = BANK / f"_kf_{idx}.jpg"
                subprocess.run(["ffmpeg", "-y", "-ss", str(t), "-i", str(tmp), "-frames:v", "1", "-vf", "scale=512:-1", str(kf)], capture_output=True, timeout=20)
                if not kf.exists():
                    continue
                lm = luma_media(kf)
                if lm < LUMA_MIN or lm > LUMA_MAX:
                    kf.unlink(missing_ok=True)
                    print(f"    - descartado (exposição luma={lm:.0f})")
                    continue
                usavel, desc = vision_descreve_valida(kf.read_bytes())
                kf.unlink(missing_ok=True)
                if not usavel:
                    continue
                dest = BANK / f"tema_{idx}_{len(out)}.mp4"
                subprocess.run(["ffmpeg", "-y", "-ss", str(t), "-i", str(tmp), "-t", str(SEG_DUR), "-an", "-vf", "scale=-2:1080",
                                "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "21", "-movflags", "+faststart", str(dest)], capture_output=True, timeout=60)
                if dest.exists() and dest.stat().st_size > 20000:
                    out.append({"file": str(dest).replace("\\", "/"), "desc": desc, "query": query})
                    print(f"    + {dest.name}: {desc[:50]}")
        except Exception:
            continue
        finally:
            tmp.unlink(missing_ok=True)
    return out


def main():
    BANK.mkdir(parents=True, exist_ok=True)
    roteiro = ROTEIRO.read_text(encoding="utf-8")
    print("=== Banco de arquivo do tema ===")
    temas = temas_do_roteiro(roteiro)
    print(f"  temas: {temas}\n")
    banco = []
    for i, t in enumerate(temas):
        print(f"  [{i+1}/{len(temas)}] {t}")
        banco.extend(archive_segmentos(t, i))
    CATALOGO.write_text(json.dumps(banco, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nOK -> {len(banco)} clipes de arquivo no banco-tema ({CATALOGO})")


if __name__ == "__main__":
    main()
