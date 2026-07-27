"""Pass do MASCOTE (canais com personagem): a cada 2-3 cenas, escolhe a pose/expressão do acervo
que melhor casa com o TEXTO da cena e grava em cena["mascote"]. Gated por preset.mascote.ativo.

Seleção: UMA chamada LLM por vídeo (lista de beats candidatos + catálogo de poses -> atribuição JSON).
Fallback: rotação por função (warn/explain/react). Lados alternam pra dar dinamismo.
"""
import json
import os
import random
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
TESTE = Path(r"F:/Canal Dark/Aplicativo de Edição/banco-videos/teste")
TIMELINE = TESTE / "timeline.json"
from gemini_api import gemini_text


def main():
    from preset import carregar
    tl = json.load(open(TIMELINE, encoding="utf-8"))
    cfg = (carregar(tl).get("mascote") or {})
    if not cfg.get("ativo"):
        print("mascote: nicho sem mascote -> skip")
        return
    banco = Path(cfg.get("banco") or r"F:/Canal Dark/Aplicativo de Edição/banco-videos/mascote_galo")
    idx_path = banco / "index_mascote.json"
    if not idx_path.exists():
        print(f"mascote: ERRO — banco sem índice ({idx_path})"); sys.exit(1)
    idx = json.load(open(idx_path, encoding="utf-8"))
    poses = [{"id": k, **v} for k, v in idx.get("itens", {}).items() if (banco / v["file"]).exists()]
    if not poses:
        print("mascote: ERRO — nenhuma pose utilizável"); sys.exit(1)

    cenas = sorted(tl.get("cenas", []), key=lambda c: c.get("inicio", 0))
    cada_min, cada_max = (cfg.get("cada") or [2, 3])
    # candidatos: a cada 2-3 cenas, pulando cenas que já têm elemento grande (card/mapa/pessoa/CTA)
    rng = random.Random(42)
    alvo, i = [], 0
    while i < len(cenas):
        c = cenas[i]
        ocupada = any(c.get(k) for k in ("ilustracao", "mapa", "pessoa_card", "data_stamp"))
        if not ocupada:
            alvo.append(c)
            i += rng.randint(cada_min, cada_max)
        else:
            i += 1
    if not alvo:
        print("mascote: nenhuma cena livre -> skip"); return

    # 1 chamada LLM: atribui pose por beat
    cat = "\n".join(f"- {p['id']}: funcao={p['funcao']}, emocao={p['emocao']}, pose={p['pose']} ({p['desc']})" for p in poses)
    beats = "\n".join(f"{k}. \"{c['texto'][:110]}\"" for k, c in enumerate(alvo))
    prompt = (f"A cartoon mascot narrator (veteran rooster) pops into a video on certain narration beats. "
              f"For EACH beat below, pick the pose id from the CATALOG that best matches the narrative function "
              f"of that line (warning->warn, explaining->explain/teach, reaction->react, story->story, greeting->greet). "
              f"Vary the choices; avoid repeating the same pose consecutively.\n\nCATALOG:\n{cat}\n\nBEATS:\n{beats}\n\n"
              f"Return ONLY a JSON object mapping beat number to pose id, e.g. {{\"0\": \"pose_id\"}}.")
    out = gemini_text(prompt, 90) or ""
    a, b = out.find("{"), out.rfind("}")
    escolha = {}
    try:
        escolha = {int(k): v for k, v in json.loads(out[a:b + 1]).items()}
    except Exception:
        print("  LLM falhou -> fallback rotação")
    by_id = {p["id"]: p for p in poses}

    lado = "right"
    usados = 0
    ultimo = None
    for k, c in enumerate(alvo):
        pid = escolha.get(k)
        if not pid or pid not in by_id or pid == ultimo:
            cands = [p for p in poses if p["id"] != ultimo] or poses
            pid = cands[k % len(cands)]["id"]
        p = by_id[pid]
        c["mascote"] = {"img": p["file"], "lado": lado, "pose": p["pose"], "emocao": p["emocao"]}
        lado = "left" if lado == "right" else "right"
        ultimo = pid
        usados += 1

    json.dump(tl, open(TIMELINE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"mascote: {usados} entradas em {len(cenas)} cenas | banco={banco.name} ({len(poses)} poses)")


if __name__ == "__main__":
    main()
