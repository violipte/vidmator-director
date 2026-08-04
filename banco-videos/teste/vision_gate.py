# -*- coding: utf-8 -*-
"""GATE DE CONTEÚDO por LLM Vision (Gemini) — roda ANTES de qualquer asset (imagem/vídeo) entrar.
Reprova por 3 critérios (REGRAS_NICHOS §85 guardrails 3-5):
  (a) relevância/assunto  — é o objeto/ação certo? (pega stock frouxo)
  (b) child-safety        — tem criança? (reprova, salvo nicho que permita — e NUNCA em risco)
  (c) talking-head        — tem criador falando pra câmera? (reprova; exceção = entrevista de TV)
Vídeo: passe 2-3 frames amostrados; imagem: passe 1. Usa Gemini 2.5 Flash (rotação de chaves).
"""
import base64, json, subprocess, sys, urllib.request, urllib.error
from pathlib import Path

_CREDS = Path(r"F:/Canal Dark/Aplicativo de Edição/video-automator/credentials.json")
try:
    GKEYS = [c["api_key"] for c in json.load(open(_CREDS, encoding="utf-8"))
             if c.get("provedor") == "gemini" and c.get("api_key")]
    _OKEY = next((c["api_key"] for c in json.load(open(_CREDS, encoding="utf-8"))
                  if c.get("provedor") == "gpt" and c.get("api_key")), None)
except Exception:
    GKEYS, _OKEY = [], None
_ROT = [0]
_LUNA_MODEL = "gpt-5.6-luna"   # fallback qdo Gemini esgota (decisão Piter 19/07); vision OK (testado)


def _b64(p):
    return base64.b64encode(Path(p).read_bytes()).decode()


def _vision_luna(prompt, frames, timeout=90):
    """Fallback: GPT Luna (OpenAI chat completions, imagens em data-url). Texto ou None."""
    if not _OKEY:
        return None
    try:
        import httpx
        content = [{"type": "text", "text": prompt}] + [
            {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + _b64(f), "detail": "low"}}
            for f in frames]
        body = {"model": _LUNA_MODEL, "messages": [{"role": "user", "content": content}],
                "max_completion_tokens": 400}
        r = httpx.post("https://api.openai.com/v1/chat/completions",
                       headers={"Authorization": "Bearer " + _OKEY}, json=body, timeout=timeout)
        if r.status_code == 200:
            return r.json()["choices"][0]["message"]["content"]
    except Exception:
        pass
    return None


def _vision(prompt, frames, timeout=90):
    """Gemini generateContent com N imagens inline + rotação de chaves. Texto ou None."""
    parts = [{"text": prompt}] + [{"inline_data": {"mime_type": "image/jpeg", "data": _b64(f)}} for f in frames]
    body = json.dumps({"contents": [{"parts": parts}], "generationConfig": {"temperature": 0}}).encode()
    n = len(GKEYS) or 1
    for _ in range(n):
        k = GKEYS[_ROT[0] % n]; _ROT[0] += 1
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


def _parse(txt):
    if not txt:
        return {}
    t = txt.strip().replace("```json", "").replace("```", "")
    a, b = t.find("{"), t.rfind("}")
    if a >= 0 and b > a:
        try:
            return json.loads(t[a:b + 1])
        except Exception:
            return {}
    return {}


_PROMPT = (
    "You are a content gate for a FACELESS documentary YouTube channel. Beat subject: {subject}. "
    "You are shown {n} frame(s) sampled from ONE short b-roll clip; judge the CLIP as a whole. "
    "Return ONLY a JSON object with EXACT fields: "
    "subject_match (bool), child_present (bool), talking_head (bool), tv_interview (bool), "
    # 02/08: nudez foi AO AR (indígena com genitália visível em footage etnográfico).
    # Canal MONETIZADO: exposição = demonetização e possível strike, por mais
    # legítimo que seja o contexto documental. Sem isto o gate não tinha como ver.
    "nudity (bool: ANY exposed genitalia, buttocks or female breasts — including "
    "ethnographic, tribal, documentary or artistic footage; when in doubt, true), "
    "watermark_visible (bool), watermark_position (string or null), text_card (bool), reason (short string). "
    "subject_match=true if the frames show the subject OR closely-related supporting imagery that would "
    "naturally illustrate a documentary line about it (documentaries use adjacent b-roll); false ONLY if "
    "clearly unrelated/off-topic. Adjacent b-roll must stay in the subject's OBJECT DOMAIN: an architectural "
    "floor plan does NOT illustrate a 'shoe technical diagram', a random office does NOT illustrate a workshop. "
    "HOWEVER, subject_match=false if the clip is: a DIFFERENT vehicle brand's "
    "promo/ad/tutorial/price screen (e.g. the beat is about one truck brand but the clip advertises another), "
    "a movie/TV-show scene, meme/cartoon/AI-stylized content, or a screen-recording of software/editing UI. "
    "If the subject NAMES a specific BRAND or MODEL (e.g. 'Hoka Bondi', 'ASICS Gel-Nimbus'), subject_match=false "
    "when the visible product is clearly from a DIFFERENT brand/model (an Adidas shoe cannot illustrate a Hoka) — "
    "adjacent b-roll only applies to GENERIC subjects, never to named products. "
    "If the subject implies a specific SPORT/ACTIVITY (running, cycling), footage of a DIFFERENT sport "
    "(basketball, soccer, gym weights) = subject_match=false — even if athletic-looking. "
    "If the subject is about BICYCLES (pedal bikes): motorcycles, scooters and mopeds = subject_match=false "
    "(in English 'bike' searches return motorcycles — an engine, exhaust, speedometer dial or motorcycle "
    "showroom means it is NOT a bicycle). "
    "A news broadcast with an anchor/presenter and a name lower-third = tv_interview=true. "
    "If the subject says 'EXACT', be strict: the exact object/model must be visible. "
    "child_present=true if any child/minor appears. "
    "talking_head=true if a person FACES and ADDRESSES the camera as a presenter/vlogger (talking to the viewer); "
    "false if it is only the object, hands working, or a wide action shot with no one addressing the camera. "
    "tv_interview=true ONLY if it clearly looks like a broadcast/TV interview (studio, news lower-third). "
    "watermark_visible=true if a channel logo/watermark/branding overlay is visible; watermark_position "
    "= corner/edge/center or null. "
    "text_card=true if the frames are mostly a TEXT/TITLE CARD, channel intro screen, thumbnail-style graphic "
    "with big text, or a black/blank frame — i.e., NOT real footage. Also text_card=true if the footage has "
    "BURNED-IN subtitles/captions, on-screen tutorial UI (step labels, red X marks), or telemetry/HUD overlays."
)


def gate(subject, frames, niche_allows_children=False):
    """Retorna {ok, flags[], reason, raw}. ok=True só se relevante, sem criança e sem talking-head (salvo TV)."""
    prompt = _PROMPT.format(subject=subject, n=len(frames))
    # 31/07: ordem invertida enquanto o free tier do Gemini está em 429 — Luna primeiro
    # (com crédito), Gemini de fallback. Reverter quando a quota resetar.
    o = _parse(_vision_luna(prompt, frames))
    if not o:
        o = _parse(_vision(prompt, frames))
    if not o:
        return {"ok": False, "flags": ["sem-resposta-vision"], "reason": "gate indisponível → rejeita por segurança", "raw": {}}
    rel = bool(o.get("subject_match"))
    child = bool(o.get("child_present"))
    th = bool(o.get("talking_head")) and not bool(o.get("tv_interview"))
    wm = bool(o.get("watermark_visible"))
    wm_pos = o.get("watermark_position")
    flags = []
    if not rel:
        flags.append("off-topic")
    if child and not niche_allows_children:
        flags.append("CHILD")
    if th:
        flags.append("talking-head")
    # marca no CENTRO = descarta (regra §85); canto/borda = soft (cropável depois)
    if wm and str(wm_pos or "").lower() == "center":
        flags.append("watermark-center")
    if bool(o.get("text_card")):
        flags.append("text-card")
    if bool(o.get("nudity")):
        flags.append("NUDEZ")
    return {"ok": not flags, "flags": flags, "reason": o.get("reason", ""),
            "watermark": wm, "watermark_pos": wm_pos, "raw": o}


def _frames_de_video(video_path, tmp_dir, n=6):
    """Amostra n frames espalhados pela duração INTEIRA do vídeo (p/ passar ao gate).
    QA tenis 23/07: amostrar só os primeiros 4s aprovou clipe de review cujo YouTuber
    fala pra câmera aos 10s+ — o beat toca QUALQUER offset, o gate julga o clipe todo."""
    tmp_dir = Path(tmp_dir); tmp_dir.mkdir(parents=True, exist_ok=True)
    dur = 0.0
    try:
        p = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                            "-of", "csv=p=0", str(video_path)], capture_output=True, text=True, timeout=30)
        dur = float((p.stdout or "0").strip() or 0)
    except Exception:
        pass
    if dur <= 0:
        dur = 5.0  # fallback: comportamento antigo (primeiros segundos)
    outs = []
    for i in range(n):
        t = max(0.5, dur * (i + 0.5) / n)  # centros de n janelas iguais — cobre o fim também
        o = tmp_dir / f"{Path(video_path).stem}_g{i}.jpg"
        subprocess.run(["ffmpeg", "-y", "-ss", str(t), "-i", str(video_path), "-frames:v", "1",
                        "-vf", "scale=384:-2", "-loglevel", "error", str(o)], capture_output=True)
        if o.exists():
            outs.append(o)
    return outs
