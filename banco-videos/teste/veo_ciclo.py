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
import shutil
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "veo_flow"))
sys.stdout.reconfigure(encoding="utf-8")

import flow_driver as fd  # noqa
import veo_driver as vd  # noqa — _normalizar_lote, _cards_falha, _aprovado
from veo_colecao import (abrir_colecao, baixar_projeto, projeto_do_canal,  # noqa
                         garantir_dentro, baixar_cards_recentes)
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
    ap.add_argument("--fila", type=int, default=9)   # Lower Priority enfileira no servidor: 3 rajadas de 3
    ap.add_argument("--rodadas", type=int, default=6)
    ap.add_argument("--espera-max", type=int, default=25, help="min de geração por rodada")
    ap.add_argument("--regen", type=int, default=1, help="re-gerações por reprovado no gate")
    ap.add_argument("--min-sim", type=float, default=0.6)
    ap.add_argument("--pausa-rajada", type=int, default=50,
                    help="segundos entre rajadas (timer puro; DOM mente)")
    ap.add_argument("--rajada", type=int, default=0,
                    help="prompts por rajada (0 = automático: 8 vídeo / 6 imagem)")
    ap.add_argument("--colher-cards", type=int, default=5,
                    help="lote com <= N itens colhe card a card (evita baixar o projeto)")
    ap.add_argument("--rajada-min", type=int, default=3,
                    help="piso da rajada quando o Flow reclamar de ritmo")
    a = ap.parse_args()

    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    job = out.parent
    lote = vd._normalizar_lote(json.loads(Path(a.lote).read_text(encoding="utf-8")))
    alvos = [x for x in lote if x["tipo"] == a.tipo]
    _reg = projeto_do_canal(a.canal) or {}
    proj = _reg.get("projeto")
    # 06/08: PROJETO É ATADO À CONTA. O seletor de perfis devolveu um perfil de OUTRA
    # conta (conta2) e o driver abriu o projeto do AMZ nela — sem login pra ele, a
    # página veio vazia e o erro saiu como "botão '+' não encontrado — UI do Flow
    # mudou". Não era a UI: era a conta errada. O perfil vira parte do registro do
    # canal e o driver não escolhe mais sozinho.
    _perfil = _reg.get("perfil")
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
        pw, ctx, page = fd.abrir(headless=False, perfil=_perfil)
        try:
            page.goto(f"{fd.BASE}/project/{proj}", wait_until="domcontentloaded")
            fd._pausa(6, 9)
            # ORDEM IMPORTA (06/08, causa raiz de "gerando fora da coleção"): o
            # popup do `garantir_modo` EXPULSA da coleção pro projeto. Conferir o
            # modelo AINDA NA RAIZ e só então entrar — nunca o contrário.
            fd.garantir_modo(page, a.tipo)
            cid_col = abrir_colecao(page, a.canal, a.colecao)

            # 1) ENVIA em RAJADAS DE 3 (Piter 05/08): 1 em 1 com pausa era lento
            # demais pro Lower Priority, que enfileira no SERVIDOR de qualquer jeito.
            # Rajada de 3 + pausa curta preenche a fila sem virar metralhadora.
            # 05/08 (3ª iteração do pacing): contar cards NÃO funciona — o grid é
            # VIRTUALIZADO, o DOM só monta o que cabe na viewport, então a contagem
            # fica capada num teto constante e o "voo" nunca drena (nem com scroll,
            # nem com reload). Ritmo por TIMER puro: rajada de 3 a cada ~50s. É
            # imune à mentira do DOM; o Lower Priority/NB enfileira no servidor.
            # VARIAÇÃO AUTOMÁTICA (05/08, regra do Piter): o filtro do Google às
            # vezes recusa por "pessoa famosa"/política — e re-tentar o MESMO texto
            # recusa de novo. Item reenviado ganha uma cauda diferente por rodada
            # (no FIM, pra não mudar o TÍTULO que o casamento do zip usa).
            VARIA = ["", " Candid documentary field recording.",
                     " Natural unposed moment, observational style.",
                     " Quiet vérité tone, ordinary working day."]
            envios_f = job / "_envios.json"
            envios = json.loads(envios_f.read_text(encoding="utf-8"))                 if envios_f.exists() else {}
            # VAZÃO ADAPTATIVA (06/08, Piter): sobe pra 8 vídeo / 6 imagem e RECUA
            # sozinha se o Flow reclamar de velocidade/volume. Recusa por POLÍTICA
            # não conta — é assunto do prompt, e cortar a vazão por causa dela
            # derrubaria a produção tratando o sintoma errado. O piso fica gravado
            # em _ritmo.json pra valer nas rodadas seguintes e no próximo lote.
            ritmo_f = job / "_ritmo.json"
            ritmo = json.loads(ritmo_f.read_text(encoding="utf-8")) if ritmo_f.exists() else {}
            padrao = 8 if a.tipo == "video" else 6
            tam = int(ritmo.get(a.tipo) or a.rajada or padrao)
            tam = max(a.rajada_min, tam)
            _log(f"  rajada: {tam} por vez, pausa ~{a.pausa_rajada}s")
            avisos_ritmo = 0
            enviados = 0
            for i in range(0, len(faltam), tam):
                fd.dispensar_avisos(page)
                garantir_dentro(page, a.canal, a.colecao, cid_col)
                for it in faltam[i:i + tam]:
                    n_env = envios.get(it["arquivo"], 0)
                    sufixo = VARIA[n_env % len(VARIA)]
                    ok_env = fd.enviar_prompt(page, it["prompt"] + sufixo,
                                              exigir_mencao=bool(it.get("avatar")))
                    if ok_env is False:
                        continue   # avatar sem chip: nem conta como envio
                    envios[it["arquivo"]] = n_env + 1
                    enviados += 1
                    fd._pausa(1.0, 2.0)
                _log(f"  rajada: {enviados}/{len(faltam)} enviados")
                # o Flow reclamou de RITMO? 2 avisos = corta a vazão pela metade
                if fd.erro_de_ritmo(page):
                    avisos_ritmo += 1
                    _log(f"  !! aviso de ritmo #{avisos_ritmo}")
                    if avisos_ritmo >= 2 and tam > a.rajada_min:
                        tam = max(a.rajada_min, tam // 2)
                        ritmo[a.tipo] = tam
                        ritmo_f.write_text(json.dumps(ritmo), encoding="utf-8")
                        avisos_ritmo = 0
                        _log(f"  >> vazão REDUZIDA para {tam} por rajada (gravado)")
                if i + tam < len(faltam):
                    fd._pausa(a.pausa_rajada * 0.8, a.pausa_rajada * 1.2)
            envios_f.write_text(json.dumps(envios), encoding="utf-8")
            _reenv = [k for k, v in envios.items() if v > 1]
            if _reenv:
                _log(f"  variação aplicada em {len(_reenv)} reenviados")
            _log(f"  {enviados} prompts enviados")

            # 2) ESPERA a geração terminar (badges de % sumirem), com teto.
            # Mesmo problema do grid lazy: recarrega periodicamente pra ler a verdade.
            t0 = time.time()
            n_esp2 = 0
            time.sleep(75)   # badges de % demoram a aparecer; checar cedo = falso "acabou"
            while time.time() - t0 < a.espera_max * 60:
                fd.dispensar_avisos(page)
                n_esp2 += 1
                if n_esp2 % 6 == 0:
                    page.reload(wait_until="domcontentloaded")
                    fd._pausa(3, 5)
                g = _n_gerando(page)
                if g == 0:
                    break
                time.sleep(20)
            _log(f"  geração encerrada ({_n_gerando(page)} pendentes no teto)")

            # 3) UM download do PROJETO inteiro (o card da coleção some na
            # virtualização do grid; o ⋮ do topo está sempre lá — plano do Piter)
            # COLHEITA PROPORCIONAL AO LOTE (06/08, Piter): "Baixar projeto" traz o
            # projeto do CANAL inteiro (2.351 arquivos e crescendo) — ótimo pra 60
            # itens, absurdo pra 3. Lote pequeno colhe card a card no topo do grid.
            zip_p = None
            if len(faltam) <= a.colher_cards:
                pasta_c = job / f"_cards_r{rodada}"
                if pasta_c.exists():
                    shutil.rmtree(pasta_c, ignore_errors=True)
                try:
                    baixar_cards_recentes(page, a.canal, a.colecao, pasta_c,
                                          n=max(3, len(faltam) * 2))
                    zip_p = "CARDS"
                except Exception as e_c:
                    _log(f"  colheita por cards falhou ({str(e_c)[:70]}) — indo de projeto")
            if zip_p is None:
                zip_p = job / f"_colecao_{a.tipo}_r{rodada}.zip"
                baixar_projeto(page, a.canal, zip_p)
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
        pasta = None
        if zip_p == "CARDS":
            pasta = job / f"_cards_r{rodada}"
        elif zip_p and zip_p.exists():
            pasta = job / f"_zip_r{rodada}"
            # 06/08: a pasta acumulava os downloads do dia (6 cópias do mesmo título,
            # uma por rodada) e o casamento podia servir a versão VELHA de um take
            # regerado. Cada extração começa limpa.
            if pasta.exists():
                shutil.rmtree(pasta, ignore_errors=True)
            with zipfile.ZipFile(zip_p) as z:
                z.extractall(pasta)
        if pasta and pasta.exists():
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
