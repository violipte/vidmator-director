"""STORY ENGINE — pass de FOLEY: objetos-âncora das cenas -> one-shots no MOMENTO em que a palavra
é FALADA (âncora via words.json, mesma técnica do produto_cta). tl["foleys"]=[{t,file,gain_db}].
Gated por preset.foley.ativo. Máx 1 foley por objeto por cena; cooldown global de 8s (não vira metralhadora).
"""
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
TESTE = Path(r"F:/Canal Dark/Aplicativo de Edição/banco-videos/teste")
TIMELINE = TESTE / "timeline.json"
CENAS = TESTE / "cenas_historia.json"
WORDS = TESTE / "words.json"

# objeto (do analisador, lower/parcial) -> foley id no banco
OBJ_MAP = [
    (("letter", "envelope"), "letter_unfold"),
    (("ring",), "ring_box"),
    (("photo", "photograph", "polaroid", "clipping", "clippings"), "polaroid"),
    (("door",), "door_open"),
    (("phone", "message"), "phone_vibrate"),
    (("pen", "write", "wrote", "writing"), "pen_writing"),
    (("wine", "glass"), "wine_pour"),
    (("suitcase", "bag", "luggage"), "suitcase_zip"),
    (("match", "candle"), "match_strike"),
    (("vinyl", "record"), "vinyl_start"),
    (("radio",), "old_radio"),
    (("heart", "heartbeat"), "heartbeat"),
    (("footsteps", "walked away", "walking away"), "footsteps_leave"),
    (("book", "page"), "page_turn"),
]
COOLDOWN = 8.0


def main():
    from preset import carregar
    tl = json.load(open(TIMELINE, encoding="utf-8"))
    cfg = (carregar(tl).get("foley") or {})
    if not cfg.get("ativo"):
        print("foley: nicho sem foley -> skip"); return
    if not (CENAS.exists() and WORDS.exists()):
        print("foley: ERRO — precisa de cenas_historia.json + words.json"); sys.exit(1)
    dados = json.load(open(CENAS, encoding="utf-8"))
    cenas = [c for c in dados.get("cenas", []) if "inicio" in c]
    words = json.load(open(WORDS, encoding="utf-8"))
    toks = [(str(w.get("word", "")).lower().strip(".,!?;:'\"-()"), w.get("start", 0)) for w in words]

    banco = Path(cfg.get("banco") or r"D:/Meu Drive/canal_dark_foley")
    cat = json.load(open(banco / "catalogo.json", encoding="utf-8"))
    gain = float(cfg.get("gain_db", -6))

    def foley_de(obj):
        o = obj.lower()
        for chaves, fid in OBJ_MAP:
            if any(k in o for k in chaves):
                return fid if fid in cat else None
        return None

    hits = []
    ultimo_t = -99.0
    for c in sorted(cenas, key=lambda x: x["inicio"]):
        ini, fim = c["inicio"], c.get("fim", c["inicio"] + 20)
        usados_cena = set()
        for obj in (c.get("objetos") or []):
            fid = foley_de(str(obj))
            if not fid or fid in usados_cena:
                continue
            # acha a 1ª vez que a palavra do objeto é FALADA dentro da janela da cena
            alvo = str(obj).lower().split()[0]
            t = next((wt for w, wt in toks if ini <= wt <= fim and alvo in w), None)
            if t is None or t - ultimo_t < COOLDOWN:
                continue
            hits.append({"t": round(t, 2), "file": cat[fid]["file"], "foley": fid, "gain_db": gain})
            usados_cena.add(fid)
            ultimo_t = t

    tl["foleys"] = hits
    json.dump(tl, open(TIMELINE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"foley: {len(hits)} one-shots | " + ", ".join(f"{h['foley']}@{h['t']:.0f}s" for h in hits[:10]))


if __name__ == "__main__":
    main()
