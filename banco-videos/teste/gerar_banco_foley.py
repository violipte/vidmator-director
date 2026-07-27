"""Gera o BANCO DE AMBIÊNCIAS ASMR (sons de ambiente p/ mixar sob a narração) via ai33.pro sound-effect.
Cada ambiência: prompt -> POST /v1/task/sound-effect -> poll -> baixa mp3 -> banco + catalogo.json (tags/mood).
Licença limpa (gerado sob a conta). Idempotente: pula as que já existem.

Uso: python gerar_banco_ambiencias.py [--um <id>]   (--um gera só uma, p/ teste)
"""
import json
import sys
import time
import urllib.request
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
BANCO = Path(r"D:/Meu Drive/canal_dark_foley")
CONFIG = Path(r"F:/Canal Dark/Aplicativo de Edição/video-automator/config.json")
KEY = json.load(open(CONFIG, encoding="utf-8")).get("ai33_api_key", "")
BASE = "https://api.ai33.pro"
DUR = 4  # s: one-shots de detalhe (não loops)

AMBIENCIAS = [
    ("letter_unfold", "old paper letter being unfolded slowly, gentle paper crinkle, close and intimate", ["letter", "paper", "memory"], "detalhe"),
    ("pen_writing",   "fountain pen writing on paper, soft scratches, close ASMR detail", ["writing", "letter", "pen"], "detalhe"),
    ("page_turn",     "single soft book page turn, close and delicate", ["book", "page", "reading"], "detalhe"),
    ("polaroid",      "vintage instant camera click and photo ejecting with a soft whir", ["photo", "camera", "memory"], "detalhe"),
    ("camera_shutter","classic film camera shutter click, single shot", ["photo", "camera"], "detalhe"),
    ("phone_vibrate", "phone vibrating twice on a wooden table", ["phone", "message", "modern"], "detalhe"),
    ("door_open",     "old wooden door opening slowly with a gentle creak", ["door", "arrival", "house"], "detalhe"),
    ("door_close",    "wooden door closing softly, latch click, final", ["door", "departure", "end"], "detalhe"),
    ("footsteps_leave","slow footsteps walking away on a wooden floor, fading", ["footsteps", "leaving", "sad"], "detalhe"),
    ("heartbeat",     "single slow human heartbeat, deep and soft, two beats", ["heart", "emotion", "tension"], "detalhe"),
    ("wine_pour",     "wine being poured slowly into a glass, gentle liquid sound", ["wine", "dinner", "date"], "detalhe"),
    ("match_strike",  "a match striking and flame igniting softly", ["fire", "candle", "beginning"], "detalhe"),
    ("vinyl_start",   "vinyl record starting: needle drop, warm crackle beginning", ["vinyl", "music", "nostalgia"], "detalhe"),
    ("old_radio",     "old radio tuning briefly through soft static", ["radio", "vintage", "memory"], "detalhe"),
    ("suitcase_zip",  "suitcase zipping closed slowly, final and heavy", ["suitcase", "departure", "travel"], "detalhe"),
    ("ring_box",      "small velvet ring box opening with a soft snap", ["ring", "proposal", "wedding"], "detalhe"),
]


def _req(method, path, data=None, headers=None):
    h = {"xi-api-key": KEY, **(headers or {})}
    if data is not None and not isinstance(data, bytes):
        data = json.dumps(data).encode()
        h["Content-Type"] = "application/json"
    r = urllib.request.urlopen(urllib.request.Request(BASE + path, data=data, headers=h, method=method), timeout=90)
    return json.loads(r.read())


def gerar(amb_id, prompt):
    r = _req("POST", "/v1/task/sound-effect", {"text": prompt, "duration_seconds": DUR})
    tid = r.get("task_id") or (r.get("data") or {}).get("task_id")
    if not tid:
        print(f"  !! sem task_id: {str(r)[:120]}"); return None
    for _ in range(60):
        time.sleep(4)
        st = _req("GET", f"/v1/task/{tid}")
        d = st.get("data") or st
        if d.get("status") == "done":
            meta = d.get("metadata") or {}
            url = meta.get("audio_url") or meta.get("url")
            if not url:
                print(f"  !! done sem audio_url: {str(meta)[:120]}"); return None
            dest = BANCO / f"{amb_id}.mp3"
            # CDN (cdn.ai33.pro) bloqueia UA do urllib (Cloudflare 1010) -> UA de navegador
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            dest.write_bytes(urllib.request.urlopen(req, timeout=120).read())
            return dest
        if d.get("status") == "error":
            print(f"  !! erro: {str(d)[:120]}"); return None
    print("  !! timeout"); return None


def main():
    if not KEY:
        print("!!! sem ai33_api_key no config.json"); return
    BANCO.mkdir(parents=True, exist_ok=True)
    cat_path = BANCO / "catalogo.json"
    cat = json.load(open(cat_path, encoding="utf-8")) if cat_path.exists() else {}
    so_um = sys.argv[sys.argv.index("--um") + 1] if "--um" in sys.argv else None

    for amb_id, prompt, tags, mood in AMBIENCIAS:
        if so_um and amb_id != so_um:
            continue
        if amb_id in cat and (BANCO / cat[amb_id]["file"]).exists():
            print(f"  = {amb_id} já existe"); continue
        print(f"[{amb_id}] gerando...")
        dest = gerar(amb_id, prompt)
        if dest:
            cat[amb_id] = {"file": dest.name, "tags": tags, "mood": mood, "dur": DUR}
            json.dump(cat, open(cat_path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
            print(f"  ✓ {dest.name} ({dest.stat().st_size//1024}KB)")
    print(f"=== banco: {len(cat)} ambiências em {BANCO} ===")


if __name__ == "__main__":
    main()
