"""Fetch live reference data over HTTP and pick values out of it."""
from __future__ import annotations
import re
import time
from ._base import register, resolve
import logging

log = logging.getLogger(__name__)

_CACHE: dict = {}
_FAILED: set = set()

_RETRIES = 3
_BACKOFF = (0.5, 1.0, 2.0)


def fetch_failed() -> bool:
    """True iff any fetch.url persistently failed (after retries) this process."""
    return bool(_FAILED)


@register("fetch.url")
def op_fetch_url(ctx, step):
    url = resolve(ctx, step["url"])
    if url in _CACHE:
        val = _CACHE[url]
        if val is None:
            _FAILED.add(url)
            if isinstance(ctx, dict):
                ctx["_fetch_failed"] = True
        return val

    val = None
    last_exc = None
    for attempt in range(_RETRIES):
        try:
            import requests
            r = requests.get(url, timeout=30, headers={"User-Agent": "GenOlympiad/1.0"})
            r.raise_for_status()
            try:
                val = r.json()
            except ValueError:
                log.debug("error ignored in op_fetch_url", exc_info=True)
                val = r.text
            last_exc = None
            break
        except Exception as e:
            log.debug("error ignored in op_fetch_url", exc_info=True)
            last_exc = e
            if attempt < _RETRIES - 1:
                time.sleep(_BACKOFF[min(attempt, len(_BACKOFF) - 1)])

    if val is None and last_exc is not None:
        _FAILED.add(url)
        if isinstance(ctx, dict):
            ctx["_fetch_failed"] = True
    _CACHE[url] = val
    return val


def _jsonpath(obj, path):
    if not path or path in ("$", "$."):
        return obj
    toks = re.findall(r"\.([A-Za-z_][\w]*)|\[(\d+)\]|\[\*\]", path.lstrip("$"))
    cur = obj
    for name, idx, in_star in [(t[0], t[1], "[*]" in m) for t, m in zip(toks, re.findall(r"\.[A-Za-z_][\w]*|\[\d+\]|\[\*\]", path.lstrip("$")))]:
        if cur is None:
            return None
        if in_star or (name == "" and idx == ""):
            rest_start = path.index("[*]") + 3
            return [_jsonpath(x, "$" + path[rest_start:]) for x in (cur if isinstance(cur, list) else [])]
        if name:
            cur = cur.get(name) if isinstance(cur, dict) else None
        elif idx != "":
            i = int(idx)
            cur = cur[i] if isinstance(cur, list) and i < len(cur) else None
    return cur


@register("json.get")
def op_json_get(ctx, step):
    obj = resolve(ctx, step["value"])
    return _jsonpath(obj, step["path"])


_ANSWER_ANCHOR = re.compile(
    r"(?i)(?:final\s*answer|answer\s*(?:is|:|=)|conclusion\s*[:=]|therefore[,:]?|so\s*the\s*answer)")


def _search_verdict(pattern, text):
    for bm in reversed(list(re.finditer(r"\\boxed\{([^{}]*)\}", text))):
        m = re.search(pattern, bm.group(1))
        if m:
            return m
    anchors = list(_ANSWER_ANCHOR.finditer(text))
    if anchors:
        m = re.search(pattern, text[anchors[-1].end():])
        if m:
            return m
    ms = list(re.finditer(pattern, text))
    return ms[-1] if ms else None


@register("regex.extract")
def op_regex_extract(ctx, step):
    val = resolve(ctx, step["value"])
    if val is None:
        return {"none": True, "empty": True}
    pick = str(step.get("pick") or "first").lower()
    text = str(val)
    m = (_search_verdict(step["pattern"], text) if pick in ("last", "verdict")
         else re.search(step["pattern"], text))
    if not m:
        return {"none": True, "empty": True}
    groups = m.groups()
    if len(groups) >= 2:
        return list(groups)
    return groups[0] if groups else m.group(0)
