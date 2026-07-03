"""Pass ADITIVO: monta a TRILHA dinâmica por tópico. Pra cada tópico escolhe uma
música do banco (mood-matched, variando), com CORTE SECO na fronteira + respiro de
silêncio (fade in/out) — variação música/silêncio. Escreve 'musica_segmentos'.
Depende de topicos.py.
"""
import json
import os
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

TESTE = Path(r"F:/Canal Dark/Aplicativo de Edição/banco-videos/teste")
TIMELINE = TESTE / "timeline.json"
# Pasta de trilha: env MUSICA_PASTA (setado pelo template/nicho via vidmator_render) > default.
BANK = Path(os.environ.get("MUSICA_PASTA") or r"D:/Meu Drive/canal_dark_trilhas")


def _catalogo(bank):
    """mood -> [arquivos]. Usa catalogo_trilhas.json se existir; senão AUTO-monta agrupando
    os .mp3/.wav pelo prefixo do nome (ex.: dark_01.mp3 -> 'dark', neutral_3.mp3 -> 'neutral')."""
    cf = bank / "catalogo_trilhas.json"
    if cf.exists():
        return json.load(open(cf, encoding="utf-8"))
    cat = {}
    for p in sorted(bank.glob("*.mp3")) + sorted(bank.glob("*.wav")):
        mood = re.sub(r"[_\-\s]*\d+$", "", p.stem).strip("_- ").lower() or "neutral"
        cat.setdefault(mood, []).append(p.name)
    return cat

VOL = 0.14          # música sob a narração (faixas já normalizadas a -19 LUFS)
GAP_IN = 0.5        # respiro de silêncio no começo do tópico (corte seco + breath)
GAP_OUT = 0.7       # silêncio antes da próxima música
FADE = 0.4          # fade in/out (evita clique no corte)


def main():
    tl = json.load(open(TIMELINE, encoding="utf-8"))
    topicos = tl.get("topicos") or []
    if not topicos:
        print("sem topicos — rode topicos.py antes"); return
    cat = _catalogo(BANK)
    if not cat:
        print(f"trilha: nenhuma faixa em {BANK} -> sem música"); tl["musica_segmentos"] = []
        json.dump(tl, open(TIMELINE, "w", encoding="utf-8"), ensure_ascii=False, indent=2); return
    print(f"trilha: banco={BANK.name} | moods={ {m: len(v) for m, v in cat.items()} }")

    idx = {m: 0 for m in cat}          # rotaciona faixas dentro do mood
    ultimo = None
    segs = []
    for t in topicos:
        mood = t.get("mood", "neutral")
        faixas = cat.get(mood) or cat.get("neutral") or []
        if not faixas:
            continue
        # escolhe variando; evita repetir a mesma faixa seguida
        f = faixas[idx[mood] % len(faixas)]
        if f == ultimo and len(faixas) > 1:
            idx[mood] += 1
            f = faixas[idx[mood] % len(faixas)]
        idx[mood] += 1
        ultimo = f
        ini = round(t["inicio"] + GAP_IN, 2)
        fim = round(t["fim"] - GAP_OUT, 2)
        if fim - ini < 2:   # tópico curto demais p/ música
            continue
        segs.append({
            "inicio": ini, "fim": fim, "vol": VOL, "fade": FADE,
            "track_path": str((BANK / f)).replace("\\", "/"),
            "mood": mood, "titulo": t.get("titulo"),
        })

    tl["musica_segmentos"] = segs
    tl["musica_envelope"] = None  # não usa mais o envelope contínuo
    json.dump(tl, open(TIMELINE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"OK: {len(segs)} segmentos de trilha (corte seco por tópico)")
    for s in segs:
        print(f"  {s['inicio']:>6.1f}-{s['fim']:>6.1f}s  [{s['mood']:<10}] {Path(s['track_path']).name[:40]}")


if __name__ == "__main__":
    main()
