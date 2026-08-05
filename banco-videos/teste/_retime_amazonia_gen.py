# -*- coding: utf-8 -*-
"""Re-temporiza o plano da Amazônia pra narração NOVA (voz do Russel).

O plano foi cronometrado na narração antiga (592s, voz Bill); a nova tem ~509s.
As DUAS leram o MESMO roteiro → as 1554 palavras alinhadas são âncoras 1:1.
Interpolação linear por palavra: t_novo = interp(t_velho, t_palavras_velho,
t_palavras_novo). Beat a beat, sem chute de fator global (o ritmo varia por trecho).
"""
import bisect
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
TESTE = Path(__file__).parent
JOB = Path(r"F:/Canal Dark/Aplicativo de Edição/banco-videos/_job_amazonia_gen")

velho = json.loads((TESTE / "palavras_amazonia.json").read_text(encoding="utf-8"))
novo = json.loads((JOB / "palavras_gen.json").read_text(encoding="utf-8"))
assert abs(len(velho) - len(novo)) <= 2, f"contagem difere: {len(velho)} x {len(novo)}"
n = min(len(velho), len(novo))
ot = [w["t_ini"] for w in velho[:n]]
nt = [w["t_ini"] for w in novo[:n]]
fim_o, fim_n = velho[n - 1]["t_fim"], novo[n - 1]["t_fim"]


def remap(t):
    t = float(t)
    if t <= ot[0]:
        return round(nt[0] + (t - ot[0]), 2)
    if t >= fim_o:
        return round(fim_n + (t - fim_o), 2)
    k = bisect.bisect_right(ot, t) - 1
    o0, o1 = ot[k], ot[k + 1] if k + 1 < n else fim_o
    n0, n1 = nt[k], nt[k + 1] if k + 1 < n else fim_n
    if o1 <= o0:
        return round(n0, 2)
    return round(n0 + (t - o0) * (n1 - n0) / (o1 - o0), 2)


def retime_obj(o):
    if isinstance(o, dict):
        for k in ("t_ini", "t_fim"):
            if k in o and isinstance(o[k], (int, float)):
                o[k] = remap(o[k])
        if "dur" in o and "t_ini" in o and "t_fim" in o:
            o["dur"] = round(o["t_fim"] - o["t_ini"], 2)
        for v in o.values():
            retime_obj(v)
    elif isinstance(o, list):
        for v in o:
            retime_obj(v)


for nome_arq, dst in (("plano_amazonia.json", "plano_gen.json"),
                      ("veo_lote.json", None)):
    src = JOB / nome_arq
    d = json.loads(src.read_text(encoding="utf-8"))
    retime_obj(d)
    alvo = JOB / (dst or nome_arq)
    alvo.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{nome_arq} -> {alvo.name} (retimado)")

print(f"duração: {fim_o:.1f}s -> {fim_n:.1f}s")
