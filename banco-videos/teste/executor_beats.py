# -*- coding: utf-8 -*-
"""EXECUTOR de plano de beats (Stage 3 do Diretor) — plano_beats.json -> assets reais.
Por beat, despacha pro resolvedor do tipo:
  footage_video  -> YouTube (licença->tier, respeita teto) + gate Vision; falhou -> Pexels T1 -> fallback
  footage_imagem -> Wikimedia Commons (licença->tier) + gate; falhou -> Pexels foto -> fallback
  stock          -> Pexels (vídeo->foto) + gate
  ilustracao     -> ilustrador.py (Together: gpt-image-2 / imagen-4-fast -> NB2 Lite) + pad_169
  animacao       -> passthrough (componente+dados; Stage 4 renderiza)
Cadeia de FALLBACK por beat (nunca footage errado, nunca vazio; último recurso = color_plate).
Regras: áudio 0%, cap por tier (T3<=5s/T2,T1<=8s), no-repeat (ids usados), marca-d'água centro=rejeita,
marca canto=aceita marcado p/ crop. RESUMÍVEL (resolvido/b###.json) e paralelo (4 workers).

Uso: python executor_beats.py --plano <plano_beats.json> --job <pasta_job> [--max N] [--tipos a,b]
"""
import argparse
import json
import re
import subprocess
import sys
import threading
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).parent))
from vision_gate import gate, _frames_de_video
from pexels_api import search as pex_search, KEYS as PEX_KEYS
from ilustrador import ilustrar, pad_169
from proxy_pool import proximo as proxy_proximo, reportar as proxy_reportar, total as proxy_total

YTDLP = [sys.executable, "-m", "yt_dlp"]
UA = {"User-Agent": "Mozilla/5.0"}
COMMONS_UA = {"User-Agent": "CanalDark/1.0 (research; github.com/violipte)"}
BAD_TITLE = re.compile(r"\b(kid|kids|child|children|baby|toy|cartoon|nursery)\b", re.I)
BRANDS = re.compile(r"\b(toyota|hilux|land ?cruiser|harley[- ]?davidson|harley|top ?gear|bbc|honda|kawasaki|suzuki|yamaha|ford|chevrolet)\b", re.I)
TETO_N = {"stock": 1, "cc_pd": 2, "web": 3}
CAP_TIER = {1: 8, 2: 8, 3: 5}
MAX_CAND = 6

_LOCK = threading.Lock()
USED = set()          # ids de fonte já usados (no-repeat)
CANAIS_BAN = set()     # canais banidos por job (canais_banidos.txt)
STATS = {"gate_reject": 0, "fallback": 0}


# ---------------- helpers de fonte ----------------
def _yt_args_proxy():
    """Args de proxy (round-robin do pool) + pacing leve. Sem pool = direto."""
    p = proxy_proximo()
    args = ["--sleep-requests", "0.8"]
    if p:
        args += ["--proxy", p]
    return p, args


def yt_search(q, n=5):
    p, pargs = _yt_args_proxy()
    r = subprocess.run(YTDLP + pargs + ["-J", "--no-warnings", "--no-flat-playlist", "--ignore-errors",
                                        "--socket-timeout", "25", f"ytsearch{n}:{q}"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    try:
        ents = [e for e in (json.loads(r.stdout).get("entries") or []) if e]
        proxy_reportar(p, ok=bool(ents))
        return ents
    except Exception:
        proxy_reportar(p, ok=False)
        return []


def yt_tier(lic):
    return 2 if "creative commons" in (lic or "").lower() else 3


def yt_baixar(e, cap, dest, seg=0):
    dur = e.get("duration") or 120
    start = int(min(max(dur * 0.2, 8) + seg * (cap + 4), max(dur - cap - 1, 1)))
    p, pargs = _yt_args_proxy()
    subprocess.run(YTDLP + pargs + ["-f", "bv[height<=1080][ext=mp4]/bv[height<=1080]/bv*/b[height<=1080]",
                                    "--download-sections", f"*{start}-{start + cap}", "--force-keyframes-at-cuts",
                                    "-o", str(dest), "--no-warnings", "--no-playlist", "--no-part",
                                    "--socket-timeout", "25", "-R", "3",
                                    f"https://www.youtube.com/watch?v={e['id']}"],
                   capture_output=True, text=True)
    proxy_reportar(p, ok=dest.exists())
    return dest.exists()


def normalizar(tmp, out, cap):
    subprocess.run(["ffmpeg", "-y", "-i", str(tmp), "-an", "-t", str(cap), "-vf", "scale=-2:1080",
                    "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-loglevel", "error", str(out)],
                   capture_output=True)
    tmp.unlink(missing_ok=True)
    return out.exists()


def commons_list(q, n=8):
    try:
        url = ("https://commons.wikimedia.org/w/api.php?action=query&format=json&generator=search"
               f"&gsrnamespace=6&gsrsearch={urllib.parse.quote(q)}&gsrlimit={n}"
               "&prop=imageinfo&iiprop=url|extmetadata&iiurlwidth=1600")
        d = json.loads(urllib.request.urlopen(urllib.request.Request(url, headers=COMMONS_UA), timeout=30).read())
        out = []
        for p in ((d.get("query") or {}).get("pages", {}) or {}).values():
            ii = (p.get("imageinfo") or [{}])[0]
            u = ii.get("thumburl") or ii.get("url")
            if not u or not re.search(r"\.(jpg|jpeg|png)$", u, re.I):
                continue
            lic = ((ii.get("extmetadata") or {}).get("LicenseShortName") or {}).get("value", "") or "?"
            tier = 1 if ("public domain" in lic.lower() or "cc0" in lic.lower()) else 2
            out.append((u, lic, tier))
        return out
    except Exception:
        return []


def baixar_url(u, dest, headers, min_kb=8):
    try:
        raw = urllib.request.urlopen(urllib.request.Request(u, headers=headers), timeout=90).read()
        if len(raw) < min_kb * 1024:
            return False
        dest.write_bytes(raw)
        return True
    except Exception:
        return False


def marca_usado(cid):
    with _LOCK:
        if cid in USED:
            return False
        USED.add(cid)
        return True


def ja_usado(cid):
    with _LOCK:
        return cid in USED


# ---------------- gate por beat ----------------
def subject_do_beat(beat, loose=False):
    base = beat.get("busca") or beat.get("texto") or "the documentary subject"
    if beat.get("strict"):
        base = base + " (the EXACT subject must be clearly visible)"
    elif loose:
        base = "a scenic or atmospheric documentary shot fitting: " + base
    # ARQUITETURA FUNCIONÁRIOS (25/07): contexto de SEÇÃO injetado pelo curador —
    # o gate julga o clipe sabendo de que produto a seção fala e quais marcas o
    # vídeo cobre (marca fora da lista NUNCA passa)
    if beat.get("_sec_ctx"):
        base = base + ". " + beat["_sec_ctx"]
    return base


def gate_retry(subject, frames, retries=2):
    """Gate com retry quando o Vision está indisponível (429/quota) — evita FALSO reject."""
    import time as _t
    for k in range(retries + 1):
        g = gate(subject, frames)
        if g["flags"] != ["sem-resposta-vision"]:
            return g
        _t.sleep(6 * (k + 1))
    return g


def _frames_pretos(frames):
    """Pré-check local: todos os frames quase pretos/brancos-chapados = clipe morto (economiza gate)."""
    try:
        from PIL import Image, ImageStat
        for f in frames:
            m = ImageStat.Stat(Image.open(f).convert("L")).mean[0]
            if 14 < m < 245:
                return False
        return True
    except Exception:
        return False


# ---- DEDUP VISUAL na ENTRADA (27/07: preqa pegava 17 dups DEPOIS do render;
# agora nenhum clipe visualmente igual a um já aceito entra no job) ----
_HASHES_JOB = {}  # job_dir -> {nome_arquivo: dhash}


def _dhash_img(img_path):
    try:
        from PIL import Image
        im = Image.open(img_path).convert("L").resize((9, 8))
        px = list(im.getdata())
        bits = 0
        for r in range(8):
            for c in range(8):
                bits = (bits << 1) | (1 if px[r * 9 + c] > px[r * 9 + c + 1] else 0)
        return bits
    except Exception:
        return None


def _dhash_video(path, tmpdir):
    """Hashes em 2 INSTANTES (1s e ~meio) — cena que diverge no início mas coincide
    no meio era o furo das 20 duplicatas do estoico (27/07)."""
    hs = []
    for ss in ("1", "3.5"):
        o = Path(tmpdir) / f"{Path(path).stem}_dh{ss}.jpg"
        subprocess.run(["ffmpeg", "-y", "-ss", ss, "-i", str(path), "-frames:v", "1",
                        "-vf", "scale=160:-2", "-loglevel", "error", str(o)], capture_output=True)
        h = _dhash_img(o) if o.exists() else None
        if h is not None:
            hs.append(h)
    return hs or None


def _e_dup_visual(path, ctx, limiar=6):
    """True se o clipe é visualmente ~igual a um asset já aceito no job (dist Hamming <= limiar)."""
    job_key = str(ctx["assets"])
    if job_key not in _HASHES_JOB:
        _HASHES_JOB[job_key] = {}
        for f in Path(ctx["assets"]).glob("*.mp4"):
            h0 = _dhash_video(f, ctx["tmp"])
            if h0 is not None:
                _HASHES_JOB[job_key][f.name] = h0
    hs = _dhash_video(path, ctx["tmp"])
    if not hs:
        return False
    for nome, hs0 in _HASHES_JOB[job_key].items():
        if nome == Path(path).name:
            continue
        for h in hs:
            for h0 in (hs0 if isinstance(hs0, list) else [hs0]):
                if bin(h ^ h0).count("1") <= limiar:
                    return True
    _HASHES_JOB[job_key][Path(path).name] = hs
    return False


def _ocr_tem_texto(img_path, min_chars=4):
    """OCR determinístico (27/07): texto queimado em crop de faixa = True. Sem engine, False."""
    try:
        import pytesseract
        from PIL import Image
        pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
        txt = pytesseract.image_to_string(Image.open(img_path), config="--psm 6").strip()
        limpo = "".join(c for c in txt if c.isalnum())
        return len(limpo) >= min_chars
    except Exception:
        return False


def gate_video(path, beat, tmpdir, loose=False):
    frames = _frames_de_video(path, tmpdir, n=6)  # duração INTEIRA (n=2 deixava caption/vlogger passar)
    # 27/07: caption PEQUENA some em frame 384px — manda também CROPS ampliados
    # das faixas topo/rodapé (onde as pills de caption vivem)
    try:
        for ss in ("1", "2.5", "4"):  # 3 instantes — caption pode entrar tarde
            for nome_c, filtro in (("topo", "crop=iw:ih*0.2:0:0,scale=768:-2"),
                                   ("rodape", "crop=iw:ih*0.2:0:ih*0.8,scale=768:-2")):
                oc = Path(tmpdir) / f"{Path(path).stem}_crop_{nome_c}_{ss}.jpg"
                subprocess.run(["ffmpeg", "-y", "-ss", ss, "-i", str(path), "-frames:v", "1",
                                "-vf", filtro, "-loglevel", "error", str(oc)], capture_output=True)
                if oc.exists():
                    # OCR DETERMINÍSTICO: qualquer texto queimado na faixa = clipe fora
                    if _ocr_tem_texto(oc):
                        return {"ok": False, "flags": ["ocr-caption"], "watermark": False,
                                "watermark_pos": None, "reason": f"texto queimado ({nome_c} @{ss}s)"}
                    frames.append(oc)
    except Exception:
        pass
    if not frames:
        return {"ok": False, "flags": ["sem-frames"], "watermark": False, "watermark_pos": None, "reason": ""}
    if _frames_pretos(frames):
        return {"ok": False, "flags": ["frame-preto"], "watermark": False, "watermark_pos": None, "reason": "clipe preto/chapado"}
    return gate_retry(subject_do_beat(beat, loose), frames)


# ---------------- resolvedores por tipo ----------------
def resolver_footage_video(beat, ctx):
    """YouTube licença->tier (respeita teto) -> Pexels T1. Marca canto = backup marcado p/ crop."""
    teto = TETO_N.get(beat.get("tier_teto", "web"), 3)
    backup = None
    if teto >= 2:
        for k, e in enumerate(yt_search(beat.get("busca") or beat.get("texto"), 5)):
            # ban por CANAL (jardim 26/07: canal 'square meter' voltou 4x por IDs novos)
            if str(e.get("channel") or e.get("uploader") or "").strip().lower() in CANAIS_BAN:
                continue
            if k >= MAX_CAND:
                break
            dur = e.get("duration") or 0
            if e.get("is_live") or dur < 20 or dur > 2700 or BAD_TITLE.search(e.get("title", "")):
                continue
            if ja_usado(e["id"]):
                continue
            tier = yt_tier(e.get("license"))
            if tier > teto:
                continue
            cap = CAP_TIER[tier]
            tmp = ctx["tmp"] / f"b{beat['i']:03d}.mp4"
            if not yt_baixar(e, cap, tmp):
                continue
            out = ctx["assets"] / f"b{beat['i']:03d}__T{tier}__yt_{e['id']}.mp4"
            if not normalizar(tmp, out, cap):
                continue
            if _e_dup_visual(out, ctx):  # DEDUP na entrada
                out.unlink(missing_ok=True)
                marca_usado(e["id"])
                continue
            g = gate_video(out, beat, ctx["tmp"] / "_g")
            if g["ok"] and not g.get("watermark"):
                marca_usado(e["id"])
                return {"status": "ok", "tipo_final": "footage_video", "arquivo": str(out), "tier": tier,
                        "fonte": "youtube", "watermark": False}
            if g["ok"] and g.get("watermark") and backup is None:
                backup = {"status": "ok", "tipo_final": "footage_video", "arquivo": str(out), "tier": tier,
                          "fonte": "youtube", "watermark": True, "watermark_pos": g.get("watermark_pos"),
                          "cid": e["id"]}
                continue  # tenta achar um limpo; guarda o com marca de canto
            with _LOCK:
                STATS["gate_reject"] += 1
            out.unlink(missing_ok=True)
    if backup:  # nenhum limpo: usa o com marca de canto (crop no StandardClip)
        marca_usado(backup.pop("cid"))
        return backup
    # Pexels T1 (stock de vídeo)
    r = resolver_stock(beat, ctx, gate_loose=False)
    if r["status"] == "ok":
        return r
    return aplicar_fallback(beat, ctx)


def resolver_footage_imagem(beat, ctx):
    teto = TETO_N.get(beat.get("tier_teto", "web"), 3)
    if teto >= 2:
        for k, (u, lic, tier) in enumerate(commons_list(beat.get("busca") or beat.get("texto"))):
            if k >= MAX_CAND or ja_usado(u):
                continue
            dest = ctx["assets"] / f"b{beat['i']:03d}__T{tier}__commons.jpg"
            if not baixar_url(u, dest, COMMONS_UA):
                continue
            g = gate_retry(subject_do_beat(beat), [dest])
            if g["ok"] and not (g.get("watermark") and str(g.get("watermark_pos") or "").lower() == "center"):
                marca_usado(u)
                return {"status": "ok", "tipo_final": "footage_imagem", "arquivo": str(dest), "tier": tier,
                        "fonte": "commons", "watermark": bool(g.get("watermark"))}
            with _LOCK:
                STATS["gate_reject"] += 1
            dest.unlink(missing_ok=True)
    # Pexels foto T1
    for it in (pex_search(beat.get("busca") or beat.get("texto"), "photos", 4) if PEX_KEYS else []):
        cid = f"pexp_{it.get('id')}"
        if ja_usado(cid):
            continue
        dest = ctx["assets"] / f"b{beat['i']:03d}__T1__pexels_{it.get('id')}.jpg"
        if not baixar_url(it["src"]["original"], dest, UA):
            continue
        g = gate_retry(subject_do_beat(beat), [dest])
        if g["ok"]:
            marca_usado(cid)
            return {"status": "ok", "tipo_final": "footage_imagem", "arquivo": str(dest), "tier": 1,
                    "fonte": "pexels", "watermark": False}
        with _LOCK:
            STATS["gate_reject"] += 1
        dest.unlink(missing_ok=True)
    return aplicar_fallback(beat, ctx)


def resolver_stock(beat, ctx, gate_loose=False):
    # QA Piter 21/07: loose deixou passar Bíblia/criança/estudante/headphones — stock agora é ESTRITO
    q = beat.get("busca") or beat.get("texto")
    dur_beat = float(beat.get("t_fim") or 0) - float(beat.get("t_ini") or 0)
    for it in (pex_search(q, "videos", 4) if PEX_KEYS else []):
        cid = f"pexv_{it.get('id')}"
        if ja_usado(cid):
            continue
        # clipe mais curto que o beat = freeze/preto na tela (QA tenis 23/07: 2.5s num beat de 5s)
        if (it.get("duration") or 0) < max(4.0, dur_beat):
            continue
        files = [f for f in it.get("video_files", []) if f.get("file_type") == "video/mp4"]
        if not files:
            continue
        files.sort(key=lambda f: abs((f.get("width") or 0) - 1920) + (0 if (f.get("width") or 0) <= 1920 else 5000))
        tmp = ctx["tmp"] / f"b{beat['i']:03d}.mp4"
        if not baixar_url(files[0]["link"], tmp, UA, min_kb=30):
            continue
        out = ctx["assets"] / f"b{beat['i']:03d}__T1__pexels_{it.get('id')}.mp4"
        if not normalizar(tmp, out, 8):
            continue
        if _e_dup_visual(out, ctx):  # DEDUP na entrada: cena ~igual já existe no job
            out.unlink(missing_ok=True)
            marca_usado(cid)  # não tentar de novo este id
            continue
        g = gate_video(out, beat, ctx["tmp"] / "_g", loose=gate_loose)
        if g["ok"]:
            marca_usado(cid)
            return {"status": "ok", "tipo_final": "stock", "arquivo": str(out), "tier": 1,
                    "fonte": "pexels", "watermark": False}
        with _LOCK:
            STATS["gate_reject"] += 1
        out.unlink(missing_ok=True)
    return {"status": "falhou"}


# ---- R-111 (QA tenis 23/07): beat que ANUNCIA produto nomeado ("Number N, the X")
# mostra O PRODUTO — nunca card de texto, nunca footage genérico/marca errada ----
_ANNOUNCE = re.compile(r"\bnumber\s+(one|two|three|four|five|\d)\b[.,:]?\s", re.I)

def modelo_anunciado(texto, style):
    """Nome completo do modelo anunciado, via desambiguacao do style_card (ou None)."""
    if not texto or not _ANNOUNCE.search(texto):
        return None
    t = texto.lower()
    for chave, nome in (style.get("desambiguacao") or {}).items():
        if chave.lower() in t:
            return nome
    m = re.search(r"\bthe\s+([A-Z][\w' -]{3,40})", texto)
    return (m.group(1).strip(" .") + " (product)") if m else None

def resolver_produto(beat, ctx, modelo):
    """Foto do produto EXATO via web (T3, gate estrito). None = deixa o fluxo normal seguir."""
    try:
        from imagens_web import buscar_imagens_web, baixar_imagem
        for url in buscar_imagens_web(f"{modelo} product photo side view", 8):
            if ja_usado(url):
                continue
            dest = ctx["assets"] / f"b{beat['i']:03d}__T3__produto.jpg"
            if not baixar_imagem(url, dest):
                continue
            _cap_resolucao(dest)
            g = gate_retry(f"EXACT {modelo} product photo", [dest])
            if g["ok"]:
                marca_usado(url)
                return {"status": "ok", "tipo_final": "footage_imagem", "arquivo": str(dest),
                        "tier": 3, "fonte": "produto(R-111)", "watermark": False, "produto": modelo}
            dest.unlink(missing_ok=True)
            with _LOCK:
                STATS["gate_reject"] += 1
    except Exception as e:
        print(f"  [R-111] busca de produto falhou ({str(e)[:60]})")
    return None


def resolver_ilustracao(beat, ctx):
    busca = BRANDS.sub("", beat.get("busca") or beat.get("texto") or "").strip() or "technical diagram"
    # R-105 (Piter 22/07): ILUSTRAÇÃO REAL da web ANTES de gerar por IA — o diagrama de
    # manual/livro que a IA tenta imitar já existe. Licença desconhecida = T3 = máscara pesada.
    try:
        from imagens_web import buscar_imagens_web, baixar_imagem
        q_web = busca if "diagram" in busca.lower() or "illustration" in busca.lower() \
            else f"{busca} diagram illustration"
        for k, url in enumerate(buscar_imagens_web(q_web, 6)):
            if ja_usado(url):
                continue
            dest = ctx["assets"] / f"b{beat['i']:03d}__T3__webilus.jpg"
            if not baixar_imagem(url, dest):
                continue
            _cap_resolucao(dest)
            g = gate_retry(subject_do_beat(beat), [dest])
            if g["ok"]:
                marca_usado(url)
                return {"status": "ok", "tipo_final": "ilustracao", "arquivo": str(dest), "tier": 3,
                        "fonte": "web_ilus(R-105)", "watermark": False}
            dest.unlink(missing_ok=True)
            with _LOCK:
                STATS["gate_reject"] += 1
    except Exception as e:
        print(f"  [R-105] busca web falhou ({str(e)[:50]}) — caindo pra geração IA")
    # último recurso: geração por IA (T0, sem risco de licença)
    b = busca.lower()
    estilo = "blueprint" if ("schematic" in b or "blueprint" in b or "system" in b) else \
             ("manual" if ("diagram" in b or "exploded" in b or "labeled" in b) else "cutaway")
    dest = ctx["assets"] / f"b{beat['i']:03d}__GEN__ilus.png"
    if ilustrar(busca, dest, estilo):
        pad_169(dest)
        return {"status": "ok", "tipo_final": "ilustracao", "arquivo": str(dest), "tier": 0,
                "fonte": f"together/{estilo}", "watermark": False}
    return aplicar_fallback(beat, ctx)


def aplicar_fallback(beat, ctx):
    """Cadeia do beat: 'animacao:X' -> componente do acervo; 'atmosferico' -> stock mood; fim -> color_plate."""
    with _LOCK:
        STATS["fallback"] += 1
    for fb in (beat.get("fallback") or []):
        if fb.startswith("animacao"):
            # QA Piter 21/07: componente do LLM aqui vazava DEFAULT (Hilux/Tehran->Dubai).
            # Executor NÃO escolhe mais: componente=None => pass registry do montador decide.
            return {"status": "ok", "tipo_final": "animacao", "arquivo": None, "tier": 0,
                    "fonte": "acervo(fallback)", "componente": None,
                    "dados": beat.get("dados") or {"text": beat.get("texto", "")}, "watermark": False}
        if fb == "atmosferico":
            fb_beat = dict(beat)
            fb_beat["busca"] = "cinematic moody landscape road"
            fb_beat["strict"] = False
            r = resolver_stock(fb_beat, ctx)
            if r["status"] == "ok":
                r["fonte"] += "(fallback-atmosferico)"
                return r
    # penúltimo recurso: card de texto com a frase do beat (sempre melhor que plate vazio)
    if beat.get("texto"):
        return {"status": "ok", "tipo_final": "animacao", "arquivo": None, "tier": 0,
                "fonte": "acervo(ultimo-recurso)", "componente": "DisplayText",
                "dados": {"text": beat["texto"][:90]}, "watermark": False}
    return {"status": "ok", "tipo_final": "color_plate", "arquivo": None, "tier": 0,
            "fonte": "plate", "watermark": False}  # nunca vazio: Stage 4 renderiza plate+wash


def _cap_resolucao(path, maxpx=2560):
    """Pexels 'original' vem com 30MP — Chrome/ANGLE não decodifica sob VRAM cheia (EncodingError
    no job seniors 22/07). Toda imagem de slot é cappada em 2560px após o download."""
    try:
        from PIL import Image
        im = Image.open(path)
        if max(im.size) > maxpx + 40:
            im.thumbnail((maxpx, maxpx), Image.LANCZOS)
            im.convert("RGB").save(path, "JPEG", quality=90)
    except Exception:
        pass


def coletar_imgs(beat, ctx, n):
    """Resolve N imagens REAIS pros slots de animação de imagem (T2 Commons -> T1 Pexels + gate)."""
    q = beat.get("busca") or beat.get("texto") or ""
    # QA Piter 21/07: busca genérica trazia foto abstrata que o gate loose engolia —
    # amarra a query no ASSUNTO do beat (mesmo subject usado no gate)
    subj = subject_do_beat(beat)
    if subj and subj.split()[0].lower() not in q.lower():
        q = f"{subj} {q}"[:120]
    achadas = []
    for k, (u, lic, tier) in enumerate(commons_list(q, n=10)):
        if len(achadas) >= n or k >= n * 3:
            break
        if ja_usado(u):
            continue
        dest = ctx["assets"] / f"b{beat['i']:03d}__T{tier}__img{len(achadas)}.jpg"
        if not baixar_url(u, dest, COMMONS_UA):
            continue
        _cap_resolucao(dest)
        g = gate_retry(subject_do_beat(beat), [dest])
        if g["ok"]:
            marca_usado(u); achadas.append(str(dest))
        else:
            dest.unlink(missing_ok=True)
    # R-25: retrato de PESSOA REAL só de fonte nomeada (Commons) — stock genérico com o nome
    # de uma pessoa real embaixo = ATRIBUIÇÃO FALSA (QA seniors 22/07: 'Jeff Galloway' loiro do Pexels)
    if beat.get("componente") in ("CharacterCard", "CharacterKeyword"):
        return achadas
    if len(achadas) < n and PEX_KEYS:
        for it in pex_search(q, "photos", n * 3):
            if len(achadas) >= n:
                break
            cid = f"pexp_{it.get('id')}"
            if ja_usado(cid):
                continue
            dest = ctx["assets"] / f"b{beat['i']:03d}__T1__img{len(achadas)}.jpg"
            if not baixar_url(it["src"].get("large2x") or it["src"]["original"], dest, UA):
                continue  # large2x (~2880px) em vez do original de 30MP
            _cap_resolucao(dest)
            g = gate_retry(subject_do_beat(beat), [dest])
            if g["ok"]:
                marca_usado(cid); achadas.append(str(dest))
            else:
                dest.unlink(missing_ok=True)
    return achadas


def resolver_beat(beat, ctx):
    tipo = beat.get("tipo")
    # R-111: anúncio de produto nomeado tenta a FOTO DO PRODUTO antes de qualquer coisa
    if beat.get("_produto"):
        r = resolver_produto(beat, ctx, beat["_produto"])
        if r:
            return r
    if tipo == "animacao":
        n_slots = beat.get("img_slots") or 0
        if n_slots:
            from acervo_registry import rebuild
            imgs = coletar_imgs(beat, ctx, n_slots)
            props = rebuild(beat.get("componente"), beat.get("dados"), beat.get("texto"), imgs) if len(imgs) >= n_slots else None
            if props:
                return {"status": "ok", "tipo_final": "animacao", "arquivo": None, "tier": 0,
                        "fonte": "acervo+imgs", "componente": beat.get("componente"),
                        "props_final": props, "arquivos_img": imgs, "watermark": False}
            tx = (beat.get("texto") or "")[:80] or "…"  # sem imgs suficientes -> texto (nunca slot vazio)
            return {"status": "ok", "tipo_final": "animacao", "arquivo": None, "tier": 0,
                    "fonte": "acervo(sem-imgs)", "componente": "SingleSentenceTextSlide",
                    "props_final": {"sentence": tx}, "watermark": False}
        return {"status": "ok", "tipo_final": "animacao", "arquivo": None, "tier": 0, "fonte": "acervo",
                "componente": beat.get("componente"), "dados": beat.get("dados"),
                "props_final": beat.get("props_final"), "watermark": False}
    if tipo == "ilustracao":
        return resolver_ilustracao(beat, ctx)
    if tipo == "footage_video":
        return resolver_footage_video(beat, ctx)
    if tipo == "footage_imagem":
        return resolver_footage_imagem(beat, ctx)
    if tipo == "stock":
        r = resolver_stock(beat, ctx)
        return r if r["status"] == "ok" else aplicar_fallback(beat, ctx)
    return aplicar_fallback(beat, ctx)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plano", required=True)
    ap.add_argument("--job", required=True)
    ap.add_argument("--max", type=int, default=0, help="limita nº de beats (teste)")
    ap.add_argument("--tipos", default="", help="só estes tipos, csv")
    ap.add_argument("--workers", type=int, default=4)
    a = ap.parse_args()

    plano = json.loads(Path(a.plano).read_text(encoding="utf-8"))
    beats = plano["beats"]
    if a.tipos:
        tset = set(a.tipos.split(","))
        beats = [b for b in beats if b.get("tipo") in tset]
    if a.max:
        beats = beats[:a.max]

    job = Path(a.job)
    ctx = {"assets": job / "assets", "tmp": job / "_tmp", "res": job / "resolvido"}
    for d in ctx.values():
        d.mkdir(parents=True, exist_ok=True)

    # R-50/51/53 [F1]: style_card.json do job — desambiguação, banned_terms e assunto-âncora
    style = {}
    sc = job / "style_card.json"
    if sc.exists():
        try:
            style = json.loads(sc.read_text(encoding="utf-8"))
            print(f"style_card [R-50]: ancora='{style.get('assunto_ancora', '')}' "
                  f"banned={len(style.get('banned_terms', []))} desamb={len(style.get('desambiguacao', {}))}")
            from acervo_registry import set_style
            set_style(style)  # builders do registry (ex.: jornal_ficticio) enxergam o card aqui também
        except Exception as e:
            print(f"style_card ilegível ({e}) — seguindo sem [R-50]")

    # ARQUITETURA FUNCIONÁRIOS (25/07): o executor também injeta o contexto de SEÇÃO
    # no gate — sem isso, buraco deixado pelo curador era preenchido às cegas (moto 2×)
    try:
        from curador_footage import secoes_do_plano, ctx_da_secao
        _secs = secoes_do_plano(plano, style.get("desambiguacao") or {})
        _todos = sorted(set((style.get("desambiguacao") or {}).values()))
        for b0 in beats:
            if not b0.get("_sec_ctx"):
                b0["_sec_ctx"] = ctx_da_secao(_secs.get(b0.get("secao", 0), {"produto": None, "titulo": ""}), _todos)
        print(f"sec_ctx [FUNC]: contexto de seção injetado em {len(beats)} beats")
    except Exception as e:
        print(f"sec_ctx indisponível ({e}) — gate sem contexto de seção")

    # R-111: marca beats de ANÚNCIO de produto (foto do produto obrigatória)
    n_ann = 0
    for b0 in beats:
        mod = modelo_anunciado(b0.get("texto"), style)
        if mod:
            b0["_produto"] = mod
            n_ann += 1
    if n_ann:
        print(f"anuncios de produto [R-111]: {n_ann} beats")

    def _sanitizar_busca(q):
        if not q:
            return q
        for k, v in (style.get("desambiguacao") or {}).items():
            q = re.sub(rf"\b{re.escape(k)}\b", v, q, flags=re.I)   # R-53: marca ambígua
        for t in (style.get("banned_terms") or []):
            q = re.sub(rf"\b{re.escape(t)}\b", "", q, flags=re.I)  # R-51: termo abstrato fora
        q = " ".join(q.split())
        anc = style.get("assunto_ancora") or ""
        # R-25/R-105: retrato de pessoa e query de DIAGRAMA não ganham âncora do nicho
        if anc and "portrait" not in q.lower() and "diagram" not in q.lower() \
                and anc.split()[0].lower() not in q.lower():
            q = f"{anc} {q}"[:140]                                  # R-51: âncora presente
        return q

    # BLACKLIST persistente do job (QA seniors 22/07: asset condenado saía do USED ao ser
    # deletado e OUTRO beat re-baixava o mesmo vídeo ruim). 1 source-id por linha.
    bl = job / "blacklist.txt"
    if bl.exists():
        n_bl = 0
        for ln in bl.read_text(encoding="utf-8").splitlines():
            sid = ln.strip()
            if sid:
                USED.add(sid); USED.add(f"pexv_{sid}"); USED.add(f"pexp_{sid}"); n_bl += 1
        print(f"blacklist [R-75]: {n_bl} source-ids banidos do job")
    cb = job / "canais_banidos.txt"
    if cb.exists():
        for ln in cb.read_text(encoding="utf-8").splitlines():
            if ln.strip():
                CANAIS_BAN.add(ln.strip().lower())
        print(f"canais banidos: {len(CANAIS_BAN)}")

    # resume: reconstrói USED e pula beats já resolvidos
    feitos = {}
    for f in ctx["res"].glob("b*.json"):
        try:
            r = json.loads(f.read_text(encoding="utf-8"))
            feitos[r["i"]] = r
            arq = r.get("arquivo") or ""
            m = re.search(r"__(?:yt|pexels)_([A-Za-z0-9_-]+)\.", arq)
            if m:
                USED.add(m.group(1)); USED.add(f"pexv_{m.group(1)}"); USED.add(f"pexp_{m.group(1)}")
        except Exception:
            pass
    pend = [b for b in beats if b["i"] not in feitos]
    print(f"beats: {len(beats)} | já resolvidos: {len(feitos)} | pendentes: {len(pend)} | proxies: {proxy_total() or 'DIRETO'}")

    def worker(b):
        if b.get("busca"):
            b["busca"] = _sanitizar_busca(b["busca"])  # R-51/R-53: uma vez, cobre os 7 resolvedores
        try:
            r = resolver_beat(b, ctx)
        except Exception as e:
            r = {"status": "erro", "erro": str(e)[:150]}
        r.update({"i": b["i"], "tipo_plano": b.get("tipo"), "t_ini": b["t_ini"], "t_fim": b["t_fim"],
                  "secao": b.get("secao"), "busca": b.get("busca"), "estrategia": b.get("estrategia")})
        (ctx["res"] / f"b{b['i']:03d}.json").write_text(json.dumps(r, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"  b{b['i']:03d} [{b.get('tipo'):>14}] -> {r.get('tipo_final', r['status']):>13} "
              f"T{r.get('tier', '-')} {Path(r['arquivo']).name if r.get('arquivo') else (r.get('componente') or '')}",
              flush=True)
        return r

    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        list(ex.map(worker, pend))

    # merge final
    todos = []
    for f in sorted(ctx["res"].glob("b*.json")):
        try:
            todos.append(json.loads(f.read_text(encoding="utf-8")))
        except Exception:
            pass
    todos.sort(key=lambda r: r["i"])
    (job / "resolvido.json").write_text(json.dumps(todos, ensure_ascii=False, indent=1), encoding="utf-8")
    cont = {}
    for r in todos:
        cont[r.get("tipo_final", r["status"])] = cont.get(r.get("tipo_final", r["status"]), 0) + 1
    print(f"\n=== RESOLVIDO: {len(todos)} beats -> {job / 'resolvido.json'} ===")
    for k, v in sorted(cont.items(), key=lambda x: -x[1]):
        print(f"  {k:>15} {v:4}")
    print(f"  gate_rejects={STATS['gate_reject']}  fallbacks={STATS['fallback']}")


if __name__ == "__main__":
    main()
