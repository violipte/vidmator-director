"""Helper compartilhado de Gemini para os passes do Director.
API (8 chaves, rotação + retry em 429/503) PRIMÁRIA -> CLI (OAuth) FALLBACK.
Resiliente: hoje (2026-06-19) o CLI quebrou (auth/gaxios) e a API estava ok; antes foi o contrário.
"""
import itertools
import json
import re
import urllib.error
import urllib.request
from pathlib import Path

CREDS = Path(r"F:/Canal Dark/Aplicativo de Edição/video-automator/credentials.json")
TESTE = Path(r"F:/Canal Dark/Aplicativo de Edição/banco-videos/teste")
def _keys(prov):
    try:
        return [c["api_key"] for c in json.load(open(CREDS, encoding="utf-8"))
                if c.get("provedor") == prov and c.get("api_key")]
    except Exception:
        return []


_GKEYS = _keys("gemini")
_OKEY = (_keys("gpt") or [None])[0]      # fallback quando o Gemini free esgota (pago, mas centavos/vídeo)
_CKEY = (_keys("claude") or [None])[0]   # fallback secundário
_GPT_MODEL = "gpt-5"
_CLAUDE_MODEL = "claude-sonnet-4-6"
_ROT = itertools.count()   # rotação de chaves (thread-safe via GIL)


# Conteúdo dos nichos (true-crime, morte/memento mori, história sombria) dispara FALSO-POSITIVO
# no filtro do Gemini -> resposta sem 'parts' -> passes quebram silenciosamente. BLOCK_NONE corrige.
_SAFETY = [{"category": c, "threshold": "BLOCK_NONE"} for c in (
    "HARM_CATEGORY_HARASSMENT", "HARM_CATEGORY_HATE_SPEECH",
    "HARM_CATEGORY_SEXUALLY_EXPLICIT", "HARM_CATEGORY_DANGEROUS_CONTENT",
)]


def _api(prompt, timeout=120):
    if not _GKEYS:
        return None
    body = json.dumps({"contents": [{"parts": [{"text": prompt}]}], "safetySettings": _SAFETY}).encode()
    n = len(_GKEYS)
    for _ in range(n):
        k = _GKEYS[next(_ROT) % n]
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={k}"
            req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read())["candidates"][0]["content"]["parts"][0]["text"]
        except urllib.error.HTTPError as e:
            if e.code in (429, 503):
                continue
            return None
        except Exception:
            continue
    return None


_USAGE_LOG = TESTE / "_gpt_usage.jsonl"   # 1 linha por chamada GPT: tokens p/ calcular custo


def _openai(prompt, timeout=120):
    """Fallback GPT (reasoning model: usa max_completion_tokens + reasoning_effort low p/ extração simples).
    Registra os tokens em _gpt_usage.jsonl pra contabilizar o custo depois."""
    if not _OKEY:
        return None
    body = json.dumps({
        "model": _GPT_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_completion_tokens": 8000,
        "reasoning_effort": "low",
    }).encode()
    try:
        req = urllib.request.Request("https://api.openai.com/v1/chat/completions", data=body,
                                     headers={"Authorization": "Bearer " + _OKEY, "Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = json.loads(r.read())
        u = data.get("usage", {}) or {}
        try:
            with open(_USAGE_LOG, "a", encoding="utf-8") as f:
                f.write(json.dumps({"model": _GPT_MODEL, "in": u.get("prompt_tokens", 0),
                                    "out": u.get("completion_tokens", 0)}) + "\n")
        except Exception:
            pass
        return data["choices"][0]["message"]["content"]
    except Exception:
        return None


def _claude(prompt, timeout=120):
    """Fallback Claude (Anthropic Messages API)."""
    if not _CKEY:
        return None
    body = json.dumps({
        "model": _CLAUDE_MODEL,
        "max_tokens": 4000,
        "messages": [{"role": "user", "content": prompt}],
    }).encode()
    try:
        req = urllib.request.Request("https://api.anthropic.com/v1/messages", data=body,
                                     headers={"x-api-key": _CKEY, "anthropic-version": "2023-06-01", "Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())["content"][0]["text"]
    except Exception:
        return None


def gemini_text(prompt, timeout=120):
    """Texto via cascata de LLM: Gemini free (8 chaves) -> GPT-5 -> Claude. SEMPRE retorna str.
    CLI REMOVIDO: o Google descontinuou o Code Assist free p/ individuais (UNSUPPORTED_CLIENT, 2026-06-20).
    Quando o Gemini free esgota, cai no GPT/Claude (pago, mas ~centavos por vídeo)."""
    return _api(prompt, timeout) or _openai(prompt, timeout) or _claude(prompt, timeout) or ""


def gemini_arr(prompt, timeout=120, retries=5):
    """Pede um JSON ARRAY ao Gemini. O modelo às vezes injeta um token lixo (ex.: 'タップ' no lugar de
    '},') que quebra o json.loads. Estratégia: por tentativa, tenta o JSON CRU e uma versão REPARADA
    ('}<lixo>{' -> '},{'); até `retries` tentativas. Retorna list ou None."""
    for _ in range(retries):
        out = gemini_text(prompt, timeout)
        if not out:
            continue
        a, b = out.find("["), out.rfind("]")
        if a < 0 or b <= a:
            continue
        chunk = out[a:b + 1]
        reparado = re.sub(r'\}\s*[^\s,\[\]\{\}"]+\s*\{', '},{', chunk)   # conserta '} lixo {' entre objetos
        for txt in (chunk, reparado):
            try:
                arr = json.loads(txt)
                if isinstance(arr, list):
                    return arr
            except Exception:
                pass
        # último recurso: extrai cada objeto {...} sozinho (ignora qualquer lixo entre eles)
        objs = []
        for o in re.findall(r'\{[^{}]*\}', chunk):
            try:
                objs.append(json.loads(o))
            except Exception:
                pass
        if objs:
            return objs
    return None
