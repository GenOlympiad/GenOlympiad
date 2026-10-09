"""Refuse malformed questions before they reach the judge VLM."""
from __future__ import annotations

import io
import json
import os
import re
import time
import logging

log = logging.getLogger(__name__)

__all__ = ["QuestionLintError", "check", "guard", "guarded_reader", "say_value", "quotable",
           "human_join", "looks_like_ref", "check_authored", "MAX_QUOTED_CHARS",
           "MAX_QUOTED_WORDS"]


class QuestionLintError(ValueError):
    """A question was refused before it could be sent."""

    def __init__(self, violations, question=""):
        self.violations = list(violations)
        self.question = question
        ValueError.__init__(self, "question refused (%s): %r"
                            % (", ".join(self.violations), (question or "")[:200]))


MAX_QUOTED_CHARS = 60
MAX_QUOTED_WORDS = 8

_NON_VALUES = frozenset((
    "", "none", "null", "nil", "nan", "n/a", "na", "unknown", "unspecified",
    "true", "false", "yes", "no", "dict", "list", "tuple", "set", "object",
))

_REF_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z0-9_]+)+$")
_REPR_RE = re.compile(r"\[\s*['\"]|\{\s*['\"]|<[A-Za-z_][\w.]* object|\bat 0x[0-9a-fA-F]{6}"
                      r"|^\s*[\[\{\(].*[\]\}\)]\s*$", re.S)
_REPR_IN_Q_RE = re.compile(r"\[\s*'|<[A-Za-z_][\w.]* object|\bat 0x[0-9a-fA-F]{6}")


def looks_like_ref(s):
    return bool(isinstance(s, str) and _REF_RE.match(s.strip()))


def human_join(seq):
    items = [say_value(x) or str(x) for x in seq]
    items = [i for i in items if i != ""]
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    return "%s and %s" % (", ".join(items[:-1]), items[-1])


def say_value(v):
    if v is None or isinstance(v, bool):
        return ""
    if isinstance(v, float):
        return str(int(v)) if v == int(v) else ("%g" % v)
    if isinstance(v, int):
        return str(v)
    if isinstance(v, str):
        return v.strip()
    if isinstance(v, (list, tuple, set, frozenset)):
        seq = sorted(v, key=lambda x: str(x)) if isinstance(v, (set, frozenset)) else list(v)
        return human_join(seq)
    return ""


def quotable(v):
    if isinstance(v, bool) or v is None:
        return None
    if isinstance(v, (list, tuple, set, frozenset, dict)):
        return None
    s = say_value(v)
    if not s or "\n" in s:
        return None
    if s.strip().lower().rstrip(".") in _NON_VALUES:
        return None
    if _REPR_RE.search(s):
        return None
    if len(s) > MAX_QUOTED_CHARS or len(s.split()) > MAX_QUOTED_WORDS:
        return None
    return s


_MIN_QUESTION_CHARS = 12
_SHOW_OBJ_RE = re.compile(r"\b(?:show|shows|see|display|contain)\s+"
                          r"(dict|list|tuple|set|none|null|nan|true|false)\b\s*[?.]", re.I)
_PRINTF_LEFTOVER_RE = re.compile(r"%[sdrf]\b|\{\d+\}")
_BRACE_REF_RE = re.compile(r"\{[A-Za-z_][A-Za-z0-9_.]*\}")
_ERR_RE = re.compile(r"\btraceback\b|\bKeyError\b|\bTypeError\b|\bNoneType\b", re.I)
_VERIFY_SHOW_RE = re.compile(r"Does it show\s+(.+?)\?\s*Answer yes or no", re.I | re.S)


def check(question):
    bad = []
    if question is None or not isinstance(question, str):
        return ["not_a_string"]
    q = question.strip()
    if len(q) < _MIN_QUESTION_CHARS:
        bad.append("empty_or_tiny")
    if looks_like_ref(q):
        bad.append("bare_ref")
    if q.lower() in _NON_VALUES:
        bad.append("bare_ref")
    if _SHOW_OBJ_RE.search(q):
        bad.append("py_object")
    if _REPR_IN_Q_RE.search(q):
        bad.append("py_object")
    if _PRINTF_LEFTOVER_RE.search(q) or _BRACE_REF_RE.search(q):
        bad.append("unfilled_tpl")
    if _ERR_RE.search(q):
        bad.append("error_text")
    m = _VERIFY_SHOW_RE.search(q)
    if m:
        span = m.group(1).strip()
        if (len(span) > MAX_QUOTED_CHARS or len(span.split()) > MAX_QUOTED_WORDS
                or "\n" in span or "?" in span):
            bad.append("verify_prose")
    return sorted(set(bad))


_REFUSAL_LOG = None


def _log_refusal(violations, question):
    global _REFUSAL_LOG
    try:
        if _REFUSAL_LOG is None:
            root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            d = os.path.join(root, 'data')
            if not os.path.isdir(d):
                os.makedirs(d, exist_ok=True)
            _REFUSAL_LOG = os.path.join(d, "QUESTION_LINT_REFUSALS.jsonl")
        rec = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "violations": violations,
               "question": (question or "")[:400]}
        with io.open(_REFUSAL_LOG, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:
        log.debug("error ignored in _log_refusal", exc_info=True)
        pass


def guard(question, where=""):
    """Raise `QuestionLintError` if `question` is malformed; otherwise return it unchanged."""
    bad = check(question)
    if bad:
        _log_refusal(bad + ([where] if where else []), question)
        raise QuestionLintError(bad, question)
    return question


def check_authored(text):
    if not isinstance(text, str):
        return ["not_a_string"]
    s = text.strip()
    if looks_like_ref(s):
        return []
    probe = _BRACE_REF_RE.sub("something", s)
    return [v for v in check(probe) if v != "bare_ref"]


def guarded_reader(fn):
    """Wrap a `fn(image, question) -> answer` reader so no malformed question can be sent."""
    def _reader(image, question):
        guard(question, where=getattr(fn, "__name__", "reader"))
        return fn(image, question)
    _reader.__name__ = getattr(fn, "__name__", "reader")
    _reader.__doc__ = getattr(fn, "__doc__", None)
    _reader.__wrapped__ = fn
    return _reader


