"""STORY ENGINE — Analisador de CENAS narrativas (canais de história: romance/emocional).
Lê roteiro_en.txt e segmenta a NARRATIVA em cenas dramáticas via LLM:
  {trecho, lugar, tempo, personagens[], emocao, intensidade, objetos[]}
+ CASTING: mapeia personagens da história -> biblioteca (woman_1, man_1, ...).
Se words.json existir, ancora cada cena em timestamps reais (inicio/fim).
Saída: cenas_historia.json (consumido por ambiencia/foley/personagens/trilha/ritmo).

Uso: python analisar_cenas.py [roteiro.txt]   (default: roteiro_en.txt)
"""
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
TESTE = Path(r"F:/Canal Dark/Aplicativo de Edição/banco-videos/teste")
WORDS = TESTE / "words.json"
SAIDA = TESTE / "cenas_historia.json"
from gemini_api import gemini_text

BIBLIOTECA = ["woman_1", "man_1"]   # elenco disponível (cresce com a biblioteca)

# vocabulário CONTROLADO — casa com os catálogos dos bancos (ambiências/trilha)
LUGARES = ("church wedding office bedroom kitchen cafe restaurant street city_night_rain rain_window "
           "car_rain hospital hospital_room library old_house park beach train train_station airport "
           "rooftop countryside harbor storm forest night_outdoor generic_interior generic_exterior")
EMOCOES = "tension tenderness grief joy nostalgia anger hope relief loneliness suspense"


def analisar(rot):
    p = (f"You are a STORY ANALYST for an emotional-stories video channel. Read this narration script and "
         f"segment it into DRAMATIC SCENES (a scene changes when place, time or dramatic situation changes; "
         f"typically 8-20 scenes). For EACH scene return:\n"
         f"- frase_inicio: the EXACT first 6-10 words of the scene as written in the script (verbatim, for anchoring)\n"
         f"- lugar: ONE from this controlled list: {LUGARES}\n"
         f"- tempo: day|night|flashback|present\n"
         f"- personagens: array of story character names present IN the scene (narrator counts as a character; "
         f"use consistent names across scenes)\n"
         f"- emocao: ONE from: {EMOCOES}\n"
         f"- intensidade: 0.0-1.0 (dramatic intensity)\n"
         f"- objetos: array of 0-3 anchor objects physically featured (e.g. letter, bracelet, ring, envelope, photo)\n"
         f"Also return 'casting': map each recurring character name to one of {BIBLIOTECA} by gender/role "
         f"(narrator male -> man_1 etc.; secondary characters that appear in only 1 scene can map to null).\n"
         f"Return ONLY a JSON object {{\"cenas\": [...], \"casting\": {{...}}}}.\n\nSCRIPT:\n{rot}")
    out = gemini_text(p, 150) or ""
    a, b = out.find("{"), out.rfind("}")
    d = json.loads(out[a:b + 1])
    # o LLM às vezes "traduz" as chaves PT (personajes/characters, intensidad/intensity...) — normaliza
    ALIAS = {"personajes": "personagens", "characters": "personagens", "personagem": "personagens",
             "intensidad": "intensidade", "intensity": "intensidade",
             "objetos_ancla": "objetos", "objects": "objetos", "lugar_": "lugar", "place": "lugar",
             "emotion": "emocao", "emocion": "emocao", "time": "tempo", "scene_start": "frase_inicio"}
    for c in d.get("cenas", d.get("scenes", [])):
        for k in list(c.keys()):
            can = ALIAS.get(k)
            if can and can not in c:
                c[can] = c.pop(k)
    if "cenas" not in d and "scenes" in d:
        d["cenas"] = d.pop("scenes")
    return d


def ancorar_tempos(cenas, rot):
    """Ancora cada cena em timestamps via words.json (mesma técnica do produto_cta: casar frase)."""
    if not WORDS.exists():
        return False
    words = json.load(open(WORDS, encoding="utf-8"))
    toks = [str(w.get("word", "")).lower().strip(".,!?;:'\"-()") for w in words]

    def acha(frase, de=0):
        seq = [t for t in re.sub(r"[^a-z0-9 ]", " ", frase.lower()).split() if t][:6]
        n = len(seq)
        if n < 3:
            return None
        for i in range(de, len(toks) - n + 1):
            if toks[i:i + n] == seq:
                return i
        return None

    ultimo = 0
    for c in cenas:
        i = acha(c.get("frase_inicio", ""), ultimo)
        if i is not None:
            c["inicio"] = round(words[i]["start"], 2)
            ultimo = i
    # fim = início da próxima; última vai até o fim do áudio
    for j, c in enumerate(cenas):
        if "inicio" not in c:
            continue
        prox = next((x["inicio"] for x in cenas[j + 1:] if "inicio" in x), None)
        c["fim"] = prox if prox else round(words[-1].get("end", words[-1]["start"]), 2)
    return True


def main():
    # GATE: só nichos narrativos (preset.story_engine) — TTM/EST/etc. pulam sem gastar LLM.
    # Com arg explícito (teste manual) roda sempre.
    if len(sys.argv) < 2:
        try:
            from preset import carregar
            tl_path = TESTE / "timeline.json"
            tl = json.load(open(tl_path, encoding="utf-8")) if tl_path.exists() else {}
            if not carregar(tl).get("story_engine"):
                print("analisar_cenas: nicho sem story_engine -> skip"); return
        except Exception:
            pass
    rot_path = Path(sys.argv[1]) if len(sys.argv) > 1 else TESTE / "roteiro_en.txt"
    if not rot_path.is_absolute():
        rot_path = TESTE / rot_path
    rot = rot_path.read_text(encoding="utf-8")
    print(f"=== Analisador de cenas: {rot_path.name} ({len(rot.split())} palavras) ===")
    d = analisar(rot)
    cenas, casting = d.get("cenas", []), d.get("casting", {})
    com_tempo = ancorar_tempos(cenas, rot)
    json.dump(d, open(SAIDA, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"{len(cenas)} cenas | casting: {casting} | timestamps: {'SIM' if com_tempo else 'não (sem words.json)'}")
    for i, c in enumerate(cenas):
        t = f"{c.get('inicio','?')}s" if "inicio" in c else "-"
        print(f"  {i+1:2}. [{t:>7}] {c.get('lugar','?'):16} {c.get('tempo','?'):9} {c.get('emocao','?'):11} "
              f"int={c.get('intensidade','?'):<4} pers={','.join(c.get('personagens',[]))[:28]:30} obj={','.join(c.get('objetos',[]))[:24]}")
    print(f"-> {SAIDA}")


if __name__ == "__main__":
    main()
