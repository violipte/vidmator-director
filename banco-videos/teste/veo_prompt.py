# -*- coding: utf-8 -*-
"""DIRETOR DE FOTOGRAFIA do modo generativo (01/08) — beat -> prompt de CENA.

Problema que resolve: o `veo_lote.py` mandava pro VEO o campo `busca` do beat, que
foi escrito pra procurar STOCK por palavra-chave. Prompt real que foi ao ar:

    "ancient Roman general alone in war tent, Roman emperor tent interior.
     Mood: marble statue, candlelight, ancient ruins, stormy sea, manuscript.
     Cinematic, photorealistic, natural motion. No captions, no subtitles, ..."

Três defeitos: (a) é lista de keywords, sem nada que o VEO obedece de verdade —
lente, movimento de câmera, luz, ação; (b) o `Mood:` despeja as palavras do
style_card como OBJETOS da cena (a tenda romana estava pedindo "stormy sea" junto);
(c) metade do texto é negação, e modelo de vídeo lida mal com "no X" — às vezes
produz justamente o X.

Aqui o beat vira uma DIREÇÃO: sujeito + ação + ambiente + luz + câmera + look, com
o mood aplicado como ESTILO (grading/atmosfera), não como coisa dentro do quadro.
LLM em BATCH (1 chamada por lote), com fallback determinístico se a API falhar.
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from vision_gate import _LUNA_MODEL, _OKEY  # noqa

GUIA = """You are the DIRECTOR OF PHOTOGRAPHY of a documentary. For each SHOT below,
write ONE generation prompt for a text-to-video model (or text-to-image when asked).

FILM LOOK (applies to every shot, as GRADING and ATMOSPHERE — never as objects in
the frame): {estilo}

Write each prompt as a single flowing sentence containing, in this order:
1. shot size and subject (e.g. "slow push-in on a weathered hand...")
2. what is HAPPENING — one concrete action or motion, not a static description
3. the environment and the light (source, direction, quality)
4. camera: lens feel and movement (handheld, slow dolly, static tripod, crane)
5. the film look above, as grading words

Hard rules:
- NEVER include words from the film look as physical objects in the scene.
- Describe only what the CAMERA SEES. No story, no narration, no metaphor.
- One subject per shot. No text, signage or readable writing in frame.
- No person addressing the camera. Faces may appear only incidentally, never
  speaking to the lens.
- Keep each prompt under 60 words. Plain descriptive English.

Reply ONLY a JSON array of strings, one per shot, in the same order. No markdown."""

# fallback determinístico — a mesma gramática, montada sem LLM
_CAMERA = ["slow dolly-in", "static tripod shot", "slow handheld drift",
           "gentle crane down", "slow tracking shot", "locked-off wide"]
_LUZ = ["low warm key light with deep shadows", "soft overcast daylight",
        "hard side light raking across the surface", "dim practical light in frame",
        "cool ambient light from a window", "golden low sun backlight"]


def _fallback(busca, estilo, i):
    base = re.sub(r"\s+", " ", (busca or "").replace(" OR ", ", ")).strip()
    return (f"{_CAMERA[i % len(_CAMERA)]} on {base}, {_LUZ[i % len(_LUZ)]}, "
            f"shallow depth of field, {estilo}").strip()[:400]


def _pedir(prompt, timeout=120):
    import httpx
    if not _OKEY:
        return None
    try:
        r = httpx.post("https://api.openai.com/v1/chat/completions",
                       headers={"Authorization": "Bearer " + _OKEY},
                       json={"model": _LUNA_MODEL, "max_completion_tokens": 3000,
                             "messages": [{"role": "user", "content": prompt}]},
                       timeout=timeout)
        if r.status_code == 200:
            return r.json()["choices"][0]["message"]["content"]
    except Exception:
        pass
    return None


def dirigir(itens, estilo, tema="", lote=10):
    """itens: [{busca, texto, tipo}] -> lista de prompts na MESMA ordem.
    `tipo` == 'imagem' muda a instrução de movimento para composição estática."""
    out = []
    for ini in range(0, len(itens), lote):
        parte = itens[ini:ini + lote]
        linhas = []
        for k, it in enumerate(parte, 1):
            alvo = (it.get("busca") or "").replace(" OR ", ", ")
            fala = (it.get("texto") or "").strip()[:120]
            midia = "STILL IMAGE (no motion — describe composition instead of camera move)" \
                if it.get("tipo") == "imagem" else "VIDEO (8 seconds)"
            linhas.append(f'{k}. [{midia}] subject: "{alvo}"'
                          + (f' | narration at this moment: "{fala}"' if fala else ""))
        cab = f'DOCUMENTARY SUBJECT: "{tema}"\n\n' if tema else ""
        resp = _pedir(GUIA.format(estilo=estilo) + "\n\nSHOTS:\n" + cab + "\n".join(linhas))
        prompts = []
        try:
            m = re.search(r"\[.*\]", resp or "", re.S)
            prompts = [p for p in json.loads(m.group(0)) if isinstance(p, str)] if m else []
        except Exception:
            prompts = []
        for k, it in enumerate(parte):
            p = prompts[k].strip() if k < len(prompts) and prompts[k].strip() else \
                _fallback(it.get("busca"), estilo, ini + k)
            out.append(p[:600])
    return out


PONTUA_MOV = """You are planning the GENERATED shots of a documentary. For EACH shot,
rate 0-10 how much REAL MOTION the shot needs to work — how much of its meaning is
carried by the subject moving, rather than by composition, texture or information.

10-8  the motion IS the shot: an animal striking, hunting or moving; water flowing
      or breaking; one person performing a clear readable action; weather turning.
7-5   a living subject or a live environment where movement helps, but the frame
      would still read as a photograph.
4-3   scene, place or object where stillness loses almost nothing.
2-0   composition/texture/detail; scientific or anatomical diagrams; explanatory
      structures; maps; and any scene whose motion would be COMPLEX or chaotic
      (several agents, fast interaction) — generators garble those, and a sharp
      still with camera movement beats mushy fake action.

Judge each shot on its own merit. Do NOT try to balance the batch — the mix is
decided downstream. Reply ONLY a JSON array of integers, same order. No markdown."""


MOVIMENTO = """You are planning the GENERATED shots of a documentary. For each shot
below, decide the medium (rubric refined by the channel owner, 05/08):
- "video"  when the subject's OWN motion carries the meaning AND that motion is
  SIMPLE and readable: one animal moving or striking, water flowing, one person
  performing a clear action, weather changing.
- "still"  for:
  • composition, texture, detail, object, environment, mood;
  • scientific/anatomical diagrams, explanatory structures, biology illustrations;
  • maps and map-like illustrations;
  • scenes whose motion would be COMPLEX or chaotic (several agents, fast
    interactions, intricate choreography) — video generators garble complex motion;
    a sharp still with camera movement reads better than mushy fake action.
  The edit adds camera movement over stills (Ken Burns / parallax), so a still is
  never static on screen — and stills are sharper and instant to generate.
Aim for a roughly BALANCED mix across the batch (~half stills). Not a hard quota:
harmony over arithmetic — but when in doubt, choose "still".
Reply ONLY a JSON array of "video"|"still", same order. No markdown."""

_VERBOS_MOV = re.compile(
    r"(swim|walk|run|fly|flee|flow|crawl|strik|attack|slither|hunt|chas|leap|jump"
    r"|dive|glid|wad|step|bit|lung|splash|drift|sway|rippl|trembl|speak|talk|swirl"
    r"|pour|drip|land|takeoff|coil|lash)", re.I)


def _parece_movimento(it):
    """Fallback determinístico quando o LLM não responde."""
    return bool(_VERBOS_MOV.search((it.get("busca") or "") + " " + (it.get("texto") or "")))


def pontuar_movimento(itens, lote=25):
    """Nota 0-10 de movimento essencial por shot (06/08).

    Substituiu o binário `classificar_midia` no misto: pedir "video|still" entregava
    ao LLM a DECISÃO junto com o julgamento, e o desempate da rubrica ("na dúvida,
    still") derrubou a fatia de vídeo pra 18% no lote da Austrália. Agora o LLM só
    ORDENA por necessidade de movimento e o CORTE é nosso — a régua ~50/50 do Piter
    vira controle do `veo_lote`, não um pedido que o modelo pode ignorar."""
    out = []
    for ini in range(0, len(itens), lote):
        parte = itens[ini:ini + lote]
        linhas = [f'{k}. "{(it.get("busca") or it.get("busca_original") or "")[:90]}"'
                  + (f' | narration: "{(it.get("texto") or "")[:70]}"' if it.get("texto") else "")
                  for k, it in enumerate(parte, 1)]
        resp = _pedir(PONTUA_MOV + "\n\nSHOTS:\n" + "\n".join(linhas))
        vals = []
        try:
            m = re.search(r"\[.*\]", resp or "", re.S)
            vals = [int(x) for x in json.loads(m.group(0))] if m else []
        except Exception:
            vals = []
        for k, it in enumerate(parte):
            v = vals[k] if k < len(vals) else None
            if v is None:
                v = 8 if _parece_movimento(it) else 4      # fallback determinístico
            out.append(max(0, min(10, int(v))))
    return out


def classificar_midia(itens, lote=25):
    """'video' | 'imagem' por shot — a régua é MOVIMENTO ESSENCIAL, não o tipo
    narrativo do beat (05/08, Piter: 84% do lote caiu na fila lenta do VEO porque a
    divisão herdava a lógica da era da BUSCA; 'stingray resting' virava vídeo)."""
    out = []
    for ini in range(0, len(itens), lote):
        parte = itens[ini:ini + lote]
        linhas = [f'{k}. "{(it.get("busca") or "")[:90]}"'
                  + (f' | narration: "{(it.get("texto") or "")[:70]}"' if it.get("texto") else "")
                  for k, it in enumerate(parte, 1)]
        resp = _pedir(MOVIMENTO + "\n\nSHOTS:\n" + "\n".join(linhas))
        vals = []
        try:
            m = re.search(r"\[.*\]", resp or "", re.S)
            vals = [str(x).lower() for x in json.loads(m.group(0))] if m else []
        except Exception:
            vals = []
        for k, it in enumerate(parte):
            v = vals[k] if k < len(vals) else ""
            if v not in ("video", "still", "imagem"):
                v = "video" if _parece_movimento(it) else "still"
            out.append("video" if v == "video" else "imagem")
    return out


if __name__ == "__main__":
    demo = [{"busca": "ancient Roman general alone in war tent", "tipo": "video",
             "texto": "He wrote only for himself, never to be read."},
            {"busca": "ancient Roman writing on scroll close up", "tipo": "video"}]
    for p in dirigir(demo, "dark stoic documentary, candlelit marble tones, "
                           "anamorphic 35mm, muted contrast", tema="stoicism"):
        print("-", p, "\n")
