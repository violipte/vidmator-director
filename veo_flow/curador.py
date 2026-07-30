#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""curador.py — CURADOR de qualidade dos clipes VEO.

Pra cada clipe manda o VÍDEO inteiro pro Gemini (nativo, vê o MOVIMENTO — pega
flicker/morphing/física, não só frames) com um rubric de defeitos típicos de IA.
Pontua 0-100 + veredito keep/reject/revisar + defeitos + pior momento.
Separa em curadoria/keep|reject|revisar/ e escreve curadoria.json.

Híbrido: os "revisar" (borderline) podem virar contact sheet (--sheets) pro Claude
dar o corte fino lendo os frames.

Uso:
  python curador.py "veo_clips"                 # cura a pasta
  python curador.py "veo_clips" --keep 70 --workers 4 --sheets

Sem dependência pesada: stdlib + ffprobe + as 8 chaves Gemini (credentials.json).
Clipes < ~18MB (VEO 8s = ~3MB) vão inline; maiores ficam como 'revisar' (Files API é TODO).
"""
import argparse
import base64
import itertools
import json
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

CREDS = Path(r"F:/Canal Dark/Aplicativo de Edição/video-automator/credentials.json")
DECUPAR = Path(r"F:/Canal Dark/Aplicativo de Edição/decupar.py")
MODEL = "gemini-2.5-flash"
MAX_INLINE_MB = 18

# BLOCK_NONE: nichos dark/true-crime disparam falso-positivo no filtro e a resposta vem sem 'parts'.
_SAFETY = [{"category": c, "threshold": "BLOCK_NONE"} for c in (
    "HARM_CATEGORY_HARASSMENT", "HARM_CATEGORY_HATE_SPEECH",
    "HARM_CATEGORY_SEXUALLY_EXPLICIT", "HARM_CATEGORY_DANGEROUS_CONTENT")]


def _gkeys():
    try:
        return [c["api_key"] for c in json.load(open(CREDS, encoding="utf-8"))
                if c.get("provedor") == "gemini" and c.get("api_key")]
    except Exception:
        return []


_GKEYS = _gkeys()
_ROT = itertools.count()

# O CÉREBRO: rubric de QC. Estrito — esses clipes vão pra vídeo publicado.
RUBRIC = (
    "You are a STRICT quality-control reviewer for AI-generated video clips (Google VEO). "
    "Watch the WHOLE clip paying attention to MOTION over time, then decide if it is clean "
    "enough to publish in a professional video, or if it has AI artifacts a viewer would notice.\n"
    "Check for these defects (watch the motion, not just single frames):\n"
    "- morphing: faces/objects/hands warping, melting or drifting over time\n"
    "- anatomia: broken anatomy (extra/missing/merged fingers, wrong hands, extra limbs, bad teeth/eyes)\n"
    "- fisica: impossible physics (objects floating, wrong gravity, clipping through each other)\n"
    "- temporal: things popping in/out, flicker, jitter, sudden identity/clothes changes\n"
    "- texto: gibberish or illegible text on screen\n"
    "- face: distorted, unstable or uncanny faces\n"
    "- outro: any other obvious AI tell\n"
    "Return ONLY a JSON object, nothing else:\n"
    '{"score": <int 0-100, 100=flawless & publishable, 0=obviously broken>, '
    '"defeitos": [<tags of defects ACTUALLY present, from the list above; [] if none>], '
    '"pior_momento": "<approx timestamp of the worst artifact, e.g. 3s; or none>", '
    '"nota": "<one short sentence in Portuguese>"}\n'
    "Be STRICT: any obvious artifact => score below 55. A clean, natural, coherent clip => 80+."
)


def duracao(v):
    try:
        r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                            "-of", "default=nk=1:nw=1", str(v)], capture_output=True, text=True)
        return float(r.stdout.strip())
    except Exception:
        return 0.0


def _gemini_video(clip, prompt, timeout=240):
    """Manda o mp4 inline pro Gemini. Rotaciona as 8 chaves, retry em 429/503. Retorna texto ou None."""
    if not _GKEYS:
        return None
    data = base64.b64encode(clip.read_bytes()).decode()
    body = json.dumps({"contents": [{"parts": [
        {"inline_data": {"mime_type": "video/mp4", "data": data}},
        {"text": prompt}]}], "safetySettings": _SAFETY}).encode()
    n = len(_GKEYS)
    for _ in range(n):
        k = _GKEYS[next(_ROT) % n]
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={k}"
            req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read())["candidates"][0]["content"]["parts"][0]["text"]
        except urllib.error.HTTPError as e:
            if e.code in (429, 503):
                continue
            return None      # 400 (grande/ruim) etc.
        except Exception:
            continue
    return None


def _parse_obj(txt):
    a, b = txt.find("{"), txt.rfind("}")
    if a < 0 or b <= a:
        return None
    try:
        return json.loads(txt[a:b + 1])
    except Exception:
        return None


def avaliar(clip, keep_thr):
    dur = duracao(clip)
    mb = clip.stat().st_size / 1e6
    base = {"clip": clip.name, "dur": round(dur, 1), "mb": round(mb, 1)}
    if mb > MAX_INLINE_MB:
        return {**base, "veredito": "revisar", "erro": f"{mb:.0f}MB > inline (Files API = TODO)"}
    out = _gemini_video(clip, f"This clip is about {round(dur, 1)} seconds long.\n" + RUBRIC)
    if not out:
        return {**base, "veredito": "revisar", "erro": "gemini sem resposta"}
    o = _parse_obj(out)
    if not o or "score" not in o:
        return {**base, "veredito": "revisar", "erro": "json invalido", "raw": out[:160]}
    try:
        score = int(o.get("score", 0))
    except (TypeError, ValueError):
        score = 0
    # veredito NOSSO por threshold: keep / revisar (borderline) / reject
    v = "keep" if score >= keep_thr else ("revisar" if score >= keep_thr - 15 else "reject")
    return {**base, "score": score, "veredito": v,
            "defeitos": o.get("defeitos", []), "pior_momento": o.get("pior_momento", ""),
            "nota": o.get("nota", "")}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pasta")
    ap.add_argument("--keep", type=int, default=70, help="score minimo p/ keep")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--sheets", action="store_true", help="gera contact sheet dos 'revisar' p/ o Claude olhar")
    a = ap.parse_args()

    pasta = Path(a.pasta)
    clips = sorted(p for p in pasta.glob("*.mp4"))
    if not clips:
        print(f"nenhum .mp4 em {pasta}")
        return
    if not _GKEYS:
        print("ERRO: nenhuma chave Gemini em credentials.json")
        return
    print(f"=== curador: {len(clips)} clipes | keep>={a.keep} | {len(_GKEYS)} chaves | {MODEL} ===")

    out_dir = pasta / "curadoria"
    for sub in ("keep", "reject", "revisar"):
        (out_dir / sub).mkdir(parents=True, exist_ok=True)

    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        res = list(ex.map(lambda c: avaliar(c, a.keep), clips))

    for r in sorted(res, key=lambda x: x.get("score", -1), reverse=True):
        v = r.get("veredito", "revisar")
        try:
            shutil.copy2(pasta / r["clip"], out_dir / v / r["clip"])
        except Exception:
            pass
        tag = {"keep": "OK ", "reject": "NAO", "revisar": "?? "}.get(v, "?")
        det = ", ".join(r.get("defeitos", [])) or r.get("erro", "") or r.get("nota", "")
        print(f"  {tag} {str(r.get('score','-')):>3} | {r['clip']:<30} | {det[:70]}")

    (out_dir / "curadoria.json").write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
    keep = [r for r in res if r.get("veredito") == "keep"]
    rev = [r for r in res if r.get("veredito") == "revisar"]
    print(f"\nOK -> keep {len(keep)} | revisar {len(rev)} | reject {len(res)-len(keep)-len(rev)}")
    print(f"relatório: {out_dir}\\curadoria.json  |  aprovados em: {out_dir}\\keep\\")

    if a.sheets and rev:
        print(f"\ngerando contact sheets dos {len(rev)} 'revisar' (pro Claude ler)...")
        for r in rev:
            subprocess.run(["python", str(DECUPAR), str(pasta / r["clip"]),
                            "--modo", "fixo", "--intervalo", "0.5"], capture_output=True)


if __name__ == "__main__":
    main()
