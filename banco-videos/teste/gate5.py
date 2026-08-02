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
Judge each image as a CUTAWAY for this moment — not as a literal illustration of the
sentence. When the narration mentions a person, place or object that is INCIDENTAL to
the film (a doctor, a researcher, a city, a date), a good editor does not cut to that
incidental thing: they stay inside the film's own world — its subject, its textures,
its environment — and let the line play over an image that carries the tension.
Cut to the literal thing ONLY when that thing IS the subject of the film.

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
  "burned_text" (caption/subtitle/text burned into the image),
  "crash" (accident/injury/CCTV footage),
  "brand" (a prominent identifiable brand/product foreign to the topic)

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


def batch_gate(candidatos, descricao, ctx_secao="", max_lote=12, tema=""):
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
        ctx = f"SECTION RULE: {ctx_secao}\n" if ctx_secao else ""
        prompt = RUBRIC.format(desc=descricao[:200], tema=(tema or "documentary")[:80], ctx=ctx)
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
