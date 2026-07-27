"""Prepara assets do BrollTest pro Remotion: copia clips usados + narração + escreve o JSON do render.
Por padrão -> public/test/ + timeline_render.json (1 vídeo por vez).
Com env JOB=<id> -> public/jobs/<id>/ + timeline_<id>.json (input ISOLADO p/ render em paralelo:
o render do job N lê o snapshot dele enquanto os passes do job N+1 reescrevem o slot compartilhado).
"""
import json
import os
import shutil
import sys
from pathlib import Path

from PIL import Image

sys.stdout.reconfigure(encoding="utf-8")


def _copy_asset(src, dest):
    """Copia asset. Se for IMAGEM, RE-ENCODA pra RGB/RGBA limpo (tira ICC/CMYK/webp que o
    Chrome do Remotion não decodifica -> EncodingError). Vídeo (.mp4) = cópia bruta."""
    src, dest = Path(src), Path(dest)
    ext = dest.suffix.lower()
    if ext in (".jpg", ".jpeg", ".png", ".webp"):
        try:
            im = Image.open(src)
            im.load()
            if ext == ".png":
                im.convert("RGBA").save(dest, "PNG")            # preserva alpha (retratos rembg)
            elif ext == ".webp":
                im.convert("RGB").save(dest, "WEBP", quality=92)
            else:
                im.convert("RGB").save(dest, "JPEG", quality=92)  # descarta ICC/CMYK
            return
        except Exception as e:
            print(f"  re-encode falhou ({src.name}): {str(e)[:40]} -> cópia bruta")
    shutil.copy2(src, dest)

REMOTION = Path(r"F:/Canal Dark/Aplicativo de Edição/remotion")
TIMELINE_SRC = Path(r"F:/Canal Dark/Aplicativo de Edição/banco-videos/teste/timeline.json")

JOB = os.environ.get("JOB", "").strip()
SUB = f"jobs/{JOB}" if JOB else "test"        # subpasta em public/ + prefixo dos rels
PUBLIC_TEST = REMOTION / "public" / SUB
CLIPS_OUT = PUBLIC_TEST / "clips"
RENDER_JSON = REMOTION / (f"timeline_{JOB}.json" if JOB else "timeline_render.json")

MUSICA_SRC = Path(r"F:/Canal Dark/Music/Impending Doom.mp3")  # mistério/tensão (era cósmico)
CLICK_SRC = Path(r"F:/Canal Dark/Aplicativo de Edição/banco-videos/teste/click.mp3")
GLITCH_SRC = Path(r"F:/Canal Dark/Music/glitch-sfx-312910.mp3")  # SFX de glitch pronto
TYPING_SRC = Path(r"F:/Canal Dark/Music/typing-18347.mp3")  # SFX digitação (ASMR, typewriter)
PAPER_SRC = Path(r"F:/Canal Dark/Music/turning-paper-turning-page-290380.mp3")  # SFX virar página
WHOOSH_SRC = Path(r"F:/Canal Dark/Music/whoosh_punch.mp3")  # whoosh JÁ cortado p/ o swoosh alto (0.55-1.85s do original)
RISER_SRC = Path(r"F:/Canal Dark/Music/riser_punch.mp3")  # riser JÁ cortado p/ o clímax (5.2-7.4s do original)
CTA_DING_SRC = Path(r"F:/Canal Dark/Music/cta_ding.mp3")  # ding do sino no CTA

tl = json.load(open(TIMELINE_SRC, encoding="utf-8"))
CLIPS_OUT.mkdir(parents=True, exist_ok=True)

# Narração
narr_src = Path(tl["narracao"])
shutil.copy2(narr_src, PUBLIC_TEST / "narracao.mp3")
print(f"narração -> {SUB}/narracao.mp3")

# Música de fundo
musica_rel = None
if MUSICA_SRC.exists():
    shutil.copy2(MUSICA_SRC, PUBLIC_TEST / "musica.mp3")
    musica_rel = f"{SUB}/musica.mp3"
    print(f"música -> {MUSICA_SRC.name}")
else:
    print(f"AVISO: música não encontrada: {MUSICA_SRC}")

# Click SFX das transições (legado — não usado mais)
click_rel = None
if CLICK_SRC.exists():
    shutil.copy2(CLICK_SRC, PUBLIC_TEST / "click.mp3")
    click_rel = f"{SUB}/click.mp3"

# Glitch/static SFX (só em mudança de tópico)
glitch_rel = None
if GLITCH_SRC.exists():
    shutil.copy2(GLITCH_SRC, PUBLIC_TEST / "glitch.mp3")
    glitch_rel = f"{SUB}/glitch.mp3"
    print("glitch -> glitch.mp3")

# SFX ASMR (vol baixo): digitação (typewriter) + virar página (cards/imagens)
sfx_typing_rel = None
if TYPING_SRC.exists():
    shutil.copy2(TYPING_SRC, PUBLIC_TEST / "sfx_typing.mp3")
    sfx_typing_rel = f"{SUB}/sfx_typing.mp3"
sfx_paper_rel = None
if PAPER_SRC.exists():
    shutil.copy2(PAPER_SRC, PUBLIC_TEST / "sfx_paper.mp3")
    sfx_paper_rel = f"{SUB}/sfx_paper.mp3"
sfx_whoosh_rel = None
if WHOOSH_SRC.exists():
    shutil.copy2(WHOOSH_SRC, PUBLIC_TEST / "sfx_whoosh.mp3")
    sfx_whoosh_rel = f"{SUB}/sfx_whoosh.mp3"
    print("whoosh -> sfx_whoosh.mp3")
sfx_riser_rel = None
if RISER_SRC.exists():
    shutil.copy2(RISER_SRC, PUBLIC_TEST / "sfx_riser.mp3")
    sfx_riser_rel = f"{SUB}/sfx_riser.mp3"
    print("riser -> sfx_riser.mp3")
cta_ding_rel = None
if CTA_DING_SRC.exists():
    shutil.copy2(CTA_DING_SRC, PUBLIC_TEST / "cta_ding.mp3")
    cta_ding_rel = f"{SUB}/cta_ding.mp3"
    print("cta_ding -> cta_ding.mp3")

# Preset do nicho (SFX por papel, etc.) — lê presets.json pelo tl["nicho"]
try:
    _presets = json.load(open(r"F:/Canal Dark/Aplicativo de Edição/banco-videos/teste/presets.json", encoding="utf-8"))
    _nicho = str(os.environ.get("NICHO") or tl.get("nicho") or "default").strip().lower()
    _preset = {**_presets.get("default", {}), **_presets.get(_nicho, {})}
except Exception:
    _preset = {}
sfx_roles = _preset.get("sfx")
print(f"preset nicho={tl.get('nicho','default')} | sfx_roles={'sim' if sfx_roles else 'nao'}")

# Legendas HIPNÓTICAS do hook (primeiros hook_ate s) — palavras do whisper
hook_ate = float(_preset.get("hook_ate", 0) or 0)
legendas_hook = []
if hook_ate > 0:
    try:
        _wjson = json.load(open(r"F:/Canal Dark/Aplicativo de Edição/banco-videos/teste/words.json", encoding="utf-8"))
        legendas_hook = [{"word": w["word"], "start": round(w.get("start", 0), 2), "end": round(w.get("end", w.get("start", 0) + 0.3), 2)}
                         for w in _wjson if w.get("start", 0) < hook_ate]
        print(f"legendas hook: {len(legendas_hook)} palavras (< {hook_ate}s)")
    except Exception as e:
        print(f"legendas hook falhou: {str(e)[:50]}")

# CTAs de YouTube: usa os do timeline (se um pass os definir) OU default (pós-intro + meio)
_dur = tl["duracao"]
ctas = tl.get("ctas") or [
    {"inicio": round(min(56.0, _dur * 0.05), 1), "dur": 5.5, "headline": "ENJOYING THE VIDEO?"},
    {"inicio": round(_dur * 0.58, 1), "dur": 5.5, "headline": "FIND THIS USEFUL?"},
]

# Clips usados (únicos)
render = {
    "duracao": tl["duracao"],
    "narracao_rel": f"{SUB}/narracao.mp3",
    "musica_rel": musica_rel,
    "musica_envelope": tl.get("musica_envelope"),
    "click_rel": click_rel,
    "glitch_rel": glitch_rel,
    "fonte_tema": tl.get("fonte_tema"),
    "sfx_typing_rel": sfx_typing_rel,
    "sfx_paper_rel": sfx_paper_rel,
    "sfx_whoosh_rel": sfx_whoosh_rel,
    "sfx_riser_rel": sfx_riser_rel,
    "cta_ding_rel": cta_ding_rel,
    "ctas": ctas,
    "sfx_roles": sfx_roles,
    "glitch_topico": _preset.get("glitch_topico", True),   # false (documentário) -> sem TVStatic+som na fronteira de tópico
    "produto_cta": tl.get("produto_cta"),                  # janela do CTA de produto (eBook+QR takeover), do produto_cta.py
    "legendas_hook": legendas_hook,
    "hook_ate": hook_ate,
    "datas": tl.get("datas") or [],
    "cenas": [],
}
copiados = set()
cid2rel = {}   # clip_id -> rel (p/ mapear os extras de presentacao split/grid)
for c in tl["cenas"]:
    cid = c["clip_id"]
    src = Path(c["clip_path"])
    ext = src.suffix.lower() if src.suffix.lower() in (".mp4", ".jpg", ".jpeg", ".png", ".webp") else ".mp4"
    dest = CLIPS_OUT / f"{cid}{ext}"
    if cid not in copiados:
        _copy_asset(src, dest)   # re-encoda imagens (tira ICC/CMYK); vídeo = cópia bruta
        copiados.add(cid)
    cid2rel[cid] = f"{SUB}/clips/{cid}{ext}"
    render["cenas"].append({
        "presentacao": c.get("presentacao"),
        "inicio": c["inicio"],
        "fim": c["fim"],
        "clip_rel": f"{SUB}/clips/{cid}{ext}",
        "clip_dur": c["clip_dur"],
        "media_tipo": c.get("media_tipo", "video"),
        "transicao": c.get("transicao", "crossfade"),
        "texto_impacto": c.get("texto_impacto"),
        "palavra_chave": c.get("palavra_chave"),
        "texto_pos": c.get("texto_pos"),
        "infografico": c.get("infografico"),
        "sfx": c.get("sfx", False),
        "aparece_em": c.get("aparece_em"),
        "fade": c.get("fade", 14),
        "entrada_texto": c.get("entrada_texto"),
        "intro": c.get("intro", False),
        "ilustracao": c.get("ilustracao"),
        "fonte": c.get("fonte"),
        "arquivo_modo": c.get("arquivo_modo"),
        "era": c.get("era"),
        "mood": c.get("mood"),
        "mascote": c.get("mascote"),
    })

# mascote: copia os PNGs do banco pra public/<SUB>/mascote/ e re-aponta o rel
_masc_cfg = (_preset.get("mascote") or {})
_masc_banco = Path(_masc_cfg.get("banco") or r"F:/Canal Dark/Aplicativo de Edição/banco-videos/mascote_galo")
_masc_out = PUBLIC_TEST / "mascote"
_masc_copiados = set()
for rc in render["cenas"]:
    m = rc.get("mascote")
    if not m:
        continue
    fname = m.get("img", "")
    src = _masc_banco / fname
    if fname not in _masc_copiados:
        if src.exists():
            _masc_out.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, _masc_out / fname)
            _masc_copiados.add(fname)
        else:
            rc["mascote"] = None
            continue
    m["img_rel"] = f"{SUB}/mascote/{fname}"
if _masc_copiados:
    print(f"mascote: {_masc_copiados and len(_masc_copiados)} poses copiadas -> {SUB}/mascote/")

# ---- STORY ENGINE: ambiências (loops), foleys (one-shots) e personagens (recortes laterais) ----
_amb_banco = Path((_preset.get("ambiencia") or {}).get("banco") or r"D:/Meu Drive/canal_dark_ambiencias")
render["ambiencias"] = []
for a in (tl.get("ambiencias") or []):
    src = _amb_banco / a["file"]
    if src.exists():
        (PUBLIC_TEST / "amb").mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, PUBLIC_TEST / "amb" / a["file"])
        render["ambiencias"].append({**a, "file_rel": f"{SUB}/amb/{a['file']}"})
if render["ambiencias"]:
    print(f"ambiencias: {len(render['ambiencias'])} janelas")

_fol_banco = Path((_preset.get("foley") or {}).get("banco") or r"D:/Meu Drive/canal_dark_foley")
render["foleys"] = []
for f in (tl.get("foleys") or []):
    src = _fol_banco / f["file"]
    if src.exists():
        (PUBLIC_TEST / "foley").mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, PUBLIC_TEST / "foley" / f["file"])
        render["foleys"].append({**f, "file_rel": f"{SUB}/foley/{f['file']}"})
if render["foleys"]:
    print(f"foleys: {len(render['foleys'])} one-shots")

_pers_banco = Path((_preset.get("personagens") or {}).get("banco") or r"F:/Canal Dark/Aplicativo de Edição/banco-videos/personagens_historia")
_pers_copiados = set()
for i, c in enumerate(tl.get("cenas", [])):
    pres = c.get("personagens")
    if not pres or i >= len(render["cenas"]):
        continue
    out = []
    for p in pres:
        src = _pers_banco / p["img"]
        if not src.exists():
            continue
        if p["img"] not in _pers_copiados:
            (PUBLIC_TEST / "pers").mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, PUBLIC_TEST / "pers" / p["img"])
            _pers_copiados.add(p["img"])
        out.append({"img_rel": f"{SUB}/pers/{p['img']}", "lado": p.get("lado", "right")})
    if out:
        render["cenas"][i]["personagens"] = out
if _pers_copiados:
    print(f"personagens: {len(_pers_copiados)} recortes copiados")

print(f"clips copiados: {len(copiados)}")

# presentacao: mapeia os extras (clip_id -> rel copiado) p/ split/grid
for rc in render["cenas"]:
    p = rc.get("presentacao")
    if p and p.get("extras"):
        p["extras"] = [cid2rel[x] for x in p["extras"] if x in cid2rel] or None

# Mapas: copia imagens dos popups -> public/<SUB>/mapas/ e passa o array
mapas_render = []
mapas = tl.get("mapas") or []
if mapas:
    MAPAS_OUT = PUBLIC_TEST / "mapas"
    MAPAS_OUT.mkdir(parents=True, exist_ok=True)
    SAT_OUT = PUBLIC_TEST / "sat"
    n_sat = 0
    for i, m in enumerate(mapas):
        img_rel = None
        src = m.get("imagem_path")
        if src and Path(src).exists():
            dest = MAPAS_OUT / f"mapa_{i}.jpg"
            _copy_asset(src, dest)
            img_rel = f"{SUB}/mapas/mapa_{i}.jpg"
        # satélite: copia a pilha de tiles -> public/<SUB>/sat/ e reescreve rels
        niveis_rel = None
        if m.get("tipo") == "satelite" and m.get("niveis"):
            SAT_OUT.mkdir(parents=True, exist_ok=True)
            niveis_rel = []
            for j, nv in enumerate(m["niveis"]):
                p = Path(nv["path"])
                if p.exists():
                    d = SAT_OUT / f"sat_{i}_{j}.jpg"
                    _copy_asset(p, d)
                    niveis_rel.append({"rel": f"{SUB}/sat/sat_{i}_{j}.jpg", "half": nv["half"]})
            if len(niveis_rel) >= 2:
                n_sat += 1
            else:
                niveis_rel = None
        mapas_render.append({
            "inicio": m["inicio"],
            "dur": m.get("dur", 5.5),
            "pais": m["pais"],
            "coord": m["coord"],
            "legenda": m["legenda"],
            "imagem_rel": img_rel,
            "tipo": "satelite" if niveis_rel else "estilizado",
            "niveis": niveis_rel,
        })
    print(f"mapas: {len(mapas_render)} ({n_sat} satélite, resto estilizado)")
render["mapas"] = mapas_render

# Pessoas: copia retratos recortados -> public/<SUB>/people/ e passa o array
pessoas_render = []
pessoas = tl.get("pessoas") or []
if pessoas:
    PEOPLE_OUT = PUBLIC_TEST / "people"
    PEOPLE_OUT.mkdir(parents=True, exist_ok=True)
    for i, p in enumerate(pessoas):
        img_rel = None
        src = p.get("imagem_path")
        if src and Path(src).exists():
            ext = Path(src).suffix or ".png"
            dest = PEOPLE_OUT / f"pessoa_{i}{ext}"
            _copy_asset(src, dest)
            img_rel = f"{SUB}/people/pessoa_{i}{ext}"
        pessoas_render.append({
            "inicio": p["inicio"], "dur": p.get("dur", 3.6), "nome": p["nome"],
            "subtitulo": p.get("subtitulo"), "imagem_rel": img_rel, "fundo": p.get("fundo", "escuro"),
        })
    print(f"pessoas: {len(pessoas_render)} (retratos -> {SUB}/people/)")
render["pessoas"] = pessoas_render

# Imagens PD do caso: copia -> public/<SUB>/imagens/ e passa o array
imagens_render = []
imagens = tl.get("imagens") or []
if imagens:
    IMG_OUT = PUBLIC_TEST / "imagens"
    IMG_OUT.mkdir(parents=True, exist_ok=True)
    for i, im in enumerate(imagens):
        rels = []
        for j, src in enumerate(im.get("imagens_path", [])):
            if src and Path(src).exists():
                ext = Path(src).suffix or ".jpg"
                dest = IMG_OUT / f"img_{i}_{j}{ext}"
                _copy_asset(src, dest)
                rels.append(f"{SUB}/imagens/img_{i}_{j}{ext}")
        if rels:
            imagens_render.append({"inicio": im["inicio"], "dur": im.get("dur", 4.0),
                                   "estilo": im.get("estilo", "photo"), "imagens_rel": rels,
                                   "legenda": im.get("legenda")})
    print(f"imagens: {len(imagens_render)} (-> {SUB}/imagens/)")
render["imagens"] = imagens_render

# Estética de ÉPOCA: se o roteiro cita datas antigas, trata o vídeo todo como vintage P&B
import re as _re
_anos = [int(_m.group()) for _d in (tl.get("datas") or [])
         for _m in [_re.search(r"(18|19|20)\d\d", _d.get("texto", ""))] if _m]
render["periodo"] = "vintage" if (_preset.get("vintage") or (_anos and min(_anos) <= 1970)) else None
print(f"periodo: {render['periodo']} (datas min={min(_anos) if _anos else '-'})")

# Tópicos + TRILHA em segmentos (corte seco por tópico)
render["topicos"] = tl.get("topicos") or []
segs_render = []
segs = tl.get("musica_segmentos") or []
if segs:
    TRILHAS_OUT = PUBLIC_TEST / "trilhas"
    TRILHAS_OUT.mkdir(parents=True, exist_ok=True)
    copiadas = {}
    for s in segs:
        src = Path(s["track_path"])
        if not src.exists():
            print(f"  trilha não encontrada: {src.name}")
            continue
        if src.name not in copiadas:
            shutil.copy2(src, TRILHAS_OUT / src.name)
            copiadas[src.name] = f"{SUB}/trilhas/{src.name}"
        segs_render.append({"inicio": s["inicio"], "fim": s["fim"], "vol": s.get("vol", 0.16),
                            "fade": s.get("fade", 0.4), "track_rel": copiadas[src.name]})
    print(f"trilha: {len(segs_render)} segmentos ({len(copiadas)} faixas -> {SUB}/trilhas/)")
render["musica_segmentos"] = segs_render

RENDER_JSON.write_text(json.dumps(render, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"render json -> {RENDER_JSON.name} (SUB={SUB})")
print(f"duração: {render['duracao']}s | cenas: {len(render['cenas'])}")
