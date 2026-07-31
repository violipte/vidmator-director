# -*- coding: utf-8 -*-
"""CURADOR v5 (F6) — footage com queries ESTRATIFICADAS + pool multi-fonte +
BATCH-SCORE (defeitos v4 anulam + régua 0-10) + escolha do MELHOR do pool.

Fluxo por beat de vídeo:
  1. 4 queries com estratégia (fiel / específica / ângulo-contexto / keywords)
  2. coleta candidatos em paralelo: pixabay_video + coverr (fontes5) — round a round
  3. batch_gate (1 chamada Vision pro pool inteiro): score 0-10 + vetos
  4. melhor >= 8 vence e SÓ ELE é reivindicado (perdedores voltam pro pool global)
  5. download + normaliza 1080p30 + dedup visual (executor) + resolvido/bNNN.json
  6. pool não rendeu? fallback = resolver_stock do executor v4 (pexels+yt intactos)

Uso: python curador5.py --job <dir> --plano plano.json [--workers 4] [--resume]
"""
import argparse
import json
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).parent))
import executor_beats as ex  # noqa — dedup/USED/normalização/fallback v4 (read-only)
from curador_footage import secoes_do_plano, ctx_da_secao  # noqa
from fontes5 import coletar_videos, coletar_imagens  # noqa
from gate5 import batch_gate, SCORE_THRESHOLD  # noqa

STOPWORDS5 = {"the", "a", "an", "of", "in", "on", "at", "with", "and", "or", "for", "to"}


def queries_estratificadas(busca, assunto_secao=""):
    """4 estratégias do dark-content-studio, determinísticas (sem LLM)."""
    base = busca.split(" OR ")[0].strip()
    kws = [w for w in re.findall(r"[a-zA-Z]{3,}", busca) if w.lower() not in STOPWORDS5]
    return [
        base,                                                       # 1 fiel
        f"{base} close up detail",                                  # 2 específica
        f"{assunto_secao} {base} wide shot".strip()[:90],           # 3 ângulo/contexto
        " ".join(kws[:4]),                                          # 4 keywords
    ]


def _baixar_normalizar(url, dest_mp4, tmp):
    """Download + normaliza 1920x1080/30fps h264 (padrão do executor)."""
    import httpx
    import threading
    # nome ÚNICO por thread+chamada (WinError 32: dois workers colidiam no mesmo temp)
    bruto = Path(tmp) / f"c5_{threading.get_ident()}_{abs(hash(url)) % 10**8}.mp4"
    try:
        with httpx.stream("GET", url, headers={"User-Agent": "Mozilla/5.0"},
                          timeout=120, follow_redirects=True) as r:
            if r.status_code != 200:
                return False
            with open(bruto, "wb") as f:
                for chunk in r.iter_bytes(1 << 16):
                    f.write(chunk)
        if bruto.stat().st_size < 200_000 or b"ftyp" not in bruto.read_bytes()[:16]:
            return False
        r2 = subprocess.run(["ffmpeg", "-nostdin", "-y", "-loglevel", "error", "-i", str(bruto),
                             "-t", "12", "-vf", "scale=1920:1080:force_original_aspect_ratio=increase,"
                             "crop=1920:1080", "-r", "30", "-an", "-c:v", "libx264", "-preset",
                             "fast", "-crf", "20", "-pix_fmt", "yuv420p", str(dest_mp4)],
                            capture_output=True, timeout=300)
        return r2.returncode == 0 and Path(dest_mp4).exists()
    except Exception:
        return False
    finally:
        try:
            bruto.unlink(missing_ok=True)
        except OSError:
            pass  # Windows pode segurar o handle um instante — o tmp é limpo depois


def resolver_beat5(b, sctx, ctx, usados_urls):
    """Pool multi-fonte + batch score; devolve dict resolvido ou None (=> fallback v4)."""
    assunto = (b.get("_sec_ctx") or "")[:0]  # ctx vai pro gate, não pra query
    for rodada, q in enumerate(queries_estratificadas(b.get("busca") or "", "")):
        if not q.strip():
            continue
        cands = coletar_videos(q, n_por_fonte=3, usados=usados_urls)
        if not cands:
            continue
        # gate pelo THUMB (barato); sem thumb usa a própria url do vídeo? -> pula
        pool = [{**c, "url": c.get("thumb") or c["url"]} for c in cands]
        notas = batch_gate(pool, b.get("busca") or q, sctx)
        melhor = next((n for n in notas if n["score"] >= SCORE_THRESHOLD), None)
        if not melhor:
            continue
        orig = next(c for c in cands if c["id"] == melhor["id"])
        dest = Path(ctx["assets"]) / f"b{b['i']:03d}__T1__{orig['id']}.mp4"
        if not _baixar_normalizar(orig["url"], dest, ctx["tmp"]):
            continue
        if ex._e_dup_visual(str(dest), ctx):
            dest.unlink(missing_ok=True)
            continue
        usados_urls.add(orig["url"])  # SÓ o vencedor é reivindicado (release implícito dos demais)
        return {"i": b["i"], "t_ini": b.get("t_ini", 0), "t_fim": b.get("t_fim", 0),
                "secao": b.get("secao", 0), "status": "ok", "arquivo": str(dest),
                "tier": 1, "fonte": orig["source"], "tipo": "stock",
                "score": melhor["score"], "busca": q[:120]}
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--job", required=True)
    ap.add_argument("--plano", required=True)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--resume", action="store_true")
    a = ap.parse_args()

    job = Path(a.job)
    plano = json.loads(Path(a.plano).read_text(encoding="utf-8"))
    sc = json.loads((job / "style_card.json").read_text(encoding="utf-8")) \
        if (job / "style_card.json").exists() else {}
    desamb = sc.get("desambiguacao") or {}
    todos = sorted(set(desamb.values()))
    secs = secoes_do_plano(plano, desamb)
    if not any(s["produto"] for s in secs.values()):
        todos = []  # nicho sem announce => ctx b-roll (fix 27/07)

    ctx = {"assets": job / "assets", "tmp": job / "_tmp", "res": job / "resolvido"}
    for d in ctx.values():
        d.mkdir(parents=True, exist_ok=True)
    usados_urls = set()

    tarefas = []
    for s, sec in sorted(secs.items()):
        sctx = ctx_da_secao(sec, todos)
        for b in sec["beats"]:
            if b.get("tipo") not in ("footage_video", "stock"):
                continue
            jres = ctx["res"] / f"b{b['i']:03d}.json"
            if a.resume and jres.exists():
                continue
            b2 = dict(b)
            b2["_sec_ctx"] = sctx
            tarefas.append((b2, sctx))
    print(f"curador5: {len(tarefas)} beats | fontes novas + batch-score + fallback v4")

    def _rodar5(par):
        """31/07 (correção Piter): a v5 SOMA fontes, NUNCA substitui a hierarquia T3.
        Ordem = cascata v4 PRIMEIRO (YouTube/footage REAL = carro-chefe do T3, com
        todos os gates do executor) e só então o pool novo (Pexels/Coverr/Pixabay
        batch-score) como ADIÇÃO — antes eu tinha invertido e o stock genérico
        ganhava do footage real."""
        b2, sctx = par
        origem = "v4"
        try:
            r = ex.resolver_footage_video(b2, ctx) if b2.get("tipo") == "footage_video" \
                else ex.resolver_stock(b2, ctx)
        except Exception as e4:
            print(f"  b{b2['i']:03d} v4 erro ({type(e4).__name__})")
            r = None
        if not (r and r.get("status") == "ok" and r.get("arquivo")):
            try:  # ADIÇÃO v5: fontes novas + batch-score entram onde o v4 não achou
                r = resolver_beat5(b2, sctx, ctx, usados_urls)
                origem = "v5"
            except Exception as e5:
                print(f"  b{b2['i']:03d} v5 erro ({type(e5).__name__})")
                r = None
        return b2, r, origem

    ok5 = ok4 = falhas = 0
    with ThreadPoolExecutor(max_workers=a.workers) as pool:
        for b2, r, origem in pool.map(_rodar5, tarefas):
            if r and r.get("status") == "ok" and r.get("arquivo"):
                (ctx["res"] / f"b{b2['i']:03d}.json").write_text(
                    json.dumps({**{k: b2.get(k) for k in ("i", "secao", "t_ini", "t_fim", "busca")},
                                **r, "tipo": b2.get("tipo")}, ensure_ascii=False), encoding="utf-8")
                if origem == "v5":
                    ok5 += 1
                else:
                    ok4 += 1
                print(f"  b{b2['i']:03d} OK [{origem}] {Path(r['arquivo']).name[-42:]}")
            else:
                falhas += 1
                print(f"  b{b2['i']:03d} BURACO")
    print(f"=== curador5: {ok5} via fontes novas + {ok4} via fallback v4 | {falhas} buracos ===")


if __name__ == "__main__":
    main()
