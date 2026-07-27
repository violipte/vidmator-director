"""Banco de ARQUIVO: ingere footage de domínio público do Internet Archive
(NASA = espaço; Prelinger = vintage) -> segmentos ~5s normalizados p/ 1080h ->
Gemini Vision descreve -> entra no MESMO catálogo (fonte:archive + era).

O Director usa como qualquer clipe; o modo fundir|enquadrar é decidido no uso.
Extrai segmentos via ffmpeg seek na URL (sem baixar o filme inteiro). Idempotente.
"""
import json
import subprocess
import sys
import urllib.request
import urllib.parse
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

BANCO = Path(r"D:/Meu Drive/canal_dark_footage_stock")
CATALOGO = BANCO / "catalogo.json"
TMP = Path(r"F:/Canal Dark/Aplicativo de Edição/banco-videos/_tmp_keyframes")
UA = {"User-Agent": "Mozilla/5.0"}

# seed MIX: espaço (NASA) + vintage (Prelinger). Domínio público.
FONTES = [
    {"cat": "archive_space", "q": "collection:nasa AND (earth OR moon OR apollo OR orbit OR space)"},
    {"cat": "archive_vintage", "q": "collection:prelinger AND (city OR street OR nature OR people OR night)"},
]
ITENS_POR_FONTE = 3      # nº de filmes por fonte
SEG_POR_ITEM = 2         # nº de segmentos por filme
SEG_DUR = 5              # duração de cada segmento (s)


def ia_get(url):
    return json.loads(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=45).read())


def buscar(q, rows):
    url = ("https://archive.org/advancedsearch.php?q=" + urllib.parse.quote(q) +
           "&fl[]=identifier&fl[]=title&fl[]=year&sort[]=downloads+desc&rows=" + str(rows) + "&output=json")
    return ia_get(url)["response"]["docs"]


def menor_mp4(ident):
    meta = ia_get(f"https://archive.org/metadata/{ident}")
    mp4s = [f for f in meta.get("files", []) if f.get("name", "").lower().endswith(".mp4") and int(f.get("size", 0)) > 0]
    if not mp4s:
        return None
    mp4s.sort(key=lambda f: int(f.get("size", 0)))
    return f"https://archive.org/download/{ident}/" + urllib.parse.quote(mp4s[0]["name"])


def duracao(url):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "csv=p=0", url], capture_output=True, text=True, timeout=90)
    try:
        return float(out.stdout.strip())
    except Exception:
        return 0.0


def extrair(url, t, dest):
    r = subprocess.run(["ffmpeg", "-y", "-ss", str(t), "-i", url, "-t", str(SEG_DUR), "-an",
                        "-vf", "scale=-2:1080", "-c:v", "libx264", "-pix_fmt", "yuv420p",
                        "-crf", "21", "-movflags", "+faststart", str(dest)],
                       capture_output=True, timeout=300)
    return dest.exists() and dest.stat().st_size > 10000


def keyframe(mp4, out_jpg):
    subprocess.run(["ffmpeg", "-y", "-ss", "2", "-i", str(mp4), "-frames:v", "1",
                    "-vf", "scale=640:-1", str(out_jpg)], capture_output=True)
    return out_jpg.exists()


def main():
    TMP.mkdir(parents=True, exist_ok=True)
    catalogo = {}
    if CATALOGO.exists():
        for it in json.load(open(CATALOGO, encoding="utf-8")):
            catalogo[it["id"]] = it
    print(f"=== Banco ARQUIVO | catálogo atual: {len(catalogo)} ===\n")
    from enriquecer import descrever

    novos = 0
    for fonte in FONTES:
        cat = fonte["cat"]
        (BANCO / cat).mkdir(parents=True, exist_ok=True)
        print(f"### {cat} ###")
        try:
            docs = buscar(fonte["q"], ITENS_POR_FONTE * 2)
        except Exception as e:
            print(f"  busca falhou: {e}")
            continue
        usados = 0
        for doc in docs:
            if usados >= ITENS_POR_FONTE:
                break
            ident = doc["identifier"]
            era = str(doc.get("year", "")) or "ARCHIVE"
            try:
                url = menor_mp4(ident)
                if not url:
                    continue
                dur = duracao(url)
                if dur < 30:  # muito curto p/ amostrar
                    continue
            except Exception as e:
                print(f"  {ident[:30]} meta/probe falhou: {str(e)[:40]}")
                continue
            # timestamps espaçados, evitando primeiros/últimos 15% (créditos/letreiros)
            ts = [round(dur * f) for f in [0.30, 0.55, 0.78][:SEG_POR_ITEM]]
            got = 0
            for n, t in enumerate(ts):
                vid = f"archive_{ident[:24]}_{n}"
                if vid in catalogo:
                    got += 1
                    continue
                dest = BANCO / cat / f"{vid}.mp4"
                try:
                    if not dest.exists() and not extrair(url, t, dest):
                        continue
                except Exception:
                    continue
                kf = TMP / f"{vid}.jpg"
                enr = None
                if keyframe(dest, kf):
                    enr, _via = descrever(kf)
                    kf.unlink(missing_ok=True)
                catalogo[vid] = {
                    "id": vid, "source": "archive", "fonte": "archive",
                    "source_url": f"https://archive.org/details/{ident}",
                    "arquivo": str(dest).replace("\\", "/"),
                    "categoria": cat, "era": era,
                    "descricao_visual": (enr or {}).get("descricao_visual", doc.get("title", "")),
                    "mood": (enr or {}).get("mood", ""),
                    "movimento": (enr or {}).get("movimento", ""),
                    "tags": ((enr or {}).get("tags", []) or []) + ["archive", "vintage"],
                    "duracao": SEG_DUR,
                    "enriquecido": bool(enr),
                }
                novos += 1
                got += 1
                print(f"  [{novos}] {vid} ({'OK' if enr else 'sem-vision'}) {catalogo[vid]['descricao_visual'][:46]}")
            if got:
                usados += 1
        json.dump(list(catalogo.values()), open(CATALOGO, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        print(f"  -> {cat} done\n")

    enr_ok = sum(1 for c in catalogo.values() if c.get("fonte") == "archive" and c.get("enriquecido"))
    arq = sum(1 for c in catalogo.values() if c.get("fonte") == "archive")
    print(f"=== DONE === +{novos} clips de arquivo | total archive no catálogo: {arq} ({enr_ok} enriquecidos)")


if __name__ == "__main__":
    main()
