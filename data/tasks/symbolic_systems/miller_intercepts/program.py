# code: miller_read_code
import math

def _pil(image):
    from PIL import Image
    return image.convert("RGB") if hasattr(image, "convert") else Image.open(str(image)).convert("RGB")


def _prep(image, cap=1400):
    import numpy as np
    import cv2
    pil = _pil(image)
    rgb = np.asarray(pil)
    bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    H, W = bgr.shape[:2]
    if max(H, W) > cap:
        s = float(cap) / max(H, W)
        bgr = cv2.resize(bgr, (int(W * s), int(H * s)), interpolation=cv2.INTER_AREA)
        H, W = bgr.shape[:2]
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    return bgr, hsv, H, W


def _hdist(a, b):
    d = abs(int(a) - int(b)) % 180
    return min(d, 180 - d)


def _sat_sel(hsv):
    import numpy as np
    S = hsv[:, :, 1].astype(np.int32)
    V = hsv[:, :, 2].astype(np.int32)
    return (S >= 100) & (V >= 90)


def _hue_peaks(hsv, H, W, want=3):
    import numpy as np
    sel = _sat_sel(hsv)
    if int(sel.sum()) < 0.0002 * H * W:
        return []
    hist = np.bincount(hsv[:, :, 0][sel].astype(np.int32), minlength=180).astype(np.float64)
    k = np.array([1., 2., 3., 4., 5., 4., 3., 2., 1.])
    k = k / k.sum()
    pad = np.concatenate([hist[-8:], hist, hist[:8]])
    sm = np.convolve(pad, k, mode="same")[8:188]
    peaks = []
    for idx in np.argsort(-sm):
        if sm[idx] <= 0.02 * sm.max():
            break
        if all(_hdist(int(idx), p) >= 14 for p in peaks):
            peaks.append(int(idx))
        if len(peaks) >= want:
            break
    return peaks


def _hue_mask(hsv, peak, halfwidth=13):
    import numpy as np
    Hc = hsv[:, :, 0].astype(np.int32)
    d = np.abs(Hc - int(peak))
    d = np.minimum(d, 180 - d)
    return (_sat_sel(hsv) & (d <= halfwidth)).astype(np.uint8)


def _fit_axis(m, H, W):
    import numpy as np
    import cv2
    ker = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    mm = cv2.morphologyEx(m, cv2.MORPH_CLOSE, ker)
    n, lbl, st, _ce = cv2.connectedComponentsWithStats(mm, 8)
    best = None
    for i in range(1, n):
        a = int(st[i, cv2.CC_STAT_AREA])
        if best is None or a > best[1]:
            best = (i, a)
    if best is None or best[1] < 0.00022 * H * W:
        return None
    ys, xs = np.nonzero(lbl == best[0])
    pts = np.stack([xs, ys], 1).astype(np.float64)
    c = pts.mean(0)
    _u, s, vt = np.linalg.svd(pts - c, full_matrices=False)
    d = vt[0]
    t = (pts - c) @ d
    return {"c": c, "d": d, "p0": c + d * float(t.min()), "p1": c + d * float(t.max()),
            "lin": float(s[1] / max(s[0], 1e-9)), "area": int(best[1])}


def _concurrency(lines):
    import numpy as np
    A = np.zeros((2, 2))
    b = np.zeros(2)
    for c, d in lines:
        d = np.asarray(d, float)
        d = d / (float(np.linalg.norm(d)) or 1.0)
        M = np.eye(2) - np.outer(d, d)
        A += M
        b += M @ np.asarray(c, float)
    try:
        o = np.linalg.solve(A, b)
    except Exception:
        return None, 1e9
    res = 0.0
    for c, d in lines:
        d = np.asarray(d, float)
        d = d / (float(np.linalg.norm(d)) or 1.0)
        v = o - np.asarray(c, float)
        res += float(np.linalg.norm(v - d * float(v @ d))) ** 2
    return o, math.sqrt(res / max(len(lines), 1))


def _plane_points(hsv, H, W):
    import numpy as np
    import cv2
    S = hsv[:, :, 1].astype(np.int32)
    V = hsv[:, :, 2].astype(np.int32)
    vmax = float(np.percentile(V, 96)) or 255.0
    kc = max(9, int(0.026 * min(H, W)))
    kc = kc + 1 if kc % 2 == 0 else kc
    KC = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kc, kc))
    ro = max(2, int(0.0035 * min(H, W)))
    KO = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * ro + 1, 2 * ro + 1))
    tries = [("grey", ((S < 75) & (V > 0.26 * vmax) & (V < 0.80 * vmax)).astype(np.uint8)),
             ("dark", ((S < 115) & (V < 0.60 * vmax)).astype(np.uint8))]
    for name, m in tries:
        mm = cv2.morphologyEx(cv2.morphologyEx(m, cv2.MORPH_OPEN, KO), cv2.MORPH_CLOSE, KC)
        n, lbl, st, _ce = cv2.connectedComponentsWithStats(mm, 8)
        best = None
        for i in range(1, n):
            a = int(st[i, cv2.CC_STAT_AREA])
            x0 = int(st[i, cv2.CC_STAT_LEFT]); y0 = int(st[i, cv2.CC_STAT_TOP])
            w = int(st[i, cv2.CC_STAT_WIDTH]); h = int(st[i, cv2.CC_STAT_HEIGHT])
            touch = (x0 <= 1) + (y0 <= 1) + (x0 + w >= W - 1) + (y0 + h >= H - 1)
            if touch >= 2:
                continue
            if best is None or a > best[1]:
                best = (i, a)
        if best is None or best[1] < 0.005 * H * W or best[1] > 0.55 * H * W:
            continue
        ys, xs = np.nonzero(lbl == best[0])
        return np.stack([xs, ys], 1).astype(np.float64), name
    return None, None


def _seg_isect(A1, B1, A2, B2):
    import numpy as np
    d1 = B1 - A1
    d2 = B2 - A2
    den = float(d1[0] * d2[1] - d1[1] * d2[0])
    if abs(den) < 1e-9:
        return None
    t = float((A2[0] - A1[0]) * d2[1] - (A2[1] - A1[1]) * d2[0]) / den
    return A1 + d1 * t


def _fit_line(P):
    import numpy as np
    c = P.mean(0)
    _u, _s, vt = np.linalg.svd(P - c, full_matrices=False)
    return c, vt[0]


def _angdiff(a, b):
    d = (a - b) % 360.0
    return min(d, 360.0 - d)


def _poly_corners(pts, min_edge_frac=0.10, ang_tol=9.0, trim=0.16):
    import numpy as np
    import cv2
    hull = cv2.convexHull(pts.reshape(-1, 1, 2).astype(np.float32)).reshape(-1, 2).astype(np.float64)
    nh = len(hull)
    peri = float(cv2.arcLength(hull.reshape(-1, 1, 2).astype(np.float32), True))
    if nh < 4 or peri <= 0:
        return hull
    segs = []
    for i in range(nh):
        A, B = hull[i], hull[(i + 1) % nh]
        L = float(np.linalg.norm(B - A))
        if L < 1e-6:
            continue
        segs.append({"i": i, "L": L,
                     "ang": math.degrees(math.atan2(B[1] - A[1], B[0] - A[0]))})
    if len(segs) < 3:
        return hull
    groups = [[segs[0]]]
    for s in segs[1:]:
        g = groups[-1]
        ref = math.degrees(math.atan2(sum(math.sin(math.radians(q["ang"])) * q["L"] for q in g),
                                      sum(math.cos(math.radians(q["ang"])) * q["L"] for q in g)))
        if _angdiff(s["ang"], ref) <= ang_tol:
            g.append(s)
        else:
            groups.append([s])
    if len(groups) > 2:
        a0 = math.degrees(math.atan2(sum(math.sin(math.radians(q["ang"])) * q["L"] for q in groups[0]),
                                     sum(math.cos(math.radians(q["ang"])) * q["L"] for q in groups[0])))
        a1 = math.degrees(math.atan2(sum(math.sin(math.radians(q["ang"])) * q["L"] for q in groups[-1]),
                                     sum(math.cos(math.radians(q["ang"])) * q["L"] for q in groups[-1])))
        if _angdiff(a0, a1) <= ang_tol:
            groups[0] = groups[-1] + groups[0]
            groups.pop()
    sides = []
    for g in groups:
        if sum(q["L"] for q in g) < min_edge_frac * peri:
            continue
        run = [q["i"] for q in g] + [(g[-1]["i"] + 1) % nh]
        if len(run) >= 6:
            cut = max(1, int(trim * len(run)))
            run = run[cut:len(run) - cut]
        sup = hull[np.array(run, dtype=int)]
        if len(sup) >= 3:
            sides.append(_fit_line(sup))
        else:
            A, B = sup[0], sup[-1]
            d = B - A
            n = float(np.linalg.norm(d))
            if n < 1e-6:
                continue
            sides.append((A, d / n))
    if len(sides) < 3:
        return cv2.approxPolyDP(hull.reshape(-1, 1, 2).astype(np.float32),
                                0.02 * peri, True).reshape(-1, 2).astype(np.float64)
    out = []
    for i in range(len(sides)):
        c1, d1 = sides[i]
        c2, d2 = sides[(i + 1) % len(sides)]
        P = _seg_isect(c1, c1 + d1, c2, c2 + d2)
        if P is not None:
            out.append(P)
    if len(out) < 3:
        return cv2.approxPolyDP(hull.reshape(-1, 1, 2).astype(np.float32),
                                0.02 * peri, True).reshape(-1, 2).astype(np.float64)
    return np.stack(out, 0).astype(np.float64)


def _axis_intercept(o, C, corners, tol=0.085, fmin=0.055, fmax=1.25):
    import numpy as np
    d = np.asarray(C, float) - np.asarray(o, float)
    L = float(np.linalg.norm(d))
    if L <= 2.0:
        return None
    u = d / L
    nn = np.array([-u[1], u[0]])
    best = None
    for P in corners:
        v = np.asarray(P, float) - np.asarray(o, float)
        f = float(v @ u) / L
        perp = abs(float(v @ nn)) / L
        if f < fmin or f > fmax:
            continue
        if best is None or perp < best["perp"]:
            best = {"frac": round(f, 4), "perp": round(perp, 4), "pt": [float(P[0]), float(P[1])]}
    if best is None or best["perp"] > tol:
        return None
    return best


def miller_read(image):
    """Find the red, green and blue axes and where the shaded plane's corners cut each one."""
    import itertools
    import numpy as np
    try:
        _bgr, hsv, H, W = _prep(image)
    except Exception as e:
        return {"no_read": True, "reason": "load_%s" % type(e).__name__}
    peaks = _hue_peaks(hsv, H, W)
    if len(peaks) < 3:
        return {"no_read": True, "reason": "only_%d_colour_axes" % len(peaks), "n_axes": len(peaks)}
    fits = []
    for pk in peaks:
        f = _fit_axis(_hue_mask(hsv, pk), H, W)
        if f is None:
            return {"no_read": True, "reason": "axis_blob_too_small", "n_axes": len(peaks)}
        f["hue"] = pk
        fits.append(f)
    nominal_hues = (0, 60, 120)
    best_perm = None
    for perm in itertools.permutations(range(3)):
        cost = sum(_hdist(fits[perm[i]]["hue"], nominal_hues[i]) for i in range(3))
        if best_perm is None or cost < best_perm[0]:
            best_perm = (cost, perm)
    hue_cost, perm = best_perm
    A = [fits[perm[i]] for i in range(3)]
    o, residual = _concurrency([(A[i]["c"], A[i]["d"]) for i in range(3)])
    if o is None:
        return {"no_read": True, "reason": "axes_not_concurrent", "n_axes": 3}
    ends = []
    for i in range(3):
        far = A[i]["p0"] if (np.linalg.norm(A[i]["p0"] - o)
                             > np.linalg.norm(A[i]["p1"] - o)) else A[i]["p1"]
        d = A[i]["d"]
        ends.append(o + d * float((far - o) @ d))
    lengths = [float(np.linalg.norm(ends[i] - o)) for i in range(3)]
    meanlen = float(np.mean(lengths)) or 1.0
    spread = float(residual) / meanlen
    angles = [math.degrees(math.atan2(float(ends[i][1] - o[1]), float(ends[i][0] - o[0])))
            for i in range(3)]
    min_separation = 999.0
    for i in range(3):
        for j in range(i + 1, 3):
            d = abs(angles[i] - angles[j]) % 360.0
            min_separation = min(min_separation, min(d, 360.0 - d))
    pts, src = _plane_points(hsv, H, W)
    if pts is None:
        return {"no_read": True, "reason": "no_shaded_patch", "n_axes": 3}
    corners = _poly_corners(pts)
    intercepts = [_axis_intercept(o, ends[i], corners) for i in range(3)]
    out = {"no_read": False, "reason": None, "n_axes": 3, "patch_src": src,
           "hue_cost": int(hue_cost), "origin": [float(o[0]), float(o[1])],
           "origin_spread": round(spread, 4), "axis_sep_deg": round(min_separation, 1),
           "lin_max": round(max(a["lin"] for a in A), 4),
           "n_corners": int(len(corners)),
           "corners": [[float(p[0]), float(p[1])] for p in corners],
           "ends": [[float(e[0]), float(e[1])] for e in ends],
           "axis_len": [round(v, 1) for v in lengths]}
    for i, k in enumerate("abc"):
        out["has_" + k] = bool(intercepts[i] is not None)
        out["f_" + k] = (None if intercepts[i] is None else intercepts[i]["frac"])
        out["perp_" + k] = (None if intercepts[i] is None else intercepts[i]["perp"])
        out["pt_" + k] = (None if intercepts[i] is None else intercepts[i]["pt"])
    out["frame_ok"] = bool(spread <= 0.16 and out["lin_max"] <= 0.42
                           and min_separation >= 20.0 and hue_cost <= 75)
    return out


def score_intercept(f, has, target):
    """Score 1 when the read intercept is within 0.05 of the reference, fading to 0 by 0.095."""
    if target is None:
        return 0.0 if has else 1.0
    if not has or f is None:
        return 0.0
    error = abs(float(f) - float(target))
    core, marg = 0.05, 0.045
    if error <= core:
        return 1.0
    if error >= core + marg:
        return 0.0
    return round(1.0 - (error - core) / marg, 4)


def frame_check_score(ok):
    """Score 1 when the three colour axes were found meeting cleanly at one corner, else 0."""
    return 1.0 if ok else 0.0


def index_triple_score(said, want):
    """Score 1 when the first three digits in the answer match the reference Miller index."""
    import re
    digits = re.findall(r"\d", str(said))
    return 1.0 if " ".join(digits[:3]) == str(want).strip() else 0.0


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
    return os.path.join(d, "e7bmiller_%s_%s.png" % (tag, h))


def miller_overlay(image, ta, tb, tc, tag="intercepts"):
    import numpy as np
    import cv2
    from PIL import Image
    m = miller_read(image)
    pil = _pil(image)
    W0, H0 = pil.size
    g = cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2GRAY)
    g = (0.35 * 255 + 0.65 * g.astype(np.float64)).astype(np.uint8)
    im = cv2.cvtColor(g, cv2.COLOR_GRAY2RGB)
    if not m.get("no_read"):
        bgr, _hsv, H, W = _prep(image)
        sx, sy = W0 / float(W), H0 / float(H)
        th = max(2, int(0.0035 * min(H0, W0)))
        rad = max(6, int(0.013 * min(H0, W0)))
        o = np.array([m["origin"][0] * sx, m["origin"][1] * sy])
        want = [ta, tb, tc]
        for i, k in enumerate("abc"):
            E = np.array([m["ends"][i][0] * sx, m["ends"][i][1] * sy])
            cv2.line(im, (int(o[0]), int(o[1])), (int(E[0]), int(E[1])), (60, 60, 60), max(1, th - 1))
            d = E - o
            n = np.array([-d[1], d[0]])
            nl = float(np.linalg.norm(n)) or 1.0
            n = n / nl
            if want[i] is not None:
                G = o + d * float(want[i])
                Gl = G + n * rad * 3.4
                cv2.line(im, (int(Gl[0]), int(Gl[1])), (int(G[0]), int(G[1])), (0, 165, 0), th)
                cv2.circle(im, (int(G[0]), int(G[1])), int(rad * 1.75), (0, 165, 0), th)
            if m.get("has_" + k):
                R = o + d * float(m["f_" + k])
                Rl = R - n * rad * 3.4
                cv2.line(im, (int(Rl[0]), int(Rl[1])), (int(R[0]), int(R[1])), (225, 30, 30), th)
                cv2.circle(im, (int(R[0]), int(R[1])), int(rad * 0.85), (225, 30, 30), th)
        for P in m["corners"]:
            cv2.drawMarker(im, (int(P[0] * sx), int(P[1] * sy)), (190, 0, 190),
                           cv2.MARKER_TILTED_CROSS, rad, max(1, th - 1))
    p = _overlay_path(image, tag)
    Image.fromarray(im).save(p)
    out = dict(m)
    out["path"] = p
    return out

# end of miller_read_code

# code: miller_overlay_marked_code
import math

def _pil(image):
    from PIL import Image
    return image.convert("RGB") if hasattr(image, "convert") else Image.open(str(image)).convert("RGB")


def _prep(image, cap=1400):
    import numpy as np
    import cv2
    pil = _pil(image)
    rgb = np.asarray(pil)
    bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    H, W = bgr.shape[:2]
    if max(H, W) > cap:
        s = float(cap) / max(H, W)
        bgr = cv2.resize(bgr, (int(W * s), int(H * s)), interpolation=cv2.INTER_AREA)
        H, W = bgr.shape[:2]
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    return bgr, hsv, H, W


def _hdist(a, b):
    d = abs(int(a) - int(b)) % 180
    return min(d, 180 - d)


def _sat_sel(hsv):
    import numpy as np
    S = hsv[:, :, 1].astype(np.int32)
    V = hsv[:, :, 2].astype(np.int32)
    return (S >= 100) & (V >= 90)


def _hue_peaks(hsv, H, W, want=3):
    import numpy as np
    sel = _sat_sel(hsv)
    if int(sel.sum()) < 0.0002 * H * W:
        return []
    hist = np.bincount(hsv[:, :, 0][sel].astype(np.int32), minlength=180).astype(np.float64)
    k = np.array([1., 2., 3., 4., 5., 4., 3., 2., 1.])
    k = k / k.sum()
    pad = np.concatenate([hist[-8:], hist, hist[:8]])
    sm = np.convolve(pad, k, mode="same")[8:188]
    peaks = []
    for idx in np.argsort(-sm):
        if sm[idx] <= 0.02 * sm.max():
            break
        if all(_hdist(int(idx), p) >= 14 for p in peaks):
            peaks.append(int(idx))
        if len(peaks) >= want:
            break
    return peaks


def _hue_mask(hsv, peak, halfwidth=13):
    import numpy as np
    Hc = hsv[:, :, 0].astype(np.int32)
    d = np.abs(Hc - int(peak))
    d = np.minimum(d, 180 - d)
    return (_sat_sel(hsv) & (d <= halfwidth)).astype(np.uint8)


def _fit_axis(m, H, W):
    import numpy as np
    import cv2
    ker = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    mm = cv2.morphologyEx(m, cv2.MORPH_CLOSE, ker)
    n, lbl, st, _ce = cv2.connectedComponentsWithStats(mm, 8)
    best = None
    for i in range(1, n):
        a = int(st[i, cv2.CC_STAT_AREA])
        if best is None or a > best[1]:
            best = (i, a)
    if best is None or best[1] < 0.00022 * H * W:
        return None
    ys, xs = np.nonzero(lbl == best[0])
    pts = np.stack([xs, ys], 1).astype(np.float64)
    c = pts.mean(0)
    _u, s, vt = np.linalg.svd(pts - c, full_matrices=False)
    d = vt[0]
    t = (pts - c) @ d
    return {"c": c, "d": d, "p0": c + d * float(t.min()), "p1": c + d * float(t.max()),
            "lin": float(s[1] / max(s[0], 1e-9)), "area": int(best[1])}


def _concurrency(lines):
    import numpy as np
    A = np.zeros((2, 2))
    b = np.zeros(2)
    for c, d in lines:
        d = np.asarray(d, float)
        d = d / (float(np.linalg.norm(d)) or 1.0)
        M = np.eye(2) - np.outer(d, d)
        A += M
        b += M @ np.asarray(c, float)
    try:
        o = np.linalg.solve(A, b)
    except Exception:
        return None, 1e9
    res = 0.0
    for c, d in lines:
        d = np.asarray(d, float)
        d = d / (float(np.linalg.norm(d)) or 1.0)
        v = o - np.asarray(c, float)
        res += float(np.linalg.norm(v - d * float(v @ d))) ** 2
    return o, math.sqrt(res / max(len(lines), 1))


def _plane_points(hsv, H, W):
    import numpy as np
    import cv2
    S = hsv[:, :, 1].astype(np.int32)
    V = hsv[:, :, 2].astype(np.int32)
    vmax = float(np.percentile(V, 96)) or 255.0
    kc = max(9, int(0.026 * min(H, W)))
    kc = kc + 1 if kc % 2 == 0 else kc
    KC = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kc, kc))
    ro = max(2, int(0.0035 * min(H, W)))
    KO = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * ro + 1, 2 * ro + 1))
    tries = [("grey", ((S < 75) & (V > 0.26 * vmax) & (V < 0.80 * vmax)).astype(np.uint8)),
             ("dark", ((S < 115) & (V < 0.60 * vmax)).astype(np.uint8))]
    for name, m in tries:
        mm = cv2.morphologyEx(cv2.morphologyEx(m, cv2.MORPH_OPEN, KO), cv2.MORPH_CLOSE, KC)
        n, lbl, st, _ce = cv2.connectedComponentsWithStats(mm, 8)
        best = None
        for i in range(1, n):
            a = int(st[i, cv2.CC_STAT_AREA])
            x0 = int(st[i, cv2.CC_STAT_LEFT]); y0 = int(st[i, cv2.CC_STAT_TOP])
            w = int(st[i, cv2.CC_STAT_WIDTH]); h = int(st[i, cv2.CC_STAT_HEIGHT])
            touch = (x0 <= 1) + (y0 <= 1) + (x0 + w >= W - 1) + (y0 + h >= H - 1)
            if touch >= 2:
                continue
            if best is None or a > best[1]:
                best = (i, a)
        if best is None or best[1] < 0.005 * H * W or best[1] > 0.55 * H * W:
            continue
        ys, xs = np.nonzero(lbl == best[0])
        return np.stack([xs, ys], 1).astype(np.float64), name
    return None, None


def _seg_isect(A1, B1, A2, B2):
    import numpy as np
    d1 = B1 - A1
    d2 = B2 - A2
    den = float(d1[0] * d2[1] - d1[1] * d2[0])
    if abs(den) < 1e-9:
        return None
    t = float((A2[0] - A1[0]) * d2[1] - (A2[1] - A1[1]) * d2[0]) / den
    return A1 + d1 * t


def _fit_line(P):
    import numpy as np
    c = P.mean(0)
    _u, _s, vt = np.linalg.svd(P - c, full_matrices=False)
    return c, vt[0]


def _angdiff(a, b):
    d = (a - b) % 360.0
    return min(d, 360.0 - d)


def _poly_corners(pts, min_edge_frac=0.10, ang_tol=9.0, trim=0.16):
    import numpy as np
    import cv2
    hull = cv2.convexHull(pts.reshape(-1, 1, 2).astype(np.float32)).reshape(-1, 2).astype(np.float64)
    nh = len(hull)
    peri = float(cv2.arcLength(hull.reshape(-1, 1, 2).astype(np.float32), True))
    if nh < 4 or peri <= 0:
        return hull
    segs = []
    for i in range(nh):
        A, B = hull[i], hull[(i + 1) % nh]
        L = float(np.linalg.norm(B - A))
        if L < 1e-6:
            continue
        segs.append({"i": i, "L": L,
                     "ang": math.degrees(math.atan2(B[1] - A[1], B[0] - A[0]))})
    if len(segs) < 3:
        return hull
    groups = [[segs[0]]]
    for s in segs[1:]:
        g = groups[-1]
        ref = math.degrees(math.atan2(sum(math.sin(math.radians(q["ang"])) * q["L"] for q in g),
                                      sum(math.cos(math.radians(q["ang"])) * q["L"] for q in g)))
        if _angdiff(s["ang"], ref) <= ang_tol:
            g.append(s)
        else:
            groups.append([s])
    if len(groups) > 2:
        a0 = math.degrees(math.atan2(sum(math.sin(math.radians(q["ang"])) * q["L"] for q in groups[0]),
                                     sum(math.cos(math.radians(q["ang"])) * q["L"] for q in groups[0])))
        a1 = math.degrees(math.atan2(sum(math.sin(math.radians(q["ang"])) * q["L"] for q in groups[-1]),
                                     sum(math.cos(math.radians(q["ang"])) * q["L"] for q in groups[-1])))
        if _angdiff(a0, a1) <= ang_tol:
            groups[0] = groups[-1] + groups[0]
            groups.pop()
    sides = []
    for g in groups:
        if sum(q["L"] for q in g) < min_edge_frac * peri:
            continue
        run = [q["i"] for q in g] + [(g[-1]["i"] + 1) % nh]
        if len(run) >= 6:
            cut = max(1, int(trim * len(run)))
            run = run[cut:len(run) - cut]
        sup = hull[np.array(run, dtype=int)]
        if len(sup) >= 3:
            sides.append(_fit_line(sup))
        else:
            A, B = sup[0], sup[-1]
            d = B - A
            n = float(np.linalg.norm(d))
            if n < 1e-6:
                continue
            sides.append((A, d / n))
    if len(sides) < 3:
        return cv2.approxPolyDP(hull.reshape(-1, 1, 2).astype(np.float32),
                                0.02 * peri, True).reshape(-1, 2).astype(np.float64)
    out = []
    for i in range(len(sides)):
        c1, d1 = sides[i]
        c2, d2 = sides[(i + 1) % len(sides)]
        P = _seg_isect(c1, c1 + d1, c2, c2 + d2)
        if P is not None:
            out.append(P)
    if len(out) < 3:
        return cv2.approxPolyDP(hull.reshape(-1, 1, 2).astype(np.float32),
                                0.02 * peri, True).reshape(-1, 2).astype(np.float64)
    return np.stack(out, 0).astype(np.float64)


def _axis_intercept(o, C, corners, tol=0.085, fmin=0.055, fmax=1.25):
    import numpy as np
    d = np.asarray(C, float) - np.asarray(o, float)
    L = float(np.linalg.norm(d))
    if L <= 2.0:
        return None
    u = d / L
    nn = np.array([-u[1], u[0]])
    best = None
    for P in corners:
        v = np.asarray(P, float) - np.asarray(o, float)
        f = float(v @ u) / L
        perp = abs(float(v @ nn)) / L
        if f < fmin or f > fmax:
            continue
        if best is None or perp < best["perp"]:
            best = {"frac": round(f, 4), "perp": round(perp, 4), "pt": [float(P[0]), float(P[1])]}
    if best is None or best["perp"] > tol:
        return None
    return best


def miller_read(image):
    import itertools
    import numpy as np
    try:
        _bgr, hsv, H, W = _prep(image)
    except Exception as e:
        return {"no_read": True, "reason": "load_%s" % type(e).__name__}
    peaks = _hue_peaks(hsv, H, W)
    if len(peaks) < 3:
        return {"no_read": True, "reason": "only_%d_colour_axes" % len(peaks), "n_axes": len(peaks)}
    fits = []
    for pk in peaks:
        f = _fit_axis(_hue_mask(hsv, pk), H, W)
        if f is None:
            return {"no_read": True, "reason": "axis_blob_too_small", "n_axes": len(peaks)}
        f["hue"] = pk
        fits.append(f)
    NOM = (0, 60, 120)
    bestp = None
    for perm in itertools.permutations(range(3)):
        cost = sum(_hdist(fits[perm[i]]["hue"], NOM[i]) for i in range(3))
        if bestp is None or cost < bestp[0]:
            bestp = (cost, perm)
    hue_cost, perm = bestp
    A = [fits[perm[i]] for i in range(3)]
    o, res = _concurrency([(A[i]["c"], A[i]["d"]) for i in range(3)])
    if o is None:
        return {"no_read": True, "reason": "axes_not_concurrent", "n_axes": 3}
    ends = []
    for i in range(3):
        far = A[i]["p0"] if (np.linalg.norm(A[i]["p0"] - o)
                             > np.linalg.norm(A[i]["p1"] - o)) else A[i]["p1"]
        d = A[i]["d"]
        ends.append(o + d * float((far - o) @ d))
    lens = [float(np.linalg.norm(ends[i] - o)) for i in range(3)]
    meanlen = float(np.mean(lens)) or 1.0
    spread = float(res) / meanlen
    angs = [math.degrees(math.atan2(float(ends[i][1] - o[1]), float(ends[i][0] - o[0])))
            for i in range(3)]
    sep = 999.0
    for i in range(3):
        for j in range(i + 1, 3):
            d = abs(angs[i] - angs[j]) % 360.0
            sep = min(sep, min(d, 360.0 - d))
    pts, src = _plane_points(hsv, H, W)
    if pts is None:
        return {"no_read": True, "reason": "no_shaded_patch", "n_axes": 3}
    corners = _poly_corners(pts)
    hit = [_axis_intercept(o, ends[i], corners) for i in range(3)]
    out = {"no_read": False, "reason": None, "n_axes": 3, "patch_src": src,
           "hue_cost": int(hue_cost), "origin": [float(o[0]), float(o[1])],
           "origin_spread": round(spread, 4), "axis_sep_deg": round(sep, 1),
           "lin_max": round(max(a["lin"] for a in A), 4),
           "n_corners": int(len(corners)),
           "corners": [[float(p[0]), float(p[1])] for p in corners],
           "ends": [[float(e[0]), float(e[1])] for e in ends],
           "axis_len": [round(v, 1) for v in lens]}
    for i, k in enumerate("abc"):
        out["has_" + k] = bool(hit[i] is not None)
        out["f_" + k] = (None if hit[i] is None else hit[i]["frac"])
        out["perp_" + k] = (None if hit[i] is None else hit[i]["perp"])
        out["pt_" + k] = (None if hit[i] is None else hit[i]["pt"])
    out["frame_ok"] = bool(spread <= 0.16 and out["lin_max"] <= 0.42
                           and sep >= 20.0 and hue_cost <= 75)
    return out


def score_intercept(f, has, target):
    if target is None:
        return 0.0 if has else 1.0
    if not has or f is None:
        return 0.0
    e = abs(float(f) - float(target))
    core, marg = 0.05, 0.045
    if e <= core:
        return 1.0
    if e >= core + marg:
        return 0.0
    return round(1.0 - (e - core) / marg, 4)


def frame_check_score(ok):
    return 1.0 if ok else 0.0


def index_triple_score(said, want):
    import re
    d = re.findall(r"\d", str(said))
    return 1.0 if " ".join(d[:3]) == str(want).strip() else 0.0


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
    return os.path.join(d, "e7bmiller_%s_%s.png" % (tag, h))


def miller_overlay(image, ta, tb, tc, tag="intercepts"):
    import numpy as np
    import cv2
    from PIL import Image
    m = miller_read(image)
    pil = _pil(image)
    W0, H0 = pil.size
    g = cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2GRAY)
    g = (0.35 * 255 + 0.65 * g.astype(np.float64)).astype(np.uint8)
    im = cv2.cvtColor(g, cv2.COLOR_GRAY2RGB)
    if not m.get("no_read"):
        bgr, _hsv, H, W = _prep(image)
        sx, sy = W0 / float(W), H0 / float(H)
        th = max(2, int(0.0035 * min(H0, W0)))
        rad = max(6, int(0.013 * min(H0, W0)))
        o = np.array([m["origin"][0] * sx, m["origin"][1] * sy])
        want = [ta, tb, tc]
        for i, k in enumerate("abc"):
            E = np.array([m["ends"][i][0] * sx, m["ends"][i][1] * sy])
            cv2.line(im, (int(o[0]), int(o[1])), (int(E[0]), int(E[1])), (60, 60, 60), max(1, th - 1))
            _mk("axes", "polylines", [[float(o[0]), float(o[1])], [float(E[0]), float(E[1])]])
            d = E - o
            n = np.array([-d[1], d[0]])
            nl = float(np.linalg.norm(n)) or 1.0
            n = n / nl
            if want[i] is not None:
                G = o + d * float(want[i])
                Gl = G + n * rad * 3.4
                cv2.line(im, (int(Gl[0]), int(Gl[1])), (int(G[0]), int(G[1])), (0, 165, 0), th)
                cv2.circle(im, (int(G[0]), int(G[1])), int(rad * 1.75), (0, 165, 0), th)
                _mk("want_intercept", "polylines",
                    [[float(Gl[0]), float(Gl[1])], [float(G[0]), float(G[1])]])
                _mk("want_intercept", "circles",
                    [float(G[0]), float(G[1]), 2.0 * int(rad * 1.75)])
            if m.get("has_" + k):
                R = o + d * float(m["f_" + k])
                Rl = R - n * rad * 3.4
                cv2.line(im, (int(Rl[0]), int(Rl[1])), (int(R[0]), int(R[1])), (225, 30, 30), th)
                cv2.circle(im, (int(R[0]), int(R[1])), int(rad * 0.85), (225, 30, 30), th)
                _mk("measured_intercept", "polylines",
                    [[float(Rl[0]), float(Rl[1])], [float(R[0]), float(R[1])]])
                _mk("measured_intercept", "circles",
                    [float(R[0]), float(R[1]), 2.0 * int(rad * 0.85)])
        for P in m["corners"]:
            cv2.drawMarker(im, (int(P[0] * sx), int(P[1] * sy)), (190, 0, 190),
                           cv2.MARKER_TILTED_CROSS, rad, max(1, th - 1))
            _mk("patch_corners", "points", [float(P[0] * sx), float(P[1] * sy)])
    p = _overlay_path(image, tag)
    Image.fromarray(im).save(p)
    out = dict(m)
    out["path"] = p
    return out


def miller_overlay_marked(image, ta, tb, tc, tag="intercepts"):
    """Draw the reference and measured intercepts on the image and return the overlay."""
    _mk_reset("axes", "want_intercept", "measured_intercept", "patch_corners")
    r = dict(miller_overlay(image, ta, tb, tc, tag))
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

# end of miller_overlay_marked_code
