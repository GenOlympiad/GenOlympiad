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


def s6_frame(W, H):
    M = float(max(W, H))
    return ([[0.0, 0.0], [W / M, 0.0], [W / M, H / M], [0.0, H / M]],
            [[0.0, 0.0], [W, 0.0], [W, H], [0.0, H]])


def s6_blank():
    return {'hit': [], 'miss': [], 'edge': [], 'frame_lines': [], 'no_plan': True,
            'n_hit': 0, 'n_miss': 0, 'n_edge': 0, 'ref_anchors': [], 'found_anchors': []}


def s6_paint_px(cells_px, oks, W, H, outline=None):
    M = float(max(W, H))
    hit, miss, edge = [], [], []
    for i, cell in enumerate(cells_px):
        x0, y0, x1, y1 = [float(v) for v in cell[:4]]
        r = [(x0 + x1) / 2.0 / M, (y0 + y1) / 2.0 / M,
             max(1.0, x1 - x0) / M, max(1.0, y1 - y0) / M]
        v = oks[i] if i < len(oks) else None
        if v is True or v == 1:
            hit.append(r)
        elif v is None:
            edge.append(r)
        else:
            miss.append(r)
    ref, found_boxes = s6_frame(W, H)
    out = {'hit': hit, 'miss': miss, 'edge': edge, 'no_plan': not cells_px,
           'n_hit': len(hit), 'n_miss': len(miss), 'n_edge': len(edge),
           'ref_anchors': ref, 'found_anchors': found_boxes, 'frame_lines': []}
    if outline:
        x0, y0, x1, y1 = [float(v) for v in outline[:4]]
        out['frame_lines'] = [[[x0 / M, y0 / M], [x1 / M, y0 / M], [x1 / M, y1 / M],
                               [x0 / M, y1 / M], [x0 / M, y0 / M]]]
    return out


def s6_outline(pl):
    if not isinstance(pl, dict) or pl.get('no_plan') or not pl.get('anchor_px'):
        return []
    W, H = [float(v) for v in pl['frame']]
    M = max(W, H)
    x0, y0, x1, y1 = [float(v) for v in pl['anchor_px']]
    return [[[x0 / M, y0 / M], [x1 / M, y0 / M], [x1 / M, y1 / M],
             [x0 / M, y1 / M], [x0 / M, y0 / M]]]


def s6_yes(a):
    s = str(a if a is not None else '').strip().lower()
    if s.startswith('yes') or s.startswith('true'):
        return True
    if s.startswith('no') or s.startswith('none') or s.startswith('false'):
        return False
    return None

def ea_fields(n_dig):
    if int(n_dig) == 8:
        return [3 + 7 * k for k in range(4)] + [36 + 7 * k for k in range(4)], 67, 0
    return [3 + 7 * k for k in range(6)] + [50 + 7 * k for k in range(6)], 95, 1


def paint_barcode_digits(image, m, bars, what='bars'):
    """Overlay each digit's span, marked right or wrong against the reference code."""
    wh = ag_wh(image)
    if not wh or not isinstance(bars, dict) or bars.get('no_read'):
        return s6_blank()
    W, H = wh
    try:
        y0, y1 = [float(v) for v in (bars.get('band_y') or [0, 0])]
        x0 = float(bars.get('x_used0'))
        x1 = float(bars.get('x_used1'))
    except (TypeError, ValueError):
        return s6_blank()
    want = str((m or {}).get('gt_full_code') or '')
    if len(want) not in (8, 13) or x1 <= x0 or y1 <= y0:
        return s6_blank()
    offs, total, skip = ea_fields(len(want))
    unit = (x1 - x0) / float(total)
    band = y1 - y0
    if str(what) == 'printed':
        top = y1 + 0.04 * band
        bot = min(float(H) - 1.0, y1 + 0.42 * band)
        read = str((m or {}).get('printed') or '')
        cells, oks = [], []
        for j in range(len(want)):
            a = x0 + (x1 - x0) * j / float(len(want))
            b = x0 + (x1 - x0) * (j + 1) / float(len(want))
            cells.append([a, top, b, bot])
            oks.append(None if j >= len(read) else (read[j] == want[j]))
        if bot - top < 4.0:
            return s6_blank()
        return s6_paint_px(cells, oks, W, H, outline=[x0, top, x1, bot])
    dec = list((m or {}).get('decoded') or '')
    raw = (bars or {}).get('decoded_raw')
    cells, oks = [], []
    for j, off in enumerate(offs):
        a, b = x0 + off * unit, x0 + (off + 7) * unit
        cells.append([a, y0, b, y1])
        idx = j + skip
        got = None
        if raw and idx < len(raw) and raw[idx] is not None:
            got = str(raw[idx])
        elif idx < len(dec):
            got = str(dec[idx])
        oks.append(None if got is None else (got == want[idx]))
    return s6_paint_px(cells, oks, W, H, outline=[x0, y0, x1, y1])

# end of code_anchorgrid

# shared code: code_9c7831ec94b7
def as_score(x):
    """The measured score as a number, with a missing value counted as 0."""
    return float(x or 0.0)

# end of code_9c7831ec94b7

# code: ean_measure_code


L_CODE = ["0001101", "0011001", "0010011", "0111101", "0100011",
          "0110001", "0101111", "0111011", "0110111", "0001011"]
R_CODE = ["".join("1" if c == "0" else "0" for c in w) for w in L_CODE]
G_CODE = [w[::-1] for w in R_CODE]
PARITY13 = ["LLLLLL", "LLGLGG", "LLGGLG", "LLGGGL", "LGLLGG",
            "LGGLLG", "LGGGLL", "LGLGLG", "LGLGGL", "LGGLGL"]


def check_digit(prefix):
    d = [int(c) for c in str(prefix)]
    w = ([3, 1] * 7)[:len(d)] if len(d) == 7 else ([1, 3] * 7)[:len(d)]
    return (10 - sum(a * b for a, b in zip(d, w)) % 10) % 10


def full_code(prefix):
    return str(prefix) + str(check_digit(prefix))


def modules(prefix):
    code = full_code(prefix)
    if len(code) == 8:
        s = "101"
        for c in code[:4]:
            s += L_CODE[int(c)]
        s += "01010"
        for c in code[4:]:
            s += R_CODE[int(c)]
        return s + "101"
    par = PARITY13[int(code[0])]
    s = "101"
    for c, p in zip(code[1:7], par):
        s += (L_CODE[int(c)] if p == "L" else G_CODE[int(c)])
    s += "01010"
    for c in code[7:]:
        s += R_CODE[int(c)]
    return s + "101"


def decode(mods):
    n = len(mods)
    if n == 67:
        guards = [mods[:3] == "101", mods[31:36] == "01010", mods[-3:] == "101"]
        if not all(guards):
            return None, guards
        digs = []
        for k in range(4):
            w = mods[3 + 7 * k:10 + 7 * k]
            digs.append(L_CODE.index(w) if w in L_CODE else None)
        for k in range(4):
            w = mods[36 + 7 * k:43 + 7 * k]
            digs.append(R_CODE.index(w) if w in R_CODE else None)
        return digs, guards
    if n == 95:
        guards = [mods[:3] == "101", mods[45:50] == "01010", mods[-3:] == "101"]
        if not all(guards):
            return None, guards
        left, par = [], ""
        for k in range(6):
            w = mods[3 + 7 * k:10 + 7 * k]
            if w in L_CODE:
                left.append(L_CODE.index(w))
                par += "L"
            elif w in G_CODE:
                left.append(G_CODE.index(w))
                par += "G"
            else:
                left.append(None)
                par += "?"
        first = PARITY13.index(par) if par in PARITY13 else None
        right = []
        for k in range(6):
            w = mods[50 + 7 * k:57 + 7 * k]
            right.append(R_CODE.index(w) if w in R_CODE else None)
        return [first] + left + right, guards
    return None, [False, False, False]


def _cv():
    import os
    for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
               "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
        os.environ.setdefault(_v, "2")
    import cv2
    import numpy as np
    try:
        cv2.setNumThreads(2)
    except Exception:
        pass
    return cv2, np


def _store():
    import sys
    import types
    m = sys.modules.get("_ean8_store")
    if m is None:
        m = types.ModuleType("_ean8_store")
        m.bars = {}
        m.rows = {}
        m.ocr = None
        sys.modules["_ean8_store"] = m
    return m


def _vrun(mask):
    cv2, np = _cv()
    a = (mask > 0).astype(np.int32)
    fwd = np.zeros_like(a)
    acc = np.zeros(a.shape[1], np.int32)
    for i in range(a.shape[0]):
        acc = (acc + 1) * a[i]
        fwd[i] = acc
    bwd = np.zeros_like(a)
    acc = np.zeros(a.shape[1], np.int32)
    for i in range(a.shape[0] - 1, -1, -1):
        acc = (acc + 1) * a[i]
        bwd[i] = acc
    return fwd + bwd - a


def _gray(image):
    cv2, np = _cv()
    if hasattr(image, "convert"):
        arr = np.array(image.convert("RGB"))[:, :, ::-1]
    elif isinstance(image, np.ndarray):
        arr = image
    else:
        arr = cv2.imread(str(image))
    if arr is None:
        return None, None
    return arr, (cv2.cvtColor(arr, cv2.COLOR_BGR2GRAY) if arr.ndim == 3 else arr)


def read_bars(image):
    """Find the bar band, measure run widths and decode them into modules and digits."""
    cv2, np = _cv()
    store = _store()
    cache_key = str(image) if not hasattr(image, "convert") else "pil:%d" % id(image)
    if cache_key in store.bars:
        return store.bars[cache_key]
    bgr, g = _gray(image)
    if g is None:
        return {"no_read": True, "reason": "unreadable"}
    H, W = g.shape
    th = cv2.threshold(g, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    dark = (th == 0).astype(np.uint8)
    tall = (dark > 0) & (_vrun(dark) >= max(8, int(0.08 * H)))
    score = np.abs(np.diff(tall.astype(np.int16), axis=1)).sum(axis=1)
    if score.max() < 8:
        return {"no_read": True, "reason": "no_bar_band"}
    top = int(np.argmax(score))
    thr = 0.50 * float(score.max())
    y0 = top
    while y0 > 0 and score[y0 - 1] >= thr:
        y0 -= 1
    y1 = top
    while y1 < H - 1 and score[y1 + 1] >= thr:
        y1 += 1
    band = dark[y0:y1 + 1, :]
    prof = (band > 0).mean(axis=0) > 0.5
    xs = np.nonzero(prof)[0]
    if len(xs) < 20:
        return {"no_read": True, "reason": "no_bars"}
    a, b = int(xs[0]), int(xs[-1])
    mm = band[:, a:b + 1].astype(float).mean(axis=0)
    uni = float(((mm >= 0.90) | (mm <= 0.10)).mean())
    if uni < 0.80:
        return {"no_read": True, "reason": "band_is_not_bar_like", "uniformity": round(uni, 3)}
    seg = prof[a:b + 1]
    runs, cur_v, ln = [], bool(seg[0]), 1
    for v in seg[1:]:
        if bool(v) == cur_v:
            ln += 1
        else:
            runs.append((cur_v, ln))
            cur_v, ln = bool(v), 1
    runs.append((cur_v, ln))
    drop_lo = drop_hi = 0
    for _side in range(8):
        if len(runs) < 8:
            break
        med = float(np.median([l for _c, l in runs]))
        if runs[0][1] > 5.0 * med:
            drop_lo += runs.pop(0)[1]
        elif runs[-1][1] > 5.0 * med:
            drop_hi += runs.pop()[1]
        else:
            break
    lens = np.array([l for _c, l in runs], float)
    thr = max(3.0, 0.25 * float(np.median(lens)))
    keep = []
    for c, l in runs:
        if l < thr:
            if keep:
                keep[-1][1] += l
        elif keep and keep[-1][0] == c:
            keep[-1][1] += l
        else:
            keep.append([c, float(l)])
    if len(keep) < 6:
        return {"no_read": True, "reason": "no_runs"}
    kl = np.array([l for _c, l in keep], float)
    m0 = float(np.percentile(kl, 10))
    singles = kl[(kl >= 0.6 * m0) & (kl <= 1.5 * m0)]
    unit = float(np.mean(singles)) if singles.size else m0
    mods = "".join(("1" if c else "0") * max(1, int(round(l / unit))) for c, l in keep)
    digs, guards = decode(mods)
    out = {"no_read": False, "band_y": [int(y0), int(y1)], "bar_span_px": b - a + 1,
           "unit_px": round(unit, 2), "n_modules_est": round(float(kl.sum()) / unit, 2),
           "n_modules_str": len(mods), "mods": mods, "guards": guards,
           "decoded": None if digs is None or any(d is None for d in digs)
                      else "".join(str(d) for d in digs),
           "decoded_raw": digs, "x0": a, "x1": b,
           "x_used0": int(a + drop_lo), "x_used1": int(b - drop_hi)}
    if len(store.bars) > 48:
        store.bars.clear()
    store.bars[cache_key] = out
    return out


def read_digit_row(image, n_digits):
    st = _store()
    ck = (str(image) if not hasattr(image, "convert") else "pil:%d" % id(image), int(n_digits))
    if ck in st.rows:
        return st.rows[ck]
    try:
        if st.ocr is None:
            from rapidocr_onnxruntime import RapidOCR
            st.ocr = RapidOCR()
        res, _ = st.ocr(str(image))
    except Exception:
        return {"no_read": True, "reason": "ocr_unavailable", "digits": None}
    toks = []
    for box, txt, _conf in (res or []):
        t = "".join(c for c in str(txt) if c.isdigit())
        if t:
            toks.append((float(box[0][1]), float(box[0][0]), t))
    if not toks:
        return {"no_read": True, "reason": "no_digits", "digits": None}
    bands = {}
    for y, x, t in toks:
        bands.setdefault(int(round(y / 45.0)), []).append((x, t))
    best = None
    for _k, items in bands.items():
        s = "".join(t for _x, t in sorted(items))
        if best is None or abs(len(s) - n_digits) < abs(len(best) - n_digits) or \
           (abs(len(s) - n_digits) == abs(len(best) - n_digits) and len(s) > len(best)):
            best = s
    out = {"no_read": not best, "digits": best,
           "n_digits": len(best or ""), "all_rows": sorted(
               "".join(t for _x, t in sorted(v)) for v in bands.values())}
    if len(st.rows) > 48:
        st.rows.clear()
    st.rows[ck] = out
    return out


def ean_measure(image, prefix, n_modules):
    """Compare the printed digits and the decoded bars with the code built from the prefix."""
    prefix = str(prefix)
    want = full_code(prefix)
    n_dig = len(want)
    bars = read_bars(image)
    row = read_digit_row(image, n_dig)
    out = {"gt_full_code": want, "gt_check_digit": want[-1], "gt_modules": int(n_modules),
           "printed": row.get("digits"), "no_read": bool(bars.get("no_read")),
           "reason": bars.get("reason"), "n_modules_est": bars.get("n_modules_est"),
           "decoded": bars.get("decoded"), "guards": bars.get("guards")}
    p = row.get("digits") or ""
    out["printed_check"] = p[n_dig - 1] if len(p) >= n_dig else None
    out["check_frac"] = 1.0 if (len(p) >= n_dig and p[n_dig - 1] == want[-1]) else 0.0
    if row.get("no_read"):
        out["check_frac"] = 0.0
        out["check_unreadable"] = True
    dec = bars.get("decoded_raw")
    if bars.get("no_read") or not dec:
        out["payload_frac"] = 0.0
    else:
        hits = sum(1.0 for i, ch in enumerate(want)
                   if i < len(dec) and dec[i] is not None and str(dec[i]) == ch)
        out["payload_frac"] = round(hits / float(n_dig), 4)
    out["payload_exact_frac"] = 1.0 if bars.get("decoded") == want else 0.0
    est = bars.get("n_modules_est")
    if est is None:
        out["width_frac"] = 0.0
    else:
        err = abs(float(est) - float(n_modules))
        out["width_frac"] = round(max(0.0, min(1.0, 1.0 - max(0.0, err - 1.0)
                                               / (0.15 * float(n_modules)))), 4)
    gu = bars.get("guards") or [False, False, False]
    parts = [sum(1.0 for x in gu if x) / 3.0,
             1.0 if len(p) == n_dig else 0.0,
             1.0 if p[:n_dig - 1] == prefix else 0.0]
    out["appearance_frac"] = round(sum(parts) / 3.0, 4)
    out["selfconsistent_frac"] = 1.0 if (out["decoded"] and out["decoded"] == p) else 0.0
    return out


def ean_overlay(image, prefix, n_modules, tag="ean"):
    """Draw the demanded and measured module strips under the picture for review."""
    cv2, np = _cv()
    from PIL import Image
    import hashlib
    import os
    import tempfile
    m = ean_measure(image, prefix, n_modules)
    bars = read_bars(image)
    bgr, _g = _gray(image)
    im = None if bgr is None else bgr.copy()
    if im is not None:
        H, W = im.shape[:2]
        lw = max(2, int(0.0022 * min(H, W)))
        strip_h = max(26, H // 22)
        want = modules(prefix)
        got = bars.get("mods") or ""
        if not bars.get("no_read"):
            y0, y1 = bars["band_y"]
            cv2.rectangle(im, (bars["x_used0"], y0), (bars["x_used1"], y1), (0, 200, 255), lw)
        panel = np.full((3 * strip_h + 26, W, 3), 245, dtype=im.dtype)
        def draw(sr, row, colour):
            if not sr:
                return
            for i, ch in enumerate(sr):
                x0 = int(i * W / float(len(sr)))
                x1 = int((i + 1) * W / float(len(sr)))
                if ch == "1":
                    panel[row:row + strip_h - 6, x0:x1] = colour
        draw(want, 4, (0, 0, 0))
        draw(got, strip_h + 10, (0, 0, 210))
        k = None
        for i in range(min(len(want), len(got))):
            if want[i] != got[i]:
                k = i
                break
        if k is None and len(want) != len(got):
            k = min(len(want), len(got))
        if k is not None and want:
            x = int((k + 0.5) * W / float(len(want)))
            cv2.line(panel, (x, 0), (x, 2 * strip_h + 10), (255, 0, 220), lw)
        cap = "black = the %d modules demanded   red = the %s measured   magenta = first " \
              "disagreement   printed %s   demanded %s" % (
                  int(n_modules), m.get("n_modules_est"), m.get("printed"), m["gt_full_code"])
        cfs = min(0.6, 0.95 * W / (max(1, len(cap)) * 21.0))
        cv2.putText(panel, cap, (10, 3 * strip_h + 16), cv2.FONT_HERSHEY_SIMPLEX, cfs,
                    (20, 20, 20), max(1, lw - 1))
        im = np.vstack([im, panel])
    d = os.path.join(tempfile.gettempdir(), "genolympiad_overlay")
    try:
        os.makedirs(d, exist_ok=True)
    except Exception:
        pass
    h = hashlib.md5(("%s|%s" % (str(image), tag)).encode("utf-8", "replace")).hexdigest()[:12]
    p = os.path.join(d, "e9cean_%s_%s.png" % (tag, h))
    if im is not None:
        Image.fromarray(im[:, :, ::-1]).save(p)
    out = dict(m)
    out["path"] = p
    return out


def as_score(x):
    return float(x or 0.0)

# end of ean_measure_code

# code: f_code
def full_score(x):
    """Always 1; this step gives full credit."""
    return 1.0

# end of f_code
