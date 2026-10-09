# code: braille_cells_code

def _pil(image):
    from PIL import Image
    return image.convert("RGB") if hasattr(image, "convert") else Image.open(str(image)).convert("RGB")


def _bgr(image, cap=1200):
    import numpy as np
    import cv2
    bgr = cv2.cvtColor(np.asarray(_pil(image)), cv2.COLOR_RGB2BGR)
    h, w = bgr.shape[:2]
    if max(h, w) > cap:
        s = cap / float(max(h, w))
        bgr = cv2.resize(bgr, (int(w * s), int(h * s)), interpolation=cv2.INTER_AREA)
    return bgr


def _stdmap(L, k):
    import numpy as np
    import cv2
    k = int(k) | 1
    m = cv2.boxFilter(L, -1, (k, k), normalize=True, borderType=cv2.BORDER_REFLECT)
    m2 = cv2.boxFilter(L * L, -1, (k, k), normalize=True, borderType=cv2.BORDER_REFLECT)
    return np.sqrt(np.clip(m2 - m * m, 0, None))


def _blobs(r8, W, H, circ, conv, inert):
    import cv2
    p = cv2.SimpleBlobDetector_Params()
    p.minThreshold, p.maxThreshold, p.thresholdStep = 12, 235, 6
    p.minRepeatability = 2
    p.filterByColor, p.blobColor = True, 255
    p.filterByArea, p.minArea, p.maxArea = True, 30.0, 0.02 * W * H
    p.filterByCircularity, p.minCircularity = True, circ
    p.filterByInertia, p.minInertiaRatio = True, inert
    p.filterByConvexity, p.minConvexity = True, conv
    p.minDistBetweenBlobs = 5.0
    return [(k.pt[0], k.pt[1], k.size / 2.0) for k in cv2.SimpleBlobDetector_create(p).detect(r8)]


def _mode_radius(P):
    import numpy as np
    if not P:
        return [], 0.0
    rs = sorted(p[2] for p in P)
    best = (0, rs[0], rs[0])
    for lo in rs:
        hi = lo * 1.7
        n = sum(1 for v in rs if lo <= v <= hi)
        if n > best[0]:
            best = (n, lo, hi)
    _n, lo, hi = best
    keep = [p for p in P if lo <= p[2] <= hi]
    return keep, float(np.median([p[2] for p in keep]))


def _clust(vals, tol):
    vals = sorted(vals)
    g = [[vals[0]]]
    for v in vals[1:]:
        if v - g[-1][-1] <= tol:
            g[-1].append(v)
        else:
            g.append([v])
    return g


def _fit(P):
    import numpy as np
    if len(P) < 3:
        return None
    P, rad = _mode_radius(P)
    if len(P) < 3 or rad < 3.5:
        return None
    xy = np.array([[p[0], p[1]] for p in P], dtype=np.float64)
    d = np.sqrt(((xy[:, None, :] - xy[None, :, :]) ** 2).sum(-1))
    np.fill_diagonal(d, 1e9)
    u0 = float(np.median(d.min(axis=1)))
    if u0 <= 1.0:
        return None
    ys = sorted(p[1] for p in P)
    win = 2.45 * u0
    bc, by = -1, ys[0]
    for y0 in ys:
        n = sum(1 for y in ys if y0 - 0.2 * u0 <= y <= y0 + win)
        if n > bc:
            bc, by = n, y0
    B = [p for p in P if by - 0.25 * u0 <= p[1] <= by + win + 0.25 * u0]
    if len(B) < 2:
        return None
    B, rad = _mode_radius(B)
    if len(B) < 2:
        return None
    rows = _clust([p[1] for p in B], 0.55 * u0)
    if len(rows) > 3:
        return None
    ry = [float(np.mean(c)) for c in rows]
    steps = [ry[i + 1] - ry[i] for i in range(len(ry) - 1)]
    if steps:
        if len(steps) > 1 and max(steps) > 1.6 * min(steps):
            return None
        u = float(min(steps))
        if len(steps) == 1 and steps[0] > 1.55 * u0:
            u = steps[0] / 2.0
    else:
        u = u0
    if u <= 1.0:
        return None
    cx = [float(np.mean(c)) for c in _clust([p[0] for p in B], 0.42 * u)]
    coh = 0
    for p in B:
        if (min(abs(p[1] - v) for v in ry) <= 0.30 * u
                and min(abs(p[0] - v) for v in cx) <= 0.30 * u):
            coh += 1
    return {"dots": B, "rad": rad, "u": u, "rows": ry, "n": len(B),
            "score": coh - 0.5 * (len(B) - coh)}


def _rows3(ry, u):
    if len(ry) >= 3:
        return [ry[0], ry[0] + (ry[-1] - ry[0]) / 2.0, ry[-1]]
    if len(ry) == 2:
        if ry[1] - ry[0] > 1.55 * u:
            return [ry[0], (ry[0] + ry[1]) / 2.0, ry[1]]
        return [ry[0], ry[1], ry[1] + u]
    return [ry[0], ry[0] + u, ry[0] + 2 * u]


def _vrun(resp, x, y, v, u):
    H, W = resp.shape
    x = int(min(W - 1, max(0, x)))
    a, b = max(0, x - int(0.15 * u)), min(W, x + int(0.15 * u) + 1)
    col = resp[:, a:b].max(axis=1)
    y = int(min(H - 1, max(0, y)))
    top, bot = y, y
    while top > 0 and col[top - 1] >= 0.5 * v:
        top -= 1
    while bot < H - 1 and col[bot + 1] >= 0.5 * v:
        bot += 1
    return (bot - top) / float(u)


def _raw_peaks(band, u, x0, x1, thr, W):
    R = max(2, int(0.55 * u))
    out = []
    lo, hi = int(max(0, x0)), int(min(W - 1, x1))
    for x in range(lo, hi):
        v = float(band[x])
        if v < thr:
            continue
        a, b = max(lo, x - R), min(hi, x + R + 1)
        if v < band[a:b].max() - 1e-9:
            continue
        lft, rgt = x, x
        while lft > 0 and band[lft - 1] >= 0.6 * v:
            lft -= 1
        while rgt < W - 1 and band[rgt + 1] >= 0.6 * v:
            rgt += 1
        w = float(rgt - lft)
        if out and x - out[-1][0] <= R:
            if v > out[-1][1]:
                out[-1] = (x, v, w)
        else:
            out.append((x, v, w))
    return out


def _rhythm(cx, sx0, sx1, u):
    core = [v for v in cx if sx0 - 0.6 * u <= v <= sx1 + 0.6 * u]
    if len(core) < 2:
        return cx
    gcore = [core[i + 1] - core[i] for i in range(len(core) - 1)]
    lim = max(2.6 * u, min(4.5 * u, 1.35 * max(gcore)))
    keep = list(core)
    for v in reversed([v for v in cx if v < core[0]]):
        if keep[0] - v <= lim:
            keep.insert(0, v)
        else:
            break
    for v in [v for v in cx if v > core[-1]]:
        if v - keep[-1] <= lim:
            keep.append(v)
        else:
            break
    return keep


def read_braille_symbols(image):
    """Find the braille dots and group them into six-dot symbols, left to right."""
    import numpy as np
    import cv2
    bgr = _bgr(image)
    H, W = bgr.shape[:2]
    L = cv2.GaussianBlur(cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB)[:, :, 0].astype(np.float32), (0, 0), 1.0)
    base = np.maximum.reduce([_stdmap(L, k) for k in (9, 15, 23, 33)])
    f = None
    for sig in (1.5, 3.0, 5.0):
        r = cv2.GaussianBlur(base, (0, 0), sig)
        r8 = np.clip(r / (np.percentile(r, 99.9) + 1e-6) * 255.0, 0, 255).astype(np.uint8)
        for (circ, conv, inert) in ((0.62, 0.85, 0.35), (0.45, 0.72, 0.25)):
            ff = _fit(_blobs(r8, W, H, circ, conv, inert))
            if ff is not None and (f is None or ff["score"] > f["score"]):
                f = ff
    if f is None:
        return {"no_read": True, "why": "no_braille_row", "n_cells": 0, "cells": []}
    u = f["u"]
    rows3 = _rows3(f["rows"], u)
    resp = np.maximum.reduce([_stdmap(L, max(5, int(c * u))) for c in (0.30, 0.45, 0.62)])
    resp = cv2.GaussianBlur(resp, (0, 0), max(1.0, 0.07 * u))
    vals = [float(resp[int(min(H - 1, max(0, y))), int(min(W - 1, max(0, x)))])
            for (x, y, _r) in f["dots"]]
    xs_seed = [p[0] for p in f["dots"]]
    sx0, sx1 = min(xs_seed), max(xs_seed)
    thr = 0.32 * float(np.median(vals))
    k = max(1, int(0.25 * u) | 1)
    raw = {}
    for ri, y in enumerate(rows3):
        ylo, yhi = int(max(0, y - 0.35 * u)), int(min(H, y + 0.35 * u) + 1)
        if yhi <= ylo:
            continue
        band = resp[ylo:yhi, :].max(axis=0)
        band = cv2.GaussianBlur(band.reshape(1, -1), (k, 1), 0).ravel()
        raw[ri] = _raw_peaks(band, u, sx0 - 6.0 * u, sx1 + 6.0 * u, thr, W)
    ws = sorted(p[2] for ri in raw for p in raw[ri] if sx0 - 0.6 * u <= p[0] <= sx1 + 0.6 * u)
    if not ws:
        return {"no_read": True, "why": "no_row_peaks", "n_cells": 0, "cells": []}
    w0 = max(float(np.median(ws[:max(1, int(0.6 * len(ws)))])), 0.35 * u)
    hits = {ri: [(p[0], p[1]) for p in raw[ri]
                 if 0.45 * w0 <= p[2] <= 2.6 * w0 and p[2] <= 2.8 * u
                 and _vrun(resp, p[0], rows3[ri], p[1], u) <= 4.6]
            for ri in raw}
    allx = sorted(x for ri in hits for (x, _v) in hits[ri])
    if not allx:
        return {"no_read": True, "why": "no_dots", "n_cells": 0, "cells": []}
    cx = _rhythm([float(np.mean(c)) for c in _clust(allx, 0.42 * u)], sx0, sx1, u)
    gaps = [cx[i + 1] - cx[i] for i in range(len(cx) - 1)]
    groups, cur = [], [0]
    for i, g in enumerate(gaps):
        if g > 1.30 * u:
            groups.append(cur)
            cur = [i + 1]
        else:
            cur.append(i + 1)
    groups.append(cur)
    codes, boxes = [], []
    for g in groups:
        gxs = [cx[i] for i in g]
        colpair = [gxs[0], (gxs[1] if len(g) >= 2 else gxs[0] + u)]
        code = []
        for ri, y in enumerate(rows3):
            for ci, cxx in enumerate(colpair):
                if any(abs(x - cxx) <= 0.42 * u for (x, _v) in hits.get(ri, [])):
                    code.append(ri + 1 + 3 * ci)
        codes.append(sorted(code))
        boxes.append([colpair[0], colpair[1]])
    return {"no_read": False, "n_cells": len(groups), "cells": codes,
            "wide_cell": bool(any(len(g) > 2 for g in groups)),
            "u": round(u, 2), "n_dots": sum(len(v) for v in hits.values()),
            "gaps_u": [round(g / u, 2) for g in gaps],
            "boxes": boxes, "rows3": [round(v, 1) for v in rows3],
            "img_w": W, "img_h": H}


def cells_overlay(image, want=None, tag="cells"):
    import hashlib
    import os
    import tempfile
    import numpy as np
    import cv2
    from PIL import Image
    m = read_braille_symbols(image)
    pil = _pil(image)
    W0, H0 = pil.size
    im = np.array(pil).copy()
    if not m.get("no_read"):
        sx, sy = W0 / float(m["img_w"]), H0 / float(m["img_h"])
        u = m["u"]
        r3 = m["rows3"]
        th = max(2, int(0.0025 * min(W0, H0)))
        fs = 0.6 * min(W0, H0) / 700.0
        for i, (x0, x1) in enumerate(m["boxes"]):
            a = (int((x0 - 0.62 * u) * sx), int((r3[0] - 0.62 * u) * sy))
            b = (int((x1 + 0.62 * u) * sx), int((r3[2] + 0.62 * u) * sy))
            cv2.rectangle(im, a, b, (235, 40, 40), th)
            cv2.line(im, (int(0.5 * (a[0] + b[0])), a[1]),
                     (int(0.5 * (a[0] + b[0])), max(4, a[1] - int(0.9 * u * sy))), (235, 40, 40), th)
            cv2.putText(im, "#%d %s" % (i + 1, "".join(str(d) for d in m["cells"][i])),
                        (a[0], max(14, a[1] - int((0.95 + 0.85 * (i % 2)) * u * sy))),
                        cv2.FONT_HERSHEY_SIMPLEX, fs, (235, 40, 40), th)
            if want is not None and i < len(want):
                dy = int((1.15 + 0.85 * (i % 2)) * u * sy)
                cv2.putText(im, "want %s" % "".join(str(d) for d in want[i]),
                            (a[0], min(H0 - 6, b[1] + dy)),
                            cv2.FONT_HERSHEY_SIMPLEX, fs, (0, 165, 0), th)
        cv2.putText(im, "cells measured: %d%s" % (m["n_cells"],
                                                  ("  required: %d" % len(want)) if want else ""),
                    (int(0.03 * W0), int(0.07 * H0)), cv2.FONT_HERSHEY_SIMPLEX,
                    fs * 1.3, (235, 40, 40), th + 1)
    d = os.path.join(tempfile.gettempdir(), "genolympiad_overlay")
    try:
        os.makedirs(d, exist_ok=True)
    except Exception:
        pass
    h = hashlib.md5(("%s|%s" % (str(image), tag)).encode("utf-8", "replace")).hexdigest()[:12]
    p = os.path.join(d, "e7bbraille_%s_%s.png" % (tag, h))
    Image.fromarray(im).save(p)
    out = {k: v for k, v in m.items() if k != "boxes"}
    out["path"] = p
    return out

# end of braille_cells_code

# code: f_code
def symbol_count_matches(reading, want):
    """Full credit if the number of braille symbols read equals the demanded number."""
    if reading.get("wide_cell"):
        return 0.0
    return 1.0 if int(reading.get("n_cells") or 0) == int(want) else 0.0

# end of f_code

# code: f_code_2
def contraction_symbols_match(reading, want, idx):
    """Full credit if the contraction's symbols carry exactly the reference dots."""
    got = reading.get("cells") or []
    if len(got) != len(want) or not idx:
        return 0.0
    return 1.0 if all(sorted(got[int(i)]) == sorted(want[int(i)]) for i in idx) else 0.0

# end of f_code_2

# code: f_code_3
def share_of_symbols_matching(reading, want):
    """Share of braille symbols whose dots match the reference, in order."""
    got = reading.get("cells") or []
    if len(got) != len(want):
        return 0.0
    ok = sum(1 for a, b in zip(got, want) if sorted(a) == sorted(b))
    return float(ok) / float(len(want))

# end of f_code_3

# code: cells_overlay_marked_code

def _pil(image):
    from PIL import Image
    return image.convert("RGB") if hasattr(image, "convert") else Image.open(str(image)).convert("RGB")


def _bgr(image, cap=1200):
    import numpy as np
    import cv2
    bgr = cv2.cvtColor(np.asarray(_pil(image)), cv2.COLOR_RGB2BGR)
    h, w = bgr.shape[:2]
    if max(h, w) > cap:
        s = cap / float(max(h, w))
        bgr = cv2.resize(bgr, (int(w * s), int(h * s)), interpolation=cv2.INTER_AREA)
    return bgr


def _stdmap(L, k):
    import numpy as np
    import cv2
    k = int(k) | 1
    m = cv2.boxFilter(L, -1, (k, k), normalize=True, borderType=cv2.BORDER_REFLECT)
    m2 = cv2.boxFilter(L * L, -1, (k, k), normalize=True, borderType=cv2.BORDER_REFLECT)
    return np.sqrt(np.clip(m2 - m * m, 0, None))


def _blobs(r8, W, H, circ, conv, inert):
    import cv2
    p = cv2.SimpleBlobDetector_Params()
    p.minThreshold, p.maxThreshold, p.thresholdStep = 12, 235, 6
    p.minRepeatability = 2
    p.filterByColor, p.blobColor = True, 255
    p.filterByArea, p.minArea, p.maxArea = True, 30.0, 0.02 * W * H
    p.filterByCircularity, p.minCircularity = True, circ
    p.filterByInertia, p.minInertiaRatio = True, inert
    p.filterByConvexity, p.minConvexity = True, conv
    p.minDistBetweenBlobs = 5.0
    return [(k.pt[0], k.pt[1], k.size / 2.0) for k in cv2.SimpleBlobDetector_create(p).detect(r8)]


def _mode_radius(P):
    import numpy as np
    if not P:
        return [], 0.0
    rs = sorted(p[2] for p in P)
    best = (0, rs[0], rs[0])
    for lo in rs:
        hi = lo * 1.7
        n = sum(1 for v in rs if lo <= v <= hi)
        if n > best[0]:
            best = (n, lo, hi)
    _n, lo, hi = best
    keep = [p for p in P if lo <= p[2] <= hi]
    return keep, float(np.median([p[2] for p in keep]))


def _clust(vals, tol):
    vals = sorted(vals)
    g = [[vals[0]]]
    for v in vals[1:]:
        if v - g[-1][-1] <= tol:
            g[-1].append(v)
        else:
            g.append([v])
    return g


def _fit(P):
    import numpy as np
    if len(P) < 3:
        return None
    P, rad = _mode_radius(P)
    if len(P) < 3 or rad < 3.5:
        return None
    xy = np.array([[p[0], p[1]] for p in P], dtype=np.float64)
    d = np.sqrt(((xy[:, None, :] - xy[None, :, :]) ** 2).sum(-1))
    np.fill_diagonal(d, 1e9)
    u0 = float(np.median(d.min(axis=1)))
    if u0 <= 1.0:
        return None
    ys = sorted(p[1] for p in P)
    win = 2.45 * u0
    bc, by = -1, ys[0]
    for y0 in ys:
        n = sum(1 for y in ys if y0 - 0.2 * u0 <= y <= y0 + win)
        if n > bc:
            bc, by = n, y0
    B = [p for p in P if by - 0.25 * u0 <= p[1] <= by + win + 0.25 * u0]
    if len(B) < 2:
        return None
    B, rad = _mode_radius(B)
    if len(B) < 2:
        return None
    rows = _clust([p[1] for p in B], 0.55 * u0)
    if len(rows) > 3:
        return None
    ry = [float(np.mean(c)) for c in rows]
    steps = [ry[i + 1] - ry[i] for i in range(len(ry) - 1)]
    if steps:
        if len(steps) > 1 and max(steps) > 1.6 * min(steps):
            return None
        u = float(min(steps))
        if len(steps) == 1 and steps[0] > 1.55 * u0:
            u = steps[0] / 2.0
    else:
        u = u0
    if u <= 1.0:
        return None
    cx = [float(np.mean(c)) for c in _clust([p[0] for p in B], 0.42 * u)]
    coh = 0
    for p in B:
        if (min(abs(p[1] - v) for v in ry) <= 0.30 * u
                and min(abs(p[0] - v) for v in cx) <= 0.30 * u):
            coh += 1
    return {"dots": B, "rad": rad, "u": u, "rows": ry, "n": len(B),
            "score": coh - 0.5 * (len(B) - coh)}


def _rows3(ry, u):
    if len(ry) >= 3:
        return [ry[0], ry[0] + (ry[-1] - ry[0]) / 2.0, ry[-1]]
    if len(ry) == 2:
        if ry[1] - ry[0] > 1.55 * u:
            return [ry[0], (ry[0] + ry[1]) / 2.0, ry[1]]
        return [ry[0], ry[1], ry[1] + u]
    return [ry[0], ry[0] + u, ry[0] + 2 * u]


def _vrun(resp, x, y, v, u):
    H, W = resp.shape
    x = int(min(W - 1, max(0, x)))
    a, b = max(0, x - int(0.15 * u)), min(W, x + int(0.15 * u) + 1)
    col = resp[:, a:b].max(axis=1)
    y = int(min(H - 1, max(0, y)))
    top, bot = y, y
    while top > 0 and col[top - 1] >= 0.5 * v:
        top -= 1
    while bot < H - 1 and col[bot + 1] >= 0.5 * v:
        bot += 1
    return (bot - top) / float(u)


def _raw_peaks(band, u, x0, x1, thr, W):
    R = max(2, int(0.55 * u))
    out = []
    lo, hi = int(max(0, x0)), int(min(W - 1, x1))
    for x in range(lo, hi):
        v = float(band[x])
        if v < thr:
            continue
        a, b = max(lo, x - R), min(hi, x + R + 1)
        if v < band[a:b].max() - 1e-9:
            continue
        lft, rgt = x, x
        while lft > 0 and band[lft - 1] >= 0.6 * v:
            lft -= 1
        while rgt < W - 1 and band[rgt + 1] >= 0.6 * v:
            rgt += 1
        w = float(rgt - lft)
        if out and x - out[-1][0] <= R:
            if v > out[-1][1]:
                out[-1] = (x, v, w)
        else:
            out.append((x, v, w))
    return out


def _rhythm(cx, sx0, sx1, u):
    core = [v for v in cx if sx0 - 0.6 * u <= v <= sx1 + 0.6 * u]
    if len(core) < 2:
        return cx
    gcore = [core[i + 1] - core[i] for i in range(len(core) - 1)]
    lim = max(2.6 * u, min(4.5 * u, 1.35 * max(gcore)))
    keep = list(core)
    for v in reversed([v for v in cx if v < core[0]]):
        if keep[0] - v <= lim:
            keep.insert(0, v)
        else:
            break
    for v in [v for v in cx if v > core[-1]]:
        if v - keep[-1] <= lim:
            keep.append(v)
        else:
            break
    return keep


def read_braille_symbols(image):
    import numpy as np
    import cv2
    bgr = _bgr(image)
    H, W = bgr.shape[:2]
    L = cv2.GaussianBlur(cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB)[:, :, 0].astype(np.float32), (0, 0), 1.0)
    base = np.maximum.reduce([_stdmap(L, k) for k in (9, 15, 23, 33)])
    f = None
    for sig in (1.5, 3.0, 5.0):
        r = cv2.GaussianBlur(base, (0, 0), sig)
        r8 = np.clip(r / (np.percentile(r, 99.9) + 1e-6) * 255.0, 0, 255).astype(np.uint8)
        for (circ, conv, inert) in ((0.62, 0.85, 0.35), (0.45, 0.72, 0.25)):
            ff = _fit(_blobs(r8, W, H, circ, conv, inert))
            if ff is not None and (f is None or ff["score"] > f["score"]):
                f = ff
    if f is None:
        return {"no_read": True, "why": "no_braille_row", "n_cells": 0, "cells": []}
    u = f["u"]
    rows3 = _rows3(f["rows"], u)
    resp = np.maximum.reduce([_stdmap(L, max(5, int(c * u))) for c in (0.30, 0.45, 0.62)])
    resp = cv2.GaussianBlur(resp, (0, 0), max(1.0, 0.07 * u))
    vals = [float(resp[int(min(H - 1, max(0, y))), int(min(W - 1, max(0, x)))])
            for (x, y, _r) in f["dots"]]
    xs_seed = [p[0] for p in f["dots"]]
    sx0, sx1 = min(xs_seed), max(xs_seed)
    thr = 0.32 * float(np.median(vals))
    k = max(1, int(0.25 * u) | 1)
    raw = {}
    for ri, y in enumerate(rows3):
        ylo, yhi = int(max(0, y - 0.35 * u)), int(min(H, y + 0.35 * u) + 1)
        if yhi <= ylo:
            continue
        band = resp[ylo:yhi, :].max(axis=0)
        band = cv2.GaussianBlur(band.reshape(1, -1), (k, 1), 0).ravel()
        raw[ri] = _raw_peaks(band, u, sx0 - 6.0 * u, sx1 + 6.0 * u, thr, W)
    ws = sorted(p[2] for ri in raw for p in raw[ri] if sx0 - 0.6 * u <= p[0] <= sx1 + 0.6 * u)
    if not ws:
        return {"no_read": True, "why": "no_row_peaks", "n_cells": 0, "cells": []}
    w0 = max(float(np.median(ws[:max(1, int(0.6 * len(ws)))])), 0.35 * u)
    hits = {ri: [(p[0], p[1]) for p in raw[ri]
                 if 0.45 * w0 <= p[2] <= 2.6 * w0 and p[2] <= 2.8 * u
                 and _vrun(resp, p[0], rows3[ri], p[1], u) <= 4.6]
            for ri in raw}
    allx = sorted(x for ri in hits for (x, _v) in hits[ri])
    if not allx:
        return {"no_read": True, "why": "no_dots", "n_cells": 0, "cells": []}
    cx = _rhythm([float(np.mean(c)) for c in _clust(allx, 0.42 * u)], sx0, sx1, u)
    gaps = [cx[i + 1] - cx[i] for i in range(len(cx) - 1)]
    groups, cur = [], [0]
    for i, g in enumerate(gaps):
        if g > 1.30 * u:
            groups.append(cur)
            cur = [i + 1]
        else:
            cur.append(i + 1)
    groups.append(cur)
    codes, boxes = [], []
    for g in groups:
        gxs = [cx[i] for i in g]
        colpair = [gxs[0], (gxs[1] if len(g) >= 2 else gxs[0] + u)]
        code = []
        for ri, y in enumerate(rows3):
            for ci, cxx in enumerate(colpair):
                if any(abs(x - cxx) <= 0.42 * u for (x, _v) in hits.get(ri, [])):
                    code.append(ri + 1 + 3 * ci)
        codes.append(sorted(code))
        boxes.append([colpair[0], colpair[1]])
    return {"no_read": False, "n_cells": len(groups), "cells": codes,
            "wide_cell": bool(any(len(g) > 2 for g in groups)),
            "u": round(u, 2), "n_dots": sum(len(v) for v in hits.values()),
            "gaps_u": [round(g / u, 2) for g in gaps],
            "boxes": boxes, "rows3": [round(v, 1) for v in rows3],
            "img_w": W, "img_h": H}


def cells_overlay(image, want=None, tag="cells"):
    import hashlib
    import os
    import tempfile
    import numpy as np
    import cv2
    from PIL import Image
    m = read_braille_symbols(image)
    pil = _pil(image)
    W0, H0 = pil.size
    im = np.array(pil).copy()
    if not m.get("no_read"):
        sx, sy = W0 / float(m["img_w"]), H0 / float(m["img_h"])
        u = m["u"]
        r3 = m["rows3"]
        th = max(2, int(0.0025 * min(W0, H0)))
        fs = 0.6 * min(W0, H0) / 700.0
        for i, (x0, x1) in enumerate(m["boxes"]):
            a = (int((x0 - 0.62 * u) * sx), int((r3[0] - 0.62 * u) * sy))
            b = (int((x1 + 0.62 * u) * sx), int((r3[2] + 0.62 * u) * sy))
            cv2.rectangle(im, a, b, (235, 40, 40), th)
            _mk("cells", "rects", [0.5 * (a[0] + b[0]), 0.5 * (a[1] + b[1]),
                                   float(b[0] - a[0]), float(b[1] - a[1])])
            cv2.line(im, (int(0.5 * (a[0] + b[0])), a[1]),
                     (int(0.5 * (a[0] + b[0])), max(4, a[1] - int(0.9 * u * sy))), (235, 40, 40), th)
            _mk("cells", "polylines", [[0.5 * (a[0] + b[0]), a[1]],
                                       [0.5 * (a[0] + b[0]), max(4, a[1] - int(0.9 * u * sy))]])
            cv2.putText(im, "#%d %s" % (i + 1, "".join(str(d) for d in m["cells"][i])),
                        (a[0], max(14, a[1] - int((0.95 + 0.85 * (i % 2)) * u * sy))),
                        cv2.FONT_HERSHEY_SIMPLEX, fs, (235, 40, 40), th)
            if want is not None and i < len(want):
                dy = int((1.15 + 0.85 * (i % 2)) * u * sy)
                cv2.putText(im, "want %s" % "".join(str(d) for d in want[i]),
                            (a[0], min(H0 - 6, b[1] + dy)),
                            cv2.FONT_HERSHEY_SIMPLEX, fs, (0, 165, 0), th)
        cv2.putText(im, "cells measured: %d%s" % (m["n_cells"],
                                                  ("  required: %d" % len(want)) if want else ""),
                    (int(0.03 * W0), int(0.07 * H0)), cv2.FONT_HERSHEY_SIMPLEX,
                    fs * 1.3, (235, 40, 40), th + 1)
    d = os.path.join(tempfile.gettempdir(), "genolympiad_overlay")
    try:
        os.makedirs(d, exist_ok=True)
    except Exception:
        pass
    h = hashlib.md5(("%s|%s" % (str(image), tag)).encode("utf-8", "replace")).hexdigest()[:12]
    p = os.path.join(d, "e7bbraille_%s_%s.png" % (tag, h))
    Image.fromarray(im).save(p)
    out = {k: v for k, v in m.items() if k != "boxes"}
    out["path"] = p
    return out


def mark_braille_overlay(image, want=None, tag="cells"):
    """Draw each braille symbol read, marked against the reference dots."""
    _mk_reset("cells")
    r = dict(cells_overlay(image, want, tag))
    r.update(_ovmark_pack(r["path"]))
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

# end of cells_overlay_marked_code
