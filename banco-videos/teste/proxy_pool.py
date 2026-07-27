# -*- coding: utf-8 -*-
"""POOL DE PROXIES p/ operações YouTube (yt-dlp) — round-robin thread-safe + bench de morto.
Arquivo: banco-videos/teste/proxies.txt (GITIGNORED — nunca versionar), 1 proxy por linha:
    http://user:pass@ip:porta
    socks5://ip:porta
    ip:porta                (assume http://)
Linhas vazias/# são ignoradas. Sem arquivo/vazio => sem proxy (conexão direta).

Uso:  from proxy_pool import proximo, reportar
      p = proximo()            # url do proxy ou None
      reportar(p, ok=False)    # 3 falhas seguidas => banco por 10 min
"""
import threading
import time
from pathlib import Path

_ARQ = Path(__file__).parent / "proxies.txt"
_LOCK = threading.Lock()
_POOL = []          # [{url, falhas, bench_ate}]
_IDX = [0]
_BENCH_S = 600      # 10 min no banco
_MAX_FALHAS = 3


def _carregar():
    if not _ARQ.exists():
        return
    for ln in _ARQ.read_text(encoding="utf-8").splitlines():
        ln = ln.split("#")[0].strip()   # corta comentário inline (e linha-comentário vira vazia)
        if not ln:
            continue
        if "://" not in ln:
            ln = "http://" + ln
        _POOL.append({"url": ln, "falhas": 0, "bench_ate": 0.0})


_carregar()


def total():
    return len(_POOL)


def proximo():
    """Próximo proxy vivo (round-robin). None = sem pool (direto)."""
    with _LOCK:
        if not _POOL:
            return None
        agora = time.time()
        for _ in range(len(_POOL)):
            p = _POOL[_IDX[0] % len(_POOL)]
            _IDX[0] += 1
            if p["bench_ate"] <= agora:
                return p["url"]
        # todos no banco -> usa o que sai primeiro (melhor que travar)
        p = min(_POOL, key=lambda x: x["bench_ate"])
        return p["url"]


def reportar(url, ok):
    """Feedback do uso: sucesso zera falhas; 3 falhas seguidas = banco 10 min."""
    if not url:
        return
    with _LOCK:
        for p in _POOL:
            if p["url"] == url:
                if ok:
                    p["falhas"] = 0
                else:
                    p["falhas"] += 1
                    if p["falhas"] >= _MAX_FALHAS:
                        p["bench_ate"] = time.time() + _BENCH_S
                        p["falhas"] = 0
                return
