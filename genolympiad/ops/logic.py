"""Comparison, combination and gating operators that turn reads into check results."""
from __future__ import annotations
from ._base import register, resolve, as_float, Fail
import logging

log = logging.getLogger(__name__)


@register("const")
def op_const(ctx, step):
    return resolve(ctx, step["value"]) if isinstance(step["value"], str) else step["value"]


@register("len")
def op_len(ctx, step):
    v = resolve(ctx, step["value"])
    return len(v) if v is not None else 0


def _band(v, t, core, margin, clamp_floor=0.0):
    if v is None or t is None:
        return 0.0
    d = abs(float(v) - float(t))
    margin = max(float(margin), 1e-9)
    frac = 1.0 - max(0.0, d - float(core)) / margin
    frac = min(1.0, max(float(clamp_floor), frac)) if frac > 0 else float(clamp_floor)
    return round(min(1.0, max(0.0, frac)), 4)


def band_bounds(ctx, step):
    t = as_float(resolve(ctx, step["target"]))
    base = abs(t) if t is not None else 0.0
    core = (as_float(resolve(ctx, step.get("core", step.get("core_abs", 0.0))), 0.0)
            + base * as_float(resolve(ctx, step.get("core_rel", 0.0)), 0.0))
    margin = (as_float(resolve(ctx, step.get("margin", step.get("margin_abs", 0.0))), 0.0)
              + base * as_float(resolve(ctx, step.get("margin_rel", 0.0)), 0.0))
    if margin <= 0:
        margin = 1e-9
    clamp_floor = as_float(resolve(ctx, step.get("clamp_floor", 0.0)), 0.0)
    return t, core, margin, clamp_floor


@register("compare.band")
def op_compare_band(ctx, step):
    v = as_float(resolve(ctx, step["value"]))
    t, core, margin, clamp_floor = band_bounds(ctx, step)
    return _band(v, t, core, margin, clamp_floor)


@register("compare.tol")
def op_compare_tol(ctx, step):
    v = as_float(resolve(ctx, step["value"]))
    t = as_float(resolve(ctx, step["target"]))
    if v is None or t is None:
        return 0.0
    return 1.0 if abs(v - t) <= as_float(resolve(ctx, step["tol"])) else 0.0


_MULT_EQUIV = {"x", "×", "✕", "·", "∗"}
_COLOR_WORD_TO_LETTER = {
    "white": "w", "red": "r", "yellow": "y", "orange": "o",
    "cyan": "c", "magenta": "m", "black": "k",
}
_SUPERSUB_DIGIT_MAP = str.maketrans(
    "⁰¹²³⁴⁵⁶⁷⁸⁹"
    "₀₁₂₃₄₅₆₇₈₉",
    "0123456789" "0123456789",
)


def _canon_equal_token(s: str) -> str:
    import re as _re2
    if isinstance(s, bool):
        return str(s).casefold()
    if isinstance(s, (int, float)) or _re2.fullmatch(r"\s*[+-]?\d+(?:\.\d+)?\s*", str(s) or ""):
        try:
            f = float(s)
            return str(int(f)) if f == int(f) else repr(f).rstrip("0").rstrip(".")
        except (ValueError, TypeError, OverflowError):
            log.debug("error ignored in _canon_equal_token", exc_info=True)
            pass
    t = str(s).strip().casefold()
    t = t.translate(_SUPERSUB_DIGIT_MAP)
    t = _re2.sub(r"\s+", " ", t)
    t = t.strip(" \t\r\n.,;:!?'\"")
    if t in _MULT_EQUIV:
        return "*"
    if t in _COLOR_WORD_TO_LETTER:
        return _COLOR_WORD_TO_LETTER[t]
    return t


@register("compare.equals")
def op_compare_equals(ctx, step):
    a = resolve(ctx, step["value"])
    b = resolve(ctx, step["target"])
    if a is None:
        return 0.0
    return 1.0 if _canon_equal_token(a) == _canon_equal_token(b) else 0.0


@register("compare.grid")
def op_compare_grid(ctx, step):
    """Fraction of grid cells matching elementwise between value and target (both list-of-lists)."""
    a = resolve(ctx, step["value"])
    b = resolve(ctx, step["target"])
    if not isinstance(a, (list, tuple)) or not isinstance(b, (list, tuple)):
        return 0.0
    def _cell(v):
        return str(v).strip().casefold()
    ign = resolve(ctx, step.get("ignore"))
    ign = None if ign is None else _cell(ign)
    total = ok = 0
    cells = []
    for i, brow in enumerate(b):
        if not isinstance(brow, (list, tuple)):
            brow = [brow]
        arow = a[i] if (i < len(a) and isinstance(a[i], (list, tuple))) else []
        for j, bv in enumerate(brow):
            av = _cell(arow[j]) if j < len(arow) else None
            bvc = _cell(bv)
            if ign is not None and bvc == ign and (av is None or av == ign):
                cells.append((i, j, None, bv, "skipped"))
                continue
            total += 1
            hit = av is not None and av == bvc
            ok += int(hit)
            cells.append((i, j, (arow[j] if j < len(arow) else None), bv,
                          "pass" if hit else "fail"))
    return round(ok / total, 4) if total else 0.0


def _f1(a, b):
    a, b = set(a), set(b)
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    return 2 * len(a & b) / (len(a) + len(b))


def _as_items(x):
    if x is None:
        return []
    if isinstance(x, str):
        import re as _re
        raw = _re.split(r"[,;\n]+", x)
    elif isinstance(x, (list, tuple)):
        raw = list(x)
    else:
        raw = [x]
    return [str(t).strip().casefold() for t in raw if str(t).strip()]


@register("compare.set")
def op_compare_set(ctx, step):
    """Graded set overlap (F1)."""
    found_boxes = set(_as_items(resolve(ctx, step["value"])))
    gt = set(_as_items(resolve(ctx, step["target"])))
    sel = step.get("selective")
    if sel is not None:
        sel = set(_as_items(sel))
        return round(_f1(found_boxes & sel, gt & sel), 4)
    return round(_f1(found_boxes, gt), 4)


@register("compare.text_f1")
def op_compare_text_f1(ctx, step):
    import re as _re
    import difflib

    def _toks(x):
        if x is None:
            return []
        if isinstance(x, (list, tuple)):
            raw = list(x)
        else:
            raw = _re.split(r"\s+", str(x).strip())
        out = []
        for t in raw:
            t = str(t).strip().lower()
            t = _re.sub(r"^[^\w']+", "", t)
            t = _re.sub(r"[^\w']+$", "", t)
            if t:
                out.append(t)
        return out

    a = _toks(resolve(ctx, step["value"]))
    b = _toks(resolve(ctx, step["target"]))
    if not b:
        return 0.0
    sm = difflib.SequenceMatcher(a=a, b=b, autojunk=False)
    matched = sum(blk.size for blk in sm.get_matching_blocks())
    prec = matched / len(a) if a else 0.0
    rec = matched / len(b) if b else 0.0
    f1 = (2 * prec * rec / (prec + rec)) if (prec + rec) else 0.0
    if step.get("raw"):
        return round(f1, 4)
    core = as_float(resolve(ctx, step.get("core", 1.0)), 1.0)
    margin = max(as_float(resolve(ctx, step.get("margin", 1e-9)), 1e-9), 1e-9)
    frac = 1.0 if f1 >= core else max(0.0, (f1 - (core - margin)) / margin)
    return round(min(1.0, max(0.0, frac)), 4)


@register("compare.min")
def op_compare_min(ctx, step):
    """Min of a list of fractions (weakest-link sub-score)."""
    vals = [as_float(resolve(ctx, x), 0.0) for x in (resolve(ctx, step["values"]) or [])]
    return round(min(vals), 4) if vals else 0.0


@register("time.to_minutes")
def op_time_to_minutes(ctx, step):
    """Parse a clock time out of a reader answer -> minutes past midnight (0-1439)."""
    import re as _re
    val = resolve(ctx, step["value"])
    if val is None:
        return None
    s = str(val).strip().lower()
    m = _re.search(r"(\d{1,2})\s*[:h.]\s*(\d{2})\s*(am|pm|a\.m\.|p\.m\.)?", s)
    if m:
        hh, mm = int(m.group(1)), int(m.group(2))
        ap = (m.group(3) or "").replace(".", "")
        if ap == "pm" and hh != 12:
            hh += 12
        elif ap == "am" and hh == 12:
            hh = 0
        if 0 <= hh <= 23 and 0 <= mm <= 59:
            return hh * 60 + mm
        return None
    v = as_float(s)
    if v is not None and 0 <= v <= 1439:
        return int(v)
    return None


@register("compare.compass")
def op_compare_compass(ctx, step):
    v = as_float(resolve(ctx, step["value"]))
    t = as_float(resolve(ctx, step["target"]))
    if v is None or t is None:
        return 0.0
    d = abs((v - t + 180.0) % 360.0 - 180.0)
    return _band(d, 0.0, as_float(resolve(ctx, step.get("core", 0.0)), 0.0),
                 as_float(resolve(ctx, step.get("margin", 1e-9)), 1e-9))


@register("category.adjacent")
def op_category_adjacent(ctx, step):
    """Ordinal-scale nearness: value and target are ranks or members of an ordered `scale`."""
    v = resolve(ctx, step["value"])
    t = resolve(ctx, step["target"])
    scale = step.get("scale")
    if scale:
        try:
            v, t = scale.index(v), scale.index(t)
        except ValueError:
            log.debug("error ignored in op_category_adjacent", exc_info=True)
            return 0.0
    vi, ti = as_float(v), as_float(t)
    if vi is None or ti is None:
        return 0.0
    steps = abs(vi - ti)
    mx = float(step.get("max_steps", 1))
    return round(max(0.0, 1.0 - steps / mx), 4)


@register("order.match")
def op_order_match(ctx, step):
    v = _as_items(resolve(ctx, step["value"]))
    t = _as_items(resolve(ctx, step["target"]))
    common = [x for x in t if x in v]
    if len(common) < 2:
        return 1.0 if v == t else 0.0
    rv = {x: v.index(x) for x in common}
    rt = {x: t.index(x) for x in common}
    conc = disc = 0
    for i in range(len(common)):
        for j in range(i + 1, len(common)):
            a, b = common[i], common[j]
            s = (rv[a] - rv[b]) * (rt[a] - rt[b])
            if s > 0:
                conc += 1
            elif s < 0:
                disc += 1
    tot = conc + disc
    return round(conc / tot, 4) if tot else 1.0


@register("trend.match")
def op_trend_match(ctx, step):
    v = resolve(ctx, step["value"]) or []
    t = resolve(ctx, step["target"]) or []
    md = float(step.get("min_delta", 0.0))

    def signs(seq):
        seq = [as_float(x) for x in seq]
        out = []
        for a, b in zip(seq, seq[1:]):
            if a is None or b is None:
                out.append(None)
            else:
                out.append(1 if b - a > md else (-1 if a - b > md else 0))
        return out
    sv, st = signs(v), signs(t) if all(isinstance(x, (int, float)) for x in t) else [1 if s == "up" else (-1 if s == "down" else 0) for s in t]
    n = min(len(sv), len(st))
    if n == 0:
        return 0.0
    ok = sum(1 for i in range(n) if sv[i] == st[i])
    return round(ok / n, 4)


def _refusal_owner(ctx, flag):
    if not isinstance(flag, str) or "." not in flag:
        return None
    owner = resolve(ctx, flag.rsplit(".", 1)[0])
    return owner if isinstance(owner, dict) else None


def _is_evaluator_refusal(ctx, flag):
    owner = _refusal_owner(ctx, flag)
    return bool(owner) and owner.get("refused") is True


def _flag_diagnosis(ctx, flag):
    return ""


@register("guard.fail")
def op_guard_fail(ctx, step):
    for flag in step.get("when", []):
        if resolve(ctx, flag):
            return Fail(flag,
                        kind=("evaluator" if _is_evaluator_refusal(ctx, flag) else "crash"),
                        diagnosis=_flag_diagnosis(ctx, flag))
    return None


@register("combine.and")
def op_combine_and(ctx, step):
    vals = [as_float(resolve(ctx, x), 0.0) for x in (resolve(ctx, step["values"]) or [])]
    out = 1.0
    for x in vals:
        out *= x
    return round(out, 4)


@register("combine.or")
def op_combine_or(ctx, step):
    vals = [as_float(resolve(ctx, x), 0.0) for x in (resolve(ctx, step["values"]) or [])]
    return round(max(vals) if vals else 0.0, 4)
