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

def paint_lamp_grid(m, want_rows, want_cols, want_matrix):
    """Overlay each lamp square, marked right or wrong against the reference pattern."""
    if not isinstance(m, dict) or m.get('no_read'):
        return s6_blank()
    try:
        W, H = float(m['orig_w']), float(m['orig_h'])
        iw, ih = float(m['img_w']), float(m['img_h'])
        px, py = float(m['px']), float(m['py'])
        phx, phy = float(m['phx']), float(m['phy'])
        kx0, ky0 = int(m['kx0']), int(m['ky0'])
        rows, cols = int(m['rows']), int(m['cols'])
    except (KeyError, TypeError, ValueError):
        return s6_blank()
    if W <= 0 or H <= 0 or iw <= 0 or ih <= 0 or rows < 1 or cols < 1:
        return s6_blank()
    sx, sy = W / iw, H / ih
    cw, ch = px * sx, py * sy
    ox, oy = (phx + kx0 * px) * sx, (phy + ky0 * py) * sy
    got = list(m.get('matrix') or [])
    want = list(want_matrix or [])
    dims_ok = (rows == int(want_rows) and cols == int(want_cols))
    cells, oks = [], []
    for r in range(rows):
        for c in range(cols):
            x0, y0 = ox + c * cw, oy + r * ch
            cells.append([x0 + 0.14 * cw, y0 + 0.14 * ch, x0 + 0.86 * cw, y0 + 0.86 * ch])
            lit = None
            if r < len(got) and c < len(got[r]):
                lit = (got[r][c] == '#')
            if lit is None or not dims_ok:
                oks.append(None)
            else:
                line = want[r] if r < len(want) else ''
                oks.append(lit == (c < len(line) and line[c] == '#'))
    paint = s6_paint_px(cells, oks, W, H,
                     outline=[ox, oy, ox + cols * cw, oy + rows * ch])
    paint['dims_ok'] = bool(dims_ok)
    paint['read_size'] = [rows, cols]
    return paint

# end of code_anchorgrid

# code: dotmatrix_dims_code

def _pil(image):
    from PIL import Image
    return image.convert("RGB") if hasattr(image, "convert") else Image.open(str(image)).convert("RGB")


def _prep(image, cap=1400):
    import numpy as np
    import cv2
    rgb = np.asarray(_pil(image))
    OH, OW = rgb.shape[:2]
    if max(OH, OW) > cap:
        s = float(cap) / max(OH, OW)
        rgb = cv2.resize(rgb, (int(OW * s), int(OH * s)), interpolation=cv2.INTER_AREA)
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY).astype(np.float32)
    return rgb, gray, OW, OH


def _on_mask(gray):
    import numpy as np
    import cv2
    H, W = gray.shape
    g8 = np.clip(cv2.GaussianBlur(gray, (3, 3), 0), 0, 255).astype(np.uint8)
    _t, th = cv2.threshold(g8, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    hi = (th > 0).astype(np.uint8)
    on, bright = (hi, True) if hi.mean() <= 0.5 else (1 - hi, False)
    k = max(3, int(round(0.006 * max(H, W))) | 1)
    on = cv2.morphologyEx(on, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k)))
    return on, bright


def _prof(img, axis, olo, ohi):
    return img[olo:ohi + 1, :].sum(axis=0) if axis == 0 else img[:, olo:ohi + 1].sum(axis=1)


def _coh(prof, pmin, pmax, step=0.1, rel=0.85):
    import numpy as np
    x = np.maximum(np.asarray(prof, dtype=np.float64), 0.0)
    tot = float(x.sum())
    if tot <= 0 or pmax <= pmin + 1:
        return None
    idx = np.arange(x.size)
    Ps = np.arange(pmin, pmax, step)
    S = np.array([abs(np.sum(x * np.exp(-2j * np.pi * idx / P))) / tot for P in Ps])
    ok = np.flatnonzero(S >= rel * float(S.max()))
    return float(Ps[ok[-1]])


def _strip_fracs(on, axis, P, ph, lo, hi, olo, ohi):
    import numpy as np
    k0, k1 = int(np.floor((lo - ph) / P)), int(np.floor((hi - ph) / P))
    out = []
    for k in range(k0, k1 + 1):
        c = ph + (k + 0.5) * P
        a, b = int(round(c - 0.30 * P)), int(round(c + 0.30 * P))
        if axis == 0:
            a, b = max(0, a), min(on.shape[1], b)
            out.append(float(on[olo:ohi + 1, a:b].mean()) if b > a else 0.0)
        else:
            a, b = max(0, a), min(on.shape[0], b)
            out.append(float(on[a:b, olo:ohi + 1].mean()) if b > a else 0.0)
    return np.asarray(out)


def _best_phase(on, axis, P, lo, hi, olo, ohi):
    import numpy as np
    best = (-1.0, 0.0)
    for ph in np.arange(0.0, P, max(0.25, P / 40.0)):
        f = _strip_fracs(on, axis, P, ph, lo, hi, olo, ohi)
        if f.size:
            s = float(np.mean(f))
            if s > best[0]:
                best = (s, float(ph))
    return best[1], best[0]


def _cell_fracs(ii, H, W, px, phx, py, phy, x0, x1, y0, y1):
    import numpy as np
    kx0, kx1 = int(np.floor((x0 - phx) / px)), int(np.floor((x1 - phx) / px))
    ky0, ky1 = int(np.floor((y0 - phy) / py)), int(np.floor((y1 - phy) / py))
    out = np.zeros((ky1 - ky0 + 1, kx1 - kx0 + 1), dtype=np.float64)
    for r in range(ky0, ky1 + 1):
        cy = phy + (r + 0.5) * py
        u, v = max(0, int(round(cy - 0.30 * py))), min(H, int(round(cy + 0.30 * py)))
        for c in range(kx0, kx1 + 1):
            cx = phx + (c + 0.5) * px
            a, b = max(0, int(round(cx - 0.30 * px))), min(W, int(round(cx + 0.30 * px)))
            if b <= a or v <= u:
                continue
            out[r - ky0, c - kx0] = (ii[v, b] - ii[u, b] - ii[v, a] + ii[u, a]) / float((v - u) * (b - a))
    return out


def _fold_submultiple(ii, on, H, W, px, phx, py, phy, x0, x1, y0, y1):
    for _ in range(4):
        M = _cell_fracs(ii, H, W, px, phx, py, phy, x0, x1, y0, y1) >= 0.40
        if not M.any():
            break
        folded = False
        if M.shape[1] >= 4 and 2.0 * px <= W / 3.0:
            has = M.any(axis=0)
            for par in (0, 1):
                a, b = has[par::2], has[1 - par::2]
                if a.size >= 2 and not a.any() and b.any():
                    px = 2.0 * px
                    phx, _s = _best_phase(on, 0, px, x0, x1, y0, y1)
                    folded = True
                    break
        if not folded and M.shape[0] >= 4 and 2.0 * py <= H / 3.0:
            has = M.any(axis=1)
            for par in (0, 1):
                a, b = has[par::2], has[1 - par::2]
                if a.size >= 2 and not a.any() and b.any():
                    py = 2.0 * py
                    phy, _s = _best_phase(on, 1, py, y0, y1, x0, x1)
                    folded = True
                    break
        if not folded:
            break
    return px, phx, py, phy


def _cell_contrast(gray, P, ph, Pc, phc, k, axis, j0, j1):
    import numpy as np
    c = ph + (k + 0.5) * P
    r = max(1, int(round(0.14 * P)))
    d = []
    for j in range(j0, j1 + 1):
        vals = []
        for v in (phc + (j + 0.5) * Pc, phc + j * Pc):
            x, y = (c, v) if axis == 0 else (v, c)
            x0, x1 = int(round(x - r)), int(round(x + r)) + 1
            y0, y1 = int(round(y - r)), int(round(y + r)) + 1
            if x0 < 0 or y0 < 0 or x1 > gray.shape[1] or y1 > gray.shape[0]:
                vals = None
                break
            vals.append(float(gray[y0:y1, x0:x1].mean()))
        if vals:
            d.append(abs(vals[0] - vals[1]))
    return float(np.median(d)) if len(d) >= 2 else 0.0


def _extend(gray, P, ph, Pc, phc, axis, k0, k1, j0, j1, limit, thr):
    import numpy as np
    inside = [_cell_contrast(gray, P, ph, Pc, phc, k, axis, j0, j1) for k in range(k0, k1 + 1)]
    ref = float(np.median(inside)) if inside else 0.0
    lo, hi = k0, k1
    for _ in range(120):
        if ph + (lo - 1) * P < -0.20 * P or \
                _cell_contrast(gray, P, ph, Pc, phc, lo - 1, axis, j0, j1) < thr:
            break
        lo -= 1
    for _ in range(120):
        if ph + (hi + 2) * P > limit + 0.20 * P or \
                _cell_contrast(gray, P, ph, Pc, phc, hi + 1, axis, j0, j1) < thr:
            break
        hi += 1
    return lo, hi, round(ref, 2)


def dotmatrix_grid(image):
    import numpy as np
    import cv2
    rgb, gray, OW, OH = _prep(image)
    H, W = gray.shape
    on8, bright = _on_mask(gray)
    ys, xs = np.nonzero(on8)
    if xs.size < 0.0006 * H * W:
        return {"no_read": True, "reason": "no_lit_cells"}
    x0, x1, y0, y1 = int(xs.min()), int(xs.max()), int(ys.min()), int(ys.max())
    on = on8.astype(np.float32)
    ii = cv2.integral(on.astype(np.float64))
    ex = np.abs(cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3))
    ey = np.abs(cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3))

    def cands(axis, edge, lo, hi, olo, ohi, dim):
        ps = set()
        for p in (_coh(_prof(on, axis, olo, ohi), 12.0, dim / 4.0),
                  _coh(_prof(edge, axis, olo, ohi), 12.0, dim / 4.0)):
            if p:
                for m in (0.5, 1.0, 2.0):
                    if 10.0 <= p * m <= dim / 3.0:
                        ps.add(round(p * m, 2))
        return [(P, _best_phase(on, axis, P, lo, hi, olo, ohi)[0]) for P in sorted(ps)]

    CX = cands(0, ex, x0, x1, y0, y1, W)
    CY = cands(1, ey, y0, y1, x0, x1, H)
    if not CX or not CY:
        return {"no_read": True, "reason": "no_period"}
    fits = []
    for px, phx in CX:
        for py, phy in CY:
            f = _cell_fracs(ii, H, W, px, phx, py, phy, x0, x1, y0, y1).ravel()
            t = f[f >= 0.06]
            if t.size < 4:
                continue
            fits.append((float(np.mean(2.0 * np.abs(t - 0.5))), px, phx, py, phy))
    if not fits:
        return {"no_read": True, "reason": "no_lattice_fit"}
    top = max(f[0] for f in fits)
    _s, px, phx, py, phy = max([f for f in fits if f[0] >= top - 0.03],
                               key=lambda f: f[1] * f[3])
    px, phx, py, phy = _fold_submultiple(ii, on, H, W, px, phx, py, phy, x0, x1, y0, y1)
    f = _cell_fracs(ii, H, W, px, phx, py, phy, x0, x1, y0, y1).ravel()
    hi_, lo_ = f[f >= 0.40], f[f < 0.40]
    if hi_.size < 3 or lo_.size < 3:
        return {"no_read": True, "reason": "degenerate_lattice"}
    sep = float(hi_.mean() - lo_.mean())
    if sep < 0.50:
        return {"no_read": True, "reason": "lattice_incoherent_%.2f" % sep}
    kx0, kx1 = int(np.floor((x0 - phx) / px)), int(np.floor((x1 - phx) / px))
    ky0, ky1 = int(np.floor((y0 - phy) / py)), int(np.floor((y1 - phy) / py))
    rng = float(np.percentile(gray, 98) - np.percentile(gray, 2))
    thr = max(4.0, 0.045 * rng)
    ky0e, ky1e, refy = _extend(gray, py, phy, px, phx, 1, ky0, ky1, kx0, kx1, H, thr)
    kx0e, kx1e, refx = _extend(gray, px, phx, py, phy, 0, kx0, kx1, ky0e, ky1e, W, thr)
    rows, cols = ky1e - ky0e + 1, kx1e - kx0e + 1
    if not (2 <= rows <= 40) or not (2 <= cols <= 90):
        return {"no_read": True, "reason": "implausible_%dx%d" % (rows, cols)}
    F = _cell_fracs(ii, H, W, px, phx, py, phy,
                    phx + kx0e * px + 1, phx + (kx1e + 1) * px - 1,
                    phy + ky0e * py + 1, phy + (ky1e + 1) * py - 1)
    F = F[:rows, :cols]
    mat = ["".join("#" if F[r, c] >= 0.40 else "." for c in range(cols)) for r in range(rows)]
    return {"no_read": False, "rows": int(rows), "cols": int(cols), "matrix": mat,
            "px": round(px, 2), "py": round(py, 2), "phx": round(phx, 2), "phy": round(phy, 2),
            "kx0": int(kx0e), "ky0": int(ky0e), "on_is_bright": bool(bright),
            "n_on": int(sum(l.count("#") for l in mat)),
            "ambiguous_frac": round(float(np.mean((F > 0.18) & (F < 0.62))), 4),
            "sep": round(sep, 3), "ref_x": refx, "ref_y": refy,
            "img_w": W, "img_h": H, "orig_w": OW, "orig_h": OH}


def dotmatrix_dims(image, want_rows, want_cols):
    """Score half each for the lamp grid rows and columns matching the spec."""
    grid = dotmatrix_grid(image)
    if grid.get("no_read"):
        return {"no_read": True, "reason": grid.get("reason"), "frac": 0.0, "rows": 0, "cols": 0}
    row_score = 1.0 if int(grid["rows"]) == int(want_rows) else 0.0
    col_score = 1.0 if int(grid["cols"]) == int(want_cols) else 0.0
    out = dict(grid)
    out["frac"] = 0.5 * row_score + 0.5 * col_score
    out["rows_ok"] = bool(row_score)
    out["cols_ok"] = bool(col_score)
    return out


def dotmatrix_raster(image, want_rows, want_cols, want_matrix):
    """Rescale the overlap of lit lamps with the reference pattern to a 0 to 1 score."""
    grid = dotmatrix_grid(image)
    if grid.get("no_read"):
        return {"no_read": True, "reason": grid.get("reason"), "frac": 0.0, "iou": 0.0}
    if int(grid["rows"]) != int(want_rows) or int(grid["cols"]) != int(want_cols):
        out = dict(grid)
        out.update({"frac": 0.0, "iou": 0.0, "reason": "dims_%dx%d" % (grid["rows"], grid["cols"])})
        return out
    wanted_on = set()
    for r, line in enumerate(want_matrix):
        for c, ch in enumerate(line):
            if ch == "#":
                wanted_on.add((r, c))
    read_on = set()
    for r, line in enumerate(grid["matrix"]):
        for c, ch in enumerate(line):
            if ch == "#":
                read_on.add((r, c))
    u = len(wanted_on | read_on)
    iou = (len(wanted_on & read_on) / float(u)) if u else 0.0
    out = dict(grid)
    out.update({"iou": round(iou, 4), "cells_right": int(sum(
        1 for r in range(int(want_rows)) for c in range(int(want_cols))
        if ((r, c) in wanted_on) == ((r, c) in read_on))), "cells_total": int(want_rows) * int(want_cols),
        "frac": round(max(0.0, min(1.0, (iou - 0.35) / 0.65)), 4)})
    return out


def dotmatrix_overlay(image, want_rows, want_cols, want_matrix, tag="cells"):
    """Draw the read lamp grid on the picture, marking lamps that differ from the pattern."""
    import hashlib
    import os
    import tempfile
    import numpy as np
    import cv2
    from PIL import Image
    grid = dotmatrix_grid(image)
    pil = _pil(image)
    W0, H0 = pil.size
    im = np.array(pil).copy()
    if not grid.get("no_read"):
        sx, sy = W0 / float(grid["img_w"]), H0 / float(grid["img_h"])
        px, py = grid["px"] * sx, grid["py"] * sy
        ox = (grid["phx"] + grid["kx0"] * grid["px"]) * sx
        oy = (grid["phy"] + grid["ky0"] * grid["py"]) * sy
        t = max(2, int(round(0.0035 * min(W0, H0))))
        for c in range(grid["cols"] + 1):
            x = int(round(ox + c * px))
            cv2.line(im, (x, int(round(oy))), (x, int(round(oy + grid["rows"] * py))), (0, 190, 220), 1)
        for r in range(grid["rows"] + 1):
            y = int(round(oy + r * py))
            cv2.line(im, (int(round(ox)), y), (int(round(ox + grid["cols"] * px)), y), (0, 190, 220), 1)
        for r in range(grid["rows"]):
            for c in range(grid["cols"]):
                cx = int(round(ox + (c + 0.5) * px))
                cy = int(round(oy + (r + 0.5) * py))
                got = grid["matrix"][r][c] == "#"
                want = None
                if r < len(want_matrix) and c < len(want_matrix[r]) \
                        and int(grid["rows"]) == int(want_rows) and int(grid["cols"]) == int(want_cols):
                    want = want_matrix[r][c] == "#"
                col = (0, 190, 220) if (want is None or want == got) else (230, 0, 180)
                cv2.circle(im, (cx, cy), int(round(0.30 * min(px, py))), col,
                           t if col[0] else max(1, t - 1))
                if want:
                    a = (int(round(ox + c * px)) + 3, int(round(oy + r * py)) + 3)
                    cv2.line(im, a, (a[0] + int(0.22 * px), a[1]), (60, 220, 90), t)
                    cv2.line(im, a, (a[0], a[1] + int(0.22 * py)), (60, 220, 90), t)
        txt = "read %dx%d  demanded %dx%d" % (grid["rows"], grid["cols"], int(want_rows), int(want_cols))
    else:
        txt = "no lamp lattice found (%s)" % grid.get("reason")
    cv2.rectangle(im, (0, 0), (W0, int(0.055 * H0)), (0, 0, 0), -1)
    cv2.putText(im, txt, (12, int(0.040 * H0)), cv2.FONT_HERSHEY_SIMPLEX,
                0.9 * min(W0, H0) / 900.0, (255, 255, 255), 2)
    d = os.path.join(tempfile.gettempdir(), "genolympiad_overlay")
    try:
        os.makedirs(d, exist_ok=True)
    except Exception:
        pass
    h = hashlib.md5(("%s|%s" % (str(image), tag)).encode("utf-8", "replace")).hexdigest()[:12]
    p = os.path.join(d, "e7bdm_%s_%s.png" % (tag, h))
    Image.fromarray(im).save(p)
    out = dict(grid)
    out["path"] = p
    out["frac"] = 1.0
    return out

# end of dotmatrix_dims_code
