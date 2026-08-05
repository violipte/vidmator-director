# -*- coding: utf-8 -*-
"""CRÍTICO — o diretor de arte que revisa a curadoria com o ROTEIRO INTEIRO na mão.

Por que existe (pedido do Piter, 02/08): o gate julga UM candidato contra UMA frase.
Ele não sabe o que veio antes, o que vem depois, nem o que o filme está construindo.
Por isso passaram coisas que, olhadas isoladamente, eram defensáveis:

  - "calm hospital hallway" -> um JAGUAR (o gate: "é o assunto do filme", e é)
  - "we store things"       -> um CATIVEIRO de macacos (o gate: "é Amazônia", e é)
  - seção da ARRAIA ilustrada com cobra, jacaré, anta e escorpião — cada plano
    defensável sozinho, o conjunto destruindo a imersão

O crítico entra DEPOIS da curadoria, vê o filme inteiro e pergunta o que o gate não
tem como perguntar: *este plano serve a ESTA cena, dentro deste filme?*

Ciclo: reprovado -> volta pro curador excluindo a fonte que errou -> nova busca. Ao
fim de MAX_RODADAS sem acerto, o beat vai pra fila do Nano Banana (`_gerar.json`) —
gerar é melhor que insistir num acervo que comprovadamente não tem aquele plano.

Uso: python critico5.py --job <dir> --plano <plano.json> --roteiro <roteiro.txt>
     [--rodadas 5] [--so-revisar]
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).parent))
from vision_gate import _vision, _vision_luna  # noqa

MAX_RODADAS = 5

PROMPT = """You are the ART DIRECTOR of this documentary, reviewing the editor's work.
You see the WHOLE film, not one line — that is the entire point of your job.

=== WHAT THE FILM IS ABOUT ===
{tema}

=== THE FILM, IN ORDER (abridged) ===
{roteiro}

=== THE MOMENT UNDER REVIEW ===
Time: {t_ini}s. Section: "{secao_titulo}"
The narrator says: "{texto}"
Lines just BEFORE: "{antes}"
Lines just AFTER: "{depois}"

=== WHAT THE EDITOR DID ===
Searched for: "{busca}"
Chose: the image you are seeing (source: {fonte})

=== YOUR CALL ===
Approve it only if the image genuinely serves THIS moment INSIDE THIS FILM.
Reject when any of these is true — each one has actually shipped in our videos:
1. It answers the film's SUBJECT instead of the requested shot (a jaguar where the
   line needs a hospital corridor). Belonging to the film is not enough.
1b. It does not show what was SEARCHED FOR. This rule OUTRANKS the narration:
   even when the image loosely fits the spoken line, if the editor searched for a
   specific thing the image must show THAT thing. A FROG for the search "macro shot
   insect" is a rejection — the frog fits "something far smaller", but the editor
   asked for an insect because the film's payoff is the mosquito, and the editor
   knows the film better than the single line does. Judge the image against the
   SEARCH first, the narration second.
2. It repeats what the neighbouring moments already show, so the cut goes nowhere.
3. It contradicts the section: in the chapter about ONE animal, another animal
   appears and the viewer loses the thread.
4. It is a stock cliché with no relation to what is being said.
5. Any text, watermark, or UI is visible in the frame.
6. It would make an attentive viewer ask "why am I looking at this?"

Answer ONLY this JSON:
{{"aprovado": true|false, "motivo": "<one short sentence>",
  "melhor_busca": "<if rejected, the search query YOU would use instead — be concrete
  and visual, in English; empty string if approved>"}}"""


def _resumo_roteiro(plano, max_linhas=60):
    """O filme em ordem, enxuto o bastante pra caber no prompt sem perder o arco."""
    txts = [(b.get("texto") or "").strip() for b in plano.get("beats", [])]
    txts = [t for t in txts if t]
    if len(txts) <= max_linhas:
        return "\n".join(txts)
    passo = len(txts) / max_linhas
    return "\n".join(txts[int(i * passo)] for i in range(max_linhas))


def _frames(arquivo, tmp, n=2):
    """1 frame de imagem, 2 de vídeo (o crítico julga a CENA, não o defeito)."""
    a = str(arquivo)
    if not a.lower().endswith((".mp4", ".webm", ".mov")):
        return [a]
    out = []
    for ss in ("1", "4"):
        o = Path(tmp) / f"cr_{abs(hash(a + ss)) % 10**8}.jpg"
        subprocess.run(["ffmpeg", "-nostdin", "-y", "-loglevel", "error", "-ss", ss,
                        "-i", a, "-frames:v", "1", "-vf", "scale=512:-2", str(o)],
                       capture_output=True, timeout=60)
        if o.exists():
            out.append(str(o))
        if len(out) >= n:
            break
    return out


def revisar_beat(b, res, plano, resumo, tema, tmp):
    """Veredito do crítico p/ um beat. (aprovado, motivo, melhor_busca)."""
    arq = res.get("arquivo")
    if not arq or not Path(arq).exists():
        return True, "", ""          # buraco não é problema do crítico
    beats = plano.get("beats", [])
    i = next((k for k, x in enumerate(beats) if x.get("i") == b.get("i")), 0)
    antes = " ".join((x.get("texto") or "") for x in beats[max(0, i - 2):i])[:180]
    depois = " ".join((x.get("texto") or "") for x in beats[i + 1:i + 3])[:180]
    p = PROMPT.format(
        tema=tema, roteiro=resumo, t_ini=int(b.get("t_ini", 0)),
        secao_titulo=(b.get("_sec_titulo") or f"section {b.get('secao', 0)}"),
        texto=(b.get("texto") or "")[:200], antes=antes, depois=depois,
        busca=(b.get("busca") or res.get("busca") or "")[:120], fonte=res.get("fonte", "?"))
    frames = _frames(arq, tmp)
    if not frames:
        return True, "", ""
    resp = _vision_luna(p, frames) or _vision(p, frames)
    try:
        import re
        m = re.search(r"\{.*\}", resp or "", re.S)
        d = json.loads(m.group(0)) if m else {}
    except Exception:
        return True, "", ""          # crítico mudo NUNCA reprova (não trava a linha)
    return (bool(d.get("aprovado", True)), str(d.get("motivo", ""))[:120],
            str(d.get("melhor_busca", ""))[:120])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--job", required=True)
    ap.add_argument("--plano", required=True)
    ap.add_argument("--roteiro", default="")
    ap.add_argument("--rodadas", type=int, default=MAX_RODADAS)
    ap.add_argument("--so-revisar", action="store_true",
                    help="só relata; não apaga nem re-resolve")
    a = ap.parse_args()

    job = Path(a.job)
    plano = json.loads(Path(a.plano).read_text(encoding="utf-8"))
    sc = json.loads((job / "style_card.json").read_text(encoding="utf-8")) \
        if (job / "style_card.json").exists() else {}
    tema = sc.get("assunto_ancora") or "documentary"
    resumo = _resumo_roteiro(plano)
    tmp = job / "_tmp"
    tmp.mkdir(parents=True, exist_ok=True)
    por_i = {b.get("i"): b for b in plano.get("beats", [])}

    # quantas vezes cada beat já foi reprovado (persistente entre execuções)
    hist_f = job / "_critico_hist.json"
    hist = json.loads(hist_f.read_text(encoding="utf-8")) if hist_f.exists() else {}

    reprovados, aprovados, pra_gerar = [], 0, []
    relatorio = []   # veredito POR BEAT — vira _critico_relatorio.json (o diretor lê)

    # COBERTURA TOTAL (02/08, QA Piter): a fonte da revisão é a MONTAGEM, não o
    # resolvido/. Três portas laterais entregavam clipe à tela sem juiz nenhum:
    # gaps 7xxx (a cobra em "treated a jaguar attack..."), demote com bg do pool
    # e beats servidos pelo pool interno do montador. Se está na tela, é julgado.
    itens = []
    vistos = set()
    mont_f = Path(r"F:/Canal Dark/Aplicativo de Edição/remotion/public/jobs")         / (job.name.replace("_job_", "") + "_mont") / "montagem.json"
    if mont_f.exists():
        mont = json.loads(mont_f.read_text(encoding="utf-8"))
        pub = mont_f.parent
        for mb in mont.get("beats", []):
            src = mb.get("src") or mb.get("bg")
            if not src:
                continue
            arq = pub / Path(str(src).replace("jobs/" + pub.name + "/", ""))
            base = por_i.get(mb.get("i")) or {
                "i": mb.get("i"), "t_ini": mb.get("t_ini"), "t_fim": mb.get("t_fim"),
                # gap/pool: sem beat no plano — o texto do momento vem do vizinho
                "texto": next((x.get("texto") or "" for x in plano.get("beats", [])
                               if x.get("t_ini", 9e9) <= mb.get("t_ini", 0) < x.get("t_fim", -1)), ""),
                "secao": mb.get("secao", 0), "busca": ""}
            chave = (mb.get("i"), Path(str(src)).name)
            if chave in vistos:
                continue
            vistos.add(chave)
            itens.append((base, {"i": mb.get("i"), "arquivo": str(arq),
                                 "fonte": "montagem", "busca": base.get("busca") or ""}))
    for f in sorted((job / "resolvido").glob("b*.json")):
        res = json.loads(f.read_text(encoding="utf-8"))
        b = por_i.get(res.get("i"))
        if b and (res.get("i"), Path(str(res.get("arquivo") or "")).name) not in vistos:
            itens.append((b, res))

    for b, res in itens:
        if not b:
            continue
        ok, motivo, melhor = revisar_beat(b, res, plano, resumo, tema, tmp)
        relatorio.append({"i": res.get("i"), "aprovado": ok, "motivo": motivo,
                          "melhor_busca": melhor, "fonte": res.get("fonte"),
                          "arquivo": Path(res.get("arquivo") or "").name})
        if ok:
            aprovados += 1
            continue
        n = hist.get(str(res.get("i")), 0) + 1
        hist[str(res.get("i"))] = n
        # item da MONTAGEM (gap/pool) não tem json em resolvido/ — a aplicação
        # (apagar + re-resolver) usa o arquivo quando existe; None = só relatório
        # o item pode ter vindo pela MONTAGEM e ainda assim ter resolvido/ — o que
        # decide é o arquivo existir (sem isto, 91 reprovados ficavam inapagáveis)
        _fj = job / "resolvido" / f"b{res.get('i'):03d}.json"             if isinstance(res.get("i"), int) and res.get("i") < 7000 else None
        reprovados.append((_fj if _fj and _fj.exists() else None, res, motivo, melhor, n))
        print(f"  b{res.get('i'):03d} REPROVADO ({n}/{a.rodadas}) — {motivo}")
        if melhor:
            print(f"        crítico sugere: \"{melhor}\"")

    (job / "_critico_relatorio.json").write_text(
        json.dumps(relatorio, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n=== crítico: {aprovados} aprovados | {len(reprovados)} reprovados ===")
    if a.so_revisar:
        return

    for f, res, _motivo, melhor, n in reprovados:
        arq = res.get("arquivo")
        if f is None:
            # gap/pool: não há resolvido pra apagar; o conserto é o beat entrar na
            # fila de geração/re-busca pelo plano (o montador re-preenche o gap)
            pass
        else:
            if arq and Path(arq).exists():
                Path(arq).unlink(missing_ok=True)
            f.unlink(missing_ok=True)
        if n >= a.rodadas:
            # o acervo já provou que não tem esse plano — gerar é mais barato que
            # continuar rodando busca (decisão do Piter: 5 tentativas e gera)
            pra_gerar.append({"i": res.get("i"),
                              "prompt": melhor or res.get("busca") or "",
                              "dest": f"b{res.get('i'):03d}__T1__gen.jpg"})
        elif melhor:
            # a busca do crítico substitui a do diretor na próxima rodada
            b = por_i.get(res.get("i"))
            if b:
                b["busca"] = melhor
    if pra_gerar:
        gf = job / "_gerar.json"
        atual = json.loads(gf.read_text(encoding="utf-8")) if gf.exists() else []
        ids = {x.get("i") for x in atual}
        atual += [x for x in pra_gerar if x["i"] not in ids]
        gf.write_text(json.dumps(atual, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"{len(pra_gerar)} beat(s) esgotaram {a.rodadas} rodadas -> Nano Banana")
    if reprovados:
        Path(a.plano).write_text(json.dumps(plano, ensure_ascii=False, indent=1),
                                 encoding="utf-8")
        hist_f.write_text(json.dumps(hist), encoding="utf-8")
        print("plano atualizado com as buscas do crítico — rode o curador com --resume")


if __name__ == "__main__":
    main()
