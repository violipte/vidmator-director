"""Pass ADITIVO: o Gemini acha momentos do roteiro que pedem uma IMAGEM real de
domínio público (recorte de jornal, foto de imprensa, registro) — coisas que vídeo
stock não tem. Busca no Wikimedia Commons (PD-preferido), baixa, e grava o array
'imagens' no timeline.json com um ESTILO de entrada (photo/split/clipping).
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
IMG_DIR = TESTE / "imagens"
CREDS = Path(r"F:/Canal Dark/Aplicativo de Edição/video-automator/credentials.json")
UA = {"User-Agent": "CanalDark/1.0 (research; pitermoreiraviolim@gmail.com)"}
DUR_IMG = 4.0


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
        "Read this documentary narration. Find the moments where a REAL public-domain IMAGE would add credibility "
        "and show something VIDEO cannot (a newspaper clipping, a press photo, a historical record, an object, a "
        "document, an old map of a place). Pick 3 to 6 of the strongest moments, spaced out. For EACH return: "
        "trecho (the exact 3 to 6 consecutive words FROM THE SCRIPT where it fits, verbatim), busca (a Wikimedia "
        "Commons search query in English to find the image), estilo (one of: photo, split, clipping; use clipping "
        "for newspaper/press, split when comparing two things, photo otherwise), busca2 (only if estilo is split: "
        "a second Commons query), and legenda (a SHORT caption IN THE SAME LANGUAGE as the script). "
        "Return ONLY a JSON array of objects with those keys. Script: "
        + roteiro.replace(chr(34), "").replace("\n", " ")
    )


def detectar(roteiro):
    from gemini_api import gemini_arr
    arr = gemini_arr(_prompt(roteiro), 180)   # API (8 chaves) + retry/repair se JSON corrompido -> CLI fallback
    return arr if arr is not None else []


def localizar(trecho, words):
    alvo = [norm(t) for t in (trecho or "").split() if norm(t)]
    if not alvo or not words:
        return None
    wn = [norm(w["word"]) for w in words]
    for i in range(len(wn) - len(alvo) + 1):
        if wn[i:i + len(alvo)] == alvo:
            return round(words[i]["start"], 2)
    fortes = [t for t in alvo if len(t) >= 4]
    for i, w in enumerate(wn):
        if fortes and w == fortes[0]:
            return round(words[i]["start"], 2)
    return None


def commons_baixar(query, dest):
    """Busca no Commons (prefere domínio público), baixa o melhor. Retorna True/False."""
    try:
        url = ("https://commons.wikimedia.org/w/api.php?action=query&format=json&generator=search"
               f"&gsrnamespace=6&gsrsearch={urllib.parse.quote(query)}&gsrlimit=8"
               "&prop=imageinfo&iiprop=url|extmetadata&iiurlwidth=1280")
        d = json.loads(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30).read())
        pages = list(((d.get("query") or {}).get("pages", {}) or {}).values())
        cand = []
        for p in pages:
            ii = (p.get("imageinfo") or [{}])[0]
            u = ii.get("thumburl") or ii.get("url")
            if not u or not re.search(r"\.(jpg|jpeg|png)$", u, re.I):
                continue
            lic = ((ii.get("extmetadata") or {}).get("LicenseShortName") or {}).get("value", "")
            pd = "public domain" in lic.lower() or "cc0" in lic.lower()
            cand.append((0 if pd else 1, u))
        cand.sort(key=lambda x: x[0])
        if not cand:
            return False
        data = urllib.request.urlopen(urllib.request.Request(cand[0][1], headers=UA), timeout=60).read()
        dest.write_bytes(data)
        return dest.stat().st_size > 8000
    except Exception as e:
        print(f"    commons falhou ({query}): {str(e)[:50]}")
        return False


def in_window(ini, segs, dur):
    return any(s["inicio"] - dur < ini < s["inicio"] + s.get("dur", dur) for s in segs)


def main():
    IMG_DIR.mkdir(parents=True, exist_ok=True)
    roteiro = ROTEIRO.read_text(encoding="utf-8")
    words = json.load(open(WORDS, encoding="utf-8")) if WORDS.exists() else []
    tl = json.load(open(TIMELINE, encoding="utf-8"))
    mapas, pessoas, datas = tl.get("mapas") or [], tl.get("pessoas") or [], tl.get("datas") or []

    print("=== Imagens PD do caso ===")
    eventos = detectar(roteiro)
    print(f"  {len(eventos)} momentos sugeridos\n")

    imagens = []
    for i, e in enumerate(eventos):
        ini = localizar(e.get("trecho"), words)
        if ini is None:
            continue
        if in_window(ini, mapas, 5.5) or in_window(ini, pessoas, 3.6) or in_window(ini, datas, 2.6):
            continue  # não empilha com mapa/pessoa/data
        estilo = e.get("estilo") if e.get("estilo") in ("photo", "split", "clipping") else "photo"
        rels = []
        d1 = IMG_DIR / f"img_{i}_0.jpg"
        if commons_baixar(e.get("busca", ""), d1):
            rels.append(str(d1).replace("\\", "/"))
        if estilo == "split":
            d2 = IMG_DIR / f"img_{i}_1.jpg"
            if e.get("busca2") and commons_baixar(e.get("busca2"), d2):
                rels.append(str(d2).replace("\\", "/"))
            if len(rels) < 2:
                estilo = "photo"  # sem 2ª imagem -> vira photo
        if not rels:
            print(f"  [skip] '{e.get('busca')}' — sem imagem")
            continue
        imagens.append({"inicio": ini, "dur": DUR_IMG, "estilo": estilo,
                        "imagens_path": rels, "legenda": e.get("legenda")})
        print(f"  {ini:>6.1f}s  [{estilo:<8}] {e.get('legenda')}  ({len(rels)} img)")

    imagens.sort(key=lambda m: m["inicio"])
    limpos = []
    for m in imagens:
        if limpos and m["inicio"] - limpos[-1]["inicio"] < DUR_IMG:
            continue
        limpos.append(m)
    tl["imagens"] = limpos
    json.dump(tl, open(TIMELINE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"\nOK -> {len(limpos)} imagens no timeline.json")


if __name__ == "__main__":
    main()
