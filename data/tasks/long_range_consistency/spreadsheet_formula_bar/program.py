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


def ag_paint_frac(plan, frac, idx=None):
    """Mark every planned box as passed, failed or unsure from one score."""
    try:
        score = float(frac)
    except Exception:
        score = 0.0
    v = True if score >= 1.0 else (None if score > 0.0 else False)
    n = len(plan.get("rects") or []) if isinstance(plan, dict) else 0
    return ag_paint(plan, [v] * n, idx)


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


SS_COLS = 5
SS_ROWS = 7


def sheet_grid_plan(image, anc):
    """Cut the boxed sheet into its rows and columns of grid squares."""
    return ag_plan(image, anc, rows=SS_ROWS, cols=SS_COLS, pad=0.05, inset=0.03)


def single_box_plan(image, anc):
    """Treat the boxed area as a single grid square."""
    return ag_plan(image, anc, rows=1, cols=1, pad=0.04, inset=0.0)


def ss_sel(rd):
    n = SS_ROWS * SS_COLS
    ans = ag_answers(rd, n)
    read_any = False
    hit = -1
    for i, a in enumerate(ans):
        s = str(a or '').strip().lower()
        if not s:
            continue
        read_any = True
        if (s.startswith('y') or 'yes' in s[:6]) and hit < 0:
            hit = i
    out = {'no_read': not read_any, 'idx': hit, 'ref': '', 'row': None, 'col': None}
    if hit >= 0:
        r, c = hit // SS_COLS, hit % SS_COLS
        out['row'] = r + 1
        out['col'] = chr(ord('A') + c)
        out['ref'] = '%s%d' % (out['col'], out['row'])
    return out


def ss_cell(pl, sel):
    if not isinstance(pl, dict) or pl.get('no_plan'):
        return pl
    i = int((sel or {}).get('idx', -1))
    return ag_pick(pl, [i if i >= 0 else 0])


def first_answer_number(reads, sel):
    """The first number in the answer, ignoring commas and the pound sign."""
    import re
    if int((sel or {}).get('idx', -1)) < 0:
        return {'no_read': False, 'v': None}
    answer = ag_answers(reads, 1)[0]
    if answer is None:
        return {'no_read': False, 'v': None}
    s = str(answer).replace(',', '').replace('\u00a3', ' ')
    m = re.search(r'-?\d+(?:\.\d+)?', s)
    return {'no_read': False, 'v': float(m.group(0)) if m else None, 'read': str(answer).strip()}


def first_answer_text(reads):
    """The first answer as trimmed text, or marked unread."""
    a = ag_answers(reads, 1)[0]
    if a is None:
        return {'no_read': True, 'v': None}
    return {'no_read': False, 'v': str(a).strip()}


def pick_named_square(plan, ref):
    """The grid square named by a reference such as B3, picked from the sheet plan."""
    if not isinstance(plan, dict) or plan.get('no_plan'):
        return plan
    s = str(ref or '').strip().upper()
    letters = ''.join(ch for ch in s if ch.isalpha())
    digits = ''.join(ch for ch in s if ch.isdigit())
    if not letters or not digits:
        return {'no_plan': True, 'reason': 'the wanted cell was not named as a column and a row'}
    c = ord(letters[0]) - ord('A')
    r = int(digits) - 1
    return ag_pick(plan, [[r, c]])


def paint_read_boxes(plan, sel, name_plan, formula_plan, frac):
    """Draw the selected grid square and the name and formula boxes, coloured by the score."""
    rects = []
    i = int((sel or {}).get('idx', -1))
    if i >= 0:
        rects.extend(list(ag_pick(plan, [i]).get('rects') or []))
    for s in (name_plan, formula_plan):
        if isinstance(s, dict):
            rects.extend(list(s.get('rects') or []))
    base = dict(plan)
    base['rects'] = rects
    return ag_paint_frac(base, frac)

# end of code_anchorgrid

# code: ss_pick_code
def outlined_value_and_ref(value_read, ref_read):
    """The value and the column and row reference read for the outlined grid square."""
    import re
    def first_text(rd):
        a = (rd.get('answers') if isinstance(rd, dict) else rd) or []
        return (str(a[0]).strip() or None) if (a and a[0] is not None) else None
    value_text, ref_text = first_text(value_read), first_text(ref_read)
    m = re.search(r'-?\d+(?:\.\d+)?', value_text.replace(',', '').replace('\u00a3', ' ')) if value_text is not None else None
    value = float(m.group(0)) if m else None
    m = re.search(r'(?<![A-Za-z0-9])([A-Za-z])\s?([0-9]+)(?![0-9])', ref_text) if ref_text is not None else None
    column_match, row_match = (re.search(r'column\s*([A-Za-z])', ref_text, re.I), re.search(r'row\s*([0-9]+)', ref_text, re.I)) if (ref_text is not None and not m) else (None, None)
    ref = '%s%s' % (m.group(1).upper(), m.group(2)) if m else ('%s%s' % (column_match.group(1).upper(), row_match.group(1)) if (column_match and row_match) else '')
    return {'no_read': (value_text is None and ref_text is None), 'refused': (value_text is None and ref_text is None), 'idx': 0, 'v': value, 'ref': ref, 'read_value': value_text, 'read_ref': ref_text, 'verdict': 'the outlined cell reads %s and sits at %s' % (value_text or 'nothing', ref or 'no readable reference')}
# end of ss_pick_code

# code: hold_b3_text_code
def hold_b3_text(read):
    """Return the B3 read as it is; sets refused when nothing was read."""
    result = dict(read) if isinstance(read, dict) else {'no_read': True, 'v': None}
    if result.get('no_read'):
        result['refused'] = True
    return result

# end of hold_b3_text_code

# code: hold_c2_text_code
def hold_c2_text(read):
    """Return the C2 read as it is; sets refused when nothing was read."""
    result = dict(read) if isinstance(read, dict) else {'no_read': True, 'v': None}
    if result.get('no_read'):
        result['refused'] = True
    return result

# end of hold_c2_text_code

# code: hold_b4_text_code
def hold_b4_text(read):
    """Return the B4 read as it is; sets refused when nothing was read."""
    result = dict(read) if isinstance(read, dict) else {'no_read': True, 'v': None}
    if result.get('no_read'):
        result['refused'] = True
    return result

# end of hold_b4_text_code
