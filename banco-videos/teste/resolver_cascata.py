"""Resolver em CASCATA do B-roll por beat (substitui stock_ondemand).
Por cena, tenta em ordem e o Gemini Vision JULGA a confiança em cada nível:
  L2  imagem PD (Wikimedia Commons)  — só se o beat é sobre algo específico/real
  L3  stock VÍDEO (Pexels)           — Vision: bom? senão cai
  L4  stock IMAGEM (Pexels foto)     — Vision: bom? senão cai
  L5  genérico (query mais ampla)    — usa o melhor
  L6  IA (Together/Gemini)           — PLUGÁVEL, desligado por ora -> usa melhor stock
Preenche clip_path + media_tipo (video|imagem) + clip_dur. Cache local em F:. Idempotente.
"""
import base64
import hashlib
import io
import os
import itertools
import json
import re
import subprocess
import sys
import threading
import time
import urllib.request
import urllib.parse
import urllib.error
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

TESTE = Path(r"F:/Canal Dark/Aplicativo de Edição/banco-videos/teste")
TIMELINE = TESTE / "timeline.json"
BANK_TEMA = TESTE / "_arquivo_tema" / "catalogo.json"
CACHE = Path(r"F:/Canal Dark/Aplicativo de Edição/banco-videos/_cache_stock")
INDEX = CACHE / "index_cascata.json"
CONFIG = Path(r"F:/Canal Dark/Aplicativo de Edição/video-automator/config.json")
CREDS = Path(r"F:/Canal Dark/Aplicativo de Edição/video-automator/credentials.json")

from pexels_api import search as _pex_search, KEYS as PEX_KEYS  # rotação de N chaves + retry 429
GKEYS = [c["api_key"] for c in json.load(open(CREDS, encoding="utf-8"))
         if c.get("provedor") == "gemini" and c.get("api_key")]
UA = {"User-Agent": "Mozilla/5.0"}
COMMONS_UA = {"User-Agent": "CanalDark/1.0 (research; pitermoreiraviolim@gmail.com)"}
TARGET_W = 1920
USE_IA = False          # nível 6 plugável (Together/Gemini) — ligar quando houver provedor
USE_COMMONS_L2 = True   # L2 imagem PD do assunto (Commons) — com gate Vision de IDENTIDADE
USE_ARCHIVE_L1 = False  # L1 vídeo PD (archive.org remote-seek) — DESLIGADO (instável); entidade real -> L2 imagem
USE_TEMA_IMG = True     # L2t IMAGEM da ÉPOCA p/ beat atmosférico (Commons por tema) — antes do stock
USE_TEMA_BANK = False   # banco de VÍDEO de arquivo (archive.org ao vivo) — DESLIGADO (instável); religar c/ banco no Drive
MAX_REUSO = 2           # reuso baixo: máx N usos do mesmo arquivo por janela
JANELA_REUSO = 390.0    # ~6,5 min
ARCH_UA = {"User-Agent": "Mozilla/5.0"}


def qhash(s):
    return hashlib.md5(s.strip().lower().encode()).hexdigest()[:12]


# ---------- fontes ----------
def pexels(q, kind="videos", n=6):
    return _pex_search(q, kind, n)   # rotaciona PEX_KEYS, retry em 429/503


def pexels_poster(item, kind):
    return item["image"] if kind == "videos" else item["src"]["large"]


def _green_frac(img_url):
    """Fração de pixels verde-chroma dominante no poster (detecta green-screen 'subscribe/intro')."""
    try:
        from PIL import Image
        data = urllib.request.urlopen(urllib.request.Request(img_url, headers=UA), timeout=15).read()
        im = Image.open(io.BytesIO(data)).convert("RGB").resize((48, 27))
        px = list(im.getdata())
        green = sum(1 for r, g, b in px if g > 90 and g > r * 1.4 and g > b * 1.4)
        return green / max(len(px), 1)
    except Exception:
        return 0.0   # na dúvida, não rejeita


def _hex_green(c):
    """avg_color do Pexels (foto) é verde-chroma? (grátis, sem download)."""
    try:
        c = c.lstrip("#"); r, g, b = int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)
        return g > 90 and g > r * 1.4 and g > b * 1.4
    except Exception:
        return False


def pexels_clean(query, kind, n=6, max_green=0.5):
    """Candidatos do Pexels com green-screen FILTRADO. Vídeo: checa poster (até 4, para no 1º limpo).
    Foto: usa avg_color (grátis). Se TODOS verdes (raro), devolve original p/ não travar a cena."""
    items = pexels(query, kind, n) or []
    if not items:
        return items
    if kind == "videos":
        for i, it in enumerate(items[:4]):
            if _green_frac(pexels_poster(it, "videos")) < max_green:
                return [it] + items[:i] + items[i + 1:]   # limpo primeiro, resto como fallback
        return items
    clean = [it for it in items if not _hex_green(it.get("avg_color", ""))]
    return clean or items


def pexels_download(item, kind, dest):
    if kind == "videos":
        files = [f for f in item.get("video_files", []) if f.get("file_type") == "video/mp4"]
        if not files:
            return 0
        files.sort(key=lambda f: abs((f.get("width") or 0) - TARGET_W) + (0 if (f.get("width") or 0) <= TARGET_W else 5000))
        link = files[0]["link"]
        dur = item.get("duration", 6) or 6
    else:
        link = item["src"]["original"]
        dur = 5
    data = urllib.request.urlopen(urllib.request.Request(link, headers=UA), timeout=180).read()
    dest.write_bytes(data)
    return dur if dest.stat().st_size > 8000 else 0


def commons_image(query, dest):
    try:
        url = ("https://commons.wikimedia.org/w/api.php?action=query&format=json&generator=search"
               f"&gsrnamespace=6&gsrsearch={urllib.parse.quote(query)}&gsrlimit=8"
               "&prop=imageinfo&iiprop=url|extmetadata&iiurlwidth=1600")
        d = json.loads(urllib.request.urlopen(urllib.request.Request(url, headers=COMMONS_UA), timeout=30).read())
        cand = []
        for p in ((d.get("query") or {}).get("pages", {}) or {}).values():
            ii = (p.get("imageinfo") or [{}])[0]
            u = ii.get("thumburl") or ii.get("url")
            if not u or not re.search(r"\.(jpg|jpeg|png)$", u, re.I):
                continue
            lic = ((ii.get("extmetadata") or {}).get("LicenseShortName") or {}).get("value", "")
            cand.append((0 if ("public domain" in lic.lower() or "cc0" in lic.lower()) else 1, u))
        cand.sort(key=lambda x: x[0])
        if not cand:
            return False
        data = urllib.request.urlopen(urllib.request.Request(cand[0][1], headers=COMMONS_UA), timeout=60).read()
        dest.write_bytes(data)
        return dest.stat().st_size > 8000
    except Exception:
        return False


# ---------- Gemini Vision via CLI (OAuth, sem quota — API key está em 429) ----------
_VIS_CTR = itertools.count()          # nomes temp ÚNICOS (thread-safe via GIL) p/ resolver paralelo
_IDX_LOCK = threading.Lock()          # escrita do índice de cache sob lock (resolve paralelo)


def _save_index(index):
    with _IDX_LOCK:
        INDEX.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")


def _safe(s):
    return str(s or "").replace(chr(34), "").replace("`", "").replace("$", "").replace("\n", " ")


def _vis_cli(prompt, img_path, timeout=70):
    """Vision pelo Gemini CLI: copia a imagem pro workspace, referencia por nome ÚNICO, parseia JSON."""
    import shutil
    loc = TESTE / f"_vis_{next(_VIS_CTR)}.jpg"
    try:
        shutil.copy2(img_path, loc)
    except Exception:
        return {}
    full = _safe(prompt) + f" The image is in the file {loc.name} in the current folder."
    out = ""
    p = None
    try:
        p = subprocess.Popen(f'gemini -p "{full}"', shell=True, cwd=str(TESTE),
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace")
        out, _ = p.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        if p:
            subprocess.run(f"taskkill /F /T /PID {p.pid}", shell=True, capture_output=True)
    except Exception:
        pass
    finally:
        loc.unlink(missing_ok=True)
    a, b = out.find("{"), out.rfind("}")
    if a >= 0 and b > a:
        try:
            return json.loads(out[a:b + 1])
        except Exception:
            pass
    return {}


_KEY_ROT = itertools.count()   # rotação das chaves (thread-safe via GIL) p/ resolve paralelo


def _api_text(prompt, b64=None, timeout=90):
    """Gemini API (generateContent) com rotação de chaves + retry em 429/503. Texto da resposta ou None."""
    parts = [{"text": prompt}]
    if b64:
        parts.append({"inline_data": {"mime_type": "image/jpeg", "data": b64}})
    body = json.dumps({"contents": [{"parts": parts}]}).encode()
    n = len(GKEYS) or 1
    for _ in range(n):
        k = GKEYS[next(_KEY_ROT) % n]
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={k}"
            req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
            with urllib.request.urlopen(req, timeout=timeout) as r:
                resp = json.loads(r.read())
            return resp["candidates"][0]["content"]["parts"][0]["text"]
        except urllib.error.HTTPError as e:
            if e.code in (429, 503):
                continue
            return None
        except Exception:
            continue
    return None


def _cli_text(prompt, timeout=150):
    """Fallback: Gemini CLI (OAuth). Retorna stdout (ou '')."""
    p = None
    try:
        p = subprocess.Popen(f'gemini -p "{_safe(prompt)}"', shell=True, cwd=str(TESTE),
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace")
        out, _ = p.communicate(timeout=timeout)
        return out or ""
    except subprocess.TimeoutExpired:
        if p:
            subprocess.run(f"taskkill /F /T /PID {p.pid}", shell=True, capture_output=True)
    except Exception:
        pass
    return ""


def _parse_obj(txt):
    if not txt:
        return {}
    a, b = txt.find("{"), txt.rfind("}")
    if a >= 0 and b > a:
        try:
            return json.loads(txt[a:b + 1])
        except Exception:
            pass
    return {}


def _ask_obj(prompt, img_path=None):
    """Pergunta ao Gemini (API primária, CLI fallback). Retorna JSON-objeto parseado."""
    b64 = poster_b64_file(img_path) if img_path else None
    txt = _api_text(prompt, b64)
    if txt is not None:
        return _parse_obj(txt)
    # API indisponível -> CLI
    if img_path:
        return _vis_cli(prompt, img_path)
    return _parse_obj(_cli_text(prompt))


def baixar_poster(url, dest, headers):
    """Baixa um poster/thumbnail pra arquivo local (pro CLI ler)."""
    try:
        raw = urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=25).read()
        dest.write_bytes(raw)
        return dest.stat().st_size > 4000
    except Exception:
        return False


def vision_fit(beat, img_path):
    """Quão bem a imagem ilustra o beat? -> good|weak|none (single image, via CLI)."""
    o = _ask_obj("Rate how well this image illustrates this documentary line in mood and content. Beat: "
                 + _safe(beat)[:160] + ". Return ONLY a JSON object with one field conf whose value is exactly "
                 "good, weak, or none. Use good only if it clearly fits; weak if mediocre; none if irrelevant.",
                 img_path)
    c = str(o.get("conf", "none")).lower()
    return c if c in ("good", "weak", "none") else "none"


def poster_b64(url, headers):
    try:
        raw = urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=25).read()
        return _b64_img(raw)
    except Exception:
        return None


def _b64_img(raw):
    from PIL import Image
    im = Image.open(io.BytesIO(raw)).convert("RGB").resize((512, 288))
    b = io.BytesIO(); im.save(b, "JPEG")
    return base64.b64encode(b.getvalue()).decode()


def poster_b64_file(path):
    try:
        return _b64_img(Path(path).read_bytes())
    except Exception:
        return None


def vision_verifica_assunto(subject, img_path):
    """Gate de IDENTIDADE (via CLI): a imagem é CLARAMENTE do assunto específico?"""
    if not img_path:
        return False
    o = _ask_obj("This image should show specifically: " + _safe(subject) + ". Is it CLEARLY a real depiction of "
                 "THAT exact subject (the actual person/place/event/object), not a generic or unrelated image? "
                 "Also return false if it is a stereoview / side-by-side duplicated image or a photo of a card/print "
                 "with borders or captions. Return ONLY a JSON object with one boolean field is_subject.", img_path)
    return bool(o.get("is_subject"))


def vision_tema_ok(query, img_path):
    """Gate SOLTO (via CLI) p/ imagem de época atmosférica: é FOTO real de mundo-real relevante ao tema?
    (rejeita mapa, gráfico, brasão, texto, logo, página de livro, retrato-posado)."""
    if not img_path:
        return False
    o = _ask_obj("Theme: " + _safe(query) + ". Is this image a REAL photograph or film still of a real-world scene "
                 "relevant to that theme, usable FULL-FRAME as documentary B-roll? Return false if it is a map, chart, "
                 "diagram, coat of arms, flag, emblem, text, book page, logo, drawing, painting, posed studio "
                 "portrait, OR a stereoview / stereograph / side-by-side duplicated image / a photo of a card, print, "
                 "postcard or museum object with borders or captions. Return ONLY a JSON object with one boolean field ok.", img_path)
    return bool(o.get("ok"))


def archive_video(query, subject, dest):
    """L1: busca vídeo PD no archive.org, verifica identidade pelo keyframe, extrai 5s. Retorna dur ou 0."""
    try:
        q = f"({query}) AND mediatype:movies AND (licenseurl:*publicdomain* OR collection:(prelinger OR nasa OR newsandpublicaffairs OR moviesandfilms))"
        u = ("https://archive.org/advancedsearch.php?q=" + urllib.parse.quote(q) +
             "&fl[]=identifier&sort[]=downloads+desc&rows=2&output=json")
        docs = json.loads(urllib.request.urlopen(urllib.request.Request(u, headers=ARCH_UA), timeout=25).read())["response"]["docs"]
    except Exception:
        return 0
    for doc in docs[:2]:
        ident = doc["identifier"]
        try:
            meta = json.loads(urllib.request.urlopen(urllib.request.Request(f"https://archive.org/metadata/{ident}", headers=ARCH_UA), timeout=25).read())
            mp4s = sorted([f for f in meta.get("files", []) if f.get("name", "").lower().endswith(".mp4") and int(f.get("size", 0)) > 0], key=lambda f: int(f.get("size", 0)))
            if not mp4s:
                continue
            url = f"https://archive.org/download/{ident}/" + urllib.parse.quote(mp4s[0]["name"])
            kf = CACHE / "_kf.jpg"
            subprocess.run(["ffmpeg", "-y", "-ss", "60", "-i", url, "-frames:v", "1", "-vf", "scale=512:-1", str(kf)], capture_output=True, timeout=45)
            if not kf.exists() or not vision_verifica_assunto(subject, kf):
                kf.unlink(missing_ok=True); continue
            kf.unlink(missing_ok=True)
            subprocess.run(["ffmpeg", "-y", "-ss", "60", "-i", url, "-t", "5", "-an", "-vf", "scale=-2:1080",
                            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "21", "-movflags", "+faststart", str(dest)],
                           capture_output=True, timeout=120)
            if dest.exists() and dest.stat().st_size > 20000:
                return 5
        except Exception:
            continue
    return 0


# ---------- classificação: query visual por beat + é sobre algo específico/real? ----------
def classificar(cenas):
    """Retorna {idx: (real_query|None, vquery)}: vquery = busca visual concisa do beat;
    real_query = busca Commons precisa SE for entidade/evento real específico (senão None)."""
    linhas = "  ".join(f"[{c['idx']}] {c['texto'].replace(chr(34), '')}" for c in cenas)
    prompt = (
        "For each documentary scene below, return a JSON object with keys: "
        "scene (the integer id shown in brackets), "
        "vquery (a concise 3-6 word ENGLISH visual search query naming the concrete scene/subject/action to "
        "illustrate that line, for stock and archive image search — never the raw sentence), and "
        "real_query (if the line names a SPECIFIC real historical subject/event/person/object/document that "
        "Wikimedia Commons would have a real archival image of, e.g. 'Pearl Harbor attack 1941', a precise Commons "
        "search query; otherwise null — be STRICT, when unsure null). "
        "Return ONLY a JSON array. Scenes: " + linhas)
    out = _api_text(prompt, timeout=150)   # API primária (paralelizável, sem quota hoje)
    if out is None:                        # API indisponível -> CLI
        out = _cli_text(prompt)
    out = out or ""
    a, b = out.find("["), out.rfind("]")
    res = {}
    if a >= 0 and b > a:
        try:
            for o in json.loads(out[a:b + 1]):
                m = re.search(r"\d+", str(o.get("scene", "")))
                if not m:
                    continue
                vq = (o.get("vquery") or "").strip() or None
                res[int(m.group())] = (o.get("real_query") or None, vq)
        except Exception as e:
            print(f"  classificar parse falhou: {str(e)[:60]}")
    return res


# ---------- L0: casa beats atmosféricos com o banco de arquivo do TEMA ----------
def match_bank(cenas, real, banco):
    """Para cada beat genérico, retorna candidatos RANKEADOS do banco-tema. {idx: [clip_i, ...] melhor->pior}."""
    gen = [c for c in cenas if not real.get(c["idx"])]
    if not gen or not banco:
        return {}
    bank_txt = "  ".join(f"[{i}] {b.get('desc', '')[:60]}" for i, b in enumerate(banco))
    beats_txt = "  ".join(f"[{c['idx']}] {c['texto'][:70].replace(chr(34), '')}" for c in gen)
    prompt = ("For each NARRATION beat, list the TOP 3 archive clip indices that best ILLUSTRATE that line, best "
              "first, or [] if none fits. Spread choices across beats for VARIETY. Return ONLY a JSON array of "
              "objects with keys scene and clips (array of clip indices). CLIPS: " + bank_txt + "   BEATS: " + beats_txt)
    try:
        p = subprocess.Popen(f'gemini -p "{prompt}"', shell=True, cwd=str(TESTE),
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace")
        out, _ = p.communicate(timeout=150)
        a, b = out.find("["), out.rfind("]")
        if a >= 0 and b > a:
            return {int(o["scene"]): [int(x) for x in (o.get("clips") or [])] for o in json.loads(out[a:b + 1]) if "scene" in o}
    except subprocess.TimeoutExpired:
        subprocess.run(f"taskkill /F /T /PID {p.pid}", shell=True, capture_output=True)
    except Exception as e:
        print(f"  match_bank falhou: {str(e)[:60]}")
    return {}


# ---------- cascata por cena ----------
# ---- BANCO LOCAL de imagens (modo híbrido do VidMator) ----
# Índice = teste/index_<nicho>_imagens.json (indexar_imagens.py: {itens:{abs_path:{keep,desc,tags,mood,tipo}}}).
# Híbrido = MISTURA por RELEVÂNCIA (não fallback): o banco só ganha do stock quando as tags casam com o beat.
_BANCO_IMGS = []      # [{path, tags(set), desc_toks(set)}]
_BANCO_USOS = {}      # path -> nº usos neste vídeo (diversidade; o reuso pós-hoc também cobre)
_BANCO_MIN_SCORE = 3  # >=1 tag forte; abaixo disso o stock decide


def carregar_banco_local(preset):
    """Carrega o banco local se fonte_imagens in (local, hibrido). Env FONTE_IMAGENS/BANCO_IMAGENS_INDEX sobrepõem."""
    global _BANCO_IMGS
    fonte = (os.environ.get("FONTE_IMAGENS") or preset.get("fonte_imagens") or "api").lower()
    if fonte not in ("local", "hibrido"):
        return fonte
    nicho = preset.get("_nicho") or "default"
    idx_path = Path(os.environ.get("BANCO_IMAGENS_INDEX") or (TESTE / f"index_{nicho}_imagens.json"))
    if not idx_path.exists():
        print(f"  banco-local: índice não existe ({idx_path.name}) -> só stock")
        return fonte
    itens = json.load(open(idx_path, encoding="utf-8")).get("itens", {})
    for p, v in itens.items():
        if not v.get("keep") or v.get("_err") or not Path(p).exists():
            continue
        tags = set()
        for t in (v.get("tags") or []):
            tags.add(t); tags.update(t.split("-"))          # "nervous-system" -> tbm "nervous","system"
        desc = {w for w in re.sub(r"[^a-z0-9 ]", " ", (v.get("desc") or "").lower()).split() if len(w) > 3}
        _BANCO_IMGS.append({"path": p, "tags": tags, "desc": desc})
    print(f"  banco-local [{fonte}]: {len(_BANCO_IMGS)} imagens utilizáveis ({idx_path.name})")
    return fonte


def banco_local_match(beat, query, idx, evitar=frozenset()):
    """Melhor imagem do banco pro beat (score tags/desc). None se nada relevante."""
    if not _BANCO_IMGS:
        return None
    toks = {w for w in re.sub(r"[^a-z0-9 ]", " ", f"{beat} {query}".lower()).split() if len(w) > 3}
    best, best_score = None, 0
    for e in _BANCO_IMGS:
        if e["path"] in evitar:
            continue
        s = 3 * len(toks & e["tags"]) + len(toks & e["desc"])
        if s < _BANCO_MIN_SCORE:
            continue
        s -= 2 * _BANCO_USOS.get(e["path"], 0)              # penaliza repetição -> espalha o banco
        if s > best_score or (s == best_score and best and hash((e["path"], idx)) % 2):
            best, best_score = e, s
    if not best:
        return None
    _BANCO_USOS[best["path"]] = _BANCO_USOS.get(best["path"], 0) + 1
    return best["path"]


def resolve(beat, query, real_query, idx, index, evitar=frozenset(), prefer_video=False):
    h = qhash(f"{query}|{real_query or ''}")
    if h in index and index[h]["file"] not in evitar:
        e = index[h]
        # se o beat agora mira VÍDEO mas o cache é imagem, re-resolve pra tentar vídeo
        if not (prefer_video and e.get("media_tipo") == "imagem"):
            return e["file"], e["media_tipo"], e["dur"], e.get("nivel", "?")

    # MIX — slot de VÍDEO: tenta stock vídeo ANTES da cascata de imagem (good|weak),
    # pra equilibrar ~50/50 imagem/vídeo. (archive de época entra aqui quando houver banco no Drive.)
    if prefer_video:
        try:
            vids = pexels_clean(query, "videos")   # green-screen filtrado
            vkey = str(CACHE / f"v{h}.mp4").replace("\\", "/")
            if vids and vkey not in evitar:   # Pexels já vem rankeado por relevância -> SEM Vision (escala p/ N grande)
                dur = pexels_download(vids[0], "videos", CACHE / f"v{h}.mp4")
                if dur:
                    index[h] = {"file": vkey, "media_tipo": "video", "dur": dur, "nivel": "L3v-mix"}
                    _save_index(index)
                    return vkey, "video", dur, "L3v-mix"
        except Exception as e:
            print(f"    L3v erro: {str(e)[:40]}")

    # L1 — VÍDEO PD real do assunto (archive.org) com gate de IDENTIDADE
    if real_query and USE_ARCHIVE_L1:
        dest = CACHE / f"a{h}.mp4"
        dur = archive_video(real_query, real_query, dest)
        if dur:
            index[h] = {"file": str(dest).replace("\\", "/"), "media_tipo": "video", "dur": dur, "nivel": "L1-archive"}
            _save_index(index)
            return index[h]["file"], "video", dur, "L1-archive"

    # L2 — IMAGEM PD do assunto (Commons) com gate de IDENTIDADE (é mesmo DO assunto?)
    if real_query and USE_COMMONS_L2:
        dest = CACHE / f"c{h}.jpg"
        if commons_image(real_query, dest):
            if vision_verifica_assunto(real_query, dest):
                index[h] = {"file": str(dest).replace("\\", "/"), "media_tipo": "imagem", "dur": 5, "nivel": "L2-commons"}
                _save_index(index)
                return index[h]["file"], "imagem", 5, "L2-commons"
            dest.unlink(missing_ok=True)  # não é do assunto -> cai pro stock

    # L2t — IMAGEM da ÉPOCA (Commons por tema) p/ beat atmosférico, ANTES do stock vídeo
    if not real_query and USE_TEMA_IMG:
        dest = CACHE / f"t{h}.jpg"
        if str(dest).replace("\\", "/") not in evitar and commons_image(query, dest):
            if vision_tema_ok(query, dest):
                index[h] = {"file": str(dest).replace("\\", "/"), "media_tipo": "imagem", "dur": 5, "nivel": "L2t-epoca"}
                _save_index(index)
                return index[h]["file"], "imagem", 5, "L2t-epoca"
            dest.unlink(missing_ok=True)  # não usável -> cai pro stock

    # Lb — BANCO LOCAL (híbrido): imagem própria do canal quando REALMENTE casa com o beat (score de tags).
    # Ganha do stock só por relevância; senão a cascata segue normal -> mistura natural local×stock.
    if not prefer_video and _BANCO_IMGS:
        lb = banco_local_match(beat, query, idx, evitar)
        if lb:
            index[h] = {"file": lb.replace("\\", "/"), "media_tipo": "imagem", "dur": 6, "nivel": "Lb-banco"}
            _save_index(index)
            return index[h]["file"], "imagem", 6, "Lb-banco"

    # L4i — beat NÃO-vídeo: Pexels FOTO antes do stock vídeo -> imagem + Ken Burns (equilibra ~50/50)
    if not prefer_video:
        try:
            fotos = pexels_clean(query, "photos")
            dest = CACHE / f"p{h}.jpg"
            if fotos and str(dest).replace("\\", "/") not in evitar and pexels_download(fotos[0], "photos", dest):
                index[h] = {"file": str(dest).replace("\\", "/"), "media_tipo": "imagem", "dur": 6, "nivel": "L4i-foto-kb"}
                _save_index(index)
                return index[h]["file"], "imagem", 6, "L4i-foto-kb"
        except Exception as e:
            print(f"    L4i erro: {str(e)[:40]}")

    # L3 — stock vídeo (Pexels top, green-screen filtrado)
    best_video = None
    try:
        vids = pexels_clean(query, "videos")
        if vids:
            best_video = vids[0]
            vkey = str(CACHE / f"v{h}.mp4").replace("\\", "/")
            if vkey not in evitar:
                dur = pexels_download(best_video, "videos", CACHE / f"v{h}.mp4")
                if dur:
                    index[h] = {"file": vkey, "media_tipo": "video", "dur": dur, "nivel": "L3-video"}
                    _save_index(index)
                    return vkey, "video", dur, "L3-video"
    except Exception as e:
        print(f"    L3 erro: {str(e)[:40]}")

    # L4 — stock imagem (Pexels top, green-screen filtrado)
    try:
        fotos = pexels_clean(query, "photos")
        if fotos:
            dest = CACHE / f"p{h}.jpg"
            if pexels_download(fotos[0], "photos", dest):
                index[h] = {"file": str(dest).replace("\\", "/"), "media_tipo": "imagem", "dur": 5, "nivel": "L4-foto"}
                _save_index(index)
                return index[h]["file"], "imagem", 5, "L4-foto"
    except Exception as e:
        print(f"    L4 erro: {str(e)[:40]}")

    # L5 — genérico: usa o melhor vídeo do L3 se existir, senão query ampla
    if best_video:
        dest = CACHE / f"v{h}.mp4"
        dur = pexels_download(best_video, "videos", dest)
        if dur:
            index[h] = {"file": str(dest).replace("\\", "/"), "media_tipo": "video", "dur": dur, "nivel": "L5-fallback"}
            _save_index(index)
            return index[h]["file"], "video", dur, "L5-fallback"
    try:
        amplo = " ".join(query.split()[-2:])
        vids = pexels_clean(amplo, "videos")
        if vids:
            dest = CACHE / f"v{h}.mp4"
            dur = pexels_download(vids[0], "videos", dest)
            if dur:
                index[h] = {"file": str(dest).replace("\\", "/"), "media_tipo": "video", "dur": dur, "nivel": "L5-amplo"}
                _save_index(index)
                return index[h]["file"], "video", dur, "L5-amplo"
    except Exception:
        pass
    # L6 IA — desligado (USE_IA=False)
    return None, None, 0, "none"


def main():
    CACHE.mkdir(parents=True, exist_ok=True)
    index = json.load(open(INDEX, encoding="utf-8")) if INDEX.exists() else {}
    tl = json.load(open(TIMELINE, encoding="utf-8"))
    cenas = tl["cenas"]
    print(f"=== Resolver em cascata: {len(cenas)} cenas | Pexels: {len(PEX_KEYS)} chave(s) (~{200*max(len(PEX_KEYS),1)} req/h) ===")
    print("  classificando (query visual + assunto real) via Gemini...")
    info = classificar(cenas)   # {idx: (real_query|None, vquery)}

    # Banco de VÍDEO de arquivo (archive.org ao vivo) — desligado por instabilidade.
    # Religar via Drive: setar USE_TEMA_BANK=True + popular catalogo.json. Por ora a época
    # vem de IMAGENS (L2t Commons), confiáveis.
    if USE_TEMA_BANK and BANK_TEMA.exists():
        banco = json.load(open(BANK_TEMA, encoding="utf-8"))
        bank_match = match_bank(cenas, real, banco) if banco else {}
        print(f"  banco-tema: {len(banco)} clipes")
    else:
        print("  banco-tema: desligado -> época via imagens (L2t Commons)")

    from collections import Counter
    niveis = Counter()
    PAR_WORKERS = 8   # resolve beats em PARALELO (downloads I/O-bound; Vision só no Commons agora)
    beats = sorted(cenas, key=lambda x: x.get("inicio", 0))
    # equilíbrio vídeo/imagem POR NICHO (video_frac do preset; default 0.8, ttm=0.5). Distribuição uniforme (Bresenham).
    # Entidade nomeada (real_query) NUNCA força vídeo -> mantém imagem real (L2 Commons).
    from preset import carregar
    _PRESET = carregar(tl)
    F_VIDEO = float(_PRESET.get("video_frac", 0.8))
    VET_REL = bool(_PRESET.get("vet_relevancia", False))
    fonte_img = carregar_banco_local(_PRESET)   # híbrido: banco local do nicho entra na cascata (Lb)
    print(f"  preset={_PRESET.get('_nicho')} | video_frac={F_VIDEO} | vet_relevancia={VET_REL} | fonte_imagens={fonte_img}")
    prefer = {c["idx"]: (not info.get(c["idx"], (None, None))[0]) and (int((k + 1) * F_VIDEO) != int(k * F_VIDEO))
              for k, c in enumerate(beats)}

    def _vquery(c):
        rq, vq = info.get(c["idx"], (None, None))
        return (vq or c.get("stock_query") or c["texto"][:60]), rq

    def _resolve_beat(c):
        q, rq = _vquery(c)
        path, mt, dur, nivel = resolve(c["texto"][:120], q, rq, c["idx"], index, prefer_video=prefer[c["idx"]])
        # #5b — aperto de relevância MODERADO (gated por preset): só VÍDEO atmosférico; rejeita só "none"
        # (claramente nada a ver) -> troca por IMAGEM (Ken Burns), NÃO cai em IA/fallback. Lenient de propósito.
        if VET_REL and mt == "video" and path and not rq:
            try:
                kf = Path(path).parent / f"_relchk_{c['idx']}.jpg"
                subprocess.run(["ffmpeg", "-y", "-ss", "2", "-i", path, "-frames:v", "1", "-vf", "scale=512:-1", str(kf)],
                               capture_output=True, timeout=30)
                if kf.exists() and vision_fit(c["texto"], str(kf)) == "none":
                    alt = resolve(c["texto"][:120], q, rq, c["idx"], index, prefer_video=False)
                    if alt[0]:
                        path, mt, dur, nivel = alt
                        print(f"  [{c['idx']:>2}] vídeo irrelevante -> trocou p/ imagem ({nivel})")
                Path(kf).unlink(missing_ok=True)
            except Exception:
                pass
        return c, q, rq, path, mt, dur, nivel

    print(f"  resolvendo {len(beats)} beats em paralelo ({PAR_WORKERS} workers)...")
    with ThreadPoolExecutor(max_workers=PAR_WORKERS) as ex:
        resolved = list(ex.map(_resolve_beat, beats))

    # Reuso baixo (pós-hoc, em ordem temporal): arquivo saturado na janela -> re-resolve evitando-o.
    usos = {}
    res = {}
    for c, q, rq, path, mt, dur, nivel in resolved:
        t0 = c.get("inicio", 0)
        if path:
            recentes = [t for t in usos.get(path, []) if t0 - t < JANELA_REUSO]
            if len(recentes) >= MAX_REUSO:
                alt = resolve(c["texto"][:120], q, rq, c["idx"], index, evitar={path}, prefer_video=prefer[c["idx"]])
                if alt[0]:
                    path, mt, dur, nivel = alt
                    print(f"  [{c['idx']:>2}] reuso>{MAX_REUSO} -> diversificou p/ {nivel}")
            usos.setdefault(path, []).append(t0)
        res[c["idx"]] = (path, mt, dur, nivel, rq, q)

    for c in cenas:
        path, mt, dur, nivel, rq, q = res.get(c["idx"], (None, None, 0, "none", None, ""))
        if not path:
            print(f"  [{c['idx']:>2}] SEM MÍDIA p/ '{q[:40]}'")
            continue
        c["clip_path"] = path; c["clip_dur"] = dur; c["media_tipo"] = mt
        c["nivel"] = nivel; c["real_query"] = rq
        niveis[nivel] += 1
        print(f"  [{c['idx']:>2}] {nivel:<12} {mt:<6} {q[:42]}")

    # FALLBACK anti-gap: cenas sem mídia (ex.: Pexels rate-limited / 429) reusam clips já resolvidos,
    # round-robin evitando repetir em sequência. Garante vídeo COMPLETO sem buracos pretos.
    pool = [(c["clip_path"], c.get("clip_dur", 5), c.get("media_tipo", "video")) for c in cenas if c.get("clip_path")]
    faltam = [c for c in cenas if not c.get("clip_path")]
    if pool and faltam:
        ri, prev = 0, None
        for c in cenas:
            if c.get("clip_path"):
                prev = c["clip_path"]; continue
            for _ in range(len(pool)):
                cand = pool[ri % len(pool)]; ri += 1
                if cand[0] != prev:
                    break
            c["clip_path"], c["clip_dur"], c["media_tipo"] = cand
            c["nivel"], c["real_query"] = "reuse-fill", None
            prev = cand[0]; niveis["reuse-fill"] += 1
        print(f"  reuse-fill: {len(faltam)} cenas sem stock preenchidas reusando {len(pool)} clips")

    json.dump(tl, open(TIMELINE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    _save_index(index)
    print(f"\nOK — níveis usados: {dict(niveis)} | cache: {len(index)}")


if __name__ == "__main__":
    main()
