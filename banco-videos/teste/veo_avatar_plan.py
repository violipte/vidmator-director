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
# 06/08 (Piter): "o avatar aparecendo em cenas aleatórias como se fosse footage de
# REALITY, com alguém filmando ele caminhando, fazendo trilha". Estilo de série de
# sobrevivência — a diferença não está na ação, está na CÂMERA: ela é operada por
# alguém que anda junto, perde e reencontra o enquadramento. (O nome do programa de
# TV NUNCA entra no prompt — mesma política de "pessoa famosa" que derrubou takes.)
ACOES_REALITY = [
    "pushes through dense scrub on a rough trail across the {amb}, branches brushing "
    "past the lens as the operator follows a few steps behind",
    "climbs over a rocky outcrop in the {amb}, using one hand for balance, the camera "
    "operator scrambling up behind him and catching up at the top",
    "wades across a shallow creek in the {amb}, boots in the water, testing each step, "
    "handheld camera following from the bank",
    "stops on the trail, turns back toward the operator and points off into the {amb} "
    "before continuing on, run-and-gun handheld",
    "crouches to check a track in the dirt of the {amb}, the operator moving in close "
    "over his shoulder for the detail then pulling back out",
    "walks a ridgeline in the {amb} with the wind picking up, the camera lagging behind "
    "and swinging to catch him against the sky",
    "shoulders his pack and sets off along a dry riverbed in the {amb}, the operator "
    "walking backwards ahead of him, frame bouncing with the pace",
    "shelters under a rock overhang in the {amb} as light rain falls, catching his "
    "breath, camera handheld and close in the confined space",
]
_CAM_REALITY = ("Shot as observational survival-series field footage: single handheld "
                "operator on foot, natural camera shake, occasional quick reframe and "
                "refocus, no music, no interview setup")

# 05/08 (print do Piter: "Falha ao gerar áudio"): pedir o áudio por NEGAÇÃO
# ("does not speak, no narration") derruba o gerador de áudio. Enquadramento
# POSITIVO: descrever o que o ambiente SOA, e a ausência de fala vira consequência.
_SEM_FALA = ("Audio: gentle ambient sounds of the environment — birdsong, insects, "
             "soft wind and distant water. He works in comfortable silence, "
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
    # "observacional" (default, host trabalhando) | "reality" (câmera acompanha a trilha)
    reality = (av.get("estilo_presenca") or "observacional") == "reality"
    banco = ACOES_REALITY if reality else ACOES_PRESENCA
    cauda = f" {_CAM_REALITY}." if reality else ""
    for k, sec in enumerate(escolhidas):
        acao = banco[k % len(banco)].format(amb=amb) + cauda
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
