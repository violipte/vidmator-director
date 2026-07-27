"""Gera uma biblioteca de SFX via ai33.pro (ElevenLabs text-to-sound) p/ avaliação.
Baixa pra public/sfx/ e escreve o manifesto src/sfx_lib.json (o SfxSampler lê)."""
import json
import sys
import time
import urllib.request
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
CONFIG = Path(r"F:/Canal Dark/Aplicativo de Edição/video-automator/config.json")
PUB = Path(r"F:/Canal Dark/Aplicativo de Edição/remotion/public/sfx")
MANIFEST = Path(r"F:/Canal Dark/Aplicativo de Edição/remotion/src/sfx_lib.json")
KEY = json.load(open(CONFIG, encoding="utf-8"))["ai33_api_key"]
BASE = "https://api.ai33.pro"

# (nome, categoria, uso, prompt, duração)
LIB = [
    ("click_sharp", "TRANSIÇÃO", "click seco/tátil", "sharp tactile UI click, very short", 1),
    ("click_soft", "TRANSIÇÃO", "click suave", "soft minimal pop click, gentle", 1),
    ("click_camera", "TRANSIÇÃO", "obturador", "camera shutter snap click", 1),
    ("click_mech", "TRANSIÇÃO", "tecla mecânica", "mechanical keyboard key click", 1),
    ("click_wood", "TRANSIÇÃO", "knock de madeira", "wooden block knock, short percussive", 1),
    ("ding_bright", "SINO", "notificação", "bright notification ding chime", 1),
    ("bell_glass", "SINO", "sino de vidro", "soft glass bell chime, delicate", 2),
    ("bell_bowl", "SINO", "tigela tibetana", "meditation singing bowl ping, calm reverb", 2),
    ("chime_sparkle", "SINO", "brilho/sparkle", "delicate celesta sparkle chime, magical", 2),
    ("whoosh_fast", "WHOOSH", "transição rápida", "fast cinematic whoosh transition", 1),
    ("whoosh_deep", "WHOOSH", "whoosh grave", "deep low cinematic whoosh", 2),
    ("whoosh_air", "WHOOSH", "ar suave", "subtle soft air whoosh, light", 1),
    ("whoosh_reverse", "WHOOSH", "reverse swell", "reverse whoosh swell into impact", 2),
    ("swish_quick", "SWISH", "swish curto", "quick short swish transition", 1),
    ("swish_paper", "SWISH", "página", "paper page swish flip", 1),
    ("swish_fabric", "SWISH", "tecido", "fabric swish movement, soft", 1),
    ("glitch_digital", "GLITCH", "glitch digital", "short digital glitch burst", 1),
    ("glitch_vhs", "GLITCH", "VHS", "VHS tracking error glitch distortion", 1),
    ("glitch_data", "GLITCH", "data corruption", "data corruption stutter glitch", 1),
    ("noise_vinyl", "NOISE", "crackle de vinil", "vinyl record crackle texture, warm", 2),
    ("noise_static", "NOISE", "estática TV", "short TV static burst", 1),
    ("noise_riser", "NOISE", "riser de ruído", "white noise riser sweep building up", 2),
]


def post(path, body):
    req = urllib.request.Request(BASE + path, data=json.dumps(body).encode(),
                                 headers={"xi-api-key": KEY, "Content-Type": "application/json"}, method="POST")
    return json.loads(urllib.request.urlopen(req, timeout=40).read())


def get(path):
    req = urllib.request.Request(BASE + path, headers={"xi-api-key": KEY})
    return json.loads(urllib.request.urlopen(req, timeout=40).read())


def gerar(nome, prompt, dur):
    try:
        r = post("/v1/task/sound-effect", {"text": prompt, "duration_seconds": dur})
        tid = r.get("task_id")
        for _ in range(25):
            t = get("/v1/task/" + str(tid))
            if t.get("status") == "done":
                url = (t.get("metadata") or {}).get("audio_url")
                if url:
                    dl = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})  # CDN bloqueia sem UA (403)
                    data = urllib.request.urlopen(dl, timeout=60).read()
                    (PUB / f"{nome}.mp3").write_bytes(data)
                    return True
                return False
            if t.get("status") == "error":
                return False
            time.sleep(2)
    except Exception as e:
        print(f"  {nome} falhou: {str(e)[:60]}")
    return False


def main():
    PUB.mkdir(parents=True, exist_ok=True)
    manifest = []
    ok = 0
    for nome, cat, uso, prompt, dur in LIB:
        if gerar(nome, prompt, dur):
            manifest.append({"nome": nome, "cat": cat, "uso": uso, "rel": f"sfx/{nome}.mp3"})
            ok += 1
            print(f"  OK {cat:<10} {nome}")
        else:
            print(f"  -- FALHOU {nome}")
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n{ok}/{len(LIB)} SFX gerados -> public/sfx/ | manifesto -> src/sfx_lib.json")


if __name__ == "__main__":
    main()
