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

def bead_marker_squares(overlay):
    """Turn the overlay's bead circles into matched and unmatched squares to draw."""
    if not isinstance(overlay, dict) or not overlay.get('ref_anchors'):
        return s6_blank()

    def squares(group):
        out = []
        for c in ((overlay.get(group) or {}).get('circles') or []):
            try:
                cx, cy, d = float(c[0]), float(c[1]), float(c[2])
            except (TypeError, ValueError, IndexError):
                continue
            out.append([cx, cy, d, d])
        return out

    hit, miss = squares('mk_bead_rod_matched'), squares('mk_bead_rod_unmatched')
    return {'hit': hit, 'miss': miss, 'edge': [], 'no_plan': not (hit or miss),
            'n_hit': len(hit), 'n_miss': len(miss), 'n_edge': 0,
            'ref_anchors': overlay['ref_anchors'], 'found_anchors': overlay['found_anchors'],
            'frame_lines': (overlay.get('mk_reckoning_beam') or {}).get('polylines') or []}

# end of code_anchorgrid

# shared code: code_7c651e814a25
def as_score(value):
    """The score as a number, zero when it is missing."""
    return float(value or 0.0)

# end of code_7c651e814a25

# code: read_abacus_code
_PREP = {}


def _prep(image, cap=1500):
    import numpy as np
    import cv2
    from PIL import Image
    key = (str(image), cap)
    hit = _PREP.get(key)
    if hit is not None:
        return hit
    pil = image.convert("RGB") if hasattr(image, "convert") else Image.open(str(image)).convert("RGB")
    a = np.asarray(pil).astype("uint8")
    H, W = a.shape[:2]
    if max(H, W) > cap:
        s = cap / float(max(H, W))
        a = cv2.resize(a, (max(8, int(W * s)), max(8, int(H * s))), interpolation=cv2.INTER_AREA)
    g = cv2.cvtColor(a, cv2.COLOR_RGB2GRAY)
    if len(_PREP) > 16:
        _PREP.clear()
    _PREP[key] = g
    return g


def _ink(g):
    import cv2
    th = cv2.threshold(g, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    dark = cv2.bitwise_not(th)
    cand = dark if dark.mean() < th.mean() else th
    share = cand.mean() / 255.0
    bs = max(31, (min(g.shape) // 12) | 1)
    import numpy as _np
    nl, lab, st, _ce = cv2.connectedComponentsWithStats((cand > 0).astype("uint8"), 8)
    surround = False
    if nl > 1:
        i = 1 + int(_np.argmax(st[1:, cv2.CC_STAT_AREA]))
        if st[i, cv2.CC_STAT_AREA] > 0.25 * cand.size:
            sides = int((lab[0] == i).any()) + int((lab[-1] == i).any()) +                 int((lab[:, 0] == i).any()) + int((lab[:, -1] == i).any())
            surround = sides >= 3
    if surround or share <= 0.004:
        for mode in (cv2.THRESH_BINARY_INV, cv2.THRESH_BINARY):
            ad = cv2.adaptiveThreshold(g, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, mode, bs, 10)
            sh = ad.mean() / 255.0
            if 0.004 < sh < share:
                cand, share = ad, sh
    return cand


def _runs(mask_1d, min_len=1):
    out, run = [], None
    n = len(mask_1d)
    for i in range(n):
        if mask_1d[i]:
            run = [i, i] if run is None else [run[0], i]
        elif run is not None:
            if run[1] - run[0] + 1 >= min_len:
                out.append((run[0], run[1]))
            run = None
    if run is not None and run[1] - run[0] + 1 >= min_len:
        out.append((run[0], run[1]))
    return out


def _hlines(ink, frac=0.45):
    import cv2
    import numpy as np
    H, W = ink.shape
    k = max(9, int(W * 0.30))
    d = max(1, int(0.006 * H))
    ink = cv2.morphologyEx(ink, cv2.MORPH_CLOSE, np.ones((1, max(3, int(0.008 * W))), "uint8"))
    thick = cv2.dilate(ink, np.ones((2 * d + 1, 1), "uint8"))
    op = cv2.morphologyEx(thick, cv2.MORPH_OPEN, np.ones((1, k), "uint8"))
    prof = (op > 0).sum(axis=1).astype("float64") / float(W)
    bands = []
    for a, b in _runs(prof >= frac):
        lo, hi = a + d, b - d
        if hi < lo:
            lo = hi = (a + b) // 2
        bands.append((lo, hi))
    return bands, prof


def _vruns(ink):
    import numpy as np
    m = (ink > 0)
    H, W = m.shape
    up = np.zeros((H, W), "int32")
    dn = np.zeros((H, W), "int32")
    for y in range(1, H):
        up[y] = (up[y - 1] + 1) * m[y]
    for y in range(H - 2, -1, -1):
        dn[y] = (dn[y + 1] + 1) * m[y]
    return (up + dn + 1) * m


def _rule_mask(ink, kfrac=0.30, dv=None):
    import cv2
    import numpy as np
    H, W = ink.shape
    d = max(1, int(0.006 * H)) if dv is None else max(1, int(dv))
    k = max(9, int(W * kfrac))
    op = cv2.morphologyEx(cv2.dilate(ink, np.ones((2 * d + 1, 1), "uint8")),
                          cv2.MORPH_OPEN, np.ones((1, k), "uint8"))
    band = cv2.bitwise_and(op, ink)
    if not band.any():
        return band
    runs = _vruns(ink)
    inband = runs[band > 0]
    thr = max(3.0, 2.6 * float(np.median(inband)))
    keep = ((band > 0) & (runs <= thr)).astype("uint8") * 255
    return keep


def _vlines(ink, y0, y1, frac=0.80):
    import numpy as np
    H, W = ink.shape
    y0 = max(0, int(y0))
    y1 = min(H, int(y1))
    if y1 - y0 < 3:
        return [], None
    band = ink[y0:y1, :]
    prof = (band > 0).sum(axis=0).astype("float64") / float(y1 - y0)
    return _runs(prof >= frac), prof


def _group(vals, tol):
    out = []
    for v in sorted(vals):
        if out and v - out[-1][-1] <= tol:
            g = out[-1]
            g[0].append(v)
            g[-1] = v
        else:
            out.append([[v], v])
    return [(sum(g[0]) / float(len(g[0])), min(g[0]), max(g[0]), len(g[0])) for g in out]


def _frac(ok):
    return 1.0 if ok else 0.0


def _beam(ink):
    import numpy as np
    H, W = ink.shape
    bands, prof = _hlines(ink, 0.55)
    if not bands:
        bands, prof = _hlines(ink, 0.40)
    if len(bands) < 2:
        return None
    ys = np.nonzero((ink > 0).any(axis=1))[0]
    if ys.size < 10:
        return None
    t, b = float(ys.min()), float(ys.max())
    h = b - t
    inner = [bd for bd in bands if t + 0.10 * h <= (bd[0] + bd[1]) / 2.0 <= t + 0.70 * h]
    if not inner:
        return None
    best = max(inner, key=lambda bd: (bd[1] - bd[0] + 1))
    return (int(best[0]), int(best[1]), (best[0] + best[1]) / 2.0)


def _beads(ink, beam, board_h):
    import cv2
    import numpy as np
    H, W = ink.shape
    bt, bb, by = beam
    lo = 0.010 * board_h
    hi = 0.34 * board_h
    found = []
    for k in (max(5, int(0.030 * board_h) | 1), max(5, int(0.050 * board_h) | 1)):
        op = cv2.morphologyEx(ink, cv2.MORPH_OPEN,
                              cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k)))
        nl, lab, st, ce = cv2.connectedComponentsWithStats(op, 8)
        for i in range(1, nl):
            x, y, w, h, a = st[i]
            if not (lo <= h <= hi and lo <= w <= 2.2 * hi):
                continue
            if not (0.45 <= w / float(max(1, h)) <= 3.2):
                continue
            if a < 0.35 * w * h:
                continue
            found.append({"cx": float(ce[i][0]), "cy": float(ce[i][1]), "top": int(y),
                          "bot": int(y + h), "h": int(h), "w": int(w), "src": "solid"})
    closed = cv2.morphologyEx(ink, cv2.MORPH_CLOSE, np.ones((3, 3), "uint8"))
    cnts, hier = cv2.findContours(closed, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    if hier is not None:
        for i, c in enumerate(cnts):
            if hier[0][i][3] == -1:
                continue
            x, y, w, h = cv2.boundingRect(c)
            if not (lo <= h <= hi and lo <= w <= 2.2 * hi):
                continue
            if not (0.45 <= w / float(max(1, h)) <= 3.2):
                continue
            if cv2.contourArea(c) < 0.30 * w * h:
                continue
            found.append({"cx": float(x + w / 2.0), "cy": float(y + h / 2.0), "top": int(y),
                          "bot": int(y + h), "h": int(h), "w": int(w), "src": "hole"})
    found = [b for b in found if not (b["top"] <= bb and b["bot"] >= bt)]
    found.sort(key=lambda b: (b["cx"], b["cy"]))
    out = []
    for b in found:
        dup = False
        for o in out:
            if abs(b["cx"] - o["cx"]) < 0.35 * max(b["h"], o["h"]) and \
               abs(b["cy"] - o["cy"]) < 0.55 * max(b["h"], o["h"]):
                dup = True
                break
        if not dup:
            out.append(b)
    if len(out) >= 6:
        mh = float(np.median([b["h"] for b in out]))
        mw = float(np.median([b["w"] for b in out]))
        out = [b for b in out if 0.55 * mh <= b["h"] <= 1.9 * mh
               and 0.45 * mw <= b["w"] <= 2.2 * mw]
    return out


def _rods(beads):
    import numpy as np
    if len(beads) < 4:
        return []
    xs = sorted(b["cx"] for b in beads)
    d = [xs[i + 1] - xs[i] for i in range(len(xs) - 1)]
    d = [v for v in d if v > 0.5]
    if not d:
        return []
    big = sorted(d)[max(0, int(0.72 * len(d))):]
    pitch = float(np.median(big)) if big else float(np.median(d))
    thr = max(3.0, 0.45 * pitch)
    groups, cur = [], [xs[0]]
    for v in xs[1:]:
        if v - cur[-1] <= thr:
            cur.append(v)
        else:
            groups.append(cur)
            cur = [v]
    groups.append(cur)
    centres = [sum(g) / float(len(g)) for g in groups]
    return sorted(centres, reverse=True)


def read_abacus(image, n_rods):
    """Read the beads each rod has against the beam and the value they show."""
    import numpy as np
    g = _prep(image)
    ink = _ink(g)
    H, W = ink.shape
    ys = np.nonzero((ink > 0).any(axis=1))[0]
    if ys.size < 20:
        return {"no_read": True, "reason": "blank"}
    board_h = float(ys.max() - ys.min())
    beam_span = _beam(ink)
    if beam_span is None:
        return {"no_read": True, "reason": "no_beam"}
    bt, bb, by = beam_span
    beads = _beads(ink, beam_span, board_h)
    if len(beads) < 6:
        return {"no_read": True, "reason": "no_beads_%d" % len(beads), "beam_y": by}
    centres = _rods(beads)
    if len(centres) < 2:
        return {"no_read": True, "reason": "no_rods", "n_beads": len(beads)}
    pitch = (max(centres) - min(centres)) / float(max(1, len(centres) - 1))
    med_h = float(np.median([b["h"] for b in beads]))
    tol = 0.62 * med_h
    rods, build = [], []
    for cx in centres:
        col = [b for b in beads if abs(b["cx"] - cx) < 0.45 * pitch]
        up_all = [b for b in col if b["bot"] <= bt + 0.25 * med_h]
        dn_all = [b for b in col if b["top"] >= bb - 0.25 * med_h]
        up, ref = 0, bt
        for b in sorted(up_all, key=lambda b: -b["bot"]):
            if ref - b["bot"] < tol:
                up += 1
                ref = b["top"]
            else:
                break
        dn, ref = 0, bb
        for b in sorted(dn_all, key=lambda b: b["top"]):
            if b["top"] - ref < tol:
                dn += 1
                ref = b["bot"]
            else:
                break
        rods.append([up, dn])
        build.append([len(up_all), len(dn_all)])
    value = 0
    for j, (u, l) in enumerate(rods):
        value += (5 * u + l) * (10 ** j)
    return {"no_read": False, "reason": None, "beam_y": round(float(by), 1),
            "n_beads": len(beads), "n_rods_measured": len(centres),
            "rod_pitch": round(float(pitch), 1), "rods": rods, "construction": build,
            "value": int(value), "median_bead_h": round(med_h, 1)}


def _want(want):
    return [[int(u), int(l)] for u, l in want]


def score_bead_positions(image, want, n_rods):
    """Share of non-zero rods set exactly as the key, less zero rods with beads moved."""
    reading = read_abacus(image, n_rods)
    if reading.get("no_read"):
        return {"no_read": True, "frac": 0.0, "reason": reading.get("reason")}
    w = _want(want)
    got = reading["rods"]
    nz = [j for j, (u, l) in enumerate(w) if (u or l)]
    zr = [j for j, (u, l) in enumerate(w) if not (u or l)]
    hit = sum(1 for j in nz if j < len(got) and list(got[j]) == w[j])
    bad = sum(1 for j in zr if j < len(got) and (got[j][0] or got[j][1]))
    f = max(0.0, (hit - bad) / float(max(1, len(nz))))
    return {"no_read": False, "frac": round(min(1.0, f), 4), "hit": hit, "wrong_zero_rods": bad,
            "n_nonzero": len(nz), "measured": got, "expected": w}


def score_high_symbols(image, want, n_rods):
    """Share of rods worth ten or more that show the key's bead pattern exactly."""
    reading = read_abacus(image, n_rods)
    if reading.get("no_read"):
        return {"no_read": True, "frac": 0.0, "reason": reading.get("reason")}
    w = [[int(u), int(l)] for u, l in want]
    got = reading["rods"]
    hi = [j for j, (u, l) in enumerate(w) if 5 * u + l >= 10]
    if not hi:
        return {"no_read": False, "frac": 1.0, "n_high": 0,
                "note": "this answer key has no rod above nine, so this leaf is vacuous on it"}
    ok = sum(1 for j in hi if j < len(got) and list(got[j]) == w[j])
    return {"no_read": False, "frac": round(ok / float(len(hi)), 4), "n_high": len(hi),
            "hit": ok, "rods": [w[j] for j in hi]}


def score_zero_rods(image, want, n_rods):
    """Share of the key's zero rods left with no beads against the beam."""
    reading = read_abacus(image, n_rods)
    if reading.get("no_read"):
        return {"no_read": True, "frac": 0.0, "reason": reading.get("reason")}
    w = _want(want)
    got = reading["rods"]
    zr = [j for j, (u, l) in enumerate(w) if not (u or l)]
    ok = sum(1 for j in zr if j < len(got) and not (got[j][0] or got[j][1]))
    return {"no_read": False, "frac": round(min(1.0, ok / float(max(1, len(zr)))), 4),
            "clear": ok, "n_zero_rods": len(zr)}


def score_rod_count(image, n_rods):
    """Full credit if the number of rods found equals the demanded number."""
    reading = read_abacus(image, n_rods)
    if reading.get("no_read"):
        return {"no_read": True, "frac": 0.0, "reason": reading.get("reason")}
    return {"no_read": False, "frac": _frac(int(reading["n_rods_measured"]) == int(n_rods)),
            "measured": reading["n_rods_measured"], "expected": int(n_rods)}


def score_construction(image, n_rods):
    """Share of rods built with two upper and five lower beads."""
    reading = read_abacus(image, n_rods)
    if reading.get("no_read"):
        return {"no_read": True, "frac": 0.0, "reason": reading.get("reason")}
    b = reading["construction"][:int(n_rods)]
    ok = sum(1 for u, l in b if u == 2 and l == 5)
    return {"no_read": False, "frac": round(min(1.0, ok / float(max(1, int(n_rods)))), 4),
            "measured": reading["construction"], "rods_built_right": ok}


def check_abacus_form(image, n_rods):
    """Full credit if the rod count is right and each rod has two upper and five lower beads."""
    reading = read_abacus(image, n_rods)
    if reading.get("no_read"):
        return {"no_read": False, "frac": 0.0, "reason": reading.get("reason")}
    b = reading["construction"]
    ok = (int(reading["n_rods_measured"]) == int(n_rods)
          and sum(1 for u, l in b if u == 2 and l == 5) == int(n_rods))
    return {"no_read": False, "frac": _frac(ok), "n_rods": reading["n_rods_measured"],
            "construction": b}


def abacus_overlay(image, want, n_rods):
    import os
    import hashlib
    import tempfile
    import cv2
    import numpy as np
    from PIL import Image
    g = _prep(image)
    ink = _ink(g)
    vis = cv2.cvtColor(g, cv2.COLOR_GRAY2BGR)
    m = read_abacus(image, n_rods)
    w = _want(want)
    if not m.get("no_read"):
        ys = np.nonzero((ink > 0).any(axis=1))[0]
        board_h = float(ys.max() - ys.min())
        bm = _beam(ink)
        cv2.line(vis, (0, int(bm[2])), (vis.shape[1] - 1, int(bm[2])), (255, 170, 80), 2)
        for b in _beads(ink, bm, board_h):
            cv2.circle(vis, (int(b["cx"]), int(b["cy"])), int(0.45 * b["h"]), (150, 150, 150), 1)
        cs = _rods(_beads(ink, bm, board_h))
        f = cv2.FONT_HERSHEY_SIMPLEX
        for j, cx in enumerate(cs):
            got = m["rods"][j] if j < len(m["rods"]) else [-1, -1]
            wj = w[j] if j < len(w) else [-1, -1]
            col = (60, 170, 60) if list(got) == list(wj) else (60, 60, 235)
            cv2.putText(vis, "%d%d" % (got[0], got[1]), (int(cx) - 14, vis.shape[0] - 26),
                        f, 0.45, col, 1, cv2.LINE_AA)
            cv2.putText(vis, "%d%d" % (wj[0], wj[1]), (int(cx) - 14, vis.shape[0] - 8),
                        f, 0.45, (90, 90, 90), 1, cv2.LINE_AA)
    d = os.path.join(tempfile.gettempdir(), "genolympiad_overlay")
    try:
        os.makedirs(d, exist_ok=True)
    except Exception:
        pass
    h = hashlib.md5(str(image).encode("utf-8", "replace")).hexdigest()[:12]
    p = os.path.join(d, "abacus_%s.png" % h)
    try:
        Image.fromarray(cv2.cvtColor(vis, cv2.COLOR_BGR2RGB)).save(p)
    except Exception:
        pass
    s = score_bead_positions(image, want, n_rods)
    return {"no_read": False, "frac": s["frac"], "overlay": p,
            "measured": s.get("measured"), "expected": s.get("expected")}

# end of read_abacus_code

# code: f_code
def full_score(value):
    """A fixed full score; the bead reading is only recorded here."""
    return 1.0

# end of f_code

# code: abacus_overlay_marked_code
_PREP = {}


def _prep(image, cap=1500):
    import numpy as np
    import cv2
    from PIL import Image
    key = (str(image), cap)
    hit = _PREP.get(key)
    if hit is not None:
        return hit
    pil = image.convert("RGB") if hasattr(image, "convert") else Image.open(str(image)).convert("RGB")
    a = np.asarray(pil).astype("uint8")
    H, W = a.shape[:2]
    if max(H, W) > cap:
        s = cap / float(max(H, W))
        a = cv2.resize(a, (max(8, int(W * s)), max(8, int(H * s))), interpolation=cv2.INTER_AREA)
    g = cv2.cvtColor(a, cv2.COLOR_RGB2GRAY)
    if len(_PREP) > 16:
        _PREP.clear()
    _PREP[key] = g
    return g


def _ink(g):
    import cv2
    th = cv2.threshold(g, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    dark = cv2.bitwise_not(th)
    cand = dark if dark.mean() < th.mean() else th
    share = cand.mean() / 255.0
    bs = max(31, (min(g.shape) // 12) | 1)
    import numpy as _np
    nl, lab, st, _ce = cv2.connectedComponentsWithStats((cand > 0).astype("uint8"), 8)
    surround = False
    if nl > 1:
        i = 1 + int(_np.argmax(st[1:, cv2.CC_STAT_AREA]))
        if st[i, cv2.CC_STAT_AREA] > 0.25 * cand.size:
            sides = int((lab[0] == i).any()) + int((lab[-1] == i).any()) +                 int((lab[:, 0] == i).any()) + int((lab[:, -1] == i).any())
            surround = sides >= 3
    if surround or share <= 0.004:
        for mode in (cv2.THRESH_BINARY_INV, cv2.THRESH_BINARY):
            ad = cv2.adaptiveThreshold(g, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, mode, bs, 10)
            sh = ad.mean() / 255.0
            if 0.004 < sh < share:
                cand, share = ad, sh
    return cand


def _runs(mask_1d, min_len=1):
    out, run = [], None
    n = len(mask_1d)
    for i in range(n):
        if mask_1d[i]:
            run = [i, i] if run is None else [run[0], i]
        elif run is not None:
            if run[1] - run[0] + 1 >= min_len:
                out.append((run[0], run[1]))
            run = None
    if run is not None and run[1] - run[0] + 1 >= min_len:
        out.append((run[0], run[1]))
    return out


def _hlines(ink, frac=0.45):
    import cv2
    import numpy as np
    H, W = ink.shape
    k = max(9, int(W * 0.30))
    d = max(1, int(0.006 * H))
    ink = cv2.morphologyEx(ink, cv2.MORPH_CLOSE, np.ones((1, max(3, int(0.008 * W))), "uint8"))
    thick = cv2.dilate(ink, np.ones((2 * d + 1, 1), "uint8"))
    op = cv2.morphologyEx(thick, cv2.MORPH_OPEN, np.ones((1, k), "uint8"))
    prof = (op > 0).sum(axis=1).astype("float64") / float(W)
    bands = []
    for a, b in _runs(prof >= frac):
        lo, hi = a + d, b - d
        if hi < lo:
            lo = hi = (a + b) // 2
        bands.append((lo, hi))
    return bands, prof


def _vruns(ink):
    import numpy as np
    m = (ink > 0)
    H, W = m.shape
    up = np.zeros((H, W), "int32")
    dn = np.zeros((H, W), "int32")
    for y in range(1, H):
        up[y] = (up[y - 1] + 1) * m[y]
    for y in range(H - 2, -1, -1):
        dn[y] = (dn[y + 1] + 1) * m[y]
    return (up + dn + 1) * m


def _rule_mask(ink, kfrac=0.30, dv=None):
    import cv2
    import numpy as np
    H, W = ink.shape
    d = max(1, int(0.006 * H)) if dv is None else max(1, int(dv))
    k = max(9, int(W * kfrac))
    op = cv2.morphologyEx(cv2.dilate(ink, np.ones((2 * d + 1, 1), "uint8")),
                          cv2.MORPH_OPEN, np.ones((1, k), "uint8"))
    band = cv2.bitwise_and(op, ink)
    if not band.any():
        return band
    runs = _vruns(ink)
    inband = runs[band > 0]
    thr = max(3.0, 2.6 * float(np.median(inband)))
    keep = ((band > 0) & (runs <= thr)).astype("uint8") * 255
    return keep


def _vlines(ink, y0, y1, frac=0.80):
    import numpy as np
    H, W = ink.shape
    y0 = max(0, int(y0))
    y1 = min(H, int(y1))
    if y1 - y0 < 3:
        return [], None
    band = ink[y0:y1, :]
    prof = (band > 0).sum(axis=0).astype("float64") / float(y1 - y0)
    return _runs(prof >= frac), prof


def _group(vals, tol):
    out = []
    for v in sorted(vals):
        if out and v - out[-1][-1] <= tol:
            g = out[-1]
            g[0].append(v)
            g[-1] = v
        else:
            out.append([[v], v])
    return [(sum(g[0]) / float(len(g[0])), min(g[0]), max(g[0]), len(g[0])) for g in out]


def _frac(ok):
    return 1.0 if ok else 0.0


def _beam(ink):
    import numpy as np
    H, W = ink.shape
    bands, prof = _hlines(ink, 0.55)
    if not bands:
        bands, prof = _hlines(ink, 0.40)
    if len(bands) < 2:
        return None
    ys = np.nonzero((ink > 0).any(axis=1))[0]
    if ys.size < 10:
        return None
    t, b = float(ys.min()), float(ys.max())
    h = b - t
    inner = [bd for bd in bands if t + 0.10 * h <= (bd[0] + bd[1]) / 2.0 <= t + 0.70 * h]
    if not inner:
        return None
    best = max(inner, key=lambda bd: (bd[1] - bd[0] + 1))
    return (int(best[0]), int(best[1]), (best[0] + best[1]) / 2.0)


def _beads(ink, beam, board_h):
    import cv2
    import numpy as np
    H, W = ink.shape
    bt, bb, by = beam
    lo = 0.010 * board_h
    hi = 0.34 * board_h
    found = []
    for k in (max(5, int(0.030 * board_h) | 1), max(5, int(0.050 * board_h) | 1)):
        op = cv2.morphologyEx(ink, cv2.MORPH_OPEN,
                              cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k)))
        nl, lab, st, ce = cv2.connectedComponentsWithStats(op, 8)
        for i in range(1, nl):
            x, y, w, h, a = st[i]
            if not (lo <= h <= hi and lo <= w <= 2.2 * hi):
                continue
            if not (0.45 <= w / float(max(1, h)) <= 3.2):
                continue
            if a < 0.35 * w * h:
                continue
            found.append({"cx": float(ce[i][0]), "cy": float(ce[i][1]), "top": int(y),
                          "bot": int(y + h), "h": int(h), "w": int(w), "src": "solid"})
    closed = cv2.morphologyEx(ink, cv2.MORPH_CLOSE, np.ones((3, 3), "uint8"))
    cnts, hier = cv2.findContours(closed, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    if hier is not None:
        for i, c in enumerate(cnts):
            if hier[0][i][3] == -1:
                continue
            x, y, w, h = cv2.boundingRect(c)
            if not (lo <= h <= hi and lo <= w <= 2.2 * hi):
                continue
            if not (0.45 <= w / float(max(1, h)) <= 3.2):
                continue
            if cv2.contourArea(c) < 0.30 * w * h:
                continue
            found.append({"cx": float(x + w / 2.0), "cy": float(y + h / 2.0), "top": int(y),
                          "bot": int(y + h), "h": int(h), "w": int(w), "src": "hole"})
    found = [b for b in found if not (b["top"] <= bb and b["bot"] >= bt)]
    found.sort(key=lambda b: (b["cx"], b["cy"]))
    out = []
    for b in found:
        dup = False
        for o in out:
            if abs(b["cx"] - o["cx"]) < 0.35 * max(b["h"], o["h"]) and \
               abs(b["cy"] - o["cy"]) < 0.55 * max(b["h"], o["h"]):
                dup = True
                break
        if not dup:
            out.append(b)
    if len(out) >= 6:
        mh = float(np.median([b["h"] for b in out]))
        mw = float(np.median([b["w"] for b in out]))
        out = [b for b in out if 0.55 * mh <= b["h"] <= 1.9 * mh
               and 0.45 * mw <= b["w"] <= 2.2 * mw]
    return out


def _rods(beads):
    import numpy as np
    if len(beads) < 4:
        return []
    xs = sorted(b["cx"] for b in beads)
    d = [xs[i + 1] - xs[i] for i in range(len(xs) - 1)]
    d = [v for v in d if v > 0.5]
    if not d:
        return []
    big = sorted(d)[max(0, int(0.72 * len(d))):]
    pitch = float(np.median(big)) if big else float(np.median(d))
    thr = max(3.0, 0.45 * pitch)
    groups, cur = [], [xs[0]]
    for v in xs[1:]:
        if v - cur[-1] <= thr:
            cur.append(v)
        else:
            groups.append(cur)
            cur = [v]
    groups.append(cur)
    centres = [sum(g) / float(len(g)) for g in groups]
    return sorted(centres, reverse=True)


def read_abacus(image, n_rods):
    import numpy as np
    g = _prep(image)
    ink = _ink(g)
    H, W = ink.shape
    ys = np.nonzero((ink > 0).any(axis=1))[0]
    if ys.size < 20:
        return {"no_read": True, "reason": "blank"}
    board_h = float(ys.max() - ys.min())
    bm = _beam(ink)
    if bm is None:
        return {"no_read": True, "reason": "no_beam"}
    bt, bb, by = bm
    beads = _beads(ink, bm, board_h)
    if len(beads) < 6:
        return {"no_read": True, "reason": "no_beads_%d" % len(beads), "beam_y": by}
    centres = _rods(beads)
    if len(centres) < 2:
        return {"no_read": True, "reason": "no_rods", "n_beads": len(beads)}
    pitch = (max(centres) - min(centres)) / float(max(1, len(centres) - 1))
    med_h = float(np.median([b["h"] for b in beads]))
    tol = 0.62 * med_h
    rods, build = [], []
    for cx in centres:
        col = [b for b in beads if abs(b["cx"] - cx) < 0.45 * pitch]
        up_all = [b for b in col if b["bot"] <= bt + 0.25 * med_h]
        dn_all = [b for b in col if b["top"] >= bb - 0.25 * med_h]
        up, ref = 0, bt
        for b in sorted(up_all, key=lambda b: -b["bot"]):
            if ref - b["bot"] < tol:
                up += 1
                ref = b["top"]
            else:
                break
        dn, ref = 0, bb
        for b in sorted(dn_all, key=lambda b: b["top"]):
            if b["top"] - ref < tol:
                dn += 1
                ref = b["bot"]
            else:
                break
        rods.append([up, dn])
        build.append([len(up_all), len(dn_all)])
    value = 0
    for j, (u, l) in enumerate(rods):
        value += (5 * u + l) * (10 ** j)
    return {"no_read": False, "reason": None, "beam_y": round(float(by), 1),
            "n_beads": len(beads), "n_rods_measured": len(centres),
            "rod_pitch": round(float(pitch), 1), "rods": rods, "construction": build,
            "value": int(value), "median_bead_h": round(med_h, 1)}


def _want(want):
    return [[int(u), int(l)] for u, l in want]


def score_bead_positions(image, want, n_rods):
    m = read_abacus(image, n_rods)
    if m.get("no_read"):
        return {"no_read": True, "frac": 0.0, "reason": m.get("reason")}
    w = _want(want)
    got = m["rods"]
    nz = [j for j, (u, l) in enumerate(w) if (u or l)]
    zr = [j for j, (u, l) in enumerate(w) if not (u or l)]
    hit = sum(1 for j in nz if j < len(got) and list(got[j]) == w[j])
    bad = sum(1 for j in zr if j < len(got) and (got[j][0] or got[j][1]))
    f = max(0.0, (hit - bad) / float(max(1, len(nz))))
    return {"no_read": False, "frac": round(min(1.0, f), 4), "hit": hit, "wrong_zero_rods": bad,
            "n_nonzero": len(nz), "measured": got, "expected": w}


def score_high_symbols(image, want, n_rods):
    m = read_abacus(image, n_rods)
    if m.get("no_read"):
        return {"no_read": True, "frac": 0.0, "reason": m.get("reason")}
    w = [[int(u), int(l)] for u, l in want]
    got = m["rods"]
    hi = [j for j, (u, l) in enumerate(w) if 5 * u + l >= 10]
    if not hi:
        return {"no_read": False, "frac": 1.0, "n_high": 0,
                "note": "this answer key has no rod above nine, so this leaf is vacuous on it"}
    ok = sum(1 for j in hi if j < len(got) and list(got[j]) == w[j])
    return {"no_read": False, "frac": round(ok / float(len(hi)), 4), "n_high": len(hi),
            "hit": ok, "rods": [w[j] for j in hi]}


def score_zero_rods(image, want, n_rods):
    m = read_abacus(image, n_rods)
    if m.get("no_read"):
        return {"no_read": True, "frac": 0.0, "reason": m.get("reason")}
    w = _want(want)
    got = m["rods"]
    zr = [j for j, (u, l) in enumerate(w) if not (u or l)]
    ok = sum(1 for j in zr if j < len(got) and not (got[j][0] or got[j][1]))
    return {"no_read": False, "frac": round(min(1.0, ok / float(max(1, len(zr)))), 4),
            "clear": ok, "n_zero_rods": len(zr)}


def score_rod_count(image, n_rods):
    m = read_abacus(image, n_rods)
    if m.get("no_read"):
        return {"no_read": True, "frac": 0.0, "reason": m.get("reason")}
    return {"no_read": False, "frac": _frac(int(m["n_rods_measured"]) == int(n_rods)),
            "measured": m["n_rods_measured"], "expected": int(n_rods)}


def score_construction(image, n_rods):
    m = read_abacus(image, n_rods)
    if m.get("no_read"):
        return {"no_read": True, "frac": 0.0, "reason": m.get("reason")}
    b = m["construction"][:int(n_rods)]
    ok = sum(1 for u, l in b if u == 2 and l == 5)
    return {"no_read": False, "frac": round(min(1.0, ok / float(max(1, int(n_rods)))), 4),
            "measured": m["construction"], "rods_built_right": ok}


def check_abacus_form(image, n_rods):
    m = read_abacus(image, n_rods)
    if m.get("no_read"):
        return {"no_read": False, "frac": 0.0, "reason": m.get("reason")}
    b = m["construction"]
    ok = (int(m["n_rods_measured"]) == int(n_rods)
          and sum(1 for u, l in b if u == 2 and l == 5) == int(n_rods))
    return {"no_read": False, "frac": _frac(ok), "n_rods": m["n_rods_measured"],
            "construction": b}


def abacus_overlay(image, want, n_rods):
    import os
    import hashlib
    import tempfile
    import cv2
    import numpy as np
    from PIL import Image
    g = _prep(image)
    ink = _ink(g)
    vis = cv2.cvtColor(g, cv2.COLOR_GRAY2BGR)
    m = read_abacus(image, n_rods)
    w = _want(want)
    if not m.get("no_read"):
        ys = np.nonzero((ink > 0).any(axis=1))[0]
        board_h = float(ys.max() - ys.min())
        bm = _beam(ink)
        cv2.line(vis, (0, int(bm[2])), (vis.shape[1] - 1, int(bm[2])), (255, 170, 80), 2)
        _mk("reckoning_beam", "polylines",
            [[0.0, float(bm[2])], [float(vis.shape[1] - 1), float(bm[2])]])
        beads = _beads(ink, bm, board_h)
        cs = _rods(beads)
        for b in beads:
            cv2.circle(vis, (int(b["cx"]), int(b["cy"])), int(0.45 * b["h"]), (150, 150, 150), 1)
            grp = "bead_rod_unmatched"
            if cs:
                j = min(range(len(cs)), key=lambda t: abs(cs[t] - b["cx"]))
                got = m["rods"][j] if j < len(m["rods"]) else [-1, -1]
                wj = w[j] if j < len(w) else [-1, -1]
                grp = "bead_rod_matched" if list(got) == list(wj) else "bead_rod_unmatched"
            _mk(grp, "circles", [float(b["cx"]), float(b["cy"]), 2.0 * 0.45 * float(b["h"])])
        f = cv2.FONT_HERSHEY_SIMPLEX
        for j, cx in enumerate(cs):
            got = m["rods"][j] if j < len(m["rods"]) else [-1, -1]
            wj = w[j] if j < len(w) else [-1, -1]
            col = (60, 170, 60) if list(got) == list(wj) else (60, 60, 235)
            cv2.putText(vis, "%d%d" % (got[0], got[1]), (int(cx) - 14, vis.shape[0] - 26),
                        f, 0.45, col, 1, cv2.LINE_AA)
            cv2.putText(vis, "%d%d" % (wj[0], wj[1]), (int(cx) - 14, vis.shape[0] - 8),
                        f, 0.45, (90, 90, 90), 1, cv2.LINE_AA)
    d = os.path.join(tempfile.gettempdir(), "genolympiad_overlay")
    try:
        os.makedirs(d, exist_ok=True)
    except Exception:
        pass
    h = hashlib.md5(str(image).encode("utf-8", "replace")).hexdigest()[:12]
    p = os.path.join(d, "abacus_%s.png" % h)
    try:
        Image.fromarray(cv2.cvtColor(vis, cv2.COLOR_BGR2RGB)).save(p)
    except Exception:
        pass
    s = score_bead_positions(image, want, n_rods)
    return {"no_read": False, "frac": s["frac"], "overlay": p, "work_w": int(vis.shape[1]),
            "measured": s.get("measured"), "expected": s.get("expected")}


def abacus_overlay_marked(image, want, n_rods):
    """Draw the beam and each rod's beads, marked as matching the key or not."""
    from PIL import Image as _I
    _mk_reset("reckoning_beam", "bead_rod_matched", "bead_rod_unmatched")
    r = dict(abacus_overlay(image, want, n_rods))
    src = image if hasattr(image, "size") else str(image)
    if hasattr(src, "size"):
        W0 = float(src.size[0])
    else:
        with _I.open(src) as _im:
            W0 = float(_im.size[0])
    _mk_scale(W0 / float(max(1, r.get("work_w") or W0)))
    r.update(_ovmark_pack(src))
    return r


_MARKS = {}


def _mk_reset(*groups):
    _MARKS.clear()
    for g in groups:
        _MARKS[g] = {"circles": [], "rects": [], "polylines": [], "points": []}


def _mk(group, kind, coords):
    b = _MARKS.setdefault(group, {"circles": [], "rects": [], "polylines": [], "points": []})
    b[kind].append(coords)


def _mk_scale(f):
    f = float(f)
    for b in _MARKS.values():
        b["circles"] = [[c[0] * f, c[1] * f, c[2] * f] for c in b["circles"]]
        b["rects"] = [[r[0] * f, r[1] * f, r[2] * f, r[3] * f] for r in b["rects"]]
        b["polylines"] = [[[p[0] * f, p[1] * f] for p in pl] for pl in b["polylines"]]
        b["points"] = [[p[0] * f, p[1] * f] for p in b["points"]]


def _ell_pts(cx, cy, a, b, deg, n=72):
    import math
    t0 = math.radians(deg)
    ct, st = math.cos(t0), math.sin(t0)
    out = []
    for i in range(n + 1):
        th = 2.0 * math.pi * i / float(n)
        x, y = a * math.cos(th), b * math.sin(th)
        out.append([cx + x * ct - y * st, cy + x * st + y * ct])
    return out


def _arrow_pts(x0, y0, x1, y1, head=0.22):
    import math
    ang = math.atan2(y1 - y0, x1 - x0)
    L = math.hypot(x1 - x0, y1 - y0) * float(head)
    b1 = [x1 - L * math.cos(ang - 0.45), y1 - L * math.sin(ang - 0.45)]
    b2 = [x1 - L * math.cos(ang + 0.45), y1 - L * math.sin(ang + 0.45)]
    return [[x0, y0], [x1, y1], b1, [x1, y1], b2]


def _ovmark_pack(canvas):
    from PIL import Image
    if hasattr(canvas, "size"):
        W, H = canvas.size
    else:
        with Image.open(str(canvas)) as _im:
            W, H = _im.size
    W, H = float(W), float(H)
    M = max(W, H)
    out = {"ref_anchors": [[0.0, 0.0], [W / M, 0.0], [W / M, H / M], [0.0, H / M]],
           "found_anchors": [[0.0, 0.0], [W, 0.0], [W, H], [0.0, H]],
           "mark_canvas": [int(W), int(H)], "n_marks": 0}
    for g, b in _MARKS.items():
        out["mk_" + g] = {
            "circles": [[c[0] / M, c[1] / M, c[2] / M] for c in b["circles"]],
            "rects": [[r[0] / M, r[1] / M, r[2] / M, r[3] / M] for r in b["rects"]],
            "polylines": [[[p[0] / M, p[1] / M] for p in pl] for pl in b["polylines"]],
            "points": [[p[0] / M, p[1] / M] for p in b["points"]],
        }
        out["n_marks"] += sum(len(v) for v in b.values())
    return out

# end of abacus_overlay_marked_code
