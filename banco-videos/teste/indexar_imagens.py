"""Indexa um BANCO DE IMAGENS LOCAL por Vision (Gemini) p/ o modo HÍBRIDO do VidMator.
Cada imagem -> {keep, desc, tags[], mood, tipo}. Resumável, rotação de chaves, save incremental.
O resolver (modo hibrido) lê o índice e escolhe por beat a imagem local mais relevante vs stock.

Uso: python indexar_imagens.py "<pasta_raiz>" [saida_index.json] [--limit N] [--nicho ttm]
"""
import base64
import glob
import itertools
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
CREDS = Path(r"F:/Canal Dark/Aplicativo de Edição/video-automator/credentials.json")
GKEYS = [c["api_key"] for c in json.load(open(CREDS, encoding="utf-8"))
         if c.get("provedor") == "gemini" and c.get("api_key")]
_ROT = itertools.count()
PROVIDER = os.environ.get("VISION_PROVIDER", "gemini").lower()   # "gemini" (free, 20rpm) | "gpt" (pago, rápido)
MODEL = os.environ.get("VISION_MODEL", "gemini-2.5-flash-lite")  # lite = limites free maiores + rápido (tagging simples)
GPT_MODEL = os.environ.get("VISION_GPT_MODEL", "gpt-4o-mini")    # vision barato; detail:low ~$0.0005/img
GPT_KEY = next((c["api_key"] for c in json.load(open(CREDS, encoding="utf-8"))
                if c.get("provedor") == "gpt" and c.get("api_key")), "")
SAFETY = [{"category": c, "threshold": "BLOCK_NONE"} for c in
          ("HARM_CATEGORY_HARASSMENT", "HARM_CATEGORY_HATE_SPEECH",
           "HARM_CATEGORY_SEXUALLY_EXPLICIT", "HARM_CATEGORY_DANGEROUS_CONTENT")]

# taxonomia por nicho (a instrução de tags muda; keep/desc/mood/tipo são comuns)
NICHO_HINT = {
    "ttm": ("a somatic + spiritual health channel (body, nervous system, trauma release, ancient wisdom, movement). "
            "tags examples: anatomy parts (psoas, spine, hips, shoulders, fascia, vagus-nerve), actions "
            "(meditation, stretching, breathing, plank, walking), themes (nervous-system, energy, trauma, chakra, "
            "ancient-ritual, nature, light, water)."),
    "default": ("a faceless spiritual/health channel. tags = 3-8 concept keywords useful to match narration."),
}


def _api_vision(prompt, img_path, mime):
    b64 = base64.b64encode(Path(img_path).read_bytes()).decode()
    body = json.dumps({"contents": [{"parts": [{"text": prompt}, {"inline_data": {"mime_type": mime, "data": b64}}]}],
                       "safetySettings": SAFETY,
                       # thinkingBudget:0 desliga o "thinking" do 2.5-flash (senão come os tokens -> MAX_TOKENS/JSON truncado)
                       "generationConfig": {"temperature": 0.2, "maxOutputTokens": 500,
                                            "thinkingConfig": {"thinkingBudget": 0}}}).encode()
    last = None
    for _ in range(max(1, len(GKEYS))):
        k = GKEYS[next(_ROT) % len(GKEYS)]
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={k}"
            r = urllib.request.urlopen(urllib.request.Request(
                url, data=body, headers={"Content-Type": "application/json"}, method="POST"), timeout=60)
            return json.loads(r.read())["candidates"][0]["content"]["parts"][0]["text"]
        except urllib.error.HTTPError as e:
            last = e.code
            if e.code in (429, 503):
                time.sleep(1.5); continue
            return None
        except Exception:
            continue
    return None


def _api_vision_gpt(prompt, img_path, mime):
    b64 = base64.b64encode(Path(img_path).read_bytes()).decode()
    body = json.dumps({"model": GPT_MODEL, "max_completion_tokens": 300,
                       "messages": [{"role": "user", "content": [
                           {"type": "text", "text": prompt},
                           {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}", "detail": "low"}}]}]}).encode()
    for _ in range(3):
        try:
            r = urllib.request.urlopen(urllib.request.Request(
                "https://api.openai.com/v1/chat/completions", data=body,
                headers={"Content-Type": "application/json", "Authorization": f"Bearer {GPT_KEY}"}, method="POST"), timeout=60)
            return json.loads(r.read())["choices"][0]["message"]["content"]
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(3); continue
            return None
        except Exception:
            time.sleep(1); continue
    return None


def _vision(prompt, img_path, mime):
    return _api_vision_gpt(prompt, img_path, mime) if PROVIDER == "gpt" else _api_vision(prompt, img_path, mime)


def tag_imagem(img_path, nicho):
    mime = "image/png" if str(img_path).lower().endswith(".png") else "image/jpeg"
    hint = NICHO_HINT.get(nicho, NICHO_HINT["default"])
    p = ("This is ONE image from " + hint + " Return ONLY a JSON object {keep, desc, tags, mood, tipo}. "
         "keep=true if it is a CLEAN, usable, visually coherent illustration/photo; keep=false if it has heavy "
         "garbled/unreadable text overlays, watermarks, deformed/broken anatomy, cluttered diagram markings, or is "
         "washed-out/corrupt. desc=4-8 word scene description. tags=array of 3-8 lowercase concept keywords to match "
         "narration. mood=one of calm/mystical/scientific/intense/dark/uplifting. tipo=one of "
         "anatomy/figure-pose/meditation/nature/abstract-energy/object/scene.")
    out = _vision(p, img_path, mime)
    if not out:
        return None
    a, b = out.find("{"), out.rfind("}")
    if a < 0 or b <= a:
        return None
    try:
        o = json.loads(out[a:b + 1])
        return {"keep": bool(o.get("keep", True)),
                "desc": str(o.get("desc", ""))[:80],
                "tags": [str(t).lower().strip()[:24] for t in (o.get("tags") or [])][:8],
                "mood": str(o.get("mood", ""))[:16],
                "tipo": str(o.get("tipo", ""))[:16]}
    except Exception:
        return None


def listar(raizes):
    out = []
    for raiz in raizes:
        for ext in ("*.jpg", "*.jpeg", "*.png", "*.webp"):
            out += glob.glob(os.path.join(raiz, "**", ext), recursive=True)
    return sorted(set(p.replace("\\", "/") for p in out))


def main():
    # aceita N pastas raiz + flags. Índice ÚNICO keyed por PATH ABSOLUTO (multi-pasta; re-root no move).
    args = sys.argv[1:]
    nicho, limit, saida, roots = "ttm", None, None, []
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--nicho" and i + 1 < len(args): nicho = args[i + 1]; i += 2
        elif a == "--limit" and i + 1 < len(args): limit = int(args[i + 1]); i += 2
        elif a == "--out" and i + 1 < len(args): saida = Path(args[i + 1]); i += 2
        elif a == "--roots-file" and i + 1 < len(args):   # JSON com lista de pastas extras (levas futuras / dedup)
            roots += [str(x).rstrip("/\\") for x in json.load(open(args[i + 1], encoding="utf-8"))]; i += 2
        else: roots.append(a.rstrip("/\\")); i += 1
    if not roots:
        print('uso: python indexar_imagens.py [--out idx.json] [--nicho ttm] [--limit N] <pasta1> [pasta2] ...'); return
    if saida is None:
        saida = Path(r"F:/Canal Dark/Aplicativo de Edição/banco-videos/teste") / f"index_{nicho}_imagens.json"

    idx = {"itens": {}}   # {abs_path_fwdslash: {keep,desc,tags,mood,tipo}}
    if saida.exists():
        try:
            idx = json.load(open(saida, encoding="utf-8")); idx.setdefault("itens", {})
        except Exception:
            pass
    feitos = {k for k, v in idx["itens"].items() if not v.get("_err")}  # _err (429 transiente) re-tenta no re-run

    imgs = listar(roots)
    todo = [p for p in imgs if p not in feitos]
    if limit:
        todo = todo[:limit]
    print(f"=== Indexar [{nicho}]: {len(imgs)} imgs em {len(roots)} pastas | {len(feitos)} feitas | {len(todo)} a processar ===")
    if not GKEYS:
        print("!!! sem chaves gemini em credentials.json"); return

    kept = rej = err = 0
    t0 = time.time()
    for i, p in enumerate(todo):
        r = tag_imagem(p, nicho)
        if r is None:
            err += 1
            idx["itens"][p] = {"keep": True, "desc": "", "tags": [], "mood": "", "tipo": "", "_err": True}
        else:
            idx["itens"][p] = r
            kept += int(r["keep"]); rej += int(not r["keep"])
        if (i + 1) % 25 == 0 or (i + 1) == len(todo):
            json.dump(idx, open(saida, "w", encoding="utf-8"), ensure_ascii=False)
            rate = (i + 1) / max(1, time.time() - t0)
            print(f"  {i+1}/{len(todo)} | keep {kept} rej {rej} err {err} | {rate:.1f} img/s | idx: {len(idx['itens'])}")
    json.dump(idx, open(saida, "w", encoding="utf-8"), ensure_ascii=False)
    print(f"=== FIM: {len(idx['itens'])} indexadas -> {saida} (keep {kept} / rej {rej} / err {err}) ===")


if __name__ == "__main__":
    main()
