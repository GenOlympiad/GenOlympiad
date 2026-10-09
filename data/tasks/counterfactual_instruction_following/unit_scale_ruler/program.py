# shared code: code_anchorgrid

import math
import struct


def ag_wh(image):
    try:
        if hasattr(image, "size"):
            w, h = image.size
            return float(w), float(h)
    except Exception:
        pass
    try:
        fh = open(str(image), "rb")
        try:
            head = fh.read(4096)
        finally:
            fh.close()
    except Exception:
        return None
    if head[:8] == b"\x89PNG\r\n\x1a\n":
        try:
            w, h = struct.unpack(">II", head[16:24])
            return float(w), float(h)
        except Exception:
            return None
    if head[:2] == b"\xff\xd8":
        i = 2
        while i + 9 < len(head):
            if head[i] != 0xFF:
                break
            mk = head[i + 1]
            try:
                ln = struct.unpack(">H", head[i + 2:i + 4])[0]
            except Exception:
                return None
            if 0xC0 <= mk <= 0xCF and mk not in (0xC4, 0xC8, 0xCC):
                try:
                    h, w = struct.unpack(">HH", head[i + 5:i + 9])
                    return float(w), float(h)
                except Exception:
                    return None
            i += 2 + ln
    return None


def ag_anchor(fb, i=0):
    g = fb
    if isinstance(fb, dict):
        if fb.get("refused") or fb.get("unreadable"):
            return None
        g = fb.get("geometry")
    if not g:
        return None
    if isinstance(g[0], (int, float)):
        g = [g]
    if i >= len(g):
        return None
    b = [float(v) for v in g[i][:4]]
    y0, x0, y1, x1 = min(b[0], b[2]), min(b[1], b[3]), max(b[0], b[2]), max(b[1], b[3])
    return [y0, x0, y1, x1]


def _ag_clip(v, lo, hi):
    return lo if v < lo else (hi if v > hi else v)


def _ag_pack(cells_px, W, H, pad_frac):
    M = float(max(W, H))
    boxes, rects = [], []
    for (x0, y0, x1, y1) in cells_px:
        w, h = max(1.0, x1 - x0), max(1.0, y1 - y0)
        g = float(pad_frac) * max(w, h)
        bx0, by0 = _ag_clip(x0 - g, 0.0, W), _ag_clip(y0 - g, 0.0, H)
        bx1, by1 = _ag_clip(x1 + g, 0.0, W), _ag_clip(y1 + g, 0.0, H)
        boxes.append([by0 * 1000.0 / H, bx0 * 1000.0 / W,
                      by1 * 1000.0 / H, bx1 * 1000.0 / W])
        rects.append([(x0 + x1) / 2.0 / M, (y0 + y1) / 2.0 / M, w / M, h / M])
    return boxes, rects


def _ag_frame(W, H):
    M = float(max(W, H))
    return ([[0.0, 0.0], [W / M, 0.0], [W / M, H / M], [0.0, H / M]],
            [[0.0, 0.0], [W, 0.0], [W, H], [0.0, H]])


def ag_plan(image, fb, rows=1, cols=1, sub=None, pad=0.06, inset=0.02, i=0,
            min_side_px=24.0, labels=None):
    a = ag_anchor(fb, i)
    if a is None:
        return {"no_plan": True, "refused": True,
                "reason": "the container was never boxed"}
    wh = ag_wh(image)
    if not wh:
        return {"no_plan": True, "refused": True,
                "reason": "the picture's size could not be read"}
    W, H = wh
    rows, cols = max(1, int(rows)), max(1, int(cols))
    ax0, ay0 = a[1] * W / 1000.0, a[0] * H / 1000.0
    ax1, ay1 = a[3] * W / 1000.0, a[2] * H / 1000.0
    if sub:
        t, l, b, r = [float(v) for v in sub[:4]]
        aw, ah = ax1 - ax0, ay1 - ay0
        ax0, ax1 = ax0 + l * aw, ax0 + r * aw
        ay0, ay1 = ay0 + t * ah, ay0 + b * ah
    aw, ah = ax1 - ax0, ay1 - ay0
    if aw < min_side_px or ah < min_side_px:
        return {"no_plan": True, "refused": True, "anchor": a,
                "reason": "the container box is too small to cut into cells"}
    cw, ch = aw / float(cols), ah / float(rows)
    if min(cw, ch) < 4.0:
        return {"no_plan": True, "refused": True, "anchor": a,
                "reason": "the cells would be smaller than a few pixels"}
    cells_px, keys = [], []
    ix, iy = float(inset) * cw, float(inset) * ch
    for r_ in range(rows):
        for c_ in range(cols):
            x0 = ax0 + c_ * cw + ix
            x1 = ax0 + (c_ + 1) * cw - ix
            y0 = ay0 + r_ * ch + iy
            y1 = ay0 + (r_ + 1) * ch - iy
            cells_px.append([x0, y0, x1, y1])
            keys.append([r_, c_])
    boxes, rects = _ag_pack(cells_px, W, H, pad)
    ref, found_boxes = _ag_frame(W, H)
    out = {"no_plan": False, "reason": "", "rows": rows, "cols": cols, "n": rows * cols,
           "frame": [W, H], "anchor": a, "anchor_px": [ax0, ay0, ax1, ay1],
           "cells": {"geometry": boxes}, "boxes": boxes, "rects": rects, "keys": keys,
           "cells_px": cells_px, "ref_anchors": ref, "found_anchors": found_boxes,
           "cell_w_px": cw, "cell_h_px": ch}
    if labels:
        out["labels"] = [str(x) for x in labels][:rows * cols]
    return out


def ag_sectors(image, fb, n, start_deg=-90.0, clockwise=True, r_in=0.55, r_out=0.95,
               span_frac=0.9, pad=0.06, i=0, min_side_px=40.0):
    a = ag_anchor(fb, i)
    if a is None:
        return {"no_plan": True, "refused": True, "reason": "the dial was never boxed"}
    wh = ag_wh(image)
    if not wh:
        return {"no_plan": True, "reason": "the picture's size could not be read"}
    W, H = wh
    n = max(1, int(n))
    ax0, ay0 = a[1] * W / 1000.0, a[0] * H / 1000.0
    ax1, ay1 = a[3] * W / 1000.0, a[2] * H / 1000.0
    if (ax1 - ax0) < min_side_px or (ay1 - ay0) < min_side_px:
        return {"no_plan": True, "refused": True, "anchor": a,
                "reason": "the dial box is too small to cut into sectors"}
    cx, cy = (ax0 + ax1) / 2.0, (ay0 + ay1) / 2.0
    rx, ry = (ax1 - ax0) / 2.0, (ay1 - ay0) / 2.0
    step = 360.0 / float(n)
    sgn = 1.0 if clockwise else -1.0
    cells_px, angs = [], []
    half = 0.5 * step * float(span_frac)
    for k in range(n):
        mid = float(start_deg) + sgn * step * k
        pts = []
        for da in (-half, 0.0, half):
            th = math.radians(mid + da)
            for rr in (float(r_in), float(r_out)):
                pts.append((cx + rx * rr * math.cos(th), cy + ry * rr * math.sin(th)))
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        cells_px.append([_ag_clip(min(xs), 0.0, W), _ag_clip(min(ys), 0.0, H),
                         _ag_clip(max(xs), 0.0, W), _ag_clip(max(ys), 0.0, H)])
        angs.append(mid % 360.0)
    boxes, rects = _ag_pack(cells_px, W, H, pad)
    ref, found_boxes = _ag_frame(W, H)
    return {"no_plan": False, "reason": "", "rows": 1, "cols": n, "n": n,
            "frame": [W, H], "anchor": a, "centre_px": [cx, cy], "radius_px": [rx, ry],
            "angles_deg": angs, "cells": {"geometry": boxes}, "boxes": boxes, "rects": rects,
            "keys": [[0, k] for k in range(n)], "cells_px": cells_px,
            "ref_anchors": ref, "found_anchors": found_boxes}


def ag_flat(pl, r, c):
    if not isinstance(pl, dict) or pl.get("no_plan"):
        return -1
    r, c = int(r), int(c)
    if r < 0 or c < 0 or r >= int(pl["rows"]) or c >= int(pl["cols"]):
        return -1
    return r * int(pl["cols"]) + c


def ag_pick(pl, idx, labels=None):
    if not isinstance(pl, dict) or pl.get("no_plan"):
        return {"no_plan": True, "refused": True,
                "reason": (pl or {}).get("reason", "no plan to pick from")}
    flat = []
    for k in (idx or []):
        if isinstance(k, (list, tuple)):
            flat.append(ag_flat(pl, k[0], k[1]))
        else:
            flat.append(int(k))
    keep = [k for k in flat if 0 <= k < len(pl["boxes"])]
    out = {"no_plan": not keep, "refused": not keep,
           "reason": "" if keep else "none of the named cells exist",
           "rows": 1, "cols": len(keep), "n": len(keep),
           "frame": pl["frame"], "anchor": pl.get("anchor"),
           "cells": {"geometry": [pl["boxes"][k] for k in keep]},
           "boxes": [pl["boxes"][k] for k in keep],
           "rects": [pl["rects"][k] for k in keep],
           "cells_px": [pl["cells_px"][k] for k in keep],
           "keys": [pl["keys"][k] for k in keep] if pl.get("keys") else [],
           "index": keep, "n_dropped": len(flat) - len(keep),
           "ref_anchors": pl["ref_anchors"], "found_anchors": pl["found_anchors"]}
    if labels:
        out["labels"] = [str(x) for x in labels][:len(keep)]
    return out


def ag_paint(pl, verdicts, idx=None):
    if not isinstance(pl, dict) or pl.get("no_plan"):
        return {"hit": [], "miss": [], "edge": [], "n_hit": 0, "n_miss": 0, "n_edge": 0,
                "no_plan": True}
    rects = pl["rects"]
    order = list(idx) if idx is not None else list(range(len(rects)))
    hit, miss, edge = [], [], []
    for j, k in enumerate(order):
        try:
            k = int(k)
        except Exception:
            continue
        if not (0 <= k < len(rects)):
            continue
        v = verdicts[j] if j < len(verdicts) else None
        (hit if v is True or v == 1 else (edge if v is None else miss)).append(rects[k])
    return {"hit": hit, "miss": miss, "edge": edge, "no_plan": False,
            "n_hit": len(hit), "n_miss": len(miss), "n_edge": len(edge),
            "ref_anchors": pl["ref_anchors"], "found_anchors": pl["found_anchors"]}


def ag_pt(fb):
    g = fb
    if isinstance(fb, dict):
        if fb.get("refused") or fb.get("unreadable"):
            return None
        g = fb.get("geometry")
    if not g or len(g) < 2:
        return None
    return float(g[0]), float(g[1])


def ag_ln(fb):
    g = fb
    if isinstance(fb, dict):
        if fb.get("refused") or fb.get("unreadable"):
            return None
        g = fb.get("geometry")
    if not g or len(g) < 4:
        return None
    return tuple(float(v) for v in g[:4])


def ag_along(pl, y=None, x=None):
    if not isinstance(pl, dict) or pl.get("no_plan"):
        return None
    W, H = [float(v) for v in pl["frame"]]
    ax0, ay0, ax1, ay1 = [float(v) for v in pl["anchor_px"]]
    if y is not None:
        span = ay1 - ay0
        return None if span <= 0 else (float(y) * H / 1000.0 - ay0) / span
    if x is not None:
        span = ax1 - ax0
        return None if span <= 0 else (float(x) * W / 1000.0 - ax0) / span
    return None


def ag_ref_line(pl, y0, x0, y1, x1):
    if not isinstance(pl, dict) or pl.get("no_plan"):
        return []
    W, H = [float(v) for v in pl["frame"]]
    M = max(W, H)
    return [[[float(x0) * W / 1000.0 / M, float(y0) * H / 1000.0 / M],
             [float(x1) * W / 1000.0 / M, float(y1) * H / 1000.0 / M]]]


def ag_paint_frac(pl, frac, idx=None):
    try:
        f = float(frac)
    except Exception:
        f = 0.0
    v = True if f >= 1.0 else (None if f > 0.0 else False)
    n = len(pl.get("rects") or []) if isinstance(pl, dict) else 0
    return ag_paint(pl, [v] * n, idx)


def ag_answers(rd, n=None):
    a = rd.get("answers") if isinstance(rd, dict) else rd
    a = list(a or [])
    if n is not None:
        n = int(n)
        a = (a + [None] * n)[:n]
    return a


def ag_count(s, lo=1, hi=64):
    import re as _re
    t = _re.findall(r"\d+", str(s if s is not None else ""))
    for x in t:
        v = int(x)
        if lo <= v <= hi:
            return v
    return None


def ag_pair(s, lo=1, hi=64):
    import re as _re
    t = [int(x) for x in _re.findall(r"\d+", str(s if s is not None else ""))]
    t = [v for v in t if lo <= v <= hi]
    return (t[0], t[1]) if len(t) >= 2 else (None, None)


def split_ruler_into_squares(image, ruler_box, n_divisions, axis='y'):
    """Cut the boxed ruler into equal grid squares along the given axis."""
    n = max(1, int(n_divisions))
    if str(axis) == 'x':
        return ag_plan(image, ruler_box, rows=1, cols=n, pad=0.05, inset=0.01)
    return ag_plan(image, ruler_box, rows=n, cols=1, pad=0.05, inset=0.01)


def read_plunger_value(pl, ln, lo, hi, axis='y', flip=False):
    g = ag_ln(ln)
    if g is None or not isinstance(pl, dict) or pl.get('no_plan'):
        return {'no_read': True, 'value': None, 'frac': None, 'cell': None}
    y0, x0, y1, x1 = g
    if str(axis) == 'x':
        f = ag_along(pl, x=(x0 + x1) / 2.0)
    else:
        f = ag_along(pl, y=(y0 + y1) / 2.0)
    if f is None:
        return {'no_read': True, 'value': None, 'frac': None, 'cell': None}
    t = f if flip else (1.0 - f) if str(axis) == 'y' else f
    val = float(lo) + (float(hi) - float(lo)) * t
    n = int(pl.get('n') or 1)
    k = int(f * n)
    k = 0 if k < 0 else (n - 1 if k >= n else k)
    return {'no_read': False, 'value': round(val, 4), 'frac': round(f, 4), 'cell': k,
            'line': [y0, x0, y1, x1]}


def paint_tip_square(plan, reading, ok=None):
    """Colour the arrow tip's grid square as right or wrong for the overlay."""
    if not isinstance(plan, dict) or plan.get('no_plan'):
        return {'hit': [], 'miss': [], 'edge': [], 'line': [], 'no_plan': True}
    k = (reading or {}).get('cell')
    oks = [None] * len(plan['rects'])
    if k is not None and 0 <= int(k) < len(oks):
        oks[int(k)] = ok
    painted = ag_paint(plan, oks)
    ln = (reading or {}).get('line')
    painted['line'] = ag_ref_line(plan, ln[0], ln[1], ln[2], ln[3]) if ln else []
    painted['cell'] = k
    return painted


def locate_tip_square(plan, tip, axis='y'):
    """Find which ruler grid square holds the arrow tip."""
    p = ag_pt(tip)
    if p is None or not isinstance(plan, dict) or plan.get('no_plan'):
        return {'no_read': True, 'cell': None}
    f = ag_along(plan, x=p[1]) if str(axis) == 'x' else ag_along(plan, y=p[0])
    if f is None:
        return {'no_read': True, 'cell': None}
    n = int(plan.get('n') or 1)
    k = int(f * n)
    k = 0 if k < 0 else (n - 1 if k >= n else k)
    return {'no_read': False, 'cell': k, 'frac': round(f, 4), 'pct': round(f * 100.0, 1),
            'line': [p[0], 0.0, p[0], 1000.0] if str(axis) == 'y' else [0.0, p[1], 1000.0, p[1]]}


def read_tick_number(plan, reads, tip_square):
    """Read the printed tick number in the grid square under the arrow tip."""
    import re
    k = (tip_square or {}).get('cell')
    answers = ag_answers(reads)
    if k is None or k >= len(answers) or answers[k] is None:
        return {'no_read': True, 'v': None, 'cell': k}
    nums = [int(x) for x in re.findall(r'-?\d+', str(answers[k]))]
    if not nums:
        return {'no_read': True, 'v': None, 'cell': k}
    return {'no_read': False, 'v': nums[len(nums) // 2], 'cell': k, 'labels': nums}

# end of code_anchorgrid

# code: arrow_tip_code
def arrow_tip(box):
    """Take the arrow tip as the middle of the bottom edge of its box."""
    g = (box or {}).get('geometry') or []
    if not g: return {'geometry': None, 'refused': True, 'unreadable': True, 'why': 'the marker arrow was never boxed'}
    b = g[0] if isinstance(g[0], (list, tuple)) else g
    if len(b) < 4: return {'geometry': None, 'refused': True, 'unreadable': True, 'why': 'the marker arrow box is degenerate'}
    y0, x0, y1, x1 = [float(v) for v in b[:4]]
    return {'geometry': [max(y0, y1), (x0 + x1) / 2.0], 'refused': False, 'unreadable': False, 'why': 'the arrow points down, so its tip is the middle of the bottom edge of the box that was confirmed round it'}

# end of arrow_tip_code

# code: hold_tick_cell_code
def refuse_missing_tip_square(tip_square):
    """Set refused when no grid square was found at the tip, so the task is withheld."""
    d = dict(tip_square) if isinstance(tip_square, dict) else {'no_read': True, 'cell': None}
    if d.get('no_read'):
        d['refused'] = True
    return d

# end of hold_tick_cell_code

# code: hold_tick_number_code
def refuse_missing_tick_number(reading, reads, tip_square):
    """Set refused when no label was read at the tip square, so the task is withheld."""
    d = dict(reading) if isinstance(reading, dict) else {'no_read': True, 'v': None, 'cell': None}
    answers = list((reads or {}).get('answers') or [])
    k = (tip_square or {}).get('cell')
    if d.get('no_read') and (k is None or k >= len(answers) or answers[k] is None):
        d['refused'] = True
    return d

# end of hold_tick_number_code

# code: chk_code
def number_matches_reference(answer, want):
    """1.0 if the number read equals the target value, else 0.0."""
    import re
    if answer is None or isinstance(answer, dict): return 0.0
    t = str(answer).strip().lower().replace(',', '').replace(' ', '')
    m = re.search(r'-?\d+', t)
    if not m: return 0.0
    return 1.0 if int(m.group(0)) == int(want) else 0.0

# end of chk_code
