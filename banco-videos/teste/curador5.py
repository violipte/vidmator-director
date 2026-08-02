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
import vision_gate as vg  # noqa — amostragem de frames p/ dar nota ao candidato do v4
from curador_footage import secoes_do_plano, ctx_da_secao  # noqa
from fontes5 import coletar_videos, coletar_imagens  # noqa
from gate5 import batch_gate, SCORE_THRESHOLD  # noqa

STOPWORDS5 = {"the", "a", "an", "of", "in", "on", "at", "with", "and", "or", "for", "to"}

# hierarquia T3 preservada (regra Piter 31/07): footage REAL vale mais que stock, então
# entra na disputa com vantagem — não com passe livre.
BONUS_TIER = {3: 2, 2: 1, 1: 0}
NOTA_V4_OTIMA = 9  # v4 com plano ótimo fecha o beat sem gastar o pool novo (tempo)


def queries_estratificadas(busca, assunto_secao="", ancora=""):
    """4 estratégias + ÂNCORA DO TEMA (31/07, QA Piter: 'ilustra a frase, não a cena').
    Beat isolado buscava 'doctor writing notebook' num vídeo de COBRA e trazia clipe
    genérico. A âncora do style_card entra em TODA query — o assunto do vídeo domina."""
    base = busca.split(" OR ")[0].strip()
    kws = [w for w in re.findall(r"[a-zA-Z]{3,}", busca) if w.lower() not in STOPWORDS5]
    anc = (ancora or "").strip()
    return [
        f"{anc} {base}".strip()[:95],                     # 1 âncora + fiel
        f"{base} close up detail {anc}".strip()[:95],     # 2 específica ancorada
        f"{anc} {' '.join(kws[:3])}".strip()[:95],        # 3 âncora + keywords
        base,                                             # 4 fiel puro (último recurso)
    ]


def _luminancia_ok(mp4, tmp, min_brilho=42):
    """Gate de TELA (31/07): clipe escuro demais NÃO vai ao ar — o Vision aprova
    'é uma cobra' mas não vê que na tela é um borrão preto (frame 7s do vídeo v2).
    Determinístico, sem API: brilho médio de 3 instantes."""
    from PIL import Image, ImageStat
    vals = []
    for ss in ("1", "2.5", "4"):
        o = Path(tmp) / f"lum_{abs(hash(str(mp4) + ss)) % 10**8}.jpg"
        subprocess.run(["ffmpeg", "-nostdin", "-y", "-loglevel", "error", "-ss", ss,
                        "-i", str(mp4), "-frames:v", "1", "-vf", "scale=160:-2", str(o)],
                       capture_output=True, timeout=60)
        if o.exists():
            try:
                vals.append(ImageStat.Stat(Image.open(o).convert("L")).mean[0])
            except Exception:
                pass
            o.unlink(missing_ok=True)
    return (sum(vals) / len(vals)) >= min_brilho if vals else True


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


def _baixar_imagem(url, dest_jpg):
    """Download de imagem + cap de resolução (o executor já tem a regra: original de
    30MP estoura EncodingError no render)."""
    import httpx
    try:
        r = httpx.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=60, follow_redirects=True)
        if r.status_code != 200 or len(r.content) < 8000:
            return False
        Path(dest_jpg).write_bytes(r.content)
        from PIL import Image
        with Image.open(dest_jpg) as im:   # valida que é imagem de verdade
            if min(im.size) < 480:
                Path(dest_jpg).unlink(missing_ok=True)
                return False
        ex._cap_resolucao(Path(dest_jpg))
        return True
    except Exception:
        Path(dest_jpg).unlink(missing_ok=True)
        return False


def resolver_beat5(b, sctx, ctx, usados_urls, ancora=""):
    """Pool multi-fonte + batch score; devolve dict resolvido ou None (=> fallback v4).

    01/08 (QA cobras + pedido do Piter): antes só VÍDEO era coletado aqui — a via de
    IMAGEM (`coletar_imagens`: Openverse/SearXNG/Pixabay/Unsplash) estava importada e
    NUNCA era chamada. Efeito: a imagem nota 9 que ilustrava o bicho não perdia a
    disputa, ela nunca ENTRAVA na disputa, e o beat acabava com vídeo genérico nota 6
    (ou com esquema técnico vindo do fallback v4). Agora vídeo e imagem vão para o
    MESMO batch-score e o melhor vence, seja qual for a mídia."""
    for rodada, q in enumerate(queries_estratificadas(b.get("busca") or "", "", ancora)):
        if not q.strip():
            continue
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=2) as _p:
            f_v = _p.submit(coletar_videos, q, 3, usados_urls)
            f_i = _p.submit(coletar_imagens, q, 3, usados_urls)
            vids = [{**c, "_midia": "video"} for c in (f_v.result() or [])]
            imgs = [{**c, "_midia": "imagem"} for c in (f_i.result() or [])]
        cands = vids + imgs
        if not cands:
            continue
        # vídeo é julgado pelo THUMB (barato); imagem, por ela mesma
        pool = [{**c, "url": c.get("thumb") or c["url"]} for c in cands]
        notas = batch_gate(pool, b.get("busca") or q, sctx, tema=ancora)
        # o pool inteiro disputa por SCORE — imagem 9 ganha de vídeo 6 (regra Piter 01/08)
        for melhor in [n for n in notas if n["score"] >= 7]:
            orig = next((c for c in cands if c["id"] == melhor["id"]), None)
            if not orig:
                continue
            if orig["_midia"] == "video":
                dest = Path(ctx["assets"]) / f"b{b['i']:03d}__T1__{orig['id']}.mp4"
                if not _baixar_normalizar(orig["url"], dest, ctx["tmp"]):
                    continue
                if not _luminancia_ok(dest, ctx["tmp"]):   # gate de TELA
                    dest.unlink(missing_ok=True)
                    continue
                tipo_final = "stock"
            else:
                dest = Path(ctx["assets"]) / f"b{b['i']:03d}__T1__{orig['id']}.jpg"
                if not _baixar_imagem(orig["url"], dest):
                    continue
                tipo_final = "footage_imagem"
            if ex._e_dup_visual(str(dest), ctx):
                dest.unlink(missing_ok=True)
                continue
            usados_urls.add(orig["url"])  # SÓ o vencedor reivindica (demais voltam ao pool)
            return {"i": b["i"], "t_ini": b.get("t_ini", 0), "t_fim": b.get("t_fim", 0),
                    "secao": b.get("secao", 0), "status": "ok", "arquivo": str(dest),
                    "tier": 1, "fonte": orig["source"], "tipo": tipo_final,
                    "tipo_final": tipo_final, "midia": orig["_midia"],
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

    ancora5 = sc.get("assunto_ancora") or ""
    ctx = {"assets": job / "assets", "tmp": job / "_tmp", "res": job / "resolvido"}
    for d in ctx.values():
        d.mkdir(parents=True, exist_ok=True)
    usados_urls = set()

    tarefas = []
    for s, sec in sorted(secs.items()):
        sctx = ctx_da_secao(sec, todos)
        for b in sec["beats"]:
            # 01/08: ILUSTRACAO entrou aqui. Os 21 beats de "diagram" do plano de cobras
            # (neuromuscular junction, diaphragm paralysis, crotoxin molecule) iam DIRETO
            # pro v4 — sem âncora do tema e sem score — e voltavam com esquema de livro
            # de fisiologia, que não ilustra cobra nenhuma. Agora disputam igual.
            if b.get("tipo") not in ("footage_video", "stock", "ilustracao", "footage_imagem"):
                continue
            jres = ctx["res"] / f"b{b['i']:03d}.json"
            if a.resume and jres.exists():
                continue
            b2 = dict(b)
            b2["_sec_ctx"] = sctx
            tarefas.append((b2, sctx))
    print(f"curador5: {len(tarefas)} beats | âncora='{ancora5}' | v4 primeiro + fontes novas")

    def _nota_do_v4(r4, b2, sctx):
        """Dá ao candidato do v4 uma NOTA na mesma régua do pool novo (0-10 + bônus de
        tier). Vídeo é julgado por 1 frame do meio; imagem, por ela mesma."""
        arq = Path(r4["arquivo"])
        alvo = arq
        if arq.suffix.lower() in (".mp4", ".mov", ".webm"):
            frames = vg._frames_de_video(arq, ctx["tmp"], n=1)
            if not frames:
                return 6  # não deu pra amostrar: assume mediano (não pune o v4 à toa)
            alvo = frames[0]
        notas = batch_gate([{"path": str(alvo), "id": f"v4_{b2['i']}", "source": "v4"}],
                           b2.get("busca") or "", sctx, tema=ancora5)
        n = notas[0]["score"] if notas else -1
        return 6 if n < 0 else n  # gate mudo não condena o que o v4 já aprovou

    def _rodar5(par):
        """01/08 (QA cobras): a ordem "v4 primeiro, v5 só se o v4 falhar" fazia o v5
        NUNCA ser consultado — 38 dos 47 beats foram decididos pelo v4 sozinho, com
        gate BINÁRIO (o primeiro que passa, não o melhor). Era daí que vinham o
        "doctor writing notebook" e os diagramas técnicos num filme sobre cobras.

        Mas inverter a ordem reintroduziria o erro de 31/07 (stock genérico ganhando
        do YouTube real). Então nem uma coisa nem outra: o candidato do v4 entra no
        MESMO batch-score, com BÔNUS DE TIER. A hierarquia T3 continua valendo —
        footage real (T3) leva +2, CC/PD (T2) +1, stock (T1) 0 — mas um plano
        medíocre do v4 (nota 4) não ganha mais de uma foto certa nota 9."""
        b2, sctx = par
        if ancora5 and ancora5.split()[0].lower() not in (b2.get("busca") or "").lower():
            b2 = {**b2, "busca": f"{ancora5} {b2.get('busca') or ''}".strip()[:110]}
        _RESOLVER_V4 = {"footage_video": ex.resolver_footage_video,
                        "footage_imagem": ex.resolver_footage_imagem,
                        "ilustracao": ex.resolver_ilustracao}
        try:
            r4 = _RESOLVER_V4.get(b2.get("tipo"), ex.resolver_stock)(b2, ctx)
        except Exception as e4:
            print(f"  b{b2['i']:03d} v4 erro ({type(e4).__name__})")
            r4 = None
        if not (r4 and r4.get("status") == "ok" and r4.get("arquivo")
                and Path(r4["arquivo"]).exists()):
            r4 = None

        nota4 = -1
        if r4:
            try:
                nota4 = _nota_do_v4(r4, b2, sctx) + BONUS_TIER.get(int(r4.get("tier") or 1), 0)
            except Exception:
                nota4 = 6
            if nota4 >= NOTA_V4_OTIMA:   # v4 achou plano BOM: nem gasta pool novo
                return b2, {**r4, "score": nota4}, "v4"

        try:  # v4 fraco (ou vazio) -> o pool novo disputa a vaga
            r5 = resolver_beat5(b2, sctx, ctx, usados_urls, ancora5)
        except Exception as e5:
            print(f"  b{b2['i']:03d} v5 erro ({type(e5).__name__})")
            r5 = None
        nota5 = (r5 or {}).get("score", -1)
        if r5 and nota5 > nota4:
            if r4:  # o do v4 perdeu a disputa — não deixa lixo no assets/
                Path(r4["arquivo"]).unlink(missing_ok=True)
            return b2, r5, "v5"
        return b2, ({**r4, "score": nota4} if r4 else None), "v4"

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
