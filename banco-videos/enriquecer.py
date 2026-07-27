"""Enriquecimento de vision — CLI PRIMÁRIO ($0, sem teto de rate), API como fallback.

Cadeia: Gemini CLI (OAuth) -> Gemini API key -> Claude CLI (Max).

Uso:
  from enriquecer import descrever ; descrever(jpg_path) -> (dict|None, via)
  python enriquecer.py backfill    # re-enriquece os enriquecido=false do catálogo
"""
import base64
import json
import os
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

CREDS = Path(r"F:/Canal Dark/Aplicativo de Edição/video-automator/credentials.json")
BANCO = Path(r"D:/Meu Drive/canal_dark_footage_stock")
CATALOGO = BANCO / "catalogo.json"
TMP = Path(r"F:/Canal Dark/Aplicativo de Edição/banco-videos/_tmp_keyframes")

PROMPT = ("Describe this video frame for a B-roll stock catalog. Reply ONLY as a JSON object with keys: "
          "descricao_visual (short English phrase of what is shown), mood (1-2 words), "
          "movimento (one of estatico lento medio rapido), tags (array of 3-6 keywords). "
          "No markdown, no extra text.")


def _parse(txt):
    a, b = txt.find("{"), txt.rfind("}")
    if a >= 0 and b > a:
        try:
            return json.loads(txt[a:b + 1])
        except Exception:
            return None
    return None


def _run_cli(cmd, cwd, timeout):
    """Roda CLI e, se pendurar, MATA A ÁRVORE (taskkill /T) — senão o node-neto
    fica preso no Windows e trava tudo. Retorna stdout (str) ou '' no timeout."""
    p = subprocess.Popen(cmd, shell=True, cwd=cwd, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace")
    try:
        out, _ = p.communicate(timeout=timeout)
        return out or ""
    except subprocess.TimeoutExpired:
        try:
            subprocess.run(f"taskkill /F /T /PID {p.pid}", shell=True, capture_output=True, timeout=15)
        except Exception:
            pass
        try:
            p.kill()
        except Exception:
            pass
        return ""


# === 1. PRIMÁRIO: Gemini CLI (OAuth conta Google, sem teto de API key) ===
def via_gemini_cli(jpg: Path):
    cmd = f'gemini -p "{PROMPT} @{jpg.name}"'
    return _parse(_run_cli(cmd, str(jpg.parent), 90))


# === 2. FALLBACK: Gemini API key (rápido, mas free tier estrangula) ===
_gk = {"i": 0}
def via_gemini_api(jpg: Path):
    import urllib.request
    import urllib.error
    keys = [c["api_key"] for c in json.load(open(CREDS, encoding="utf-8"))
            if c.get("provedor") == "gemini" and c.get("api_key")]
    if not keys:
        return None
    b64 = base64.b64encode(jpg.read_bytes()).decode()
    body = json.dumps({"contents": [{"parts": [
        {"text": PROMPT}, {"inline_data": {"mime_type": "image/jpeg", "data": b64}}]}]}).encode()
    for _ in range(len(keys)):
        key = keys[_gk["i"] % len(keys)]; _gk["i"] += 1
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={key}"
        try:
            req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
            with urllib.request.urlopen(req, timeout=60) as r:
                resp = json.loads(r.read())
            return _parse(resp["candidates"][0]["content"]["parts"][0]["text"])
        except urllib.error.HTTPError as e:
            if e.code in (429, 503):
                continue
            return None
        except Exception:
            return None
    return None


# === 3. ÚLTIMO RECURSO: Claude CLI (Max plan, vision via leitura) ===
def via_claude_cli(jpg: Path):
    cmd = f'claude -p "Read the image file {jpg.name} in this folder and {PROMPT}"'
    # nota: env limpo seria ideal, mas _run_cli usa shell; o claude -p funciona standalone aqui
    return _parse(_run_cli(cmd, str(jpg.parent), 150))


def descrever(jpg: Path):
    """CLI primário, API fallback. Retorna (dict|None, nome_da_via)."""
    for fn in (via_gemini_cli, via_gemini_api, via_claude_cli):
        r = fn(jpg)
        if r and r.get("descricao_visual"):
            return r, fn.__name__
    return None, None


def backfill():
    """Re-enriquece os clips com enriquecido=false usando a cadeia CLI-primário."""
    cat = json.load(open(CATALOGO, encoding="utf-8"))
    TMP.mkdir(parents=True, exist_ok=True)
    faltam = [c for c in cat if not c.get("enriquecido")]
    print(f"=== Backfill: {len(faltam)} clips sem enriquecimento ===")
    for i, c in enumerate(faltam):
        mp4 = Path(c["arquivo"])
        if not mp4.exists():
            print(f"  {c['id']} arquivo sumiu, skip"); continue
        kf = TMP / f"{c['id']}.jpg"
        ss = max(0.5, c.get("duracao", 5) * 0.35)
        subprocess.run(["ffmpeg", "-y", "-ss", str(ss), "-i", str(mp4), "-frames:v", "1",
                        "-vf", "scale=640:-1", str(kf)], capture_output=True)
        if not kf.exists():
            print(f"  {c['id']} keyframe falhou, skip"); continue
        r, via = descrever(kf)
        kf.unlink(missing_ok=True)
        if r:
            c["descricao_visual"] = r.get("descricao_visual", c["descricao_visual"])
            c["mood"] = r.get("mood", "")
            c["movimento"] = r.get("movimento", "")
            c["tags"] = r.get("tags", [])
            c["enriquecido"] = True
            print(f"  [{i+1}/{len(faltam)}] {c['id']} OK ({via}) {c['descricao_visual'][:45]}")
        else:
            print(f"  [{i+1}/{len(faltam)}] {c['id']} FALHOU todas as vias")
        if (i + 1) % 10 == 0:
            json.dump(cat, open(CATALOGO, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    json.dump(cat, open(CATALOGO, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    enr = sum(1 for x in cat if x.get("enriquecido"))
    print(f"=== DONE: {enr}/{len(cat)} enriquecidos ===")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "backfill":
        backfill()
    else:
        print("uso: python enriquecer.py backfill")
