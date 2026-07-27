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
    """Frase de contexto pro gate — a REGRA DURA da seção."""
    lista = "; ".join(todos_produtos) or "none"
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

    secs = secoes_do_plano(plano, desamb)
    print(f"curador_footage: {len(secs)} seções | produtos: {todos}")

    out = {"beats": {}, "excedente": {}}
    for s, sec in sorted(secs.items()):
        sctx = ctx_da_secao(sec, todos)
        alvo_beats = [b for b in sec["beats"] if b.get("tipo") in ("footage_video", "stock")
                      and not ex.modelo_anunciado(b.get("texto"), {"desambiguacao": desamb})]  # anúncio = imagem (R-111)
        print(f"\n== seção {s} ({sec['produto'] or 'genérica'}): {len(alvo_beats)} beats de vídeo "
              f"+ {a.excedente} excedentes ==")
        for b in alvo_beats:
            b2 = dict(b)
            b2["_sec_ctx"] = sctx
            r = ex.resolver_footage_video(b2, ctx) if b.get("tipo") == "footage_video" \
                else ex.resolver_stock(b2, ctx)
            if r.get("status") == "ok" and r.get("arquivo"):
                out["beats"][str(b["i"])] = {"arquivo": r["arquivo"], "tier": r.get("tier", 1),
                                             "fonte": r.get("fonte"), "watermark": bool(r.get("watermark"))}
                # formato do executor: o resume pula beats já curados
                (ctx["res"] / f"b{b['i']:03d}.json").write_text(
                    json.dumps({**{k: b.get(k) for k in ("i", "secao", "t_ini", "t_fim", "busca")},
                                **r, "tipo": b.get("tipo")}, ensure_ascii=False), encoding="utf-8")
                print(f"  b{b['i']:03d} OK {Path(r['arquivo']).name[-40:]}")
            else:
                print(f"  b{b['i']:03d} BURACO (sem clipe aprovado) — animador vai acusar")
        # EXCEDENTE da seção: buscas derivadas do assunto (bg/duo/split do animador)
        out["excedente"][str(s)] = []
        base_busca = sec["produto"] or (sec["titulo"] or "senior runner training")
        for k in range(a.excedente):
            fake = {"i": 900 + s * 10 + k, "tipo": "stock", "secao": s,
                    "busca": f"{base_busca} b-roll closeup" if k == 0 else f"{base_busca} action shot",
                    "_sec_ctx": sctx, "t_ini": 0, "t_fim": 5}
            r = ex.resolver_stock(fake, ctx)
            if r.get("status") == "ok" and r.get("arquivo"):
                out["excedente"][str(s)].append({"arquivo": r["arquivo"], "tier": r.get("tier", 1),
                                                 "watermark": bool(r.get("watermark"))})
                print(f"  excedente {k+1} OK {Path(r['arquivo']).name[-40:]}")

    (job / "curadoria_footage.json").write_text(json.dumps(out, ensure_ascii=False, indent=1),
                                                encoding="utf-8")
    n_ok = len(out["beats"])
    n_exc = sum(len(v) for v in out["excedente"].values())
    print(f"\n=== CURADORIA: {n_ok} beats + {n_exc} excedentes -> {job / 'curadoria_footage.json'} ===")


if __name__ == "__main__":
    main()
