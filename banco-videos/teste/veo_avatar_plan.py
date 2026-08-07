# -*- coding: utf-8 -*-
"""PLANEJADOR DE TAKES DO AVATAR — presença do host no vídeo.

FORMATO DEFINIDO PELO PITER EM 06/08 (depois do QA do vídeo da Austrália):
o host aparece em TRÊS lugares, e só:

  1. ABERTURA        — introduz o vídeo
  2. CTA DO MEIO     — entre o fim do capítulo 2 e o CARD do capítulo 3
                       (tem que vir ANTES do card, não depois)
  3. CTA FINAL       — o ÚLTIMO clipe do vídeo, se despedindo

O que saiu: as 5-8 "presenças silenciosas" espalhadas pelo meio. Ficaram fora de
contexto ("aparece o host andando e atravessando um galho, sem áudio nem função —
quando sugeri ele aparecer nos clipes, não foi nesse sentido"). O resto do vídeo é
só ilustração do assunto.

⚠️ TAKES SÃO GERADOS EM SILÊNCIO E DUBLADOS (06/08, decisão do plano B).
Prova que forçou a mudança — STT dos takes crus do 1º corte:
    av_hook      -> "...Subscribe so you don't miss it. Travis Arewa."
    av_cta_final -> "...subscribe and ring the bell. TraviSero."
"Travis Arewa"/"TraviSero" = o VEO PRONUNCIANDO O NOME DO CHIP. Mesmo com o nome
fora do texto do prompt, o gerador de áudio lê o nome do personagem em voz alta —
renomear não resolve, só troca a palavra estranha. Além disso o casamento por
título colocou a fala do CTA dentro do slot da abertura.
Gerando MUDO e dublando com a voz clonada (Chatterbox, a MESMA da narração):
nome nunca é falado, fala nunca sai trocada, texto exato, e a voz do host passa a
ser idêntica à da narração em vez de só parecida.

style_card["avatar"]:
  "fala_hook", "fala_cta_meio", "fala_cta_final"   (texto que será DUBLADO)
  "ambiente": "australian bushland"
  "cta_ranking": true   (mantém os 2 CTAs; false = só a abertura)

Uso: python veo_avatar_plan.py --job <dir> --plano <plano.json> [--aplicar]
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.stdout.reconfigure(encoding="utf-8")
from veo_personagem import personagem_do_canal, montar_prompt_avatar  # noqa

# O take é MUDO: pedimos o ambiente, nunca a fala. Enquadramento POSITIVO — pedir
# por negação ("does not speak") derruba o gerador de áudio (05/08).
_AMBIENTE = ("Audio: only the natural ambience of the place — wind in the trees, "
             "distant birds, quiet air")
# 06/08 (QA do Piter): "tem uma câmera de fundo" — o VEO põe tripé/câmera em quadro
# quando o prompt cheira a set de filmagem. Pedir explicitamente que não haja.
_SEM_SET = ("No camera, no tripod, no microphone, no filming equipment anywhere in "
            "frame. Just the person and the landscape")
# 06/08 (QA): o take saiu num RIO BARRENTO DE SELVA mesmo pedindo "australian
# bushland" — o VEO reproduz o fundo do RETRATO do personagem (criado na Amazônia)
# quando o ambiente vem genérico. Descrever o lugar com substantivos concretos, e
# repetir a âncora no fim do prompt, faz o cenário obedecer.
def _ancora(amb):
    return f"The setting is unmistakably {amb}"


# 06/08 (Piter, e é óbvio quando dito): "coloca ele no ambiente do qual está fazendo
# o vídeo, com as roupas adequadas ao ambiente e o local". O host estava de camisa de
# campo amazônica à beira de um rio de selva num vídeo sobre a Austrália — o problema
# nunca foi o modelo teimoso, foi a FICHA errada pro vídeo. Ambiente e FIGURINO passam
# a vir do style_card DESTE vídeo, não do cadastro fixo do canal. (A tentativa
# anterior — esconder tudo num close — tratava o sintoma.)
_ENQUADRA = ("Medium shot, chest up, the location clearly readable behind him")


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
    figurino = (av.get("figurino") or "").strip()
    modo = (av.get("modo") or "insercao").strip()
    secoes = json.loads(Path(plano).read_text(encoding="utf-8")).get("secoes", [])
    if len(secoes) < 3:
        print("plano com poucas seções — planejador precisa de secoes[]")
        return None

    lote, ilhas = [], {}
    i_neg = -50

    def _take(arquivo, acao, fala, secao, cta=None, antes_do_card=False, ultimo=False):
        """Um take do host. Dois modos, conforme `avatar.modo`:

        "insercao" (padrão a partir de 06/08, desenho do Piter) — o VEO gera COM
          fala (lábios batem), a fala é EXCLUSIVA do host (o roteiro narrado não a
          contém) e a ilha ACRESCENTA tempo ao vídeo. O `veo_gate_fala` confere por
          STT que o take diz exatamente a frase e regera se sobrar sujeira.
        "dublagem" — take mudo + voz clonada por cima. Sem risco de o VEO falar o
          nome do chip, mas os lábios não batem. Serve pra nicho onde o host é só
          presença; não serve pra canal onde ele apresenta de verdade.
        """
        nonlocal i_neg
        corpo = (f"{acao}. {('Wearing ' + figurino + '. ') if figurino else ''}"
                 f"{_ENQUADRA}. {_ancora(amb)}. {_SEM_SET}")
        if modo != "insercao":
            corpo += f". {_AMBIENTE}"
        lote.append({"i": i_neg, "tipo": "video", "arquivo": arquivo, "avatar": True,
                     "busca_original": f"host take {arquivo}",
                     "prompt": montar_prompt_avatar(
                         ficha, corpo, estilo=estilo,
                         fala=(fala if modo == "insercao" else ""))})
        i_neg -= 1
        ilha = ({"clip": arquivo, "fala": fala, "inserir": True}
                if modo == "insercao" else {"clip": arquivo, "dub": fala})
        if cta:
            ilha["cta"] = cta
            ilha["props"] = {}
        if antes_do_card:
            ilha["antes_do_card"] = True
        if ultimo:
            ilha["ultimo_clipe"] = True
        ilhas[str(secao)] = ilha

    # 07/08 (QA Piter: "o avatar com CTA no final ficou igual da intro"): as três
    # aparições precisam ser VISUALMENTE distintas. Escrever "stands facing the lens"
    # na abertura e "stands in late golden light" no fecho entregava o mesmo
    # enquadramento — o VEO não separa cenas por adjetivo de luz. O que separa é
    # POSTURA + DISTÂNCIA + HORA DO DIA, e isso agora é explícito em cada take.

    # 1. ABERTURA — de pé, plano médio, luz dura do meio-dia
    fala_hook = (av.get("fala_hook") or "").strip()
    if fala_hook:
        _take("av_hook.mp4",
              f"stands upright in the middle of the {amb} under hard midday sun, "
              f"medium shot from the chest up, talking straight to the lens with "
              f"small natural hand gestures",
              fala_hook, secoes[0]["i"])

    if av.get("cta_ranking", True):
        # 2. CTA DO MEIO — ANTES do card do 3º ITEM DA CONTAGEM (Piter: "depois que
        #    termina o 02, antes de aparecer a animação do 03").
        #    06/08: era `secoes[len//2]`, que na Austrália calhou de ser o 3º item por
        #    acidente (2 seções de intro) e na África cairia no #2 — o meio da LISTA
        #    DE SEÇÕES não é o meio da CONTAGEM. Achar os itens pelo "#N" do título e
        #    pegar o TERCEIRO é a regra que o Piter descreveu, sem depender de quantas
        #    seções de abertura o roteiro tem.
        import re as _re
        itens = [s for s in secoes if _re.search(r"#\s*\d", str(s.get("titulo") or ""))]
        sec_meio = (itens[2] if len(itens) >= 3 else secoes[len(secoes) // 2])["i"]
        # 2. CTA MEIO — SENTADO, plano mais aberto, fim de tarde
        _take("av_cta_meio.mp4",
              f"sits low on a rock in the {amb} in warm late-afternoon light, wider "
              f"shot showing the landscape around him, leaning forward with elbows on "
              f"his knees as he turns to the lens",
              (av.get("fala_cta_meio") or
               "Before the next one on our list, subscribe, like and hit the bell."),
              sec_meio, cta="SubscribeBellPulse", antes_do_card=True)

        # 3. CTA FINAL — o ÚLTIMO clipe do vídeo
        sec_fim = secoes[-1]["i"]
        # 3. CTA FINAL — CAMINHANDO em direção à câmera, close, contraluz do pôr do sol
        _take("av_cta_final.mp4",
              f"walks slowly toward the camera through the {amb} at sunset, backlit "
              f"with the low sun behind him, close shot from the shoulders up, "
              f"raising one hand in a goodbye wave as he stops",
              (av.get("fala_cta_final") or
               "Thanks for watching. Subscribe, and I'll see you next time."),
              sec_fim, cta="SubscribeMinimal", ultimo=True)

    out = job / "_avatar_plan.json"
    out.write_text(json.dumps(lote, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(lote)} takes [modo={modo}] -> {out.name}")
    for k, v in ilhas.items():
        marca = "ANTES DO CARD" if v.get("antes_do_card") else (
            "ÚLTIMO CLIPE" if v.get("ultimo_clipe") else "abertura")
        txt = v.get("fala") or v.get("dub") or ""
        print(f"  seção {k}: {v['clip']:<18} [{marca}] {txt[:50]!r}")
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
