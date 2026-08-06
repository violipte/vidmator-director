# -*- coding: utf-8 -*-
"""PLANEJADOR DE TAKES DO AVATAR (05/08, desenho do Piter) — presença do host no vídeo.

"Alguns takes do avatar sempre ficam interessantes no meio do vídeo. Às vezes ele
andando ou fazendo alguma ação simples coerente com o ambiente, encaixado no vídeo,
uma variação entre 5~8 takes."

Gera o plano de takes do host pra QUALQUER canal com avatar:
  • 1 HOOK falado (fala 80-90 chars — teto aprovado: 122 corta, 69 arrasta, 89 natural)
  • takes de PRESENÇA silenciosa espalhados pelas seções: ação simples e coerente com
    o ambiente (andar, examinar, anotar). Áudio nativo = só o AMBIENTE — sem fala.
  • CTAs por formato (ranking: 1 no fim do 2º item mostrado + 1 no encerramento),
    com overlay clássico de YT por baixo (SubscribeBellPulse / SubscribeMinimal).

REGRAS DE POLÍTICA (aprendidas a caro em 05/08):
  • o NOME existe SÓ no chip do @ — `montar_prompt_avatar` troca nome por pronome e
    o driver apaga o resíduo que o "Incluir no comando" deixa no texto;
  • recusou ("pessoa famosa")? o ciclo reenvia com variação de cauda automática.

style_card["avatar"] (além de escopo/nome/voz/descricao):
  "takes_meio": 5,          # presença silenciosa (5-8; Piter)
  "cta_ranking": true,      # CTA meio+fim no formato ranking/top-N
  "ambiente": "rainforest riverbank"   # opcional; default derivado do gen_estilo

Uso: python veo_avatar_plan.py --job <dir> --plano <plano.json> [--aplicar]
Saída: <job>/_avatar_plan.json (lote pro veo_ciclo) + mapping de ilhas
(--aplicar grava as ilhas no style_card; sem ele, só mostra).
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.stdout.reconfigure(encoding="utf-8")
from veo_personagem import personagem_do_canal, montar_prompt_avatar  # noqa

# ações simples e AMBIENTE-COERENTES — sem fala; o áudio nativo vira o leito ASMR.
# {amb} = ambiente do canal. Variedade primeiro: nunca duas iguais no mesmo vídeo.
ACOES_PRESENCA = [
    "walks slowly along a narrow trail through the {amb}, looking around with quiet attention, gentle handheld follow",
    "crouches low to study animal tracks pressed in soft ground, then looks up across the {amb}, static tripod",
    "writes a few lines in a worn field notebook while standing in the {amb}, soft natural light, medium shot",
    "examines the underside of a large leaf with one hand, turning it toward the light in the {amb}, close medium shot",
    "stands still at the edge of the {amb}, scanning the distance, light wind moving the vegetation, wide shot",
    "steps carefully over roots and fallen branches deeper into the {amb}, camera tracking a few paces behind",
    "kneels at the water's edge and studies the surface for movement in the {amb}, low angle, static tripod",
    "adjusts the strap of a field bag and checks the sky before moving on through the {amb}, medium wide shot",
]
_SEM_FALA = ("Natural ambient sound only, he does not speak, no narration, "
             "unhurried observational pacing")


def planejar(job, plano, aplicar=False):
    job = Path(job)
    sc = json.loads((job / "style_card.json").read_text(encoding="utf-8"))
    av = sc.get("avatar") or {}
    canal = sc.get("canal") or ""
    ficha = personagem_do_canal(canal)
    if not ficha or av.get("escopo") == "nenhum":
        print("canal sem avatar — nada a planejar")
        return None
    estilo = (sc.get("gen_estilo") or "cinematic documentary, natural light")[:200]
    amb = av.get("ambiente") or "surrounding environment"
    n_meio = max(0, min(8, int(av.get("takes_meio", 5))))
    secoes = json.loads(Path(plano).read_text(encoding="utf-8")).get("secoes", [])
    if len(secoes) < 3:
        print("plano com poucas seções — planejador precisa de secoes[]")
        return None

    lote, ilhas = [], {}
    i_neg = -50

    # HOOK falado (seção 0) — a fala vem do style_card ou fica pro operador ajustar
    fala_hook = (av.get("fala_hook") or "").strip()
    if fala_hook:
        lote.append({"i": i_neg, "tipo": "video", "arquivo": "av_hook.mp4", "avatar": True,
                     "busca_original": "host hook take",
                     "prompt": montar_prompt_avatar(
                         ficha, f"stands facing the lens in the {amb}, speaking naturally "
                                f"at an easy pace, static tripod 35mm", estilo=estilo,
                         fala=fala_hook)})
        ilhas["0"] = "av_hook.mp4"
        i_neg -= 1

    # CTAs do formato ranking: meio (antes do antepenúltimo item) + encerramento
    if av.get("cta_ranking", True):
        sec_meio = str(secoes[len(secoes) // 2]["i"])
        sec_fim = str(secoes[-1]["i"])
        lote.append({"i": i_neg, "tipo": "video", "arquivo": "av_cta_meio.mp4", "avatar": True,
                     "busca_original": "host mid cta take",
                     "prompt": montar_prompt_avatar(
                         ficha, f"sits at rest in the {amb}, speaking warmly toward the lens, "
                                f"static tripod", estilo=estilo,
                         fala=av.get("fala_cta_meio") or
                         "If this is helping you, subscribe. It genuinely matters.")})
        ilhas[sec_meio] = {"clip": "av_cta_meio.mp4", "cta": "SubscribeBellPulse", "props": {}}
        i_neg -= 1
        lote.append({"i": i_neg, "tipo": "video", "arquivo": "av_cta_final.mp4", "avatar": True,
                     "busca_original": "host closing cta take",
                     "prompt": montar_prompt_avatar(
                         ficha, f"pauses in late golden light in the {amb}, gives a small nod "
                                f"toward the lens, static tripod", estilo=estilo,
                         fala=av.get("fala_cta_final") or
                         "If this taught you something, subscribe and ring the bell.")})
        ilhas[sec_fim] = {"clip": "av_cta_final.mp4", "cta": "SubscribeMinimal", "props": {}}
        i_neg -= 1

    # PRESENÇA silenciosa: distribui pelas seções que sobraram (sem hook/CTA)
    livres = [str(s["i"]) for s in secoes[1:-1] if str(s["i"]) not in ilhas]
    passo = max(1, len(livres) // max(1, n_meio))
    escolhidas = livres[::passo][:n_meio]
    for k, sec in enumerate(escolhidas):
        acao = ACOES_PRESENCA[k % len(ACOES_PRESENCA)].format(amb=amb)
        arq = f"av_meio_{k:02d}.mp4"
        lote.append({"i": i_neg, "tipo": "video", "arquivo": arq, "avatar": True,
                     "busca_original": f"host silent presence take {k}",
                     "prompt": montar_prompt_avatar(
                         ficha, f"{acao}. {_SEM_FALA}", estilo=estilo, fala="")})
        ilhas[sec] = arq
        i_neg -= 1

    out = job / "_avatar_plan.json"
    out.write_text(json.dumps(lote, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(lote)} takes -> {out.name}")
    print("ilhas:", json.dumps(ilhas, ensure_ascii=False))
    if aplicar:
        sc["avatar"]["ilhas"] = ilhas
        (job / "style_card.json").write_text(json.dumps(sc, ensure_ascii=False, indent=1),
                                             encoding="utf-8")
        print("ilhas gravadas no style_card")
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--job", required=True)
    ap.add_argument("--plano", required=True)
    ap.add_argument("--aplicar", action="store_true")
    a = ap.parse_args()
    planejar(a.job, a.plano, aplicar=a.aplicar)
