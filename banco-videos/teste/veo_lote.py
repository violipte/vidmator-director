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
    ap.add_argument("--alvo-video", type=float, default=0.45,
                    help="piso da fatia de VÍDEO no misto (0.45 = ~45%%)")
    ap.add_argument("--sem-reclass", action="store_true",
                    help="não reclassifica vídeo->imagem por movimento (misto)")
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

    # RECLASSIFICAÇÃO POR MOVIMENTO (05/08, Piter). No misto, a divisão herdava a
    # lógica da era da BUSCA (footage->vídeo, ilustração->imagem) e 84% do lote caía
    # na fila lenta do VEO — inclusive "stingray RESTING on the riverbed". A régua
    # certa pra GERAÇÃO é outra: vídeo SÓ quando o movimento do sujeito é a história;
    # o resto vira still (mais nítido, instantâneo, 0 créd) e ganha movimento na
    # montagem (Ken Burns semântico / parallax). Quem já tem .mp4 no assets não muda.
    if modo == "misto" and not a.sem_reclass:
        from veo_prompt import pontuar_movimento
        cands = [b for b in brutos if b["tipo"] == "video"
                 and not (job / "assets" / f"b{b['i']:03d}.mp4").exists()]
        if cands:
            notas = pontuar_movimento(cands)
            # O LLM ORDENA; o CORTE e' nosso (06/08). A regua ~50/50 do Piter virou
            # controle daqui porque pedir a DECISAO ao modelo deixava o desempate da
            # rubrica mandar: 18% de video no 1o lote da Australia.
            #   nota <=2  NUNCA vira video (diagrama/mapa/estrutura ou caos ilegivel)
            #   nota >=8  SEMPRE video (o movimento E' a cena), mesmo passando do alvo
            #   3..7      preenche por ordem de nota ate bater o alvo
            alvo = max(0.0, min(1.0, a.alvo_video))
            _ids = {id(c) for c in cands}
            # desconta so' o que JA' e' video fora dos candidatos (mp4 no assets) —
            # os outros nao-candidatos sao imagem e nao entram na conta
            ja_video = sum(1 for b in brutos if b["tipo"] == "video" and id(b) not in _ids)
            n_alvo = int(round(len(brutos) * alvo)) - ja_video
            fixos = [b for b, n in zip(cands, notas) if n >= 8]
            meio = sorted([(n, k) for k, (b, n) in enumerate(zip(cands, notas))
                           if 3 <= n <= 7], key=lambda x: -x[0])
            escolhidos = {id(b) for b in fixos}
            for _n, k in meio:
                if len(escolhidos) >= n_alvo:
                    break
                escolhidos.add(id(cands[k]))
            for b in cands:
                b["tipo"] = "video" if id(b) in escolhidos else "imagem"
            n_v = sum(1 for b in brutos if b["tipo"] == "video")
            print(f"movimento: {len(fixos)} obrigatorios (nota>=8) + "
                  f"{len(escolhidos) - len(fixos)} por alvo | mix final "
                  f"{n_v}/{len(brutos)} video ({n_v / len(brutos):.0%})")

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
