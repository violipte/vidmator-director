# -*- coding: utf-8 -*-
"""SMOKE TEST da frota — cada perfil abre o Flow e diz se está LOGADO.

Antes de disparar geração em N perfis, vale saber quais realmente entram. Abrir o
Flow e ler a página é o ÚNICO teste honesto: o `Preferences` mente em perfil
multi-conta (Profile 6 tinha 3 contas), e o tamanho do cookie store só diz que
existe cookie, não que a sessão vale.

Sinais lidos da página real:
  - "Novo projeto" / grade de projetos  -> LOGADO
  - "Fazer login" / accounts.google.com -> SEM SESSÃO
  - "Create with Google Flow"           -> sessão expirada (o driver já trata assim)

Uso:
  python smoke_perfis.py                  # todos os perfis do meu dono
  python smoke_perfis.py --perfil X       # um só
  python smoke_perfis.py --todos          # inclusive de outros donos (cuidado)
"""
import argparse
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
BASE = "https://labs.google/fx/pt/tools/flow"


def testar(caminho, timeout_s=45):
    """(estado, detalhe) — abre, lê, fecha. Não gera nada."""
    from playwright.sync_api import sync_playwright
    pw = ctx = None
    try:
        pw = sync_playwright().start()
        ctx = pw.chromium.launch_persistent_context(
            user_data_dir=str(caminho), channel="chrome", headless=False,
            viewport={"width": 1280, "height": 860},
            args=["--disable-blink-features=AutomationControlled",
                  "--hide-crash-restore-bubble", "--no-first-run",
                  "--no-default-browser-check"])
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.goto(BASE, timeout=timeout_s * 1000, wait_until="domcontentloaded")
        page.wait_for_timeout(4000)
        url = page.url
        txt = (page.inner_text("body")[:3000] if page.locator("body").count() else "")
        if "accounts.google.com" in url or "Fazer login" in txt or "Sign in" in txt:
            return "SEM SESSÃO", "caiu na tela de login"
        if "Create with Google Flow" in txt:
            # 02/08: eu chamava isto de "expirado" — é a LANDING PÚBLICA do Flow
            # (Pricing/Plans, zero avatar). Cookie copiado não autentica: o Chrome
            # 127+ usa App-Bound Encryption, a chave é atrelada ao binário/perfil
            # de origem. Só login manual resolve.
            tem_conta = page.locator('img[alt*="@"], [aria-label*="Conta"], '
                                     '[aria-label*="Account"]').count()
            return ("EXPIRADO" if tem_conta else "DESLOGADO"), (
                "sessão existe mas o Flow pede re-login" if tem_conta
                else "landing pública — nunca logou neste perfil")
        if "Novo projeto" in txt or "New project" in txt or "/project/" in url:
            return "LOGADO", "grade de projetos visível"
        return "INDEFINIDO", (txt[:70].replace("\n", " ") or url)[:70]
    except Exception as e:
        return "ERRO", f"{type(e).__name__}: {str(e)[:60]}"
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
    ap.add_argument("--perfil", default="")
    ap.add_argument("--todos", action="store_true")
    a = ap.parse_args()
    from perfis import status, EU

    alvos = [s for s in status()
             if (a.perfil and s["perfil"] == a.perfil)
             or (not a.perfil and (a.todos or s["dono"] == EU))]
    if not alvos:
        print("nenhum perfil alvo")
        return
    print(f"{'PERFIL':<26} {'CONTA':<38} RESULTADO")
    for s in alvos:
        if s["ocupado"]:
            print(f"  {s['perfil']:<24} {(s['conta'] or '—'):<38} PULADO (ocupado)")
            continue
        est, det = testar(s["caminho"])
        print(f"  {s['perfil']:<24} {(s['conta'] or '—'):<38} {est} — {det}")


if __name__ == "__main__":
    main()
