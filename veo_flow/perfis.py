# -*- coding: utf-8 -*-
"""MONITOR DE PERFIS do Flow — quais contas Google estão LIVRES pra automação.

Por que existe (pedido do Piter, 02/08): o `veo_driver` usa um perfil Chrome
dedicado (`veo_flow/chrome_profile`). Quando esse perfil já está aberto — o Piter
usando o Flow na mão, ou um driver anterior que não fechou —, o Playwright não
assume o controle e sai com "Abrindo em uma sessão de navegador existente",
gerando ZERO imagens sem erro claro. Foi o que travou a fila de 5 gaps.

Com vários perfis, a automação deixa de depender de UM: o driver pergunta qual
está livre e usa esse.

Um perfil está OCUPADO quando o `lockfile`/`SingletonLock` dele está preso por um
processo Chrome vivo. No Windows o lockfile fica retido pelo processo — se dá pra
renomear, ninguém está segurando.

Uso:
  python perfis.py                 # tabela de status
  python perfis.py --livre         # imprime só o caminho do 1º livre (pro driver)
  python perfis.py --novo <nome>   # cria um perfil novo (precisa login manual)
"""
import argparse
import json
import os
import shutil
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
AQUI = Path(__file__).resolve().parent
# `chrome_profile` é o histórico (perfil original, já logado); os novos seguem
# o padrão chrome_profile_<nome> pra listagem automática
PADRAO = "chrome_profile"


def listar():
    return sorted([p for p in AQUI.iterdir()
                   if p.is_dir() and p.name.startswith(PADRAO)],
                  key=lambda p: (p.name != PADRAO, p.name))


def _preso(perfil):
    """True se um Chrome vivo está segurando o perfil.

    Testa renomeando o lockfile: no Windows o arquivo fica retido enquanto o
    processo existe, então falha = ocupado. É o teste HONESTO — checar só se o
    arquivo existe daria falso positivo com sobra de crash anterior."""
    for nome in ("lockfile", "SingletonLock"):
        f = perfil / nome
        if not f.exists():
            continue
        tmp = perfil / (nome + ".livre_test")
        try:
            f.rename(tmp)
            tmp.rename(f)
        except OSError:
            return True
    return False


def _logado(perfil):
    """Heurística de sessão: cookie store do Default com tamanho real."""
    for c in (perfil / "Default" / "Network" / "Cookies",
              perfil / "Default" / "Cookies"):
        if c.exists() and c.stat().st_size > 20_000:
            return True
    return False


def status():
    out = []
    for p in listar():
        out.append({"perfil": p.name, "caminho": str(p),
                    "ocupado": _preso(p), "logado": _logado(p)})
    return out


def primeiro_livre():
    """Perfil LOGADO e não ocupado — o que o driver deve usar. None se não há."""
    for s in status():
        if not s["ocupado"] and s["logado"]:
            return s["caminho"]
    return None


def clonar_do_chrome(origem, nome):
    """Clona a SESSÃO de um perfil do Chrome do sistema pra um perfil dedicado.

    Por que clonar em vez de apontar direto (02/08): o Playwright abre o
    `user_data_dir` INTEIRO, e o Chrome do Piter fica com ele travado enquanto
    estiver aberto — apontar pro `User Data` real só funcionaria com o Chrome
    fechado, que é justamente o que queremos evitar.

    Copia só o que carrega SESSÃO (cookies, prefs, storage) — não o cache, que é
    pesado e inútil aqui. Os cookies do Chrome são cifrados por DPAPI atrelado ao
    USUÁRIO do Windows, não ao caminho: cópia no mesmo usuário mantém o login.
    """
    base = Path(os.environ.get("LOCALAPPDATA", "")) / "Google/Chrome/User Data"
    src = base / origem
    if not src.exists():
        return None, f"perfil de origem não existe: {src}"
    destino = AQUI / f"{PADRAO}_{nome}"
    alvo = destino / "Default"
    alvo.mkdir(parents=True, exist_ok=True)
    itens = ["Preferences", "Secure Preferences", "Login Data", "Web Data",
             "Network/Cookies", "Network/Trust Tokens", "Local Storage",
             "Session Storage", "IndexedDB"]
    copiados = []
    for it in itens:
        o = src / it
        d = alvo / it
        try:
            if o.is_dir():
                shutil.copytree(o, d, dirs_exist_ok=True)
                copiados.append(it)
            elif o.exists():
                d.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(o, d)
                copiados.append(it)
        except OSError:
            pass          # arquivo travado pelo Chrome vivo: segue com o resto
    # "Local State" fica na RAIZ do User Data e guarda a chave que decifra os
    # cookies — sem ele o perfil clonado abre deslogado
    try:
        ls = base / "Local State"
        if ls.exists():
            shutil.copy2(ls, destino / "Local State")
            copiados.append("Local State")
    except OSError:
        pass
    return destino, copiados


def criar(nome):
    """Clona a estrutura mínima. O LOGIN é manual (uma vez por conta):
    `flow_driver.py login` apontando pra este perfil."""
    novo = AQUI / f"{PADRAO}_{nome}"
    if novo.exists():
        return novo, False
    novo.mkdir(parents=True)
    return novo, True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--livre", action="store_true", help="só o caminho do 1º livre")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--novo", default="", help="cria chrome_profile_<nome>")
    ap.add_argument("--clonar", nargs=2, metavar=("ORIGEM", "NOME"),
                    help='clona sessão de um perfil do Chrome: --clonar "Profile 2" conta2')
    a = ap.parse_args()

    if a.clonar:
        d, r = clonar_do_chrome(a.clonar[0], a.clonar[1])
        if d is None:
            print(r); return
        print(f"clonado -> {d}")
        print(f"  itens: {', '.join(r) if r else 'NENHUM (Chrome travando?)'}")
        st = [x for x in status() if x["caminho"] == str(d)]
        if st:
            print(f"  login detectado: {'sim' if st[0]['logado'] else 'NÃO — faça login manual'}")
        return
    if a.novo:
        p, criado = criar(a.novo)
        print(f"{'criado' if criado else 'já existia'}: {p}")
        if criado:
            print("faça o login UMA vez nele:")
            print(f'  "F:/Canal Dark/veo_venv/Scripts/python.exe" flow_driver.py login '
                  f'--perfil "{p}"')
        return

    st = status()
    if a.livre:
        print(primeiro_livre() or "")
        return
    if a.json:
        print(json.dumps(st, ensure_ascii=False, indent=1))
        return

    print(f"{'PERFIL':<28} {'ESTADO':<12} {'LOGIN':<10}")
    for s in st:
        estado = "OCUPADO" if s["ocupado"] else "livre"
        print(f"  {s['perfil']:<26} {estado:<12} {'sim' if s['logado'] else 'NÃO'}")
    livre = primeiro_livre()
    print()
    print(f"-> disponível pro driver: {Path(livre).name if livre else 'NENHUM'}")
    if not livre:
        print("   (feche a janela do Chrome que está usando o perfil, ou crie outro:")
        print("    python perfis.py --novo conta2)")


if __name__ == "__main__":
    main()
