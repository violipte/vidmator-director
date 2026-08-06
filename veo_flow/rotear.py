# -*- coding: utf-8 -*-
"""ROTEAR — dado um JOB, qual perfil do Flow usar. A cadeia inteira, num lugar só.

Resposta à pergunta do Piter (02/08): "como a automação vai reconhecer qual perfil
usar na hora de editar o canal?"

    job/style_card.json  ──canal──>  frota.json  ──perfil──>  chrome_profile_X
         (sigla EN2)                  (EN2 -> conta2)          (conta verificada)

Três elos, e cada um falha de um jeito diferente — por isso a checagem devolve o
MOTIVO, não só None:

  1. o job não declara `canal`      -> não há o que rotear (era o caso de todos os
                                       jobs em 02/08: style_card sem sigla)
  2. o canal não está na frota      -> falta atribuir perfil ao canal
  3. o perfil não tem sessão/ocupado -> existe rota, mas não dá pra usar agora

IDENTIDADE do perfil: não é o nome da pasta (convenção, mente se alguém renomeia) —
é a CONTA Google lida do próprio perfil (`account_info.gaia`, ID único). A frota
guarda a conta esperada; se o perfil logar noutra conta, isso APARECE em vez de
gerar no lugar errado em silêncio.

Uso:
  python rotear.py --job <dir>          # qual perfil roda este job
  python rotear.py --canal EN2          # qual perfil roda este canal
"""
import argparse
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))


def canal_do_job(job):
    """A sigla do canal declarada no job. `canal` é o campo canônico; aceita
    `sigla`/`alias` porque o cadastro do Painel usa esses nomes."""
    sc = Path(job) / "style_card.json"
    if not sc.exists():
        return None, f"job sem style_card.json: {job}"
    try:
        d = json.loads(sc.read_text(encoding="utf-8"))
    except Exception as e:
        return None, f"style_card ilegível: {type(e).__name__}"
    for k in ("canal", "sigla", "alias"):
        if d.get(k):
            return str(d[k]).strip().upper(), ""
    return None, ("style_card não declara `canal` — sem isso não há rota. "
                  "Acrescente \"canal\": \"EN2\" ao style_card.json do job")


def rotear(canal=None, job=None):
    """{perfil, caminho, conta, pronto, motivo} — pronto=False vem com o motivo."""
    from frota import rota
    from perfis import status as st_perfis

    if not canal:
        canal, err = canal_do_job(job)
        if not canal:
            return {"pronto": False, "motivo": err}
    r = rota(canal)
    if not r:
        return {"pronto": False, "canal": canal,
                "motivo": f"canal {canal} não tem perfil atribuído — "
                          f"`frota.py --canal {canal} --perfil <nome>`"}
    st = next((s for s in st_perfis() if s["perfil"] == r["perfil"]), None)
    if not st:
        return {"pronto": False, "canal": canal, **r,
                "motivo": f"perfil {r['perfil']} registrado na frota mas não existe em disco"}
    # a conta ESPERADA (frota) contra a conta REAL (perfil) — divergência aqui
    # significa gerar na conta errada, onde o projeto/personagem do canal não existe
    esperada = (r.get("conta") or "").strip().lower()
    real = (st.get("conta") or "").strip().lower()
    if esperada and real and esperada != real:
        return {"pronto": False, "canal": canal, **r, "conta_real": real,
                "motivo": f"perfil logado em {real}, mas a frota espera {esperada}"}
    if not st["logado"]:
        return {"pronto": False, "canal": canal, **r, "conta_real": real,
                "motivo": f"perfil {r['perfil']} sem sessão — faça login uma vez"}
    if st["ocupado"]:
        return {"pronto": False, "canal": canal, **r, "conta_real": real,
                "motivo": f"perfil {r['perfil']} OCUPADO agora (outro driver ou janela aberta)"}
    return {"pronto": True, "canal": canal, **r, "conta_real": real, "motivo": ""}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--job", default="")
    ap.add_argument("--canal", default="")
    a = ap.parse_args()
    if not (a.job or a.canal):
        ap.error("informe --job ou --canal")
    r = rotear(canal=a.canal or None, job=a.job or None)
    print(json.dumps(r, ensure_ascii=False, indent=1))
    sys.exit(0 if r.get("pronto") else 1)


if __name__ == "__main__":
    main()
