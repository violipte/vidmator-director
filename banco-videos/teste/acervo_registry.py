# -*- coding: utf-8 -*-
"""REGISTRY do acervo (Diretor v2) — cada animação tem ID, natureza, e um BUILDER validado.
Esquema do Piter (20/07): o LLM entrega NATUREZA+DADOS; o código SORTEIA o ID dentro da
natureza elegível (random com seed por beat + quota por vídeo) e o builder monta os props.
REGRA DE FERRO: builder retorna None se os dados não sustentam o componente -> re-sorteia
outro ID (NUNCA renderiza default de exemplo, NUNCA texto vazio).

Naturezas: mapa | chart | texto_overlay | texto_full | imagem | pessoa
`needs_imgs`: nº de imagens reais que o executor precisa resolver (0 = nenhuma).
"""
import random
import re

def _num(texto):
    m = re.search(r"(\d[\d,\.]*)\s*(million|billion|thousand|percent|%)?", texto or "", re.I)
    if not m:
        return None
    v = float(m.group(1).replace(",", ""))
    u = (m.group(2) or "").lower()
    if u == "million": return v, "M"
    if u == "billion": return v, "B"
    if u == "thousand": return v, "K"
    if u in ("percent", "%"): return v, "%"
    if v >= 1e6: return round(v / 1e6, 1), "M"
    if v >= 1e4: return round(v / 1e3), "K"
    return v, ""

def _s(d, *ks):
    # 31/07: o LLM às vezes devolve `dados` como LISTA (ex.: [{...}]) — normaliza pro
    # 1º dict em vez de estourar AttributeError no meio do v2 pass
    if isinstance(d, (list, tuple)):
        d = next((x for x in d if isinstance(x, dict)), None)
    if not isinstance(d, dict):
        return None
    for k in ks:
        v = d.get(k)
        if v not in (None, "", []):
            return v
    return None

def _pais_ok(nome):
    """rejeita continente/região (bug 'North America' em componente de PAÍS)"""
    return str(nome).strip().lower() not in {
        "north america", "south america", "europe", "asia", "africa", "oceania",
        "middle east", "latin america", "central america", "antarctica", "worldwide", "global"}

# ---------------- builders (dados, texto, imgs) -> props | None ----------------
R = []  # (id, comp, natureza, needs_imgs, peso, builder)

def reg(comp, natureza, needs_imgs=0, peso=1.0):
    def deco(fn):
        R.append({"id": len(R), "comp": comp, "natureza": natureza,
                  "needs_imgs": needs_imgs, "peso": peso, "build": fn})
        return fn
    return deco

# ===== CHARTS =====
def _valor_num(*vals):
    """Número + sufixo a partir do que o diretor escreve: "10,000+", "< 1",
    "29 000", 27000. Ele redige como se fala; o componente conta um INTEIRO.
    Sem isto, 13 pedidos de contador animado viraram None no job amazônico."""
    import re as _re
    for v in vals:
        if isinstance(v, (int, float)):
            return int(v), ""
        s = str(v or "").strip()
        if not s:
            continue
        m = _re.search(r"(\d[\d.,\s]*)", s)
        if not m:
            continue
        try:
            n = int(float(m.group(1).replace(" ", "").replace(",", "")))
        except ValueError:
            continue
        resto = s.replace(m.group(1), "").strip()
        suf = "+" if "+" in resto else ("%" if "%" in resto else resto[:6])
        return n, suf
    return None, ""


@reg("NumberCountOverlay", "chart", peso=1.2)
def _b(d, t, im):
    # 02/08: exigia o número no TEXTO (`_num(t)`) e ignorava o que vinha em `dados`.
    # O diretor manda {"number": "10,000+"} e o beat era descartado. Agora dados
    # primeiro, texto como reserva.
    val, suf = _valor_num(_s(d, "number", "value", "valor", "count"))
    if val is None:
        g = _num(t)
        if not g:
            return None
        val, suf = g[0], g[1]
    lab = str(_s(d, "label", "title", "description", "unit") or "")[:40]
    return {"value": val, "suffix": suf, "label": lab} if lab else None

@reg("PercentageBarChart", "chart")
def _b(d, t, im):
    g = _num(t)
    if not g or g[1] != "%" or not (0 < g[0] <= 100): return None
    tt = str(_s(d, "title", "label") or "")[:50]
    return {"titleText": tt, "percentage": g[0], "bottomText": str(_s(d, "bottom", "subtitle") or "")[:40]} if tt else None

@reg("CirclePercent", "chart")
def _b(d, t, im):
    g = _num(t)
    if not g or g[1] != "%" or not (0 < g[0] <= 100): return None
    tt = str(_s(d, "title", "label") or "")[:50]
    return {"titleContent": tt, "percent": g[0]} if tt else None

@reg("BarChartComparison", "chart")
def _b(d, t, im):
    labs = [str(x).replace("(example)", "").strip() for x in (_s(d, "labels") or [])]
    vals = _s(d, "values") or []
    if len(labs) < 2 or len(vals) < 2: return None
    try: v0, v1 = float(vals[0]), float(vals[1])
    except Exception: return None
    dig = (t or "").replace(",", "").replace(".", "")
    if str(int(v0)) not in dig and str(int(v1)) not in dig: return None  # não ancorado
    return {"chartTitle": corte(_s(d, "title") or "", 44), "leftLabel": labs[0][:22], "leftValue": v0,
            "rightLabel": labs[1][:22], "rightValue": v1}

@reg("GrowingBarChart", "chart")
def _b(d, t, im):
    data = _s(d, "data") or []
    if not (data and isinstance(data[-1], dict)): return None
    tt = corte(_s(d, "title") or "", 44)
    p = {"title": tt}
    if data[-1].get("year"): p["finalBarYear"] = data[-1]["year"]
    p["finalBarText"] = str(data[-1].get("label") or data[-1].get("value") or "")[:20]
    return p if tt and p["finalBarText"] else None

@reg("PollSurveyBar", "chart")
def _b(d, t, im):
    g = _num(t)
    if not g or g[1] != "%": return None
    q = str(_s(d, "title", "question", "label") or "")[:70]
    return {"question": q, "primaryPercentage": g[0], "primaryLabel": str(_s(d, "primary", "label") or "A")[:20],
            "secondaryLabel": str(_s(d, "secondary") or "Others")[:20]} if q else None

# ===== MAPAS =====
@reg("MultiCountryOutline", "mapa")
def _b(d, t, im):
    def nome(x):
        return str(x.get("country") or x.get("name") or "") if isinstance(x, dict) else str(x)
    cs = [nome(x) for x in (_s(d, "regions", "countries") or []) if nome(x) and _pais_ok(nome(x))]
    if len(cs) < 2: return None
    p = {"countries": cs[:6]}
    vals = _s(d, "values") or []
    dig = (t or "").replace(",", "")
    limp = []
    for x in vals[:len(cs)]:
        s = str(x.get("label", "")) if isinstance(x, dict) else str(x)
        dd = "".join(c for c in s if c.isdigit())
        limp.append(s if (dd and dd in dig.replace(".", "")) else "")
    if any(limp): p["values"] = limp
    return p

def _coord(*vals):
    """(lat, lon) a partir das MUITAS formas que o diretor emite (02/08).

    Aqui estava a regressão que o Piter sentiu como "foi emburrecendo": o diretor
    PEDIA mapa — 9 pedidos no job amazônico — e o builder devolvia None em todos,
    porque ele mandava `coords: [-3.35, -64.71]` e o builder exigia `lat`/`lon`
    separados. Resultado: `ok=0` no registry-pass, repick, e o mapa virava uma pílula
    de texto. Os componentes SEMPRE estiveram registrados; faltava o tradutor.
    Aceita: [lat, lon] | {"lat":..,"lon":..} | {"latitude":..,"longitude":..}."""
    for v in vals:
        if isinstance(v, (list, tuple)) and len(v) >= 2:
            try:
                return float(v[0]), float(v[1])
            except (TypeError, ValueError):
                continue
        if isinstance(v, dict):
            la = v.get("lat", v.get("latitude"))
            lo = v.get("lon", v.get("lng", v.get("longitude")))
            if la is not None and lo is not None:
                try:
                    return float(la), float(lo)
                except (TypeError, ValueError):
                    continue
    return None, None


@reg("MapRoute", "mapa")
def _b(d, t, im):
    s, e = _s(d, "start_location") or {}, _s(d, "end_location") or {}
    la1, lo1 = _coord(s, _s(d, "start_coords", "startCoord"))
    la2, lo2 = _coord(e, _s(d, "end_coords", "endCoord"))
    n1 = str((s.get("name") if isinstance(s, dict) else None)
             or _s(d, "start_name", "from", "origem") or "")[:18]
    n2 = str((e.get("name") if isinstance(e, dict) else None)
             or _s(d, "end_name", "to", "destino") or "")[:18]
    # rota SEM coordenada real nunca renderiza (era o default Tehran->Dubai no ar)
    if not (n1 or n2):
        # o diretor às vezes nomeia a ROTA ("Solimões River") em vez das pontas —
        # com as coordenadas certas, isso basta pra desenhar o traçado
        rota = str(_s(d, "route_name", "name") or "").split(",")[0][:18]
        n1, n2 = (rota or "Origin"), (rota and "" or "Destination")
    if not (la1 is not None and la2 is not None):
        return None
    return {"startName": n1.split(",")[0], "endName": n2.split(",")[0],
            "startCoord": [lo1, la1], "endCoord": [lo2, la2]}


@reg("SatelliteLocationPin", "mapa")
def _b(d, t, im):
    nome = str(_s(d, "location", "name", "locationName", "place") or "")[:28]
    lat, lon = _coord(_s(d, "coords", "coordinates", "coord"), d)
    if not nome or lat is None:
        return None
    return {"locationName": nome, "locationSubTitle": str(_s(d, "year", "subtitle") or "")[:20],
            "latitude": lat, "longitude": lon}

@reg("RegionLocationText", "mapa")
def _b(d, t, im):
    pais = str(_s(d, "country", "countryName") or "")
    if not pais or not _pais_ok(pais): return None
    return {"countryName": pais[:24], "regionName": str(_s(d, "region", "city") or "")[:24],
            "text": str(_s(d, "text", "label") or "")[:40]}

# ===== TEXTO FULL (cartão com fundo próprio) =====
_ROTEIRO = {"txt": ""}


def set_roteiro(txt):
    """Carrega o roteiro ORIGINAL (fonte de verdade dos nomes próprios)."""
    _ROTEIRO["txt"] = " ".join((txt or "").lower().split())


def _autor_confiavel(nome):
    """01/08 (QA cobras): o roteiro dizia "The doctor in Minas Gerais"; o STT ouviu
    "Nasgerice" e o diretor extraiu isso como ENTIDADE PESSOA — o vídeo foi ao ar com
    uma citação assinada por alguém que NÃO EXISTE. Nome próprio é justamente o que o
    STT mais erra, e o diretor trabalha sobre a transcrição (precisa dela pro timing).
    Regra: só assina se o nome aparece LITERAL no roteiro. Senão o card vai sem
    assinatura — melhor citação anônima que fonte inventada."""
    n = " ".join((nome or "").lower().split())
    if not n:
        return False
    if not _ROTEIRO["txt"]:
        return True  # roteiro não carregado => não bloqueia (comportamento antigo)
    return n in _ROTEIRO["txt"]


@reg("QuoteCard", "texto_full", peso=1.2)
def _b(d, t, im):
    q = str(_s(d, "quote", "quoteText") or "")[:180]
    autor = str(_s(d, "author") or "")
    if not q or not autor: return None
    nome, _, cargo = autor.partition(",")
    if not _autor_confiavel(nome):
        print(f"[registry] atribuição DESCARTADA (nome ausente do roteiro): {nome.strip()!r}")
        nome, cargo = "", ""
    return {"quoteText": q, "name": nome.strip()[:30], "title": cargo.strip()[:40]}

@reg("ChapterTitle", "texto_full")
def _b(d, t, im):
    tt = corte(_s(d, "title") or "", 40)
    return {"title": tt, "chapterNumber": _s(d, "number") or 1, "subtitle": corte(_s(d, "subtitle") or "", 50)} if tt else None

@reg("TitleDescription", "texto_full")
def _b(d, t, im):
    tt = corte(_s(d, "title") or (t or "").split(",")[0], 38)
    ds = corte(_s(d, "description") or t or "", 110)
    return {"title": tt, "description": ds} if tt and ds and tt != ds[:38] else None

@reg("TextReveal", "texto_full")
def _b(d, t, im):
    mt = str(_s(d, "main", "title", "text") or "")[:30].strip()
    sec = str(_s(d, "secondary") or t or "")[:80].strip()
    return {"mainText": mt, "secondaryText": sec, "finalLabel": str(_s(d, "label") or "")[:24]} if mt else None

@reg("DualImpactSentence", "texto_full")
def _b(d, t, im):
    # 02/08: o diretor escreve sentence1/sentence2; o builder só olhava first/second
    # e devolvia None — 6 pedidos perdidos num job só.
    a = str(_s(d, "first", "text", "sentence1", "linha1") or "")[:70].strip()
    b2 = str(_s(d, "second", "sentence2", "linha2") or "")[:70].strip()
    return {"firstSentence": a, "secondSentence": b2} if a and b2 else None

@reg("SubjectTitleCard", "texto_full")
def _b(d, t, im):
    tt = str(_s(d, "name", "title") or "")[:34].strip()
    return {"firstTitle": tt, "firstSubtitle": str(_s(d, "subtitle", "description", "title") or "")[:60]} if tt else None

# ===== TEXTO OVERLAY (transparente — montador põe footage do tema atrás) =====
@reg("DisplayText", "texto_overlay")
def _b(d, t, im):
    tx = str(_s(d, "text") or t or "")[:80].strip()
    return {"text": tx} if len(tx) > 3 else None

@reg("SingleSentenceTextSlide", "texto_overlay")
def _b(d, t, im):
    tx = str(_s(d, "text", "sentence") or t or "")[:90].strip()
    return {"sentence": tx} if len(tx) > 3 else None

@reg("OneWordCallout", "texto_overlay")
def _b(d, t, im):
    w = str(_s(d, "word") or "").strip()
    return {"word": w[:16]} if 2 < len(w) <= 16 else None

@reg("BulletPointOverlay", "texto_overlay")
def _b(d, t, im):
    pts = [str(x)[:40] for x in (_s(d, "points", "bullets") or []) if str(x).strip()]
    return {"bullets": pts[:5]} if len(pts) >= 2 else None

@reg("CaptionTextOverlay", "texto_overlay")
def _b(d, t, im):
    tx = str(_s(d, "text", "caption") or t or "")[:70].strip()
    return {"caption": tx} if len(tx) > 3 else None

@reg("DateLocationOverlay", "texto_overlay")
def _b(d, t, im):
    tx = str(_s(d, "text", "date", "location") or "")[:40].strip()
    return {"text": tx} if tx else None

# ===== IMAGEM (slots preenchidos pelo executor com T2/T1 reais) =====
@reg("TwoImageComparison", "imagem", needs_imgs=2)
def _b(d, t, im):
    if len(im) < 2: return None
    return {"titleText": str(_s(d, "title", "text") or "")[:36], "leftImage": im[0], "rightImage": im[1]}

@reg("ThreeImageReveal", "imagem", needs_imgs=3)
def _b(d, t, im):
    return {"images": im[:3]} if len(im) >= 3 else None

@reg("FourImageSlideshow", "imagem", needs_imgs=4)
def _b(d, t, im):
    return {"images": im[:4]} if len(im) >= 4 else None

@reg("FourImageCaptionGrid", "imagem", needs_imgs=4)
def _b(d, t, im):
    if len(im) < 4: return None
    caps = [str(x)[:24] for x in (_s(d, "captions") or [])][:4]
    return {"images": im[:4], "captions": caps if len(caps) == 4 else [], "showText": len(caps) == 4}

@reg("DualImageOnGrid", "imagem", needs_imgs=2)
def _b(d, t, im):
    if len(im) < 2: return None
    labs = [str(x)[:20] for x in (_s(d, "labels") or [])]
    return {"leftImage": im[0], "rightImage": im[1],
            "leftLabel": (labs[0] if labs else ""), "rightLabel": (labs[1] if len(labs) > 1 else "")}

@reg("SplitScreenComparison", "imagem", needs_imgs=2)
def _b(d, t, im):
    return {"leftImage": im[0], "rightImage": im[1]} if len(im) >= 2 else None

@reg("BeforeAfterArrow", "imagem", needs_imgs=2)
def _b(d, t, im):
    return {"beforeImage": im[0], "afterImage": im[1]} if len(im) >= 2 else None

@reg("ImageCallout", "imagem", needs_imgs=1)
def _b(d, t, im):
    tx = str(_s(d, "text", "label", "callout") or "")[:36].strip()
    return {"image": im[0], "calloutText": tx} if im and tx else None

@reg("ArticleNewsCard", "imagem", needs_imgs=1)
def _b(d, t, im):
    tx = str(_s(d, "text") or t or "")[:120].strip()
    return {"articleImage": im[0], "articleText": tx,
            "highlightText": str(_s(d, "highlight") or "")[:40]} if im and tx else None

# ===== PESSOA =====
@reg("CharacterCard", "pessoa", needs_imgs=1)
def _b(d, t, im):
    nome = str(_s(d, "name") or "")[:30].strip()
    if not nome or not im: return None
    return {"characterImage": im[0], "title": nome, "subtitle": str(_s(d, "title", "subtitle", "description") or "")[:56]}

@reg("CharacterKeyword", "pessoa", needs_imgs=1)
def _b(d, t, im):
    kw = str(_s(d, "keyword", "word") or "").strip()
    return {"characterImage": im[0], "keyword": kw[:16]} if im and 2 < len(kw) <= 16 else None

@reg("NodeHierarchy", "pessoa")
def _b(d, t, im):
    top = str(_s(d, "top", "topNode") or "").strip()
    baixo = [str(x)[:20] for x in (_s(d, "bottom", "bottomNodes", "nodes") or []) if str(x).strip()]
    return {"topNode": top[:20], "bottomNodes": baixo[:3]} if top and len(baixo) >= 2 else None


# ============================================================================
# ALMOXARIFADO 2.0 (21/07) — variações novas com contrato unificado por categoria.
# Os comps antigos das naturezas rebuild-adas saem do SORTEIO (DEPRECATED) mas
# continuam rebuild-áveis (planos antigos). ChapterTitle/QuoteCard/pessoa ficam.
# ============================================================================
DEPRECATED = {
    "NumberCountOverlay", "PercentageBarChart", "CirclePercent", "BarChartComparison",
    "GrowingBarChart", "PollSurveyBar",
    "MultiCountryOutline", "MapRoute", "SatelliteLocationPin", "RegionLocationText",
    "TitleDescription", "TextReveal", "DualImpactSentence", "SubjectTitleCard",
    "DisplayText", "SingleSentenceTextSlide", "OneWordCallout", "BulletPointOverlay",
    "CaptionTextOverlay", "DateLocationOverlay",
    "TwoImageComparison", "ThreeImageReveal", "FourImageSlideshow", "FourImageCaptionGrid",
    "DualImageOnGrid", "SplitScreenComparison", "BeforeAfterArrow", "ImageCallout", "ArticleNewsCard",
}

def _reg2(comp, natureza, needs_imgs=0, peso=1.0, max_uso=None, build=None, min_dur=0.0, max_dur=None):
    R.append({"id": len(R), "comp": comp, "natureza": natureza, "needs_imgs": needs_imgs,
              "peso": peso, "max_uso": max_uso, "build": build, "min_dur": min_dur, "max_dur": max_dur})

# ---- HUMANIZAÇÃO DE TEXTO (QA Piter 21/07: transcrição CRUA truncada na tela = LIXO) ----
_UNIT_W = {"one":1,"two":2,"three":3,"four":4,"five":5,"six":6,"seven":7,"eight":8,"nine":9,"ten":10,
           "eleven":11,"twelve":12,"thirteen":13,"fourteen":14,"fifteen":15,"sixteen":16,"seventeen":17,
           "eighteen":18,"nineteen":19}
_TENS_W = {"twenty":20,"thirty":30,"forty":40,"fifty":50,"sixty":60,"seventy":70,"eighty":80,"ninety":90}
_SCALE_W = {"hundred":100,"thousand":1000,"million":1000000,"billion":1000000000}

def _digitos_no_texto(s):
    """'nineteen twenty' -> '1920'; 'forty five percent' -> '45 percent'; 'ninety thousand' -> '90,000'.
    'one'..'nine' sozinhos ficam por extenso (legibilidade)."""
    # 'forty-five' -> 'forty five' (só entre palavras-número)
    todas = set(_UNIT_W) | set(_TENS_W) | set(_SCALE_W)
    s = re.sub(r"\b(" + "|".join(todas) + r")-(" + "|".join(todas) + r")\b",
               r"\1 \2", s, flags=re.I)
    toks = s.split()
    res, i = [], 0
    while i < len(toks):
        raiz = toks[i].lower().strip(".,;:!?\"'()")
        if raiz in _UNIT_W or raiz in _TENS_W:
            j, seq, cur, total, punct = i, [], 0, 0, ""
            while j < len(toks):
                w = toks[j].lower().strip(".,;:!?\"'()")
                if w in _UNIT_W: cur += _UNIT_W[w]; seq.append(_UNIT_W[w])
                elif w in _TENS_W: cur += _TENS_W[w]; seq.append(_TENS_W[w])
                elif w in _SCALE_W:
                    cur = max(cur, 1) * _SCALE_W[w]
                    if _SCALE_W[w] >= 1000: total += cur; cur = 0
                    seq = []
                elif w == "and" and (cur or total): pass
                else: break
                m = re.search(r"[.,;:!?]+$", toks[j]); punct = m.group(0) if m else ""
                j += 1
                if punct: break  # pontuação FECHA o número ('nineteen twenty, seventeen' != 1937)
            n_words = j - i
            ano = None
            if len(seq) >= 2 and 13 <= seq[0] <= 19 and total == 0:
                y = seq[0] * 100 + sum(seq[1:])
                if 1300 <= y <= 2099: ano = y
            n = int(total + cur)
            if ano is not None:
                res.append(str(ano) + punct); i = j; continue
            if n >= 10 or n_words >= 2:  # 'one company' fica 'one company'
                fmt = str(n) if 1300 <= n <= 2099 else f"{n:,}"  # ano falado ('two thousand three') sem vírgula
                res.append(fmt + punct); i = j; continue
        res.append(toks[i]); i += 1
    return " ".join(res)

def humanizar(t):
    """Texto de TELA: siglas faladas coladas ('w l a'->'WLA'), números por extenso->dígitos, capitaliza."""
    s = " ".join((t or "").split())
    def _sig(m):
        letras = m.group(0).split()
        if set(x.lower() for x in letras) <= {"a", "i"}: return m.group(0)  # 'a', 'I' = palavras
        return "".join(x.upper() for x in letras)
    s = re.sub(r"\b(?:[A-Za-z] ){1,4}[A-Za-z]\b", _sig, s)
    s = _digitos_no_texto(s)
    return (s[0:1].upper() + s[1:]) if s else s

def corte(s, n):
    """Trunca SEM cortar palavra (QA tenis 23/07: 'Flagship Com', kicker pela metade).
    Estourou -> corta na última fronteira de palavra e limpa pontuação pendurada."""
    s = " ".join(str(s or "").split())
    if len(s) <= n:
        return s
    c = s[:n].rsplit(" ", 1)[0].rstrip(" ,;:—–-")
    return c if c else s[:n]

def frase_de_tela(t, max_p=12, min_p=3):
    """1ª sentença/cláusula COMPLETA em até max_p palavras — nunca corta no meio. None = recusa.
    Preferência (QA tenis 23/07): frase com ':' usa a CAUDA ('...this list: Rule one: cushioning'
    -> 'Rule one: cushioning') — o anúncio é a parte forte, não o preâmbulo inteiro."""
    s = humanizar(t)
    if ":" in s:
        cauda = s.split(":", 1)[1].strip().rstrip(".!?").strip()
        if 2 <= len(cauda.split()) <= max_p - 3:
            return cauda[0:1].upper() + cauda[1:]
    partes = re.split(r"(?<=[.!?;:,])\s+", s)
    acc = ""
    for p in partes:
        cand = (acc + " " + p).strip() if acc else p
        if len(cand.split()) <= max_p:
            acc = cand
            if cand.rstrip()[-1:] in ".!?": break
        else:
            break
    acc = acc.strip().rstrip(",;:").strip()
    return acc if len(acc.split()) >= min_p else None

_STOPW = {"and", "the", "of", "to", "a", "an", "or", "but", "with", "for", "in", "on", "at", "that", "which"}

def frase_forcada(t, max_p=8):
    """Último recurso: primeiras max_p palavras humanizadas + '...' (nunca termina em stopword)."""
    f = frase_de_tela(t, max_p=12)
    if f: return f
    ws = humanizar(t).split()[:max_p]
    while ws and ws[-1].lower().strip(".,;:") in _STOPW:
        ws.pop()
    return (" ".join(ws) + "...") if len(ws) >= 3 else None

# ---- TEXTO FULL (contrato {text,kicker}; SÓ frase completa humanizada — dados OU narração) ----
def _texto_build(d, t, im):
    fonte = str(_s(d, "text", "title", "sentence", "quote") or "").strip() or (t or "")
    tx = frase_de_tela(fonte, max_p=12)
    if not tx or len(tx) < 4: return None
    return {"text": corte(tx, 90), "kicker": corte(_s(d, "kicker", "label", "subtitle") or "", 34)}

for _c, _p, _mx in [("Texto01_Typewriter", 1.0, 1), ("Texto02_HighlightSweep", 1.0, 1),
                    ("Texto03_WordPop", 1.0, 1), ("Texto04_EditorialSerif", 1.1, 1),
                    ("Texto05_BoxedKicker", 1.0, 1), ("Texto06_SplitBar", 1.0, 1),
                    ("Texto07_StampImpact", 0.8, 1), ("Texto08_GradientGlow", 1.0, 1),
                    ("Texto09_UnderlineDraw", 1.0, 1), ("Texto10_LetterCascade", 0.9, 1)]:
    _reg2(_c, "texto_full", peso=_p, max_uso=_mx, build=_texto_build, min_dur=2.2)

# ---- TEXTO OVERLAY (contrato {text,kicker,dim}; dim calibrado: destaque 0.45-0.55, placa própria 0) ----
_OVL_DIM = {"Ovl01_ChapterBig": 0.5, "Ovl02_SubchapterLine": 0.45, "Ovl03_LowerThird": 0.0,
            "Ovl04_FootnotePill": 0.0, "Ovl05_CornerTag": 0.0, "Ovl06_CenterPunch": 0.55,
            "Ovl07_QuoteAttribution": 0.5, "Ovl08_SideNote": 0.35, "Ovl09_TickerCaption": 0.3,
            "Ovl10_NumberBadge": 0.4}

def _mk_ovl(comp):
    def _b(d, t, im):
        fonte = str(_s(d, "text", "title", "caption", "sentence") or "").strip() or (t or "")
        tx = frase_de_tela(fonte, max_p=10)
        if not tx or len(tx) < 4: return None
        return {"text": corte(tx, 90), "kicker": corte(_s(d, "kicker", "label") or "", 34), "dim": _OVL_DIM[comp]}
    return _b

for _c, _p, _mx, _md in [("Ovl01_ChapterBig", 1.0, 2, 2.0), ("Ovl02_SubchapterLine", 1.0, 3, 1.2),
                    ("Ovl03_LowerThird", 1.2, 4, 1.0), ("Ovl04_FootnotePill", 1.0, 3, 1.0),
                    ("Ovl05_CornerTag", 0.9, 3, 1.0), ("Ovl06_CenterPunch", 1.0, 2, 2.0),
                    ("Ovl07_QuoteAttribution", 0.9, 2, 2.5), ("Ovl08_SideNote", 0.9, 3, 1.2),
                    ("Ovl09_TickerCaption", 1.0, 3, 1.0), ("Ovl10_NumberBadge", 0.9, 2, 1.2)]:
    _reg2(_c, "texto_overlay", peso=_p, max_uso=_mx, build=_mk_ovl(_c), min_dur=_md)

# ---- GRÁFICOS (contrato {title,kicker,labels,values,suffix}; NÚMEROS SÓ ANCORADOS no texto) ----
# A DUPLICATA VELHA de _nums_do_texto morava aqui e SOBRESCREVIA a lógica correta
# (last-def-wins): sem punct-break ('nineteen twenty, seventeen'=1937!), sem hífen.
# _anc e o montador (R-26/27) usavam a versão bugada. Agora há UMA fonte: o parser
# tokenizado de _digitos_no_texto, reutilizado abaixo (QA 22/07 — golden test pegou).
def _nums_do_texto(t):
    """Set de números do texto (dígitos + POR EXTENSO), com pontuação fechando número
    e hífen tratado — mesma semântica do parser de _digitos_no_texto.
    ANCORAGEM ≠ display: aqui 'one'/'two' isolados CONTAM (QA 22/07: 'one day... takes
    two' não ancorava values [1,2] perfeitos porque o display os mantém por extenso)."""
    achados = set(re.findall(r"\d[\d,]*", (t or "").replace(",", "")))
    convertido = _digitos_no_texto(" ".join((t or "").split()))
    achados |= set(x.replace(",", "") for x in re.findall(r"\d[\d,]*", convertido))
    for w in re.findall(r"[a-z]+", (t or "").lower().replace("-", " ")):
        if w in _UNIT_W: achados.add(str(_UNIT_W[w]))
        elif w in _TENS_W: achados.add(str(_TENS_W[w]))
    return achados

def _anc(vals, t):
    nums = _nums_do_texto(t)
    def ok(v):
        try: v = float(v)
        except Exception: return False
        cand = {str(int(v))}
        for esc in (1000, 1000000, 1000000000):  # 90 K ancorado por 'ninety thousand' (90000)
            if v * esc <= 1e12: cand.add(str(int(v * esc)))
        return bool(cand & nums)
    return any(ok(v) for v in vals)

def _num_dado(d, t, keys=("number", "value", "percentage")):
    """valor numérico vindo dos DADOS do LLM, aceito só se ancorado no texto falado."""
    for k in keys:
        v = _s(d, k)
        if v is None: continue
        try: v = float(v)
        except Exception: continue
        if _anc([v], t): return v
    return None

_SUFFIX_OK = {"%", "k", "m", "b", "x", "kg", "g", "mm", "cm", "km", "mi", "lbs", "oz", "yrs", "hrs", "min", "$"}

def _graf_uni(d, t, im):   # numero_unico (number_end cobre RANGE '3-8%': headline = teto falado)
    v = _num_dado(d, t, ("number", "value", "number_end"))
    if v is not None and v < 4 and not _s(d, "percentage"):
        return None  # R-92: 1-3 solto é ordinal/idiomático ('number one enemy'), não headline
    if v is not None and not _s(d, "title", "label"):
        d = {**d, "title": corte(_s(d, "description", "unit") or "", 44)}  # LLM manda description às vezes
    suf = str(_s(d, "unit", "suffix") or "")[:6]
    if suf.lower() not in _SUFFIX_OK:
        # R-92 (QA tenis: '25 genera'): unidade longa NÃO é suffix — vira parte do título
        if suf and suf.lower() not in ("", "%"):
            tt0 = str(_s(d, "title", "label") or "")
            unit_full = str(_s(d, "unit", "suffix") or "")
            if unit_full.lower() not in tt0.lower():
                d = {**d, "title": corte(f"{unit_full.capitalize()} — {tt0}", 44) if tt0 else corte(unit_full.capitalize(), 44)}
        suf = ""
    if v is None:
        g = _num(t)
        if not g: return None
        v, suf = g
    else:
        if v >= 1e9: v, suf = round(v / 1e9, 1), "B"
        elif v >= 1e6: v, suf = round(v / 1e6, 1), "M"
        elif v >= 1e4: v, suf = round(v / 1e3), "K"
    tt = corte(_s(d, "title", "label") or "", 44)
    return {"title": tt, "labels": [], "values": [float(v)], "suffix": suf} if tt else None

def _graf_pct(d, t, im):   # percentual
    # R-92 (QA tenis 23/07): '%' na tela EXIGE percentual FALADO — 'number one enemy'
    # virava Donut '1%'. Sem 'percent'/'%' no áudio, não existe gráfico de porcentagem.
    tl = (t or "").lower()
    if "percent" not in tl and "%" not in tl: return None
    v = _num_dado(d, t, ("percentage", "number", "value"))
    if v is None:
        g = _num(t)
        if g and g[1] == "%": v = g[0]
    if v is None or not (1 < v <= 100): return None  # 0-1% nunca é o dado central de um beat
    tt = corte(_s(d, "title", "label") or "", 44)
    return {"title": tt, "labels": [], "values": [float(v)], "suffix": "%"} if tt else None

def _fnum(v):
    """'15%' -> 15.0, '$80,000' -> 80000.0 — float('15%') explodia e RECUSAVA dados perfeitos
    (QA seniors 22/07: o VersusBars do 15%-vs-34% morreu por isso e o dado virou ticker de rodapé)."""
    try:
        return float(str(v).replace("%", "").replace("$", "").replace(",", "").strip())
    except Exception:
        return None

def _graf_cmp(d, t, im):   # comparacao (2 lados)
    labs = [str(x)[:22] for x in (_s(d, "labels") or [])]
    vals_raw = _s(d, "values") or []
    if len(labs) < 2 or len(vals_raw) < 2: return None
    vals = [_fnum(vals_raw[0]), _fnum(vals_raw[1])]
    if None in vals: return None
    if not _anc(vals, t): return None
    suf = str(_s(d, "suffix", "unit") or "")[:6]
    if not suf and any("%" in str(v) for v in vals_raw[:2]): suf = "%"
    return {"title": corte(_s(d, "title") or "", 44), "labels": labs[:2], "values": vals, "suffix": suf}

def _graf_serie(d, t, im): # tendencia/serie/distribuicao/ranking (3+ pontos)
    labs = [str(x)[:18] for x in (_s(d, "labels") or [])]
    vals = [_fnum(v) for v in (_s(d, "values") or [])]
    if len(labs) < 3 or len(vals) < 3 or len(labs) != len(vals) or None in vals: return None
    if not _anc(vals, t): return None
    return {"title": corte(_s(d, "title") or "", 44), "labels": labs[:6], "values": vals[:6],
            "suffix": str(_s(d, "suffix", "unit") or "")[:6]}

for _c, _fn, _p, _mx, _md in [
        ("Graf01_CounterGlow", _graf_uni, 1.1, 2, 2.5), ("Graf02_Odometer", _graf_uni, 1.0, 2, 2.5),
        ("Graf03_DonutPercent", _graf_pct, 1.0, 2, 2.5), ("Graf04_GaugeMeter", _graf_pct, 1.0, 2, 2.5),
        ("Graf05_VersusBars", _graf_cmp, 1.1, 2, 3.0), ("Graf06_VersusTug", _graf_cmp, 0.9, 2, 3.0),
        ("Graf07_TimelineRise", _graf_serie, 1.0, 2, 3.5), ("Graf08_LinePulse", _graf_serie, 0.9, 2, 3.5),
        ("Graf09_RankList", _graf_serie, 0.9, 2, 3.5), ("Graf10_BigStatCard", _graf_uni, 1.0, 2, 2.5),
        ("Graf11_PieSlices", _graf_serie, 0.8, 1, 3.5), ("Graf12_MultiBars", _graf_serie, 0.9, 2, 3.5),
        ("Graf13_DualLine", _graf_serie, 0.8, 1, 3.5), ("Graf14_OvlCounterPunch", _graf_uni, 1.0, 2, 2.0),
        ("Graf15_OvlStatCorner", _graf_uni, 1.0, 3, 2.0), ("Graf16_OvlProgressBar", _graf_pct, 1.0, 2, 2.0)]:
    _reg2(_c, "chart", peso=_p, max_uso=_mx, build=_fn, min_dur=_md)

# ---- VIDRUSH PACK (decupagem 14 vídeos, 24/07): dado ANOTA o footage corrente ----
def _ovl_spec(d, t, im):
    """Ovl11 '17 • LBS DRAG': número + UNIDADE-PALAVRA (a que não cabe em suffix)."""
    v = _fnum(_s(d, "number", "value") or (_s(d, "values") or [None])[0])
    unit = str(_s(d, "unit", "suffix", "label") or "").strip()
    if v is None or len(unit) < 2 or not _anc([v], t): return None
    return {"text": f"{v:g}", "kicker": corte(unit, 18)}

def _ovl_giant(d, t, im):
    """Ovl12: número dramático GIGANTE sobre o footage (nunca ano — R-27 cuida)."""
    v = _fnum(_s(d, "number", "value") or (_s(d, "values") or [None])[0])
    if v is None or v < 10 or 1300 <= v <= 2099 or not _anc([v], t): return None
    txt = f"{v / 1000:g}K" if v >= 10000 else f"{v:g}"
    return {"text": txt, "kicker": corte(frase_de_tela(t, max_p=8) or "", 60)}

def _ovl_price(d, t, im):
    """Ovl13: preço estilizado — exige cifra/preço FALADO no texto."""
    tl = (t or "").lower()
    if "$" not in str(d or {}) and "dollar" not in tl and "price" not in tl and "cost" not in tl:
        return None
    v = _fnum(_s(d, "price", "cost", "number", "value") or (_s(d, "values") or [None])[0])
    if v is None or v <= 0 or not _anc([v], t): return None
    return {"text": f"${v:,.0f}", "kicker": corte(_s(d, "label", "title") or "", 24)}

def _ovl_verdict(d, t, im):
    """Ovl14: nome do item + veredito de 1 linha (anúncio forma B do VidRush)."""
    nome = str(_s(d, "name", "title") or "").strip()
    ver = str(_s(d, "verdict", "subtitle", "description") or "").strip() or (frase_de_tela(t, max_p=10) or "")
    if len(nome) < 3: return None
    return {"text": corte(nome, 34), "kicker": corte(ver, 60)}

def _lst_check(d, t, im):
    """Lst01/02: critérios/razões — exige lista REAL de 2-5 itens nos dados."""
    pts = [corte(x, 46) for x in (_s(d, "points", "bullets", "items") or []) if str(x).strip()]
    tt = corte(_s(d, "title", "label") or "", 34)
    if len(pts) < 2 or not tt: return None
    return {"title": tt, "items": pts[:5]}

for _c, _fn, _p, _mx, _md in [
        ("Ovl11_SpecBadge", _ovl_spec, 1.5, 3, 1.5), ("Ovl12_GiantStat", _ovl_giant, 1.2, 2, 2.0),
        ("Ovl13_PriceTag", _ovl_price, 1.3, 2, 1.5), ("Ovl14_PillVerdict", _ovl_verdict, 0.9, 2, 2.2),
        ("Lst01_NoteChecklist", _lst_check, 1.0, 2, 3.5), ("Lst02_SidePanelList", _lst_check, 1.0, 2, 3.5)]:
    _reg2(_c, "chart", peso=_p, max_uso=_mx, build=_fn, min_dur=_md)

# G1 (VidRush): dado único NUNCA vira card escuro quando há footage — troca card<->overlay
SWAP_TO_OVL = {"Graf01_CounterGlow": "Graf14_OvlCounterPunch", "Graf02_Odometer": "Graf14_OvlCounterPunch",
               "Graf03_DonutPercent": "Graf16_OvlProgressBar", "Graf10_BigStatCard": "Graf15_OvlStatCorner"}

# ---- IMAGEM (slots reais do executor; Img13 VETADA pelo Piter — fora do sorteio) ----
def _mk_img(n):
    def _b(d, t, im):
        if len(im) < n: return None
        caps = [str(x)[:26] for x in (_s(d, "captions", "labels") or [])][:n]
        return {"images": list(im[:n]), "captions": caps if len(caps) == n else [],
                "title": str(_s(d, "title", "text") or "")[:40], "kicker": str(_s(d, "kicker") or "")[:24]}
    return _b

def _img14_build(d, t, im):
    """TitleCutout: a PALAVRA é a arte — sem título real (4-14 chars), recusa (QA: default HILUX vazou)."""
    p = _mk_img(1)(d, t, im)
    if not p: return None
    tt = str(_s(d, "title", "word", "name") or "").strip()
    if not (4 <= len(tt) <= 14): return None
    p["title"] = humanizar(tt)[:14]
    return p

for _c, _n, _p, _mx in [
        ("Img01_KenBurnsCine", 1, 1.2, 3), ("Img02_PolaroidDrop", 1, 1.0, 2),
        ("Img03_FramedGridPan", 1, 1.1, 2), ("Img04_SplitSlide", 2, 1.0, 2),
        ("Img05_BeforeAfterWipe", 2, 0.9, 2), ("Img06_StackReveal", 3, 0.9, 2),
        ("Img07_FilmstripSlide", 4, 0.8, 1), ("Img08_GridPop", 4, 0.8, 1),
        ("Img09_PaperTear", 1, 0.9, 2), ("Img10_ParallaxDepth", 1, 1.0, 2),
        ("Img11_VintageAngled", 1, 1.0, 2), ("Img12_SpotlightDetail", 1, 0.9, 2),
        ("Img15_CorkBoardPin", 2, 0.8, 1),
        ("Img16_ZoomOutReveal", 1, 0.9, 2), ("Img17_DiagonalDuo", 2, 0.9, 2),
        ("Img18_PhotoStatBadge", 1, 0.9, 2), ("Img19_NewsClipping", 1, 0.8, 1),
        ("Img20_TripleCarousel", 3, 0.9, 2)]:
    _reg2(_c, "imagem", needs_imgs=_n, peso=_p, max_uso=_mx, build=_mk_img(_n),
          min_dur=(2.5 if _n == 1 else 3.0 if _n == 2 else 3.5 if _n == 3 else 4.0))
_reg2("Img14_TitleCutout", "imagem", needs_imgs=1, peso=0.8, max_uso=1, build=_img14_build, min_dur=2.5)

# ---- VIDRUSH PACK imagem (24/07): anúncio com texto sobre produto, callouts, collage ----
def _img21_build(d, t, im):
    if not im: return None
    tt = corte(_s(d, "title", "name") or "", 40)
    if not tt: return None
    return {"images": [im[0]], "title": tt, "kicker": corte(_s(d, "kicker", "subtitle", "tag") or "", 30)}

def _img22_build(d, t, im):
    labs = [corte(x, 22) for x in (_s(d, "callouts", "labels", "points") or []) if str(x).strip()]
    if not im or len(labs) < 2: return None
    return {"images": [im[0]], "captions": labs[:4], "title": corte(_s(d, "title") or "", 30)}

def _img23_build(d, t, im):
    if len(im) < 2: return None
    labs = [corte(x, 18) for x in (_s(d, "labels", "captions") or []) if str(x).strip()]
    return {"images": list(im[:3]), "captions": labs[:3], "title": corte(_s(d, "title") or "", 40)}

_reg2("Img21_ProductAnnounce", "imagem", needs_imgs=1, peso=1.0, max_uso=5, build=_img21_build, min_dur=2.5)
_reg2("Img22_ProductCallouts", "imagem", needs_imgs=1, peso=1.0, max_uso=2, build=_img22_build, min_dur=3.0)
_reg2("Img23_CollageCompare", "imagem", needs_imgs=2, peso=1.0, max_uso=2, build=_img23_build, min_dur=3.0)

# ---- MAPAS (novos, geo-validados; Map09-12 satélite ficam FORA até o executor
#      ganhar o passo de prefetch ESRI via satelite_fetch.py) ----
# GAZETTEER local — coords REAIS pré-cadastradas (nunca inventadas pelo LLM).
# Lugar fora daqui e sem lat/lon explícito => builder recusa (regra de ferro).
GAZ = {
    "milwaukee": (43.04, -87.91, "United States"), "york": (39.96, -76.73, "United States"),
    "kansas city": (39.10, -94.58, "United States"), "tomahawk": (45.47, -89.73, "United States"),
    "washington": (38.90, -77.04, "United States"), "washington d.c.": (38.90, -77.04, "United States"),
    "detroit": (42.33, -83.05, "United States"), "chicago": (41.88, -87.63, "United States"),
    "new york": (40.71, -74.01, "United States"), "los angeles": (34.05, -118.24, "United States"),
    "sturgis": (44.41, -103.51, "United States"), "daytona": (29.21, -81.02, "United States"),
    "tokyo": (35.68, 139.69, "Japan"), "osaka": (34.69, 135.50, "Japan"), "hamamatsu": (34.71, 137.73, "Japan"),
    "london": (51.51, -0.13, "United Kingdom"), "berlin": (52.52, 13.40, "Germany"),
    "paris": (48.86, 2.35, "France"), "rome": (41.90, 12.50, "Italy"), "moscow": (55.76, 37.62, "Russia"),
    "sao paulo": (-23.55, -46.63, "Brazil"), "sydney": (-33.87, 151.21, "Australia"),
    "toronto": (43.65, -79.38, "Canada"), "mexico city": (19.43, -99.13, "Mexico"),
}

def _gaz(nome):
    n = str(nome or "").split(",")[0].strip().lower()
    return GAZ.get(n)

def _paises_de(d):
    def nome(x):
        return str(x.get("country") or x.get("name") or "") if isinstance(x, dict) else str(x)
    cs = [nome(x).strip() for x in (_s(d, "regions", "countries") or []) if nome(x).strip() and _pais_ok(nome(x))]
    if not cs:  # deriva o país de um lugar conhecido do gazetteer ("Milwaukee, Wisconsin" -> United States)
        g = _gaz(_s(d, "location", "city", "place"))
        if g: cs = [g[2]]
    return cs

def _pontos_de(d):
    pts = []
    for k in ("start_location", "end_location", "location"):
        v = _s(d, k)
        if isinstance(v, dict) and v.get("lat") is not None and v.get("lon") is not None and v.get("name"):
            pts.append({"nome": str(v["name"]).split(",")[0][:20], "lat": float(v["lat"]), "lon": float(v["lon"])})
        elif isinstance(v, str) and v.strip():
            g = _gaz(v)
            if g: pts.append({"nome": v.split(",")[0].strip()[:20], "lat": g[0], "lon": g[1]})
    if not pts and _s(d, "lat") is not None and _s(d, "lon") is not None:
        pts.append({"nome": str(_s(d, "location", "name") or "")[:20], "lat": float(_s(d, "lat")), "lon": float(_s(d, "lon"))})
    return pts

def _map_pais1(d, t, im):
    cs = _paises_de(d)
    if not cs: return None
    return {"paises": cs[:1], "titulo": cs[0][:30], "kicker": str(_s(d, "kicker", "label", "text") or "")[:26]}

def _map_multi(d, t, im):
    cs = _paises_de(d)
    if len(cs) < 2: return None
    vals = _s(d, "values") or []
    dig = (t or "").replace(",", "").replace(".", "")
    limp = []
    for x in vals[:len(cs)]:
        s = str(x.get("label", "")) if isinstance(x, dict) else str(x)
        dd = "".join(c for c in s if c.isdigit())
        limp.append(s[:16] if (not dd or dd in dig) else "")
    return {"paises": cs[:5], "valores": limp if any(limp) else [], "kicker": str(_s(d, "kicker", "title") or "")[:26]}

def _map_rota(d, t, im):
    pts = _pontos_de(d)
    if len(pts) < 2: return None
    return {"pontos": pts[:2], "kicker": str(_s(d, "kicker", "title") or "")[:26]}

def _map_pin(d, t, im):
    pts = _pontos_de(d)
    if not pts: return None
    return {"pontos": pts[:1], "titulo": str(_s(d, "subtitle", "year", "text") or "")[:26],
            "kicker": str(_s(d, "kicker", "country") or "")[:26]}

def _map_stat(d, t, im):
    cs = _paises_de(d)
    g = _num(t)
    if not cs or not g: return None
    suf = g[1] if g[1] else ""
    return {"paises": cs[:1], "valores": [f"{g[0]:g}{suf}"], "titulo": str(_s(d, "title", "label") or "")[:36],
            "kicker": str(_s(d, "kicker") or "")[:26]}

def _map_radar(d, t, im):
    pts = _pontos_de(d)
    tl = (t or "").lower()
    if not pts or not any(w in tl for w in ("war", "military", "battle", "test", "zone", "combat", "operation")):
        return None
    return {"pontos": pts[:1], "kicker": str(_s(d, "kicker", "title") or "")[:26]}

def _map_cine(d, t, im):
    if not im: return None
    cs, pts = _paises_de(d), _pontos_de(d)
    if not cs and not pts: return None
    p = {"images": list(im[:1]), "titulo": str(_s(d, "subtitle", "text", "title") or "")[:30],
         "kicker": str(_s(d, "kicker") or "")[:22]}
    if cs: p["paises"] = cs[:1]
    if pts: p["pontos"] = pts[:1]
    return p

for _c, _fn, _ni, _p, _mx, _md in [
        ("Map01_CountryFocus", _map_pais1, 0, 1.1, 2, 3.0), ("Map02_MultiHighlight", _map_multi, 0, 1.0, 2, 3.5),
        ("Map03_RouteArc", _map_rota, 0, 1.1, 2, 3.5), ("Map04_PinCallout", _map_pin, 0, 1.0, 2, 3.0),
        ("Map05_RegionZoom", _map_pais1, 0, 0.9, 1, 3.0), ("Map07_RadarSweep", _map_radar, 0, 0.6, 1, 3.0),
        ("Map08_StatMap", _map_stat, 0, 1.0, 2, 3.0), ("Map13_CineLocation", _map_cine, 1, 1.0, 1, 3.5)]:
    _reg2(_c, "mapa", needs_imgs=_ni, peso=_p, max_uso=_mx, build=_fn, min_dur=_md)

# ---- SOCIAL (só formatos "editoriais"; identidade SEMPRE fictícia; peso baixo) ----
STYLE = {}  # setado por montador/executor via set_style(style_card) — contexto do NICHO

def set_style(sc):
    global STYLE
    STYLE = sc or {}

def _soc_news(d, t, im):
    tt = str(_s(d, "title", "quote", "text") or "")[:64].strip()
    if len(tt) < 8 or not im: return None
    # R-32/QA tenis 23/07: kicker era "The Motor Chronicle" HARDCODED (nicho Harley vazando
    # em vídeo de tênis) e o corpo cortava no meio ("...isn'TA"). Kicker = style_card;
    # corpo SÓ com sentença FECHADA — jornal com frase pendurada não existe.
    corpo = frase_de_tela(t or "", max_p=30, min_p=6) or ""
    if not corpo.rstrip().endswith((".", "!", "?")): return None
    kicker = str(STYLE.get("jornal_ficticio") or "The Daily Chronicle")
    return {"kicker": kicker, "titulo": humanizar(tt).upper()[:64], "texto": corpo[:230],
            "grifo": str(_s(d, "highlight") or "")[:40], "imagem": im[0]}

_reg2("Soc04_Newspaper", "texto_full", needs_imgs=1, peso=0.5, max_uso=1, build=_soc_news, min_dur=4.0)

# R-21 [F1]: max_dur — overlay leve <=4s, card de texto full <=5s (footage não tem teto)
for _r in R:
    if _r["comp"].startswith("Ovl"): _r["max_dur"] = 4.0
    if _r["comp"].startswith("Texto"): _r["max_dur"] = 5.0

# min_dur dos estruturais antigos que continuam vivos
for _r in R:
    if _r["comp"] == "QuoteCard": _r["min_dur"] = 3.0
    if _r["comp"] == "ChapterTitle": _r["min_dur"] = 3.0


# ---------------- PICKER (random com ID + quota, esquema do Piter) ----------------
NATUREZAS = sorted({r["natureza"] for r in R})

def escolher(natureza, dados, texto, seed, quotas, max_uso=2, imgs=None, last_use=None, beat_i=None, cooldown=8, dur=None):
    """Sorteia um ID dentro da natureza; builder valida; inválido/quota cheia -> próximo.
    Retorna (comp, props, needs_imgs) ou None. `imgs`=paths já resolvidos (fase executor).
    `last_use`/`beat_i`/`cooldown`: mesma variação não repete a menos de N beats (vizinhança).
    `dur`: duração do beat em s — card pesado NÃO entra em beat curto (QA Piter 21/07: Chapter de <1s)."""
    pool = [r for r in R if r["natureza"] == natureza and r["comp"] not in DEPRECATED]
    rng = random.Random(seed)
    pool = sorted(pool, key=lambda r: (quotas.get(r["comp"], 0), -r["peso"] * rng.random()))
    for r in pool:
        teto = r.get("max_uso") or max_uso
        if quotas.get(r["comp"], 0) >= teto:
            continue
        if dur is not None and dur < r.get("min_dur", 0):
            continue
        if dur is not None and r.get("max_dur") and dur > r["max_dur"]:
            continue  # R-21: overlay/card parado em beat longo cansa (max_dur)
        if last_use is not None and beat_i is not None:
            lu = last_use.get(r["comp"])
            if lu is not None and (beat_i - lu) < cooldown:
                continue
        if r["needs_imgs"] > 0 and imgs is None:
            # fase de PLANO: aceita sem imgs (executor resolve depois); valida só os dados
            props = r["build"](dados, texto, ["__IMG__"] * r["needs_imgs"])
            if props is not None:
                quotas[r["comp"]] = quotas.get(r["comp"], 0) + 1
                if last_use is not None and beat_i is not None:
                    last_use[r["comp"]] = beat_i
                return r["comp"], None, r["needs_imgs"]
            continue
        props = r["build"](dados, texto, imgs or [])
        if props is not None:
            quotas[r["comp"]] = quotas.get(r["comp"], 0) + 1
            if last_use is not None and beat_i is not None:
                last_use[r["comp"]] = beat_i
            return r["comp"], props, r["needs_imgs"]
    return None

def rebuild(comp, dados, texto, imgs):
    """Reconstrói props de um comp específico (fase executor, com imgs reais)."""
    for r in R:
        if r["comp"] == comp:
            return r["build"](dados, texto, imgs or [])
    return None
