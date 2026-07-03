"""Pass ADITIVO: detecta DATAS faladas (mês+ano ou ano) nas words e marca pra
exibir em fonte grande na tela, sincronizado à fala. Escreve 'datas' no timeline.json.
"""
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

TESTE = Path(r"F:/Canal Dark/Aplicativo de Edição/banco-videos/teste")
TIMELINE = TESTE / "timeline.json"
WORDS = TESTE / "words.json"

MESES = {
    # EN
    "january": "January", "february": "February", "march": "March", "april": "April", "may": "May",
    "june": "June", "july": "July", "august": "August", "september": "September", "october": "October",
    "november": "November", "december": "December",
    # PT
    "janeiro": "Janeiro", "fevereiro": "Fevereiro", "março": "Março", "marco": "Março", "abril": "Abril",
    "maio": "Maio", "junho": "Junho", "julho": "Julho", "agosto": "Agosto", "setembro": "Setembro",
    "outubro": "Outubro", "novembro": "Novembro", "dezembro": "Dezembro",
}
ANO = re.compile(r"^(1[0-9]{3}|20[0-9]{2})$")


def clean(w):
    return re.sub(r"[^a-zA-Zçãâáéíóõ0-9]", "", (w or "")).lower()


def main():
    words = json.load(open(WORDS, encoding="utf-8"))
    tl = json.load(open(TIMELINE, encoding="utf-8"))
    datas = []
    for i, w in enumerate(words):
        tok = clean(w["word"])
        m = ANO.match(tok)
        if not m:
            continue
        ano = m.group(0)
        # procura mês até 3 tokens antes
        mes = None
        for j in range(max(0, i - 3), i):
            mc = clean(words[j]["word"])
            if mc in MESES:
                mes = MESES[mc]
        texto = f"{mes} {ano}" if mes else ano
        ini = round(words[i]["start"] - 0.15, 2)
        datas.append({"inicio": max(0, ini), "texto": texto, "dur": 2.6})

    # dedup/space (>= 2.5s entre datas)
    datas.sort(key=lambda d: d["inicio"])
    limpos = []
    for d in datas:
        if limpos and (d["inicio"] - limpos[-1]["inicio"] < 2.5 or d["texto"] == limpos[-1]["texto"]):
            continue
        limpos.append(d)

    tl["datas"] = limpos
    json.dump(tl, open(TIMELINE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"OK: {len(limpos)} datas detectadas")
    for d in limpos:
        print(f"  {d['inicio']:>6.1f}s  {d['texto']}")


if __name__ == "__main__":
    main()
