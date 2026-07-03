"""Pass ADITIVO: detecta PESSOAS históricas/públicas citadas no roteiro, busca o
retrato em domínio público (Wikipedia REST), recorta o fundo (rembg) e insere um
card de pessoa (retrato + nome) no momento da fala. Escreve o array 'pessoas' no
timeline.json. Padrão dos outros passes (detectar_mapas / ilustrar).

IMPORTANTE: rodar com `python` (Python 3.14 — tem rembg), NÃO `python3` (3.13).
"""
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
WORDS = TESTE / "words.json"
TIMELINE = TESTE / "timeline.json"
PESSOAS_DIR = TESTE / "pessoas"
CREDS = Path(r"F:/Canal Dark/Aplicativo de Edição/video-automator/credentials.json")
UA = {"User-Agent": "CanalDark/1.0 (research; github.com/violipte)"}

DUR_PESSOA = 3.6      # duração do card de pessoa (s)
FUNDO = "escuro"      # "escuro" (nicho dark) ou "claro"

# rembg precisa do backend onnxruntime. Se ausente (ex.: py3.14 sem wheel), NÃO tocar no rembg
# (a chamada falha de forma fatal e derruba o pass) -> usar retrato sem recorte. Checa UMA vez.
try:
    import onnxruntime as _ort  # noqa: F401
    _REMBG_OK = True
except Exception:
    _REMBG_OK = False


def norm(s):
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def _parse_arr(txt):
    a, b = txt.find("["), txt.rfind("]")
    if a >= 0 and b > a:
        try:
            return json.loads(txt[a:b + 1])
        except Exception:
            return None
    return None


def _prompt(roteiro):
    return (
        "Read this narration script. List every REAL, NAMED historical or public PERSON explicitly mentioned "
        "(skip generic groups like scientists or people). For EACH return: nome (display name), subtitulo (a "
        "SHORT label with role and life years if known, e.g. Naturalist 1809-1882). CRITICAL: write subtitulo in "
        "the SAME LANGUAGE as the narration script below — if the script is in English, subtitulo MUST be in "
        "English; if Portuguese, in Portuguese. Also return wiki (the "
        "exact English Wikipedia page title for this person), and trecho (the exact 3 to 6 consecutive words "
        "FROM THE SCRIPT where the person is first named, verbatim). Return ONLY a JSON array of objects with "
        "keys nome, subtitulo, wiki, trecho. If nobody is named, return []. Script: "
        + roteiro.replace(chr(34), "").replace("\n", " ")
    )


def detectar(roteiro):
    from gemini_api import gemini_arr
    arr = gemini_arr(_prompt(roteiro), 180)   # API (8 chaves) + retry se JSON vier corrompido -> CLI fallback
    return arr if arr is not None else []


def localizar(trecho, words):
    alvo = [norm(t) for t in (trecho or "").split() if norm(t)]
    if not alvo or not words:
        return None
    wn = [norm(w["word"]) for w in words]
    n = len(alvo)
    for i in range(len(wn) - n + 1):
        if wn[i:i + n] == alvo:
            return round(words[i]["start"], 2)
    fortes = [t for t in alvo if len(t) >= 4]
    for i, w in enumerate(wn):
        if fortes and w == fortes[0]:
            return round(words[i]["start"], 2)
    return None


def retrato(wiki, idx):
    """Busca retrato PD na Wikipedia, recorta fundo (rembg), salva PNG. Retorna path ou None."""
    PESSOAS_DIR.mkdir(parents=True, exist_ok=True)
    try:
        sm_url = "https://en.wikipedia.org/api/rest_v1/page/summary/" + urllib.parse.quote((wiki or "").replace(" ", "_"))
        d = json.loads(urllib.request.urlopen(urllib.request.Request(sm_url, headers=UA), timeout=30).read())
        img = (d.get("originalimage") or {}).get("source") or (d.get("thumbnail") or {}).get("source")
        if not img:
            return None
        raw = urllib.request.urlopen(urllib.request.Request(img, headers=UA), timeout=60).read()
    except Exception as e:
        print(f"    retrato falhou ({wiki}): {str(e)[:50]}")
        return None
    dest = PESSOAS_DIR / f"pessoa_{idx}.png"
    try:
        import io
        from PIL import Image
        im = Image.open(io.BytesIO(raw)).convert("RGB")
        if im.height > 1600:  # reduz antes do cutout (mais rápido, sobra p/ 1080p)
            im = im.resize((round(im.width * 1600 / im.height), 1600))
        if _REMBG_OK:
            try:
                from rembg import remove
                remove(im).save(dest)   # RGBA transparente (fundo recortado)
                return str(dest).replace("\\", "/")
            except Exception as e:
                print(f"    rembg falhou ({str(e)[:40]}); usando retrato sem recorte")
        im.save(dest)   # sem recorte (retrato retangular — ok p/ card, vira foto emoldurada)
        return str(dest).replace("\\", "/")
    except Exception as e:
        print(f"    processamento falhou: {str(e)[:50]}")
        return None


def in_window(c_ini, segs, dur):
    for s in segs:
        if c_ini < s["inicio"] + dur and c_ini > s["inicio"] - dur:
            return True
    return False


def main():
    # modo teste: detecta num .txt, imprime e baixa o 1º retrato p/ validar
    if len(sys.argv) > 1:
        txt = Path(sys.argv[1]).read_text(encoding="utf-8")
        print(f"=== Detecção (teste) em {sys.argv[1]} ===")
        det = detectar(txt)
        print(json.dumps(det, ensure_ascii=False, indent=2))
        if det:
            img = retrato(det[0].get("wiki") or det[0]["nome"], 0)
            print(f"\n1º retrato ({det[0]['nome']}): {img}")
        return

    roteiro = ROTEIRO.read_text(encoding="utf-8")
    words = json.load(open(WORDS, encoding="utf-8")) if WORDS.exists() else []
    tl = json.load(open(TIMELINE, encoding="utf-8"))

    print("=== Detector de pessoas ===")
    pessoas_det = detectar(roteiro)
    print(f"  {len(pessoas_det)} pessoa(s) detectada(s)\n")

    pessoas = []
    vistos = set()
    for i, e in enumerate(pessoas_det):
        nome = e.get("nome")
        if not nome or norm(nome) in vistos:
            continue
        ini = localizar(e.get("trecho"), words)
        if ini is None:
            print(f"  [skip] {nome} — trecho não localizado")
            continue
        img = retrato(e.get("wiki") or nome, len(pessoas))
        if not img:
            print(f"  [skip] {nome} — sem retrato")
            continue
        vistos.add(norm(nome))
        pessoas.append({
            "inicio": ini, "dur": DUR_PESSOA, "nome": nome,
            "subtitulo": e.get("subtitulo"), "imagem_path": img, "fundo": FUNDO,
        })
        print(f"  {ini:>6.1f}s  {nome}  ({e.get('subtitulo')})")

    pessoas.sort(key=lambda m: m["inicio"])
    limpos = []
    for p in pessoas:
        if limpos and p["inicio"] - limpos[-1]["inicio"] < DUR_PESSOA:
            continue
        limpos.append(p)

    tl["pessoas"] = limpos
    json.dump(tl, open(TIMELINE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"\nOK -> {len(limpos)} cards de pessoa no timeline.json")


if __name__ == "__main__":
    main()
