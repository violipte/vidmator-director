"""STORY ENGINE — pass de AMBIÊNCIA ASMR: cenas_historia.json -> janelas de som de ambiente no timeline.
Mapeia o `lugar` de cada cena pro banco (catalogo.json), FUNDE cenas consecutivas com a mesma ambiência
(não reinicia o loop a cada cena) e grava tl["ambiencias"]=[{inicio,fim,file,gain_db}].
Gated por preset.ambiencia.ativo. Nível padrão = -6dB relativo (escolha "D" do Piter, 2026-07-09).
"""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
TESTE = Path(r"F:/Canal Dark/Aplicativo de Edição/banco-videos/teste")
TIMELINE = TESTE / "timeline.json"
CENAS = TESTE / "cenas_historia.json"

# lugar (vocabulário do analisador) -> id no banco de ambiências; sinônimos/derivas do LLM inclusos
LUGAR_MAP = {
    "church": "church", "wedding": "wedding", "office": "office", "bedroom": "bedroom_night",
    "kitchen": "kitchen", "cafe": "cafe", "restaurant": "restaurant", "street": "city_street",
    "city_night_rain": "city_night_rain", "rain_window": "rain_window", "car_rain": "car_rain",
    "hospital": "hospital", "hospital_room": "hospital_room", "library": "library",
    "old_house": "old_house", "park": "park", "beach": "ocean_waves", "train": "train_interior",
    "train_station": "train_station", "airport": "airport", "rooftop": "rooftop",
    "countryside": "countryside", "harbor": "harbor", "storm": "storm_heavy",
    "forest": "forest_birds", "night_outdoor": "night_crickets",
    # genéricos: interior neutro fica SEM ambiência de lugar; usa tempo como pista
    "generic_interior": None, "generic_exterior": "city_street",
}
TEMPO_FALLBACK = {"night": "night_crickets", "flashback": None, "present": None, "day": None}
MERGE_GAP = 2.0   # cenas coladas (<2s de buraco) com mesma ambiência = 1 janela só


def main():
    from preset import carregar
    tl = json.load(open(TIMELINE, encoding="utf-8"))
    cfg = (carregar(tl).get("ambiencia") or {})
    if not cfg.get("ativo"):
        print("ambiencia: nicho sem ambiência -> skip"); return
    if not CENAS.exists():
        print("ambiencia: ERRO — sem cenas_historia.json (rode analisar_cenas antes)"); sys.exit(1)
    dados = json.load(open(CENAS, encoding="utf-8"))
    cenas = [c for c in dados.get("cenas", []) if "inicio" in c and "fim" in c]
    if not cenas:
        print("ambiencia: ERRO — cenas sem timestamps (words.json não ancorou)"); sys.exit(1)

    banco = Path(cfg.get("banco") or r"D:/Meu Drive/canal_dark_ambiencias")
    cat = json.load(open(banco / "catalogo.json", encoding="utf-8"))
    gain = float(cfg.get("gain_db", -6))

    janelas = []
    for c in sorted(cenas, key=lambda x: x["inicio"]):
        amb = LUGAR_MAP.get(str(c.get("lugar", "")).lower())
        if amb is None:
            amb = TEMPO_FALLBACK.get(str(c.get("tempo", "")).lower())
        if not amb or amb not in cat:
            continue
        f = cat[amb]["file"]
        if janelas and janelas[-1]["file"] == f and c["inicio"] - janelas[-1]["fim"] <= MERGE_GAP:
            janelas[-1]["fim"] = c["fim"]          # funde com a janela anterior
        else:
            janelas.append({"inicio": round(c["inicio"], 2), "fim": round(c["fim"], 2),
                            "file": f, "amb": amb, "gain_db": gain})

    tl["ambiencias"] = janelas
    json.dump(tl, open(TIMELINE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    cobre = sum(j["fim"] - j["inicio"] for j in janelas)
    print(f"ambiencia: {len(janelas)} janelas ({cobre:.0f}s cobertos) | " +
          ", ".join(f"{j['amb']}@{j['inicio']:.0f}s" for j in janelas[:8]))


if __name__ == "__main__":
    main()
