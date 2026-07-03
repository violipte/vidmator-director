"""Equilibra o TEXTO do intro: de 14/14 (caption) para ~1 a cada 2 cenas,
mantendo só as frases de IMPACTO mais fortes e espaçadas. Não mexe no resto.
Também valida o highlight (palavra_chave deve existir no texto exibido).
"""
import json
import re
import subprocess
from pathlib import Path

TESTE = Path(r"F:/Canal Dark/Aplicativo de Edição/banco-videos/teste")
TIMELINE = TESTE / "timeline.json"
INTRO = 40.0


def norm(s):
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def _parse_arr(txt):
    a, b = txt.find("["), txt.rfind("]")
    if a >= 0 and b > a:
        try:
            return json.loads(txt[a:b + 1])
        except Exception:
            return None
    return None


def escolher_fortes(intro_txt):
    """CLI escolhe os ~7 hooks mais fortes, espaçados (sem adjacentes)."""
    linhas = "  ".join(f"[{c['idx']}] {c['texto_impacto'].replace(chr(34), '')}" for c in intro_txt)
    prompt = (
        "These are on-screen text phrases for a video intro, one per scene. Select ONLY the 6 to 8 "
        "STRONGEST as genuine impact hooks or quotes, and SPACE THEM OUT (avoid picking two consecutive "
        "idx). The rest will be removed to keep the intro from feeling like captions. Return ONLY a JSON "
        "array of the idx numbers to KEEP. Phrases: " + linhas
    )
    try:
        p = subprocess.Popen(f'gemini -p "{prompt}"', shell=True, cwd=str(TESTE),
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                             encoding="utf-8", errors="replace")
        out, _ = p.communicate(timeout=120)
        arr = _parse_arr(out or "")
        if arr:
            return set(int(x) for x in arr)
    except subprocess.TimeoutExpired:
        subprocess.run(f"taskkill /F /T /PID {p.pid}", shell=True, capture_output=True)
    except Exception:
        pass
    return None


def fix_keyword(c):
    """Garante que a palavra_chave exista no texto exibido (senão = palavra mais longa)."""
    if not c.get("texto_impacto"):
        return
    words = c["texto_impacto"].split()
    kw = norm(c.get("palavra_chave"))
    ok = kw and any(norm(w) == kw or (len(norm(w)) >= 4 and len(kw) >= 4 and kw in norm(w)) for w in words)
    if not ok:
        cand = [w for w in words if len(norm(w)) >= 4]
        c["palavra_chave"] = max(cand or words, key=lambda w: len(w))


tl = json.load(open(TIMELINE, encoding="utf-8"))
intro_txt = [c for c in tl["cenas"] if c["inicio"] < INTRO and c.get("texto_impacto")]
intro_txt.sort(key=lambda c: c["idx"])
print(f"intro: {len(intro_txt)} cenas com texto -> equilibrando p/ ~7 espaçados")

keep = escolher_fortes(intro_txt)
if keep:
    print(f"  CLI escolheu: {sorted(keep)}")
else:
    # fallback determinístico: alternado (1 a cada 2), sem adjacentes
    keep = {c["idx"] for n, c in enumerate(intro_txt) if n % 2 == 0}
    print(f"  fallback alternado: {sorted(keep)}")

# enforce: sem dois adjacentes (idx consecutivos) — dropa o segundo
kept_sorted = sorted(keep)
final = []
for idx in kept_sorted:
    if final and idx - final[-1] == 1:
        continue
    final.append(idx)
keep = set(final)
print(f"  mantidos (sem adjacentes): {sorted(keep)} ({len(keep)})")

# remove texto das cenas do intro NÃO escolhidas
removidos = 0
for c in intro_txt:
    if c["idx"] not in keep:
        c["texto_impacto"] = None
        c["palavra_chave"] = None
        c["texto_pos"] = None
        c["entrada_texto"] = None
        removidos += 1

# valida keyword/highlight em TODAS as cenas com texto (intro + resto)
for c in tl["cenas"]:
    if c.get("texto_impacto"):
        fix_keyword(c)

json.dump(tl, open(TIMELINE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
intro_final = sum(1 for c in tl["cenas"] if c["inicio"] < INTRO and c.get("texto_impacto"))
n_intro_cenas = sum(1 for c in tl["cenas"] if c["inicio"] < INTRO)
print(f"OK: intro com texto {intro_final}/{n_intro_cenas} cenas (removidos {removidos})")
for c in tl["cenas"]:
    if c["inicio"] < INTRO and c.get("texto_impacto"):
        print(f"  {c['inicio']:>4.1f}s [{c.get('entrada_texto'):<7}] \"{c['texto_impacto']}\" (kw: {c.get('palavra_chave')})")
