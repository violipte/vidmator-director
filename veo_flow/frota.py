# -*- coding: utf-8 -*-
"""FROTA — conta ↔ perfil ↔ canais. O roteador da produção paralela.

Desenho em `FROTA.md`. A regra que manda: **o personagem vive no projeto, o projeto
vive numa conta**, então um CANAL pertence a uma conta e não migra sem perder o
elenco. Por isso o roteamento é sempre pelo CANAL — nunca "qual perfil está livre".

Hoje 2 perfis; o plano é ~11 (5 do família + 6 de um 2º Ultra). Crescer deve ser
acrescentar uma linha aqui, não repensar o fluxo.

Uso:
  python frota.py                                   # panorama
  python frota.py --registrar conta2 --conta x@y.com --plano familia --dono editor
  python frota.py --canal AMZ --perfil chrome_profile
  python frota.py --rota AMZ                        # qual perfil roda esse canal
"""
import argparse
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
AQUI = Path(__file__).resolve().parent
F_FROTA = AQUI / "frota.json"
F_PROJ = AQUI / "projetos.json"


def _ler(f, padrao=None):
    try:
        return json.loads(f.read_text(encoding="utf-8"))
    except Exception:
        return padrao if padrao is not None else {}


def _salvar(f, d):
    f.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")


def frota():
    d = _ler(F_FROTA)
    if "perfis" not in d:
        # semente a partir do que já existe — não obriga migração manual
        d = {"perfis": {
            "chrome_profile": {"conta": "", "plano": "ultra", "dono": "flow",
                               "canais": ["AMZ"]},
            "chrome_profile_conta2": {"conta": "", "plano": "familia",
                                      "dono": "editor", "canais": []}}}
        _salvar(F_FROTA, d)
    return d


def registrar(perfil, conta="", plano="familia", dono="editor"):
    d = frota()
    p = d["perfis"].setdefault(perfil, {"canais": []})
    if conta:
        p["conta"] = conta
    p["plano"] = plano
    p["dono"] = dono
    p.setdefault("canais", [])
    _salvar(F_FROTA, d)
    return p


def atribuir_canal(canal, perfil):
    """Um canal só pode estar em UM perfil — mover exige recriar projeto e
    personagem na conta nova, então aqui a troca é explícita e avisada."""
    d = frota()
    if perfil not in d["perfis"]:
        return None, f"perfil não registrado: {perfil}"
    antigo = next((k for k, v in d["perfis"].items()
                   if canal in (v.get("canais") or []) and k != perfil), None)
    if antigo:
        d["perfis"][antigo]["canais"].remove(canal)
    d["perfis"][perfil].setdefault("canais", []).append(canal)
    _salvar(F_FROTA, d)
    aviso = (f"⚠️ {canal} saiu de {antigo}: projeto e personagens NÃO migram entre "
             f"contas — recrie no perfil novo") if antigo else ""
    return d["perfis"][perfil], aviso


def rota(canal):
    """Perfil que deve rodar este canal (+ dono). None se o canal não tem casa."""
    for nome, p in frota()["perfis"].items():
        if canal in (p.get("canais") or []):
            return {"perfil": nome, "dono": p.get("dono"), "conta": p.get("conta"),
                    "plano": p.get("plano"),
                    "caminho": str(AQUI / nome)}
    return None


def perfis_do_dono(dono):
    return [nome for nome, p in frota()["perfis"].items() if p.get("dono") == dono]


def capacidade():
    """Quantos navegadores podem gerar AO MESMO TEMPO (1 por perfil)."""
    d = frota()["perfis"]
    return {"perfis": len(d), "contas": len({p.get("conta") or n for n, p in d.items()}),
            "canais": sum(len(p.get("canais") or []) for p in d.values())}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--registrar", default="")
    ap.add_argument("--conta", default="")
    ap.add_argument("--plano", default="familia", choices=["familia", "ultra"])
    ap.add_argument("--dono", default="editor")
    ap.add_argument("--canal", default="")
    ap.add_argument("--perfil", default="")
    ap.add_argument("--rota", default="")
    a = ap.parse_args()

    if a.registrar:
        p = registrar(a.registrar, a.conta, a.plano, a.dono)
        print(f"registrado {a.registrar}: {json.dumps(p, ensure_ascii=False)}")
        print("falta o LOGIN (uma vez):")
        print(f'  "F:/Canal Dark/veo_venv/Scripts/python.exe" flow_driver.py login '
              f'--perfil "{AQUI / a.registrar}"')
        return
    if a.canal and a.perfil:
        p, aviso = atribuir_canal(a.canal, a.perfil)
        if p is None:
            print(aviso)
            return
        print(f"{a.canal} -> {a.perfil} | canais: {p['canais']}")
        if aviso:
            print(aviso)
        return
    if a.rota:
        r = rota(a.rota)
        print(json.dumps(r, ensure_ascii=False, indent=1) if r
              else f"canal {a.rota} não tem perfil — atribua com --canal {a.rota} --perfil <nome>")
        return

    d = frota()["perfis"]
    cap = capacidade()
    print(f"{'PERFIL':<26} {'DONO':<8} {'PLANO':<9} {'CONTA':<24} CANAIS")
    for nome, p in d.items():
        print(f"  {nome:<24} {p.get('dono', '—'):<8} {p.get('plano', '—'):<9} "
              f"{(p.get('conta') or '(sem e-mail)'):<24} {', '.join(p.get('canais') or []) or '—'}")
    print(f"\ncapacidade: {cap['perfis']} perfil(is) = {cap['perfis']} geração(ões) "
          f"simultânea(s) | {cap['canais']} canal(is)")
    orfaos = [c for c in _ler(F_PROJ) if not rota(c)]
    if orfaos:
        print(f"⚠️ canais SEM perfil: {', '.join(orfaos)}")


if __name__ == "__main__":
    main()
