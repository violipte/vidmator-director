# -*- coding: utf-8 -*-
"""LOGIN assistido de um perfil — abre a janela e DETECTA sozinho quando entrou.

O `flow_driver.cmd_login()` espera um ENTER no terminal, o que não funciona quando
quem abre a janela é a automação rodando em background. Aqui a janela abre, o
humano loga, e o script faz polling da própria página até ver a grade de projetos —
então salva e fecha. Ninguém precisa voltar ao terminal.

⚠️ Quem digita a credencial é SEMPRE a pessoa. A automação não toca em e-mail,
senha nem 2FA — só abre a porta e confirma que entrou.

Uso:
  "F:/Canal Dark/veo_venv/Scripts/python.exe" login_perfil.py conta2 [--espera 300]
"""
import argparse
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
BASE = "https://labs.google/fx/pt/tools/flow"


def logar(perfil_dir, espera_s=300, conta_esperada="", manter=False):
    from playwright.sync_api import sync_playwright
    pw = ctx = None
    try:
        pw = sync_playwright().start()
        ctx = pw.chromium.launch_persistent_context(
            user_data_dir=str(perfil_dir), channel="chrome", headless=False,
            viewport={"width": 1280, "height": 900},
            args=["--disable-blink-features=AutomationControlled",
                  "--hide-crash-restore-bubble",
                  # ver flow_driver.abrir(): infobar do --no-sandbox (que vem do
                  # Playwright) desloca ~40px e quebra clique por coordenada
                  "--test-type", "--no-first-run",
                  "--no-default-browser-check"])
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.goto(BASE, wait_until="domcontentloaded", timeout=60000)
        print(f"JANELA ABERTA em {Path(perfil_dir).name}")
        if conta_esperada:
            print(f"  entre com: {conta_esperada}")
        print(f"  faça o login nesta janela — detecto sozinho (até {espera_s}s)")
        t0 = time.time()
        while time.time() - t0 < espera_s:
            try:
                txt = page.inner_text("body")[:2500]
                if "Novo projeto" in txt or "New project" in txt or "/project/" in page.url:
                    # deixa o Chrome gravar cookies/estado antes de fechar
                    page.wait_for_timeout(3500)
                    print(f"LOGADO ({int(time.time() - t0)}s) — sessão salva")
                    if manter:
                        # janela fica de pé: o Chrome só grava cookies no disco ao
                        # FECHAR de forma limpa, então quem fecha é o próprio Piter
                        print("  janela MANTIDA aberta — feche-a quando quiser")
                        ctx.wait_for_event("close", timeout=0)
                    return True
            except Exception:
                pass
            page.wait_for_timeout(3000)
        print(f"TIMEOUT após {espera_s}s — sem login detectado")
        return False
    except Exception as e:
        print(f"ERRO: {type(e).__name__}: {str(e)[:80]}")
        return False
    finally:
        try:
            if ctx:
                ctx.close()
            if pw:
                pw.stop()
        except Exception:
            pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("perfil", help="nome curto (conta2) ou caminho completo")
    ap.add_argument("--espera", type=int, default=300)
    ap.add_argument("--manter", action="store_true",
                    help="deixa a janela ABERTA depois de logar (o Piter segue usando)")
    a = ap.parse_args()
    p = Path(a.perfil)
    if not p.is_absolute():
        p = AQUI / (a.perfil if a.perfil.startswith("chrome_profile")
                    else f"chrome_profile_{a.perfil}")
    if not p.exists():
        print(f"perfil não existe: {p}")
        sys.exit(2)
    conta = ""
    try:
        from perfis import status
        conta = next((s["conta"] for s in status() if s["caminho"] == str(p)), "")
    except Exception:
        pass
    sys.exit(0 if logar(p, a.espera, conta, a.manter) else 1)


if __name__ == "__main__":
    main()
