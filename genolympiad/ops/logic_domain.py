"""Comparison operators that need domain knowledge, such as weather codes and weekdays."""
from __future__ import annotations
import re
from ._base import register, resolve, as_float
import logging

log = logging.getLogger(__name__)


def _band(v, t, core, margin):
    if v is None or t is None:
        return 0.0
    d = abs(float(v) - float(t))
    margin = max(float(margin), 1e-9)
    frac = 1.0 - max(0.0, d - float(core)) / margin
    return round(min(1.0, max(0.0, frac)), 4)


_AQI_ORDER = ["good", "moderate", "usg", "unhealthy", "very unhealthy", "hazardous"]


def _aqi_category(aqi):
    a = as_float(aqi)
    if a is None:
        return None
    if a <= 50:  return "good"
    if a <= 100: return "moderate"
    if a <= 150: return "usg"
    if a <= 200: return "unhealthy"
    if a <= 300: return "very unhealthy"
    return "hazardous"


_CAT_PATTERNS = [
    ("hazardous", r"(hazard)"),
    ("very unhealthy", r"(very\s*unhealthy|maroon|purple)"),
    ("usg", r"(sensitive|usg|unhealthy for sensitive)"),
    ("unhealthy", r"(unhealthy|red\b)"),
    ("moderate", r"(moderate|fair|yellow)"),
    ("good", r"(good|clean|green\b|healthy|excellent)"),
]


def _parse_category(text):
    t = (text or "").lower()
    for bucket, pat in _CAT_PATTERNS:
        if re.search(pat, t):
            return bucket
    return None


def _parse_aqi_number(text):
    if text is None:
        return None
    t = str(text).strip().lower()
    t = re.sub(r"[-+]?\d+(?:\.\d+)?\s*%", " ", t)
    t = t.replace(",", " ")
    m = re.search(r"(\d+(?:\.\d+)?)", t)
    return float(m.group(1)) if m else None


def _cat_adjacent(a, b, max_steps=1):
    try:
        return abs(_AQI_ORDER.index(a) - _AQI_ORDER.index(b)) <= max_steps
    except (ValueError, TypeError):
        log.debug("error ignored in _cat_adjacent", exc_info=True)
        return False


@register("aqi.consistency")
def op_aqi_consistency(ctx, step):
    val = resolve(ctx, step["value"])
    if not isinstance(val, str):
        return 0.0
    aqi = _parse_aqi_number(val)
    drawn_cat = _parse_category(val)
    if aqi is None or drawn_cat is None:
        return 0.0

    live_aqi = as_float(resolve(ctx, step["live_aqi"]))
    live_cat = resolve(ctx, step["live_category"])
    if live_aqi is None or live_cat is None:
        return 0.0
    band = as_float(resolve(ctx, step.get("aqi_band", 15.0)), 15.0)
    internal_adjacent = int(as_float(resolve(ctx, step.get("internal_adjacent", 1)), 1) or 0)

    number_cat = _aqi_category(aqi)
    if number_cat is None:
        return 0.0
    if not (_cat_adjacent(drawn_cat, number_cat, 1) if internal_adjacent else drawn_cat == number_cat):
        return 0.0
    if number_cat != str(live_cat).strip().lower():
        return 0.0
    return 1.0 if abs(aqi - live_aqi) <= band else 0.0


def _to_floats(seq):
    if seq is None or isinstance(seq, dict):
        return None
    if isinstance(seq, str):
        seq = re.split(r"[\s,;]+", seq.strip())
    out = [as_float(x) for x in seq]
    return out


def _signs(seq):
    return [(1 if seq[i + 1] > seq[i] else (-1 if seq[i + 1] < seq[i] else 0))
            for i in range(len(seq) - 1)]


@register("compare.seq_band")
def op_compare_seq_band(ctx, step):
    v = _to_floats(resolve(ctx, step["value"]))
    t = _to_floats(resolve(ctx, step["target"]))
    if not v or not t or None in v or None in t:
        return 0.0
    n = min(len(v), len(t))
    if n == 0 or len(v) != len(t):
        return 0.0
    core = as_float(resolve(ctx, step.get("core", 0.0)), 0.0)
    margin = as_float(resolve(ctx, step.get("margin", 1e-9)), 1e-9)
    shape_frac = as_float(resolve(ctx, step.get("shape_frac", 0.0)), 0.0)
    shape_delta = as_float(resolve(ctx, step.get("shape_delta", 0.0)), 0.0)

    value_term = sum(_band(v[i], t[i], core, margin) for i in range(n)) / n

    ds, ts = _signs(v[:n]), _signs(t[:n])
    graded = [(d, tv) for d, tv, delta in
              zip(ds, ts, [abs(t[i + 1] - t[i]) for i in range(n - 1)]) if delta >= shape_delta]
    if not graded:
        shape_credit = 1.0
    else:
        agree = sum(1 for d, tv in graded if d == tv) / len(graded)
        thr = shape_frac if shape_frac > 0 else 1e-9
        shape_credit = min(1.0, agree / thr)

    return round(min(1.0, max(0.0, value_term * shape_credit)), 4)


_PHASE_ORDER = ["new moon", "waxing crescent", "first quarter", "waxing gibbous",
                "full moon", "waning gibbous", "last quarter", "waning crescent"]
_WAXING = {"waxing crescent", "first quarter", "waxing gibbous"}
_HINGE = {"new moon", "full moon"}


@register("compare.phase_neighbor")
def op_compare_phase_neighbor(ctx, step):
    """Graded moon-phase match: exact phase -> 1.0, a neighbouring phase -> `neighbor` (default 0.5)."""
    val = resolve(ctx, step["value"])
    tgt = resolve(ctx, step["target"])
    if not isinstance(val, str) or not isinstance(tgt, str):
        return 0.0
    v, t = val.strip().lower(), tgt.strip().lower()
    if v == t:
        return 1.0
    if v not in _PHASE_ORDER or t not in _PHASE_ORDER:
        return 0.0
    i, j = _PHASE_ORDER.index(v), _PHASE_ORDER.index(t)
    d = min(abs(i - j), 8 - abs(i - j))
    if d != 1:
        return 0.0
    neighbor = as_float(resolve(ctx, step.get("neighbor", 0.5)), 0.5)
    if v in _HINGE or t in _HINGE:
        return round(neighbor, 4)
    return round(neighbor, 4) if ((v in _WAXING) == (t in _WAXING)) else 0.0
