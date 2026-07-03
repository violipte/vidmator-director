"""Director v3: word-level (Whisper) + ducking + infográficos + texto + transições.

- Timing: word timestamps (cortes caem no gap real entre palavras = silêncio exato)
- Ducking: envelope de volume da música (baixa na fala, sobe nas pausas)
- Match cena->clip + texto_impacto + infografico: Gemini
"""
import json
import re
import subprocess
import sys
import urllib.request
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

BASE = Path(r"F:/Canal Dark/Aplicativo de Edição/banco-videos")
TESTE = BASE / "teste"
NARRACAO = TESTE / "narracao_joanne.mp3"
WORDS = TESTE / "words.json"
CATALOGO = Path(r"D:/Meu Drive/canal_dark_footage_stock/catalogo.json")  # banco real do Drive
TIMELINE = TESTE / "timeline.json"
CREDS = Path(r"F:/Canal Dark/Aplicativo de Edição/video-automator/credentials.json")

INTRO_END = 40.0      # primeiros 40s = ritmo acelerado (cenas curtas, transições rápidas)
# (alvo, min, max) de duração de cena por posição
def _targets(t):
    return (2.6, 1.7, 4.0) if t < INTRO_END else (4.8, 3.0, 8.0)
DUCK_LOW = 0.07       # volume música durante fala
DUCK_HIGH = 0.26      # volume música nas pausas
DUCK_PAD = 0.15       # padding ao redor da fala


def norm(s):
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


# footage de arquivo: enquadrar (moldura) quando o trecho evoca o passado/registro; senão fundir
ARQ_PAST = re.compile(r"\b(18|19|20)\d\d\b|\b(ago|ancient|history|historic|century|decade|era|past|old|war|empire|memory|remember)\w*", re.I)


def archive_modo(texto):
    return "enquadrar" if ARQ_PAST.search(texto or "") else "fundir"


def calc_aparece(c, words, infografico, texto_imp, palavra):
    """Tempo absoluto (s) em que o overlay deve aparecer = quando a palavra/número é falado."""
    sw = [w for w in words if w["start"] >= c["ini"] - 0.05 and w["start"] < c["fim"]]
    alvo = None
    if infografico:
        for w in sw:
            if any(ch.isdigit() for ch in w["word"]):
                alvo = w["start"] - 0.25  # contador começa um tico antes
                break
    elif texto_imp and palavra:
        kw = norm(palavra)
        for w in sw:
            wn = norm(w["word"])
            if not wn:
                continue
            # match exato; substring só se ambas >=4 letras (evita "a","is","to" casarem)
            if wn == kw or (len(wn) >= 4 and len(kw) >= 4 and (kw in wn or wn in kw)):
                alvo = w["start"] - 0.45  # reveal sobe até a palavra-chave
                break
    if alvo is None and (infografico or texto_imp):
        alvo = c["ini"] + 0.3
    if alvo is None:
        return None
    return round(max(c["ini"], alvo), 2)


def duracao_audio(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "csv=p=0", str(path)], capture_output=True, text=True)
    return float(out.stdout.strip())


def construir_cenas(words, dur):
    """Agrupa palavras em cenas ~ALVO_S, quebrando em fim-de-frase, clamp 3-8s.
    Cortes caem no meio do gap entre palavras (silêncio real)."""
    grupos, start_i = [], 0
    for i, w in enumerate(words):
        t0 = words[start_i]["start"]
        alvo, _mn, mx = _targets(t0)
        scene_dur = w["end"] - t0
        ends_phrase = bool(re.search(r"[.!?,;:—]$", w["word"]))
        is_intro = t0 < INTRO_END
        is_last = i == len(words) - 1
        # intro: corta em qualquer gap ao atingir alvo (rápido). resto: exige fim-de-frase.
        if is_last or scene_dur >= mx or (scene_dur >= alvo and (ends_phrase or is_intro)):
            grupos.append((start_i, i))
            start_i = i + 1

    cenas = []
    for gi, (a, b) in enumerate(grupos):
        ini = 0.0 if gi == 0 else (words[grupos[gi - 1][1]]["end"] + words[a]["start"]) / 2
        fim = dur if gi == len(grupos) - 1 else (words[b]["end"] + words[grupos[gi + 1][0]]["start"]) / 2
        texto = " ".join(words[k]["word"] for k in range(a, b + 1)).strip()
        cenas.append({"texto": texto, "ini": round(ini, 2), "fim": round(fim, 2)})

    # merge cenas < MIN_S
    mudou = True
    while mudou and len(cenas) > 1:
        mudou = False
        for i, c in enumerate(cenas):
            _a, mn, _x = _targets(c["ini"])
            if c["fim"] - c["ini"] < mn:
                j = i - 1 if i == len(cenas) - 1 else i + 1
                a, b = sorted([i, j])
                cenas[a] = {"texto": (cenas[a]["texto"] + " " + cenas[b]["texto"]).strip(),
                            "ini": cenas[a]["ini"], "fim": cenas[b]["fim"]}
                del cenas[b]
                mudou = True
                break
    return cenas


def envelope_ducking(words, dur):
    """Array de volume da música @10fps: DUCK_LOW na fala, DUCK_HIGH nas pausas (com suavização)."""
    step = 0.1
    n = int(dur / step) + 2
    falando = [False] * n
    for w in words:
        a = max(0, int((w["start"] - DUCK_PAD) / step))
        b = min(n - 1, int((w["end"] + DUCK_PAD) / step))
        for k in range(a, b + 1):
            falando[k] = True
    vols = [DUCK_LOW if falando[k] else DUCK_HIGH for k in range(n)]
    # suavização (média móvel ~0.4s) pra ramps suaves
    win = 4
    suav = []
    for k in range(n):
        lo, hi = max(0, k - win), min(n, k + win + 1)
        suav.append(round(sum(vols[lo:hi]) / (hi - lo), 3))
    return {"step": step, "vols": suav}


def gemini(cenas):
    creds = json.load(open(CREDS, encoding="utf-8"))
    key = next(c["api_key"] for c in creds if c.get("provedor") == "gemini" and c.get("api_key"))
    cenas_txt = "\n".join(f"[{i}] {c['texto']}" for i, c in enumerate(cenas))
    prompt = (
        "You are editing a video (any niche: history, true crime, science, etc.). For EACH short scene write a "
        "stock_query: a precise English STOCK-FOOTAGE search phrase (4 to 7 words) for the IDEAL generic/atmospheric "
        "B-roll for that line — content AND mood, cinematic (e.g. 'foggy dark victorian street night', 'lonely ocean "
        "horizon storm clouds', 'old documents candlelight closeup'). Avoid named people/places (those are handled "
        "separately) — describe a filmable GENERIC scene. Then choose AT MOST ONE overlay:\n\n"
        "A) INFOGRAPHIC — if the scene states a NUMERIC FACT (percentage, count, distance, temperature, "
        "years), return infografico = {tipo, valor, sufixo, label}: tipo 'ring' for percentages else 'counter'; "
        "valor=number only; sufixo=unit (e.g. '%',' light-years',' billion yrs','M °C'); label=2-4 word caption.\n"
        "B) TEXTO_IMPACTO — else, if emotionally impactful/quotable, give texto_impacto (max 6 words) + "
        "palavra_chave (one word to highlight, present in texto_impacto).\n"
        "C) Otherwise both null. Only scenes with a real number get an infographic; ~30% of the rest get text.\n\n"
        f"=== SCENES ===\n{cenas_txt}\n\n"
        'Return ONLY a JSON array: [{"scene":0,"stock_query":"...","texto_impacto":null,"palavra_chave":null,'
        '"infografico":null}, ...]'
    )
    body = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode("utf-8")
    for model in ("gemini-2.5-flash", "gemini-2.0-flash", "gemini-flash-latest"):
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
            req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
            with urllib.request.urlopen(req, timeout=120) as r:
                resp = json.loads(r.read())
            txt = resp["candidates"][0]["content"]["parts"][0]["text"]
            txt = re.sub(r"^```(?:json)?|```$", "", txt.strip(), flags=re.MULTILINE).strip()
            arr = json.loads(txt)
            print(f"  Gemini OK ({model})")
            return {int(o["scene"]): (o.get("stock_query"), o.get("texto_impacto"), o.get("palavra_chave"), o.get("infografico")) for o in arr}
        except Exception as e:
            print(f"  Gemini {model} falhou: {str(e)[:80]}")
    return {}


def main():
    dur = duracao_audio(NARRACAO)
    words = json.load(open(WORDS, encoding="utf-8"))

    cenas = construir_cenas(words, dur)
    durs = [c["fim"] - c["ini"] for c in cenas]
    print(f"=== Director v3 (word-level) ===")
    print(f"  Narração {dur:.1f}s | palavras {len(words)} | cenas {len(cenas)}")
    print(f"  Dur cenas: min {min(durs):.1f}s max {max(durs):.1f}s média {sum(durs)/len(durs):.1f}s")

    env = envelope_ducking(words, dur)
    print(f"  Envelope ducking: {len(env['vols'])} amostras @ {env['step']}s\n")

    print("  Stock queries + overlays (Gemini)...")
    match = gemini(cenas)

    # transições: intro favorece movimento (punchy); resto cicla variado
    TRANS_INTRO = ["whip", "slide_left", "zoom", "slide_right", "whip", "zoom"]
    TRANS_NORM = ["crossfade", "slide_left", "zoom", "slide_right", "whip", "crossfade", "zoom"]
    POS = ["center", "left", "right"]
    MOVE = {"slide_left", "slide_right", "zoom", "whip"}  # transições que ganham click
    # estilos de entrada de texto (intro usa os mais punchy)
    ENTRADA_INTRO = ["pop", "blur", "pop", "up"]
    ENTRADA_NORM = ["words", "up", "blur", "words", "pop"]

    tl = {"narracao": str(NARRACAO).replace("\\", "/"), "duracao": round(dur, 2),
          "musica_envelope": env, "cenas": []}
    txt_count = 0
    for i, c in enumerate(cenas):
        stock_query, texto_imp, palavra, infografico = match.get(i, (None, None, None, None))
        if infografico:
            texto_imp = None
        texto_imp = texto_imp or None
        is_intro = c["ini"] < INTRO_END
        pos = None
        entrada = None
        if texto_imp or infografico:
            pos = POS[txt_count % len(POS)]
            entrada = (ENTRADA_INTRO if is_intro else ENTRADA_NORM)[txt_count % (len(ENTRADA_INTRO) if is_intro else len(ENTRADA_NORM))]
            txt_count += 1
        if i == 0:
            trans = "none"
        elif is_intro:
            trans = TRANS_INTRO[(i - 1) % len(TRANS_INTRO)]
        else:
            trans = TRANS_NORM[(i - 1) % len(TRANS_NORM)]
        fade = 7 if is_intro else 14   # frames de transição (intro = mais rápido)
        aparece = calc_aparece(c, words, infografico, texto_imp, palavra)
        tl["cenas"].append({
            "idx": i, "inicio": round(c["ini"], 2), "fim": round(c["fim"], 2),
            "dur_cena": round(c["fim"] - c["ini"], 2),
            "texto": c["texto"], "clip_id": f"scene_{i}",
            "clip_path": None, "clip_dur": 0,          # preenchidos pelo stock_ondemand.py
            "stock_query": stock_query or c["texto"][:60],
            "transicao": trans, "sfx": trans in MOVE, "fade": fade, "intro": is_intro,
            "texto_impacto": texto_imp, "palavra_chave": (palavra or None),
            "texto_pos": pos, "entrada_texto": entrada, "infografico": infografico,
            "aparece_em": aparece,
            "fonte": None, "era": None, "arquivo_modo": None,
        })

    TIMELINE.write_text(json.dumps(tl, ensure_ascii=False, indent=2), encoding="utf-8")
    n_txt = sum(1 for c in tl["cenas"] if c["texto_impacto"])
    n_info = sum(1 for c in tl["cenas"] if c.get("infografico"))
    n_sfx = sum(1 for c in tl["cenas"] if c["sfx"])
    print(f"\nOK -> {TIMELINE}")
    print(f"  {len(tl['cenas'])} cenas | {n_txt} texto | {n_info} infográficos | {n_sfx} com whoosh")


if __name__ == "__main__":
    main()
