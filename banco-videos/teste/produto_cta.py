"""Pass ADITIVO (só nichos com preset.produto_cta.ativo): acha no words.json o trecho em que o PRODUTO
é falado (o soft-sell, ~8min) e emite a janela `produto_cta` no timeline. O BrollTest renderiza o
componente ProductCTA (mockup do eBook + QR + oferta) como takeover de tela nesse trecho.
"""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
TESTE = Path(r"F:/Canal Dark/Aplicativo de Edição/banco-videos/teste")
TIMELINE = TESTE / "timeline.json"
WORDS = TESTE / "words.json"


def main():
    from preset import carregar
    tl = json.load(open(TIMELINE, encoding="utf-8"))
    cfg = (carregar(tl).get("produto_cta") or {})
    if not cfg.get("ativo"):
        print("produto_cta: nicho sem CTA de produto -> skip")
        return
    if not WORDS.exists():
        print("produto_cta: sem words.json -> skip")
        return
    words = json.load(open(WORDS, encoding="utf-8"))

    toks = [str(w.get("word", "")).lower().strip(".,!?;:'\"-()[]") for w in words]

    def match_all(frases, after=0.0):
        """Todas as (start, end) onde alguma FRASE (sequência de palavras) casa no áudio, após 'after'."""
        out = []
        for fr in frases:
            seq = fr.split(); n = len(seq)
            for i in range(len(words) - n + 1):
                st = words[i].get("start", 0)
                if st >= after and toks[i:i + n] == seq:
                    out.append((st, words[i + n - 1].get("end", st)))
        return sorted(out)

    # ÂNCORA robusta: o NOME do produto (FRASE) só existe no bloco do soft-sell. Casar palavras soltas
    # ("motion"/"healing"/"cycles") pegava menções genéricas lá no começo -> CTA visual caía aos ~3min
    # (dessincronizado do pitch falado, que está por volta dos 4-5min). Frase evita isso.
    nome = match_all(["healing in motion", "special guide", "somatic cycles"])
    if not nome:
        # ⚠️ CTA do eBook = CORE BUSINESS (Piter 2026-07-02): se o preset exige produto e a narração
        # NÃO fala o produto, o vídeo está QUEBRADO -> falha RUIDOSA (aborta o job), nunca skip silencioso.
        print("produto_cta: ERRO FATAL — preset exige CTA de produto mas o NOME do produto não está na narração!")
        sys.exit(1)
    ini_anchor = nome[0][0]
    urg = match_all(["limited time", "pinned comment", "first comment", "first pinned", "pinned"], after=ini_anchor + 3)
    fim_anchor = urg[-1][1] if urg else (ini_anchor + 30)
    ini = max(0.0, round(ini_anchor - 1.5, 2))
    fim = round(fim_anchor + 2.0, 2)
    fim = min(fim, ini + 70)          # teto 70s (cobre todo o pitch do produto sem truncar)
    fim = max(fim, ini + 14)          # piso 14s (ler + escanear o QR)

    tl["produto_cta"] = {
        "inicio": ini, "fim": fim,
        "img": cfg.get("img"), "qr": cfg.get("qr"),
        "headline": cfg.get("headline"), "offer": cfg.get("offer"),
    }
    json.dump(tl, open(TIMELINE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"produto_cta: takeover {ini:.1f}-{fim:.1f}s ({fim-ini:.0f}s) | img={cfg.get('img')} qr={cfg.get('qr')}")


if __name__ == "__main__":
    main()
