# -*- coding: utf-8 -*-
"""PERSONAGEM DO CANAL no Flow (04/08) — identidade consistente do host.

Por que existe: o VEO NÃO mantém o mesmo rosto entre gerações. Dois clipes do "mesmo"
biólogo saem como duas pessoas diferentes — e um canal com host que troca de cara a
cada vídeo não constrói identidade nenhuma. O Flow tem a aba **Personagens**
("Crie e reutilize personagens para manter a consistência nos vídeos"), que resolve
isso: cria-se o personagem UMA vez e ele é reusado nas gerações seguintes.

ESCOPO (style_card["avatar"]["escopo"], decisão do Piter 04/08):
  "canal"  -> UM personagem para o canal inteiro, reusado em todo vídeo. É o que dá
              IDENTIDADE — o espectador reconhece o host. Criado uma vez e guardado
              em `veo_flow/personagens.json`.
  "video"  -> um personagem novo por vídeo (variedade; sem identidade fixa).
  "nenhum" -> canal faceless puro, sem avatar (o padrão dos demais canais).

FLUXO (ditado pelo Piter 04/08 — detalhe em `veo_flow/FLOW_MAP.md`):
  descrever no campo "Descreva seu personagem..." (Nano Banana gera ali, 0 créditos)
  -> **Selecionar uma voz** (sempre! muitas são ruins: ver `veo_flow/VOZES.md`)
  -> nomear -> **Concluir** (canto superior direito).
Alternativa: gerar a imagem no projeto e usar "Adicionar do projeto".

USO NA GERAÇÃO: basta escrever **@Nome** no prompt (ex.: `@Russel`) — é assim que o
clipe sai com o MESMO host. `montar_prompt_avatar()` monta isso.
"""
import json
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "veo_flow"))
sys.stdout.reconfigure(encoding="utf-8")


def _fd():
    """flow_driver só é importado por quem DIRIGE o browser — assim `config_do_canal`
    e o registro funcionam no Python normal (o playwright mora no veo_venv)."""
    import flow_driver as fd
    return fd

REGISTRO = Path(__file__).resolve().parents[2] / "veo_flow" / "personagens.json"


def _registro_ler():
    try:
        return json.loads(REGISTRO.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _registro_gravar(d):
    REGISTRO.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")


def config_do_canal(style_card):
    """Normaliza o bloco `avatar` do style_card (ausente => canal faceless)."""
    av = (style_card or {}).get("avatar") or {}
    return {"escopo": av.get("escopo", "nenhum"),
            "nome": av.get("nome") or "",
            "descricao": av.get("descricao") or "",
            "voz": av.get("voz") or "Iapetus",
            "fala_intro": bool(av.get("fala_intro", True)),
            "id_flow": av.get("id_flow") or ""}


def personagem_do_canal(canal):
    """Devolve o personagem já registrado para o canal, ou None."""
    return _registro_ler().get(canal)


def registrar_existente(canal, nome, voz="", descricao=""):
    """Registra um personagem criado NA MÃO no Flow (sem recriá-lo).
    Foi assim que o 'Russel' do canal AMZ entrou: o Piter montou na interface."""
    reg = _registro_ler()
    reg[canal] = {"nome": nome, "voz": voz, "descricao": descricao,
                  "escopo": "canal", "mencao": f"@{nome}", "origem": "manual"}
    _registro_gravar(reg)
    return reg[canal]


def montar_prompt_avatar(ficha, acao, estilo="", fala=""):
    """Prompt de um beat COM o host. A menção @Nome é o que amarra a identidade.

    A fala vai como ÁUDIO explícito: pedir a fala junto da descrição visual fez o
    gerador DESENHAR a legenda no quadro (04/08, QA do Piter: "imagem precisa ser sem
    texto, somente o vídeo com texto").

    ⚠️ 05/08 (Piter): o NOME do personagem existe SÓ no chip do @ — nome escrito no
    TEXTO do prompt dispara a política de "pessoa famosa" do Google e o take cai.
    No corpo, sempre pronome; qualquer ocorrência do nome é trocada automaticamente."""
    nome = (ficha.get("nome") or "").strip()
    if nome:
        pad = re.compile(rf"\b{re.escape(nome)}\b", re.I)
        for rot, txt in (("acao", acao), ("fala", fala), ("estilo", estilo)):
            if pad.search(txt or ""):
                print(f"  !! nome '{nome}' no {rot} do prompt — trocado por pronome "
                      f"(política de pessoa famosa)")
        acao = pad.sub("he", acao or "")
        fala = pad.sub("he", fala or "")
        estilo = pad.sub("", estilo or "")
    # calibração EMPÍRICA — APROVADA pelo Piter 05/08 ("take com 89 ficou
    # excelente, teto de 90 aprovado"):
    #   122 chars -> CORTA no meio | 69 -> fala inteiro mas LENTO (VEO estica
    #   pra preencher os 8s) | 89 -> ritmo natural. Faixa boa: 80-90 chars.
    if fala and (len(fala) > 90 or len(fala.split()) > 16):
        raise ValueError(f"fala do take longa demais ({len(fala)} chars / "
                         f"{len(fala.split())} palavras; teto 90/16): {fala[:60]!r}")
    p = f"{ficha['mencao']} {acao.strip()}"
    if estilo:
        p += f". {estilo.strip()}"
    p += ". Clean frame, no subtitles, no captions, no burned-in text, no watermark"
    if fala:
        p += f". AUDIO ONLY (spoken by him, never written on screen): {fala.strip()}"
    p = p[:900]
    # 06/08 (Piter renomeou o host pra "Travesseiro" pra fugir da política de pessoa
    # famosa): com nome COMUM o vazamento deixa de ser risco de recusa e vira erro
    # VISÍVEL — "travesseiro" solto no texto faz o gerador desenhar um travesseiro na
    # cena. A substituição acima é best-effort (regex de palavra); esta checagem é a
    # rede: fora do chip inicial, o nome não pode sobrar em lugar nenhum.
    if nome:
        corpo = p[len(ficha["mencao"]):]
        # SUBSTRING, não palavra inteira: a troca por pronome usa \b e deixaria passar
        # "Travesseiros"/"Travesseiro-". Com nome COMUM, qualquer pedaço do nome no
        # corpo já é motivo pra abortar — o gerador desenharia o objeto na cena.
        if nome.lower() in corpo.lower():
            raise ValueError(
                f"nome '{nome}' vazou no CORPO do prompt — o gerador desenharia o "
                f"objeto na cena. Prompt: {p[:160]!r}")
    return p


def criar_personagem(page, nome, descricao, voz="Iapetus", espera_gen=45):
    """Cria o personagem completo (fluxo ditado pelo Piter 04/08 — ver FLOW_MAP.md):
    descrever -> Nano Banana gera -> escolher VOZ -> nomear -> Concluir.

    A voz é parte da identidade tanto quanto o rosto: um canal que troca de voz entre
    vídeos não é reconhecido. Vozes testadas em `veo_flow/VOZES.md`.
    """
    fd = _fd()
    bt = page.get_by_role("button", name=re.compile("Personag", re.I))
    if not bt.count():
        raise RuntimeError("aba Personagens não encontrada — a UI do Flow mudou")
    bt.first.click()
    fd._pausa(2.0, 3.0)

    # 04/08: sem personagem criado, o clique em "Personagens" já CAI na tela de
    # criação — e o "Novo personagem" do topo é o CABEÇALHO com a seta de VOLTAR.
    # Clicar nele saía da tela e o campo nunca aparecia.
    cx = page.get_by_placeholder(re.compile("Descreva seu personagem", re.I))
    if not cx.count():
        b = page.get_by_role("button", name=re.compile("Novo personagem|Criar", re.I))
        if b.count():
            b.last.click()
            fd._pausa(1.5, 2.5)
        cx = page.get_by_placeholder(re.compile("Descreva seu personagem", re.I))
    cx.wait_for(timeout=20000)
    cx.click()
    cx.fill(descricao[:900])
    fd._pausa(0.6, 1.2)
    page.keyboard.press("Enter")
    print(f"  '{nome}': imagem-base pedida ao Nano Banana...")
    time.sleep(espera_gen)

    # ---- voz ----
    bv = page.get_by_role("button", name=re.compile("Selecionar uma voz|voz", re.I))
    if bv.count():
        bv.first.click()
        fd._pausa(1.5, 2.5)
        alvo = page.get_by_text(re.compile(rf"^{re.escape(voz)}$", re.I))
        if not alvo.count():
            alvo = page.get_by_text(re.compile(re.escape(voz), re.I))
        if alvo.count():
            alvo.first.click()
            fd._pausa(0.8, 1.4)
            add = page.get_by_role("button", name=re.compile("Adicionar ao personagem", re.I))
            if add.count():
                add.first.click()
                fd._pausa(1.0, 2.0)
            print(f"  voz: {voz}")
        else:
            print(f"  !! voz '{voz}' não encontrada na lista — segue sem voz")
            page.keyboard.press("Escape")
    else:
        print("  !! botão de voz não encontrado — segue sem voz")

    # ---- nome (título 'Personagem sem título', lápis ao lado) ----
    try:
        lap = page.get_by_role("button", name=re.compile("edit|Renomear|lápis", re.I))
        if lap.count():
            lap.first.click()
            fd._pausa(0.5, 1.0)
        tit = page.get_by_text(re.compile("Personagem sem título", re.I))
        if tit.count():
            tit.first.click()
            fd._pausa(0.4, 0.8)
        page.keyboard.press("Control+A")
        page.keyboard.type(nome, delay=45)
        page.keyboard.press("Tab")
        fd._pausa(0.6, 1.2)
    except Exception:
        print(f"  !! não consegui renomear — o personagem pode ficar 'sem título'")

    # ---- concluir (canto superior DIREITO) ----
    cc = page.get_by_role("button", name=re.compile("^Concluir$|Concluir", re.I))
    if cc.count():
        cc.first.click()
        fd._pausa(1.5, 2.5)
        print(f"  personagem '{nome}' CONCLUÍDO")
    else:
        print("  !! botão Concluir não encontrado — conferir na tela")
    return nome


def garantir_personagem(page, canal, cfg):
    """Idempotente: cria só se o canal ainda não tem personagem (escopo=canal).
    escopo=video cria sempre; escopo=nenhum não faz nada."""
    if cfg["escopo"] == "nenhum" or not cfg["descricao"]:
        return None
    reg = _registro_ler()
    if cfg["escopo"] == "canal" and reg.get(canal):
        print(f"  personagem do canal já existe: {reg[canal]['nome']} (reusando)")
        return reg[canal]
    nome = cfg["nome"] or f"host_{canal}"
    criar_personagem(page, nome, cfg["descricao"], voz=cfg.get("voz") or "Iapetus")
    ficha = {"nome": nome, "descricao": cfg["descricao"], "escopo": cfg["escopo"],
             "voz": cfg.get("voz") or "Iapetus", "mencao": f"@{nome}"}
    if cfg["escopo"] == "canal":
        reg[canal] = ficha
        _registro_gravar(reg)
        print(f"  personagem do canal REGISTRADO: {nome} -> {REGISTRO.name}")
    return ficha
