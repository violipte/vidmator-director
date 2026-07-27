# -*- coding: utf-8 -*-
"""GOLDEN TESTS das regras R-xx (R-82: toda regra nasce de um bug REAL — este arquivo
guarda o bug exato que a originou). Roda em <1s, SEM render. `python test_regras.py`.
Se qualquer um falhar, NÃO renderize: o bug do vídeo passado voltou.
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).parent))
import acervo_registry as ar  # noqa

FALHAS = []


def caso(nome, cond, detalhe=""):
    if cond:
        print(f"  ok  {nome}")
    else:
        print(f"  FALHOU {nome} {detalhe}")
        FALHAS.append(nome)


print("== R-26: o caso 15% vs 34% (seniors — dado de ouro virou rodapé) ==")
caso("_fnum('15%') = 15.0", ar._fnum("15%") == 15.0)
caso("_fnum('$80,000') = 80000", ar._fnum("$80,000") == 80000.0)
d_ouro = {"labels": ["Runners Died", "Non-Runners Died"], "values": ["15%", "34%"],
          "title": "Mortality Rate Comparison"}
t_ouro = "By the end of the study, only fifteen percent of the runners had died compared to thirty four percent"
p = ar._graf_cmp(d_ouro, t_ouro, [])
caso("VersusBars monta com values '15%'/'34%' + texto POR EXTENSO",
     bool(p) and p["values"] == [15.0, 34.0] and p["suffix"] == "%", str(p))
r = ar.escolher("chart", d_ouro, t_ouro, 7, {}, dur=7.0)
caso("escolher('chart') acha comparativo pro dado de ouro", bool(r) and r[0].startswith("Graf"), str(r and r[0]))

print("== R-35/36/38: números por extenso e pontuação ==")
caso("'nineteen twenty, seventeen' = 1920 e 17, NUNCA 1937",
     "1920" in ar._nums_do_texto("By nineteen twenty, seventeen years later")
     and "1937" not in ar._nums_do_texto("By nineteen twenty, seventeen years later"))
caso("'forty-five percent' ancora 45", ar._anc([45], "a tariff of forty-five percent"))
caso("'ninety thousand' ancora 90000", ar._anc([90000], "around ninety thousand units"))
caso("ano 'two thousand three' sem vírgula", "2003" in ar.humanizar("by two thousand three the company"))
caso("ano por extenso detectado p/ R-27", "1984" in ar._nums_do_texto("In nineteen eighty four, researchers"))

print("== R-39: texto de tela nunca é transcrição cortada ==")
caso("'w l a' vira WLA", "WLA" in ar.humanizar("the w l a, a rugged workhorse"))
caso("frase >12 palavras sem cláusula = RECUSA",
     ar.frase_de_tela("stopped building heavy motorcycles for civilians and started building them for young soldiers overseas") is None)
caso("frase_forcada não termina em stopword",
     not (ar.frase_forcada("sales curved upward through the late eighties and nineties") or "x").rstrip(".").split()[-1].lower() in ("and", "the", "of"))

print("== R-30/32: defaults NUNCA ==")
caso("MapRoute sem coords = None", ar.rebuild("MapRoute", {"start_location": {"name": "Tehran"}}, "", []) is None)
caso("continente rejeitado", ar._paises_de({"countries": ["North America"]}) == [])
caso("Img14 sem título = None", ar.rebuild("Img14_TitleCutout", {}, "some text", ["foto.jpg"]) is None)
caso("builder texto sem matéria = None", ar._texto_build({}, "", []) is None)

print("== R-21: duração é elegibilidade ==")
caso("chart pesado NÃO entra em beat de 1.5s",
     ar.escolher("chart", d_ouro, t_ouro, 7, {}, dur=1.5) is None or not ar.escolher("chart", d_ouro, t_ouro, 7, {}, dur=1.5))
caso("overlay leve não fica 9s parado (max_dur)",
     (lambda r2: r2 is None or not r2[0].startswith("Ovl"))(ar.escolher("texto_overlay", {}, "The eagle soars alone", 7, {}, dur=9.0)))

print("== R-25: pessoa nomeada ==")
caso("CharacterCard sem foto = None", ar.rebuild("CharacterCard", {"name": "Jeff Galloway"}, "", []) is None)

print("== R-37: número inventado pelo LLM não ancora ==")
caso("values [50,70,90] sem número no áudio = recusa",
     ar._graf_serie({"labels": ["a", "b", "c"], "values": [50, 70, 90]}, "sales curved upward", []) is None)

print("== R-92/R-109/R-32: os prints do Piter no tenis (23/07) ==")
caso("'number one enemy' NUNCA vira Donut 1%",
     ar._graf_pct({"percentage": 1}, "the number one enemy is not slowness, it is falling", []) is None)
caso("% exige 'percent' FALADO",
     ar._graf_pct({"percentage": 50}, "half of the runners kept going", []) is None)
caso("unidade longa nao vira suffix truncado ('genera')",
     (lambda p: bool(p) and p["suffix"] == "" and "generation" in p["title"].lower())(
         ar._graf_uni({"number": 25, "unit": "generations"}, "for over twenty five generations", [])))
caso("jornal recusa corpo sem sentença fechada",
     ar._soc_news({"title": "Width Options"}, "which for older feet isn", ["img.jpg"]) is None)
ar.set_style({"jornal_ficticio": "The Runner Tribune"})
p_soc = ar._soc_news({"title": "Width Options"}, "It comes in narrow, standard, wide and extra wide sizes.", ["img.jpg"])
caso("kicker do jornal vem do style_card (nunca Motor Chronicle)",
     bool(p_soc) and p_soc["kicker"] == "The Runner Tribune", str(p_soc and p_soc.get("kicker")))
ar.set_style({})

print("== R-32/R-39/R-111: os prints do Piter no tenis v2 (23/07 tarde) ==")
_T44 = "Generations — ASICS Gel-Nimbus: Flagship Comfort Shoe"
caso("corte() nunca deixa palavra pela metade ('Flagship Com')",
     ar.corte(_T44, 44).split()[-1] in _T44.split(), ar.corte(_T44, 44))
caso("corte() curto passa intacto", ar.corte("ASICS", 44) == "ASICS")
caso("frase_de_tela prefere a cláusula pós-':'",
     (ar.frase_de_tela("Three rules for choosing any shoe on this list: Rule one: cushioning.") or "").lower().startswith("rule one"))
p_uni = ar._graf_uni({"number": 25, "unit": "generations"}, "for over twenty five generations", [])
caso("Graf10 recebe SÓ o valor real (nunca herda default [..,18])",
     bool(p_uni) and p_uni.get("values", [None])[-1] == 25, str(p_uni))

print("== VidRush pack (24/07): dado anota o footage ==")
caso("Ovl11 SpecBadge monta com número + unidade-palavra",
     (lambda p: bool(p) and p["text"] == "17" and p["kicker"] == "lbs drag")(
         ar._ovl_spec({"number": 17, "unit": "lbs drag"}, "seventeen pounds of drag", [])))
caso("Ovl11 recusa número não-falado", ar._ovl_spec({"number": 17, "unit": "lbs"}, "smooth retrieve", []) is None)
caso("Ovl13 PriceTag exige preço falado",
     ar._ovl_price({"number": 450}, "well built for the trail", []) is None)
caso("Ovl13 monta com 'dollars' falado",
     (lambda p: bool(p) and p["text"] == "$450")(
         ar._ovl_price({"number": 450}, "four hundred fifty dollars gets you in", [])))
caso("Ovl12 GiantStat nunca pega ano", ar._ovl_giant({"number": 1984}, "in nineteen eighty four", []) is None)
caso("SWAP_TO_OVL cobre os 4 cards de dado único",
     set(ar.SWAP_TO_OVL) == {"Graf01_CounterGlow", "Graf02_Odometer", "Graf03_DonutPercent", "Graf10_BigStatCard"})
caso("Lst01 checklist exige 2+ itens reais",
     ar._lst_check({"title": "Why it wins", "points": ["only one"]}, "", []) is None)
caso("Img21 announce exige foto + título",
     ar._img21_build({"title": "#5 NB 880"}, "", []) is None
     and bool(ar._img21_build({"title": "#5 NB 880"}, "", ["foto.jpg"])))

print()
if FALHAS:
    print(f"{len(FALHAS)} REGRESSÃO(ÕES): {FALHAS} — NÃO RENDERIZE.")
    sys.exit(1)
print("TODAS AS REGRAS VERDES — camada de decisão íntegra.")
sys.exit(0)
