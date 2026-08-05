# -*- coding: utf-8 -*-
"""CICLO POR COLEÇÃO — encarregado v2 do modo generativo (05/08, desenho do Piter).

    PROJETO  = CANAL   (personagens moram nele; o @Russel só existe dentro dele)
      └─ COLEÇÃO = VÍDEO  (nome = data de publicação; tem "Baixar coleção" próprio)

Por que existe: o fluxo antigo fazia ~6 interações de UI POR CLIPE (abrir /edit/,
ler prompt, voltar, hover, ⋮, Baixar) — e era nelas que o lote de 98 morria: popup
na frente, card fora da viewport, botão fora do lugar. Nada disso é "gerar vídeo".
Aqui a UI sai do caminho crítico:

    rodada:  1. entra na coleção e SÓ ENVIA os prompts que faltam (a única coisa
                que o Flow faz bem sozinho)
             2. espera os badges de % sumirem (geração acabou)
             3. UM "Baixar coleção" -> zip -> casa por título (veo_zip) -> assets/
             4. gate local nos vídeos novos; reprovado é APAGADO e volta na próxima
    para quando: tudo tem arquivo, ou 2 rodadas seguidas sem arquivo novo.

Idempotente por construção: quem tem arquivo em assets/ nunca é re-enviado; re-rodar
é sempre seguro. Sem custo por geração (Veo Lower Priority / Nano Banana — Piter
05/08), duplicata ocasional do casamento é tempo, não dinheiro.

Uso:
  "F:/Canal Dark/veo_venv/Scripts/python.exe" -u veo_ciclo.py \
      --lote <job>/veo_lote.json --out <job>/assets --canal AMZ --colecao 05-08-26 \
      --tipo video [--fila 4] [--rodadas 6] [--espera-max 25]
"""
import argparse
import json
import re
import sys
import time
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "veo_flow"))
sys.stdout.reconfigure(encoding="utf-8")

import flow_driver as fd  # noqa
import veo_driver as vd  # noqa — _normalizar_lote, _cards_falha, _aprovado
from veo_colecao import abrir_colecao, baixar_colecao, projeto_do_canal  # noqa
from veo_zip import aplicar  # noqa
from veo_supervisor import matar_tudo  # noqa


def _log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def _n_cards(page):
    try:
        return page.locator('a[href*="/edit/"]').count()
    except Exception:
        return 0


def _n_gerando(page):
    """Badges de progresso ('4%'…'99%') = gerações em andamento."""
    try:
        return page.get_by_text(re.compile(r"^\d{1,2}\s*%$")).count()
    except Exception:
        return 0


def _prontos(out, alvos):
    return sum(1 for it in alvos if (out / it["arquivo"]).exists())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lote", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--canal", required=True)
    ap.add_argument("--colecao", required=True, help="nome da coleção = data de publicação")
    ap.add_argument("--tipo", default="video", choices=["video", "imagem"])
    ap.add_argument("--fila", type=int, default=4)
    ap.add_argument("--rodadas", type=int, default=6)
    ap.add_argument("--espera-max", type=int, default=25, help="min de geração por rodada")
    ap.add_argument("--regen", type=int, default=1, help="re-gerações por reprovado no gate")
    ap.add_argument("--min-sim", type=float, default=0.6)
    a = ap.parse_args()

    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    job = out.parent
    lote = vd._normalizar_lote(json.loads(Path(a.lote).read_text(encoding="utf-8")))
    alvos = [x for x in lote if x["tipo"] == a.tipo]
    proj = (projeto_do_canal(a.canal) or {}).get("projeto")
    if not proj:
        _log(f"!!! canal {a.canal} sem projeto registrado (veo_flow/projetos.json)")
        sys.exit(2)
    # tentativas do gate sobrevivem entre rodadas E entre execuções
    f_tent = job / f"_gate_tentativas_{a.tipo}.json"
    tent = json.loads(f_tent.read_text(encoding="utf-8")) if f_tent.exists() else {}

    _log(f"=== CICLO {a.canal}/{a.colecao}: {len(alvos)} {a.tipo}s | fila {a.fila} ===")
    parados = 0
    for rodada in range(1, a.rodadas + 1):
        desist = {k for k, v in tent.items() if v > a.regen}
        faltam = [it for it in alvos if not (out / it["arquivo"]).exists()
                  and it["arquivo"] not in desist]
        if not faltam:
            break
        _log(f"--- rodada {rodada}: faltam {len(faltam)} (desistidos {len(desist)}) ---")
        antes = _prontos(out, alvos)
        matar_tudo()
        pw, ctx, page = fd.abrir(headless=False)
        try:
            page.goto(f"{fd.BASE}/project/{proj}", wait_until="domcontentloaded")
            fd._pausa(6, 9)
            abrir_colecao(page, a.canal, a.colecao)
            fd.garantir_modo(page, a.tipo)

            # 1) ENVIA o que falta, mantendo <= fila gerações simultâneas
            cards0, falhas0, enviados = _n_cards(page), vd._cards_falha(page), 0
            for it in faltam:
                t_espera = time.time()
                while True:
                    voo = enviados - max(0, _n_cards(page) - cards0) \
                          - max(0, vd._cards_falha(page) - falhas0)
                    if voo < a.fila:
                        break
                    fd.dispensar_avisos(page)
                    if time.time() - t_espera > 12 * 60:
                        _log("  fila presa há 12min — sigo pro download do que houver")
                        break
                    time.sleep(10)
                fd.enviar_prompt(page, it["prompt"])
                enviados += 1
                fd._pausa(3, 6)
            _log(f"  {enviados} prompts enviados")

            # 2) ESPERA a geração terminar (badges de % sumirem), com teto
            t0 = time.time()
            while time.time() - t0 < a.espera_max * 60:
                fd.dispensar_avisos(page)
                g = _n_gerando(page)
                if g == 0:
                    break
                time.sleep(20)
            _log(f"  geração encerrada ({_n_gerando(page)} pendentes no teto)")

            # 3) UM download da coleção inteira
            zip_p = job / f"_colecao_{a.tipo}_r{rodada}.zip"
            baixar_colecao(page, a.canal, a.colecao, zip_p)
        except Exception as e:
            _log(f"!! rodada {rodada} caiu: {type(e).__name__}: {str(e)[:120]}")
            try:
                page.screenshot(path=str(job / f"_ciclo_erro_r{rodada}.png"))
            except Exception:
                pass
            zip_p = None
        finally:
            try:
                ctx.close()
                pw.stop()
            except Exception:
                pass

        # 4) casa por título + gate local (browser JÁ fechado — daqui é tudo local)
        if zip_p and zip_p.exists():
            pasta = job / f"_zip_r{rodada}"
            with zipfile.ZipFile(zip_p) as z:
                z.extractall(pasta)
            n, casados, sobra_f, sobra_i = aplicar(pasta, alvos, out, min_sim=a.min_sim)
            _log(f"  zip: {n} casados | {len(sobra_f)} sem par | {len(sobra_i)} sem arquivo")
            novos = [it for it in alvos if (out / it["arquivo"]).exists()
                     and it["arquivo"] not in tent]
            for it in novos:
                if a.tipo == "video":
                    ok, flags = vd._aprovado(out / it["arquivo"], it, a.tipo, out / "_tmp")
                    if not ok:
                        (out / it["arquivo"]).unlink(missing_ok=True)
                        tent[it["arquivo"]] = tent.get(it["arquivo"], 0) + 1
                        _log(f"  {it['arquivo']} REPROVADO {flags} — re-gera na próxima "
                             f"({tent[it['arquivo']]}/{a.regen})")
                        continue
                tent.setdefault(it["arquivo"], 0)   # 0 = aprovado/aceito
            f_tent.write_text(json.dumps(tent, ensure_ascii=False), encoding="utf-8")

        agora = _prontos(out, alvos)
        _log(f"  rodada {rodada}: {agora}/{len(alvos)} prontos (+{agora - antes})")
        parados = parados + 1 if agora == antes else 0
        if parados >= 2:
            _log("!!! 2 rodadas sem arquivo novo — parando (conferir tela/sessão)")
            break

    matar_tudo()
    finais = _prontos(out, alvos)
    desist = {k for k, v in tent.items() if v > a.regen}
    _log(f"=== FIM: {finais}/{len(alvos)} {a.tipo}s | desistidos no gate: {len(desist)} ===")
    if desist:
        _log(f"    (vão pro curador/banco): {sorted(desist)[:8]}")


if __name__ == "__main__":
    main()
