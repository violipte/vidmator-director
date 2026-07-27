"""STORY ENGINE — pass de PERSONAGENS: recortes do elenco nas laterais, POR PRESENÇA na cena.
Usa o casting do analisador (Clara->woman_1 etc.). 1 imagem padrão por personagem (decisão Piter
2026-07-17: sem variação de emoção). Lado FIXO por personagem (woman_1=left, man_1=right).
Anota cena-a-cena do TIMELINE (beats do Director): cena["personagens"]=[{img,lado}].
Gated por preset.personagens.ativo; se a biblioteca ainda não existe, skip com aviso (não quebra).
"""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
TESTE = Path(r"F:/Canal Dark/Aplicativo de Edição/banco-videos/teste")
TIMELINE = TESTE / "timeline.json"
CENAS = TESTE / "cenas_historia.json"
LADOS = {"woman_1": "left", "man_1": "right", "woman_2": "left", "man_2": "right"}


def main():
    from preset import carregar
    tl = json.load(open(TIMELINE, encoding="utf-8"))
    cfg = (carregar(tl).get("personagens") or {})
    if not cfg.get("ativo"):
        print("personagens: nicho sem elenco -> skip"); return
    if not CENAS.exists():
        print("personagens: ERRO — sem cenas_historia.json"); sys.exit(1)
    dados = json.load(open(CENAS, encoding="utf-8"))
    historia = [c for c in dados.get("cenas", []) if "inicio" in c]
    casting = {k: v for k, v in (dados.get("casting") or {}).items() if v}

    banco = Path(cfg.get("banco") or r"F:/Canal Dark/Aplicativo de Edição/banco-videos/personagens_historia")
    imgs = {}
    for lib_id in set(casting.values()):
        cand = sorted(banco.glob(f"{lib_id}*.png"))
        if cand:
            imgs[lib_id] = cand[0].name          # 1 imagem padrão por personagem
    if not imgs:
        print(f"personagens: biblioteca vazia em {banco} -> skip (gerar woman_1/man_1 primeiro)"); return

    def cena_da_historia(t):
        for h in historia:
            if h["inicio"] <= t <= h.get("fim", h["inicio"] + 999):
                return h
        return None

    n = 0
    for c in tl.get("cenas", []):
        meio = (c.get("inicio", 0) + c.get("fim", 0)) / 2
        h = cena_da_historia(meio)
        if not h:
            continue
        pres = []
        for nome in (h.get("personagens") or []):
            lib = casting.get(nome)
            if lib and lib in imgs:
                pres.append({"img": imgs[lib], "lado": LADOS.get(lib, "right"), "lib": lib})
        if pres:
            c["personagens"] = pres[:2]          # máx 2 (1 por lateral)
            n += 1
    json.dump(tl, open(TIMELINE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"personagens: {n} beats anotados | elenco: {imgs}")


if __name__ == "__main__":
    main()
