# -*- coding: utf-8 -*-
"""FUNCIONÁRIO 2 — CURADOR DE FOOTAGE (ARQUITETURA_FUNCIONARIOS.md, 25/07).

Trabalha POR SEÇÃO, nunca por beat solto. Pra cada seção:
- assunto (produto da desambiguacao ou tema genérico) e REGRA DURA:
  * seção de produto: todo clipe mostra O produto OU é brand-neutro;
  * "a shoe is visible but it is NOT the section's product" => REJEITA;
  * marca fora da lista do vídeo NUNCA passa (em NENHUMA seção).
- resolve os beats de vídeo da seção + EXCEDENTE (2 clipes extras por seção
  pra bg/duo/split/reserva do animador — fim do demote cego).

Reusa a infra do executor_beats (busca/download/normalização/gate) com o
contexto de seção injetado via beat["_sec_ctx"] (subject_do_beat).

Uso: python curador_footage.py --job <dir> --plano plano.json [--excedente 2]
Output: <job>/curadoria_footage.json  {"beats": {i: arquivo}, "excedente": {sec: [...]}}
"""
import argparse
import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).parent))
import executor_beats as ex  # noqa — infra de busca/gate/download


def secoes_do_plano(plano, desamb):
    """Mapeia secao -> {produto, beats_video, titulo}. Produto = chave da desambiguacao
    no texto de QUALQUER beat da seção (o anúncio nomeia; o resto herda)."""
    secs = {}
    for b in plano.get("beats", []):
        s = b.get("secao", 0)
        secs.setdefault(s, {"produto": None, "beats": [], "titulo": ""})
        secs[s]["beats"].append(b)
        tl = (b.get("texto") or "").lower()
        for k, v in desamb.items():
            if k.lower() in tl and re.search(r"\bnumber\s+(one|two|three|four|five|\d)", tl):
                secs[s]["produto"] = v  # o ANÚNCIO define o produto da seção
    for s0 in plano.get("secoes", []):
        if s0.get("i") in secs:
            secs[s0["i"]]["titulo"] = s0.get("titulo") or ""
    return secs


def ctx_da_secao(sec, todos_produtos):
    """Frase de contexto pro gate — a REGRA DURA da seção.
    27/07: nicho SEM announce (estoico) não tem "produtos" — a desambiguacao é
    ilustração de pessoas, não catálogo. Tratar bustos como produto concorrente
    travou o gate (0/288 no banco)."""
    lista = "; ".join(todos_produtos) or "none"
    if not sec.get("produto") and not todos_produtos:
        return ("Crash/accident/injury or CCTV footage = subject_match=false. "
                "A person presenting/talking toward the camera (vlogger, host, channel intro) = "
                "talking_head=true even in a wide shot. "
                "SECTION CONTEXT: thematic documentary B-ROLL. subject_match=true if the frames "
                "match the search subject OR its mood/atmosphere (statues, ruins, nature, objects, "
                "silhouettes are all fine). Reject only clearly unrelated or off-mood content. "
                "There are NO product/brand constraints in this video.")
    base = ("IMPORTANT: 'bike' in this video ALWAYS means pedal BICYCLE — any motorcycle, moped or "
            "scooter content (engine, exhaust, throttle, speedometer dial) = subject_match=false. "
            "Crash/accident/injury or CCTV footage = subject_match=false. ") \
        if any("bike" in p.lower() for p in todos_produtos) else \
        "Crash/accident/injury or CCTV footage = subject_match=false. "
    base += ("A person presenting/talking toward the camera (vlogger, host in a garden/workshop, "
             "channel intro with title text) = talking_head=true even in a wide shot. ")
    if sec["produto"]:
        return (base + f"SECTION CONTEXT: this segment is specifically about the {sec['produto']}. "
                f"The video covers ONLY these products: {lista}. "
                f"If a competing product is prominently visible and it is clearly NOT the {sec['produto']} "
                f"(different brand or model), subject_match=false. "
                f"A brand that is not in the list above must NEVER appear legible.")
    return (base + f"SECTION CONTEXT: general segment of a video that covers ONLY these products: {lista}. "
            f"Neutral footage of people/roads/scenery is fine, but a SPECIFIC competing product from a "
            f"brand outside the list, prominent and identifiable, = subject_match=false.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--job", required=True)
    ap.add_argument("--plano", required=True)
    ap.add_argument("--excedente", type=int, default=2)
    ap.add_argument("--banco", type=int, default=0,
                    help="clipes extras do BANCO DE NICHO (queries_banco do style_card) — mata a repetição")
    ap.add_argument("--workers", type=int, default=6, help="buscas/gates em paralelo (27/07)")
    ap.add_argument("--resume", action="store_true",
                    help="pula beats/banco que já têm resolvido/bNNN.json (não refaz trabalho)")
    a = ap.parse_args()

    job = Path(a.job)
    plano = json.loads(Path(a.plano).read_text(encoding="utf-8"))
    sc = {}
    if (job / "style_card.json").exists():
        sc = json.loads((job / "style_card.json").read_text(encoding="utf-8"))
    desamb = sc.get("desambiguacao") or {}
    todos = sorted(set(desamb.values()))

    ctx = {"assets": job / "assets", "tmp": job / "_tmp", "res": job / "resolvido"}
    for d in ctx.values():
        d.mkdir(parents=True, exist_ok=True)

    # blacklist + resume (mesma disciplina do executor)
    bl = job / "blacklist.txt"
    if bl.exists():
        for ln in bl.read_text(encoding="utf-8").splitlines():
            sid = ln.strip()
            if sid:
                ex.USED.add(sid), ex.USED.add(f"pexv_{sid}"), ex.USED.add(f"pexp_{sid}")
    cb = job / "canais_banidos.txt"  # 27/07: ban de canal vale no CURADOR também
    if cb.exists():
        for ln in cb.read_text(encoding="utf-8").splitlines():
            if ln.strip():
                ex.CANAIS_BAN.add(ln.strip().lower())
        print(f"canais banidos (curador): {len(ex.CANAIS_BAN)}")

    # RESUME: semeia USED com o que JÁ está no job (mesma disciplina do executor main).
    # Sem isso o banco re-baixa os mesmos pexels/yt e o dedup mata um a um (0/18, 27/07).
    if a.resume:
        n_seed = 0
        for f in list(ctx["res"].glob("b*.json")) + list(ctx["assets"].glob("*.*")):
            arq = f.name
            if f.suffix == ".json":
                try:
                    arq = json.loads(f.read_text(encoding="utf-8")).get("arquivo") or ""
                except Exception:
                    continue
            m = re.search(r"__(?:yt|pexels)_([A-Za-z0-9_-]+)\.", arq)
            if m:
                sid = m.group(1)
                ex.USED.add(sid), ex.USED.add(f"pexv_{sid}"), ex.USED.add(f"pexp_{sid}")
                n_seed += 1
        print(f"USED semeado do job (resume): {n_seed} ids")

    secs = secoes_do_plano(plano, desamb)
    # nicho sem announce (nenhuma seção com produto) => desambiguacao NÃO é catálogo
    # de produtos; ctx vira b-roll temático (fix 0/288 estoico 27/07)
    if not any(sec["produto"] for sec in secs.values()):
        todos = []
    print(f"curador_footage: {len(secs)} seções | produtos: {todos or 'nenhum (b-roll temático)'}")

    out = {"beats": {}, "excedente": {}}
    tarefas = []  # (tipo_tarefa, beat_enriquecido, secao)
    for s, sec in sorted(secs.items()):
        sctx = ctx_da_secao(sec, todos)
        alvo_beats = [b for b in sec["beats"] if b.get("tipo") in ("footage_video", "stock")
                      and not ex.modelo_anunciado(b.get("texto"), {"desambiguacao": desamb})]  # anúncio = imagem (R-111)
        print(f"== seção {s} ({sec['produto'] or 'genérica'}): {len(alvo_beats)} beats de vídeo "
              f"+ {a.excedente} excedentes ==")
        for b in alvo_beats:
            jres = ctx["res"] / f"b{b['i']:03d}.json"
            if a.resume and jres.exists():
                try:
                    r0 = json.loads(jres.read_text(encoding="utf-8"))
                    if r0.get("arquivo") and Path(r0["arquivo"]).exists():
                        out["beats"][str(b["i"])] = {"arquivo": r0["arquivo"], "tier": r0.get("tier", 1),
                                                     "fonte": r0.get("fonte"),
                                                     "watermark": bool(r0.get("watermark"))}
                        continue  # resume: já curado, não refaz
                except Exception:
                    pass
            b2 = dict(b)
            b2["_sec_ctx"] = sctx
            tarefas.append(("beat", b2, s))
        base_busca = sec["produto"] or (sec["titulo"] or "b-roll")
        out["excedente"][str(s)] = []
        for k in range(a.excedente):
            fake = {"i": 900 + s * 10 + k, "tipo": "stock", "secao": s,
                    "busca": f"{base_busca} b-roll closeup" if k == 0 else f"{base_busca} action shot",
                    "_sec_ctx": sctx, "t_ini": 0, "t_fim": 5}
            tarefas.append(("excedente", fake, s))

    def _rodar(t):
        tipo_t, b2, s = t
        r = ex.resolver_footage_video(b2, ctx) if b2.get("tipo") == "footage_video" \
            else ex.resolver_stock(b2, ctx)
        return tipo_t, b2, s, r

    # PARALELO (27/07 — Piter: "dá pra paralelizar?"): buscas+gates simultâneos
    with ThreadPoolExecutor(max_workers=a.workers) as pool:
        for tipo_t, b2, s, r in pool.map(_rodar, tarefas):
            if r.get("status") == "ok" and r.get("arquivo"):
                if tipo_t == "beat":
                    out["beats"][str(b2["i"])] = {"arquivo": r["arquivo"], "tier": r.get("tier", 1),
                                                  "fonte": r.get("fonte"), "watermark": bool(r.get("watermark"))}
                    (ctx["res"] / f"b{b2['i']:03d}.json").write_text(
                        json.dumps({**{k: b2.get(k) for k in ("i", "secao", "t_ini", "t_fim", "busca")},
                                    **r, "tipo": b2.get("tipo")}, ensure_ascii=False), encoding="utf-8")
                    print(f"  b{b2['i']:03d} OK {Path(r['arquivo']).name[-40:]}")
                else:
                    out["excedente"][str(s)].append({"arquivo": r["arquivo"], "tier": r.get("tier", 1),
                                                     "watermark": bool(r.get("watermark"))})
                    print(f"  excedente s{s} OK {Path(r['arquivo']).name[-40:]}")
            elif tipo_t == "beat":
                print(f"  b{b2['i']:03d} BURACO (sem clipe aprovado) — animador vai acusar")

    # BANCO DE NICHO (27/07 — "tem MUITO clipe repetido"): enche o pool com clipes
    # temáticos variados; com abundância, reuso vira exceção natural do sort por uso
    if a.banco > 0:
        qs = sc.get("queries_banco") or []
        sctx_banco = ctx_da_secao({"produto": None, "titulo": ""}, todos)

        # sufixo por ciclo: mesma query re-buscada devolve a MESMA lista (determinística);
        # variar o texto abre resultados novos em vez de re-tentar os USED
        _SUF = ["", " cinematic", " slow motion", " dark moody", " closeup", " night",
                " aerial", " 4k film"]

        def _banco_task(kk):
            ciclo = kk // len(qs)
            q = qs[kk % len(qs)] + _SUF[ciclo % len(_SUF)]
            fake = {"i": 800 + kk, "tipo": "stock", "secao": 900,
                    "busca": q, "t_ini": 0, "t_fim": 5, "_sec_ctx": sctx_banco}
            return kk, q, ex.resolver_stock(fake, ctx)

        # ondas paralelas: cada onda = a.workers tentativas simultâneas; pode passar
        # 1-2 do alvo (bom — banco maior = menos repetição)
        n_ok_banco = 0
        k = 0
        if a.resume:  # banco já parcialmente feito: conta os existentes e continua depois deles
            feitos = sorted(int(f.stem[1:]) for f in ctx["res"].glob("b8*.json")
                            if f.stem[1:].isdigit() and int(f.stem[1:]) >= 800)
            if feitos:
                n_ok_banco = len(feitos)
                k = feitos[-1] - 800 + 1
                print(f"  banco resume: {n_ok_banco} existentes, continuando de k={k}")
        with ThreadPoolExecutor(max_workers=a.workers) as pool:
            while n_ok_banco < a.banco and k < a.banco * 8 and qs:
                lote = range(k, min(k + a.workers, a.banco * 8))
                for kk, q, r in pool.map(_banco_task, lote):
                    if r.get("status") == "ok" and r.get("arquivo"):
                        (ctx["res"] / f"b{800 + kk:03d}.json").write_text(
                            json.dumps({"i": 800 + kk, "secao": 900, "t_ini": 0, "t_fim": 5,
                                        "busca": q, **r, "tipo": "stock"},
                                       ensure_ascii=False), encoding="utf-8")
                        n_ok_banco += 1
                print(f"  banco: {n_ok_banco}/{a.banco} (tentativas {min(k + a.workers, a.banco * 8)})")
                k += a.workers
        print(f"banco de nicho: {n_ok_banco} clipes")

    (job / "curadoria_footage.json").write_text(json.dumps(out, ensure_ascii=False, indent=1),
                                                encoding="utf-8")
    n_ok = len(out["beats"])
    n_exc = sum(len(v) for v in out["excedente"].values())
    print(f"\n=== CURADORIA: {n_ok} beats + {n_exc} excedentes -> {job / 'curadoria_footage.json'} ===")


if __name__ == "__main__":
    main()
