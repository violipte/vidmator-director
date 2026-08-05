# -*- coding: utf-8 -*-
"""GATE v5 (F6) — batch Vision: caçador de defeitos (v4) + SCORE de match (0-10).

Diferença pro gate v4: em vez de validar candidato a candidato durante o loop,
COLETA um pool inteiro e valida TODOS numa chamada só do Gemini — menos chamadas,
menos rate limit, e a escolha vira "o MELHOR do pool" (sort por score), não o
primeiro-que-passa. A régua do amigo (strict photo editor, 8+ = 'ilustraria esse
tópico exato num documentário') + os NOSSOS vetos (defeito anula o score).

Uso: batch_gate(candidatos, descricao, ctx_secao) -> lista com score+vetos, ordenada.
"""
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).parent))
from vision_gate import _vision, _vision_luna  # noqa — rotação de 8 keys Gemini + fallback Luna

RUBRIC = """You are the FILM EDITOR of a documentary. You are choosing the shot that
plays on screen while the narrator says a specific line.

DOCUMENTARY SUBJECT (what the whole film is about): "{tema}"
NARRATION AT THIS MOMENT: "{desc}"
{ctx}
SHOT THE EDITOR ASKED FOR: "{busca}"

CONTEXT AROUND THIS MOMENT (02/08 — the art director used to catch these AFTER the
fact, at the cost of re-searching 68% of the video; now you catch them here):
- Lines just before and after: "{vizinhas}"
- Already ON SCREEN in this section: {ja_na_secao}
- Species this section is about: {especie}

Use that context. Three failures it prevents, all of which shipped:
a) REPEAT — if the neighbouring moments already show this same thing, the cut goes
   nowhere. A close-up of the animal, right after another close-up of the animal,
   is a wasted beat even when it is beautiful. Score it 3-5.
b) WRONG SPECIES — when the section is about a named species, another species is a
   factual error, not a stylistic choice. We shipped an *Aedes* mosquito while the
   narration announced *Anopheles darlingi*, and a larva where the line needed the
   adult. If the section names a species and the image is clearly another, veto
   "fora_do_pedido".
c) LITERAL WHEN THE LINE IS ABOUT A SYSTEM — when the narration talks about distance
   to a clinic, cost, labour or access, another portrait of the animal answers
   nothing. The shot has to show the SYSTEM (the river, the boat, the road, the
   clinic, the work), not the creature again. Score it 3-5.

Judge each image as a CUTAWAY for this moment — not as a literal illustration of the
sentence. When the narration mentions a person, place or object that is INCIDENTAL to
the film (a doctor, a researcher, a city, a date), a good editor does not cut to that
incidental thing: they stay inside the film's own world — its subject, its textures,
its environment — and let the line play over an image that carries the tension.
Cut to the literal thing ONLY when that thing IS the subject of the film.

HARD LIMIT (02/08): "stay inside the film's world" is NOT a licence to ignore the
requested shot. Real failures we shipped: "calm hospital hallway" returned a jaguar,
"dirty boots by the door" returned a snake, "antivenom vial" returned a spider — all
rated 10, all of them beautiful, all of them WRONG. Scoring them low was not enough,
because when the whole pool is wrong the least-wrong still wins: they now get the
"fora_do_pedido" VETO, which annuls the score entirely. An empty beat is better than
a beat that answers a question nobody asked.

For EACH numbered image below, give a JSON object with:
- "score" (0-10): how well it works as the shot for this moment.
  10 = belongs to the documentary subject AND carries the mood/tension of this line
  8-9 = clearly belongs to the subject and fits the moment
  6-7 = belongs to the subject but is flat//generic for this moment
  3-5 = only literally matches the sentence but is foreign to the film's subject
        (e.g. an office, a stock businessman, a lab diagram in a wildlife film)
  0-2 = unusable, wrong, or empty/dark frame with no readable content
  Prefer the shot that serves the FILM over the shot that serves the sentence.
- "vetos": array of any that apply (empty if none):
  "talking_head" (person presenting/talking to camera, vlogger, host),
  "child" (any minor visible),
  "watermark" (visible watermark/logo overlay),
  "burned_text" (ANY text baked into the footage — subtitle, caption, headline,
     big title card, thumbnail-style lettering, channel name, "TOP 10"/"10 ANIMAIS"
     style numbering, arrows or circles drawn on the image. If you can READ words
     on the frame and they are not a natural part of the scene (a road sign, a
     product label), veto it. Text on the frame means the clip was cut from
     SOMEONE ELSE'S finished video — it exposes the source and looks stolen.),
  "crash" (accident/injury/CCTV footage),
  "nudez" (ANY exposed genitalia, buttocks or female breasts — including
     ethnographic, tribal, documentary, artistic or historical footage. This is
     for a MONETISED channel: exposure is demonetisation and possible strike,
     regardless of how legitimate the context is. When in doubt, veto.),
  "screen_capture" (a recording of a video PLAYER or app: progress bar, play
     button, seek scrubber, UI chrome at the edges of frame),
  "fora_do_pedido" (the image does NOT show what the SHOT THE EDITOR ASKED FOR
     describes. Ask yourself literally: "is this a <requested shot>?" — if the
     answer is no, veto it, even when the image belongs beautifully to the
     documentary subject. A jaguar is not a hospital corridor. A snake is not a
     pair of boots by a door. A spider is not an antivenom vial. Belonging to the
     film does NOT substitute for answering the request.),
  "brand" (a prominent identifiable brand/product foreign to the topic),
  "fake" (AI-generated, digitally composited, or manipulated to look real:
     an animal at an IMPOSSIBLE size next to a boat/person/car, two species
     that never meet posed together, painterly or 3D-render lighting sold as
     a photograph, anatomy that does not exist. This is a DOCUMENTARY — a
     viral fake destroys the credibility of every real fact around it. When
     an image looks too extraordinary to be a real photograph, it is not one.)

Respond ONLY a JSON array, one object per image, same order. No markdown."""


def _preparar_frame(raw, destino):
    """Garante que o que vai pro Vision É uma imagem — e uma que a API aceite.

    01/08 (a raiz do "gate cego"): o researchgate devolveu HTML (`<!DOCTYPE`) com
    status 200. Mandar isso rotulado como image/jpeg faz a API rejeitar a requisição
    INTEIRA -> `notas` vazio -> TODOS os candidatos do lote ficam com score 0 -> o
    beat cai no fallback v4 (esquema/diagrama genérico). UM candidato podre cegava a
    curadoria do lote inteiro. Aqui o byte vira JPEG de verdade ou é descartado."""
    try:
        import io
        from PIL import Image
        with Image.open(io.BytesIO(raw)) as im:
            im = im.convert("RGB")
            if max(im.size) > 1024:
                im.thumbnail((1024, 1024))
            im.save(destino, "JPEG", quality=85)
        return True
    except Exception:
        return False


def _notas_do_vision(prompt, frames):
    """Notas alinhadas aos frames. Se a chamada morrer com N>1, BISSECTA em vez de
    devolver zero pra todo mundo — assim um frame que a API rejeite não derruba os
    vizinhos. Devolve None quando nem o frame sozinho foi avaliado (≠ 'nota 0')."""
    # 31/07: Gemini em 429 (quota free estourada) — Luna PRIMEIRO evita queimar
    # 8 tentativas mortas por lote; Gemini fica de fallback (volta quando resetar)
    resp = _vision_luna(prompt, frames) or _vision(prompt, frames)
    try:
        m = re.search(r"\[.*\]", resp or "", re.S)
        notas = json.loads(m.group(0)) if m else []
    except Exception:
        notas = []
    if isinstance(notas, list) and len(notas) >= len(frames):
        return notas[:len(frames)]
    if len(frames) == 1:
        return notas if isinstance(notas, list) and notas else [None]
    meio = len(frames) // 2
    return _notas_do_vision(prompt, frames[:meio]) + _notas_do_vision(prompt, frames[meio:])


CLIP_PY = Path(r"F:/Canal Dark/clip_venv/Scripts/python.exe")
CLIP_TOPK = 8      # quantos finalistas seguem pro Vision
CLIP_MIN = 4       # lote menor que isto não compensa o custo de subir o modelo
_CLIP_OK = {"v": None}   # None = não testado; False = indisponível, para de tentar


def _pre_filtro_clip(frames, validos, descricao, tema, busca=""):
    """Peneira SEMÂNTICA local antes do Vision pago (02/08).

    Motivo: em 31/07 a curadoria parou com 8 chaves Gemini em 429 + Luna sem crédito.
    O CLIP roda na 5070 Ti, custa 0, e ordena por 'casa com o texto' — então o Vision
    só arbitra os finalistas. Validado no job de cobras: separou a gravura de
    *Bothrops jararaca* (0.263) da prancha anatômica de perna humana (0.057).

    Falha do CLIP nunca derruba o gate: sem venv/modelo, devolve o lote intacto e o
    Vision decide sozinho, como antes.
    """
    if _CLIP_OK["v"] is False or len(frames) <= CLIP_MIN or not CLIP_PY.exists():
        return frames, validos
    # 02/08: o alvo era "{tema}. {descricao}" — mesma contaminação da query: pra
    # "hospital hallway" o CLIP ranqueava FAUNA no topo, porque o tema pesava mais
    # que o pedido. O que o editor PEDIU manda; tema entra só como contexto.
    alvo = (busca or descricao or "")[:150]
    if tema and not busca:
        alvo = f"{tema}. {descricao}"[:180]
    try:
        import subprocess
        r = subprocess.run([str(CLIP_PY), str(Path(__file__).parent / "clip_rank.py"),
                            "--texto", alvo, "--imgs", *frames],
                           capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=180)
        ranking = json.loads((r.stdout or "").strip().splitlines()[-1])
        if not ranking:
            return frames, validos
        _CLIP_OK["v"] = True
        ordem = {x["path"]: i for i, x in enumerate(x for x in ranking)}
        pares = sorted(zip(frames, validos), key=lambda fv: ordem.get(fv[0], 999))[:CLIP_TOPK]
        return [f for f, _ in pares], [v for _, v in pares]
    except Exception:
        _CLIP_OK["v"] = False   # some do caminho até o próximo processo
        return frames, validos


def batch_gate(candidatos, descricao, ctx_secao="", max_lote=12, tema="", busca="",
               vizinhas="", ja_na_secao="", especie=""):
    """candidatos: [{url|path, source, id, ...}] -> mesmos itens + score/vetos, ordenado.
    Baixa miniaturas quando url remota; aceita path local. Veto => score forçado a 0.
    Candidato que o Vision não conseguiu avaliar sai com score -1 (≠ 'ruim')."""
    import httpx
    out = []
    for ini in range(0, len(candidatos), max_lote):
        lote = candidatos[ini:ini + max_lote]
        frames, validos = [], []
        for c in lote:
            try:
                if c.get("path"):
                    raw = Path(c["path"]).read_bytes()
                else:
                    raw = httpx.get(c["url"], headers={"User-Agent": "Mozilla/5.0"},
                                    timeout=25, follow_redirects=True).content
                if len(raw) < 4000 or len(raw) > 12_000_000:
                    continue
                p_tmp = Path(c.get("_tmp") or (Path(__file__).parent / "_tmp"))
                p_tmp.mkdir(exist_ok=True)
                f_tmp = p_tmp / f"g5_{abs(hash(c.get('id') or c.get('url'))) % 10**10}.jpg"
                if not _preparar_frame(raw, f_tmp):
                    continue  # HTML/paywall/formato torto — fora ANTES de cegar o lote
                frames.append(str(f_tmp))
                validos.append(c)
            except Exception:
                continue
        if not frames:
            continue
        frames, validos = _pre_filtro_clip(frames, validos, descricao, tema, busca)
        ctx = f"SECTION RULE: {ctx_secao}\n" if ctx_secao else ""
        prompt = RUBRIC.format(desc=descricao[:200], tema=(tema or "documentary")[:80],
                               ctx=ctx, busca=(busca or descricao)[:120],
                               vizinhas=(vizinhas or "(not provided)")[:300],
                               ja_na_secao=(ja_na_secao or "(none yet)")[:200],
                               especie=(especie or "(not a specific species)")[:60])
        notas = _notas_do_vision(prompt, frames)
        for i, c in enumerate(validos):
            bruto = notas[i] if i < len(notas) else None
            if not isinstance(bruto, dict):
                # o Vision NÃO avaliou este candidato — não é "ruim", é desconhecido.
                # score -1 deixa o curador distinguir pool fraco de gate fora do ar.
                out.append({**c, "score": -1, "vetos": [], "sem_gate": True})
                continue
            vetos = bruto.get("vetos") or []
            score = int(bruto.get("score") or 0)
            if vetos:
                score = 0  # defeito ANULA — proteção v4 preservada
            out.append({**c, "score": max(0, min(10, score)), "vetos": vetos})
    out.sort(key=lambda x: -x["score"])
    return out


SCORE_THRESHOLD = 8  # principal precisa de 8+; 5-7 vira reserva (poss/extra)


if __name__ == "__main__":
    from fontes5 import coletar_imagens
    q = sys.argv[1] if len(sys.argv) > 1 else "ancient greek temple ruins at sunset"
    cands = coletar_imagens(q)
    print(f"{len(cands)} candidatos de {len(set(c['source'] for c in cands))} fontes")
    for r in batch_gate(cands, q)[:6]:
        print(f"  {r['score']:>2} {r['source']:<10} vetos={r['vetos']} {r['url'][:60]}")
