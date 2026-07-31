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

RUBRIC = """You are a STRICT photo editor selecting images for a professional documentary.

TOPIC: "{desc}"
{ctx}
For EACH numbered image below, give a JSON object with:
- "score" (0-10): how precisely it matches the topic.
  10 = the EXACT subject is clearly the main focus, professional quality
  8-9 = main subject matches, minor details differ
  6-7 = related theme but a key element is missing or wrong
  3-5 = loosely related, generic/cliché, or staged stock look
  0-2 = wrong subject or unusable
  Be STRICT: only award 8+ if the image could genuinely illustrate this exact
  topic in a documentary.
- "vetos": array of any that apply (empty if none):
  "talking_head" (person presenting/talking to camera, vlogger, host),
  "child" (any minor visible),
  "watermark" (visible watermark/logo overlay),
  "burned_text" (caption/subtitle/text burned into the image),
  "crash" (accident/injury/CCTV footage),
  "brand" (a prominent identifiable brand/product foreign to the topic)

Respond ONLY a JSON array, one object per image, same order. No markdown."""


def batch_gate(candidatos, descricao, ctx_secao="", max_lote=12):
    """candidatos: [{url|path, source, id, ...}] -> mesmos itens + score/vetos, ordenado.
    Baixa miniaturas quando url remota; aceita path local. Veto => score forçado a 0."""
    import base64
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
                f_tmp.write_bytes(raw)
                frames.append(str(f_tmp))
                validos.append(c)
            except Exception:
                continue
        if not frames:
            continue
        ctx = f"SECTION RULE: {ctx_secao}\n" if ctx_secao else ""
        prompt = RUBRIC.format(desc=descricao[:220], ctx=ctx)
        resp = _vision(prompt, frames) or _vision_luna(prompt, frames)
        try:
            m = re.search(r"\[.*\]", resp or "", re.S)
            notas = json.loads(m.group(0)) if m else []
        except Exception:
            notas = []
        for i, c in enumerate(validos):
            n = notas[i] if i < len(notas) and isinstance(notas[i], dict) else {}
            vetos = n.get("vetos") or []
            score = int(n.get("score") or 0)
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
