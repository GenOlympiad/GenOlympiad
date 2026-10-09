"""The judge VLM: answers one question about one image."""
from __future__ import annotations

import base64
import hashlib
import io
import json
import logging
import os
import re
import threading
import time

from .question_lint import guarded_reader

log = logging.getLogger(__name__)

JUDGES = ("gemini", "openrouter")
GEMINI_MODEL = "gemini-2.5-flash"
OPENROUTER_MODEL = "google/gemini-2.5-flash"
DEFAULT_THINKING_BUDGET = 0
DEFAULT_MAX_TOKENS = 2048
_ESCALATE = 4
_TRIES = 3

_state = {"judge": None, "model": GEMINI_MODEL, "key": None, "cache_dir": None, "fresh": "",
          "rejected": None}
_reads = 0
_reads_lock = threading.Lock()
_mode = threading.local()


def _count_read():
    global _reads
    with _reads_lock:
        _reads += 1


def paid_vlm_reads() -> int:
    """Paid judge VLM reads made by this process; answers from the cache are not counted."""
    with _reads_lock:
        return _reads


def current_read_mode():
    """(thinking budget, max output tokens) for reads on this thread."""
    t = getattr(_mode, "thinking", None)
    m = getattr(_mode, "max_tokens", None)
    return (DEFAULT_THINKING_BUDGET if t is None else int(t),
            DEFAULT_MAX_TOKENS if m is None else int(m))


class read_mode:
    """Context manager: run the enclosed reads on this thread with another generation config."""

    def __init__(self, thinking=None, max_tokens=None):
        self.thinking, self.max_tokens = thinking, max_tokens
        self.prev = None

    def __enter__(self):
        self.prev = (getattr(_mode, "thinking", None), getattr(_mode, "max_tokens", None))
        if self.thinking is not None:
            _mode.thinking = int(self.thinking)
        if self.max_tokens is not None:
            _mode.max_tokens = int(self.max_tokens)
        return self

    def __exit__(self, *exc):
        _mode.thinking, _mode.max_tokens = self.prev
        return False


def cache_key(model, raw, question, fresh=""):
    """Content address of one answer: model, PNG bytes of the image, question."""
    base = model + "|" + hashlib.sha256(raw).hexdigest() + "|" + question
    if fresh:
        base += "|fresh=" + fresh
    return hashlib.sha256(base.encode("utf-8")).hexdigest()[:32]


def extract(answer):
    """Reduce a raw answer to the bare token the operators expect."""
    if answer is None:
        return None
    s = str(answer).strip()
    if s.startswith("{") or s.startswith("["):
        try:
            d = json.loads(s)
        except ValueError:
            d = None
        if isinstance(d, dict):
            for k in ("answer", "label", "value", "color", "number", "text"):
                if k in d and d[k] is not None:
                    s = str(d[k]).strip()
                    break
            else:
                if d:
                    s = str(next(iter(d.values()))).strip()
    s = s.strip().strip(".,;:!\"'` )(").strip()
    m = re.match(r"(?i)^(yes|no|true|false)\b", s)
    if m:
        return m.group(1).lower()
    return s


def _png_bytes(image):
    from PIL import Image
    pil = image if hasattr(image, "convert") else Image.open(image).convert("RGB")
    buf = io.BytesIO()
    pil.save(buf, format="PNG")
    return buf.getvalue()


def _cache_path(route, key):
    d = os.path.join(_state["cache_dir"], route)
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, key + ".json")


def _cached(path):
    if not os.path.exists(path):
        return None
    with io.open(path, encoding="utf-8") as fh:
        return json.load(fh)["answer"]


class KeyRejected(RuntimeError):
    """The judge VLM service refused the API key."""


def _rejection(r):
    """The service's own first line when a reply refuses the key, else None."""
    text = r.text or ""
    refused = r.status_code in (401, 403) or (
        r.status_code == 400 and ("API_KEY_INVALID" in text or "API key not valid" in text))
    if not refused:
        return None
    try:
        err = r.json().get("error")
        message = err.get("message") if isinstance(err, dict) else err
    except (ValueError, AttributeError):
        message = None
    lines = str(message or text or "status %d" % r.status_code).strip().splitlines()
    return (lines[0] if lines else "status %d" % r.status_code)[:200]


def rejected():
    """The service's message if it refused the key during this process, else None."""
    return _state["rejected"]


def check_key(judge, *, model=None, key=None):
    """Raise KeyRejected when the judge VLM service refuses the key; one free request."""
    import requests
    if judge == "gemini":
        r = requests.get("https://generativelanguage.googleapis.com/v1beta/models/%s"
                         % (model or GEMINI_MODEL), headers={"x-goog-api-key": key or ""},
                         timeout=60)
    elif judge == "openrouter":
        r = requests.get("https://openrouter.ai/api/v1/key",
                         headers={"Authorization": "Bearer " + (key or "")}, timeout=60)
    else:
        return
    why = _rejection(r)
    if why:
        raise KeyRejected(why)


def _ask_http(post, parse, body, bigger):
    """One request with retries on 429/5xx and one larger retry for a cut-off answer."""
    import requests
    last = None
    for attempt in range(_TRIES):
        if _state["rejected"]:
            return None, None, None
        try:
            r = post(body)
            why = _rejection(r)
            if why:
                _state["rejected"] = why
                log.warning("the judge VLM rejected the key: %s", why)
                return None, None, None
            if r.status_code in (429, 500, 502, 503):
                time.sleep(5 * (attempt + 1))
                continue
            r.raise_for_status()
            ans, finish, cut = parse(r.json())
            used = None
            if cut or not ans:
                r2 = post(bigger(body))
                r2.raise_for_status()
                a2, f2, _ = parse(r2.json())
                if a2:
                    ans, finish, used = a2, f2, "escalated"
            return ans, finish, used
        except requests.RequestException as e:
            last = e
            log.warning("judge VLM request failed (try %d): %s", attempt + 1, e)
            time.sleep(2 * (attempt + 1))
    if last is not None:
        log.warning("judge VLM gave no answer after %d tries", _TRIES)
    return None, None, None


@guarded_reader
def gemini_answer(image, question):
    """Answer through the Gemini API (temperature 0)."""
    import requests
    raw = _png_bytes(image)
    model = _state["model"] or GEMINI_MODEL
    path = _cache_path("gemini_direct", cache_key(model, raw, question, _state["fresh"]))
    hit = _cached(path)
    if hit is not None:
        return extract(hit)
    if not _state["key"]:
        log.warning("no GEMINI_API_KEY: the judge VLM cannot answer")
        return None
    think, maxtok = current_read_mode()
    url = "https://generativelanguage.googleapis.com/v1beta/models/%s:generateContent" % model
    body = {"contents": [{"parts": [
        {"inline_data": {"mime_type": "image/png", "data": base64.b64encode(raw).decode()}},
        {"text": question}]}],
        "generationConfig": {"temperature": 0, "maxOutputTokens": int(maxtok),
                             "thinkingConfig": {"thinkingBudget": int(think)}}}

    def post(b):
        return requests.post(url, headers={"x-goog-api-key": _state["key"]}, json=b,
                             timeout=90 if b is body else 180)

    def parse(js):
        c = (js.get("candidates") or [{}])[0]
        parts = ((c.get("content") or {}).get("parts")) or []
        text = "".join(p.get("text", "") for p in parts if isinstance(p, dict)).strip()
        finish = c.get("finishReason")
        return text, finish, str(finish).upper() == "MAX_TOKENS"

    def bigger(b):
        b2 = dict(b)
        b2["generationConfig"] = dict(b["generationConfig"], maxOutputTokens=int(maxtok) * _ESCALATE)
        return b2

    ans, finish, used = _ask_http(post, parse, body, bigger)
    if not ans:
        return None
    with io.open(path, "w", encoding="utf-8") as fh:
        json.dump({"answer": ans, "finish": finish, "thinking": int(think),
                   "max_tokens": int(maxtok) * (_ESCALATE if used else 1),
                   "escalated": bool(used)}, fh, ensure_ascii=False)
    _count_read()
    return extract(ans)


@guarded_reader
def openrouter_answer(image, question):
    """Answer through OpenRouter (temperature 0)."""
    import requests
    raw = _png_bytes(image)
    model = _state["model"] or OPENROUTER_MODEL
    path = _cache_path("openrouter_direct", cache_key(model, raw, question, _state["fresh"]))
    hit = _cached(path)
    if hit is not None:
        return extract(hit)
    if not _state["key"]:
        log.warning("no OPENROUTER_API_KEY: the judge VLM cannot answer")
        return None
    _think, maxtok = current_read_mode()
    uri = "data:image/png;base64," + base64.b64encode(raw).decode()
    body = {"model": model, "temperature": 0, "max_tokens": int(maxtok),
            "messages": [{"role": "user", "content": [
                {"type": "image_url", "image_url": {"url": uri}},
                {"type": "text", "text": question}]}]}

    def post(b):
        return requests.post("https://openrouter.ai/api/v1/chat/completions",
                             headers={"Authorization": "Bearer " + _state["key"]}, json=b,
                             timeout=90 if b is body else 180)

    def parse(js):
        c = (js.get("choices") or [{}])[0]
        text = ((c.get("message") or {}).get("content") or "").strip()
        finish = c.get("finish_reason")
        return text, finish, str(finish) == "length"

    def bigger(b):
        return dict(b, max_tokens=int(maxtok) * _ESCALATE)

    ans, finish, used = _ask_http(post, parse, body, bigger)
    if not ans:
        return None
    with io.open(path, "w", encoding="utf-8") as fh:
        json.dump({"answer": ans, "finish": finish, "max_tokens": int(maxtok),
                   "escalated": bool(used)}, fh, ensure_ascii=False)
    _count_read()
    return extract(ans)


_BACKENDS = {"gemini": gemini_answer, "openrouter": openrouter_answer}
_KEY_VARS = {"gemini": ("GEMINI_API_KEY", "GOOGLE_API_KEY"), "openrouter": ("OPENROUTER_API_KEY",)}
_DEFAULT_MODEL = {"gemini": GEMINI_MODEL, "openrouter": OPENROUTER_MODEL}


def register_judge(name, fn):
    """Add a judge: fn(image, question) returns an answer; its calls are not counted as paid."""
    _BACKENDS[name] = guarded_reader(lambda image, question: extract(fn(image, question)))
    _KEY_VARS[name] = ()
    _DEFAULT_MODEL[name] = name


def judge_names():
    """Names of every judge this process knows."""
    return tuple(_BACKENDS)


def configure(judge, *, model=None, key=None, cache_dir):
    """Choose the judge VLM for this process and install it in the operators."""
    if judge not in _BACKENDS:
        raise ValueError("unknown judge %r; choose one of %s" % (judge, ", ".join(JUDGES)))
    if key is None:
        key = next((os.environ[v] for v in _KEY_VARS[judge] if os.environ.get(v)), None)
    _state.update(judge=judge, model=model or _DEFAULT_MODEL[judge], key=key,
                  cache_dir=os.path.abspath(cache_dir))
    from . import ops
    ops.set_vlm_reader(_BACKENDS[judge])


def current():
    """The installed answer function."""
    return _BACKENDS[_state["judge"] or "gemini"]


def _set_repeat_tag(tag):
    _state["fresh"] = str(tag or "")
