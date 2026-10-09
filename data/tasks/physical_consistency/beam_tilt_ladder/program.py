# code: beam_read_code
import numpy as np
import cv2

cv2.setNumThreads(2)


def _load(image, cap=1500):
    a = cv2.imread(str(image), cv2.IMREAD_COLOR)
    if a is None:
        return None
    h, w = a.shape[:2]
    if max(h, w) > cap:
        s = cap / float(max(h, w))
        a = cv2.resize(a, (int(w * s), int(h * s)), interpolation=cv2.INTER_AREA)
    return a


def _clean(m, k=5):
    ker = np.ones((k, k), np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, ker)
    return cv2.morphologyEx(m, cv2.MORPH_OPEN, ker)


def _mask(bgr, lo, hi):
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    m = cv2.inRange(hsv, tuple(int(v) for v in lo), tuple(int(v) for v in hi))
    if float(lo[0]) <= 2 and float(hi[0]) <= 25:
        m |= cv2.inRange(hsv, (int(180 - hi[0]), int(lo[1]), int(lo[2])), (179, 255, 255))
    return _clean(m, 5)


def measure_beam_tilts(image, lo, hi, k):
    """Find the red beams by colour and measure each one's tilt in degrees, top to bottom."""
    bgr = _load(image)
    if bgr is None:
        return {"no_read": True, "reason": "unreadable_file", "n_bars": 0, "tilts": []}
    H, W = bgr.shape[:2]
    m = _mask(bgr, lo, hi)
    n, lab, st, cen = cv2.connectedComponentsWithStats(m, 8)
    bars = []
    for i in range(1, n):
        x, y, w, h, a = st[i]
        if a < 0.0006 * m.size:
            continue
        if w < 1.8 * max(1, h) or not (0.055 * W < w < 0.93 * W) or h > 0.30 * H:
            continue
        if x <= 2 or x + w >= W - 2:
            continue
        bars.append({"i": int(i), "x": int(x), "y": int(y), "w": int(w), "h": int(h),
                     "cx": float(cen[i][0]), "cy": float(cen[i][1])})
    bars.sort(key=lambda z: -z["w"])
    keep = []
    for b in bars:
        dup = False
        for a2 in keep:
            ov = min(a2["x"] + a2["w"], b["x"] + b["w"]) - max(a2["x"], b["x"])
            if ov > 0.6 * b["w"] and abs(a2["cy"] - b["cy"]) < 0.06 * H:
                dup = True
                break
        if not dup:
            keep.append(b)
    if not keep:
        return {"no_read": True, "reason": "no_beam_layer", "n_bars": 0, "tilts": []}
    rows = []
    for b in keep:
        ys, xs = np.nonzero(lab == b["i"])
        vx, vy, x0, y0 = cv2.fitLine(np.stack([xs, ys], 1).astype(np.float32),
                                     cv2.DIST_L2, 0, 0.01, 0.01).ravel()
        ang = float(np.degrees(np.arctan2(vy, vx)))
        if ang > 90:
            ang -= 180
        if ang < -90:
            ang += 180
        rows.append({"x": b["x"], "w": b["w"], "cx": b["cx"], "cy": b["cy"],
                     "y": b["y"], "h": b["h"], "tilt_deg": round(ang, 2)})
    xs0 = [r["x"] for r in rows]
    stacked = (max(xs0) - min(xs0)) < 0.25 * W if len(rows) > 1 else True
    rows.sort(key=lambda r: (r["cy"], r["cx"]) if stacked else (r["cx"], r["cy"]))
    return {"no_read": False, "n_bars": len(rows), "bars": rows,
            "tilts": [r["tilt_deg"] for r in rows],
            "layout": "stacked" if stacked else "row", "k_expected": int(k), "H": H, "W": W}


def beams_readable_frac(m, k):
    if m.get("no_read"):
        return 0.0
    return 1.0 if int(m.get("n_bars") or 0) == int(k) else 0.0


def _bandfrac(err, core, margin):
    err = abs(float(err))
    if err <= core:
        return 1.0
    if err >= margin:
        return 0.0
    return round(1.0 - (err - core) / (margin - core), 4)


def per_beam_frac(m, targets, rel=0.20, floor_deg=2.0, ramp=2.0):
    if m.get("no_read"):
        return 0.0
    got = list(m.get("tilts") or [])
    t = [float(x) for x in targets]
    if len(got) != len(t):
        return 0.0
    per = []
    for g, ti in zip(got, t):
        core = max(float(floor_deg), float(rel) * abs(ti))
        per.append(_bandfrac(g - ti, core, ramp * core))
    return round(sum(per) / float(len(per)), 4)


def magnitude_ratio(m, targets):
    got = list(m.get("tilts") or [])
    t = [float(x) for x in targets]
    if m.get("no_read") or len(got) != len(t):
        return None
    v = [abs(got[i]) for i in range(len(t)) if abs(t[i]) >= 1e-6]
    if len(v) < 2:
        return None
    return round(max(v) / max(1.0, min(v)), 3)


def magnitude_ratio_frac(m, targets, core=0.25, margin=0.55):
    got = magnitude_ratio(m, targets)
    if got is None:
        return 0.0
    t = [abs(float(x)) for x in targets if abs(float(x)) >= 1e-6]
    if len(t) < 2:
        return 0.0
    want = max(t) / min(t)
    return _bandfrac((got - want) / want, core, margin)


def beam_overlay(image, lo, hi, targets, out_path):
    m = measure_beam_tilts(image, lo, hi, len(targets))
    bgr = _load(image)
    if bgr is None:
        return {"no_read": True, "path": None}
    vis = bgr.copy()
    if not m.get("no_read"):
        for i, b in enumerate(m["bars"]):
            want = float(targets[i]) if i < len(targets) else None
            cv2.rectangle(vis, (b["x"], b["y"]), (b["x"] + b["w"], b["y"] + b["h"]),
                          (0, 200, 255), 2)
            import math
            th = math.radians(b["tilt_deg"])
            hx = 0.5 * b["w"] * math.cos(th)
            hy = 0.5 * b["w"] * math.sin(th)
            cv2.line(vis, (int(b["cx"] - hx), int(b["cy"] - hy)),
                     (int(b["cx"] + hx), int(b["cy"] + hy)), (60, 60, 235), 2)
            cv2.putText(vis, "%.1f/%s" % (b["tilt_deg"], "-" if want is None else "%.1f" % want),
                        (b["x"], max(14, b["y"] - 6)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)
        r = magnitude_ratio(m, targets)
        cv2.putText(vis, "range %s (want %.2f)" % (r, max(abs(float(x)) for x in targets) /
                                                   min([abs(float(x)) for x in targets
                                                        if abs(float(x)) >= 1e-6] or [1.0])),
                    (12, 26), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
    cv2.imwrite(str(out_path), vis)
    return {"no_read": bool(m.get("no_read")), "path": str(out_path)}


def draw_tilt_overlay(image, lo, hi, targets):
    """Save a picture of the measured beam tilts for review; always scores 1."""
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
        beam_overlay(image, lo, hi, targets, os.path.join(d, "tilt_%s.png" % h))
    except Exception:
        pass
    return 1.0

# end of beam_read_code

# code: f_code
def beam_count_score(reading, k):
    """Score 1 when the number of beams found equals the number drawn in the prompt."""
    return beams_readable_frac(reading, k)
import numpy as np
import cv2

cv2.setNumThreads(2)


def _load(image, cap=1500):
    a = cv2.imread(str(image), cv2.IMREAD_COLOR)
    if a is None:
        return None
    h, w = a.shape[:2]
    if max(h, w) > cap:
        s = cap / float(max(h, w))
        a = cv2.resize(a, (int(w * s), int(h * s)), interpolation=cv2.INTER_AREA)
    return a


def _clean(m, k=5):
    ker = np.ones((k, k), np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, ker)
    return cv2.morphologyEx(m, cv2.MORPH_OPEN, ker)


def _mask(bgr, lo, hi):
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    m = cv2.inRange(hsv, tuple(int(v) for v in lo), tuple(int(v) for v in hi))
    if float(lo[0]) <= 2 and float(hi[0]) <= 25:
        m |= cv2.inRange(hsv, (int(180 - hi[0]), int(lo[1]), int(lo[2])), (179, 255, 255))
    return _clean(m, 5)


def measure_beam_tilts(image, lo, hi, k):
    bgr = _load(image)
    if bgr is None:
        return {"no_read": True, "reason": "unreadable_file", "n_bars": 0, "tilts": []}
    H, W = bgr.shape[:2]
    m = _mask(bgr, lo, hi)
    n, lab, st, cen = cv2.connectedComponentsWithStats(m, 8)
    bars = []
    for i in range(1, n):
        x, y, w, h, a = st[i]
        if a < 0.0006 * m.size:
            continue
        if w < 1.8 * max(1, h) or not (0.055 * W < w < 0.93 * W) or h > 0.30 * H:
            continue
        if x <= 2 or x + w >= W - 2:
            continue
        bars.append({"i": int(i), "x": int(x), "y": int(y), "w": int(w), "h": int(h),
                     "cx": float(cen[i][0]), "cy": float(cen[i][1])})
    bars.sort(key=lambda z: -z["w"])
    keep = []
    for b in bars:
        dup = False
        for a2 in keep:
            ov = min(a2["x"] + a2["w"], b["x"] + b["w"]) - max(a2["x"], b["x"])
            if ov > 0.6 * b["w"] and abs(a2["cy"] - b["cy"]) < 0.06 * H:
                dup = True
                break
        if not dup:
            keep.append(b)
    if not keep:
        return {"no_read": True, "reason": "no_beam_layer", "n_bars": 0, "tilts": []}
    rows = []
    for b in keep:
        ys, xs = np.nonzero(lab == b["i"])
        vx, vy, x0, y0 = cv2.fitLine(np.stack([xs, ys], 1).astype(np.float32),
                                     cv2.DIST_L2, 0, 0.01, 0.01).ravel()
        ang = float(np.degrees(np.arctan2(vy, vx)))
        if ang > 90:
            ang -= 180
        if ang < -90:
            ang += 180
        rows.append({"x": b["x"], "w": b["w"], "cx": b["cx"], "cy": b["cy"],
                     "y": b["y"], "h": b["h"], "tilt_deg": round(ang, 2)})
    xs0 = [r["x"] for r in rows]
    stacked = (max(xs0) - min(xs0)) < 0.25 * W if len(rows) > 1 else True
    rows.sort(key=lambda r: (r["cy"], r["cx"]) if stacked else (r["cx"], r["cy"]))
    return {"no_read": False, "n_bars": len(rows), "bars": rows,
            "tilts": [r["tilt_deg"] for r in rows],
            "layout": "stacked" if stacked else "row", "k_expected": int(k), "H": H, "W": W}


def beams_readable_frac(m, k):
    if m.get("no_read"):
        return 0.0
    return 1.0 if int(m.get("n_bars") or 0) == int(k) else 0.0


def _bandfrac(err, core, margin):
    err = abs(float(err))
    if err <= core:
        return 1.0
    if err >= margin:
        return 0.0
    return round(1.0 - (err - core) / (margin - core), 4)


def per_beam_frac(m, targets, rel=0.20, floor_deg=2.0, ramp=2.0):
    if m.get("no_read"):
        return 0.0
    got = list(m.get("tilts") or [])
    t = [float(x) for x in targets]
    if len(got) != len(t):
        return 0.0
    per = []
    for g, ti in zip(got, t):
        core = max(float(floor_deg), float(rel) * abs(ti))
        per.append(_bandfrac(g - ti, core, ramp * core))
    return round(sum(per) / float(len(per)), 4)


def magnitude_ratio(m, targets):
    got = list(m.get("tilts") or [])
    t = [float(x) for x in targets]
    if m.get("no_read") or len(got) != len(t):
        return None
    v = [abs(got[i]) for i in range(len(t)) if abs(t[i]) >= 1e-6]
    if len(v) < 2:
        return None
    return round(max(v) / max(1.0, min(v)), 3)


def magnitude_ratio_frac(m, targets, core=0.25, margin=0.55):
    got = magnitude_ratio(m, targets)
    if got is None:
        return 0.0
    t = [abs(float(x)) for x in targets if abs(float(x)) >= 1e-6]
    if len(t) < 2:
        return 0.0
    want = max(t) / min(t)
    return _bandfrac((got - want) / want, core, margin)


def beam_overlay(image, lo, hi, targets, out_path):
    m = measure_beam_tilts(image, lo, hi, len(targets))
    bgr = _load(image)
    if bgr is None:
        return {"no_read": True, "path": None}
    vis = bgr.copy()
    if not m.get("no_read"):
        for i, b in enumerate(m["bars"]):
            want = float(targets[i]) if i < len(targets) else None
            cv2.rectangle(vis, (b["x"], b["y"]), (b["x"] + b["w"], b["y"] + b["h"]),
                          (0, 200, 255), 2)
            import math
            th = math.radians(b["tilt_deg"])
            hx = 0.5 * b["w"] * math.cos(th)
            hy = 0.5 * b["w"] * math.sin(th)
            cv2.line(vis, (int(b["cx"] - hx), int(b["cy"] - hy)),
                     (int(b["cx"] + hx), int(b["cy"] + hy)), (60, 60, 235), 2)
            cv2.putText(vis, "%.1f/%s" % (b["tilt_deg"], "-" if want is None else "%.1f" % want),
                        (b["x"], max(14, b["y"] - 6)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)
        r = magnitude_ratio(m, targets)
        cv2.putText(vis, "range %s (want %.2f)" % (r, max(abs(float(x)) for x in targets) /
                                                   min([abs(float(x)) for x in targets
                                                        if abs(float(x)) >= 1e-6] or [1.0])),
                    (12, 26), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
    cv2.imwrite(str(out_path), vis)
    return {"no_read": bool(m.get("no_read")), "path": str(out_path)}


def draw_tilt_overlay(image, lo, hi, targets):
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
        beam_overlay(image, lo, hi, targets, os.path.join(d, "tilt_%s.png" % h))
    except Exception:
        pass
    return 1.0

# end of f_code

# code: f_code_2
def tilt_match_score(reading, targets):
    """The mean per-beam closeness of measured tilts to the target tilts."""
    return per_beam_frac(reading, targets)
import numpy as np
import cv2

cv2.setNumThreads(2)


def _load(image, cap=1500):
    a = cv2.imread(str(image), cv2.IMREAD_COLOR)
    if a is None:
        return None
    h, w = a.shape[:2]
    if max(h, w) > cap:
        s = cap / float(max(h, w))
        a = cv2.resize(a, (int(w * s), int(h * s)), interpolation=cv2.INTER_AREA)
    return a


def _clean(m, k=5):
    ker = np.ones((k, k), np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, ker)
    return cv2.morphologyEx(m, cv2.MORPH_OPEN, ker)


def _mask(bgr, lo, hi):
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    m = cv2.inRange(hsv, tuple(int(v) for v in lo), tuple(int(v) for v in hi))
    if float(lo[0]) <= 2 and float(hi[0]) <= 25:
        m |= cv2.inRange(hsv, (int(180 - hi[0]), int(lo[1]), int(lo[2])), (179, 255, 255))
    return _clean(m, 5)


def measure_beam_tilts(image, lo, hi, k):
    bgr = _load(image)
    if bgr is None:
        return {"no_read": True, "reason": "unreadable_file", "n_bars": 0, "tilts": []}
    H, W = bgr.shape[:2]
    m = _mask(bgr, lo, hi)
    n, lab, st, cen = cv2.connectedComponentsWithStats(m, 8)
    bars = []
    for i in range(1, n):
        x, y, w, h, a = st[i]
        if a < 0.0006 * m.size:
            continue
        if w < 1.8 * max(1, h) or not (0.055 * W < w < 0.93 * W) or h > 0.30 * H:
            continue
        if x <= 2 or x + w >= W - 2:
            continue
        bars.append({"i": int(i), "x": int(x), "y": int(y), "w": int(w), "h": int(h),
                     "cx": float(cen[i][0]), "cy": float(cen[i][1])})
    bars.sort(key=lambda z: -z["w"])
    keep = []
    for b in bars:
        dup = False
        for a2 in keep:
            ov = min(a2["x"] + a2["w"], b["x"] + b["w"]) - max(a2["x"], b["x"])
            if ov > 0.6 * b["w"] and abs(a2["cy"] - b["cy"]) < 0.06 * H:
                dup = True
                break
        if not dup:
            keep.append(b)
    if not keep:
        return {"no_read": True, "reason": "no_beam_layer", "n_bars": 0, "tilts": []}
    rows = []
    for b in keep:
        ys, xs = np.nonzero(lab == b["i"])
        vx, vy, x0, y0 = cv2.fitLine(np.stack([xs, ys], 1).astype(np.float32),
                                     cv2.DIST_L2, 0, 0.01, 0.01).ravel()
        ang = float(np.degrees(np.arctan2(vy, vx)))
        if ang > 90:
            ang -= 180
        if ang < -90:
            ang += 180
        rows.append({"x": b["x"], "w": b["w"], "cx": b["cx"], "cy": b["cy"],
                     "y": b["y"], "h": b["h"], "tilt_deg": round(ang, 2)})
    xs0 = [r["x"] for r in rows]
    stacked = (max(xs0) - min(xs0)) < 0.25 * W if len(rows) > 1 else True
    rows.sort(key=lambda r: (r["cy"], r["cx"]) if stacked else (r["cx"], r["cy"]))
    return {"no_read": False, "n_bars": len(rows), "bars": rows,
            "tilts": [r["tilt_deg"] for r in rows],
            "layout": "stacked" if stacked else "row", "k_expected": int(k), "H": H, "W": W}


def beams_readable_frac(m, k):
    if m.get("no_read"):
        return 0.0
    return 1.0 if int(m.get("n_bars") or 0) == int(k) else 0.0


def _bandfrac(err, core, margin):
    err = abs(float(err))
    if err <= core:
        return 1.0
    if err >= margin:
        return 0.0
    return round(1.0 - (err - core) / (margin - core), 4)


def per_beam_frac(m, targets, rel=0.20, floor_deg=2.0, ramp=2.0):
    if m.get("no_read"):
        return 0.0
    got = list(m.get("tilts") or [])
    t = [float(x) for x in targets]
    if len(got) != len(t):
        return 0.0
    per = []
    for g, ti in zip(got, t):
        core = max(float(floor_deg), float(rel) * abs(ti))
        per.append(_bandfrac(g - ti, core, ramp * core))
    return round(sum(per) / float(len(per)), 4)


def magnitude_ratio(m, targets):
    got = list(m.get("tilts") or [])
    t = [float(x) for x in targets]
    if m.get("no_read") or len(got) != len(t):
        return None
    v = [abs(got[i]) for i in range(len(t)) if abs(t[i]) >= 1e-6]
    if len(v) < 2:
        return None
    return round(max(v) / max(1.0, min(v)), 3)


def magnitude_ratio_frac(m, targets, core=0.25, margin=0.55):
    got = magnitude_ratio(m, targets)
    if got is None:
        return 0.0
    t = [abs(float(x)) for x in targets if abs(float(x)) >= 1e-6]
    if len(t) < 2:
        return 0.0
    want = max(t) / min(t)
    return _bandfrac((got - want) / want, core, margin)


def beam_overlay(image, lo, hi, targets, out_path):
    m = measure_beam_tilts(image, lo, hi, len(targets))
    bgr = _load(image)
    if bgr is None:
        return {"no_read": True, "path": None}
    vis = bgr.copy()
    if not m.get("no_read"):
        for i, b in enumerate(m["bars"]):
            want = float(targets[i]) if i < len(targets) else None
            cv2.rectangle(vis, (b["x"], b["y"]), (b["x"] + b["w"], b["y"] + b["h"]),
                          (0, 200, 255), 2)
            import math
            th = math.radians(b["tilt_deg"])
            hx = 0.5 * b["w"] * math.cos(th)
            hy = 0.5 * b["w"] * math.sin(th)
            cv2.line(vis, (int(b["cx"] - hx), int(b["cy"] - hy)),
                     (int(b["cx"] + hx), int(b["cy"] + hy)), (60, 60, 235), 2)
            cv2.putText(vis, "%.1f/%s" % (b["tilt_deg"], "-" if want is None else "%.1f" % want),
                        (b["x"], max(14, b["y"] - 6)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)
        r = magnitude_ratio(m, targets)
        cv2.putText(vis, "range %s (want %.2f)" % (r, max(abs(float(x)) for x in targets) /
                                                   min([abs(float(x)) for x in targets
                                                        if abs(float(x)) >= 1e-6] or [1.0])),
                    (12, 26), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
    cv2.imwrite(str(out_path), vis)
    return {"no_read": bool(m.get("no_read")), "path": str(out_path)}


def draw_tilt_overlay(image, lo, hi, targets):
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
        beam_overlay(image, lo, hi, targets, os.path.join(d, "tilt_%s.png" % h))
    except Exception:
        pass
    return 1.0

# end of f_code_2

# code: beam_marks_code
import numpy as np
import cv2

cv2.setNumThreads(2)


def _load(image, cap=1500):
    a = cv2.imread(str(image), cv2.IMREAD_COLOR)
    if a is None:
        return None
    h, w = a.shape[:2]
    if max(h, w) > cap:
        s = cap / float(max(h, w))
        a = cv2.resize(a, (int(w * s), int(h * s)), interpolation=cv2.INTER_AREA)
    return a


def _clean(m, k=5):
    ker = np.ones((k, k), np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, ker)
    return cv2.morphologyEx(m, cv2.MORPH_OPEN, ker)


def _mask(bgr, lo, hi):
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    m = cv2.inRange(hsv, tuple(int(v) for v in lo), tuple(int(v) for v in hi))
    if float(lo[0]) <= 2 and float(hi[0]) <= 25:
        m |= cv2.inRange(hsv, (int(180 - hi[0]), int(lo[1]), int(lo[2])), (179, 255, 255))
    return _clean(m, 5)


def measure_beam_tilts(image, lo, hi, k):
    bgr = _load(image)
    if bgr is None:
        return {"no_read": True, "reason": "unreadable_file", "n_bars": 0, "tilts": []}
    H, W = bgr.shape[:2]
    m = _mask(bgr, lo, hi)
    n, lab, st, cen = cv2.connectedComponentsWithStats(m, 8)
    bars = []
    for i in range(1, n):
        x, y, w, h, a = st[i]
        if a < 0.0006 * m.size:
            continue
        if w < 1.8 * max(1, h) or not (0.055 * W < w < 0.93 * W) or h > 0.30 * H:
            continue
        if x <= 2 or x + w >= W - 2:
            continue
        bars.append({"i": int(i), "x": int(x), "y": int(y), "w": int(w), "h": int(h),
                     "cx": float(cen[i][0]), "cy": float(cen[i][1])})
    bars.sort(key=lambda z: -z["w"])
    keep = []
    for b in bars:
        dup = False
        for a2 in keep:
            ov = min(a2["x"] + a2["w"], b["x"] + b["w"]) - max(a2["x"], b["x"])
            if ov > 0.6 * b["w"] and abs(a2["cy"] - b["cy"]) < 0.06 * H:
                dup = True
                break
        if not dup:
            keep.append(b)
    if not keep:
        return {"no_read": True, "reason": "no_beam_layer", "n_bars": 0, "tilts": []}
    rows = []
    for b in keep:
        ys, xs = np.nonzero(lab == b["i"])
        vx, vy, x0, y0 = cv2.fitLine(np.stack([xs, ys], 1).astype(np.float32),
                                     cv2.DIST_L2, 0, 0.01, 0.01).ravel()
        ang = float(np.degrees(np.arctan2(vy, vx)))
        if ang > 90:
            ang -= 180
        if ang < -90:
            ang += 180
        rows.append({"x": b["x"], "w": b["w"], "cx": b["cx"], "cy": b["cy"],
                     "y": b["y"], "h": b["h"], "tilt_deg": round(ang, 2)})
    xs0 = [r["x"] for r in rows]
    stacked = (max(xs0) - min(xs0)) < 0.25 * W if len(rows) > 1 else True
    rows.sort(key=lambda r: (r["cy"], r["cx"]) if stacked else (r["cx"], r["cy"]))
    return {"no_read": False, "n_bars": len(rows), "bars": rows,
            "tilts": [r["tilt_deg"] for r in rows],
            "layout": "stacked" if stacked else "row", "k_expected": int(k), "H": H, "W": W}


def beams_readable_frac(m, k):
    if m.get("no_read"):
        return 0.0
    return 1.0 if int(m.get("n_bars") or 0) == int(k) else 0.0


def _bandfrac(err, core, margin):
    err = abs(float(err))
    if err <= core:
        return 1.0
    if err >= margin:
        return 0.0
    return round(1.0 - (err - core) / (margin - core), 4)


def per_beam_frac(m, targets, rel=0.20, floor_deg=2.0, ramp=2.0):
    if m.get("no_read"):
        return 0.0
    got = list(m.get("tilts") or [])
    t = [float(x) for x in targets]
    if len(got) != len(t):
        return 0.0
    per = []
    for g, ti in zip(got, t):
        core = max(float(floor_deg), float(rel) * abs(ti))
        per.append(_bandfrac(g - ti, core, ramp * core))
    return round(sum(per) / float(len(per)), 4)


def magnitude_ratio(m, targets):
    got = list(m.get("tilts") or [])
    t = [float(x) for x in targets]
    if m.get("no_read") or len(got) != len(t):
        return None
    v = [abs(got[i]) for i in range(len(t)) if abs(t[i]) >= 1e-6]
    if len(v) < 2:
        return None
    return round(max(v) / max(1.0, min(v)), 3)


def magnitude_ratio_frac(m, targets, core=0.25, margin=0.55):
    got = magnitude_ratio(m, targets)
    if got is None:
        return 0.0
    t = [abs(float(x)) for x in targets if abs(float(x)) >= 1e-6]
    if len(t) < 2:
        return 0.0
    want = max(t) / min(t)
    return _bandfrac((got - want) / want, core, margin)


def beam_overlay(image, lo, hi, targets, out_path):
    m = measure_beam_tilts(image, lo, hi, len(targets))
    bgr = _load(image)
    if bgr is None:
        return {"no_read": True, "path": None}
    vis = bgr.copy()
    if not m.get("no_read"):
        for i, b in enumerate(m["bars"]):
            want = float(targets[i]) if i < len(targets) else None
            cv2.rectangle(vis, (b["x"], b["y"]), (b["x"] + b["w"], b["y"] + b["h"]),
                          (0, 200, 255), 2)
            import math
            th = math.radians(b["tilt_deg"])
            hx = 0.5 * b["w"] * math.cos(th)
            hy = 0.5 * b["w"] * math.sin(th)
            cv2.line(vis, (int(b["cx"] - hx), int(b["cy"] - hy)),
                     (int(b["cx"] + hx), int(b["cy"] + hy)), (60, 60, 235), 2)
            cv2.putText(vis, "%.1f/%s" % (b["tilt_deg"], "-" if want is None else "%.1f" % want),
                        (b["x"], max(14, b["y"] - 6)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)
        r = magnitude_ratio(m, targets)
        cv2.putText(vis, "range %s (want %.2f)" % (r, max(abs(float(x)) for x in targets) /
                                                   min([abs(float(x)) for x in targets
                                                        if abs(float(x)) >= 1e-6] or [1.0])),
                    (12, 26), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
    cv2.imwrite(str(out_path), vis)
    return {"no_read": bool(m.get("no_read")), "path": str(out_path)}


def draw_tilt_overlay(image, lo, hi, targets):
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
        beam_overlay(image, lo, hi, targets, os.path.join(d, "tilt_%s.png" % h))
    except Exception:
        pass
    return 1.0

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


def beam_marks(image, lo, hi, targets):
    """Overlay marks for each measured beam line next to the line at its wanted tilt."""
    import math
    from PIL import Image as _I
    _mk_reset("measured", "want")
    im = image if hasattr(image, "size") else _I.open(str(image))
    W, H = float(im.size[0]), float(im.size[1])
    m = measure_beam_tilts(image, lo, hi, len(targets or []))
    if m.get("no_read"):
        return {"no_read": True, "n_marks": 0, "reason": m.get("reason")}
    for i, b in enumerate(m.get("bars") or []):
        th = math.radians(float(b["tilt_deg"]))
        hx, hy = 0.5 * b["w"] * math.cos(th), 0.5 * b["w"] * math.sin(th)
        _mk("measured", "polylines", [[b["cx"] - hx, b["cy"] - hy], [b["cx"] + hx, b["cy"] + hy]])
        _mk("measured", "rects", [b["x"] + b["w"] / 2.0, b["y"] + b["h"] / 2.0, b["w"], b["h"]])
        if i < len(targets or []):
            tw = math.radians(float(targets[i]))
            gx, gy = 0.55 * b["w"] * math.cos(tw), 0.55 * b["w"] * math.sin(tw)
            _mk("want", "polylines", [[b["cx"] - gx, b["cy"] - gy], [b["cx"] + gx, b["cy"] + gy]])
    _mk_scale(max(W, H) / float(max(m.get("W") or W, m.get("H") or H)))
    out = {"no_read": False, "n_bars": m.get("n_bars")}
    out.update(_ovmark_pack(im))
    return out

# end of beam_marks_code

# code: f_code_3
def tilt_range_score(reading, targets):
    """How closely the steepest to shallowest tilt ratio matches the target ratio."""
    return magnitude_ratio_frac(reading, targets)
import numpy as np
import cv2

cv2.setNumThreads(2)


def _load(image, cap=1500):
    a = cv2.imread(str(image), cv2.IMREAD_COLOR)
    if a is None:
        return None
    h, w = a.shape[:2]
    if max(h, w) > cap:
        s = cap / float(max(h, w))
        a = cv2.resize(a, (int(w * s), int(h * s)), interpolation=cv2.INTER_AREA)
    return a


def _clean(m, k=5):
    ker = np.ones((k, k), np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, ker)
    return cv2.morphologyEx(m, cv2.MORPH_OPEN, ker)


def _mask(bgr, lo, hi):
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    m = cv2.inRange(hsv, tuple(int(v) for v in lo), tuple(int(v) for v in hi))
    if float(lo[0]) <= 2 and float(hi[0]) <= 25:
        m |= cv2.inRange(hsv, (int(180 - hi[0]), int(lo[1]), int(lo[2])), (179, 255, 255))
    return _clean(m, 5)


def measure_beam_tilts(image, lo, hi, k):
    bgr = _load(image)
    if bgr is None:
        return {"no_read": True, "reason": "unreadable_file", "n_bars": 0, "tilts": []}
    H, W = bgr.shape[:2]
    m = _mask(bgr, lo, hi)
    n, lab, st, cen = cv2.connectedComponentsWithStats(m, 8)
    bars = []
    for i in range(1, n):
        x, y, w, h, a = st[i]
        if a < 0.0006 * m.size:
            continue
        if w < 1.8 * max(1, h) or not (0.055 * W < w < 0.93 * W) or h > 0.30 * H:
            continue
        if x <= 2 or x + w >= W - 2:
            continue
        bars.append({"i": int(i), "x": int(x), "y": int(y), "w": int(w), "h": int(h),
                     "cx": float(cen[i][0]), "cy": float(cen[i][1])})
    bars.sort(key=lambda z: -z["w"])
    keep = []
    for b in bars:
        dup = False
        for a2 in keep:
            ov = min(a2["x"] + a2["w"], b["x"] + b["w"]) - max(a2["x"], b["x"])
            if ov > 0.6 * b["w"] and abs(a2["cy"] - b["cy"]) < 0.06 * H:
                dup = True
                break
        if not dup:
            keep.append(b)
    if not keep:
        return {"no_read": True, "reason": "no_beam_layer", "n_bars": 0, "tilts": []}
    rows = []
    for b in keep:
        ys, xs = np.nonzero(lab == b["i"])
        vx, vy, x0, y0 = cv2.fitLine(np.stack([xs, ys], 1).astype(np.float32),
                                     cv2.DIST_L2, 0, 0.01, 0.01).ravel()
        ang = float(np.degrees(np.arctan2(vy, vx)))
        if ang > 90:
            ang -= 180
        if ang < -90:
            ang += 180
        rows.append({"x": b["x"], "w": b["w"], "cx": b["cx"], "cy": b["cy"],
                     "y": b["y"], "h": b["h"], "tilt_deg": round(ang, 2)})
    xs0 = [r["x"] for r in rows]
    stacked = (max(xs0) - min(xs0)) < 0.25 * W if len(rows) > 1 else True
    rows.sort(key=lambda r: (r["cy"], r["cx"]) if stacked else (r["cx"], r["cy"]))
    return {"no_read": False, "n_bars": len(rows), "bars": rows,
            "tilts": [r["tilt_deg"] for r in rows],
            "layout": "stacked" if stacked else "row", "k_expected": int(k), "H": H, "W": W}


def beams_readable_frac(m, k):
    if m.get("no_read"):
        return 0.0
    return 1.0 if int(m.get("n_bars") or 0) == int(k) else 0.0


def _bandfrac(err, core, margin):
    err = abs(float(err))
    if err <= core:
        return 1.0
    if err >= margin:
        return 0.0
    return round(1.0 - (err - core) / (margin - core), 4)


def per_beam_frac(m, targets, rel=0.20, floor_deg=2.0, ramp=2.0):
    if m.get("no_read"):
        return 0.0
    got = list(m.get("tilts") or [])
    t = [float(x) for x in targets]
    if len(got) != len(t):
        return 0.0
    per = []
    for g, ti in zip(got, t):
        core = max(float(floor_deg), float(rel) * abs(ti))
        per.append(_bandfrac(g - ti, core, ramp * core))
    return round(sum(per) / float(len(per)), 4)


def magnitude_ratio(m, targets):
    got = list(m.get("tilts") or [])
    t = [float(x) for x in targets]
    if m.get("no_read") or len(got) != len(t):
        return None
    v = [abs(got[i]) for i in range(len(t)) if abs(t[i]) >= 1e-6]
    if len(v) < 2:
        return None
    return round(max(v) / max(1.0, min(v)), 3)


def magnitude_ratio_frac(m, targets, core=0.25, margin=0.55):
    got = magnitude_ratio(m, targets)
    if got is None:
        return 0.0
    t = [abs(float(x)) for x in targets if abs(float(x)) >= 1e-6]
    if len(t) < 2:
        return 0.0
    want = max(t) / min(t)
    return _bandfrac((got - want) / want, core, margin)


def beam_overlay(image, lo, hi, targets, out_path):
    m = measure_beam_tilts(image, lo, hi, len(targets))
    bgr = _load(image)
    if bgr is None:
        return {"no_read": True, "path": None}
    vis = bgr.copy()
    if not m.get("no_read"):
        for i, b in enumerate(m["bars"]):
            want = float(targets[i]) if i < len(targets) else None
            cv2.rectangle(vis, (b["x"], b["y"]), (b["x"] + b["w"], b["y"] + b["h"]),
                          (0, 200, 255), 2)
            import math
            th = math.radians(b["tilt_deg"])
            hx = 0.5 * b["w"] * math.cos(th)
            hy = 0.5 * b["w"] * math.sin(th)
            cv2.line(vis, (int(b["cx"] - hx), int(b["cy"] - hy)),
                     (int(b["cx"] + hx), int(b["cy"] + hy)), (60, 60, 235), 2)
            cv2.putText(vis, "%.1f/%s" % (b["tilt_deg"], "-" if want is None else "%.1f" % want),
                        (b["x"], max(14, b["y"] - 6)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)
        r = magnitude_ratio(m, targets)
        cv2.putText(vis, "range %s (want %.2f)" % (r, max(abs(float(x)) for x in targets) /
                                                   min([abs(float(x)) for x in targets
                                                        if abs(float(x)) >= 1e-6] or [1.0])),
                    (12, 26), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
    cv2.imwrite(str(out_path), vis)
    return {"no_read": bool(m.get("no_read")), "path": str(out_path)}


def draw_tilt_overlay(image, lo, hi, targets):
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
        beam_overlay(image, lo, hi, targets, os.path.join(d, "tilt_%s.png" % h))
    except Exception:
        pass
    return 1.0

# end of f_code_3
