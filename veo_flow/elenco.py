# -*- coding: utf-8 -*-
"""ELENCO — o canal tem host fixo, elenco novo a cada vídeo, ou ninguém?

Desenho do Piter (02/08): "quero que o fluxo entenda de forma natural se aquele
canal precisa de novos personagens em todo vídeo ou se vai ser um host fixo (como
o Russel) e trabalhar conforme essa info".

Três REGIMES, e cada um manda num comportamento diferente do gerador:

  canal   (host fixo)   O personagem vive no PROJETO e é o mesmo em todo vídeo —
                        é o caso do @Russel no AMZ. Criar UMA vez; depois é só
                        mencionar. Foi por isso que o projeto virou "1 por canal":
                        projeto por vídeo mataria o personagem.
  video   (elenco novo) Cada vídeo tem gente própria (uma vítima, uma testemunha,
                        um cientista). O personagem nasce NA COLEÇÃO do vídeo e
                        morre com ela — mencioná-lo no vídeo seguinte é erro.
  nenhum  (sem gente)   Canal de b-roll/ilustração: nada de personagem. É o caso
                        dos gaps do editor VidMator — imagem avulsa, sem menção.

A política mora no personagens.json (campo `escopo`) e no projetos.json
(`elenco`). Sem declaração explícita, INFERE: personagem com escopo=canal ⇒ host
fixo; nada declarado ⇒ nenhum. Inferir é melhor que exigir configuração — canal
novo funciona sem ninguém lembrar de preencher.

Uso:
  from elenco import politica, mencao_para
  politica("AMZ")            -> {"regime": "canal", "host": "Russel", ...}
  mencao_para("AMZ", "05-08-26")  -> "@Russel"  (ou None)
"""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
AQUI = Path(__file__).resolve().parent
F_PERS = AQUI / "personagens.json"
F_PROJ = AQUI / "projetos.json"

REGIMES = ("canal", "video", "nenhum")


def _ler(f):
    try:
        return json.loads(f.read_text(encoding="utf-8"))
    except Exception:
        return {}


def politica(canal):
    """Regime do canal + quem é o host, se houver."""
    pers = _ler(F_PERS).get(canal) or {}
    proj = _ler(F_PROJ).get(canal) or {}
    regime = proj.get("elenco")
    if regime not in REGIMES:
        # INFERÊNCIA: o que já está declarado no personagem manda
        esc = (pers.get("escopo") or "").lower()
        regime = "canal" if esc == "canal" else ("video" if esc == "video" else "nenhum")
    return {"canal": canal, "regime": regime,
            "host": pers.get("nome") if regime == "canal" else None,
            "mencao": pers.get("mencao") if regime == "canal" else None,
            "descricao": pers.get("descricao", ""),
            "voz": pers.get("voz"), "voz_ref": pers.get("voz_ref"),
            "projeto": proj.get("projeto")}


def mencao_para(canal, video=None):
    """A menção que o PROMPT deve usar neste vídeo — ou None.

    host fixo -> sempre a mesma (@Russel). elenco novo -> a do personagem criado
    PARA ESTE vídeo (nunca a de outro; personagem de vídeo passado não existe mais
    na coleção nova). nenhum -> None, e o prompt vai sem gente."""
    p = politica(canal)
    if p["regime"] == "canal":
        return p["mencao"] or (f"@{p['host']}" if p["host"] else None)
    if p["regime"] == "video" and video:
        elenco = (_ler(F_PROJ).get(canal, {}).get("elenco_por_video") or {}).get(video)
        if elenco:
            return elenco.get("mencao") or f"@{elenco.get('nome', '')}".rstrip("@")
    return None


def precisa_criar(canal, video=None):
    """(bool, motivo) — o gerador deve criar personagem antes de gerar?"""
    p = politica(canal)
    if p["regime"] == "nenhum":
        return False, "canal sem personagem"
    if p["regime"] == "canal":
        if p["mencao"] or p["host"]:
            return False, f"host fixo já existe ({p['host']})"
        return True, "host fixo declarado mas ainda não criado"
    if not video:
        return False, "elenco por vídeo, mas nenhum vídeo informado"
    if mencao_para(canal, video):
        return False, f"elenco deste vídeo já existe"
    return True, "elenco por vídeo: este vídeo ainda não tem personagem"


def registrar_elenco_do_video(canal, video, nome, mencao=None, descricao=""):
    """Grava o personagem criado PARA um vídeo (regime `video`)."""
    d = _ler(F_PROJ)
    c = d.setdefault(canal, {})
    c.setdefault("elenco_por_video", {})[video] = {
        "nome": nome, "mencao": mencao or f"@{nome}", "descricao": descricao}
    F_PROJ.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")


def definir_regime(canal, regime):
    if regime not in REGIMES:
        raise ValueError(f"regime deve ser um de {REGIMES}")
    d = _ler(F_PROJ)
    d.setdefault(canal, {})["elenco"] = regime
    F_PROJ.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    return politica(canal)


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("canal", nargs="?", default="")
    ap.add_argument("--video", default="")
    ap.add_argument("--regime", default="", choices=["", *REGIMES])
    a = ap.parse_args()

    if a.canal and a.regime:
        print(json.dumps(definir_regime(a.canal, a.regime), ensure_ascii=False, indent=1))
        return
    if a.canal:
        p = politica(a.canal)
        print(json.dumps(p, ensure_ascii=False, indent=1))
        cria, motivo = precisa_criar(a.canal, a.video or None)
        print(f"criar personagem? {'SIM' if cria else 'não'} — {motivo}")
        print(f"menção no prompt: {mencao_para(a.canal, a.video or None) or '(nenhuma)'}")
        return
    # sem argumento: panorama de todos os canais registrados
    canais = sorted(set(_ler(F_PERS)) | set(_ler(F_PROJ)))
    print(f"{'CANAL':<8} {'REGIME':<10} {'HOST':<14} MENÇÃO")
    for c in canais:
        p = politica(c)
        print(f"  {c:<6} {p['regime']:<10} {(p['host'] or '—'):<14} {p['mencao'] or '—'}")


if __name__ == "__main__":
    main()
