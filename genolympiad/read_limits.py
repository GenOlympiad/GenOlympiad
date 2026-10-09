"""Time limits, retries and refusal rules for judge VLM reads."""
from __future__ import annotations

import contextlib
import functools
import threading
import logging

log = logging.getLogger(__name__)


def _authored_none():
    try:
        from genolympiad.ops.evidence_grounding import authored_none
        return authored_none
    except Exception:
        log.debug("error ignored in _authored_none", exc_info=True)
        return None


def _is_shrug():
    try:
        from genolympiad.ops.evidence_grounding import is_shrug
        return is_shrug
    except Exception:
        log.debug("error ignored in _is_shrug", exc_info=True)
        return None


def probe():
    return {"authored_none": _authored_none() is not None,
            "is_shrug": _is_shrug() is not None}


def _norm(s):
    return " ".join(str(s or "").strip().strip(".;,:!\"'`").split()).lower()


class ReaderWallTimeout(Exception):

    def __init__(self, label, seconds, attempts):
        Exception.__init__(self, "%s exceeded its %gs wall clock on %d attempt(s)"
                                 % (label, float(seconds), attempts))
        self.label, self.seconds, self.attempts = label, float(seconds), int(attempts)


@contextlib.contextmanager
def carry_read_mode(snap):
    if not snap:
        yield None
        return
    try:
        from genolympiad import judge_vlm as _readers
    except Exception:
        log.debug("error ignored in carry_read_mode", exc_info=True)
        yield None
        return
    with _readers.read_mode(thinking=snap[0], max_tokens=snap[1]):
        yield snap


def wall_call(fn, args=(), kwargs=None, timeout_s=None, retries=None, label="reader"):
    kwargs = dict(kwargs or {})
    return fn(*args, **kwargs)


class ReadScope(object):

    __slots__ = ("_hits", "_lock", "label", "task_counter")

    def __init__(self, label=""):
        self._hits = []
        self._lock = threading.Lock()
        self.label = str(label or "")
        self.task_counter = task_counter()

    def note(self, exc):
        with self._lock:
            self._hits.append(exc)

    def hits(self):
        with self._lock:
            return list(self._hits)

    def __len__(self):
        with self._lock:
            return len(self._hits)

    def __bool__(self):
        return len(self) > 0

    __nonzero__ = __bool__


_SCOPES = threading.local()
_TASK = threading.local()
_COUNT_LOCK = threading.Lock()


def begin_task_count():
    counter = [0]
    _TASK.counter = counter
    return counter


def end_task_count():
    """Stop counting for this thread."""
    _TASK.counter = None


def task_counter():
    c = getattr(_TASK, "counter", None)
    if c is None:
        sc = current_scope()
        c = getattr(sc, "task_counter", None) if sc is not None else None
    return c


def _scope_stack():
    st = getattr(_SCOPES, "stack", None)
    if st is None:
        st = []
        _SCOPES.stack = st
    return st


def current_scope():
    st = _scope_stack()
    return st[-1] if st else None


def _pop_frame(st, sc):
    if st and st[-1] is sc:
        st.pop()
    elif sc in st:
        st.remove(sc)


@contextlib.contextmanager
def read_scope(label=""):
    sc = ReadScope(label)
    st = _scope_stack()
    st.append(sc)
    try:
        yield sc
    finally:
        _pop_frame(st, sc)


@contextlib.contextmanager
def use_scope(sc):
    if sc is None:
        yield None
        return
    st = _scope_stack()
    st.append(sc)
    try:
        yield sc
    finally:
        _pop_frame(st, sc)


def scoped(fn):

    @functools.wraps(fn)
    def _scoped_op(*a, **kw):
        with read_scope(getattr(fn, "__name__", "")):
            return fn(*a, **kw)

    _scoped_op._scoped_flag = True
    return _scoped_op


def mark_timeout(exc, scope=None):
    sc = scope if scope is not None else current_scope()
    if sc is None:
        return False
    sc.note(exc)
    return True


def pop_timeouts(scope=None):
    sc = scope if scope is not None else current_scope()
    if sc is None:
        return []
    return sc.hits()


def wall_reader(fn, label="vlm reader", timeout_s=None, retries=None):
    if fn is None:
        return None
    if getattr(fn, "_walled", False):
        return fn

    @functools.wraps(fn)
    def _walled_reader(*a, **kw):
        counter = task_counter()
        if counter is not None:
            with _COUNT_LOCK:
                counter[0] += 1
        try:
            return wall_call(fn, a, kw, timeout_s=timeout_s, retries=retries, label=label)
        except ReaderWallTimeout as _wt:
            log.debug("error ignored in wall_reader", exc_info=True)
            mark_timeout(_wt)
            return None

    _walled_reader._walled = True
    _walled_reader._wall_inner = fn
    _walled_reader._wall_label = label
    return _walled_reader


def wall_refusal(exc, what="reader"):
    return {"unreadable": True, "empty": True, "no_read": True, "refused": True,
            "reason": "wall_timeout", "held": True,
            "refusal": ("%s hung: %s. Withheld, because an evaluator that will not answer is never the model's zero." % (what, exc))}


