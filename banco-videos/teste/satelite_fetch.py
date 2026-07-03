"""Fetcher de TILES de satélite (ESRI World Imagery, sem API key) para o SatelliteZoom.
Dado (lng,lat), baixa uma pilha de níveis de zoom progressivo (global -> rua) em 16:9.
Reutilizável: detectar_mapas.py chama fetch_niveis() pros mapas marcados como 'satelite'.

Uso standalone: python satelite_fetch.py <lng> <lat> <ident>
"""
import json
import math
import sys
import urllib.request
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
TESTE = Path(r"F:/Canal Dark/Aplicativo de Edição/banco-videos/teste")
SAT_DIR = TESTE / "sat_tiles"
EXPORT = "https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/export"
UA = {"User-Agent": "Mozilla/5.0"}
# half = metade da LARGURA do bbox em metros (Web Mercator). Mergulho global -> rua.
HALFS = [1500000, 330000, 73000, 16000, 3600, 800]
# 960x540: tiles menores decodificam confiável sob gl=angle (1280x720 causava EncodingError
# sob carga). Exibidos com objectFit cover em 1920x1080 -> nitidez suficiente.
W, H = 960, 540


def _merc(lon, lat):
    R = 6378137.0
    return math.radians(lon) * R, math.log(math.tan(math.pi / 4 + math.radians(lat) / 2)) * R


def fetch_niveis(lng, lat, ident, halfs=None):
    """Baixa os tiles e retorna [{path, half}] (ou [] se falhar). Pula níveis que já existem."""
    halfs = halfs or HALFS
    SAT_DIR.mkdir(parents=True, exist_ok=True)
    try:
        x, y = _merc(float(lng), float(lat))
    except Exception:
        return []
    niveis = []
    for i, half in enumerate(halfs):
        hh = half * H / W
        bbox = f"{x - half},{y - hh},{x + half},{y + hh}"
        url = f"{EXPORT}?bbox={bbox}&bboxSR=3857&imageSR=3857&size={W},{H}&format=jpg&f=image"
        dest = SAT_DIR / f"{ident}_{i}.jpg"
        try:
            data = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40).read()
            if data[:2] != b"\xff\xd8" or len(data) < 8000:
                print(f"    nivel {i} inválido"); return []
            dest.write_bytes(data)
            niveis.append({"path": str(dest).replace("\\", "/"), "half": half})
        except Exception as e:
            print(f"    nivel {i} falhou: {str(e)[:50]}"); return []
    return niveis


def main():
    if len(sys.argv) < 4:
        print("uso: python satelite_fetch.py <lng> <lat> <ident>"); return
    n = fetch_niveis(sys.argv[1], sys.argv[2], sys.argv[3])
    print(json.dumps(n, ensure_ascii=False, indent=2))
    print(f"{len(n)} níveis")


if __name__ == "__main__":
    main()
