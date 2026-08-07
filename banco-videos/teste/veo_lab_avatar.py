# -*- coding: utf-8 -*-
"""LABORATÓRIO DO AVATAR (07/08) — testar a fala do host SEM renderizar vídeo.

Piter, 07/08: "vamos praticar somente a geração do avatar até masterizar esse
processo e não ficar regenerando um vídeo longo o tempo todo."

Regenerar 8 minutos de vídeo pra avaliar 8 segundos de host consumiu uma tarde
inteira. Aqui o ciclo é: monta N VARIANTES de prompt para a MESMA fala, gera todas
na mesma rodada, transcreve cada take e diz qual variante o VEO obedeceu. O
resultado é uma tabela de qual FORMA DE PEDIR funciona — que é o conhecimento que
falta, não mais um vídeo.

Variantes em teste (hipóteses do caderno de 06/08):
  curto      só o essencial: chip + "says" + fala + enquadramento. Sem cenário,
             sem figurino, sem estilo. (hipótese principal: descrição longa
             COMPETE com a instrução de fala)
  completo   o prompt de produção de hoje (cenário + figurino + estilo)
  dobrado    a fala aparece DUAS vezes, no início e no fim
  imperativo  "Dialogue (exact words he speaks aloud): ..." em vez de "says"

Uso:
  python veo_lab_avatar.py --job <dir> --montar          # escreve o lote
  python veo_lab_avatar.py --job <dir> --avaliar <zip>   # transcreve e tabela
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.stdout.reconfigure(encoding="utf-8")
from veo_personagem import personagem_do_canal  # noqa: E402

# enquadramentos distintos por PAPEL (07/08, QA: "o CTA final ficou igual da intro")
PAPEIS = {
    "hook": "stands upright facing the lens, medium shot from the chest up",
    "meio": "sits low on a rock, wider shot with the sea behind him",
    "final": "walks toward the camera and stops, close shot from the shoulders up",
}

# ⚠️ CADA VARIANTE PRECISA DE UMA FRASE PRÓPRIA (07/08, 1ª rodada do lab).
# Com as 4 variantes dizendo a MESMA frase, um erro de casamento por título torna o
# resultado inatribuível: o take de "hook/completo" veio falando a linha do CTA e o
# placar virou ruído de casamento, não obediência. Frases distintas fazem a própria
# TRANSCRIÇÃO identificar qual prompt gerou qual clipe — sem depender do título.
FALAS = {
    "hook": [
        "Sharks kill around ten people a year. We kill a hundred million sharks in that same year.",
        "Five hundred shark species swim this ocean and almost none of them care that you exist.",
        "The shark that bites the most people is not the one that kills them, and that matters.",
        "Everything you fear about sharks is true. It is also almost never pointed at a human.",
    ],
    "meio": [
        "Before we get to the next one on this list, take a second to subscribe, hit the like button and ring the bell.",
        "We are halfway down the list now. Hit subscribe so the next one finds you when it lands.",
        "Two left, and they are the serious ones. Subscribe and turn the bell on before we carry on.",
        "If this is holding your attention, subscribe. It genuinely helps this channel keep going.",
    ],
    "final": [
        "Thanks for watching. Hit subscribe for more, and I will see you out on the water again.",
        "That is the list. Subscribe if you want the next one, and I will see you out here soon.",
        "Thanks for staying to the end. Subscribe, and I will see you on the next one out here.",
        "That is all five of them. Hit subscribe for more, and I will see you on the next dive.",
    ],
}


def _variantes(ficha, papel, acao, fala, amb, figurino, estilo):
    m = ficha["mencao"]
    f = fala.strip()
    return {
        # 1. CURTO — a hipótese principal
        "curto": f'{m} says, word for word: "{f}" — {acao}. Clean frame, no subtitles',
        # 2. COMPLETO — o que a produção usa hoje
        "completo": (f'{m} says, word for word: "{f}". While saying it, he {acao} in the '
                     f'{amb}. Wearing {figurino}. {estilo}. Clean frame, no subtitles, '
                     f'no captions, no burned-in text'),
        # 3. DOBRADO — fala no começo E no fim
        "dobrado": (f'{m} speaks these exact words: "{f}" — {acao} in the {amb}. '
                    f'Clean frame, no subtitles. Spoken line, verbatim: "{f}"'),
        # 4. IMPERATIVO — rótulo de roteiro em vez de verbo narrativo
        "imperativo": (f'{m} {acao} in the {amb}. Clean frame, no subtitles. '
                       f'Dialogue (the exact words he speaks aloud, nothing else): "{f}"'),
    }


def montar(job):
    job = Path(job)
    sc = json.loads((job / "style_card.json").read_text(encoding="utf-8"))
    av = sc["avatar"]
    ficha = personagem_do_canal(sc.get("canal") or "")
    amb = av.get("ambiente", "")
    fig = av.get("figurino", "")
    est = (sc.get("gen_estilo") or "")[:120]
    lote, mapa = [], {}
    i = -100
    for papel, acao in PAPEIS.items():
        for k, (nome_v, _) in enumerate(_variantes(ficha, papel, acao, "x", amb, fig, est).items()):
            fala = FALAS[papel][k % len(FALAS[papel])]
            prompt = _variantes(ficha, papel, acao, fala, amb, fig, est)[nome_v]
            arq = f"lab_{papel}_{nome_v}.mp4"
            lote.append({"i": i, "tipo": "video", "arquivo": arq, "avatar": True,
                         "busca_original": f"host {papel} {nome_v}",
                         "prompt": prompt[:900]})
            mapa[arq] = {"papel": papel, "variante": nome_v, "fala": fala}
            i -= 1
    (job / "_lab_lote.json").write_text(json.dumps(lote, ensure_ascii=False, indent=1),
                                        encoding="utf-8")
    (job / "_lab_mapa.json").write_text(json.dumps(mapa, ensure_ascii=False, indent=1),
                                        encoding="utf-8")
    print(f"{len(lote)} takes = {len(PAPEIS)} papéis x {len(_variantes(ficha,'x','y','z','','',''))} variantes")
    for a_, m_ in mapa.items():
        print(f"  {a_:<28} {m_['papel']:<6} {m_['variante']}")
    print(f"\nlote -> {job / '_lab_lote.json'}")


def avaliar(job, pasta_zip, limite=200, desde=""):
    """Transcreve TODOS os clipes de host e atribui cada um pela FALA.

    07/08 (2ª versão): a 1ª casava por título e só depois transcrevia — mas o título
    do Flow não distingue variantes, e o placar virou ruído. Agora a atribuição é
    pelo CONTEÚDO: cada variante tem frase própria, então o que o clipe DIZ revela
    qual prompt o gerou. Título e carimbo saem do circuito.
    """
    from veo_gate_fala import transcrever_take, avaliar as _av, _palavras
    from veo_zip import _tokens, _PESSOA_TITULO
    job = Path(job)
    mapa = json.loads((job / "_lab_mapa.json").read_text(encoding="utf-8"))
    esperadas = {arq: info for arq, info in mapa.items()}

    import re as _re
    arquivos = [f for f in Path(pasta_zip).rglob("*")
                if f.is_file() and f.suffix.lower() in (".mp4", ".webm", ".mov")
                and (_tokens(f.name) & _PESSOA_TITULO)]
    # 07/08: o projeto do CANAL acumula 95 clipes de host de trabalhos anteriores, e
    # o avaliador ouvia só os 30 primeiros em ordem alfabética — 5 células ficaram
    # "vazias" por clipes que eu nunca escutei, não por takes que falharam.
    if desde:
        def _st(f):
            m = _re.search(r"_(\d{12})", f.stem)
            return m.group(1) if m else "0"
        arquivos = [f for f in arquivos if _st(f) >= desde]
    print(f"{len(arquivos)} clipes de pessoa a ouvir"
          f"{(' (desde ' + desde + ')') if desde else ''}\n")

    achados = {}          # arquivo_alvo -> (motivo, clipe)
    for f in arquivos[:limite]:
        # 07/08: o Whisper estoura em clipe ocasional ("crash nativo") e derrubava a
        # corrida inteira. Cada clipe falha SOZINHO — o laboratório não pode morrer
        # por causa de um take.
        try:
            dito = transcrever_take(f)
        except Exception as e:
            print(f"  (STT falhou) {f.name[:44]:<46} {type(e).__name__}")
            continue
        if not dito.strip():
            continue
        # a qual das 12 falas este take mais se parece?
        melhor, nota = None, 0.0
        for arq, info in esperadas.items():
            pd = set(_palavras(info["fala"]))
            dt = set(_palavras(dito))
            if not pd:
                continue
            n = len(pd & dt) / len(pd)
            if n > nota:
                melhor, nota = arq, n
        if not melhor or nota < 0.5:
            print(f"  (fora do teste) {f.name[:44]:<46} {dito[:46]!r}")
            continue
        ok, motivo = _av(dito, esperadas[melhor]["fala"])
        ant = achados.get(melhor)
        if ok or not ant:
            achados[melhor] = (motivo if ok else motivo, f, ok)

    print()
    placar = {}
    for arq, info in esperadas.items():
        r = achados.get(arq)
        rot = f"{info['papel']}/{info['variante']}"
        if not r:
            print(f"  ------ {rot:<18} nenhum clipe disse esta fala")
            placar.setdefault(info["variante"], []).append(False)
            continue
        motivo, f, ok = r
        placar.setdefault(info["variante"], []).append(ok)
        print(f"  {'PASSA ' if ok else 'FALHA '} {rot:<18} {motivo[:58]}")

    print("\n=== PLACAR POR VARIANTE (qual forma de PEDIR o VEO obedece) ===")
    for v, res in sorted(placar.items(), key=lambda x: (-sum(x[1]), x[0])):
        print(f"  {v:<12} {sum(res)}/{len(res)}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--job", required=True)
    ap.add_argument("--montar", action="store_true")
    ap.add_argument("--avaliar", default="")
    ap.add_argument("--desde", default="", help="AAAAMMDDHHMM: só clipes deste carimbo em diante")
    a = ap.parse_args()
    if a.montar:
        montar(a.job)
    elif a.avaliar:
        avaliar(a.job, a.avaliar, desde=a.desde)
