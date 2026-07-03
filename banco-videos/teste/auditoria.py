"""Painel de AUDITORIA do resolver: por cena, mostra o thumbnail do clipe escolhido
+ a fala + a query + o NÍVEL da cascata (L1-archive/L2-commons/L3-video/L4-foto/L5).
Gera _auditoria.html (abrir no navegador) pra calibrar o 'gosto' do Vision.
"""
import base64
import json
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
TESTE = Path(r"F:/Canal Dark/Aplicativo de Edição/banco-videos/teste")
TIMELINE = TESTE / "timeline.json"
OUT = TESTE / "_auditoria.html"
TMP = TESTE / "_audit_thumbs"

COR = {"L1-archive": "#22c55e", "L2-commons": "#38bdf8", "L3-video": "#a3a3a3",
       "L4-foto": "#fbbf24", "L5-fallback": "#f97316", "L5-amplo": "#f97316", "none": "#ef4444"}


def thumb_b64(clip_path):
    TMP.mkdir(exist_ok=True)
    out = TMP / "t.jpg"
    src = Path(clip_path)
    if src.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp"):
        subprocess.run(["ffmpeg", "-y", "-i", str(src), "-vf", "scale=320:-1", str(out)], capture_output=True)
    else:
        subprocess.run(["ffmpeg", "-y", "-ss", "1", "-i", str(src), "-frames:v", "1", "-vf", "scale=320:-1", str(out)], capture_output=True)
    if out.exists():
        return base64.b64encode(out.read_bytes()).decode()
    return ""


def main():
    tl = json.load(open(TIMELINE, encoding="utf-8"))
    cards = []
    for c in tl["cenas"]:
        if not c.get("clip_path"):
            continue
        b64 = thumb_b64(c["clip_path"])
        nivel = c.get("nivel", "?")
        cor = COR.get(nivel, "#888")
        rq = c.get("real_query") or ""
        cards.append(f'''<div class="card">
  <img src="data:image/jpeg;base64,{b64}"/>
  <div class="tag" style="background:{cor}">{nivel} · {c.get("media_tipo","?")}</div>
  <div class="q">{c.get("stock_query","")}</div>
  <div class="t">{c["texto"][:90]}</div>
  {f'<div class="rq">assunto: {rq}</div>' if rq else ''}
</div>''')
    from collections import Counter
    dist = Counter(c.get("nivel") for c in tl["cenas"] if c.get("clip_path"))
    legenda = " · ".join(f"<b style='color:{COR.get(k,'#888')}'>{k}</b>: {v}" for k, v in dist.items())
    html = f'''<!doctype html><meta charset="utf-8"><title>Auditoria do resolver</title>
<style>body{{background:#0c0f16;color:#e7edf5;font-family:Segoe UI,system-ui,sans-serif;margin:24px}}
h1{{font-size:20px}} .leg{{margin:8px 0 20px;font-size:14px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(330px,1fr));gap:14px}}
.card{{background:#151a24;border:1px solid #232a37;border-radius:10px;overflow:hidden}}
.card img{{width:100%;display:block}} .tag{{display:inline-block;margin:8px;padding:3px 9px;border-radius:5px;color:#06101a;font-weight:700;font-size:12px}}
.q{{padding:0 10px;font-weight:600;font-size:14px}} .t{{padding:4px 10px 10px;color:#9aa7b8;font-size:13px}}
.rq{{padding:0 10px 10px;color:#38bdf8;font-size:12px}}</style>
<h1>Auditoria do resolver — {len(cards)} cenas</h1>
<div class="leg">Níveis: {legenda}</div>
<div class="grid">{''.join(cards)}</div>'''
    OUT.write_text(html, encoding="utf-8")
    print(f"OK -> {OUT}")
    print("  distribuição:", dict(dist))


if __name__ == "__main__":
    main()
