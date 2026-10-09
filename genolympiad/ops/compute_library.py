"""Shared computation for the registered operators: tolerance bands, answers, tokens and grid cells."""
from __future__ import annotations

import math
import re
import logging

log = logging.getLogger(__name__)

__all__ = [
    "band", "band_multi", "log_error", "answers_of", "count_yes", "canon", "token_in", "boxes_of",
    "permille_to_px", "grid_cells", "product",
]


def _f(x, default=None):
    if x is None or isinstance(x, (dict, list, tuple, set)):
        return default
    if isinstance(x, bool):
        return float(x)
    try:
        return float(x)
    except (TypeError, ValueError):
        log.debug("error ignored in _f", exc_info=True)
        return default


def _as_list(x):
    if x is None:
        return []
    if isinstance(x, (list, tuple)):
        return list(x)
    return [x]


def band(value, target, core=0.0, margin=0.0, space="linear", fold=None, clamp_floor=0.0):
    """Graded tolerance ramp -> a fraction in [0, 1], rounded to 4 decimals."""
    v = _f(value)
    t = _f(target)
    if v is None or t is None:
        return 0.0
    core_v = _f(core, 0.0) or 0.0
    margin_v = _f(margin, 0.0) or 0.0
    if space in ("log", "log_ratio"):
        if v <= 0 or t <= 0:
            return 0.0
        d = abs(math.log(v / t))
        if space == "log_ratio":
            if core_v <= 0 or margin_v <= 0:
                return 0.0
            core_l = math.log(core_v)
            margin_v = math.log(margin_v) - core_l
            core_v = core_l
    else:
        d = abs(v - t)
        if fold:
            fold = abs(float(fold))
            d = d % fold
            d = min(d, fold - d)
    margin_v = max(float(margin_v), 1e-9)
    floor = _f(clamp_floor, 0.0) or 0.0
    frac = 1.0 - max(0.0, d - float(core_v)) / margin_v
    frac = min(1.0, max(floor, frac)) if frac > 0 else floor
    return round(min(1.0, max(0.0, frac)), 4)


def band_multi(values, target, core=0.0, margin=0.0, aggregate="mean", space="linear",
               fold=None, clamp_floor=0.0, require_all=True):
    vals = _as_list(values)
    tgts = _as_list(target)
    if not vals:
        return 0.0
    if len(tgts) == 1:
        tgts = tgts * len(vals)
    if len(tgts) != len(vals):
        if require_all:
            return 0.0
        n = min(len(tgts), len(vals))
        vals, tgts = vals[:n], tgts[:n]
        if not vals:
            return 0.0
    fr = [band(v, t, core, margin, space=space, fold=fold, clamp_floor=clamp_floor)
          for v, t in zip(vals, tgts)]
    if aggregate == "min":
        out = min(fr)
    elif aggregate == "max":
        out = max(fr)
    elif aggregate == "product":
        out = 1.0
        for f in fr:
            out *= f
    elif aggregate == "first":
        out = fr[0]
    else:
        out = sum(fr) / float(len(fr))
    return round(min(1.0, max(0.0, out)), 4)


def log_error(value, target):
    v = _f(value)
    t = _f(target)
    if v is None or t is None or v <= 0 or t <= 0:
        return None
    return abs(math.log(v / t))


def answers_of(node):
    if isinstance(node, dict):
        return list(node.get("answers") or [])
    if isinstance(node, (list, tuple)):
        return list(node)
    return [] if node is None else [node]


def count_yes(node, prefix="y"):
    ans = answers_of(node)
    p = str(prefix).lower()
    return {"n": sum(1 for a in ans if str(a).strip().lower().startswith(p)),
            "asked": len(ans)}


def canon(s, keep="alnum"):
    t = str(s).lower()
    if keep == "alpha":
        return re.sub(r"[^a-z]", "", t)
    if keep == "digits":
        return re.sub(r"[^0-9]", "", t)
    if keep == "word":
        return re.sub(r"[^a-z0-9_]", "", t)
    if keep == "space":
        return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", t)).strip()
    return re.sub(r"[^a-z0-9]", "", t)


TOKEN_IN_MODES = frozenset(("substring", "equals", "any", "all", "starts_with"))


def token_in(answer, target=None, vocabulary=None, keep="alnum", mode="substring"):
    """Canonicalise both sides, then match -> 1.0 or 0.0."""
    if str(mode) not in TOKEN_IN_MODES:
        raise ValueError(
            "compare.token_in: unregistered mode %r. Registered modes are %s. A mode this "
            "operator does not implement must never fall back to a different rule."
            % (mode, ", ".join(sorted(TOKEN_IN_MODES))))
    if answer is None or isinstance(answer, (dict, list, tuple, set)):
        return 0.0
    cands = [str(x) for x in (vocabulary if vocabulary is not None else _as_list(target))]
    if not cands:
        return 0.0
    if mode == "starts_with":
        a = str(answer).strip().lower()
        return 1.0 if any(a.startswith(c.strip().lower()) for c in cands) else 0.0
    a = canon(answer, keep)
    hits = [(canon(c, keep) in a) if mode != "equals" else (canon(c, keep) == a)
            for c in cands]
    if mode == "all":
        return 1.0 if all(hits) else 0.0
    return 1.0 if any(hits) else 0.0


def boxes_of(node, min_size=0.0):
    """A reader record (or a bare geometry list) -> normalised box dicts."""
    geo = node.get("geometry") if isinstance(node, dict) else node
    out = []
    for b in (geo or []):
        try:
            y0, x0, y1, x1 = [float(v) for v in list(b)[:4]]
        except (TypeError, ValueError):
            log.debug("error ignored in boxes_of", exc_info=True)
            continue
        w, h = x1 - x0, y1 - y0
        if w <= 0 or h <= 0 or w < min_size or h < min_size:
            continue
        out.append({"y0": y0, "x0": x0, "y1": y1, "x1": x1, "w": w, "h": h,
                    "cx": (x0 + x1) / 2.0, "cy": (y0 + y1) / 2.0})
    return out


def permille_to_px(value, size, scale=1000.0):
    """One per-mille coordinate (or a list of them) along an axis of pixel length `size`."""
    if isinstance(value, (list, tuple)):
        return [permille_to_px(v, size, scale) for v in value]
    v = _f(value)
    return None if v is None else v * float(size) / float(scale)


def grid_cells(box, rows, cols, inset=0.0, round_to=2, min_side=0.0, square_tol=None):
    b = boxes_of([box[0]] if isinstance(box, list) and box and isinstance(box[0], (list, tuple))
                 else box)
    if not b:
        return {"geometry": [], "rows": 0, "cols": 0, "n": 0, "degenerate": True,
                "why": "no box"}
    b = b[0]
    rows, cols = int(rows), int(cols)
    if rows < 1 or cols < 1 or b["h"] < min_side or b["w"] < min_side:
        return {"geometry": [], "rows": rows, "cols": cols, "n": 0, "degenerate": True,
                "why": "box too small to slice"}
    if square_tol is not None and abs(b["h"] - b["w"]) / max(b["h"], b["w"]) > float(square_tol):
        return {"geometry": [], "rows": rows, "cols": cols, "n": 0, "degenerate": True,
                "why": "box is not square"}
    ch, cw = b["h"] / float(rows), b["w"] / float(cols)
    p = float(inset)
    out = []
    for r in range(rows):
        for c in range(cols):
            rect = [b["y0"] + (r + p) * ch, b["x0"] + (c + p) * cw,
                    b["y0"] + (r + 1 - p) * ch, b["x0"] + (c + 1 - p) * cw]
            out.append([round(v, int(round_to)) for v in rect] if round_to is not None else rect)
    return {"geometry": out, "rows": rows, "cols": cols, "n": len(out),
            "degenerate": False, "why": ""}


def product(values):
    out = 1.0
    for v in _as_list(values):
        f = _f(v)
        out *= 0.0 if f is None else f
    return round(out, 4)


