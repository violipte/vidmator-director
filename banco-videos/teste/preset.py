"""Preset de ESTILO por NICHO. Cada vídeo tem um `nicho` -> calibra todos os passes
(footage, vintage, efeitos, apresentações, fontes, ritmo). Receitas em presets.json.

Seleção do nicho (nesta ordem): env NICHO > timeline.json["nicho"] > "default".
Cada pass faz: `from preset import carregar; P = carregar(tl)`.
"""
import json
import os
from pathlib import Path

_PRESETS = Path(__file__).parent / "presets.json"


def nicho_ativo(tl=None):
    n = os.environ.get("NICHO") or (tl or {}).get("nicho") or "default"
    return str(n).strip().lower()


def carregar(tl=None):
    """Retorna o dict de knobs do nicho ativo (merge sobre o default). Inclui `_nicho`."""
    try:
        data = json.load(open(_PRESETS, encoding="utf-8"))
    except Exception:
        data = {}
    n = nicho_ativo(tl)
    p = dict(data.get("default", {}))
    p.update(data.get(n, {}))
    p["_nicho"] = n if n in data else "default"
    return p
