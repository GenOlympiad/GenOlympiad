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


def s3_ray(fb):
    g = fb
    if isinstance(fb, dict):
        if fb.get('refused') or fb.get('unreadable'):
            return None
        g = fb.get('geometry')
    if not g:
        return None
    if isinstance(g[0], (list, tuple)):
        g = g[0]
    if len(g) < 4:
        return None
    try:
        return [float(g[0]), float(g[1]), float(g[2]), float(g[3])]
    except Exception:
        return None


def s3_px(pl, y, x):
    W, H = float(pl['frame'][0]), float(pl['frame'][1])
    return [float(x) * W / 1000.0, float(y) * H / 1000.0]


def s3_bearing_px(pl, x, y):
    import math
    cx, cy = pl['centre_px'][0], pl['centre_px'][1]
    return math.degrees(math.atan2(float(x) - cx, cy - float(y))) % 360.0


def s3_ray_bearing(pl, ray):
    import math
    if not ray:
        return None
    p = s3_px(pl, ray[0], ray[1])
    t = s3_px(pl, ray[2], ray[3])
    dx, dy = t[0] - p[0], t[1] - p[1]
    if abs(dx) < 1e-9 and abs(dy) < 1e-9:
        return None
    return math.degrees(math.atan2(dx, -dy)) % 360.0


def s3_sector(pl, bearing):
    if bearing is None or not isinstance(pl, dict) or pl.get('no_plan'):
        return None
    n = int(pl['n'])
    return int(round(float(bearing) * n / 360.0)) % n


def s3_side(pl, x):
    cx = float(pl['centre_px'][0])
    if abs(float(x) - cx) < 1e-9:
        return None
    return 'left' if float(x) < cx else 'right'


def s3_word4(bearing):
    if bearing is None:
        return None
    return ['top', 'right', 'bottom', 'left'][int(round(float(bearing) / 90.0)) % 4]


def s3_dir4(bearing):
    if bearing is None:
        return None
    return ['up', 'right', 'down', 'left'][int(round(float(bearing) / 90.0)) % 4]


def s3_num(s, lo=-100000.0, hi=100000.0):
    import re
    t = str(s if s is not None else '').strip()
    low = t.lower()
    if not t or low.startswith('none') or low.startswith('no number') or low.startswith('no '):
        return None
    t = t.replace('−', '-').replace(',', '')
    for x in re.findall(r'-?\d+(?:\.\d+)?', t):
        v = float(x)
        if lo <= v <= hi:
            return v
    return None


def s3_verdict(frac):
    try:
        f = float(frac)
    except Exception:
        f = 0.0
    return True if f >= 1.0 else (None if f > 0.0 else False)


def paint_sector_marks(pl, idx, oks, blanks=None):
    ids, vs = [], []
    src_idx = list(idx or [])
    src_oks = list(oks or [])
    for j, k in enumerate(src_idx):
        if k is None:
            continue
        k = int(k)
        if k in ids:
            continue
        ids.append(k)
        vs.append(src_oks[j] if j < len(src_oks) else None)
    for b in list(blanks or []):
        if b is None:
            continue
        b = int(b)
        if b not in ids:
            ids.append(b)
            vs.append(None)
    return ag_paint(pl, vs, ids)


def s3_blanks(rd, n):
    ans = ag_answers(rd, n)
    return [i for i, a in enumerate(ans) if a is None]


def s3_hold(reason):
    return {'no_plan': True, 'refused': True, 'unreadable': True, 'reason': str(reason)}


def as_answer(word):
    """Wrap one spoke label as a single answer for the label check."""
    return {'answers': [word]}


def result_value(res, key='v'):
    try:
        return res.get(key)
    except Exception:
        return None

def plan_spoke_sectors(image, chart_box, labels):
    """Cut the boxed chart into one sector per spoke, clockwise from the top."""
    n = len(list(labels or []))
    if n < 3:
        return s3_hold('the chart pins no spoke list to cut on')
    plan = ag_sectors(image, chart_box, n, start_deg=-90.0, clockwise=True,
                    r_in=0.08, r_out=1.0, span_frac=0.55, pad=0.02)
    return s3_hold(plan.get('reason')) if plan.get('no_plan') else plan


def find_longest_shortest_spokes(label_reads, value_reads, plan, labels):
    """Find the spoke labels with the largest and smallest read values."""
    n = int(plan['n'])
    words = ag_answers(label_reads, n)
    vals = ag_answers(value_reads, n)
    known = [str(x).strip().upper() for x in (labels or [])]
    spoke_labels, num = [], []
    for i in range(n):
        s = str(words[i] if words[i] is not None else '').strip().upper()
        w = None
        for lab in known:
            if lab and lab in s:
                w = lab
                break
        spoke_labels.append(w)
        num.append(s3_num(vals[i], -1, 20))
    live = [i for i in range(n) if num[i] is not None and spoke_labels[i] is not None]
    blanks = [i for i in range(n) if num[i] is None or spoke_labels[i] is None]
    if len(live) < 2:
        return {'no_read': True, 'imax': None, 'imin': None, 'vmax': None, 'vmin': None,
                'blanks': blanks, 'reach': num, 'words': spoke_labels}
    imax = live[0]
    imin = live[0]
    for i in live:
        if num[i] > num[imax]:
            imax = i
        if num[i] < num[imin]:
            imin = i
    return {'no_read': False, 'imax': imax, 'imin': imin, 'vmax': spoke_labels[imax], 'vmin': spoke_labels[imin],
            'blanks': blanks, 'reach': num, 'words': spoke_labels}


def mark_extreme_spokes(plan, extremes, reference):
    """Mark the largest and smallest spoke sectors right or wrong for the overlay."""
    idx, oks = [], []
    if extremes.get('imax') is not None:
        idx.append(int(extremes['imax']))
        oks.append(str(extremes.get('vmax')) == str(reference['max_label']).strip().upper())
    if extremes.get('imin') is not None:
        idx.append(int(extremes['imin']))
        oks.append(str(extremes.get('vmin')) == str(reference['min_label']).strip().upper())
    return paint_sector_marks(plan, idx, oks, extremes.get('blanks'))

# end of code_anchorgrid

# code: law_code

def extreme_labels_match(cmax, cmin, labels, want_max, want_min):
    """1 if the largest and smallest spoke labels read both match the reference, else 0."""
    def pick(node):
        a = ((node or {}).get('answers') or [None])[0]
        if not a:
            return None
        s = str(a).upper()
        hit = [str(L).upper() for L in (labels or []) if str(L).upper() in s]
        return hit[0] if len(hit) == 1 else None

    got_max, got_min = pick(cmax), pick(cmin)
    ok = (got_max is not None and got_min is not None
          and got_max == str(want_max).strip().upper()
          and got_min == str(want_min).strip().upper())
    return {'frac': 1.0 if ok else 0.0, 'read_max': got_max, 'read_min': got_min,
            'want_max': str(want_max).upper(), 'want_min': str(want_min).upper()}

# end of law_code
