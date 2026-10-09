# code: helpers
from genolympiad.task_helpers import to_float
# end of helpers

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

def pr_unskew(x, y, ang, iw, ih):
    import math
    a = float(ang or 0.0)
    if a == 0.0:
        return x, y
    th = math.radians(a)
    cx, cy = float(iw) / 2.0, float(ih) / 2.0
    dx, dy = float(x) - cx, float(y) - cy
    ct, st = math.cos(th), math.sin(th)
    return cx + ct * dx - st * dy, cy + st * dx + ct * dy


def pr_angle(sk):
    try:
        vals = [float(v) for v in (sk or [])]
    except (TypeError, ValueError):
        return 0.0
    return vals[0] if vals else 0.0


def pr_paint(roll, skew, image, seq):
    """Paint each time column's wanted pitch-row square green or red by whether the read row matches."""
    if not isinstance(roll, dict) or roll.get('no_read'):
        return s6_blank()
    wh = ag_wh(image)
    if not wh:
        return s6_blank()
    W, H = wh
    try:
        iw = float(roll.get('img_w') or W)
        ih = float(roll.get('img_h') or H)
        xb = [float(v) for v in (roll.get('xb') or [])]
        yb = [float(v) for v in (roll.get('yb') or [])]
    except (TypeError, ValueError):
        return s6_blank()
    if len(xb) < 2 or len(yb) < 2 or iw <= 0 or ih <= 0:
        return s6_blank()
    sx, sy = W / iw, H / ih
    angle = pr_angle(skew)
    n_rows, n_cols = len(yb) - 1, len(xb) - 1
    lanes = list(reversed(list(roll.get('lane_rows') or [])))
    read_pitch_rows = list(roll.get('lane_index_per_col') or [])
    wanted = []
    for x in (seq or []):
        try:
            wanted.append(int(x))
        except (TypeError, ValueError):
            wanted.append(-1)
    square_ok = [None] * (n_rows * n_cols)
    for c in range(min(n_cols, len(wanted))):
        w = wanted[c]
        if w < 0 or w >= len(lanes):
            continue
        want_row = int(lanes[w])
        if want_row < 0 or want_row >= n_rows:
            continue
        g = read_pitch_rows[c] if c < len(read_pitch_rows) else None
        if g is None:
            continue
        if int(g) == w:
            square_ok[want_row * n_cols + c] = True
        else:
            square_ok[want_row * n_cols + c] = False
            if 0 <= int(g) < len(lanes):
                read_row = int(lanes[int(g)])
                if 0 <= read_row < n_rows:
                    square_ok[read_row * n_cols + c] = False
    cells = []
    for r in range(n_rows):
        for c in range(n_cols):
            cw, chh = xb[c + 1] - xb[c], yb[r + 1] - yb[r]
            ux, uy = pr_unskew((xb[c] + xb[c + 1]) / 2.0, (yb[r] + yb[r + 1]) / 2.0, angle, iw, ih)
            cells.append([(ux - cw / 2.0) * sx, (uy - chh / 2.0) * sy,
                          (ux + cw / 2.0) * sx, (uy + chh / 2.0) * sy])
    fx0, fy0 = pr_unskew(xb[0], yb[0], angle, iw, ih)
    fx1, fy1 = pr_unskew(xb[-1], yb[-1], angle, iw, ih)
    painted = s6_paint_px(cells, square_ok, W, H,
                     outline=[min(fx0, fx1) * sx, min(fy0, fy1) * sy,
                              max(fx0, fx1) * sx, max(fy0, fy1) * sy])
    painted['read_size'] = [n_rows, n_cols]
    painted['skew_deg'] = round(angle, 3)
    return painted

# end of code_anchorgrid

# code: read_roll_code

def _pil(image):
    from PIL import Image
    return image.convert("RGB") if hasattr(image, "convert") else Image.open(str(image)).convert("RGB")


_PREP_CACHE = {}
_SKEW = {}


def _skew_angle(g):
    import math
    import numpy as np
    import cv2
    H, W = g.shape
    e = cv2.Canny(cv2.GaussianBlur(g.astype("uint8"), (3, 3), 0), 50, 150)
    thr = int(0.22 * min(H, W))
    step = math.pi / 5400.0
    lim = math.radians(6.0)
    devs = []
    for lo, hi in ((0.0, lim), (math.pi - lim, math.pi),
                   (math.pi / 2 - lim, math.pi / 2 + lim)):
        L = cv2.HoughLines(e, 1, step, thr, min_theta=lo, max_theta=hi)
        if L is None:
            continue
        for rho_theta in L[:400]:
            th = math.degrees(float(rho_theta[0][1]))
            d = ((th + 45.0) % 90.0) - 45.0
            if abs(d) <= 6.0:
                devs.append(d)
    if len(devs) < 6:
        return 0.0
    med = float(np.median(devs))
    near = [d for d in devs if abs(d - med) <= 0.6]
    return float(np.mean(near)) if len(near) >= 4 else med


def _sharpen_skew(g, ang0, half=0.7, step=0.05):
    import math
    import numpy as np
    import cv2
    H, W = g.shape
    s = min(1.0, 700.0 / max(H, W))
    gg = cv2.resize(g, (max(32, int(W * s)), max(32, int(H * s))),
                    interpolation=cv2.INTER_AREA) if s < 1.0 else g
    h, w = gg.shape
    dy = np.abs(np.diff(gg, axis=0))
    dx = np.abs(np.diff(gg, axis=1))
    xs = np.arange(dy.shape[1])
    ys = np.arange(dx.shape[0])
    best, bang = None, ang0
    a = ang0 - half
    while a <= ang0 + half + 1e-9:
        tn = math.tan(math.radians(a))
        yy = np.clip(np.arange(dy.shape[0])[:, None] + np.round(xs[None, :] * tn).astype("int32"),
                     0, dy.shape[0] - 1)
        hp = dy[yy, xs[None, :]].mean(axis=1)
        xx = np.clip(np.arange(dx.shape[1])[None, :] - np.round(ys[:, None] * tn).astype("int32"),
                     0, dx.shape[1] - 1)
        vp = dx[ys[:, None], xx].mean(axis=0)
        sc = float((hp ** 2).sum() / max(1, hp.size) + (vp ** 2).sum() / max(1, vp.size))
        if best is None or sc > best:
            best, bang = sc, a
        a += step
    return float(bang)


def _prep(image, cap=1600):
    import numpy as np
    import cv2
    key = (str(image) if not hasattr(image, "convert") else "pil:%d" % id(image), cap)
    hit = _PREP_CACHE.get(key)
    if hit is not None:
        return hit
    pil = _pil(image)
    a = np.asarray(pil).astype("uint8")
    H, W = a.shape[:2]
    if max(H, W) > cap:
        s = cap / float(max(H, W))
        a = cv2.resize(a, (int(W * s), int(H * s)), interpolation=cv2.INTER_AREA)
        H, W = a.shape[:2]
    g = cv2.cvtColor(a, cv2.COLOR_RGB2GRAY).astype("float32")
    ang = _sharpen_skew(g, _skew_angle(g))
    _SKEW[key] = round(float(ang), 3)
    if abs(ang) > 0.12:
        M = cv2.getRotationMatrix2D((W / 2.0, H / 2.0), ang, 1.0)
        a = cv2.warpAffine(a, M, (W, H), flags=cv2.INTER_LINEAR,
                           borderMode=cv2.BORDER_REPLICATE)
        g = cv2.cvtColor(a, cv2.COLOR_RGB2GRAY).astype("float32")
    out = (a, g)
    if len(_PREP_CACHE) > 24:
        _PREP_CACHE.clear()
        _SKEW.clear()
        _SKEW[key] = round(float(ang), 3)
    _PREP_CACHE[key] = out
    return out


def _overlay_path(image, tag):
    import hashlib
    import os
    import tempfile
    d = os.path.join(tempfile.gettempdir(), "genolympiad_overlay")
    try:
        os.makedirs(d, exist_ok=True)
    except Exception:
        pass
    h = hashlib.md5(("%s|%s" % (str(image), tag)).encode("utf-8", "replace")).hexdigest()[:12]
    return os.path.join(d, "e7bpr_%s_%s.png" % (tag, h))


def _peak_groups(prof, min_frac, merge):
    import numpy as np
    idx = np.nonzero(prof >= min_frac)[0]
    if idx.size == 0:
        return []
    groups, cur = [], [int(idx[0])]
    for i in idx[1:]:
        if int(i) - cur[-1] <= merge:
            cur.append(int(i))
        else:
            groups.append(cur)
            cur = [int(i)]
    groups.append(cur)
    out = []
    for gp in groups:
        w = prof[gp]
        out.append(float(np.sum(np.array(gp, dtype="float64") * w) / max(1e-9, float(np.sum(w)))))
    return out


def _longest_run(mask, gap):
    import numpy as np
    idx = np.nonzero(mask)[0]
    if idx.size == 0:
        return (0, 0, 0)
    best = cur = (int(idx[0]), int(idx[0]))
    bestn = curn = 1
    for i in idx[1:]:
        if int(i) - cur[1] <= gap:
            cur = (cur[0], int(i))
            curn += 1
        else:
            if curn > bestn:
                best, bestn = cur, curn
            cur, curn = (int(i), int(i)), 1
    if curn > bestn:
        best, bestn = cur, curn
    return (best[0], best[1], bestn)


def name_column(image):
    import numpy as np
    import cv2
    a, g = _prep(image)
    H, W = g.shape
    g8 = g.astype("uint8")
    bs = max(15, int(0.05 * min(H, W)) | 1)
    cand = []
    for mode in (cv2.THRESH_BINARY_INV, cv2.THRESH_BINARY):
        ink = cv2.adaptiveThreshold(g8, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, mode, bs, 12)
        n, lbl, st, ce = cv2.connectedComponentsWithStats(ink, 8)
        for i in range(1, n):
            x, y, w, h, area = st[i]
            if area < 30:
                continue
            if not (0.012 * H <= h <= 0.22 * H):
                continue
            if not (0.006 * W <= w <= 0.10 * W):
                continue
            if area / float(max(1, w * h)) > 0.85:
                continue
            if float(ce[i][0]) > 0.42 * W:
                continue
            cand.append({"cx": float(ce[i][0]), "cy": float(ce[i][1]),
                         "x": int(x), "y": int(y), "w": int(w), "h": int(h)})
    if len(cand) < 3:
        return {"found": False, "reason": "no_glyphs_%d" % len(cand), "x_right": 0.0, "glyphs": []}
    best = None
    for seed in cand:
        grp = [d for d in cand if abs(d["cx"] - seed["cx"]) <= max(12.0, 0.030 * W)]
        ded = []
        for d in sorted(grp, key=lambda d: d["cy"]):
            if ded and abs(d["cy"] - ded[-1]["cy"]) < 0.4 * max(d["h"], ded[-1]["h"]):
                continue
            ded.append(d)
        if len(ded) < 3:
            continue
        span = max(d["cy"] for d in ded) - min(d["cy"] for d in ded)
        if span < 0.35 * H:
            continue
        key = (len(ded), span)
        if best is None or key > best[0]:
            best = (key, ded)
    if best is None:
        return {"found": False, "reason": "no_stack", "x_right": 0.0, "glyphs": []}
    grp = best[1]
    return {"found": True, "x_right": float(max(d["x"] + d["w"] for d in grp)),
            "x_left": float(min(d["x"] for d in grp)), "n_glyphs": len(grp),
            "glyphs": [{"cy": d["cy"], "cx": d["cx"], "x": d["x"], "y": d["y"],
                        "w": d["w"], "h": d["h"]} for d in grp]}


def _regularity(vals):
    import numpy as np
    v = sorted(float(x) for x in vals)
    if len(v) < 3:
        return (0, 0.0, 1.0)
    dif = np.diff(v)
    med = float(np.median(dif))
    if med <= 1.0:
        return (0, 0.0, 1.0)
    keep = [d for d in dif if 0.6 * med <= d <= 1.6 * med]
    period = float(np.median(keep)) if keep else med
    if period <= 1.0:
        return (0, 0.0, 1.0)
    ks = [int(round((x - v[0]) / period)) for x in v]
    on = [(k, x) for k, x in zip(ks, v) if abs(v[0] + k * period - x) <= 0.22 * period]
    if len(on) < 3:
        return (len(on), period, 1.0)
    kk = np.array([p[0] for p in on], dtype="float64")
    vv = np.array([p[1] for p in on], dtype="float64")
    b, a0 = np.polyfit(kk, vv, 1)
    if b <= 1.0:
        return (len(on), period, 1.0)
    res = float(np.mean(np.abs(a0 + b * kk - vv))) / b
    return (len(on), float(b), res)


def _rule_ladder(g, xcut):
    import numpy as np
    import cv2
    H, W = g.shape
    dy = np.abs(np.diff(g, axis=0))
    dx = np.abs(np.diff(g, axis=1))
    mad = float(np.median(dy)) + float(np.median(dx))
    base = max(8.0, 3.0 * mad)
    ymid0, ymid1 = int(0.12 * H), int(0.88 * H)
    xc = int(max(0, min(W - 8, xcut)))
    best = None
    dil = 5
    dyD = cv2.dilate(dy, cv2.getStructuringElement(cv2.MORPH_RECT, (1, dil)))
    dxD = cv2.dilate(dx, cv2.getStructuringElement(cv2.MORPH_RECT, (dil, 1)))
    for t in (base, 1.7 * base, 0.6 * base, 3.0 * base, 6.0 * base, 10.0 * base):
        vp = (dxD[ymid0:ymid1] > t).mean(axis=0)
        hp = (dyD[:, xc:] > t).mean(axis=1)
        for frac in (0.55, 0.42, 0.68, 0.32, 0.80):
            xs = [v for v in _peak_groups(vp, frac, max(3, W // 200)) if v >= xcut - 2]
            if len(xs) < 4:
                continue
            nx, px, rx = _regularity(xs)
            if nx < 4:
                continue
            ys = _peak_groups(hp, frac, max(3, H // 200))
            if len(ys) < 3:
                continue
            ny, py, ry = _regularity(ys)
            if ny < 3:
                continue
            key = (nx + ny - 1.5 * ((len(xs) - nx) + (len(ys) - ny)), -(rx + ry))
            if best is None or key > best[0]:
                best = (key, xs, ys, dyD, dxD, t, frac, dil)
    if best is None:
        return None
    return {"xs": best[1], "ys": best[2], "dy": best[3], "dx": best[4],
            "gthr": best[5], "frac": best[6], "dilate": best[7]}


def lattice(image, gthr=None, frac=None):
    import numpy as np
    a, g = _prep(image)
    H, W = g.shape
    nc = name_column(image)
    xcut = nc["x_right"] if nc.get("found") else 0.0
    lad = _rule_ladder(g, xcut)
    if lad is None:
        return {"no_read": True, "reason": "no_regular_grid", "name_col": nc}
    dy, dx, xs = lad["dy"], lad["dx"], lad["xs"]
    gthr = lad["gthr"]
    gapy = max(4, H // 60)
    y0s, y1s = [], []
    for x in xs:
        xi = min(W - 2, max(0, int(round(x))))
        band = (dx[:, max(0, xi - 1):xi + 2] > gthr).any(axis=1)
        lo, hi, cnt = _longest_run(band, gapy)
        if cnt > 0.25 * H:
            y0s.append(lo)
            y1s.append(hi)
    if not y0s:
        return {"no_read": True, "reason": "no_vertical_extent", "name_col": nc}
    Y0, Y1 = float(np.median(y0s)), float(np.median(y1s))
    if Y1 - Y0 < 0.25 * H:
        return {"no_read": True, "reason": "lattice_too_short", "name_col": nc}
    xlo, xhi = int(min(xs)), int(max(xs))
    ys = [v for v in lad["ys"] if Y0 - 4 <= v <= Y1 + 4]
    if len(ys) < 3:
        return {"no_read": True, "reason": "few_horizontal_rules_%d" % len(ys), "name_col": nc}
    gapx = max(4, W // 60)
    x1s = []
    for y in ys:
        yi = min(H - 2, max(0, int(round(y))))
        band = (dy[max(0, yi - 1):yi + 2, :] > gthr).any(axis=0)
        band[:int(max(0, xlo - 2))] = False
        lo, hi, cnt = _longest_run(band, gapx)
        if cnt > 0.25 * W:
            x1s.append(hi)
    if not x1s:
        return {"no_read": True, "reason": "no_horizontal_extent", "name_col": nc}
    X0, X1 = float(min(xs)), float(np.median(x1s))
    if X1 - X0 < 0.25 * W:
        return {"no_read": True, "reason": "lattice_too_narrow", "name_col": nc}
    xin = sorted([v for v in xs if X0 - 3 <= v <= X1 + 3])
    if len(xin) < 3:
        return {"no_read": True, "reason": "few_column_rules", "name_col": nc}
    dif = list(np.diff(xin))
    med = float(np.median(dif))
    keep = [d for d in dif if 0.6 * med <= d <= 1.6 * med]
    period = float(np.median(keep)) if keep else med
    if period <= 1.0:
        return {"no_read": True, "reason": "degenerate_pitch", "name_col": nc}
    ks = [int(round((v - X0) / period)) for v in xin]
    pick = [(k, v) for k, v in zip(ks, xin) if abs(X0 + k * period - v) <= 0.28 * period]
    if len(pick) >= 3:
        kk = np.array([p[0] for p in pick], dtype="float64")
        vv = np.array([p[1] for p in pick], dtype="float64")
        b, a0 = np.polyfit(kk, vv, 1)
        if b > 1.0:
            period, X0 = float(b), float(a0)
    span = (X1 - X0) / period
    n_cols = int(span) + (1 if (span - int(span)) >= 0.35 else 0)
    n_cols = max(1, n_cols)
    yin = sorted(ys)
    step = (Y1 - Y0) / float(max(1, len(yin) - 1))
    if abs(yin[0] - Y0) > 0.25 * step:
        yin = [Y0] + yin
    if abs(yin[-1] - Y1) > 0.25 * step:
        yin = yin + [Y1]
    return {"no_read": False, "X0": X0, "X1": X1, "Y0": Y0, "Y1": Y1,
            "period_x": period, "n_cols": n_cols, "n_rows": len(yin) - 1,
            "xb": [X0 + k * period for k in range(n_cols + 1)], "yb": yin,
            "img_w": W, "img_h": H, "name_col": nc}


def read_roll(image, seq=None, n_lanes_want=7):
    """Find the roll grid, read which pitch row is marked in each time column, and score it."""
    import numpy as np
    grid = lattice(image)
    if grid.get("no_read"):
        return {"no_read": True, "reason": grid.get("reason"), "n_cols": 0, "n_rows": 0,
                "n_lanes": 0}
    a, g = _prep(image)
    xb, yb = grid["xb"], grid["yb"]
    n_cols, n_rows = grid["n_cols"], grid["n_rows"]
    name_col = grid["name_col"]
    lane_rows = []
    if name_col.get("found"):
        for glyph in name_col["glyphs"]:
            for r in range(n_rows):
                if yb[r] <= glyph["cy"] < yb[r + 1] and r not in lane_rows:
                    lane_rows.append(r)
                    break
    n_lanes = len(lane_rows)
    if not lane_rows:
        lane_rows = list(range(n_rows))
    lane_rows.sort()
    HH, WW = a.shape[:2]
    cells = np.zeros((n_rows, n_cols, 3), dtype="float64")
    for r in range(n_rows):
        for c in range(n_cols):
            y0, y1 = yb[r], yb[r + 1]
            x0, x1 = xb[c], xb[c + 1]
            py0, py1 = int(y0 + 0.30 * (y1 - y0)), int(y0 + 0.70 * (y1 - y0))
            px0, px1 = int(x0 + 0.30 * (x1 - x0)), int(x0 + 0.70 * (x1 - x0))
            py0, px0 = max(0, min(py0, HH - 2)), max(0, min(px0, WW - 2))
            py1, px1 = max(py0 + 1, min(py1, HH - 1)), max(px0 + 1, min(px1, WW - 1))
            cells[r, c] = a[py0:py1, px0:px1].reshape(-1, 3).mean(axis=0)
    bg = np.median(cells.reshape(-1, 3), axis=0)
    dist = np.sqrt(((cells - bg) ** 2).sum(axis=2))
    d98 = float(np.percentile(dist, 98))
    filled = dist > max(30.0, 0.45 * d98)
    if d98 < 45.0:
        filled[:, :] = False
    lane_order = list(reversed(lane_rows))
    pitch_row_per_col, per_col = [], []
    for c in range(n_cols):
        filled_rows = [r for r in range(n_rows) if filled[r, c]]
        per_col.append(len(filled_rows))
        if len(filled_rows) == 0:
            pitch_row_per_col.append(-1)
        elif len(filled_rows) == 1 and filled_rows[0] in lane_order:
            pitch_row_per_col.append(lane_order.index(filled_rows[0]))
        else:
            pitch_row_per_col.append(None)
    out = {"no_read": False, "n_cols": n_cols, "n_rows": n_rows, "n_lanes": n_lanes,
           "lane_rows": lane_rows, "marks_per_col": per_col, "lane_index_per_col": pitch_row_per_col,
           "d98": round(d98, 1), "X0": grid["X0"], "X1": grid["X1"], "Y0": grid["Y0"],
           "Y1": grid["Y1"], "xb": xb, "yb": yb, "img_w": grid["img_w"], "img_h": grid["img_h"]}
    if seq is not None:
        wanted = [int(s) for s in seq]
        n_ok = sum(1 for i, w in enumerate(wanted)
                   if i < len(pitch_row_per_col) and pitch_row_per_col[i] is not None and pitch_row_per_col[i] == w)
        expected_marks = [0 if w < 0 else 1 for w in wanted]
        m_ok = sum(1 for i, e in enumerate(expected_marks) if i < len(per_col) and per_col[i] == e)
        out["n_correct"] = n_ok
        out["seq_len"] = len(wanted)
        out["col_frac"] = round(n_ok / float(max(1, len(wanted))), 4)
        out["mark_frac"] = round(m_ok / float(max(1, len(expected_marks))), 4)
        out["dims_ok"] = bool(n_rows == n_lanes_want and n_lanes == n_lanes_want
                              and n_cols == len(wanted))
    return out


def roll_overlay(image, seq, n_lanes_want=7, tag="roll"):
    """Draw the grid, the wanted and the actually filled squares, and save the overlay image."""
    import numpy as np
    import cv2
    from PIL import Image
    roll = read_roll(image, seq, n_lanes_want)
    base, _g = _prep(image)
    canvas = np.array(base).copy()
    H0, W0 = canvas.shape[:2]
    if not roll.get("no_read"):
        sx = sy = 1.0
        line_width = max(2, int(0.0025 * min(H0, W0)))
        font_scale = 0.65 * min(W0, H0) / 1024.0
        xb, yb = roll["xb"], roll["yb"]
        lanes = list(reversed(roll["lane_rows"]))
        for x in xb:
            cv2.line(canvas, (int(x * sx), int(yb[0] * sy)), (int(x * sx), int(yb[-1] * sy)),
                     (0, 190, 200), 1)
        for y in yb:
            cv2.line(canvas, (int(xb[0] * sx), int(y * sy)), (int(xb[-1] * sx), int(y * sy)),
                     (0, 190, 200), 1)
        for c, want in enumerate(seq):
            if c >= roll["n_cols"]:
                break
            cx = int(0.5 * (xb[c] + xb[c + 1]) * sx)
            top = int(yb[0] * sy)
            bot = int(yb[-1] * sy)
            cv2.putText(canvas, str(c + 1), (cx - int(9 * font_scale * 2), max(16, top - int(26 * font_scale * 2))),
                        cv2.FONT_HERSHEY_SIMPLEX, font_scale, (0, 190, 200), line_width)
            if 0 <= int(want) < len(lanes):
                r = lanes[int(want)]
                y0, y1 = int(yb[r] * sy), int(yb[r + 1] * sy)
                x0, x1 = int(xb[c] * sx), int(xb[c + 1] * sx)
                cv2.rectangle(canvas, (x0 + 3, y0 + 3), (x1 - 3, y1 - 3), (0, 190, 0), line_width)
                cv2.line(canvas, (cx, max(2, top - int(18 * font_scale * 2))), (cx, y0 + 3), (0, 190, 0), 1)
            read_pitch_row = roll["lane_index_per_col"][c]
            if read_pitch_row is not None and read_pitch_row != int(want) and 0 <= read_pitch_row < len(lanes):
                r = lanes[read_pitch_row]
                y0, y1 = int(yb[r] * sy), int(yb[r + 1] * sy)
                x0, x1 = int(xb[c] * sx), int(xb[c + 1] * sx)
                cv2.rectangle(canvas, (x0 + 7, y0 + 7), (x1 - 7, y1 - 7), (220, 0, 200), line_width)
                cv2.line(canvas, (cx, min(H0 - 2, bot + int(18 * font_scale * 2))), (cx, y1 - 7),
                         (220, 0, 200), 1)
        for gl in (name_column(image) or {}).get("glyphs", []):
            cv2.rectangle(canvas, (int(gl["x"] * sx) - 4, int(gl["y"] * sy) - 4),
                          (int((gl["x"] + gl["w"]) * sx) + 4, int((gl["y"] + gl["h"]) * sy) + 4),
                          (255, 140, 0), max(1, line_width - 1))
        skew = 0.0
        for k, v in _SKEW.items():
            if k[0] == (str(image) if not hasattr(image, "convert") else "pil:%d" % id(image)):
                skew = v
        caption = ["green = the cell this step demands;  magenta = the cell actually filled;  "
               "orange = the lane letters the read is anchored on",
               "lanes labelled %d   grid rows %d   time columns %d   columns matching the line "
               "%s/%s   (frame straightened by %.2f deg before measuring)"
               % (roll["n_lanes"], roll["n_rows"], roll["n_cols"], roll.get("n_correct"), roll.get("seq_len"),
                  skew)]
        cfs = min(font_scale, 0.78 * W0 / max(len(caption[0]), len(caption[1])) / 9.0)
        lh = int(30 * cfs * 2)
        band = np.full((2 * lh + 16, W0, 3), 18, dtype=canvas.dtype)
        for i, line in enumerate(caption):
            cv2.putText(band, line, (10, (i + 1) * lh), cv2.FONT_HERSHEY_SIMPLEX, cfs,
                        (245, 245, 245), max(1, line_width - 1))
        canvas = np.vstack([canvas, band])
    path = _overlay_path(image, tag)
    Image.fromarray(canvas).save(path)
    out = dict(roll)
    out["path"] = path
    return out

# end of read_roll_code

# code: f_code
def grid_size_ok(n_rows, n_cols):
    """1 if the read grid has at least 3 rows and 4 columns, else 0."""
    return 1.0 if (int(n_rows) >= 3 and int(n_cols) >= 4) else 0.0

# end of f_code

# code: f_code_2
def dims_score(ok):
    """1 if the pitch-row and column counts match the reference, else 0."""
    return 1.0 if bool(ok) else 0.0

# end of f_code_2

# code: f_code_3
def column_share(value):
    """The share of time columns whose marked pitch row matches the reference line."""
    return 0.0 if value is None else float(value)

# end of f_code_3
