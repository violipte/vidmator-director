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
BANCO = Path(r"D:/Meu Drive/canal_dark_ambiencias")
CONFIG = Path(r"F:/Canal Dark/Aplicativo de Edição/video-automator/config.json")
KEY = json.load(open(CONFIG, encoding="utf-8")).get("ai33_api_key", "")
BASE = "https://api.ai33.pro"
DUR = 20  # s por loop (mix em volume baixo, com loop no Remotion)

AMBIENCIAS = [
    ("rain_window",  "gentle steady rain tapping against a window, cozy quiet interior, seamless ambient loop", ["rain", "cozy", "interior", "sad", "calm"], "melancolico"),
    ("rain_thunder", "steady rain with soft distant thunder rolls, ambient loop", ["rain", "thunder", "storm", "tension"], "tenso"),
    ("fireplace",    "warm crackling fireplace, gentle wood pops, quiet room, seamless loop", ["fire", "warm", "cozy", "home", "night"], "acolhedor"),
    ("cafe",         "quiet cozy cafe ambience, soft unintelligible murmur, occasional cup clinks, loop", ["cafe", "city", "people", "date"], "neutro"),
    ("city_street",  "distant city street ambience, soft traffic hum, occasional far car horn, loop", ["city", "street", "urban"], "neutro"),
    ("ocean_waves",  "soft ocean waves washing on a sandy beach, gentle and slow, seamless loop", ["beach", "sea", "waves", "peaceful"], "calmo"),
    ("forest_birds", "peaceful morning forest with soft songbirds and light breeze, loop", ["forest", "birds", "morning", "nature"], "leve"),
    ("night_crickets","warm summer night with crickets and very distant owls, seamless loop", ["night", "crickets", "summer", "quiet"], "intimo"),
    ("wind_leaves",  "soft wind moving through tree leaves, calm outdoor air, loop", ["wind", "trees", "outdoor", "autumn"], "melancolico"),
    ("snow_wind",    "cold muffled winter wind, distant and lonely, snowy stillness, loop", ["winter", "snow", "wind", "cold", "lonely"], "triste"),
    ("train_interior","rhythmic train car interior, soft rails clatter and hum, seamless loop", ["train", "travel", "journey"], "nostalgico"),
    ("car_rain",     "inside a parked car with rain drumming softly on the roof, intimate, loop", ["car", "rain", "intimate", "conversation"], "intimo"),
    ("hospital",     "very quiet hospital corridor ambience, soft distant monitor beeps, air hum, loop", ["hospital", "tense", "sad", "waiting"], "triste"),
    ("church",       "large empty church hall ambience, airy reverb, faint distant bells, loop", ["church", "wedding", "solemn", "reverb"], "solene"),
    ("library",      "silent library ambience, faint page turns and distant footsteps, loop", ["library", "quiet", "study"], "neutro"),
    ("old_house",    "old wooden house at night, soft creaks and a distant ticking clock, loop", ["house", "old", "night", "memory"], "nostalgico"),
    ("clock",        "slow wall clock ticking in a silent room, steady and lonely, seamless loop", ["clock", "time", "waiting", "tension"], "tenso"),
    ("airport",      "airport hall ambience, soft crowd murmur and unintelligible distant announcements, loop", ["airport", "farewell", "travel", "crowd"], "nostalgico"),
    ("park",         "city park afternoon, distant activity, birds, a light breeze, loop", ["park", "afternoon", "peaceful"], "leve"),
    ("harbor",       "quiet harbor ambience, seagulls, ropes creaking, water lapping on hulls, loop", ["harbor", "sea", "gulls", "departure"], "nostalgico"),
    # --- complemento romance/emocional (2026-07-07) ---
    ("restaurant",   "quiet intimate restaurant dinner ambience, soft cutlery, low murmur, candles atmosphere, loop", ["restaurant", "dinner", "date", "intimate"], "intimo"),
    ("kitchen",      "quiet home kitchen ambience in the morning, gentle dishes and soft frying pan sounds, loop", ["kitchen", "home", "cooking", "morning"], "acolhedor"),
    ("bedroom_night","quiet bedroom at night, soft room tone, distant traffic through the window, loop", ["bedroom", "night", "intimate", "quiet"], "intimo"),
    ("office",       "office ambience, soft keyboards, distant phones, air conditioning hum, loop", ["office", "work", "day"], "neutro"),
    ("wedding",      "wedding reception ambience, joyful crowd murmur, glasses clinking, festive air, loop", ["wedding", "party", "celebration", "crowd"], "alegre"),
    ("storm_heavy",  "heavy dramatic thunderstorm, intense rain and close thunder cracks, loop", ["storm", "dramatic", "breakup", "tension"], "dramatico"),
    ("city_night_rain","city street at night in the rain, wet asphalt, distant neon buzz and cars passing, loop", ["city", "night", "rain", "lonely"], "melancolico"),
    ("countryside",  "countryside farm morning, distant rooster, cowbells, gentle breeze in the grass, loop", ["farm", "countryside", "morning", "rural"], "leve"),
    ("rooftop",      "city rooftop at dusk, open wind, distant city hum far below, loop", ["rooftop", "city", "confession", "dusk"], "nostalgico"),
    ("train_station","train station platform, echoing announcements unintelligible, distant train brakes, loop", ["station", "farewell", "departure", "travel"], "nostalgico"),
    ("bus",          "city bus interior, engine hum, soft rattles, occasional stops, loop", ["bus", "commute", "city", "travel"], "neutro"),
    ("hospital_room","quiet hospital room, close soft monitor beeps, gentle air, heavy stillness, loop", ["hospital", "grief", "bedside", "sad"], "triste"),
    ("carnival",     "distant carnival fair at night, faint rides and crowd joy carried on the wind, loop", ["carnival", "fair", "nostalgic", "date"], "nostalgico"),
    ("graduation",   "ceremony hall ambience, applause swells and proud crowd murmur, loop", ["graduation", "milestone", "applause", "crowd"], "alegre"),
    ("beach_bonfire","evening beach with soft waves and a crackling bonfire close by, loop", ["beach", "bonfire", "night", "romantic"], "intimo"),
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
