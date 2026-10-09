# shared code: code_559a4d70187e
def as_score(x):
    """Pass a score through as a float."""
    return float(x)

# end of code_559a4d70187e

# code: find_footprint_code

def _pil(image):
    from PIL import Image
    return image.convert("RGB") if hasattr(image, "convert") else Image.open(str(image)).convert("RGB")


def _prep(image, cap=1000):
    import numpy as np
    import cv2
    rgb = np.asarray(_pil(image))
    OH, OW = rgb.shape[:2]
    H, W = OH, OW
    if max(H, W) > cap:
        s = float(cap) / max(H, W)
        rgb = cv2.resize(rgb, (int(W * s), int(H * s)), interpolation=cv2.INTER_AREA)
        H, W = rgb.shape[:2]
    return rgb, cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY), H, W, OW, OH


def _ink(gray):
    import numpy as np
    paper = float(np.percentile(gray, 80))
    thr = max(35.0, min(205.0, 0.62 * paper))
    return (gray.astype(np.float32) < thr).astype(np.uint8), float(thr), paper


def _strip_border(ink):
    import numpy as np
    import cv2
    n, lbl, st, ce = cv2.connectedComponentsWithStats(ink, 8)
    H, W = ink.shape
    border = np.zeros((H, W), bool)
    border[0, :] = True
    border[-1, :] = True
    border[:, 0] = True
    border[:, -1] = True
    nb = float(border.sum())
    out = ink.copy()
    for i in range(1, n):
        m = lbl == i
        if float((m & border).sum()) / nb > 0.15:
            out[m] = 0
    return out


def _sample(mask, x, y):
    import numpy as np
    H, W = mask.shape
    xi = np.clip(np.round(x).astype(np.int64), 0, W - 1)
    yi = np.clip(np.round(y).astype(np.int64), 0, H - 1)
    return mask[yi, xi]


def _ring_support(ink, cx, cy, r, n=360):
    import numpy as np
    tol = max(2.5, 0.045 * r)
    th = np.linspace(0, 2 * np.pi, n, endpoint=False)
    hit = np.zeros(n, bool)
    for dd in np.linspace(-tol, tol, 9):
        rr = r + dd
        hit |= _sample(ink, cx + rr * np.cos(th), cy + rr * np.sin(th)) > 0
    return float(hit.mean())


def _refine_ring(ink, cx, cy, r):
    import numpy as np
    best = (_ring_support(ink, cx, cy, r), float(cx), float(cy), float(r))
    for rr in np.linspace(0.74 * r, 1.34 * r, 31):
        s = _ring_support(ink, cx, cy, rr)
        if s > best[0]:
            best = (s, float(cx), float(cy), float(rr))
    step = max(1.5, 0.04 * best[3])
    for dx in (-2 * step, -step, 0.0, step, 2 * step):
        for dy in (-2 * step, -step, 0.0, step, 2 * step):
            s = _ring_support(ink, best[1] + dx, best[2] + dy, best[3])
            if s > best[0] + 1e-9:
                best = (s, best[1] + dx, best[2] + dy, best[3])
    for rr in np.linspace(0.90 * best[3], 1.12 * best[3], 17):
        s = _ring_support(ink, best[1], best[2], rr)
        if s > best[0]:
            best = (s, best[1], best[2], float(rr))
    return best


def _disc_stats(ink, cx, cy, r):
    import numpy as np
    H, W = ink.shape
    lo = int(max(0, cy - 3.2 * r)); hi = int(min(H, cy + 3.2 * r + 1))
    le = int(max(0, cx - 3.2 * r)); ri = int(min(W, cx + 3.2 * r + 1))
    sub = ink[lo:hi, le:ri]
    if sub.size < 100:
        return 1.0, 0.0, 0.0
    yy, xx = np.mgrid[lo:hi, le:ri]
    rr = np.hypot(xx - cx, yy - cy)
    im = rr < 0.82 * r
    am = (rr > 1.25 * r) & (rr < 3.1 * r)
    fi = float(sub[im].mean()) if im.sum() > 20 else 1.0
    fa = float(sub[am].mean()) if am.sum() > 200 else 0.0
    th = np.linspace(0, 2 * np.pi, 72, endpoint=False)
    occ = np.zeros(72, bool)
    for k in np.linspace(1.05, 4.5, 40):
        occ |= _sample(ink, cx + k * r * np.cos(th), cy + k * r * np.sin(th)) > 0
    return fi, fa, float(occ.mean())


_MEMO = {}


def _memo(key, fn):
    if key in _MEMO:
        return _MEMO[key]
    v = fn()
    if len(_MEMO) > 64:
        _MEMO.clear()
    _MEMO[key] = v
    return v


def find_footprint(image):
    """Find the plain circle where the mirror cylinder stands, cached per image."""
    return _memo(("fp", str(image)), lambda: _find_footprint(image))


def _find_footprint(image):
    import numpy as np
    import cv2
    rgb, gray, H, W, OW, OH = _prep(image)
    ink0, thr, paper = _ink(gray)
    ink = _strip_border(ink0)
    if int(ink.sum()) < 200:
        return {"no_read": True, "reason": "no_ink", "circle_ok": False}
    base = min(H, W)
    rmin, rmax = 0.030 * base, 0.24 * base
    g = cv2.medianBlur(gray, 5)
    cands = []
    for dp, p2 in ((1.0, 45), (1.2, 32), (1.6, 45), (2.0, 60), (1.0, 25), (1.0, 18)):
        try:
            c = cv2.HoughCircles(g, cv2.HOUGH_GRADIENT, dp, minDist=base * 0.12, param1=140,
                                 param2=p2, minRadius=int(rmin), maxRadius=int(rmax))
        except Exception:
            c = None
        if c is None:
            continue
        for cx, cy, r in c[0][:12]:
            if abs(cx - W / 2.0) > 0.30 * W or abs(cy - H / 2.0) > 0.30 * H:
                continue
            cands.append((float(cx), float(cy), float(r), "ring"))
    seen = set()
    ded = []
    for cx, cy, r, how in cands:
        k = (int(cx / 5), int(cy / 5), int(r / 5))
        if k in seen:
            continue
        seen.add(k)
        ded.append((cx, cy, r, how))
    cands = ded
    dt = cv2.distanceTransform((1 - ink).astype(np.uint8), cv2.DIST_L2, 5)
    step = max(5, int(base / 40))
    for cy in range(int(0.28 * H), int(0.72 * H), step):
        for cx in range(int(0.28 * W), int(0.72 * W), step):
            r = float(dt[cy, cx])
            if rmin <= r <= rmax:
                cands.append((float(cx), float(cy), r, "hole"))
    out = []
    for cx, cy, r, how in cands:
        sup = 0.0
        if how == "ring":
            sup, cx, cy, r = _refine_ring(ink, cx, cy, r)
            if not (rmin <= r <= rmax):
                continue
        fi, fa, wrap = _disc_stats(ink, cx, cy, r)
        out.append({"cx": cx, "cy": cy, "r": r, "how": how, "ring_support": round(sup, 3),
                    "inner_ink": round(fi, 4), "ann_ink": round(fa, 4), "wrap": round(wrap, 3)})
    prim = [c for c in out if c["how"] == "ring" and c["ring_support"] >= 0.72
            and c["wrap"] >= 0.30 and c["ann_ink"] > 0.010]
    sec = [c for c in out if c["inner_ink"] < 0.08 and c["wrap"] >= 0.55 and c["ann_ink"] > 0.010]
    if prim:
        best = dict(max(prim, key=lambda c: (c["ring_support"] + 0.25 * c["wrap"]
                                             - 0.35 * (abs(c["cx"] - W / 2.0)
                                                       + abs(c["cy"] - H / 2.0)) / base)))
        best["circle_ok"] = True
        best["fit"] = "printed_ring"
    elif sec:
        best = dict(max(sec, key=lambda c: c["wrap"] - 2.5 * c["inner_ink"] - 0.4 * c["r"] / base))
        best["circle_ok"] = False
        best["fit"] = "blank_hole"
    else:
        return {"no_read": True, "reason": "no_footprint", "circle_ok": False}
    best["no_read"] = False
    best["needs_second_opinion"] = not best["circle_ok"]
    best["img_w"] = W
    best["img_h"] = H
    best["thr"] = round(thr, 1)
    best["n_cands"] = len(out)
    return best


def _outer_radius(ink, cx, cy, H, W, q=0.999):
    import numpy as np
    ys, xs = np.nonzero(ink)
    if xs.size < 200:
        return None
    d = np.hypot(xs - cx, ys - cy)
    lim = float(min(cx, cy, W - cx, H - cy))
    d = d[d <= lim]
    if d.size < 200:
        return None
    return float(min(np.quantile(d, q) * 1.03, lim))


def _tmp_path(image, tag):
    import hashlib
    import os
    import tempfile
    d = os.path.join(tempfile.gettempdir(), "genolympiad_overlay")
    try:
        os.makedirs(d, exist_ok=True)
    except Exception:
        pass
    h = hashlib.md5(("%s|%s" % (str(image), tag)).encode("utf-8", "replace")).hexdigest()[:12]
    return os.path.join(d, "e7bpolar_%s_%s.png" % (tag, h))


def mirror_view(image, nr=640, na=1400):
    return _memo(("mv", str(image), nr, na), lambda: _mirror_view(image, nr, na))


def _mirror_view(image, nr=640, na=1400):
    import numpy as np
    import cv2
    f = find_footprint(image)
    if f.get("no_read"):
        return {"no_read": True, "reason": f.get("reason", "no_footprint")}
    rgb, gray, H, W, OW, OH = _prep(image)
    ink0, thr, paper = _ink(gray)
    ink = _strip_border(ink0)
    cx, cy, r0 = f["cx"], f["cy"], f["r"]
    R = _outer_radius(ink, cx, cy, H, W)
    lim = float(min(cx, cy, W - cx, H - cy))
    if R is None:
        R = lim
    R = float(min(max(R, 2.2 * r0), lim))
    s = float(OW) / float(W)
    g0 = cv2.cvtColor(np.asarray(_pil(image)), cv2.COLOR_RGB2GRAY)
    pol = cv2.warpPolar(g0, (nr, na), (cx * s, cy * s), R * s, cv2.WARP_POLAR_LINEAR)
    mv = np.flip(pol.T, axis=0)
    i0 = int(nr * min(0.85, (r0 * 1.06) / R))
    band = mv[:max(24, nr - i0), :]
    bp = float(np.percentile(band, 80))
    bthr = max(35.0, min(205.0, 0.62 * bp))
    bink = (band.astype(np.float32) < bthr)
    col = bink.mean(axis=0)
    occ = col > 0.015
    best_len, best_start = 0, 0
    if occ.any():
        idx = np.nonzero(occ)[0]
        ext = np.concatenate([idx, idx + na])
        gaps = np.diff(ext)
        k = int(np.argmax(gaps))
        best_len = int(gaps[k] - 1)
        best_start = int((ext[k] + 1) % na)
    wedge_deg = 360.0 * best_len / float(na)
    roll = -(best_start + best_len // 2) % na
    band = np.roll(band, roll, axis=1)
    path = _tmp_path(image, "mv")
    cv2.imwrite(path, band)
    return {"no_read": False, "path": path, "band_h": int(band.shape[0]), "band_w": int(band.shape[1]),
            "cx": cx, "cy": cy, "r0": r0, "R": R, "scale": s, "na": na, "nr": nr,
            "wedge_deg": round(wedge_deg, 1), "roll": int(roll), "bthr": round(bthr, 1),
            "inner_ink": f["inner_ink"], "ring_support": f["ring_support"], "fit": f["fit"],
            "circle_ok": f["circle_ok"], "img_w": W, "img_h": H}


def _ocr_tokens(arr_or_path, fracs=(1.0, 0.62, 0.44, 0.30)):
    import os
    import tempfile
    import numpy as np
    import cv2
    from PIL import Image
    if hasattr(arr_or_path, "shape"):
        a = arr_or_path
        if a.ndim == 2:
            a = cv2.cvtColor(a, cv2.COLOR_GRAY2RGB)
        pil = Image.fromarray(a.astype(np.uint8))
    else:
        pil = _pil(arr_or_path)
    m = int(0.36 * min(pil.size)) + 6
    pad = Image.new("RGB", (pil.width + 2 * m, pil.height + 2 * m), (245, 245, 245))
    pad.paste(pil, (m, m))
    pil = pad
    W0, H0 = pil.size
    rapid = None
    read_tables = None
    try:
        from genolympiad.readers.table_reader import _rapid, read_tables
        rapid = _rapid
    except Exception:
        try:
            from genolympiad.readers.table_reader import read_tables
        except Exception:
            return []
    toks = []
    seen_w = set()
    for fr in fracs:
        w = int(min(1500, W0 * fr))
        if w < 90 or w in seen_w:
            continue
        seen_w.add(w)
        h = max(24, int(H0 * w / float(W0)))
        im = pil.resize((int(w), h), Image.LANCZOS)
        fd, tp = tempfile.mkstemp(suffix=".png")
        os.close(tp) if False else os.close(fd)
        k = W0 / float(w)
        raw = []
        try:
            im.save(tp)
            if rapid is not None:
                res, _t = rapid()(tp)
                for box, txt, conf in (res or []):
                    xs = [q[0] for q in box]
                    ys = [q[1] for q in box]
                    raw.append([min(xs), min(ys), max(xs), max(ys), str(txt)])
            else:
                res = read_tables(tp, borderless=True)
                for b in (getattr(res, "boxes", []) or []):
                    if len(b) >= 5:
                        raw.append([b[0], b[1], b[2], b[3], str(b[4])])
        except Exception:
            raw = []
        finally:
            try:
                os.remove(tp)
            except Exception:
                pass
        for b in raw:
            t = str(b[4]).strip().upper()
            if t:
                toks.append([float(b[0]) * k - m, float(b[1]) * k - m, float(b[2]) * k - m,
                             float(b[3]) * k - m, t])
    return _merge_tokens(toks)


def _merge_tokens(toks):
    if not toks:
        return []
    t = sorted(toks, key=lambda z: 0.5 * (z[0] + z[2]))
    groups = []
    for z in t:
        put = False
        for g in groups:
            gx0 = min(q[0] for q in g)
            gx1 = max(q[2] for q in g)
            gy0 = min(q[1] for q in g)
            gy1 = max(q[3] for q in g)
            ovx = min(gx1, z[2]) - max(gx0, z[0])
            ovy = min(gy1, z[3]) - max(gy0, z[1])
            if (ovx > 0.5 * min(gx1 - gx0, z[2] - z[0])
                    and ovy > 0.4 * min(gy1 - gy0, z[3] - z[1])):
                g.append(z)
                put = True
                break
        if not put:
            groups.append([z])
    out = []
    for g in groups:
        tx = [q[4] for q in g]
        best = max(set(tx), key=lambda s: (tx.count(s), len(s)))
        med = lambda i: float(sorted(q[i] for q in g)[len(g) // 2])
        out.append([med(0), med(1), med(2), med(3), best])
    return out


def _lev(a, b):
    la, lb = len(a), len(b)
    if la == 0 or lb == 0:
        return max(la, lb)
    prev = list(range(lb + 1))
    for i in range(1, la + 1):
        cur = [i] + [0] * lb
        for j in range(1, lb + 1):
            cur[j] = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (a[i - 1] != b[j - 1]))
        prev = cur
    return prev[lb]


def _sim(a, b):
    a = "".join(ch for ch in str(a).upper() if ch.isalnum())
    b = "".join(ch for ch in str(b).upper() if ch.isalnum())
    if not b:
        return 0.0
    if not a:
        return 0.0
    return max(0.0, 1.0 - _lev(a, b) / float(len(b)))


def _best_word(toks, payload):
    best = (0.0, None, None)
    if not toks:
        return best
    t = sorted(toks, key=lambda z: z[0])
    L = max(1, len(payload))
    bw = None
    for i in range(len(t)):
        for j in range(i, min(len(t), i + 7)):
            run = t[i:j + 1]
            y0 = max(z[1] for z in run)
            y1 = min(z[3] for z in run)
            hmin = min(z[3] - z[1] for z in run)
            if len(run) > 1 and (y1 - y0) < 0.35 * hmin:
                continue
            s = ""
            cx0, cx1 = [], []
            for z in run:
                txt = str(z[4])
                n = max(1, len(txt))
                w = (float(z[2]) - float(z[0])) / n
                for c in range(len(txt)):
                    cx0.append(float(z[0]) + c * w)
                    cx1.append(float(z[0]) + (c + 1) * w)
                s += txt
            cands = [(s, 0, len(s))]
            for k in range(0, max(1, len(s) - L + 1)):
                cands.append((s[k:k + L], k, min(len(s), k + L)))
            for cs, a, b in cands:
                if b <= a:
                    continue
                v = _sim(cs, payload)
                x0, x1 = cx0[a], cx1[b - 1]
                w = x1 - x0
                if v > best[0] + 1e-9 or (abs(v - best[0]) <= 1e-9 and bw is not None
                                          and w < bw - 1e-9):
                    best = (v, x0, x1)
                    bw = w
    return best


def _ideal_star(n=5, inner=0.40, size=256):
    import math
    import numpy as np
    import cv2
    pts = []
    for k in range(2 * n):
        a = -math.pi / 2 + k * math.pi / n
        rad = 0.46 if k % 2 == 0 else 0.46 * inner
        pts.append([size / 2 + size * rad * math.cos(a), size / 2 + size * rad * math.sin(a)])
    img = np.zeros((size, size), np.uint8)
    cv2.fillPoly(img, [np.array(pts, np.int32)], 255)
    c, _ = cv2.findContours(img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    return max(c, key=cv2.contourArea)


_IDEAL_CACHE = {}


def _ideal_star_mask(n=5, inner=0.40, off=0.0, size=256):
    import math
    import numpy as np
    import cv2
    key = (n, inner, round(off, 4), size)
    if key in _IDEAL_CACHE:
        return _IDEAL_CACHE[key]
    pts = []
    for k in range(2 * n):
        a = -math.pi / 2 + off + k * math.pi / n
        rad = 1.0 if k % 2 == 0 else inner
        pts.append([math.cos(a) * rad, math.sin(a) * rad])
    q = np.array(pts, np.float64)
    for j in (0, 1):
        lo, hi = q[:, j].min(), q[:, j].max()
        q[:, j] = (q[:, j] - lo) / (hi - lo) * (size - 2) + 1
    m = np.zeros((size, size), np.uint8)
    cv2.fillPoly(m, [q.astype(np.int32)], 255)
    _IDEAL_CACHE[key] = m > 0
    return _IDEAL_CACHE[key]


def _shape_score(mask, n_points=5, normalize=True):
    import numpy as np
    import cv2
    import math as _m
    m = (mask > 0).astype(np.uint8)
    if m.sum() < 200:
        return None
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE,
                         cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))
    cnts, _h = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not cnts:
        return None
    cnts = sorted(cnts, key=cv2.contourArea, reverse=True)[:8]
    best = None
    for c in cnts:
        if cv2.contourArea(c) < 0.005 * m.size:
            continue
        r = _one_shape(c, m, n_points, normalize)
        if r is not None and (best is None or r["_score"] > best["_score"]):
            best = r
    return best


def _one_shape(c, m, n_points, normalize):
    import math
    import numpy as np
    import cv2
    x, y, w, h = cv2.boundingRect(c)
    if w < 12 or h < 12:
        return None
    sub = np.zeros((h, w), np.uint8)
    cv2.drawContours(sub, [c - [x, y]], -1, 255, -1)
    if not normalize:
        side = max(w, h)
        pad = np.zeros((side, side), np.uint8)
        pad[(side - h) // 2:(side - h) // 2 + h, (side - w) // 2:(side - w) // 2 + w] = sub
        sub = pad
    sq = cv2.resize(sub, (256, 256), interpolation=cv2.INTER_AREA)
    sq = (sq > 110).astype(np.uint8) * 255
    cc, _h2 = cv2.findContours(sq, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not cc:
        return None
    c2 = max(cc, key=cv2.contourArea)
    dist = float(cv2.matchShapes(c2, _ideal_star(n_points), cv2.CONTOURS_MATCH_I1, 0.0))
    sqb = sq > 110
    iou = 0.0
    for off in (0.0, math.pi / float(n_points)):
        idl = _ideal_star_mask(n_points, 0.40, off)
        inter = float(np.logical_and(sqb, idl).sum())
        uni = float(np.logical_or(sqb, idl).sum())
        if uni > 0:
            iou = max(iou, inter / uni)
    v = int(len(cv2.approxPolyDP(c2, 0.013 * cv2.arcLength(c2, True), True)))
    hull = cv2.convexHull(c2)
    ha = float(cv2.contourArea(hull))
    sol = float(cv2.contourArea(c2)) / ha if ha > 1 else 1.0
    out = {"dist": round(dist, 4), "iou": round(iou, 4), "verts": v, "solidity": round(sol, 4),
           "x0": int(x), "x1": int(x + w), "y0": int(y), "y1": int(y + h),
           "w": int(w), "h": int(h)}
    out["_score"] = _star_identity(out, n_points)
    return out


def _band(x, target, core, marg):
    if x is None:
        return 0.0
    e = abs(float(x) - float(target))
    if e <= core:
        return 1.0
    if e >= marg:
        return 0.0
    return round((marg - e) / (marg - core), 4)


def _star_identity(sh, n_points=5):
    if sh is None:
        return 0.0
    return ramp(sh.get("iou", 0.0), 0.45, 0.88)


def decode_payload(image, kind, payload, span_deg, n_points=5):
    """Unwrap the artwork around the circle and score the hidden picture and its span."""
    return _memo(("dp", str(image), str(kind), str(payload), float(span_deg)),
                 lambda: _decode_payload(image, kind, payload, span_deg, n_points))


def _decode_payload(image, kind, payload, span_deg, n_points=5):
    import numpy as np
    import cv2
    mv = mirror_view(image)
    if mv.get("no_read"):
        return {"no_read": True, "reason": mv.get("reason"), "identity": 0.0, "span_score": 0.0,
                "reader_blind": False}
    band = cv2.imread(mv["path"], cv2.IMREAD_GRAYSCALE)
    if band is None:
        return {"no_read": True, "reason": "band_lost", "identity": 0.0, "span_score": 0.0,
                "reader_blind": False}
    na = float(mv["na"])
    out = dict(mv)
    out["kind"] = str(kind)
    if str(kind) == "word":
        want = str(payload).strip().upper()
        best = (0.0, None, None)
        n_tok = 0
        for tag, im in (("up", band), ("mirror", np.flip(band, axis=1)),
                        ("inward", np.flip(band, axis=0)),
                        ("both", np.flip(np.flip(band, axis=0), axis=1))):
            toks = _ocr_tokens(im)
            n_tok += len(toks)
            b = _best_word(toks, want)
            if b[0] > best[0]:
                if tag in ("mirror", "both") and b[1] is not None:
                    best = (b[0], band.shape[1] - b[2], band.shape[1] - b[1])
                else:
                    best = b
            if best[0] >= 0.999:
                break
        out["identity"] = round(best[0], 4)
        out["reader_blind"] = bool(n_tok == 0)
        if best[1] is None:
            out["payload_span_deg"] = 0.0
        else:
            bink = (band.astype(np.float32) < mv["bthr"])
            colink = bink.mean(axis=0) > 0.015
            lo = max(0, int(best[1]))
            hi = min(band.shape[1] - 1, int(best[2]))
            idx = np.nonzero(colink[lo:hi + 1])[0]
            if idx.size > 2:
                lo, hi = lo + int(idx[0]), lo + int(idx[-1])
            out["payload_box"] = [int(lo), int(hi)]
            out["payload_span_deg"] = round(360.0 * (hi - lo) / na, 1)
    else:
        bink = (band.astype(np.float32) < mv["bthr"]).astype(np.uint8) * 255
        sh = _shape_score(bink, n_points)
        out["identity"] = _star_identity(sh, n_points)
        out["reader_blind"] = bool(sh is None)
        out["shape"] = sh
        if sh:
            out["payload_box"] = [int(sh["x0"]), int(sh["x1"])]
        out["payload_span_deg"] = round(360.0 * ((sh["x1"] - sh["x0"]) / na), 1) if sh else 0.0
    out["span_score"] = _band(out["payload_span_deg"], float(span_deg), 40.0, 110.0)
    out["frac_cv"] = round(float(out["identity"]) * float(out["span_score"]), 4)
    out["no_read"] = False
    return out


def answer_identity(answer, kind, payload):
    """How well the answer names the hidden word, or 1 if it names a star."""
    text = str(answer or "").strip().upper()
    if str(kind) == "word":
        tokens = [[0.0, 0.0, 1.0, 1.0, t]
                for t in "".join(c if c.isalnum() else " " for c in text).split()]
        score = _best_word(tokens, str(payload).strip().upper())[0]
    else:
        score = 1.0 if "STAR" in text else 0.0
    return round(float(score), 4)


def ramp(x, lo, hi):
    x = float(x)
    if x <= lo:
        return 0.0
    if x >= hi:
        return 1.0
    return round((x - lo) / (hi - lo), 4)


def combine_identity_span(identity, span_score):
    """The span score scaled by how surely the hidden picture was identified."""
    try:
        identity_value = float(identity)
    except Exception:
        identity_value = 0.0
    return round(ramp(identity_value, 0.80, 1.00) * float(span_score), 4)


def footprint_blank(image):
    """Score how free of paint the inside of the cylinder circle is."""
    footprint = find_footprint(image)
    if footprint.get("no_read"):
        return {"no_read": True, "frac": 0.0, "inner_ink": 1.0}
    inner_ink = float(footprint["inner_ink"])
    frac = 1.0 if inner_ink <= 0.010 else (0.0 if inner_ink >= 0.075 else round((0.075 - inner_ink) / 0.065, 4))
    return {"no_read": False, "frac": frac, "inner_ink": round(inner_ink, 4),
            "circle_ok": footprint["circle_ok"], "r": footprint["r"], "cx": footprint["cx"], "cy": footprint["cy"]}


def flat_view_leak(image, kind, payload, n_points=5):
    """Score 1 if the hidden picture cannot be recognised in the flat, unwrapped floor."""
    import numpy as np
    import cv2
    if str(kind) == "word":
        tokens = _ocr_tokens(image)
        similarity = _best_word(tokens, str(payload).strip().upper())[0]
    else:
        rgb, gray, H, W, OW, OH = _prep(image)
        ink = _strip_border(_ink(gray)[0])
        similarity = _star_identity(_shape_score(ink.astype(np.uint8) * 255, n_points, normalize=False),
                             n_points)
    frac = 1.0 if similarity <= 0.50 else (0.0 if similarity >= 0.80 else round((0.80 - similarity) / 0.30, 4))
    return {"no_read": False, "leak": round(float(similarity), 4), "frac": frac}


def draw_evidence(image, kind, payload, span_deg, n_points=5, tag="ev"):
    """Draw the circle, outer edge and picture span on the photo, with the unwrapped band below."""
    import math
    import numpy as np
    import cv2
    from PIL import Image
    decoded = decode_payload(image, kind, payload, span_deg, n_points)
    picture = _pil(image)
    W0, H0 = picture.size
    canvas = np.array(picture).copy()
    if not decoded.get("no_read"):
        s = float(W0) / float(decoded["img_w"])
        cx, cy = decoded["cx"] * s, decoded["cy"] * s
        r0, R = decoded["r0"] * s, decoded["R"] * s
        w = max(2, int(0.004 * min(H0, W0)))
        box = decoded.get("payload_box")
        na = float(decoded.get("na") or 1400)
        roll = float(decoded.get("roll") or 0)
        if box and box[1] > box[0]:
            a0 = 2 * math.pi * ((box[0] - roll) % na) / na
            a1 = 2 * math.pi * ((box[1] - roll) % na) / na
            if a1 < a0:
                a1 += 2 * math.pi
            for a in (a0, a1):
                cv2.line(canvas, (int(cx + r0 * math.cos(a)), int(cy + r0 * math.sin(a))),
                         (int(cx + R * math.cos(a)), int(cy + R * math.sin(a))),
                         (255, 132, 0), w + 1)
            cv2.ellipse(canvas, (int(cx), int(cy)), (int(R * 0.965), int(R * 0.965)), 0.0,
                        math.degrees(a0), math.degrees(a1), (255, 132, 0), w + 1)
        cv2.circle(canvas, (int(cx), int(cy)), int(r0), (235, 0, 200), w + 1)
        cv2.circle(canvas, (int(cx), int(cy)), int(R), (0, 190, 90), w)
        cv2.drawMarker(canvas, (int(cx), int(cy)), (235, 0, 200), cv2.MARKER_CROSS,
                       int(0.5 * r0), w)
        band = cv2.imread(decoded["path"], cv2.IMREAD_GRAYSCALE)
        if band is not None:
            band_height = max(80, int(0.30 * H0))
            band_rgb = cv2.cvtColor(cv2.resize(band, (W0, band_height), interpolation=cv2.INTER_AREA),
                              cv2.COLOR_GRAY2RGB)
            if box and box[1] > box[0]:
                k = float(W0) / float(band.shape[1])
                cv2.rectangle(band_rgb, (int(box[0] * k), 1), (int(box[1] * k), band_height - 2),
                              (255, 132, 0), w + 1)
            cv2.rectangle(band_rgb, (0, 0), (W0 - 1, band_height - 1), (0, 190, 90), w)
            canvas = np.concatenate([canvas, band_rgb], axis=0)
    path = _tmp_path(image, tag)
    Image.fromarray(canvas).save(path)
    out = {"path": path}
    for k in ("identity", "span_score", "payload_span_deg", "wedge_deg", "inner_ink",
              "ring_support", "fit", "frac_cv", "no_read"):
        if k in decoded:
            out[k] = decoded[k]
    return out

# end of find_footprint_code

# code: _leafval_code
def pass_at_half(x):
    """Score 1 if the value is at least 0.5, else 0."""
    return 1.0 if float(x or 0.0) >= 0.5 else 0.0

# end of _leafval_code
