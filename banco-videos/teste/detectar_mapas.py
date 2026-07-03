"""Detector de MAPAS: lê roteiro + words.json, usa Gemini (CLI primário, API
fallback) pra achar lugares/eventos geográficos citados. Pra cada um: país (nome
do atlas EN), coord [lng,lat], legenda curta e busca de imagem. Localiza o
timestamp da fala (via trecho-gatilho) e baixa a imagem do Pexels. Escreve o
array 'mapas' no timeline.json (sem mexer no resto).

Uso:
  python detectar_mapas.py            # roda no roteiro/words/timeline reais
  python detectar_mapas.py <arquivo>  # só testa a detecção num .txt (imprime JSON)
"""
import json
import re
import subprocess
import sys
import urllib.request
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

TESTE = Path(r"F:/Canal Dark/Aplicativo de Edição/banco-videos/teste")
ROTEIRO = TESTE / "roteiro_en.txt"
WORDS = TESTE / "words.json"
TIMELINE = TESTE / "timeline.json"
MAPAS_DIR = TESTE / "mapas"
CREDS = Path(r"F:/Canal Dark/Aplicativo de Edição/video-automator/credentials.json")
PEXELS_CFG = Path(r"F:/Canal Dark/Aplicativo de Edição/video-automator/config.json")

DUR_MAPA = 5.5  # duração padrão de um segmento de mapa (s)


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
    # SEM aspas duplas (shell-safe no Windows)
    return (
        "Read this narration script. Identify every concrete GEOGRAPHIC place or event tied to a place "
        "(a country, a famous city, a historical event with a location, a landmark). For EACH, return: "
        "pais (the MODERN country English name as in Natural Earth maps, e.g. Egypt, Greece, Italy, Turkey, "
        "China, France, Peru; map ancient places to their modern country - Rome to Italy, Athens to Greece, "
        "Babylon to Iraq), lng and lat (decimal degrees of the key city/landmark), legenda (a 2 to 4 word "
        "on-screen label), busca_imagem (2 to 4 word English query to find a representative photo), and "
        "trecho (the exact 3 to 6 consecutive words FROM THE SCRIPT where this place is first mentioned, "
        "verbatim), and tipo: use satelite for a SPECIFIC pinpoint modern location that exists today and looks "
        "striking from directly above (one city, a landmark, a building, an island, a mountain, a specific site "
        "like the pyramids or a stadium); use estilizado for countries, regions, broad geopolitics, movement "
        "across territory, or ancient/abstract places (e.g. the Roman Empire, Europe). When unsure use estilizado. "
        "Skip vague/metaphorical mentions. If no real place is mentioned, return []. "
        "Return ONLY a JSON array of objects with keys pais, lng, lat, legenda, busca_imagem, trecho, tipo. "
        "Script: " + roteiro.replace(chr(34), "").replace("\n", " ")
    )


def detectar(roteiro):
    prompt = _prompt(roteiro)
    # 1) PRIMÁRIO: Gemini CLI (sem teto)
    try:
        p = subprocess.Popen(f'gemini -p "{prompt}"', shell=True, cwd=str(TESTE),
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                             encoding="utf-8", errors="replace")
        out, _ = p.communicate(timeout=180)
        arr = _parse_arr(out or "")
        if arr is not None:
            print("  Gemini CLI OK")
            return arr
    except subprocess.TimeoutExpired:
        subprocess.run(f"taskkill /F /T /PID {p.pid}", shell=True, capture_output=True)
        print("  CLI timeout -> API")
    except Exception as e:
        print(f"  CLI falhou: {str(e)[:70]} -> API")
    # 2) FALLBACK: API
    try:
        key = next(c["api_key"] for c in json.load(open(CREDS, encoding="utf-8"))
                   if c.get("provedor") == "gemini" and c.get("api_key"))
        body = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode()
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={key}"
        req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=120) as r:
            resp = json.loads(r.read())
        arr = _parse_arr(resp["candidates"][0]["content"]["parts"][0]["text"])
        if arr is not None:
            print("  Gemini API OK (fallback)")
            return arr
    except Exception as e:
        print(f"  API falhou: {str(e)[:70]}")
    return []


def localizar(trecho, words):
    """Acha o start (s) do trecho na sequência de palavras (match por janela normalizada)."""
    alvo = [norm(t) for t in (trecho or "").split() if norm(t)]
    if not alvo or not words:
        return None
    wn = [norm(w["word"]) for w in words]
    n = len(alvo)
    for i in range(len(wn) - n + 1):
        if wn[i:i + n] == alvo:
            return round(words[i]["start"], 2)
    # match parcial: primeira palavra forte (>=4) do trecho
    fortes = [t for t in alvo if len(t) >= 4]
    for i, w in enumerate(wn):
        if fortes and w == fortes[0]:
            return round(words[i]["start"], 2)
    return None


def baixar_imagem(busca, idx):
    MAPAS_DIR.mkdir(parents=True, exist_ok=True)
    dest = MAPAS_DIR / f"mapa_{idx}.jpg"
    try:
        from pexels_api import search as _pex_search   # rotação de N chaves + retry 429
        fotos = _pex_search(busca, "photos", 1)
        if not fotos:
            return None, None
        url = fotos[0]["src"]["large"]
        req2 = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        dest.write_bytes(urllib.request.urlopen(req2, timeout=60).read())
        return str(dest), fotos[0].get("alt", "")[:40]
    except Exception as e:
        print(f"    imagem falhou ({busca}): {str(e)[:60]}")
        return None, None


import urllib.parse  # noqa: E402


def main():
    # modo teste: só detecta num .txt e imprime
    if len(sys.argv) > 1:
        txt = Path(sys.argv[1]).read_text(encoding="utf-8")
        print(f"=== Detecção (teste) em {sys.argv[1]} ===")
        ev = detectar(txt)
        print(json.dumps(ev, ensure_ascii=False, indent=2))
        print(f"\n{len(ev)} lugares detectados")
        return

    roteiro = ROTEIRO.read_text(encoding="utf-8")
    words = json.load(open(WORDS, encoding="utf-8")) if WORDS.exists() else []
    tl = json.load(open(TIMELINE, encoding="utf-8"))

    print("=== Detector de mapas ===")
    eventos = detectar(roteiro)
    print(f"  {len(eventos)} lugares detectados\n")

    # localiza (ainda SEM baixar imagem)
    cand = []
    for e in eventos:
        ini = localizar(e.get("trecho"), words)
        if ini is None:
            continue
        cand.append({"inicio": ini, "dur": DUR_MAPA, "pais": e.get("pais"),
                     "coord": [e.get("lng"), e.get("lat")], "legenda": e.get("legenda"),
                     "busca_imagem": e.get("busca_imagem"),
                     "tipo": "satelite" if str(e.get("tipo", "")).lower().startswith("sat") else "estilizado"})

    # MINIMIZA repetição: sem país repetido + cooldown + teto adaptativo (~1 mapa / 75s)
    dur = tl.get("duracao") or (words[-1]["end"] if words else 0)
    COOLDOWN = 38.0
    MAX_MAPAS = max(3, int(dur / 50))
    cand.sort(key=lambda m: m["inicio"])
    limpos, paises = [], set()
    for m in cand:
        pais = (m.get("pais") or "").lower()
        if pais in paises:
            continue                                  # não repete país
        if limpos and m["inicio"] - limpos[-1]["inicio"] < COOLDOWN:
            continue                                  # cooldown entre mapas
        limpos.append(m); paises.add(pais)
        if len(limpos) >= MAX_MAPAS:
            break
    print(f"  {len(cand)} candidatos -> {len(limpos)} mapas (teto {MAX_MAPAS}, cooldown {COOLDOWN:.0f}s, sem país repetido)")

    # satélite: baixa pilha de tiles ESRI pros mapas marcados (fallback p/ estilizado se falhar)
    from satelite_fetch import fetch_niveis
    for i, m in enumerate(limpos):
        if m.get("tipo") == "satelite":
            lng, lat = m["coord"]
            niveis = fetch_niveis(lng, lat, f"sat{i}") if lng is not None and lat is not None else []
            if niveis:
                m["niveis"] = niveis
                print(f"  {m['inicio']:>6.1f}s  {m['pais']:<14} '{m['legenda']}'  SATÉLITE ({len(niveis)} níveis)")
                continue
            m["tipo"] = "estilizado"  # fetch falhou -> cai pro mapa estilizado

    # imagem (estilizado): baixa só dos mapas estilizados mantidos
    for i, m in enumerate(limpos):
        if m.get("tipo") == "satelite":
            continue
        img_path, _alt = baixar_imagem(m.get("busca_imagem") or m.get("pais", ""), i)
        m["imagem_path"] = img_path
        print(f"  {m['inicio']:>6.1f}s  {m['pais']:<14} '{m['legenda']}'  estilizado img={'ok' if img_path else 'X'}")

    tl["mapas"] = limpos
    TIMELINE.write_text(json.dumps(tl, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nOK -> {len(limpos)} mapas gravados no timeline.json")


if __name__ == "__main__":
    main()
