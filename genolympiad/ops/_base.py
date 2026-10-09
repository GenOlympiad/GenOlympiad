"""The operator registry, the failure marker, majority voting and reference resolution."""
from __future__ import annotations
import logging

log = logging.getLogger(__name__)


OPS: dict = {}


def register(name):
    def deco(fn):
        OPS[name] = fn
        return fn
    return deco


class Fail:
    def __init__(self, reason="", kind="crash", diagnosis=""):
        self.reason = reason
        self.kind = kind if kind in ("crash", "evaluator") else "crash"
        self.diagnosis = str(diagnosis or "")

    @property
    def evaluator(self):
        return self.kind == "evaluator"

    def __repr__(self):
        return f"FAIL({self.reason})" if self.kind == "crash" else \
               f"FAIL[{self.kind}]({self.reason})"


def _hashable(r):
    if isinstance(r, (list, set)):
        return tuple(sorted(r) if isinstance(r, set) else r)
    if isinstance(r, dict):
        return tuple(sorted(r.items()))
    return r


def majority(reads):
    reads = [r for r in reads if r is not None]
    if not reads:
        return None
    counts = {}
    for r in reads:
        k = _hashable(r)
        counts[k] = counts.get(k, 0) + 1
    return max(reads, key=lambda r: counts[_hashable(r)])


_MISSING = object()


def resolve(ctx, ref):
    """Resolve a step argument."""
    if not isinstance(ref, str):
        return ref
    parts = ref.split(".")
    if parts[0] not in ctx:
        return ref
    cur = ctx[parts[0]]
    for part in parts[1:]:
        if isinstance(cur, dict):
            cur = cur.get(part, _MISSING)
        elif isinstance(cur, (list, tuple)) and part.isdigit():
            cur = cur[int(part)] if int(part) < len(cur) else _MISSING
        else:
            cur = getattr(cur, part, _MISSING)
        if cur is _MISSING:
            return None
    return cur


_TPL_RE = None


def fmt_inline(ctx, s, strict=False):
    global _TPL_RE
    if not isinstance(s, str):
        return s
    from ..question_lint import say_value, looks_like_ref
    v = resolve(ctx, s)
    if strict and isinstance(s, str):
        if v is None and looks_like_ref(s):
            raise ValueError("vlm question reference %r does not resolve (head present, "
                             "sub-field missing)" % s)
        if isinstance(v, str) and v == s and looks_like_ref(s):
            raise ValueError("vlm question reference %r does not resolve (no such context "
                             "variable)" % s)
    if strict and not isinstance(v, (str, int, float)) and v is not None:
        spoken = say_value(v)
        if not spoken:
            raise ValueError("vlm question argument %r resolved to a %s, which has no spoken "
                             "form" % (s, type(v).__name__))
        q = spoken
    else:
        q = str(v) if (strict or v is not None) else s
    if "{" not in q:
        return q
    if _TPL_RE is None:
        import re
        _TPL_RE = re.compile(r"\{([A-Za-z_][\w.]*)\}")
    misses = []

    def _sub(m):
        ref = m.group(1)
        rv = resolve(ctx, ref)
        if rv is None or (isinstance(rv, str) and rv == ref):
            if strict:
                raise ValueError(f"vlm question placeholder '{{{ref}}}' does not resolve")
            misses.append(ref)
            return m.group(0)
        if isinstance(rv, (str, int, float)) and not isinstance(rv, bool):
            return str(rv)
        spoken = say_value(rv)
        if not spoken:
            if strict:
                raise ValueError("vlm question placeholder '{%s}' resolved to a %s, which has "
                                 "no spoken form" % (ref, type(rv).__name__))
            misses.append(ref)
            return m.group(0)
        return spoken

    out = _TPL_RE.sub(_sub, q)
    if misses:
        import warnings
        warnings.warn("unresolved inline template ref(s) %s in %r" % (sorted(set(misses)), s[:80]),
                      RuntimeWarning, stacklevel=2)
    return out


_ALIGN_KEY_FIELDS = ("key", "id", "label", "name", "tag", "code", "number", "no", "index")


def _align_norm(v):
    if v is None:
        return None
    if isinstance(v, bool):
        return str(v).lower()
    if isinstance(v, (int, float)):
        f = float(v)
        return ("%d" % int(f)) if f == int(f) else ("%g" % f)
    s = " ".join(str(v).split()).strip().lower()
    if not s:
        return None
    try:
        f = float(s.replace(",", ""))
        return ("%d" % int(f)) if f == int(f) else ("%g" % f)
    except ValueError:
        log.debug("error ignored in _align_norm", exc_info=True)
        return s


def _align_row_keys(row):
    keys = []

    def add(v):
        n = _align_norm(v)
        if n is not None and n not in keys:
            keys.append(n)

    if isinstance(row, dict):
        for f in _ALIGN_KEY_FIELDS:
            if f in row:
                add(row[f])
        for v in row.values():
            if isinstance(v, (str, int, float)) and not isinstance(v, bool):
                add(v)
    elif isinstance(row, (list, tuple)):
        for v in row:
            if isinstance(v, (str, int, float)) and not isinstance(v, bool):
                add(v)
    else:
        add(row)
        if isinstance(row, str):
            import re
            for tok in re.findall(r"-?\d+(?:\.\d+)?|[A-Za-z]+", row):
                add(tok)
    return keys


def align_by_printed_key(got, keys, fallback_positional=True, return_report=False):
    rows = list(got or [])
    want = [_align_norm(k) for k in (keys or [])]
    aligned = [None] * len(want)
    used = set()
    for i, k in enumerate(want):
        if k is None:
            continue
        for j, row in enumerate(rows):
            if j in used:
                continue
            if k in _align_row_keys(row):
                aligned[i] = row
                used.add(j)
                break
    matched = sum(1 for a in aligned if a is not None)
    mode = "key"
    if matched == 0 and fallback_positional and rows and want:
        aligned = [rows[i] if i < len(rows) else None for i in range(len(want))]
        used = set(range(min(len(rows), len(want))))
        matched = sum(1 for a in aligned if a is not None)
        mode = "positional_fallback"
    if not return_report:
        return aligned
    return aligned, {
        "mode": mode, "matched": matched,
        "missing": [keys[i] for i, a in enumerate(aligned) if a is None],
        "extra": [rows[j] for j in range(len(rows)) if j not in used],
    }


def as_float(v, default=None):
    """Best-effort numeric coercion for reads that may arrive as '12.4 cm', '77.3 W', '-5'."""
    if v is None or isinstance(v, (dict, list, tuple, set, bool)):
        return default
    if isinstance(v, (int, float)):
        return float(v)
    import re
    s = str(v).strip().replace(",", "")
    neg = False
    su = s.upper()
    if su.endswith(("S", "W")):
        neg = True
    m = re.search(r"-?\d+(?:\.\d+)?", s)
    if not m:
        return default
    x = float(m.group(0))
    if neg and x > 0:
        x = -x
    return x
