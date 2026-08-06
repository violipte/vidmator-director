# -*- coding: utf-8 -*-
"""ÂNCORA de tema no prompt de geração — regra única, usada por TODAS as portas.

Por que existe (06/08, QA do Piter sobre o job amazônico):

O gerador não sabe ONDE a cena acontece. A `busca` que o diretor escreve descreve o
ASSUNTO do beat, não o cenário — e um assunto genérico sem cenário sai em qualquer
lugar do mundo. No job da Amazônia, `"solitary person in vast landscape
contemplative"` voltou um vale ESCOCÊS: montanha, urze, moletom. Correto para o
pedido, errado para o vídeo.

O que revelou o defeito não foi o prompt — foi o fato de que existiam DUAS portas de
geração com regras diferentes:

    curador5._fila_geracao()   -> _gerar.json   (buraco de beat)   SEM âncora
    montador5._prompt_do_gap() -> gaps          (buraco de tempo)  COM âncora

b074 ("stingray in natural habitat") e b075 ("tropical river ... jungle") passaram
porque o próprio texto já dizia o bioma. Foi sorte, não regra: o único beat cujo
texto não carregava cenário foi o único que saiu errado. Uma regra que só vale
quando o prompt já se defende sozinho não é uma regra.

Daí este módulo: leve de propósito (só stdlib) para que qualquer porta possa
importá-lo sem arrastar CLIP, gate ou registry — o custo de importar foi o que
manteve as duas cópias divergentes.
"""
import re

MAX = 180

# ESQUEMA não tem lugar. Um diagrama de coagulação não acontece na Amazônia — a
# âncora geográfica só disputa espaço com o assunto e empurra o gerador para uma
# foto de selva com rótulos falsos. O Piter já tinha validado isso na mão em
# 02/08: "neurotoxin molecular structure diagram" saiu ótimo SEM âncora nenhuma.
# A âncora serve para CENA (onde a câmera está), não para ilustração técnica.
_ESQUEMA = ("diagram", "infographic", "schematic", "cross-section", "cutaway",
            "molecular", "anatomy", "anatomical", "chart", "graph of",
            "vector illustration", "scientific illustration")


def ancorar(busca, ancora, falado=""):
    """Prompt de geração com o tema garantido na frente.

    `busca` é o pedido do diretor; `falado` é a narração do momento, usada só quando
    o beat não trouxe busca (caso dos gaps de tempo). A âncora entra como PREFIXO —
    o gerador lê o começo como cenário e o resto como assunto.

    Só entra se ainda não estiver lá: `"amazon rainforest, amazon rainforest, x"`
    desperdiça prompt e empurra o assunto para fora do limite de caracteres.
    """
    alvo = (busca or falado or "").strip()
    anc = (ancora or "").strip()
    if not anc:
        return alvo[:MAX]
    if not alvo:
        return anc[:MAX]
    if e_esquema(alvo):
        return alvo[:MAX]
    if not _ja_ancorado(alvo, anc):
        alvo = f"{anc}, {alvo}"
    return alvo.strip()[:MAX]


def e_esquema(alvo):
    """O pedido é ilustração TÉCNICA, não cena? Então não leva âncora de lugar."""
    a = (alvo or "").lower()
    return any(k in a for k in _ESQUEMA)


def _ja_ancorado(alvo, anc):
    """A âncora já está no prompt?

    Compara por PALAVRA-CHAVE, não por substring: 'amazon' dentro de 'amazonian' é
    presença real, mas 'amazon' dentro de 'amazonas' também — e ambos ancoram. O que
    não vale é casar 'jungle' com 'junglefowl' em posição de assunto, por isso a
    checagem é por prefixo de token e não por `in` cru na string inteira.

    Usa a palavra mais específica da âncora (a mais longa), não a primeira: em
    'the amazon rainforest' a primeira é 'the', que casa com tudo.
    """
    toks = [t for t in re.findall(r"[a-z]+", anc.lower()) if len(t) > 3]
    if not toks:
        return False
    chave = max(toks, key=len)
    return any(t.startswith(chave[:6]) for t in re.findall(r"[a-z]+", alvo.lower()))


def conferir(prompt, ancora):
    """(ok, motivo) — o prompt saiu ancorado? Para o crítico auditar a fila ANTES de
    gastar geração, em vez de descobrir no frame renderizado."""
    if not (ancora or "").strip():
        return True, "job sem âncora declarada"
    if e_esquema(prompt or ""):
        return True, "ilustração técnica — âncora de lugar não se aplica"
    if _ja_ancorado(prompt or "", ancora):
        return True, ""
    return False, f"prompt sem o tema '{ancora}' — pode sair em qualquer lugar do mundo"
