"""Sobe 15 MP4s + 1 HTML catalogo pro holywhispersportal.site.

Stack: Supabase Storage (CDN MP4) + FlowLink Pages API (HTML).
Idempotente: re-rodar sobrescreve.

URL final: https://video-overlays.holywhispersportal.site/
"""
import json
import sys
import urllib.request
import urllib.error
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

# === Credenciais (do CLAUDE HWP handoff) ===
SUPA = "https://ctmhpvuixgmuomdcvccq.supabase.co"
SUPA_KEY = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
    "eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImN0bWhwdnVpeGdtdW9tZGN2Y2NxIiwicm9sZSI6"
    "InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MjkxMzA2MCwiZXhwIjoyMDg4NDg5MDYwfQ."
    "VXXedPHDNytQiY9q5a54aQQPugEmZIteIwRF6IyRRqc"
)
FLOWLINK_KEY = "oRFWD2CueoiXj5B7z86JsWT1YAMWo6siVngyjyocNdYGlLLwssiMPyna6_6R9Yxm"

# === Config ===
SUBDOMAIN = "video-overlays"
PATH = "/"
TITLE = "Video Overlays · Remotion Catalog"
LOCAL_MP4_DIR = Path(r"F:/Canal Dark/Aplicativo de Edição/remotion/out")

# === Categorização (label visivel + clip nome) ===
CATEGORIES = [
    ("Transições", [
        ("01-CrossfadeTransition", "Crossfade clássico"),
        ("02-SlideHorizontalTransition", "Slide horizontal"),
        ("03-WhipPanTransition", "Whip pan (motion blur)"),
        ("04-SmoothZoomTransition", "Smooth zoom (Hitchcock)"),
    ]),
    ("Efeitos do nicho cosmic", [
        ("05-LightRays", "God rays / raios de luz"),
        ("06-ParticlesDrift", "Particles drift (cosmic dust)"),
        ("07-StarsDrifting", "Stars drifting (constelações)"),
        ("08-AuroraGlow", "Aurora glow background"),
        ("09-LightLeak", "Light leak (cinema)"),
    ]),
    ("CTAs (3 variações)", [
        ("10-CtaCardSide", "Card lateral com mockup ebook"),
        ("11-CtaBannerSlim", "Banner faixa horizontal slim"),
        ("12-CtaPopupCenter", "Pop-up centralizado com backdrop"),
    ]),
    ("Texto animado", [
        ("13-WordByWordReveal", "Word-by-word reveal"),
    ]),
    ("Inscreva-se", [
        ("14-SubscribeBellPulse", "Botão + bell ring + thumb pulse"),
        ("15-SubscribeMinimal", "Minimalista (só botão pulsando)"),
    ]),
]


def supa_upload(remote_path: str, data: bytes, content_type: str) -> str:
    """Upload idempotente: DELETE (best-effort) + POST com x-upsert."""
    url = f"{SUPA}/storage/v1/object/images/{remote_path}"
    # 1. DELETE best-effort (404 OK)
    try:
        del_req = urllib.request.Request(url, method="DELETE", headers={
            "Authorization": f"Bearer {SUPA_KEY}",
        })
        urllib.request.urlopen(del_req, timeout=60)
    except urllib.error.HTTPError as e:
        if e.code not in (404, 400):
            pass  # tolerante — segue pra POST
    # 2. POST fresh
    req = urllib.request.Request(url, data=data, method="POST", headers={
        "Authorization": f"Bearer {SUPA_KEY}",
        "Content-Type": content_type,
        "x-upsert": "true",
    })
    urllib.request.urlopen(req, timeout=300)
    return f"{SUPA}/storage/v1/object/public/images/{remote_path}"


def main():
    # Step 1: upload MP4s
    print("=== Step 1: upload MP4s ===")
    url_map = {}
    for cat_label, items in CATEGORIES:
        for clip_id, _label in items:
            local = LOCAL_MP4_DIR / f"{clip_id}.mp4"
            if not local.exists():
                print(f"  MISSING {local.name}, abortando")
                sys.exit(1)
            size_kb = local.stat().st_size // 1024
            print(f"  uploading {clip_id} ({size_kb} KB)...", end="", flush=True)
            remote = f"playground/overlays/{clip_id}.mp4"
            url = supa_upload(remote, local.read_bytes(), "video/mp4")
            print(" OK")
            url_map[clip_id] = url
    print(f"\nTotal: {len(url_map)} MP4s uploaded\n")

    # Step 2: build HTML
    print("=== Step 2: build catalog HTML ===")
    sections_html = ""
    for cat_label, items in CATEGORIES:
        cards_html = ""
        for clip_id, label in items:
            url = url_map[clip_id]
            cards_html += f"""
        <article class="card">
          <video autoplay muted loop playsinline preload="metadata">
            <source src="{url}" type="video/mp4">
          </video>
          <div class="card-body">
            <div class="card-id">{clip_id}</div>
            <h3>{label}</h3>
          </div>
        </article>"""
        sections_html += f"""
    <section>
      <h2 class="cat-heading">{cat_label} <span class="cat-count">{len(items)}</span></h2>
      <div class="grid">{cards_html}
      </div>
    </section>"""

    from datetime import datetime
    total = sum(len(items) for _, items in CATEGORIES)
    gerado = datetime.now().strftime("%d/%m/%Y %H:%M")

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<meta name="robots" content="noindex, nofollow">
<title>{TITLE}</title>
<style>
  :root {{
    --bg: #07060d;
    --bg-card: #14131e;
    --border: #25243a;
    --text: #f0eaff;
    --text-dim: #8a8a9c;
    --accent: #facc15;
  }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    background: radial-gradient(ellipse at top, #1a0e2e 0%, var(--bg) 60%);
    color: var(--text);
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    padding: 48px 24px;
    min-height: 100vh;
  }}
  .header {{ max-width: 1280px; margin: 0 auto 40px; }}
  .header h1 {{
    font-family: Georgia, serif; font-size: 2.4rem; font-weight: 600;
    margin-bottom: 10px; letter-spacing: 0.5px;
  }}
  .header p {{ color: var(--text-dim); font-size: 0.95rem; line-height: 1.5; max-width: 700px; }}
  .meta {{ color: var(--text-dim); font-size: 0.8rem; margin-top: 14px;
    font-family: 'JetBrains Mono', monospace; }}
  section {{ max-width: 1280px; margin: 0 auto 56px; }}
  .cat-heading {{
    font-size: 1.3rem; font-weight: 600; margin-bottom: 18px; color: var(--accent);
    display: flex; align-items: center; gap: 10px; letter-spacing: 0.3px;
  }}
  .cat-count {{
    background: var(--bg-card); color: var(--text-dim); padding: 2px 10px;
    border-radius: 999px; font-size: 0.75rem; font-weight: 600;
    border: 1px solid var(--border);
  }}
  .grid {{
    display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 18px;
  }}
  .card {{
    background: var(--bg-card); border: 1px solid var(--border); border-radius: 12px;
    overflow: hidden; transition: transform 0.15s, border-color 0.15s;
  }}
  .card:hover {{ transform: translateY(-2px); border-color: var(--accent); }}
  .card video {{
    width: 100%; aspect-ratio: 16 / 9; object-fit: cover;
    background: #000; display: block; border-bottom: 1px solid var(--border);
  }}
  .card-body {{ padding: 12px 16px 14px; }}
  .card-id {{ color: var(--text-dim); font-size: 0.7rem;
    font-family: 'JetBrains Mono', monospace; letter-spacing: 0.5px; margin-bottom: 2px; }}
  .card h3 {{ font-size: 0.95rem; font-weight: 500; line-height: 1.3; }}
  footer {{
    max-width: 1280px; margin: 60px auto 0; padding-top: 30px;
    border-top: 1px solid var(--border); color: var(--text-dim);
    font-size: 0.85rem; text-align: center;
  }}
</style>
</head>
<body>
<div class="header">
  <h1>Video Overlays — Remotion Catalog</h1>
  <p>Catálogo de overlays e transições renderizados em Remotion. Cada clip é um loop de ~3s autoplay. Os arquivos finais entram no pipeline FFmpeg do <code>engine.py</code> via composição (overlay/concat) sem afetar o render NVENC principal.</p>
  <div class="meta">{total} clips · gerado em {gerado} · sample · loop autoplay</div>
</div>
{sections_html}
<footer>
  Render: Remotion 4.0 · 1280×720 @ 30fps · H.264 / yuv420p · CRF 23 · hosted Supabase Storage
</footer>
</body>
</html>"""
    print(f"  HTML size: {len(html) // 1024} KB ({total} cards)\n")

    # Step 3: POST FlowLink Pages
    print("=== Step 3: POST FlowLink Pages ===")
    payload = {
        "tipo": "outro",
        "subdomain": SUBDOMAIN,
        "path": PATH,
        "titulo": TITLE,
        "html_content": html,
        "meta_description": "Internal catalog of Remotion-rendered overlays and transitions.",
        "publish": True,
    }
    page_id = None
    try:
        req = urllib.request.Request(
            "https://admin.flowlink.site/api/admin/pages/generate",
            data=json.dumps(payload).encode("utf-8"),
            method="POST",
            headers={
                "Authorization": f"Bearer {FLOWLINK_KEY}",
                "Content-Type": "application/json",
            },
        )
        resp = json.loads(urllib.request.urlopen(req, timeout=60).read().decode("utf-8"))
        print(f"  POST OK: {json.dumps(resp, indent=2)[:200]}")
        page_id = resp.get("page_id") or resp.get("id")
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        if e.code == 409:
            print(f"  409: page existe. PATCHing html_content via Supabase REST...")
            search_path = PATH.replace("/", "%2F")
            r = urllib.request.urlopen(urllib.request.Request(
                f"{SUPA}/rest/v1/landing_pages?subdomain=eq.{SUBDOMAIN}&path=eq.{search_path}&select=id",
                headers={"apikey": SUPA_KEY, "Authorization": f"Bearer {SUPA_KEY}"},
            ), timeout=30)
            existing = json.loads(r.read().decode("utf-8"))
            if existing:
                page_id = existing[0]["id"]
                req2 = urllib.request.Request(
                    f"{SUPA}/rest/v1/landing_pages?id=eq.{page_id}",
                    data=json.dumps({"html_content": html}).encode("utf-8"),
                    method="PATCH",
                    headers={
                        "apikey": SUPA_KEY,
                        "Authorization": f"Bearer {SUPA_KEY}",
                        "Content-Type": "application/json",
                        "Prefer": "return=minimal",
                    },
                )
                urllib.request.urlopen(req2, timeout=60)
                print(f"  html_content PATCHed (page_id={page_id})")
        else:
            raise RuntimeError(f"FlowLink HTTP {e.code}: {body[:500]}")

    if not page_id:
        print("  AVISO: page_id não obtido, pulando step 4")
        sys.exit(2)

    # Step 4: PATCH domain
    print("\n=== Step 4: PATCH domain → holywhispersportal.site ===")
    req3 = urllib.request.Request(
        f"{SUPA}/rest/v1/landing_pages?id=eq.{page_id}",
        data=json.dumps({"domain": "holywhispersportal.site"}).encode("utf-8"),
        method="PATCH",
        headers={
            "apikey": SUPA_KEY,
            "Authorization": f"Bearer {SUPA_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal",
        },
    )
    urllib.request.urlopen(req3, timeout=60)
    print("  domain switched to holywhispersportal.site\n")

    print("=== DONE ===")
    print(f"  Live: https://{SUBDOMAIN}.holywhispersportal.site/")
    print(f"  page_id: {page_id}")
    print(f"  Total MP4s: {len(url_map)}\n")


if __name__ == "__main__":
    main()
