# code: f_code

import math


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


def table(node):
    g = (node or {}).get("geometry") or []
    bs = []
    for b in g:
        try:
            y0, x0, y1, x1 = [float(v) for v in b[:4]]
        except Exception:
            continue
        if y1 - y0 <= 0 or x1 - x0 <= 0:
            continue
        bs.append([y0, x0, y1, x1])
    bs.sort(key=lambda b: (b[1] + b[3]) / 2.0)
    hs = [b[2] - b[0] for b in bs]
    n = len(hs)
    mean = (sum(hs) / n) if n else 0.0
    norms = [h / mean for h in hs] if mean > 0 else []
    spread = (max(hs) / min(hs)) if (n >= 2 and min(hs) > 0) else None
    return {"n_cols": n, "heights": [round(h, 2) for h in hs],
            "norms": [round(v, 4) for v in norms],
            "spread": (round(spread, 4) if spread is not None else None)}


def column_count_score(node, k):
    """Score 1 when the number of columns found equals the required number."""
    measured = table(node)
    ok = 1.0 if int(measured["n_cols"]) == int(k) else 0.0
    return {"frac": ok, "verdict": "columns found %d vs required %d -> frac %s"
            % (measured["n_cols"], int(k), ok), "heights": measured["heights"]}

# end of f_code

# code: f_code_2

import math


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


def table(node):
    g = (node or {}).get("geometry") or []
    bs = []
    for b in g:
        try:
            y0, x0, y1, x1 = [float(v) for v in b[:4]]
        except Exception:
            continue
        if y1 - y0 <= 0 or x1 - x0 <= 0:
            continue
        bs.append([y0, x0, y1, x1])
    bs.sort(key=lambda b: (b[1] + b[3]) / 2.0)
    hs = [b[2] - b[0] for b in bs]
    n = len(hs)
    mean = (sum(hs) / n) if n else 0.0
    norms = [h / mean for h in hs] if mean > 0 else []
    spread = (max(hs) / min(hs)) if (n >= 2 and min(hs) > 0) else None
    return {"n_cols": n, "heights": [round(h, 2) for h in hs],
            "norms": [round(v, 4) for v in norms],
            "spread": (round(spread, 4) if spread is not None else None)}


def spread_floor_score(node, min_spread):
    """Score 1 when the deepest-to-shallowest ratio reaches the floor."""
    measured = table(node)
    spread = measured["spread"]
    ok = 1.0 if (spread is not None and float(spread) >= float(min_spread)) else 0.0
    return {"frac": ok, "verdict": "deepest/shallowest %s vs floor %s -> frac %s"
            % (spread, min_spread, ok)}

# end of f_code_2

# code: f_code_3

import math


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


def table(node):
    g = (node or {}).get("geometry") or []
    bs = []
    for b in g:
        try:
            y0, x0, y1, x1 = [float(v) for v in b[:4]]
        except Exception:
            continue
        if y1 - y0 <= 0 or x1 - x0 <= 0:
            continue
        bs.append([y0, x0, y1, x1])
    bs.sort(key=lambda b: (b[1] + b[3]) / 2.0)
    hs = [b[2] - b[0] for b in bs]
    n = len(hs)
    mean = (sum(hs) / n) if n else 0.0
    norms = [h / mean for h in hs] if mean > 0 else []
    spread = (max(hs) / min(hs)) if (n >= 2 and min(hs) > 0) else None
    return {"n_cols": n, "heights": [round(h, 2) for h in hs],
            "norms": [round(v, 4) for v in norms],
            "spread": (round(spread, 4) if spread is not None else None)}


def depth_profile_score(node, targets, core=0.1823, margin=0.2560):
    """Average how closely each mean-normalised depth matches its target."""
    measured = table(node)
    got = list(measured["norms"])
    target_list = [float(x) for x in targets]
    if len(got) != len(target_list):
        return {"frac": 0.0, "verdict": "read %d columns, the answer key has %d -> frac 0.0"
                % (len(got), len(target_list)), "norms": got}
    total = 0.0
    per_vessel = []
    for g, t in zip(got, target_list):
        log_error = _logerr(g, t)
        v = 0.0 if log_error is None else _bandfrac(log_error, core, margin)
        per_vessel.append(v)
        total += v
    frac = round(total / len(target_list), 4)
    return {"frac": frac, "norms": got, "targets": target_list, "per_vessel": per_vessel,
            "verdict": "mean-normalised depths %s vs %s (log band core %s / margin %s) -> frac %s"
            % (got, target_list, core, margin, frac)}

# end of f_code_3

# code: f_code_4

import math


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


def table(node):
    g = (node or {}).get("geometry") or []
    bs = []
    for b in g:
        try:
            y0, x0, y1, x1 = [float(v) for v in b[:4]]
        except Exception:
            continue
        if y1 - y0 <= 0 or x1 - x0 <= 0:
            continue
        bs.append([y0, x0, y1, x1])
    bs.sort(key=lambda b: (b[1] + b[3]) / 2.0)
    hs = [b[2] - b[0] for b in bs]
    n = len(hs)
    mean = (sum(hs) / n) if n else 0.0
    norms = [h / mean for h in hs] if mean > 0 else []
    spread = (max(hs) / min(hs)) if (n >= 2 and min(hs) > 0) else None
    return {"n_cols": n, "heights": [round(h, 2) for h in hs],
            "norms": [round(v, 4) for v in norms],
            "spread": (round(spread, 4) if spread is not None else None)}


def spread_ratio_score(node, spread, core=0.2231, margin=0.4700):
    """Score how closely the deepest-to-shallowest ratio matches the target."""
    measured = table(node)
    log_error = _logerr(measured["spread"], spread)
    frac = 0.0 if log_error is None else _bandfrac(log_error, core, margin)
    return {"frac": frac, "verdict": "deepest/shallowest %s vs %s (log band core %s / margin %s)"
            " -> frac %s" % (measured["spread"], spread, core, margin, frac)}

# end of f_code_4

# code: f_code_5

import math


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


def table(node):
    g = (node or {}).get("geometry") or []
    bs = []
    for b in g:
        try:
            y0, x0, y1, x1 = [float(v) for v in b[:4]]
        except Exception:
            continue
        if y1 - y0 <= 0 or x1 - x0 <= 0:
            continue
        bs.append([y0, x0, y1, x1])
    bs.sort(key=lambda b: (b[1] + b[3]) / 2.0)
    hs = [b[2] - b[0] for b in bs]
    n = len(hs)
    mean = (sum(hs) / n) if n else 0.0
    norms = [h / mean for h in hs] if mean > 0 else []
    spread = (max(hs) / min(hs)) if (n >= 2 and min(hs) > 0) else None
    return {"n_cols": n, "heights": [round(h, 2) for h in hs],
            "norms": [round(v, 4) for v in norms],
            "spread": (round(spread, 4) if spread is not None else None)}


def pair_ratio_score(node, pair, ratio, core=0.1823, margin=0.2560):
    """Score how closely the depth ratio of the equal-width pair matches the target."""
    measured = table(node)
    heights = list(measured["heights"])
    i, j = int(pair[0]), int(pair[1])
    if max(i, j) >= len(heights) or min(heights[i], heights[j]) <= 0:
        return {"frac": 0.0, "verdict": "the equal-width pair could not be read -> frac 0.0"}
    measured_ratio = heights[i] / float(heights[j])
    log_error = _logerr(measured_ratio, ratio)
    frac = 0.0 if log_error is None else _bandfrac(log_error, core, margin)
    return {"frac": frac, "verdict": "depth ratio of the two equal-width vessels %.4f vs %s "
            "(log band core %s / margin %s) -> frac %s" % (measured_ratio, ratio, core, margin, frac)}

# end of f_code_5

# code: f_code_6

import math


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


def table(node):
    g = (node or {}).get("geometry") or []
    bs = []
    for b in g:
        try:
            y0, x0, y1, x1 = [float(v) for v in b[:4]]
        except Exception:
            continue
        if y1 - y0 <= 0 or x1 - x0 <= 0:
            continue
        bs.append([y0, x0, y1, x1])
    bs.sort(key=lambda b: (b[1] + b[3]) / 2.0)
    hs = [b[2] - b[0] for b in bs]
    n = len(hs)
    mean = (sum(hs) / n) if n else 0.0
    norms = [h / mean for h in hs] if mean > 0 else []
    spread = (max(hs) / min(hs)) if (n >= 2 and min(hs) > 0) else None
    return {"n_cols": n, "heights": [round(h, 2) for h in hs],
            "norms": [round(v, 4) for v in norms],
            "spread": (round(spread, 4) if spread is not None else None)}


def depth_profile_overlay(node, targets, core=0.1823, margin=0.2560):
    """Average depth matches against the key and report the heights for drawing."""
    measured = table(node)
    got = list(measured["norms"])
    target_list = [float(x) for x in targets]
    frac = 0.0
    if len(got) == len(target_list):
        total = 0.0
        for g, t in zip(got, target_list):
            log_error = _logerr(g, t)
            total += 0.0 if log_error is None else _bandfrac(log_error, core, margin)
        frac = round(total / len(target_list), 4)
    return {"frac": frac, "heights": measured["heights"], "norms": got, "targets": target_list,
            "spread": measured["spread"],
            "verdict": "measured column heights (per-mille) %s -> mean-normalised %s vs key %s"
            % (measured["heights"], got, target_list)}

# end of f_code_6
