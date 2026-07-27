"""Clipador de B-roll do YouTube — SÓ material livre (Creative Commons), com o
trecho recortado direto (sem baixar o vídeo todo), normalizado 1080p, entrando no
banco com ATRIBUIÇÃO. Recusa vídeo protegido por copyright (trava de licença).

Uso:
  # 1) buscar candidatos CC (lista url/licença/duração pra você escolher)
  python clipar_youtube.py --busca "berlin wall 1989 archival" --n 12

  # 2) clipar um trecho de um vídeo CC (start-end em s ou MM:SS)
  python clipar_youtube.py <url> 1:30 1:44 --cat historia
  #    --pd  => você ASSUME que é domínio público (registra como asserção sua)
"""
import json
import subprocess
import sys
import hashlib
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

BANK = Path(r"D:/Meu Drive/canal_dark_footage_stock")
CATALOGO = BANK / "catalogo.json"
YT_DIR = BANK / "youtube_cc"
TMP = Path(r"F:/Canal Dark/Aplicativo de Edição/banco-videos/_tmp_yt")
YTDLP = [sys.executable, "-m", "yt_dlp"]


def info(url):
    r = subprocess.run(YTDLP + ["-J", "--no-warnings", "--no-download", url],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    try:
        return json.loads(r.stdout)
    except Exception:
        return None


def is_free(inf, pd_flag):
    lic = (inf.get("license") or "").strip()
    if "creative commons" in lic.lower():
        return True, lic
    if pd_flag:
        return True, "PUBLIC DOMAIN (asserido pelo usuário)"
    return False, lic or "Standard YouTube License / desconhecida"


def buscar(query, n):
    r = subprocess.run(
        YTDLP + ["-J", "--no-warnings", "--no-download", "--ignore-errors",
                 "--flat-playlist" if False else "--no-flat-playlist",
                 f"ytsearch{n}:{query}"],
        capture_output=True, text=True, encoding="utf-8", errors="replace")
    try:
        data = json.loads(r.stdout)
    except Exception:
        # ytsearch retorna 1 objeto por linha às vezes; tenta por linha
        entries = []
        for ln in (r.stdout or "").splitlines():
            try:
                entries.append(json.loads(ln))
            except Exception:
                pass
        data = {"entries": entries}
    livres = []
    for e in (data.get("entries") or []):
        if not e:
            continue
        ok, lic = is_free(e, False)
        if ok:
            livres.append((e.get("webpage_url") or e.get("url"), round(e.get("duration") or 0),
                           (e.get("title") or "")[:52], lic))
    print(f"=== {len(livres)} vídeos CREATIVE COMMONS (de {n} buscados) ===")
    for url, dur, tit, lic in livres:
        print(f"  {dur:>4}s  {tit:<52}  {url}")
    if not livres:
        print("  (nenhum CC — tente outra query; a maioria do YouTube é protegida)")


def clip(url, start, end, dest):
    # REGRA ABSOLUTA: clipe do YouTube NUNCA leva áudio.
    #  (1) baixa SÓ o stream de vídeo (bv*, sem faixa de áudio) — o áudio nem toca o disco
    #  (2) ffmpeg com -an garante MUDO mesmo se cair no fallback progressivo (b)
    # Áudio de YT = principal gatilho do Content ID (música/voz). B-roll é sempre mudo.
    TMP.mkdir(parents=True, exist_ok=True)
    tmp = TMP / "yt_sec.%(ext)s"
    for t in list(TMP.glob("yt_sec.*")):
        t.unlink(missing_ok=True)
    r = subprocess.run(
        YTDLP + ["--no-warnings", "--force-keyframes-at-cuts",
                 "--download-sections", f"*{start}-{end}",
                 "-f", "bv*[height<=1080]/bv*/b[height<=1080]/b",   # VÍDEO-ONLY (sem +ba)
                 "-o", str(tmp), url],
        capture_output=True, text=True, encoding="utf-8", errors="replace")
    got = list(TMP.glob("yt_sec.*"))
    if not got:
        print(f"    download falhou: {(r.stderr or '')[-160:].strip()}")
        return False
    src = got[0]
    # normaliza 1080p + REMOVE 100% do áudio (-an) — regra absoluta
    subprocess.run(["ffmpeg", "-y", "-i", str(src), "-an",
                    "-vf", "scale=-2:1080", "-c:v", "libx264", "-pix_fmt", "yuv420p",
                    "-crf", "20", "-movflags", "+faststart", str(dest)],
                   capture_output=True)
    src.unlink(missing_ok=True)
    # trava final: se por qualquer motivo houver faixa de áudio, rejeita
    if dest.exists():
        chk = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a",
                              "-show_entries", "stream=codec_type", "-of", "csv=p=0", str(dest)],
                             capture_output=True, text=True)
        if (chk.stdout or "").strip():
            print("    ERRO: clipe saiu com áudio — rejeitado (regra absoluta)")
            dest.unlink(missing_ok=True)
            return False
    return dest.exists() and dest.stat().st_size > 10000


def registrar(dest, inf, lic, categoria, start, end):
    cat = {}
    if CATALOGO.exists():
        for it in json.load(open(CATALOGO, encoding="utf-8")):
            cat[it["id"]] = it
    vid = f"yt_{inf.get('id','x')}_{start}".replace(":", "")
    enr = None
    try:
        from _tmp_kf_helper import _kf  # noqa
    except Exception:
        pass
    # keyframe + descrição (best-effort, reusa enriquecer.descrever CLI-primário)
    try:
        kf = TMP / f"{vid}.jpg"
        subprocess.run(["ffmpeg", "-y", "-ss", "1", "-i", str(dest), "-frames:v", "1",
                        "-vf", "scale=640:-1", str(kf)], capture_output=True)
        if kf.exists():
            sys.path.insert(0, str(Path(__file__).parent))
            from enriquecer import descrever
            enr, _via = descrever(kf)
            kf.unlink(missing_ok=True)
    except Exception as e:
        print(f"    (descrição pulada: {str(e)[:50]})")
    cat[vid] = {
        "id": vid, "source": "youtube_cc", "fonte": "youtube_cc",
        "arquivo": str(dest).replace("\\", "/"), "categoria": categoria,
        "descricao_visual": (enr or {}).get("descricao_visual", inf.get("title", "")[:60]),
        "mood": (enr or {}).get("mood", ""), "movimento": (enr or {}).get("movimento", ""),
        "tags": ((enr or {}).get("tags", []) or []) + ["youtube", "creative_commons"],
        "duracao": _segs(end) - _segs(start),
        "enriquecido": bool(enr),
        "atribuicao": {"titulo": inf.get("title"), "autor": inf.get("uploader"),
                       "url": inf.get("webpage_url"), "licenca": lic,
                       "canal_url": inf.get("uploader_url")},
    }
    json.dump(list(cat.values()), open(CATALOGO, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"OK -> {dest.name} | fonte:youtube_cc | {'descrito' if enr else 'sem-vision'}")
    print(f"   ATRIBUIÇÃO: {inf.get('uploader')} — {inf.get('webpage_url')} [{lic}]")


def _segs(t):
    t = str(t)
    if ":" in t:
        p = [float(x) for x in t.split(":")]
        return p[0] * 60 + p[1] if len(p) == 2 else p[0] * 3600 + p[1] * 60 + p[2]
    return float(t)


def main():
    a = sys.argv[1:]
    if not a:
        print(__doc__); return
    if a[0] == "--busca":
        query = a[1]
        n = int(a[a.index("--n") + 1]) if "--n" in a else 10
        buscar(query, n)
        return
    url, start, end = a[0], a[1], a[2]
    categoria = a[a.index("--cat") + 1] if "--cat" in a else "youtube_cc"
    pd_flag = "--pd" in a
    print(f"=== clipar {start}-{end} de {url} ===")
    inf = info(url)
    if not inf:
        print("  ERRO: não consegui ler o vídeo."); return
    ok, lic = is_free(inf, pd_flag)
    if not ok:
        print(f"  RECUSADO ❌ — licença: {lic}")
        print(f"  '{inf.get('title','')[:60]}' NÃO é Creative Commons. Use só material livre.")
        print("  (se você TEM CERTEZA que é domínio público, rode de novo com --pd)")
        return
    print(f"  licença OK ✅ [{lic}] — '{inf.get('title','')[:55]}'")
    YT_DIR.mkdir(parents=True, exist_ok=True)
    dest = YT_DIR / (f"yt_{inf.get('id','x')}_{str(start).replace(':','')}.mp4")
    if clip(url, start, end, dest):
        registrar(dest, inf, lic, categoria, start, end)
    else:
        print("  falhou ao clipar.")


if __name__ == "__main__":
    main()
