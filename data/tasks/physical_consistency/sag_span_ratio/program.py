# shared code: code_62024d8d9cb8
def check_cable_count(m, k):
    """1 if exactly k cable curves were measured, else 0."""
    return cables_readable_frac(m, k)
import numpy as np
import cv2

cv2.setNumThreads(2)

_HUE = {"red": [(0, 8), (168, 180)], "orange": [(8, 21)], "yellow": [(21, 36)],
        "green": [(38, 85)], "cyan": [(85, 100)], "blue": [(96, 130)],
        "purple": [(128, 158)], "violet": [(128, 158)], "magenta": [(140, 170)]}


def _load(image, cap=1500):
    a = cv2.imread(str(image), cv2.IMREAD_COLOR)
    if a is None:
        return None
    h, w = a.shape[:2]
    if max(h, w) > cap:
        s = cap / float(max(h, w))
        a = cv2.resize(a, (int(w * s), int(h * s)), interpolation=cv2.INTER_AREA)
    return a


def _clean(m, k=3):
    ker = np.ones((k, k), np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, ker)
    return cv2.morphologyEx(m, cv2.MORPH_OPEN, ker)


def sag_read(image, colours):
    bgr = _load(image)
    if bgr is None:
        return {"no_read": True, "reason": "unreadable_file", "n_curves": 0}
    H, W = bgr.shape[:2]
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    out, found = [], 0
    for c in colours:
        name = str(c).lower()
        m = np.zeros(bgr.shape[:2], np.uint8)
        for lo, hi in _HUE[name]:
            m |= cv2.inRange(hsv, (lo, 70, 50), (min(hi, 179), 255, 255))
        m = _clean(m, 3)
        n, lab, st, cen = cv2.connectedComponentsWithStats(m, 8)
        best = None
        for i in range(1, n):
            x, y, w, h, a = st[i]
            if a < 0.00012 * m.size:
                continue
            if w < 1.8 * max(1, h) or w < 0.05 * W:
                continue
            if best is None or a > best[1]:
                best = (int(i), int(a))
        if best is None:
            out.append({"colour": name, "ratio": None, "span_px": None})
            continue
        ys, xs = np.nonzero(lab == best[0])
        x0, x1 = int(xs.min()), int(xs.max())
        span = x1 - x0
        if span < 0.045 * W:
            out.append({"colour": name, "ratio": None, "span_px": int(span)})
            continue

        def yat(xc, half=3):
            sel = ys[(xs >= xc - half) & (xs <= xc + half)]
            return float(sel.mean()) if sel.size else None

        yl, yr, ym = yat(x0 + 3), yat(x1 - 3), yat((x0 + x1) // 2)
        if yl is None or yr is None or ym is None:
            out.append({"colour": name, "ratio": None, "span_px": int(span)})
            continue
        dip = ym - 0.5 * (yl + yr)
        found += 1
        out.append({"colour": name, "ratio": round(dip / float(span), 5),
                    "span_px": int(span), "dip_px": round(float(dip), 1),
                    "x0": x0, "x1": x1, "y_left": round(yl, 1), "y_right": round(yr, 1),
                    "y_mid": round(ym, 1)})
    return {"no_read": bool(found == 0), "n_curves": found, "curves": out,
            "ratios": [c["ratio"] for c in out], "H": H, "W": W}


def cables_readable_frac(m, k):
    if m.get("no_read"):
        return 0.0
    return 1.0 if int(m.get("n_curves") or 0) == int(k) else 0.0


def _bandfrac(err, core, margin):
    err = abs(float(err))
    if err <= core:
        return 1.0
    if err >= margin:
        return 0.0
    return round(1.0 - (err - core) / (margin - core), 4)


def dip_ratio_frac(m, targets, rel_core=0.25, rel_margin=0.40,
                   abs_core=0.004, abs_margin=0.008):
    if m.get("no_read"):
        return 0.0
    got = list(m.get("ratios") or [])
    t = [float(x) for x in targets]
    if len(got) != len(t):
        return 0.0
    per = []
    for g, ti in zip(got, t):
        if g is None:
            per.append(0.0)
            continue
        core = max(float(abs_core), float(rel_core) * abs(ti))
        marg = max(float(abs_margin), float(rel_margin) * abs(ti))
        per.append(_bandfrac(g - ti, core, max(marg, core + 1e-6)))
    return round(sum(per) / float(len(per)), 4)


def sag_overlay(image, colours, targets, out_path):
    m = sag_read(image, colours)
    bgr = _load(image)
    if bgr is None:
        return {"no_read": True, "path": None}
    vis = bgr.copy()
    for i, c in enumerate(m.get("curves") or []):
        if c.get("ratio") is None:
            continue
        x0, x1 = c["x0"], c["x1"]
        yl, yr, ym = c["y_left"], c["y_right"], c["y_mid"]
        cv2.line(vis, (x0, int(yl)), (x1, int(yr)), (255, 255, 255), 1)
        xm = (x0 + x1) // 2
        cv2.line(vis, (xm, int(0.5 * (yl + yr))), (xm, int(ym)), (60, 60, 235), 2)
        cv2.putText(vis, "%.3f/%.3f" % (c["ratio"], float(targets[i])),
                    (x0, max(14, int(min(yl, ym)) - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                    (0, 0, 0), 2)
    cv2.imwrite(str(out_path), vis)
    return {"no_read": bool(m.get("no_read")), "path": str(out_path)}


def overlay_frac(image, colours, targets):
    import hashlib
    import os
    import tempfile
    d = os.path.join(tempfile.gettempdir(), "genolympiad_overlay")
    try:
        os.makedirs(d, exist_ok=True)
    except Exception:
        pass
    h = hashlib.md5(str(image).encode("utf-8", "replace")).hexdigest()[:12]
    try:
        sag_overlay(image, colours, targets, os.path.join(d, "sag_%s.png" % h))
    except Exception:
        pass
    return 1.0

# end of code_62024d8d9cb8

# shared code: code_9979297637ea
import numpy as np
import cv2

cv2.setNumThreads(2)

_HUE = {"red": [(0, 8), (168, 180)], "orange": [(8, 21)], "yellow": [(21, 36)],
        "green": [(38, 85)], "cyan": [(85, 100)], "blue": [(96, 130)],
        "purple": [(128, 158)], "violet": [(128, 158)], "magenta": [(140, 170)]}


def _load(image, cap=1500):
    a = cv2.imread(str(image), cv2.IMREAD_COLOR)
    if a is None:
        return None
    h, w = a.shape[:2]
    if max(h, w) > cap:
        s = cap / float(max(h, w))
        a = cv2.resize(a, (int(w * s), int(h * s)), interpolation=cv2.INTER_AREA)
    return a


def _clean(m, k=3):
    ker = np.ones((k, k), np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, ker)
    return cv2.morphologyEx(m, cv2.MORPH_OPEN, ker)


def sag_read(image, colours):
    """For each cable colour, find its curve and measure the dip as a share of the span."""
    bgr = _load(image)
    if bgr is None:
        return {"no_read": True, "reason": "unreadable_file", "n_curves": 0}
    H, W = bgr.shape[:2]
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    out, found = [], 0
    for c in colours:
        name = str(c).lower()
        m = np.zeros(bgr.shape[:2], np.uint8)
        for lo, hi in _HUE[name]:
            m |= cv2.inRange(hsv, (lo, 70, 50), (min(hi, 179), 255, 255))
        m = _clean(m, 3)
        n, labels, stats, centroids = cv2.connectedComponentsWithStats(m, 8)
        best = None
        for i in range(1, n):
            x, y, w, h, a = stats[i]
            if a < 0.00012 * m.size:
                continue
            if w < 1.8 * max(1, h) or w < 0.05 * W:
                continue
            if best is None or a > best[1]:
                best = (int(i), int(a))
        if best is None:
            out.append({"colour": name, "ratio": None, "span_px": None})
            continue
        ys, xs = np.nonzero(labels == best[0])
        x0, x1 = int(xs.min()), int(xs.max())
        span = x1 - x0
        if span < 0.045 * W:
            out.append({"colour": name, "ratio": None, "span_px": int(span)})
            continue

        def yat(xc, half=3):
            sel = ys[(xs >= xc - half) & (xs <= xc + half)]
            return float(sel.mean()) if sel.size else None

        y_left, y_right, y_mid = yat(x0 + 3), yat(x1 - 3), yat((x0 + x1) // 2)
        if y_left is None or y_right is None or y_mid is None:
            out.append({"colour": name, "ratio": None, "span_px": int(span)})
            continue
        dip = y_mid - 0.5 * (y_left + y_right)
        found += 1
        out.append({"colour": name, "ratio": round(dip / float(span), 5),
                    "span_px": int(span), "dip_px": round(float(dip), 1),
                    "x0": x0, "x1": x1, "y_left": round(y_left, 1), "y_right": round(y_right, 1),
                    "y_mid": round(y_mid, 1)})
    return {"no_read": bool(found == 0), "n_curves": found, "curves": out,
            "ratios": [c["ratio"] for c in out], "H": H, "W": W}


def cables_readable_frac(m, k):
    if m.get("no_read"):
        return 0.0
    return 1.0 if int(m.get("n_curves") or 0) == int(k) else 0.0


def _bandfrac(err, core, margin):
    err = abs(float(err))
    if err <= core:
        return 1.0
    if err >= margin:
        return 0.0
    return round(1.0 - (err - core) / (margin - core), 4)


def dip_ratio_frac(m, targets, rel_core=0.25, rel_margin=0.40,
                   abs_core=0.004, abs_margin=0.008):
    if m.get("no_read"):
        return 0.0
    got = list(m.get("ratios") or [])
    t = [float(x) for x in targets]
    if len(got) != len(t):
        return 0.0
    per = []
    for g, ti in zip(got, t):
        if g is None:
            per.append(0.0)
            continue
        core = max(float(abs_core), float(rel_core) * abs(ti))
        marg = max(float(abs_margin), float(rel_margin) * abs(ti))
        per.append(_bandfrac(g - ti, core, max(marg, core + 1e-6)))
    return round(sum(per) / float(len(per)), 4)


def sag_overlay(image, colours, targets, out_path):
    m = sag_read(image, colours)
    bgr = _load(image)
    if bgr is None:
        return {"no_read": True, "path": None}
    vis = bgr.copy()
    for i, c in enumerate(m.get("curves") or []):
        if c.get("ratio") is None:
            continue
        x0, x1 = c["x0"], c["x1"]
        yl, yr, ym = c["y_left"], c["y_right"], c["y_mid"]
        cv2.line(vis, (x0, int(yl)), (x1, int(yr)), (255, 255, 255), 1)
        xm = (x0 + x1) // 2
        cv2.line(vis, (xm, int(0.5 * (yl + yr))), (xm, int(ym)), (60, 60, 235), 2)
        cv2.putText(vis, "%.3f/%.3f" % (c["ratio"], float(targets[i])),
                    (x0, max(14, int(min(yl, ym)) - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                    (0, 0, 0), 2)
    cv2.imwrite(str(out_path), vis)
    return {"no_read": bool(m.get("no_read")), "path": str(out_path)}


def overlay_frac(image, colours, targets):
    """Save a picture marking each cable's measured dip, then return 1 always."""
    import hashlib
    import os
    import tempfile
    overlay_dir = os.path.join(tempfile.gettempdir(), "genolympiad_overlay")
    try:
        os.makedirs(overlay_dir, exist_ok=True)
    except Exception:
        pass
    name_hash = hashlib.md5(str(image).encode("utf-8", "replace")).hexdigest()[:12]
    try:
        sag_overlay(image, colours, targets, os.path.join(overlay_dir, "sag_%s.png" % name_hash))
    except Exception:
        pass
    return 1.0

# end of code_9979297637ea

# shared code: code_d899ea7c9dff
def score_dip_ratios(m, t):
    """Mean closeness of each cable's dip to span ratio to its target."""
    return dip_ratio_frac(m, t)
import numpy as np
import cv2

cv2.setNumThreads(2)

_HUE = {"red": [(0, 8), (168, 180)], "orange": [(8, 21)], "yellow": [(21, 36)],
        "green": [(38, 85)], "cyan": [(85, 100)], "blue": [(96, 130)],
        "purple": [(128, 158)], "violet": [(128, 158)], "magenta": [(140, 170)]}


def _load(image, cap=1500):
    a = cv2.imread(str(image), cv2.IMREAD_COLOR)
    if a is None:
        return None
    h, w = a.shape[:2]
    if max(h, w) > cap:
        s = cap / float(max(h, w))
        a = cv2.resize(a, (int(w * s), int(h * s)), interpolation=cv2.INTER_AREA)
    return a


def _clean(m, k=3):
    ker = np.ones((k, k), np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, ker)
    return cv2.morphologyEx(m, cv2.MORPH_OPEN, ker)


def sag_read(image, colours):
    bgr = _load(image)
    if bgr is None:
        return {"no_read": True, "reason": "unreadable_file", "n_curves": 0}
    H, W = bgr.shape[:2]
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    out, found = [], 0
    for c in colours:
        name = str(c).lower()
        m = np.zeros(bgr.shape[:2], np.uint8)
        for lo, hi in _HUE[name]:
            m |= cv2.inRange(hsv, (lo, 70, 50), (min(hi, 179), 255, 255))
        m = _clean(m, 3)
        n, lab, st, cen = cv2.connectedComponentsWithStats(m, 8)
        best = None
        for i in range(1, n):
            x, y, w, h, a = st[i]
            if a < 0.00012 * m.size:
                continue
            if w < 1.8 * max(1, h) or w < 0.05 * W:
                continue
            if best is None or a > best[1]:
                best = (int(i), int(a))
        if best is None:
            out.append({"colour": name, "ratio": None, "span_px": None})
            continue
        ys, xs = np.nonzero(lab == best[0])
        x0, x1 = int(xs.min()), int(xs.max())
        span = x1 - x0
        if span < 0.045 * W:
            out.append({"colour": name, "ratio": None, "span_px": int(span)})
            continue

        def yat(xc, half=3):
            sel = ys[(xs >= xc - half) & (xs <= xc + half)]
            return float(sel.mean()) if sel.size else None

        yl, yr, ym = yat(x0 + 3), yat(x1 - 3), yat((x0 + x1) // 2)
        if yl is None or yr is None or ym is None:
            out.append({"colour": name, "ratio": None, "span_px": int(span)})
            continue
        dip = ym - 0.5 * (yl + yr)
        found += 1
        out.append({"colour": name, "ratio": round(dip / float(span), 5),
                    "span_px": int(span), "dip_px": round(float(dip), 1),
                    "x0": x0, "x1": x1, "y_left": round(yl, 1), "y_right": round(yr, 1),
                    "y_mid": round(ym, 1)})
    return {"no_read": bool(found == 0), "n_curves": found, "curves": out,
            "ratios": [c["ratio"] for c in out], "H": H, "W": W}


def cables_readable_frac(m, k):
    if m.get("no_read"):
        return 0.0
    return 1.0 if int(m.get("n_curves") or 0) == int(k) else 0.0


def _bandfrac(err, core, margin):
    err = abs(float(err))
    if err <= core:
        return 1.0
    if err >= margin:
        return 0.0
    return round(1.0 - (err - core) / (margin - core), 4)


def dip_ratio_frac(m, targets, rel_core=0.25, rel_margin=0.40,
                   abs_core=0.004, abs_margin=0.008):
    if m.get("no_read"):
        return 0.0
    got = list(m.get("ratios") or [])
    t = [float(x) for x in targets]
    if len(got) != len(t):
        return 0.0
    per = []
    for g, ti in zip(got, t):
        if g is None:
            per.append(0.0)
            continue
        core = max(float(abs_core), float(rel_core) * abs(ti))
        marg = max(float(abs_margin), float(rel_margin) * abs(ti))
        per.append(_bandfrac(g - ti, core, max(marg, core + 1e-6)))
    return round(sum(per) / float(len(per)), 4)


def sag_overlay(image, colours, targets, out_path):
    m = sag_read(image, colours)
    bgr = _load(image)
    if bgr is None:
        return {"no_read": True, "path": None}
    vis = bgr.copy()
    for i, c in enumerate(m.get("curves") or []):
        if c.get("ratio") is None:
            continue
        x0, x1 = c["x0"], c["x1"]
        yl, yr, ym = c["y_left"], c["y_right"], c["y_mid"]
        cv2.line(vis, (x0, int(yl)), (x1, int(yr)), (255, 255, 255), 1)
        xm = (x0 + x1) // 2
        cv2.line(vis, (xm, int(0.5 * (yl + yr))), (xm, int(ym)), (60, 60, 235), 2)
        cv2.putText(vis, "%.3f/%.3f" % (c["ratio"], float(targets[i])),
                    (x0, max(14, int(min(yl, ym)) - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                    (0, 0, 0), 2)
    cv2.imwrite(str(out_path), vis)
    return {"no_read": bool(m.get("no_read")), "path": str(out_path)}


def overlay_frac(image, colours, targets):
    import hashlib
    import os
    import tempfile
    d = os.path.join(tempfile.gettempdir(), "genolympiad_overlay")
    try:
        os.makedirs(d, exist_ok=True)
    except Exception:
        pass
    h = hashlib.md5(str(image).encode("utf-8", "replace")).hexdigest()[:12]
    try:
        sag_overlay(image, colours, targets, os.path.join(d, "sag_%s.png" % h))
    except Exception:
        pass
    return 1.0

# end of code_d899ea7c9dff
