"""Pass ADITIVO (só nichos com banco_epoca, ex.: documentário): substitui o footage das cenas
ATMOSFÉRICAS por clipes do BANCO DE ÉPOCA (archive real). Gemini casa cada cena com o clipe cujo
`desc` melhor ilustra. Reuso cap 2x. Roda DEPOIS do resolver (sobrescreve o stock onde há match).
"""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
TESTE = Path(r"F:/Canal Dark/Aplicativo de Edição/banco-videos/teste")
TIMELINE = TESTE / "timeline.json"
CATALOGO = Path(r"D:/Meu Drive/canal_dark_footage_epoca/catalogo.json")


def main():
    from preset import carregar
    tl = json.load(open(TIMELINE, encoding="utf-8"))
    P = carregar(tl)
    if not P.get("banco_epoca"):
        print(f"epoca: nicho={P['_nicho']} não usa banco de época -> skip")
        return
    if not CATALOGO.exists():
        print("epoca: catálogo de época não existe -> skip")
        return
    cat = json.load(open(CATALOGO, encoding="utf-8"))
    cenas = tl["cenas"]
    # ALVO: toda cena servida por STOCK genérico (L3/L4/L5 = footage/foto MODERNA) -> trocar por época.
    # MANTÉM L1-epoca (já), L2/L2t-commons (imagens de época reais), pessoas/mapas/datas (cards).
    alvos = [c for c in cenas if str(c.get("nivel", "")).startswith(("L3", "L4", "L5"))]
    if not alvos or not cat:
        print("epoca: nenhuma cena de stock p/ trocar")
        return
    CAP = 3   # reuso máx por clipe (47 clipes p/ ~40 cenas -> reuso baixo)
    usos = {}
    feito = set()

    def assign(c, ci):
        c["clip_path"] = cat[ci]["file"]
        c["media_tipo"] = "video"
        c["nivel"] = "L1-epoca"
        c["clip_dur"] = 5
        c["presentacao"] = None   # era imagem (Ken Burns) -> agora vídeo de época
        usos[ci] = usos.get(ci, 0) + 1
        feito.add(c["idx"])

    bank_txt = "  ".join(f"[{i}] {c.get('desc', '')}" for i, c in enumerate(cat))
    beats_txt = "  ".join(f"[{c['idx']}] {c['texto'][:70].replace(chr(34), '')}" for c in alvos)
    from gemini_api import gemini_arr
    prompt = ("For each narration BEAT of a WWII documentary, pick the archive CLIP index whose description best "
              "ILLUSTRATES that line. SPREAD choices across beats for VARIETY (avoid repeating a clip). "
              "Return ONLY a JSON array of objects {scene, clip} (both numbers). CLIPS: "
              + bank_txt + "   BEATS: " + beats_txt)
    arr = gemini_arr(prompt, 220) or []
    by_idx = {c["idx"]: c for c in cenas}
    for o in arr:
        try:
            s = int(o["scene"]); ci = int(o["clip"])
        except Exception:
            continue
        c = by_idx.get(s)
        if c and c["idx"] not in feito and 0 <= ci < len(cat) and usos.get(ci, 0) < CAP:
            assign(c, ci)
    # FILL: cena de stock que o Gemini não casou -> clipe menos usado (garante época em todas)
    for c in alvos:
        if c["idx"] in feito:
            continue
        ci = min(range(len(cat)), key=lambda i: usos.get(i, 0))
        if usos.get(ci, 0) >= CAP:
            break
        assign(c, ci)
    json.dump(tl, open(TIMELINE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"epoca: {len(feito)} cenas com footage de época real (de {len(cat)} clipes; {len(alvos)} eram stock)")


if __name__ == "__main__":
    main()
