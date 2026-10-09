# shared code: code_3baec8af2b90
def n(c):
    return len(c or [])

# end of code_3baec8af2b90

# code: f_code

import math

_WORDS = ("red", "green", "blue", "yellow", "purple", "orange", "pink", "cyan", "white",
          "black", "brown", "violet", "magenta")
_ALIAS = {"violet": "purple", "magenta": "purple", "cyan": "blue"}


def _colour_of(ans):
    s = str(ans or "").lower()
    for w in _WORDS:
        if w in s:
            return _ALIAS.get(w, w)
    return None


def _bandfrac(err, core, margin):
    err = abs(float(err))
    if err <= core:
        return 1.0
    if err >= core + margin:
        return 0.0
    return round(1.0 - (err - core) / margin, 4)


def _logerr(v, t):
    if v is None or t is None or float(v) <= 0 or float(t) <= 0:
        return None
    return abs(math.log(float(v) / float(t)))


def mobile(bar, col, cord, colours):
    bs = []
    for i, b in enumerate((bar or {}).get("geometry") or []):
        try:
            y0, x0, y1, x1 = [float(v) for v in b[:4]]
        except Exception:
            continue
        if x1 - x0 <= 0 or y1 - y0 <= 0:
            continue
        bs.append({"x0": x0, "x1": x1, "cy": (y0 + y1) / 2.0, "i": i})
    bs.sort(key=lambda b: b["cy"])
    ans = list((col or {}).get("answers") or [])
    for b in bs:
        b["colour"] = _colour_of(ans[b["i"]]) if b["i"] < len(ans) else None
    want = [str(c).lower() for c in (colours or [])]
    m = {"n_bars": len(want), "n_ok": 0, "ratios": [], "spread": None, "tie": [],
         "read": [b["colour"] for b in bs], "bound_by": "top-to-bottom order"}
    if not bs:
        return m
    order = bs
    got = [b["colour"] for b in bs]
    if len(bs) == len(want) and sorted(x for x in got if x) == sorted(want):
        order = [next(b for b in bs if b["colour"] == c) for c in want]
        m["bound_by"] = "atomic colour answers"
    tie0 = None
    g = (cord or {}).get("geometry") or []
    if g and len(g[0]) >= 4:
        y0, x0, y1, x1 = [float(v) for v in g[0][:4]]
        tie0 = (x0 + x1) / 2.0
    ties = []
    for k, b in enumerate(order):
        if k == 0:
            ties.append(tie0)
            continue
        p = order[k - 1]
        cands = [p["x0"], p["x1"]]
        inside = [t for t in cands if b["x0"] <= t <= b["x1"]]
        if inside:
            ties.append(inside[0])
        else:
            mid = (b["x0"] + b["x1"]) / 2.0
            ties.append(min(cands, key=lambda t: abs(t - mid)))
    ratios = []
    for b, t in zip(order, ties):
        if t is None:
            ratios.append(None)
            continue
        left = t - b["x0"]
        right = b["x1"] - t
        ratios.append(round(left / right, 4) if (left > 0 and right > 0) else None)
    m["ratios"] = ratios
    m["tie"] = [None if t is None else round(t, 1) for t in ties]
    m["n_ok"] = sum(1 for r in ratios if r)
    vals = [r for r in ratios if r]
    if len(vals) >= 2:
        m["spread"] = round(max(vals) / min(vals), 4)
    elif len(vals) == 1:
        m["spread"] = None
    return m


def all_bars_measured(bar, col, cord, colours):
    """Score 1 if every beam of the mobile was measured."""
    model = mobile(bar, col, cord, colours)
    score = 1.0 if (model["n_ok"] == model["n_bars"] and model["n_bars"] > 0) else 0.0
    return {"frac": score, "verdict": "bars measured %d of %d (colour answers %s, bound by %s) "
            "-> frac %s" % (model["n_ok"], model["n_bars"], model["read"], model["bound_by"], score)}

# end of f_code

# code: f_code_2

import math

_WORDS = ("red", "green", "blue", "yellow", "purple", "orange", "pink", "cyan", "white",
          "black", "brown", "violet", "magenta")
_ALIAS = {"violet": "purple", "magenta": "purple", "cyan": "blue"}


def _colour_of(ans):
    s = str(ans or "").lower()
    for w in _WORDS:
        if w in s:
            return _ALIAS.get(w, w)
    return None


def _bandfrac(err, core, margin):
    err = abs(float(err))
    if err <= core:
        return 1.0
    if err >= core + margin:
        return 0.0
    return round(1.0 - (err - core) / margin, 4)


def _logerr(v, t):
    if v is None or t is None or float(v) <= 0 or float(t) <= 0:
        return None
    return abs(math.log(float(v) / float(t)))


def mobile(bar, col, cord, colours):
    bs = []
    for i, b in enumerate((bar or {}).get("geometry") or []):
        try:
            y0, x0, y1, x1 = [float(v) for v in b[:4]]
        except Exception:
            continue
        if x1 - x0 <= 0 or y1 - y0 <= 0:
            continue
        bs.append({"x0": x0, "x1": x1, "cy": (y0 + y1) / 2.0, "i": i})
    bs.sort(key=lambda b: b["cy"])
    ans = list((col or {}).get("answers") or [])
    for b in bs:
        b["colour"] = _colour_of(ans[b["i"]]) if b["i"] < len(ans) else None
    want = [str(c).lower() for c in (colours or [])]
    m = {"n_bars": len(want), "n_ok": 0, "ratios": [], "spread": None, "tie": [],
         "read": [b["colour"] for b in bs], "bound_by": "top-to-bottom order"}
    if not bs:
        return m
    order = bs
    got = [b["colour"] for b in bs]
    if len(bs) == len(want) and sorted(x for x in got if x) == sorted(want):
        order = [next(b for b in bs if b["colour"] == c) for c in want]
        m["bound_by"] = "atomic colour answers"
    tie0 = None
    g = (cord or {}).get("geometry") or []
    if g and len(g[0]) >= 4:
        y0, x0, y1, x1 = [float(v) for v in g[0][:4]]
        tie0 = (x0 + x1) / 2.0
    ties = []
    for k, b in enumerate(order):
        if k == 0:
            ties.append(tie0)
            continue
        p = order[k - 1]
        cands = [p["x0"], p["x1"]]
        inside = [t for t in cands if b["x0"] <= t <= b["x1"]]
        if inside:
            ties.append(inside[0])
        else:
            mid = (b["x0"] + b["x1"]) / 2.0
            ties.append(min(cands, key=lambda t: abs(t - mid)))
    ratios = []
    for b, t in zip(order, ties):
        if t is None:
            ratios.append(None)
            continue
        left = t - b["x0"]
        right = b["x1"] - t
        ratios.append(round(left / right, 4) if (left > 0 and right > 0) else None)
    m["ratios"] = ratios
    m["tie"] = [None if t is None else round(t, 1) for t in ties]
    m["n_ok"] = sum(1 for r in ratios if r)
    vals = [r for r in ratios if r]
    if len(vals) >= 2:
        m["spread"] = round(max(vals) / min(vals), 4)
    elif len(vals) == 1:
        m["spread"] = None
    return m


def arm_ratio_score(bar, col, cord, colours, targets, core=0.1823, margin=0.2560):
    """Average closeness of each beam's left to right arm ratio to the reference ratio."""
    model = mobile(bar, col, cord, colours)
    ratios = list(model["ratios"])
    target_ratios = [float(x) for x in targets]
    if len(ratios) != len(target_ratios):
        return {"frac": 0.0, "ratios": ratios,
                "verdict": "measured %d bars, the answer key has %d -> frac 0.0"
                % (len(ratios), len(target_ratios))}
    total = 0.0
    per_bar = []
    for g, t in zip(ratios, target_ratios):
        error = _logerr(g, t)
        v = 0.0 if error is None else _bandfrac(error, core, margin)
        per_bar.append(v)
        total += v
    frac = round(total / len(target_ratios), 4)
    return {"frac": frac, "ratios": ratios, "targets": target_ratios, "ties": model["tie"], "per_bar": per_bar,
            "verdict": "left-arm/right-arm per bar %s vs %s (log band core %s / margin %s) "
            "-> frac %s" % (ratios, target_ratios, core, margin, frac)}

# end of f_code_2

# code: f_code_3

import math

_WORDS = ("red", "green", "blue", "yellow", "purple", "orange", "pink", "cyan", "white",
          "black", "brown", "violet", "magenta")
_ALIAS = {"violet": "purple", "magenta": "purple", "cyan": "blue"}


def _colour_of(ans):
    s = str(ans or "").lower()
    for w in _WORDS:
        if w in s:
            return _ALIAS.get(w, w)
    return None


def _bandfrac(err, core, margin):
    err = abs(float(err))
    if err <= core:
        return 1.0
    if err >= core + margin:
        return 0.0
    return round(1.0 - (err - core) / margin, 4)


def _logerr(v, t):
    if v is None or t is None or float(v) <= 0 or float(t) <= 0:
        return None
    return abs(math.log(float(v) / float(t)))


def mobile(bar, col, cord, colours):
    bs = []
    for i, b in enumerate((bar or {}).get("geometry") or []):
        try:
            y0, x0, y1, x1 = [float(v) for v in b[:4]]
        except Exception:
            continue
        if x1 - x0 <= 0 or y1 - y0 <= 0:
            continue
        bs.append({"x0": x0, "x1": x1, "cy": (y0 + y1) / 2.0, "i": i})
    bs.sort(key=lambda b: b["cy"])
    ans = list((col or {}).get("answers") or [])
    for b in bs:
        b["colour"] = _colour_of(ans[b["i"]]) if b["i"] < len(ans) else None
    want = [str(c).lower() for c in (colours or [])]
    m = {"n_bars": len(want), "n_ok": 0, "ratios": [], "spread": None, "tie": [],
         "read": [b["colour"] for b in bs], "bound_by": "top-to-bottom order"}
    if not bs:
        return m
    order = bs
    got = [b["colour"] for b in bs]
    if len(bs) == len(want) and sorted(x for x in got if x) == sorted(want):
        order = [next(b for b in bs if b["colour"] == c) for c in want]
        m["bound_by"] = "atomic colour answers"
    tie0 = None
    g = (cord or {}).get("geometry") or []
    if g and len(g[0]) >= 4:
        y0, x0, y1, x1 = [float(v) for v in g[0][:4]]
        tie0 = (x0 + x1) / 2.0
    ties = []
    for k, b in enumerate(order):
        if k == 0:
            ties.append(tie0)
            continue
        p = order[k - 1]
        cands = [p["x0"], p["x1"]]
        inside = [t for t in cands if b["x0"] <= t <= b["x1"]]
        if inside:
            ties.append(inside[0])
        else:
            mid = (b["x0"] + b["x1"]) / 2.0
            ties.append(min(cands, key=lambda t: abs(t - mid)))
    ratios = []
    for b, t in zip(order, ties):
        if t is None:
            ratios.append(None)
            continue
        left = t - b["x0"]
        right = b["x1"] - t
        ratios.append(round(left / right, 4) if (left > 0 and right > 0) else None)
    m["ratios"] = ratios
    m["tie"] = [None if t is None else round(t, 1) for t in ties]
    m["n_ok"] = sum(1 for r in ratios if r)
    vals = [r for r in ratios if r]
    if len(vals) >= 2:
        m["spread"] = round(max(vals) / min(vals), 4)
    elif len(vals) == 1:
        m["spread"] = None
    return m


def arm_spread_score(bar, col, cord, colours, spread, core=0.2231, margin=0.4700):
    """Closeness of the steepest to shallowest arm ratio spread to the reference spread."""
    model = mobile(bar, col, cord, colours)
    error = _logerr(model["spread"], spread)
    frac = 0.0 if error is None else _bandfrac(error, core, margin)
    return {"frac": frac, "verdict": "steepest/shallowest arm ratio %s vs %s (log band core %s / "
            "margin %s) -> frac %s" % (model["spread"], spread, core, margin, frac)}

# end of f_code_3

# code: f_code_4

import math

_WORDS = ("red", "green", "blue", "yellow", "purple", "orange", "pink", "cyan", "white",
          "black", "brown", "violet", "magenta")
_ALIAS = {"violet": "purple", "magenta": "purple", "cyan": "blue"}


def _colour_of(ans):
    s = str(ans or "").lower()
    for w in _WORDS:
        if w in s:
            return _ALIAS.get(w, w)
    return None


def _bandfrac(err, core, margin):
    err = abs(float(err))
    if err <= core:
        return 1.0
    if err >= core + margin:
        return 0.0
    return round(1.0 - (err - core) / margin, 4)


def _logerr(v, t):
    if v is None or t is None or float(v) <= 0 or float(t) <= 0:
        return None
    return abs(math.log(float(v) / float(t)))


def mobile(bar, col, cord, colours):
    bs = []
    for i, b in enumerate((bar or {}).get("geometry") or []):
        try:
            y0, x0, y1, x1 = [float(v) for v in b[:4]]
        except Exception:
            continue
        if x1 - x0 <= 0 or y1 - y0 <= 0:
            continue
        bs.append({"x0": x0, "x1": x1, "cy": (y0 + y1) / 2.0, "i": i})
    bs.sort(key=lambda b: b["cy"])
    ans = list((col or {}).get("answers") or [])
    for b in bs:
        b["colour"] = _colour_of(ans[b["i"]]) if b["i"] < len(ans) else None
    want = [str(c).lower() for c in (colours or [])]
    m = {"n_bars": len(want), "n_ok": 0, "ratios": [], "spread": None, "tie": [],
         "read": [b["colour"] for b in bs], "bound_by": "top-to-bottom order"}
    if not bs:
        return m
    order = bs
    got = [b["colour"] for b in bs]
    if len(bs) == len(want) and sorted(x for x in got if x) == sorted(want):
        order = [next(b for b in bs if b["colour"] == c) for c in want]
        m["bound_by"] = "atomic colour answers"
    tie0 = None
    g = (cord or {}).get("geometry") or []
    if g and len(g[0]) >= 4:
        y0, x0, y1, x1 = [float(v) for v in g[0][:4]]
        tie0 = (x0 + x1) / 2.0
    ties = []
    for k, b in enumerate(order):
        if k == 0:
            ties.append(tie0)
            continue
        p = order[k - 1]
        cands = [p["x0"], p["x1"]]
        inside = [t for t in cands if b["x0"] <= t <= b["x1"]]
        if inside:
            ties.append(inside[0])
        else:
            mid = (b["x0"] + b["x1"]) / 2.0
            ties.append(min(cands, key=lambda t: abs(t - mid)))
    ratios = []
    for b, t in zip(order, ties):
        if t is None:
            ratios.append(None)
            continue
        left = t - b["x0"]
        right = b["x1"] - t
        ratios.append(round(left / right, 4) if (left > 0 and right > 0) else None)
    m["ratios"] = ratios
    m["tie"] = [None if t is None else round(t, 1) for t in ties]
    m["n_ok"] = sum(1 for r in ratios if r)
    vals = [r for r in ratios if r]
    if len(vals) >= 2:
        m["spread"] = round(max(vals) / min(vals), 4)
    elif len(vals) == 1:
        m["spread"] = None
    return m


def report_arm_ratios(bar, col, cord, colours, targets):
    """Score 1 if any arm ratios were measured, reporting them beside the reference ratios."""
    model = mobile(bar, col, cord, colours)
    return {"frac": 0.0 if not model["ratios"] else 1.0, "ratios": model["ratios"], "ties": model["tie"],
            "read": model["read"], "spread": model["spread"], "targets": list(targets),
            "verdict": "colour answers %s (bound by %s), tie points %s, arm ratios %s vs key %s"
            % (model["read"], model["bound_by"], model["tie"], model["ratios"], list(targets))}

# end of f_code_4
