"""Adensa o TEXTO no intro (<40s): gera frase punchy de impacto pra cada cena
do intro que ainda não tem overlay, via Gemini, sincronizada com a fala.
Não mexe nas cenas fora do intro. Preserva os matches bons.
"""
import json
import re
import subprocess
import urllib.request
from pathlib import Path

TESTE = Path(r"F:/Canal Dark/Aplicativo de Edição/banco-videos/teste")
TIMELINE = TESTE / "timeline.json"
WORDS = TESTE / "words.json"
CREDS = Path(r"F:/Canal Dark/Aplicativo de Edição/video-automator/credentials.json")
INTRO = 40.0
POS = ["center", "left", "right"]
ENTRADA = ["cascade", "slam", "pop", "cascade", "up"]


def norm(s):
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def calc_aparece(c, words, palavra):
    sw = [w for w in words if w["start"] >= c["inicio"] - 0.05 and w["start"] < c["fim"]]
    kw = norm(palavra)
    for w in sw:
        wn = norm(w["word"])
        if wn and (wn == kw or (len(wn) >= 4 and len(kw) >= 4 and (kw in wn or wn in kw))):
            return round(max(c["inicio"], w["start"] - 0.4), 2)
    return round(c["inicio"] + 0.2, 2)


def _parse_arr(txt):
    a, b = txt.find("["), txt.rfind("]")
    if a >= 0 and b > a:
        try:
            return json.loads(txt[a:b + 1])
        except Exception:
            return None
    return None


def _prompt(cenas_intro):
    # SEM aspas duplas (pra não quebrar no shell do Windows); 1 linha
    linhas = "  ".join(f"[{c['idx']}] {c['texto'].replace(chr(34), '')}" for c in cenas_intro)
    return (
        "This is the fast intro of a cosmic spiritual video. For each numbered narration line, create a "
        "SHORT punchy on-screen text of 2 to 4 words (energetic, a fragment or rephrase of the hook) and "
        "pick palavra_chave (the single most important word to highlight, must appear in your texto). "
        "Almost every line gets text. Return ONLY a JSON array where each item has keys idx, texto, "
        "palavra_chave. Lines: " + linhas
    )


def gemini_intro(cenas_intro):
    prompt = _prompt(cenas_intro)
    # 1) PRIMÁRIO: Gemini CLI (sem teto)
    try:
        p = subprocess.Popen(f'gemini -p "{prompt}"', shell=True, cwd=str(TESTE),
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                             encoding="utf-8", errors="replace")
        out, _ = p.communicate(timeout=150)
        arr = _parse_arr(out or "")
        if arr:
            print("  Gemini CLI OK")
            return {int(o["idx"]): (o.get("texto"), o.get("palavra_chave")) for o in arr}
    except subprocess.TimeoutExpired:
        subprocess.run(f"taskkill /F /T /PID {p.pid}", shell=True, capture_output=True)
    except Exception as e:
        print(f"  CLI falhou: {str(e)[:70]}")
    # 2) FALLBACK: API
    try:
        key = next(c["api_key"] for c in json.load(open(CREDS, encoding="utf-8"))
                   if c.get("provedor") == "gemini" and c.get("api_key"))
        body = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode()
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={key}"
        req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=90) as r:
            resp = json.loads(r.read())
        arr = _parse_arr(resp["candidates"][0]["content"]["parts"][0]["text"])
        if arr:
            print("  Gemini API OK (fallback)")
            return {int(o["idx"]): (o.get("texto"), o.get("palavra_chave")) for o in arr}
    except Exception as e:
        print(f"  API falhou: {str(e)[:70]}")
    return {}


tl = json.load(open(TIMELINE, encoding="utf-8"))
words = json.load(open(WORDS, encoding="utf-8"))

# cenas do intro SEM overlay (sem texto e sem infografico)
alvo = [c for c in tl["cenas"] if c["inicio"] < INTRO and not c.get("texto_impacto") and not c.get("infografico")]
print(f"intro: {len(alvo)} cenas sem texto -> gerando frases punchy")
gen = gemini_intro(alvo)

# index das cenas do intro que JÁ tinham texto (pra continuar o ciclo de pos/entrada)
ja = sum(1 for c in tl["cenas"] if c["inicio"] < INTRO and c.get("texto_impacto"))
k = ja
add = 0
by_idx = {c["idx"]: c for c in tl["cenas"]}
for idx, (texto, palavra) in gen.items():
    if not texto:
        continue
    c = by_idx.get(idx)
    if not c:
        continue
    c["texto_impacto"] = texto
    c["palavra_chave"] = palavra
    c["texto_pos"] = POS[k % len(POS)]
    c["entrada_texto"] = ENTRADA[k % len(ENTRADA)]
    c["aparece_em"] = calc_aparece(c, words, palavra)
    k += 1
    add += 1

json.dump(tl, open(TIMELINE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
intro_txt = sum(1 for c in tl["cenas"] if c["inicio"] < INTRO and c.get("texto_impacto"))
print(f"OK: +{add} textos no intro. Total intro com texto: {intro_txt}")
for c in tl["cenas"]:
    if c["inicio"] < INTRO and c.get("texto_impacto"):
        print(f"  {c['inicio']:>4.1f}s [{c.get('entrada_texto'):<7}] \"{c['texto_impacto']}\"")
