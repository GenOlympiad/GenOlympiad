# shared code: code_23f92a6803dd
import math


def _band(v, t, core, margin):
    if v is None or t is None:
        return 0.0
    d = abs(float(v) - float(t))
    return round(min(1.0, max(0.0, 1.0 - max(0.0, d - float(core)) / max(float(margin), 1e-9))), 4)


def _logband(got, target, core_ratio=1.20, margin_ratio=1.42):
    if not got or not target or got <= 0 or target <= 0:
        return 0.0
    d = abs(math.log(float(got) / float(target)))
    core = math.log(float(core_ratio))
    margin = math.log(float(margin_ratio)) - core
    return round(min(1.0, max(0.0, 1.0 - max(0.0, d - core) / max(margin, 1e-9))), 4)


def _median(xs):
    s = sorted(xs)
    n = len(s)
    if not n:
        return 0.0
    return float(s[n // 2]) if n % 2 else 0.5 * (s[n // 2 - 1] + s[n // 2])


def _std(xs):
    n = len(xs)
    if n < 2:
        return 0.0
    mu = sum(xs) / float(n)
    return math.sqrt(sum((x - mu) ** 2 for x in xs) / float(n))


def n_total(k, ncol):
    return {"n": int(k) * int(ncol)}


def _boxes(r):
    g = r.get("geometry") if isinstance(r, dict) else r
    out = []
    for b in (g or []):
        try:
            y0, x0, y1, x1 = [float(v) for v in list(b)[:4]]
        except Exception:
            continue
        if y1 < y0:
            y0, y1 = y1, y0
        if x1 < x0:
            x0, x1 = x1, x0
        out.append({"cx": 0.5 * (x0 + x1), "cy": 0.5 * (y0 + y1),
                    "area": max(1.0, (y1 - y0) * (x1 - x0))})
    return out


def _split_columns(cands, ncol):
    cs = sorted(cands, key=lambda c: c["cx"])
    if int(ncol) <= 1:
        return [cs] if cs else []
    if len(cs) < 6:
        return []
    best, bi = -1.0, None
    for i in range(2, len(cs) - 2):
        dd = cs[i]["cx"] - cs[i - 1]["cx"]
        if dd > best:
            best, bi = dd, i
    if bi is None:
        return []
    return [cs[:bi], cs[bi:]]


def gaps_read(marks, k, ncol=1):
    """Split the flash marks into columns and list the vertical gaps down each column."""
    cands = _boxes(marks)
    if len(cands) < 4:
        return {"no_read": True, "reason": "too_few_marks", "n_found": len(cands)}
    cols = _split_columns(cands, ncol)
    if len(cols) != int(ncol) or any(len(c) < 3 for c in cols):
        return {"no_read": True, "reason": "columns_not_found",
                "n_found": [len(c) for c in cols]}
    out = []
    for g in cols:
        g = sorted(g, key=lambda c: c["cy"])
        ys = [c["cy"] for c in g]
        gaps = [round(ys[i + 1] - ys[i], 2) for i in range(len(ys) - 1)]
        ar = [c["area"] for c in g]
        out.append({"n": len(g), "gaps": gaps,
                    "centres": [[round(c["cx"], 1), round(c["cy"], 1)] for c in g],
                    "cx_std_frac": round(_std([c["cx"] for c in g]) / 1000.0, 4),
                    "area_ratio": round(max(ar) / float(max(1.0, min(ar))), 3)})
    return {"no_read": False, "k": int(k), "ncol": int(ncol), "columns": out}


def _tail(gaps, lock):
    t = gaps[int(lock) - 1:]
    return t if len(t) >= 2 else gaps[-2:]


def _head(gaps, lock):
    return gaps[:max(2, int(lock) - 1)]


def column_readable_frac(measured, k, ncol):
    """1 if every column holds nearly the reference number of flashes, else 0."""
    if measured.get("no_read"):
        return 0.0
    columns = measured.get("columns") or []
    if len(columns) != int(ncol):
        return 0.0
    return 1.0 if all(c["n"] >= max(4, int(k) - 2) for c in columns) else 0.0


def flash_count_frac(measured, k, ncol):
    """The share of columns holding exactly the reference number of flashes."""
    if measured.get("no_read"):
        return 0.0
    columns = measured.get("columns") or []
    if not columns:
        return 0.0
    return round(sum(1 for c in columns if c["n"] == int(k)) / float(len(columns)), 4)


def head_widen_frac(measured, lock):
    """How steadily the gaps widen before the lock flash, averaged over columns."""
    if measured.get("no_read"):
        return 0.0
    scores = []
    for c in measured["columns"]:
        h = _head(c["gaps"], lock)
        pf = []
        for i in range(len(h) - 1):
            if h[i] <= 0.5:
                pf.append(0.0)
                continue
            pf.append(round(min(1.0, max(0.0, (h[i + 1] / h[i] - 1.0) / 0.10)), 4))
        scores.append(sum(pf) / float(max(1, len(pf))))
    return round(sum(scores) / float(len(scores)), 4)


def tail_lock_frac(measured, lock):
    """How even the gaps stay after the lock flash, averaged over columns."""
    if measured.get("no_read"):
        return 0.0
    scores = []
    for c in measured["columns"]:
        t = _tail(c["gaps"], lock)
        if not t or min(t) <= 0.5:
            scores.append(0.0)
            continue
        scores.append(_band(max(t) / min(t), 1.0, 0.12, 0.18))
    return round(sum(scores) / float(len(scores)), 4)


def first_over_tail_frac(measured, lock, target):
    """How close the first gap over the median later gap is to the reference ratio."""
    if measured.get("no_read"):
        return 0.0
    scores = []
    for c in measured["columns"]:
        t = _tail(c["gaps"], lock)
        if not c["gaps"] or not t or _median(t) <= 0.5:
            scores.append(0.0)
            continue
        scores.append(_logband(c["gaps"][0] / _median(t), float(target), 1.20, 1.42))
    return round(sum(scores) / float(len(scores)), 4)


def two_regime_frac(measured, lock, target):
    """The product of the widening, steady tail and first gap ratio scores."""
    if measured.get("no_read"):
        return 0.0
    return round(head_widen_frac(measured, lock) * tail_lock_frac(measured, lock)
                 * first_over_tail_frac(measured, lock, target), 4)


def speed_ratio_frac(measured, target):
    """How close the ratio of the two columns' later gaps is to the reference ratio."""
    if measured.get("no_read"):
        return 0.0
    columns = measured.get("columns") or []
    if len(columns) < 2:
        return 0.0
    t0, t1 = _tail(columns[0]["gaps"], 4), _tail(columns[1]["gaps"], 4)
    if not t0 or not t1:
        return 0.0
    a, b = _median(t0), _median(t1)
    if b <= 0.5:
        return 0.0
    return _logband(a / b, float(target), 1.18, 1.40)


def carrier_frac(measured, k, ncol):
    """The share of columns with the right flash count, a straight line and even marks."""
    if measured.get("no_read"):
        return 0.0
    columns = measured.get("columns") or []
    if len(columns) != int(ncol):
        return 0.0
    ok = [1.0 if (c["n"] == int(k) and c["cx_std_frac"] <= 0.012
                  and c["area_ratio"] <= 1.60) else 0.0 for c in columns]
    return round(sum(ok) / float(len(ok)), 4)

# end of code_23f92a6803dd
