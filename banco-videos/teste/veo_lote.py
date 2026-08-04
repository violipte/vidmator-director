# -*- coding: utf-8 -*-
"""MODO GENERATIVO (v3-gen) — gera o LOTE de prompts do plano pro Flow.

MODO DE GERAÇÃO POR CANAL (01/08, pedido do Piter: "vários canais terão estilos de
visual diferente; quero canais só com vídeo, só com imagem ou misto"):
  style_card["gen_modo"] = "video"  -> TODO beat vira VEO (canal 100% movimento)
                           "imagem" -> TODO beat vira Nano Banana (o montador dá vida
                                       com Ken Burns semântico / parallax 2.5D)
                           "misto"  -> por tipo do beat (padrão; vídeo p/ footage,
                                       imagem p/ ilustração)
  style_card["gen_estilo"] = look do canal, ex.: "dark stoic documentary, candlelit
                             marble tones, anamorphic 35mm, muted contrast".
                             Sem isso, é derivado das mood_words.

Os prompts saem do `veo_prompt.dirigir()` (diretor de fotografia), NÃO da query de
busca crua — ver o cabeçalho de veo_prompt.py pro porquê.

Uso: python veo_lote.py --job <dir> --plano plano.json [--secao N] [--max N]
     [--modo video|imagem|misto]  (sobrepõe o style_card)
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from veo_prompt import dirigir  # noqa

sys.stdout.reconfigure(encoding="utf-8")

TIPOS_VIDEO = ("footage_video", "stock")
TIPOS_IMAGEM = ("ilustracao", "footage_imagem")


def _estilo_do_canal(sc):
    """Look do canal. `gen_estilo` é a fonte boa; mood_words são o fallback — e aí
    entram como GRADING (o diretor de fotografia sabe que não é objeto de cena)."""
    if sc.get("gen_estilo"):
        return str(sc["gen_estilo"])[:220]
    mood = ", ".join(sc.get("mood_words") or [])
    return (f"cinematic documentary, photorealistic, {mood}".strip(", ")
            if mood else "cinematic documentary, photorealistic, natural light")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--job", required=True)
    ap.add_argument("--plano", required=True)
    ap.add_argument("--secao", type=int, default=None, help="limita a uma seção")
    ap.add_argument("--max", type=int, default=0, help="limita o nº de prompts (piloto)")
    ap.add_argument("--modo", choices=["video", "imagem", "misto"], default=None,
                    help="sobrepõe o gen_modo do style_card")
    a = ap.parse_args()

    job = Path(a.job)
    plano = json.loads(Path(a.plano).read_text(encoding="utf-8"))
    sc = json.loads((job / "style_card.json").read_text(encoding="utf-8")) \
        if (job / "style_card.json").exists() else {}
    modo = a.modo or sc.get("gen_modo") or "misto"
    estilo = _estilo_do_canal(sc)
    tema = sc.get("assunto_ancora") or ""

    brutos = []
    for b in plano.get("beats", []):
        if a.secao is not None and b.get("secao") != a.secao:
            continue
        if not (b.get("busca") or "").strip():
            continue  # beat de animação: quem faz é o Remotion, não o Flow
        if modo == "video":
            midia = "video"
        elif modo == "imagem":
            midia = "imagem"
        elif b.get("tipo") in TIPOS_VIDEO:
            midia = "video"
        elif b.get("tipo") in TIPOS_IMAGEM:
            midia = "imagem"
        else:
            continue
        brutos.append({"i": b["i"], "t_ini": b.get("t_ini", 0), "t_fim": b.get("t_fim", 0),
                       "secao": b.get("secao", 0), "tipo": midia,
                       "busca": b.get("busca"), "texto": b.get("texto")})
        if a.max and len(brutos) >= a.max:
            break

    print(f"modo={modo} | estilo='{estilo[:60]}...' | dirigindo {len(brutos)} planos...")
    prompts = dirigir(brutos, estilo, tema=tema)

    lote = []
    for it, p in zip(brutos, prompts):
        ext = "mp4" if it["tipo"] == "video" else "jpg"
        lote.append({k: it[k] for k in ("i", "t_ini", "t_fim", "secao", "tipo")}
                    | {"arquivo": f"b{it['i']:03d}.{ext}", "prompt": p,
                       "busca_original": it.get("busca")})

    (job / "veo_lote.json").write_text(json.dumps(lote, ensure_ascii=False, indent=1),
                                       encoding="utf-8")
    md = [f"# Lote generativo — {job.name} · modo **{modo}** · {len(lote)} gerações", "",
          f"Look do canal: `{estilo}`", ""]
    for x in lote:
        md += [f"## {x['arquivo']} ({x['tipo']})", "```", x["prompt"], "```", ""]
    (job / "veo_lote.md").write_text("\n".join(md), encoding="utf-8")
    nv = sum(1 for x in lote if x["tipo"] == "video")
    print(f"lote: {len(lote)} prompts ({nv} VEO + {len(lote) - nv} Nano) -> {job / 'veo_lote.json'}")


if __name__ == "__main__":
    main()
