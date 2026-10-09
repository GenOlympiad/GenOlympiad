# shared code: code_0e0b685fd080



def _frac(b):
    return 1.0 if b else 0.0


def expand(n_bars, rep_start, endings):
    n = int(n_bars)
    rs = max(1, int(rep_start))
    eds = [(int(a), int(b)) for a, b in endings]
    if not eds:
        return list(range(1, n + 1))
    a1 = eds[0][0]
    order = list(range(1, rs))
    for (a, b) in eds:
        order += list(range(rs, a1))
        order += list(range(a, b + 1))
    order += list(range(eds[-1][1] + 1, n + 1))
    return order


def _mid(b):
    ymin, xmin, ymax, xmax = [float(v) for v in list(b)[:4]]
    return ((min(ymin, ymax) + max(ymin, ymax)) / 2.0,
            (min(xmin, xmax) + max(xmin, xmax)) / 2.0)


def layout(nums, staff):
    g = (nums.get("geometry") if isinstance(nums, dict) else None) or []
    sg = (staff.get("geometry") if isinstance(staff, dict) else None) or []
    if len(g) < 2 or not sg or len(sg[0]) < 4:
        return {"no_read": True, "reason": "n_numbers_%d" % len(g),
                "boundary_boxes": [], "bar_boxes": [], "n_bars": len(g)}
    ymin, xmin, ymax, xmax = [float(v) for v in list(sg[0])[:4]]
    sy0, sy1 = min(ymin, ymax), max(ymin, ymax)
    sx0, sx1 = min(xmin, xmax), max(xmin, xmax)
    cx = sorted(_mid(b)[1] for b in g)
    ny = min(min(float(v) for v in (b[0], b[2])) for b in g)
    ny1 = max(max(float(v) for v in (b[0], b[2])) for b in g)
    n = len(cx)
    edges = [sx0] + [(cx[i] + cx[i + 1]) / 2.0 for i in range(n - 1)] + [sx1]
    bw = (sx1 - sx0) / float(max(1, n))
    sy0 = max(sy0, ny1)
    sy1 = min(sy1, sy0 + 1.2 * bw)
    h = max(1.0, sy1 - sy0)
    top = max(0.0, min(sy0 - 2.2 * h, ny - 1.4 * h))
    bot = sy1 + 0.4 * h
    bnd, bars = [], []
    for e in edges:
        bnd.append([round(sy0 - 0.5 * h, 1), round(e - 0.30 * bw, 1),
                    round(sy1 + 0.5 * h, 1), round(e + 0.30 * bw, 1)])
    for i in range(n):
        bars.append([round(top, 1), round(edges[i], 1), round(bot, 1), round(edges[i + 1], 1)])
    return {"no_read": False, "boundary_boxes": bnd, "bar_boxes": bars, "n_bars": n,
            "n_boundaries": len(bnd)}


def _side(a):
    if a is None:
        return None
    t = str(a).strip().lower()
    if "right" in t:
        return "right"
    if "left" in t:
        return "left"
    if "both" in t:
        return "both"
    return None


def _yes(a):
    if a is None:
        return False
    return str(a).strip().lower().startswith("y")


def _num(a):
    import re
    if a is None:
        return None
    m = re.search(r"\d+", str(a))
    return int(m.group(0)) if m else None


def read_score(lay, reps, brs, nums_read):
    if lay.get("no_read"):
        return {"no_read": True, "reason": lay.get("reason")}
    n = int(lay["n_bars"])
    ra = (reps.get("answers") if isinstance(reps, dict) else None) or []
    ba = (brs.get("answers") if isinstance(brs, dict) else None) or []
    na = (nums_read.get("answers") if isinstance(nums_read, dict) else None) or []
    rep_start, rep_ends, n_dot_pairs = 1, [], 0
    for k in range(min(len(ra), n + 1)):
        s = _side(ra[k])
        if s in ("right", "both"):
            rep_start = max(rep_start, k + 1)
            n_dot_pairs += 1
        elif s == "left":
            rep_ends.append(k)
            n_dot_pairs += 1
    endings, cur, cur_num = [], None, None
    for i in range(n):
        has = _yes(ba[i]) if i < len(ba) else False
        num = _num(na[i]) if i < len(na) else None
        if not has:
            if cur:
                endings.append(cur)
            cur, cur_num = None, None
            continue
        if cur and (num is None or num == cur_num):
            cur = (cur[0], i + 1)
        else:
            if cur:
                endings.append(cur)
            cur, cur_num = (i + 1, i + 1), num
    if cur:
        endings.append(cur)
    order = expand(n, rep_start, endings)
    return {"no_read": False, "n_bars_measured": n, "repeat_start_bar": int(rep_start),
            "repeat_end_bars": sorted(set(rep_ends)), "endings": [list(e) for e in endings],
            "play_order": order, "n_dot_pairs": n_dot_pairs, "n_thick": n_dot_pairs}


def system_readable(lay, reps, brs, nums_read):
    """Score 1 if the score system could be read at all, else 0."""
    score = read_score(lay, reps, brs, nums_read)
    return {"frac": 0.0 if score.get("no_read") else 1.0}


def score_play_order(lay, reps, brs, nums_read, want_order):
    """Score 1 if the bar order played through the repeats matches the reference order."""
    score = read_score(lay, reps, brs, nums_read)
    if score.get("no_read"):
        return {"frac": 0.0, "reason": score.get("reason")}
    got = [int(v) for v in score["play_order"]]
    want = [int(v) for v in want_order]
    return {"frac": _frac(got == want), "measured": got, "expected": want}


def score_repeat_start(lay, reps, brs, nums_read, want_start):
    """Score 1 if the bar where the repeat starts matches the reference bar."""
    score = read_score(lay, reps, brs, nums_read)
    if score.get("no_read"):
        return {"frac": 0.0, "reason": score.get("reason")}
    return {"frac": _frac(int(score["repeat_start_bar"]) == int(want_start)),
            "measured": score["repeat_start_bar"], "expected": int(want_start)}


def score_endings(lay, reps, brs, nums_read, want_endings):
    """The share of reference first and second endings read with the right bar spans."""
    score = read_score(lay, reps, brs, nums_read)
    if score.get("no_read"):
        return {"frac": 0.0, "reason": score.get("reason")}
    got = [tuple(int(v) for v in e) for e in score["endings"]]
    want = [tuple(int(v) for v in e) for e in want_endings]
    n_match = 0
    for i, w in enumerate(want):
        if i < len(got) and got[i] == w:
            n_match += 1
    return {"frac": round(n_match / float(max(1, len(want))), 4),
            "measured": [list(e) for e in got], "expected": [list(e) for e in want]}


def score_bar_count(lay, reps, brs, nums_read, n_bars):
    """Score 1 if the number of bars measured equals the reference count."""
    score = read_score(lay, reps, brs, nums_read)
    if score.get("no_read"):
        return {"frac": 0.0, "reason": score.get("reason")}
    return {"frac": _frac(int(score["n_bars_measured"]) == int(n_bars)),
            "measured": score["n_bars_measured"], "expected": int(n_bars)}


def repeat_marks_drawn(lay, reps, brs, nums_read, want_endings):
    """Score 1 if repeat dots, a thick bar line and the right number of ending brackets appear."""
    score = read_score(lay, reps, brs, nums_read)
    if score.get("no_read"):
        return {"frac": 0.0, "reason": score.get("reason")}
    ok = (score["n_dot_pairs"] >= 1 and len(score["endings"]) == len(want_endings) and score["n_thick"] >= 1)
    return {"frac": _frac(ok), "n_dot_pairs": score["n_dot_pairs"],
            "n_brackets": len(score["endings"]), "n_thick": score["n_thick"]}


def as_score(value):
    return float(value or 0.0)

# end of code_0e0b685fd080

# code: layout_for_system_readable_code

def layout_for_system_readable(bars, staff):
    """Order the bar boxes left to right and lay out a box per bar line and per bar."""
    def _f(b):
        try: v = [float(x) for x in list(b)[:4]]
        except Exception: return None
        return None if len(v) != 4 or v[1] == v[3] or v[0] == v[2] else [min(v[0], v[2]), min(v[1], v[3]), max(v[0], v[2]), max(v[1], v[3])]
    nrm = lambda nd: [r for r in (_f(b) for b in ((nd or {}).get("geometry") or [])) if r]; med = lambda xs: (lambda s: float(s[len(s) // 2]) if len(s) % 2 else 0.5 * (s[len(s) // 2 - 1] + s[len(s) // 2]))(sorted(xs))
    g = sorted(nrm(bars), key=lambda b: 0.5 * (b[1] + b[3])); sg = nrm(staff); n = len(g)
    if n < 2 or g[-1][3] <= g[0][1]: return {"no_read": True, "refused": True, "reason": ("n_bars_%d" % n) if n < 2 else "bars_have_no_width", "boundary_boxes": [], "bar_boxes": [], "n_bars": n}
    a0, a1 = med([b[0] for b in g]), med([b[2] for b in g]); sy0, sy1 = (sg[0][0], sg[0][2]) if (a1 <= a0 and sg) else (a0, a1); sx0, sx1 = g[0][1], g[-1][3]
    edges = [sx0] + [0.5 * (g[i][3] + g[i + 1][1]) for i in range(n - 1)] + [sx1]; bar_width = (sx1 - sx0) / float(max(1, n)); h = max(1.0, sy1 - sy0)
    boundaries = [[round(max(0.0, sy0 - 0.5 * h), 1), round(max(0.0, e - 0.30 * bar_width), 1), round(min(1000.0, sy1 + 0.5 * h), 1), round(min(1000.0, e + 0.30 * bar_width), 1)] for e in edges]
    return {"no_read": False, "boundary_boxes": boundaries, "bar_boxes": [[round(max(0.0, sy0 - 2.2 * h), 1), round(edges[i], 1), round(min(1000.0, sy1 + 0.4 * h), 1), round(edges[i + 1], 1)] for i in range(n)], "n_bars": n, "n_boundaries": len(boundaries)}

# end of layout_for_system_readable_code

# code: layout_for_bar_count_code

def layout_for_bar_count(bars, staff):
    """Order the bar boxes left to right and lay out a box per bar line and per bar."""
    def _f(b):
        try: v = [float(x) for x in list(b)[:4]]
        except Exception: return None
        return None if len(v) != 4 or v[1] == v[3] or v[0] == v[2] else [min(v[0], v[2]), min(v[1], v[3]), max(v[0], v[2]), max(v[1], v[3])]
    nrm = lambda nd: [r for r in (_f(b) for b in ((nd or {}).get("geometry") or [])) if r]; med = lambda xs: (lambda s: float(s[len(s) // 2]) if len(s) % 2 else 0.5 * (s[len(s) // 2 - 1] + s[len(s) // 2]))(sorted(xs))
    g = sorted(nrm(bars), key=lambda b: 0.5 * (b[1] + b[3])); sg = nrm(staff); n = len(g)
    if n < 2 or g[-1][3] <= g[0][1]: return {"no_read": True, "refused": True, "reason": ("n_bars_%d" % n) if n < 2 else "bars_have_no_width", "boundary_boxes": [], "bar_boxes": [], "n_bars": n}
    a0, a1 = med([b[0] for b in g]), med([b[2] for b in g]); sy0, sy1 = (sg[0][0], sg[0][2]) if (a1 <= a0 and sg) else (a0, a1); sx0, sx1 = g[0][1], g[-1][3]
    edges = [sx0] + [0.5 * (g[i][3] + g[i + 1][1]) for i in range(n - 1)] + [sx1]; bar_width = (sx1 - sx0) / float(max(1, n)); h = max(1.0, sy1 - sy0)
    boundaries = [[round(max(0.0, sy0 - 0.5 * h), 1), round(max(0.0, e - 0.30 * bar_width), 1), round(min(1000.0, sy1 + 0.5 * h), 1), round(min(1000.0, e + 0.30 * bar_width), 1)] for e in edges]
    return {"no_read": False, "boundary_boxes": boundaries, "bar_boxes": [[round(max(0.0, sy0 - 2.2 * h), 1), round(edges[i], 1), round(min(1000.0, sy1 + 0.4 * h), 1), round(edges[i + 1], 1)] for i in range(n)], "n_bars": n, "n_boundaries": len(boundaries)}

# end of layout_for_bar_count_code

# code: layout_for_repeat_start_code

def layout_for_repeat_start(bars, staff):
    """Order the bar boxes left to right and lay out a box per bar line and per bar."""
    def _f(b):
        try: v = [float(x) for x in list(b)[:4]]
        except Exception: return None
        return None if len(v) != 4 or v[1] == v[3] or v[0] == v[2] else [min(v[0], v[2]), min(v[1], v[3]), max(v[0], v[2]), max(v[1], v[3])]
    nrm = lambda nd: [r for r in (_f(b) for b in ((nd or {}).get("geometry") or [])) if r]; med = lambda xs: (lambda s: float(s[len(s) // 2]) if len(s) % 2 else 0.5 * (s[len(s) // 2 - 1] + s[len(s) // 2]))(sorted(xs))
    g = sorted(nrm(bars), key=lambda b: 0.5 * (b[1] + b[3])); sg = nrm(staff); n = len(g)
    if n < 2 or g[-1][3] <= g[0][1]: return {"no_read": True, "refused": True, "reason": ("n_bars_%d" % n) if n < 2 else "bars_have_no_width", "boundary_boxes": [], "bar_boxes": [], "n_bars": n}
    a0, a1 = med([b[0] for b in g]), med([b[2] for b in g]); sy0, sy1 = (sg[0][0], sg[0][2]) if (a1 <= a0 and sg) else (a0, a1); sx0, sx1 = g[0][1], g[-1][3]
    edges = [sx0] + [0.5 * (g[i][3] + g[i + 1][1]) for i in range(n - 1)] + [sx1]; bar_width = (sx1 - sx0) / float(max(1, n)); h = max(1.0, sy1 - sy0)
    boundaries = [[round(max(0.0, sy0 - 0.5 * h), 1), round(max(0.0, e - 0.30 * bar_width), 1), round(min(1000.0, sy1 + 0.5 * h), 1), round(min(1000.0, e + 0.30 * bar_width), 1)] for e in edges]
    return {"no_read": False, "boundary_boxes": boundaries, "bar_boxes": [[round(max(0.0, sy0 - 2.2 * h), 1), round(edges[i], 1), round(min(1000.0, sy1 + 0.4 * h), 1), round(edges[i + 1], 1)] for i in range(n)], "n_bars": n, "n_boundaries": len(boundaries)}

# end of layout_for_repeat_start_code

# code: layout_for_ending_spans_code

def layout_for_ending_spans(bars, staff):
    """Order the bar boxes left to right and lay out a box per bar line and per bar."""
    def _f(b):
        try: v = [float(x) for x in list(b)[:4]]
        except Exception: return None
        return None if len(v) != 4 or v[1] == v[3] or v[0] == v[2] else [min(v[0], v[2]), min(v[1], v[3]), max(v[0], v[2]), max(v[1], v[3])]
    nrm = lambda nd: [r for r in (_f(b) for b in ((nd or {}).get("geometry") or [])) if r]; med = lambda xs: (lambda s: float(s[len(s) // 2]) if len(s) % 2 else 0.5 * (s[len(s) // 2 - 1] + s[len(s) // 2]))(sorted(xs))
    g = sorted(nrm(bars), key=lambda b: 0.5 * (b[1] + b[3])); sg = nrm(staff); n = len(g)
    if n < 2 or g[-1][3] <= g[0][1]: return {"no_read": True, "refused": True, "reason": ("n_bars_%d" % n) if n < 2 else "bars_have_no_width", "boundary_boxes": [], "bar_boxes": [], "n_bars": n}
    a0, a1 = med([b[0] for b in g]), med([b[2] for b in g]); sy0, sy1 = (sg[0][0], sg[0][2]) if (a1 <= a0 and sg) else (a0, a1); sx0, sx1 = g[0][1], g[-1][3]
    edges = [sx0] + [0.5 * (g[i][3] + g[i + 1][1]) for i in range(n - 1)] + [sx1]; bar_width = (sx1 - sx0) / float(max(1, n)); h = max(1.0, sy1 - sy0)
    boundaries = [[round(max(0.0, sy0 - 0.5 * h), 1), round(max(0.0, e - 0.30 * bar_width), 1), round(min(1000.0, sy1 + 0.5 * h), 1), round(min(1000.0, e + 0.30 * bar_width), 1)] for e in edges]
    return {"no_read": False, "boundary_boxes": boundaries, "bar_boxes": [[round(max(0.0, sy0 - 2.2 * h), 1), round(edges[i], 1), round(min(1000.0, sy1 + 0.4 * h), 1), round(edges[i + 1], 1)] for i in range(n)], "n_bars": n, "n_boundaries": len(boundaries)}

# end of layout_for_ending_spans_code

# code: layout_for_play_order_code

def layout_for_play_order(bars, staff):
    """Order the bar boxes left to right and lay out a box per bar line and per bar."""
    def _f(b):
        try: v = [float(x) for x in list(b)[:4]]
        except Exception: return None
        return None if len(v) != 4 or v[1] == v[3] or v[0] == v[2] else [min(v[0], v[2]), min(v[1], v[3]), max(v[0], v[2]), max(v[1], v[3])]
    nrm = lambda nd: [r for r in (_f(b) for b in ((nd or {}).get("geometry") or [])) if r]; med = lambda xs: (lambda s: float(s[len(s) // 2]) if len(s) % 2 else 0.5 * (s[len(s) // 2 - 1] + s[len(s) // 2]))(sorted(xs))
    g = sorted(nrm(bars), key=lambda b: 0.5 * (b[1] + b[3])); sg = nrm(staff); n = len(g)
    if n < 2 or g[-1][3] <= g[0][1]: return {"no_read": True, "refused": True, "reason": ("n_bars_%d" % n) if n < 2 else "bars_have_no_width", "boundary_boxes": [], "bar_boxes": [], "n_bars": n}
    a0, a1 = med([b[0] for b in g]), med([b[2] for b in g]); sy0, sy1 = (sg[0][0], sg[0][2]) if (a1 <= a0 and sg) else (a0, a1); sx0, sx1 = g[0][1], g[-1][3]
    edges = [sx0] + [0.5 * (g[i][3] + g[i + 1][1]) for i in range(n - 1)] + [sx1]; bar_width = (sx1 - sx0) / float(max(1, n)); h = max(1.0, sy1 - sy0)
    boundaries = [[round(max(0.0, sy0 - 0.5 * h), 1), round(max(0.0, e - 0.30 * bar_width), 1), round(min(1000.0, sy1 + 0.5 * h), 1), round(min(1000.0, e + 0.30 * bar_width), 1)] for e in edges]
    return {"no_read": False, "boundary_boxes": boundaries, "bar_boxes": [[round(max(0.0, sy0 - 2.2 * h), 1), round(edges[i], 1), round(min(1000.0, sy1 + 0.4 * h), 1), round(edges[i + 1], 1)] for i in range(n)], "n_bars": n, "n_boundaries": len(boundaries)}

# end of layout_for_play_order_code

# code: layout_for_volta_overlay_code

def layout_for_volta_overlay(bars, staff):
    """Order the bar boxes left to right and lay out a box per bar line and per bar."""
    def _f(b):
        try: v = [float(x) for x in list(b)[:4]]
        except Exception: return None
        return None if len(v) != 4 or v[1] == v[3] or v[0] == v[2] else [min(v[0], v[2]), min(v[1], v[3]), max(v[0], v[2]), max(v[1], v[3])]
    nrm = lambda nd: [r for r in (_f(b) for b in ((nd or {}).get("geometry") or [])) if r]; med = lambda xs: (lambda s: float(s[len(s) // 2]) if len(s) % 2 else 0.5 * (s[len(s) // 2 - 1] + s[len(s) // 2]))(sorted(xs))
    g = sorted(nrm(bars), key=lambda b: 0.5 * (b[1] + b[3])); sg = nrm(staff); n = len(g)
    if n < 2 or g[-1][3] <= g[0][1]: return {"no_read": True, "refused": True, "reason": ("n_bars_%d" % n) if n < 2 else "bars_have_no_width", "boundary_boxes": [], "bar_boxes": [], "n_bars": n}
    a0, a1 = med([b[0] for b in g]), med([b[2] for b in g]); sy0, sy1 = (sg[0][0], sg[0][2]) if (a1 <= a0 and sg) else (a0, a1); sx0, sx1 = g[0][1], g[-1][3]
    edges = [sx0] + [0.5 * (g[i][3] + g[i + 1][1]) for i in range(n - 1)] + [sx1]; bar_width = (sx1 - sx0) / float(max(1, n)); h = max(1.0, sy1 - sy0)
    boundaries = [[round(max(0.0, sy0 - 0.5 * h), 1), round(max(0.0, e - 0.30 * bar_width), 1), round(min(1000.0, sy1 + 0.5 * h), 1), round(min(1000.0, e + 0.30 * bar_width), 1)] for e in edges]
    return {"no_read": False, "boundary_boxes": boundaries, "bar_boxes": [[round(max(0.0, sy0 - 2.2 * h), 1), round(edges[i], 1), round(min(1000.0, sy1 + 0.4 * h), 1), round(edges[i + 1], 1)] for i in range(n)], "n_bars": n, "n_boundaries": len(boundaries)}

# end of layout_for_volta_overlay_code

# code: layout_for_repeat_form_code

def layout_for_repeat_form(bars, staff):
    """Order the bar boxes left to right and lay out a box per bar line and per bar."""
    def _f(b):
        try: v = [float(x) for x in list(b)[:4]]
        except Exception: return None
        return None if len(v) != 4 or v[1] == v[3] or v[0] == v[2] else [min(v[0], v[2]), min(v[1], v[3]), max(v[0], v[2]), max(v[1], v[3])]
    nrm = lambda nd: [r for r in (_f(b) for b in ((nd or {}).get("geometry") or [])) if r]; med = lambda xs: (lambda s: float(s[len(s) // 2]) if len(s) % 2 else 0.5 * (s[len(s) // 2 - 1] + s[len(s) // 2]))(sorted(xs))
    g = sorted(nrm(bars), key=lambda b: 0.5 * (b[1] + b[3])); sg = nrm(staff); n = len(g)
    if n < 2 or g[-1][3] <= g[0][1]: return {"no_read": True, "refused": True, "reason": ("n_bars_%d" % n) if n < 2 else "bars_have_no_width", "boundary_boxes": [], "bar_boxes": [], "n_bars": n}
    a0, a1 = med([b[0] for b in g]), med([b[2] for b in g]); sy0, sy1 = (sg[0][0], sg[0][2]) if (a1 <= a0 and sg) else (a0, a1); sx0, sx1 = g[0][1], g[-1][3]
    edges = [sx0] + [0.5 * (g[i][3] + g[i + 1][1]) for i in range(n - 1)] + [sx1]; bar_width = (sx1 - sx0) / float(max(1, n)); h = max(1.0, sy1 - sy0)
    boundaries = [[round(max(0.0, sy0 - 0.5 * h), 1), round(max(0.0, e - 0.30 * bar_width), 1), round(min(1000.0, sy1 + 0.5 * h), 1), round(min(1000.0, e + 0.30 * bar_width), 1)] for e in edges]
    return {"no_read": False, "boundary_boxes": boundaries, "bar_boxes": [[round(max(0.0, sy0 - 2.2 * h), 1), round(edges[i], 1), round(min(1000.0, sy1 + 0.4 * h), 1), round(edges[i + 1], 1)] for i in range(n)], "n_bars": n, "n_boundaries": len(boundaries)}

# end of layout_for_repeat_form_code
