"""Mini catálogo de B-roll via Pexels API (stock grátis).

Busca clips por queries do nicho cosmic/espiritual, baixa em 1080p e monta
um catálogo JSON pronto pro matcher (Fase 1).

Setup:
  1. Pegue a chave grátis em https://www.pexels.com/api/ (botão "Get Started")
  2. Adicione em config.json do video-automator:
       "pexels_api_key": "SUA_CHAVE"
     (ou exporte PEXELS_API_KEY no ambiente)
  3. python construir_catalogo.py

Idempotente: re-rodar pula clips já baixados.
Pexels free: 200 req/hora, 20k/mês — folgado pro nosso volume.
"""
import json
import os
import sys
import urllib.request
import urllib.error
import urllib.parse
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

BASE = Path(r"F:/Canal Dark/Aplicativo de Edição/banco-videos")
CLIPS_DIR = BASE / "clips"
CATALOGO = BASE / "catalogo.json"
CONFIG = Path(r"F:/Canal Dark/Aplicativo de Edição/video-automator/config.json")

# === Queries do nicho (mini catálogo). Cada uma puxa PER_QUERY clips. ===
# Formato: (query_pexels, nicho_tag, mood)
QUERIES = [
    ("nebula",                 "cosmic", "expansive"),
    ("galaxy",                 "cosmic", "expansive"),
    ("starry night sky",       "cosmic", "calm"),
    ("aurora borealis",        "cosmic", "ethereal"),
    ("milky way timelapse",    "cosmic", "expansive"),
    ("calm ocean sunset",      "nature", "peaceful"),
    ("mountain sunrise",       "nature", "hopeful"),
    ("clouds timelapse",       "nature", "flowing"),
    ("forest sunlight rays",   "nature", "sacred"),
    ("candle flame dark",      "intimate", "intimate"),
    ("water ripple slow",      "nature", "meditative"),
    ("person silhouette sunset", "human", "reflective"),
]
PER_QUERY = 4           # clips por query (mini = ~48 total)
TARGET_W = 1920         # preferência de resolução (Full HD)


def get_api_key() -> str:
    if os.environ.get("PEXELS_API_KEY"):
        return os.environ["PEXELS_API_KEY"]
    try:
        cfg = json.load(open(CONFIG, encoding="utf-8"))
        k = cfg.get("pexels_api_key", "")
        if k:
            return k
    except Exception:
        pass
    print("ERRO: sem chave Pexels.")
    print("  1. Pegue grátis em https://www.pexels.com/api/")
    print('  2. Adicione em config.json: "pexels_api_key": "SUA_CHAVE"')
    print("     (ou: export PEXELS_API_KEY=...)")
    sys.exit(1)


def pexels_search(api_key: str, query: str, per_page: int) -> list:
    url = (
        f"https://api.pexels.com/videos/search?query={urllib.parse.quote(query)}"
        f"&per_page={per_page}&orientation=landscape&size=medium"
    )
    req = urllib.request.Request(url, headers={
        "Authorization": api_key,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    })
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read()).get("videos", [])


def pick_file(video: dict) -> dict | None:
    """Escolhe o video_file ~1080p mp4 (evita 4K gigante)."""
    files = [f for f in video.get("video_files", []) if f.get("file_type") == "video/mp4"]
    if not files:
        return None
    # ordena pela distância de TARGET_W, preferindo <= 1920
    def score(f):
        w = f.get("width") or 0
        penalty = 0 if w <= TARGET_W else 5000  # penaliza 4K
        return abs(w - TARGET_W) + penalty
    files.sort(key=score)
    return files[0]


def download(url: str, dest: Path) -> bool:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=300) as r:
            dest.write_bytes(r.read())
        return True
    except Exception as e:
        print(f"    download falhou: {e}")
        return False


def main():
    api_key = get_api_key()
    CLIPS_DIR.mkdir(parents=True, exist_ok=True)

    # Carrega catálogo existente (idempotência)
    catalogo = {}
    if CATALOGO.exists():
        for item in json.load(open(CATALOGO, encoding="utf-8")):
            catalogo[item["id"]] = item

    print(f"=== Mini catálogo Pexels ({len(QUERIES)} queries × {PER_QUERY}) ===\n")
    novos = 0
    for query, nicho, mood in QUERIES:
        print(f"[{query}] (nicho={nicho}, mood={mood})")
        try:
            videos = pexels_search(api_key, query, PER_QUERY)
        except urllib.error.HTTPError as e:
            print(f"  ERRO HTTP {e.code} — checar chave/limite")
            if e.code == 401:
                sys.exit(1)
            continue
        for v in videos:
            vid = f"pexels_{v['id']}"
            if vid in catalogo and (CLIPS_DIR / f"{vid}.mp4").exists():
                print(f"  SKIP {vid} (já existe)")
                continue
            vf = pick_file(v)
            if not vf:
                continue
            dest = CLIPS_DIR / f"{vid}.mp4"
            print(f"  baixando {vid} ({vf.get('width')}x{vf.get('height')}, {v.get('duration')}s)...", end="", flush=True)
            if not download(vf["link"], dest):
                continue
            print(" OK")
            catalogo[vid] = {
                "id": vid,
                "source": "pexels",
                "source_url": v.get("url", ""),
                "author": (v.get("user") or {}).get("name", ""),
                "local_path": str(dest).replace("\\", "/"),
                "query": query,
                # descrição inicial = query (enriquecer depois com visão/Gemini)
                "descricao_visual": query,
                "nicho": nicho,
                "mood": mood,
                "movimento": "",           # preencher na Fase 0 (visão)
                "duracao": v.get("duration", 0),
                "width": vf.get("width", 0),
                "height": vf.get("height", 0),
            }
            novos += 1
        print()

    # Salva catálogo
    lista = list(catalogo.values())
    with open(CATALOGO, "w", encoding="utf-8") as f:
        json.dump(lista, f, ensure_ascii=False, indent=2)

    total_mb = sum((CLIPS_DIR / f"{i['id']}.mp4").stat().st_size for i in lista if (CLIPS_DIR / f"{i['id']}.mp4").exists()) / 1024 / 1024
    print(f"=== DONE ===")
    print(f"  Catálogo: {len(lista)} clips ({novos} novos)")
    print(f"  Tamanho total: {total_mb:.0f} MB")
    print(f"  JSON: {CATALOGO}")


if __name__ == "__main__":
    main()
