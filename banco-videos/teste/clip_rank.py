# -*- coding: utf-8 -*-
"""RANQUEADOR CLIP local (02/08) — peneira semântica ANTES do Vision pago.

Problema que resolve: hoje TODO candidato vai pro Gemini/Luna. Em 31/07 isso parou a
produção (8 chaves em 429 + Luna sem crédito) e limita o pool a ~12 por chamada. O
CLIP roda na 5070 Ti, custa 0 e julga "esta imagem casa com este texto" em lote —
então dá pra avaliar 50 candidatos, mandar só os 5 melhores pro Vision arbitrar.

NÃO substitui o Vision: CLIP mede SEMELHANÇA SEMÂNTICA, não enxerga defeito
(talking-head, criança, marca d'água, texto queimado). A divisão é:
  CLIP   -> "isto tem a ver com o assunto?"  (barato, em lote, local)
  Vision -> "isto pode ir ao ar?"            (caro, só nos finalistas)

Roda em venv PRÓPRIO (F:/Canal Dark/clip_venv) — o venv do PROD (chatterbox-test)
NÃO é tocado: trocar o torch de lá derruba a narração.

Uso (por subprocess, como o thumb_picker do automator):
  clip_venv/Scripts/python.exe clip_rank.py --texto "..." --imgs a.jpg b.jpg ...
Devolve JSON: [{"path": ..., "score": 0-100}, ...] ordenado do melhor pro pior.
"""
import argparse
import json
import sys

MODELO = ("ViT-B-32", "laion2b_s34b_b79k")  # leve (~600MB) e rápido; sobe em ~3s
_CACHE = {}


def _carregar():
    if "m" not in _CACHE:
        import open_clip
        import torch
        dev = "cuda" if torch.cuda.is_available() else "cpu"
        modelo, _, preproc = open_clip.create_model_and_transforms(
            MODELO[0], pretrained=MODELO[1])
        modelo = modelo.to(dev).eval()
        _CACHE.update(m=modelo, p=preproc, t=open_clip.get_tokenizer(MODELO[0]), d=dev)
    return _CACHE


def ranquear(texto, imagens):
    """[(path, score 0-100)] ordenado. Score = similaridade cosseno reescalada."""
    import torch
    from PIL import Image
    c = _carregar()
    tensores, validos = [], []
    for p in imagens:
        try:
            tensores.append(c["p"](Image.open(p).convert("RGB")))
            validos.append(p)
        except Exception:
            continue          # arquivo corrompido não derruba o lote inteiro
    if not tensores:
        return []
    with torch.no_grad():
        lote = torch.stack(tensores).to(c["d"])
        f_img = c["m"].encode_image(lote)
        f_txt = c["m"].encode_text(c["t"]([texto]).to(c["d"]))
        f_img /= f_img.norm(dim=-1, keepdim=True)
        f_txt /= f_txt.norm(dim=-1, keepdim=True)
        sims = (f_img @ f_txt.T).squeeze(-1).cpu().tolist()
    # calibrado no job real de cobras (02/08): o cosseno ficou entre 0.057 (prancha
    # anatômica de perna humana) e 0.263 (gravura de Bothrops jararaca). A faixa
    # 0.15-0.35 que eu tinha chutado zerava 15 das 19 imagens e perdia a ordenação.
    return sorted(({"path": p, "score": round(max(0.0, min(1.0, (s - 0.05) / 0.23)) * 100, 1)}
                   for p, s in zip(validos, sims)),
                  key=lambda x: -x["score"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--texto", required=True)
    ap.add_argument("--imgs", nargs="+", required=True)
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(ranquear(a.texto, a.imgs), ensure_ascii=False))


if __name__ == "__main__":
    main()
