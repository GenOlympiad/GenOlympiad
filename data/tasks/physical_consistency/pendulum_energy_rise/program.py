# shared code: code_239530c69260
def score_colour_order(measured, c):
    """The share of pendulum colours that sit in the expected left-to-right order."""
    return colour_order_frac(measured, c)
import math

import numpy as np
import cv2

cv2.setNumThreads(2)

_HUE = {"red": [(0, 8), (168, 180)], "orange": [(9, 22)], "yellow": [(23, 36)],
        "green": [(38, 85)], "cyan": [(86, 100)], "blue": [(101, 130)],
        "purple": [(131, 158)], "magenta": [(159, 172)]}


def _load(image, cap=1500):
    a = cv2.imread(str(image), cv2.IMREAD_COLOR)
    if a is None:
        return None
    h, w = a.shape[:2]
    if max(h, w) > cap:
        s = cap / float(max(h, w))
        a = cv2.resize(a, (int(w * s), int(h * s)), interpolation=cv2.INTER_AREA)
    return a


def _band(v, t, core, margin):
    if v is None or t is None:
        return 0.0
    d = abs(float(v) - float(t))
    return round(min(1.0, max(0.0, 1.0 - max(0.0, d - float(core)) / max(float(margin), 1e-9))), 4)


def _logband(got, target, core_ratio=1.25, margin_ratio=1.40):
    if not got or not target or got <= 0 or target <= 0:
        return 0.0
    d = abs(math.log(float(got) / float(target)))
    core = math.log(float(core_ratio))
    margin = math.log(float(margin_ratio)) - core
    return round(min(1.0, max(0.0, 1.0 - max(0.0, d - core) / max(margin, 1e-9))), 4)


def _colour_mask(bgr, hsv, name, smin=80, vmin=40):
    m = np.zeros(hsv.shape[:2], np.uint8)
    for lo, hi in _HUE[str(name)]:
        m |= cv2.inRange(hsv, (int(lo), smin, vmin), (int(min(hi, 179)), 255, 255))
    k = np.ones((3, 3), np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, k)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, k)
    n, lab, st, _ = cv2.connectedComponentsWithStats(m, 8)
    keep = np.zeros_like(m)
    floor = max(50.0, 0.00018 * m.size)
    for i in range(1, n):
        if st[i, cv2.CC_STAT_AREA] >= floor:
            keep[lab == i] = 255
    return keep


def _pivot(mask):
    import numpy as _np
    mu = mask.copy()
    dt = cv2.distanceTransform(mu, cv2.DIST_L2, 5)
    mx = float(dt.max())
    cordm = None
    if mx >= 4.0:
        thr = 0.55 * mx
        core = (dt > thr).astype(_np.uint8) * 255
        if core.any():
            rad = max(3, int(round(thr)) + 2)
            ker = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * rad + 1, 2 * rad + 1))
            grown = cv2.dilate(core, ker)
            cand = cv2.bitwise_and(mu, cv2.bitwise_not(grown))
            if int((cand > 0).sum()) >= 60:
                cordm = cand
    src = cordm if cordm is not None else mu
    ys, xs = _np.nonzero(src)
    if ys.size < 10:
        ys, xs = _np.nonzero(mu)
    ys = ys.astype(_np.float64)
    xs = xs.astype(_np.float64)
    y0 = float(_np.percentile(ys, 0.4))
    band = ys <= y0 + max(5.0, 0.008 * mask.shape[0])
    if int(band.sum()) < 5:
        band = ys <= y0 + 12.0
    return float(_np.mean(xs[band])), y0, cordm


def _lobes(xs, ys, px, py, d, rmax):
    sel = (d >= 0.35 * rmax) & (d <= 0.90 * rmax)
    if int(sel.sum()) < 40:
        return 0
    ang = np.degrees(np.arctan2(xs[sel] - px, np.maximum(ys[sel] - py, 0.0) + 1e-6))
    hist, _ = np.histogram(ang, bins=np.arange(-100.0, 100.1, 2.0))
    if hist.max() <= 0:
        return 0
    live = hist >= max(3.0, 0.10 * float(hist.max()))
    runs, i, n = [], 0, live.size
    while i < n:
        if not live[i]:
            i += 1
            continue
        j = i
        while j + 1 < n and (live[j + 1] or (j + 2 < n and live[j + 2])):
            j += 1
        runs.append((i, j))
        i = j + 1
    total = float(hist.sum())
    return int(sum(1 for a, b in runs if float(hist[a:b + 1].sum()) >= 0.06 * total))


def pendulum_read(image, colours):
    bgr = _load(image)
    if bgr is None:
        return {"no_read": True, "reason": "unreadable_file"}
    H, W = bgr.shape[:2]
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    per = []
    for c in colours:
        m = _colour_mask(bgr, hsv, c)
        ys, xs = np.nonzero(m)
        if ys.size < 150:
            per.append(None)
            continue
        ys = ys.astype(np.float64)
        xs = xs.astype(np.float64)
        px, py, _cordm = _pivot(m)
        d = np.hypot(xs - px, ys - py)
        rmax = float(d.max())
        if rmax < 0.04 * H:
            per.append(None)
            continue
        arms = {}
        for sgn in (-1, 1):
            sel = (xs - px) * sgn > 0.006 * W
            if int(sel.sum()) < 25:
                continue
            i = int(np.argmax(np.where(sel, d, -1.0)))
            L, drop = float(d[i]), float(ys[i] - py)
            if L < 0.03 * H:
                continue
            arms[sgn] = {"L": round(L, 1), "drop": round(drop, 1),
                         "r": round(max(0.0, min(2.0, (L - drop) / L)), 4),
                         "tip": [int(xs[i]), int(ys[i])]}
        if not arms:
            per.append(None)
            continue
        rs = [a["r"] for a in arms.values()]
        per.append({"colour": str(c), "pivot": [round(px, 1), round(py, 1)],
                    "arms": [arms.get(-1), arms.get(1)],
                    "cord_px": round(float(np.mean([a["L"] for a in arms.values()])), 1),
                    "rise_over_L": round(float(np.mean(rs)), 4),
                    "one_sided": len(arms) < 2,
                    "exposures": _lobes(xs, ys, px, py, d, rmax)})
    got = [(p["pivot"][0], p["colour"]) for p in per if p]
    got.sort()
    return {"no_read": False, "H": H, "W": W, "per": per,
            "colours": [str(c) for c in colours],
            "rise_over_L": [(p["rise_over_L"] if p else None) for p in per],
            "cord_px": [(p["cord_px"] if p else None) for p in per],
            "exposures": [(p["exposures"] if p else 0) for p in per],
            "n_found": sum(1 for p in per if p),
            "order": [c for _x, c in got]}


def pendulums_readable_frac(m, k):
    if m.get("no_read"):
        return 0.0
    ok = sum(1 for p in (m.get("per") or []) if p and p.get("rise_over_L") is not None)
    return 1.0 if ok >= max(2, int(k) - 1) else 0.0


def exposures_frac(m, k):
    if m.get("no_read"):
        return 0.0
    e = m.get("exposures") or []
    return round(sum(1 for x in e if int(x) == 2) / float(max(1, int(k))), 4)


def colour_order_frac(m, expected):
    if m.get("no_read"):
        return 0.0
    got = m.get("order") or []
    exp = [str(x) for x in expected]
    if not got:
        return 0.0
    hit = sum(1 for i, c in enumerate(exp) if i < len(got) and got[i] == c)
    return round(hit / float(len(exp)), 4)


def rise_ratio_frac(m, targets):
    if m.get("no_read"):
        return 0.0
    vals = m.get("rise_over_L") or []
    fr = []
    for i, t in enumerate(targets):
        v = vals[i] if i < len(vals) else None
        fr.append(_band(v, float(t), 0.012 + 0.10 * float(t), 0.016 + 0.12 * float(t)))
    return round(sum(fr) / float(max(1, len(targets))), 4)


def rise_spread_frac(m, target):
    if m.get("no_read"):
        return 0.0
    vals = [v for v in (m.get("rise_over_L") or []) if v]
    if len(vals) < 2 or min(vals) <= 0:
        return 0.0
    return _logband(max(vals) / min(vals), float(target), 1.25, 1.45)


def cord_copy_frac(m, cord_units):
    if m.get("no_read"):
        return 0.0
    got = [v for v in (m.get("cord_px") or [])]
    if any(v is None for v in got) or not got:
        return 0.0
    gm, tm = max(got), max(float(x) for x in cord_units)
    fr = [_band(g / gm, float(t) / tm, 0.12 * (float(t) / tm) + 0.02,
                0.12 * (float(t) / tm) + 0.02) for g, t in zip(got, cord_units)]
    return round(sum(fr) / float(len(fr)), 4)


def pendulum_overlay(image, colours, targets, out_path):
    m = pendulum_read(image, colours)
    bgr = _load(image)
    if bgr is None:
        return {"no_read": True, "path": None}
    vis = bgr.copy()
    if not m.get("no_read"):
        for p, t in zip(m["per"], list(targets) + [None] * 8):
            if not p:
                continue
            px, py = int(p["pivot"][0]), int(p["pivot"][1])
            cv2.circle(vis, (px, py), 5, (0, 220, 255), -1)
            for a in p["arms"]:
                if not a:
                    continue
                cv2.line(vis, (px, py), tuple(a["tip"]), (0, 220, 255), 2)
                if t:
                    yy = int(py + a["L"] * (1.0 - float(t)))
                    xx = int(a["tip"][0])
                    cv2.line(vis, (xx - 16, yy), (xx + 16, yy), (255, 90, 90), 3)
            cv2.putText(vis, "%.3f" % p["rise_over_L"], (px - 30, max(16, py - 8)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 0), 2)
        sp = [v for v in m["rise_over_L"] if v]
        if len(sp) >= 2 and min(sp) > 0:
            cv2.putText(vis, "spread max/min = %.2f  order=%s"
                        % (max(sp) / min(sp), ",".join(m["order"])), (10, 24),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
    cv2.imwrite(str(out_path), vis)
    return {"no_read": bool(m.get("no_read")), "path": str(out_path)}


def draw_pendulum_overlay(image, colours, targets):
    import hashlib
    import os as _os
    import tempfile
    d = _os.path.join(tempfile.gettempdir(), "genolympiad_overlay")
    try:
        _os.makedirs(d, exist_ok=True)
    except Exception:
        pass
    h = hashlib.md5(str(image).encode("utf-8", "replace")).hexdigest()[:12]
    try:
        pendulum_overlay(image, colours, targets, _os.path.join(d, "pend_%s.png" % h))
    except Exception:
        pass
    return 1.0

# end of code_239530c69260

# shared code: code_8c8bb5a078ce
def score_rise_spread(measured, s):
    """Score how closely the highest-to-lowest rise ratio matches the target spread."""
    return rise_spread_frac(measured, s)
import math

import numpy as np
import cv2

cv2.setNumThreads(2)

_HUE = {"red": [(0, 8), (168, 180)], "orange": [(9, 22)], "yellow": [(23, 36)],
        "green": [(38, 85)], "cyan": [(86, 100)], "blue": [(101, 130)],
        "purple": [(131, 158)], "magenta": [(159, 172)]}


def _load(image, cap=1500):
    a = cv2.imread(str(image), cv2.IMREAD_COLOR)
    if a is None:
        return None
    h, w = a.shape[:2]
    if max(h, w) > cap:
        s = cap / float(max(h, w))
        a = cv2.resize(a, (int(w * s), int(h * s)), interpolation=cv2.INTER_AREA)
    return a


def _band(v, t, core, margin):
    if v is None or t is None:
        return 0.0
    d = abs(float(v) - float(t))
    return round(min(1.0, max(0.0, 1.0 - max(0.0, d - float(core)) / max(float(margin), 1e-9))), 4)


def _logband(got, target, core_ratio=1.25, margin_ratio=1.40):
    if not got or not target or got <= 0 or target <= 0:
        return 0.0
    d = abs(math.log(float(got) / float(target)))
    core = math.log(float(core_ratio))
    margin = math.log(float(margin_ratio)) - core
    return round(min(1.0, max(0.0, 1.0 - max(0.0, d - core) / max(margin, 1e-9))), 4)


def _colour_mask(bgr, hsv, name, smin=80, vmin=40):
    m = np.zeros(hsv.shape[:2], np.uint8)
    for lo, hi in _HUE[str(name)]:
        m |= cv2.inRange(hsv, (int(lo), smin, vmin), (int(min(hi, 179)), 255, 255))
    k = np.ones((3, 3), np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, k)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, k)
    n, lab, st, _ = cv2.connectedComponentsWithStats(m, 8)
    keep = np.zeros_like(m)
    floor = max(50.0, 0.00018 * m.size)
    for i in range(1, n):
        if st[i, cv2.CC_STAT_AREA] >= floor:
            keep[lab == i] = 255
    return keep


def _pivot(mask):
    import numpy as _np
    mu = mask.copy()
    dt = cv2.distanceTransform(mu, cv2.DIST_L2, 5)
    mx = float(dt.max())
    cordm = None
    if mx >= 4.0:
        thr = 0.55 * mx
        core = (dt > thr).astype(_np.uint8) * 255
        if core.any():
            rad = max(3, int(round(thr)) + 2)
            ker = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * rad + 1, 2 * rad + 1))
            grown = cv2.dilate(core, ker)
            cand = cv2.bitwise_and(mu, cv2.bitwise_not(grown))
            if int((cand > 0).sum()) >= 60:
                cordm = cand
    src = cordm if cordm is not None else mu
    ys, xs = _np.nonzero(src)
    if ys.size < 10:
        ys, xs = _np.nonzero(mu)
    ys = ys.astype(_np.float64)
    xs = xs.astype(_np.float64)
    y0 = float(_np.percentile(ys, 0.4))
    band = ys <= y0 + max(5.0, 0.008 * mask.shape[0])
    if int(band.sum()) < 5:
        band = ys <= y0 + 12.0
    return float(_np.mean(xs[band])), y0, cordm


def _lobes(xs, ys, px, py, d, rmax):
    sel = (d >= 0.35 * rmax) & (d <= 0.90 * rmax)
    if int(sel.sum()) < 40:
        return 0
    ang = np.degrees(np.arctan2(xs[sel] - px, np.maximum(ys[sel] - py, 0.0) + 1e-6))
    hist, _ = np.histogram(ang, bins=np.arange(-100.0, 100.1, 2.0))
    if hist.max() <= 0:
        return 0
    live = hist >= max(3.0, 0.10 * float(hist.max()))
    runs, i, n = [], 0, live.size
    while i < n:
        if not live[i]:
            i += 1
            continue
        j = i
        while j + 1 < n and (live[j + 1] or (j + 2 < n and live[j + 2])):
            j += 1
        runs.append((i, j))
        i = j + 1
    total = float(hist.sum())
    return int(sum(1 for a, b in runs if float(hist[a:b + 1].sum()) >= 0.06 * total))


def pendulum_read(image, colours):
    bgr = _load(image)
    if bgr is None:
        return {"no_read": True, "reason": "unreadable_file"}
    H, W = bgr.shape[:2]
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    per = []
    for c in colours:
        m = _colour_mask(bgr, hsv, c)
        ys, xs = np.nonzero(m)
        if ys.size < 150:
            per.append(None)
            continue
        ys = ys.astype(np.float64)
        xs = xs.astype(np.float64)
        px, py, _cordm = _pivot(m)
        d = np.hypot(xs - px, ys - py)
        rmax = float(d.max())
        if rmax < 0.04 * H:
            per.append(None)
            continue
        arms = {}
        for sgn in (-1, 1):
            sel = (xs - px) * sgn > 0.006 * W
            if int(sel.sum()) < 25:
                continue
            i = int(np.argmax(np.where(sel, d, -1.0)))
            L, drop = float(d[i]), float(ys[i] - py)
            if L < 0.03 * H:
                continue
            arms[sgn] = {"L": round(L, 1), "drop": round(drop, 1),
                         "r": round(max(0.0, min(2.0, (L - drop) / L)), 4),
                         "tip": [int(xs[i]), int(ys[i])]}
        if not arms:
            per.append(None)
            continue
        rs = [a["r"] for a in arms.values()]
        per.append({"colour": str(c), "pivot": [round(px, 1), round(py, 1)],
                    "arms": [arms.get(-1), arms.get(1)],
                    "cord_px": round(float(np.mean([a["L"] for a in arms.values()])), 1),
                    "rise_over_L": round(float(np.mean(rs)), 4),
                    "one_sided": len(arms) < 2,
                    "exposures": _lobes(xs, ys, px, py, d, rmax)})
    got = [(p["pivot"][0], p["colour"]) for p in per if p]
    got.sort()
    return {"no_read": False, "H": H, "W": W, "per": per,
            "colours": [str(c) for c in colours],
            "rise_over_L": [(p["rise_over_L"] if p else None) for p in per],
            "cord_px": [(p["cord_px"] if p else None) for p in per],
            "exposures": [(p["exposures"] if p else 0) for p in per],
            "n_found": sum(1 for p in per if p),
            "order": [c for _x, c in got]}


def pendulums_readable_frac(m, k):
    if m.get("no_read"):
        return 0.0
    ok = sum(1 for p in (m.get("per") or []) if p and p.get("rise_over_L") is not None)
    return 1.0 if ok >= max(2, int(k) - 1) else 0.0


def exposures_frac(m, k):
    if m.get("no_read"):
        return 0.0
    e = m.get("exposures") or []
    return round(sum(1 for x in e if int(x) == 2) / float(max(1, int(k))), 4)


def colour_order_frac(m, expected):
    if m.get("no_read"):
        return 0.0
    got = m.get("order") or []
    exp = [str(x) for x in expected]
    if not got:
        return 0.0
    hit = sum(1 for i, c in enumerate(exp) if i < len(got) and got[i] == c)
    return round(hit / float(len(exp)), 4)


def rise_ratio_frac(m, targets):
    if m.get("no_read"):
        return 0.0
    vals = m.get("rise_over_L") or []
    fr = []
    for i, t in enumerate(targets):
        v = vals[i] if i < len(vals) else None
        fr.append(_band(v, float(t), 0.012 + 0.10 * float(t), 0.016 + 0.12 * float(t)))
    return round(sum(fr) / float(max(1, len(targets))), 4)


def rise_spread_frac(m, target):
    if m.get("no_read"):
        return 0.0
    vals = [v for v in (m.get("rise_over_L") or []) if v]
    if len(vals) < 2 or min(vals) <= 0:
        return 0.0
    return _logband(max(vals) / min(vals), float(target), 1.25, 1.45)


def cord_copy_frac(m, cord_units):
    if m.get("no_read"):
        return 0.0
    got = [v for v in (m.get("cord_px") or [])]
    if any(v is None for v in got) or not got:
        return 0.0
    gm, tm = max(got), max(float(x) for x in cord_units)
    fr = [_band(g / gm, float(t) / tm, 0.12 * (float(t) / tm) + 0.02,
                0.12 * (float(t) / tm) + 0.02) for g, t in zip(got, cord_units)]
    return round(sum(fr) / float(len(fr)), 4)


def pendulum_overlay(image, colours, targets, out_path):
    m = pendulum_read(image, colours)
    bgr = _load(image)
    if bgr is None:
        return {"no_read": True, "path": None}
    vis = bgr.copy()
    if not m.get("no_read"):
        for p, t in zip(m["per"], list(targets) + [None] * 8):
            if not p:
                continue
            px, py = int(p["pivot"][0]), int(p["pivot"][1])
            cv2.circle(vis, (px, py), 5, (0, 220, 255), -1)
            for a in p["arms"]:
                if not a:
                    continue
                cv2.line(vis, (px, py), tuple(a["tip"]), (0, 220, 255), 2)
                if t:
                    yy = int(py + a["L"] * (1.0 - float(t)))
                    xx = int(a["tip"][0])
                    cv2.line(vis, (xx - 16, yy), (xx + 16, yy), (255, 90, 90), 3)
            cv2.putText(vis, "%.3f" % p["rise_over_L"], (px - 30, max(16, py - 8)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 0), 2)
        sp = [v for v in m["rise_over_L"] if v]
        if len(sp) >= 2 and min(sp) > 0:
            cv2.putText(vis, "spread max/min = %.2f  order=%s"
                        % (max(sp) / min(sp), ",".join(m["order"])), (10, 24),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
    cv2.imwrite(str(out_path), vis)
    return {"no_read": bool(m.get("no_read")), "path": str(out_path)}


def draw_pendulum_overlay(image, colours, targets):
    import hashlib
    import os as _os
    import tempfile
    d = _os.path.join(tempfile.gettempdir(), "genolympiad_overlay")
    try:
        _os.makedirs(d, exist_ok=True)
    except Exception:
        pass
    h = hashlib.md5(str(image).encode("utf-8", "replace")).hexdigest()[:12]
    try:
        pendulum_overlay(image, colours, targets, _os.path.join(d, "pend_%s.png" % h))
    except Exception:
        pass
    return 1.0

# end of code_8c8bb5a078ce

# shared code: code_cc598a02e032
import math

import numpy as np
import cv2

cv2.setNumThreads(2)

_HUE = {"red": [(0, 8), (168, 180)], "orange": [(9, 22)], "yellow": [(23, 36)],
        "green": [(38, 85)], "cyan": [(86, 100)], "blue": [(101, 130)],
        "purple": [(131, 158)], "magenta": [(159, 172)]}


def _load(image, cap=1500):
    a = cv2.imread(str(image), cv2.IMREAD_COLOR)
    if a is None:
        return None
    h, w = a.shape[:2]
    if max(h, w) > cap:
        s = cap / float(max(h, w))
        a = cv2.resize(a, (int(w * s), int(h * s)), interpolation=cv2.INTER_AREA)
    return a


def _band(v, t, core, margin):
    if v is None or t is None:
        return 0.0
    d = abs(float(v) - float(t))
    return round(min(1.0, max(0.0, 1.0 - max(0.0, d - float(core)) / max(float(margin), 1e-9))), 4)


def _logband(got, target, core_ratio=1.25, margin_ratio=1.40):
    if not got or not target or got <= 0 or target <= 0:
        return 0.0
    d = abs(math.log(float(got) / float(target)))
    core = math.log(float(core_ratio))
    margin = math.log(float(margin_ratio)) - core
    return round(min(1.0, max(0.0, 1.0 - max(0.0, d - core) / max(margin, 1e-9))), 4)


def _colour_mask(bgr, hsv, name, smin=80, vmin=40):
    m = np.zeros(hsv.shape[:2], np.uint8)
    for lo, hi in _HUE[str(name)]:
        m |= cv2.inRange(hsv, (int(lo), smin, vmin), (int(min(hi, 179)), 255, 255))
    k = np.ones((3, 3), np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, k)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, k)
    n, lab, st, _ = cv2.connectedComponentsWithStats(m, 8)
    keep = np.zeros_like(m)
    floor = max(50.0, 0.00018 * m.size)
    for i in range(1, n):
        if st[i, cv2.CC_STAT_AREA] >= floor:
            keep[lab == i] = 255
    return keep


def _pivot(mask):
    import numpy as _np
    mu = mask.copy()
    dt = cv2.distanceTransform(mu, cv2.DIST_L2, 5)
    mx = float(dt.max())
    cordm = None
    if mx >= 4.0:
        thr = 0.55 * mx
        core = (dt > thr).astype(_np.uint8) * 255
        if core.any():
            rad = max(3, int(round(thr)) + 2)
            ker = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * rad + 1, 2 * rad + 1))
            grown = cv2.dilate(core, ker)
            cand = cv2.bitwise_and(mu, cv2.bitwise_not(grown))
            if int((cand > 0).sum()) >= 60:
                cordm = cand
    src = cordm if cordm is not None else mu
    ys, xs = _np.nonzero(src)
    if ys.size < 10:
        ys, xs = _np.nonzero(mu)
    ys = ys.astype(_np.float64)
    xs = xs.astype(_np.float64)
    y0 = float(_np.percentile(ys, 0.4))
    band = ys <= y0 + max(5.0, 0.008 * mask.shape[0])
    if int(band.sum()) < 5:
        band = ys <= y0 + 12.0
    return float(_np.mean(xs[band])), y0, cordm


def _lobes(xs, ys, px, py, d, rmax):
    sel = (d >= 0.35 * rmax) & (d <= 0.90 * rmax)
    if int(sel.sum()) < 40:
        return 0
    ang = np.degrees(np.arctan2(xs[sel] - px, np.maximum(ys[sel] - py, 0.0) + 1e-6))
    hist, _ = np.histogram(ang, bins=np.arange(-100.0, 100.1, 2.0))
    if hist.max() <= 0:
        return 0
    live = hist >= max(3.0, 0.10 * float(hist.max()))
    runs, i, n = [], 0, live.size
    while i < n:
        if not live[i]:
            i += 1
            continue
        j = i
        while j + 1 < n and (live[j + 1] or (j + 2 < n and live[j + 2])):
            j += 1
        runs.append((i, j))
        i = j + 1
    total = float(hist.sum())
    return int(sum(1 for a, b in runs if float(hist[a:b + 1].sum()) >= 0.06 * total))


def pendulum_read(image, colours):
    """Measure each coloured pendulum's pivot, cord length, rise and exposures from the image."""
    bgr = _load(image)
    if bgr is None:
        return {"no_read": True, "reason": "unreadable_file"}
    H, W = bgr.shape[:2]
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    per_colour = []
    for c in colours:
        m = _colour_mask(bgr, hsv, c)
        ys, xs = np.nonzero(m)
        if ys.size < 150:
            per_colour.append(None)
            continue
        ys = ys.astype(np.float64)
        xs = xs.astype(np.float64)
        px, py, _cordm = _pivot(m)
        d = np.hypot(xs - px, ys - py)
        rmax = float(d.max())
        if rmax < 0.04 * H:
            per_colour.append(None)
            continue
        arms = {}
        for sgn in (-1, 1):
            sel = (xs - px) * sgn > 0.006 * W
            if int(sel.sum()) < 25:
                continue
            i = int(np.argmax(np.where(sel, d, -1.0)))
            L, drop = float(d[i]), float(ys[i] - py)
            if L < 0.03 * H:
                continue
            arms[sgn] = {"L": round(L, 1), "drop": round(drop, 1),
                         "r": round(max(0.0, min(2.0, (L - drop) / L)), 4),
                         "tip": [int(xs[i]), int(ys[i])]}
        if not arms:
            per_colour.append(None)
            continue
        rises = [a["r"] for a in arms.values()]
        per_colour.append({"colour": str(c), "pivot": [round(px, 1), round(py, 1)],
                    "arms": [arms.get(-1), arms.get(1)],
                    "cord_px": round(float(np.mean([a["L"] for a in arms.values()])), 1),
                    "rise_over_L": round(float(np.mean(rises)), 4),
                    "one_sided": len(arms) < 2,
                    "exposures": _lobes(xs, ys, px, py, d, rmax)})
    pivots_by_x = [(p["pivot"][0], p["colour"]) for p in per_colour if p]
    pivots_by_x.sort()
    return {"no_read": False, "H": H, "W": W, "per": per_colour,
            "colours": [str(c) for c in colours],
            "rise_over_L": [(p["rise_over_L"] if p else None) for p in per_colour],
            "cord_px": [(p["cord_px"] if p else None) for p in per_colour],
            "exposures": [(p["exposures"] if p else 0) for p in per_colour],
            "n_found": sum(1 for p in per_colour if p),
            "order": [c for _x, c in pivots_by_x]}


def pendulums_readable_frac(m, k):
    if m.get("no_read"):
        return 0.0
    ok = sum(1 for p in (m.get("per") or []) if p and p.get("rise_over_L") is not None)
    return 1.0 if ok >= max(2, int(k) - 1) else 0.0


def exposures_frac(m, k):
    if m.get("no_read"):
        return 0.0
    e = m.get("exposures") or []
    return round(sum(1 for x in e if int(x) == 2) / float(max(1, int(k))), 4)


def colour_order_frac(m, expected):
    if m.get("no_read"):
        return 0.0
    got = m.get("order") or []
    exp = [str(x) for x in expected]
    if not got:
        return 0.0
    hit = sum(1 for i, c in enumerate(exp) if i < len(got) and got[i] == c)
    return round(hit / float(len(exp)), 4)


def rise_ratio_frac(m, targets):
    if m.get("no_read"):
        return 0.0
    vals = m.get("rise_over_L") or []
    fr = []
    for i, t in enumerate(targets):
        v = vals[i] if i < len(vals) else None
        fr.append(_band(v, float(t), 0.012 + 0.10 * float(t), 0.016 + 0.12 * float(t)))
    return round(sum(fr) / float(max(1, len(targets))), 4)


def rise_spread_frac(m, target):
    if m.get("no_read"):
        return 0.0
    vals = [v for v in (m.get("rise_over_L") or []) if v]
    if len(vals) < 2 or min(vals) <= 0:
        return 0.0
    return _logband(max(vals) / min(vals), float(target), 1.25, 1.45)


def cord_copy_frac(m, cord_units):
    if m.get("no_read"):
        return 0.0
    got = [v for v in (m.get("cord_px") or [])]
    if any(v is None for v in got) or not got:
        return 0.0
    gm, tm = max(got), max(float(x) for x in cord_units)
    fr = [_band(g / gm, float(t) / tm, 0.12 * (float(t) / tm) + 0.02,
                0.12 * (float(t) / tm) + 0.02) for g, t in zip(got, cord_units)]
    return round(sum(fr) / float(len(fr)), 4)


def pendulum_overlay(image, colours, targets, out_path):
    m = pendulum_read(image, colours)
    bgr = _load(image)
    if bgr is None:
        return {"no_read": True, "path": None}
    vis = bgr.copy()
    if not m.get("no_read"):
        for p, t in zip(m["per"], list(targets) + [None] * 8):
            if not p:
                continue
            px, py = int(p["pivot"][0]), int(p["pivot"][1])
            cv2.circle(vis, (px, py), 5, (0, 220, 255), -1)
            for a in p["arms"]:
                if not a:
                    continue
                cv2.line(vis, (px, py), tuple(a["tip"]), (0, 220, 255), 2)
                if t:
                    yy = int(py + a["L"] * (1.0 - float(t)))
                    xx = int(a["tip"][0])
                    cv2.line(vis, (xx - 16, yy), (xx + 16, yy), (255, 90, 90), 3)
            cv2.putText(vis, "%.3f" % p["rise_over_L"], (px - 30, max(16, py - 8)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 0), 2)
        sp = [v for v in m["rise_over_L"] if v]
        if len(sp) >= 2 and min(sp) > 0:
            cv2.putText(vis, "spread max/min = %.2f  order=%s"
                        % (max(sp) / min(sp), ",".join(m["order"])), (10, 24),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
    cv2.imwrite(str(out_path), vis)
    return {"no_read": bool(m.get("no_read")), "path": str(out_path)}


def draw_pendulum_overlay(image, colours, targets):
    """Save a drawing of the measured pendulums to a temporary file and return 1."""
    import hashlib
    import os as _os
    import tempfile
    overlay_dir = _os.path.join(tempfile.gettempdir(), "genolympiad_overlay")
    try:
        _os.makedirs(overlay_dir, exist_ok=True)
    except Exception:
        pass
    name_hash = hashlib.md5(str(image).encode("utf-8", "replace")).hexdigest()[:12]
    try:
        pendulum_overlay(image, colours, targets, _os.path.join(overlay_dir, "pend_%s.png" % name_hash))
    except Exception:
        pass
    return 1.0

# end of code_cc598a02e032

# shared code: code_ecc4f194366a
def score_readable(measured, k):
    """Score 1 when the rise of all but at most one pendulum could be measured."""
    return pendulums_readable_frac(measured, k)
import math

import numpy as np
import cv2

cv2.setNumThreads(2)

_HUE = {"red": [(0, 8), (168, 180)], "orange": [(9, 22)], "yellow": [(23, 36)],
        "green": [(38, 85)], "cyan": [(86, 100)], "blue": [(101, 130)],
        "purple": [(131, 158)], "magenta": [(159, 172)]}


def _load(image, cap=1500):
    a = cv2.imread(str(image), cv2.IMREAD_COLOR)
    if a is None:
        return None
    h, w = a.shape[:2]
    if max(h, w) > cap:
        s = cap / float(max(h, w))
        a = cv2.resize(a, (int(w * s), int(h * s)), interpolation=cv2.INTER_AREA)
    return a


def _band(v, t, core, margin):
    if v is None or t is None:
        return 0.0
    d = abs(float(v) - float(t))
    return round(min(1.0, max(0.0, 1.0 - max(0.0, d - float(core)) / max(float(margin), 1e-9))), 4)


def _logband(got, target, core_ratio=1.25, margin_ratio=1.40):
    if not got or not target or got <= 0 or target <= 0:
        return 0.0
    d = abs(math.log(float(got) / float(target)))
    core = math.log(float(core_ratio))
    margin = math.log(float(margin_ratio)) - core
    return round(min(1.0, max(0.0, 1.0 - max(0.0, d - core) / max(margin, 1e-9))), 4)


def _colour_mask(bgr, hsv, name, smin=80, vmin=40):
    m = np.zeros(hsv.shape[:2], np.uint8)
    for lo, hi in _HUE[str(name)]:
        m |= cv2.inRange(hsv, (int(lo), smin, vmin), (int(min(hi, 179)), 255, 255))
    k = np.ones((3, 3), np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, k)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, k)
    n, lab, st, _ = cv2.connectedComponentsWithStats(m, 8)
    keep = np.zeros_like(m)
    floor = max(50.0, 0.00018 * m.size)
    for i in range(1, n):
        if st[i, cv2.CC_STAT_AREA] >= floor:
            keep[lab == i] = 255
    return keep


def _pivot(mask):
    import numpy as _np
    mu = mask.copy()
    dt = cv2.distanceTransform(mu, cv2.DIST_L2, 5)
    mx = float(dt.max())
    cordm = None
    if mx >= 4.0:
        thr = 0.55 * mx
        core = (dt > thr).astype(_np.uint8) * 255
        if core.any():
            rad = max(3, int(round(thr)) + 2)
            ker = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * rad + 1, 2 * rad + 1))
            grown = cv2.dilate(core, ker)
            cand = cv2.bitwise_and(mu, cv2.bitwise_not(grown))
            if int((cand > 0).sum()) >= 60:
                cordm = cand
    src = cordm if cordm is not None else mu
    ys, xs = _np.nonzero(src)
    if ys.size < 10:
        ys, xs = _np.nonzero(mu)
    ys = ys.astype(_np.float64)
    xs = xs.astype(_np.float64)
    y0 = float(_np.percentile(ys, 0.4))
    band = ys <= y0 + max(5.0, 0.008 * mask.shape[0])
    if int(band.sum()) < 5:
        band = ys <= y0 + 12.0
    return float(_np.mean(xs[band])), y0, cordm


def _lobes(xs, ys, px, py, d, rmax):
    sel = (d >= 0.35 * rmax) & (d <= 0.90 * rmax)
    if int(sel.sum()) < 40:
        return 0
    ang = np.degrees(np.arctan2(xs[sel] - px, np.maximum(ys[sel] - py, 0.0) + 1e-6))
    hist, _ = np.histogram(ang, bins=np.arange(-100.0, 100.1, 2.0))
    if hist.max() <= 0:
        return 0
    live = hist >= max(3.0, 0.10 * float(hist.max()))
    runs, i, n = [], 0, live.size
    while i < n:
        if not live[i]:
            i += 1
            continue
        j = i
        while j + 1 < n and (live[j + 1] or (j + 2 < n and live[j + 2])):
            j += 1
        runs.append((i, j))
        i = j + 1
    total = float(hist.sum())
    return int(sum(1 for a, b in runs if float(hist[a:b + 1].sum()) >= 0.06 * total))


def pendulum_read(image, colours):
    bgr = _load(image)
    if bgr is None:
        return {"no_read": True, "reason": "unreadable_file"}
    H, W = bgr.shape[:2]
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    per = []
    for c in colours:
        m = _colour_mask(bgr, hsv, c)
        ys, xs = np.nonzero(m)
        if ys.size < 150:
            per.append(None)
            continue
        ys = ys.astype(np.float64)
        xs = xs.astype(np.float64)
        px, py, _cordm = _pivot(m)
        d = np.hypot(xs - px, ys - py)
        rmax = float(d.max())
        if rmax < 0.04 * H:
            per.append(None)
            continue
        arms = {}
        for sgn in (-1, 1):
            sel = (xs - px) * sgn > 0.006 * W
            if int(sel.sum()) < 25:
                continue
            i = int(np.argmax(np.where(sel, d, -1.0)))
            L, drop = float(d[i]), float(ys[i] - py)
            if L < 0.03 * H:
                continue
            arms[sgn] = {"L": round(L, 1), "drop": round(drop, 1),
                         "r": round(max(0.0, min(2.0, (L - drop) / L)), 4),
                         "tip": [int(xs[i]), int(ys[i])]}
        if not arms:
            per.append(None)
            continue
        rs = [a["r"] for a in arms.values()]
        per.append({"colour": str(c), "pivot": [round(px, 1), round(py, 1)],
                    "arms": [arms.get(-1), arms.get(1)],
                    "cord_px": round(float(np.mean([a["L"] for a in arms.values()])), 1),
                    "rise_over_L": round(float(np.mean(rs)), 4),
                    "one_sided": len(arms) < 2,
                    "exposures": _lobes(xs, ys, px, py, d, rmax)})
    got = [(p["pivot"][0], p["colour"]) for p in per if p]
    got.sort()
    return {"no_read": False, "H": H, "W": W, "per": per,
            "colours": [str(c) for c in colours],
            "rise_over_L": [(p["rise_over_L"] if p else None) for p in per],
            "cord_px": [(p["cord_px"] if p else None) for p in per],
            "exposures": [(p["exposures"] if p else 0) for p in per],
            "n_found": sum(1 for p in per if p),
            "order": [c for _x, c in got]}


def pendulums_readable_frac(m, k):
    if m.get("no_read"):
        return 0.0
    ok = sum(1 for p in (m.get("per") or []) if p and p.get("rise_over_L") is not None)
    return 1.0 if ok >= max(2, int(k) - 1) else 0.0


def exposures_frac(m, k):
    if m.get("no_read"):
        return 0.0
    e = m.get("exposures") or []
    return round(sum(1 for x in e if int(x) == 2) / float(max(1, int(k))), 4)


def colour_order_frac(m, expected):
    if m.get("no_read"):
        return 0.0
    got = m.get("order") or []
    exp = [str(x) for x in expected]
    if not got:
        return 0.0
    hit = sum(1 for i, c in enumerate(exp) if i < len(got) and got[i] == c)
    return round(hit / float(len(exp)), 4)


def rise_ratio_frac(m, targets):
    if m.get("no_read"):
        return 0.0
    vals = m.get("rise_over_L") or []
    fr = []
    for i, t in enumerate(targets):
        v = vals[i] if i < len(vals) else None
        fr.append(_band(v, float(t), 0.012 + 0.10 * float(t), 0.016 + 0.12 * float(t)))
    return round(sum(fr) / float(max(1, len(targets))), 4)


def rise_spread_frac(m, target):
    if m.get("no_read"):
        return 0.0
    vals = [v for v in (m.get("rise_over_L") or []) if v]
    if len(vals) < 2 or min(vals) <= 0:
        return 0.0
    return _logband(max(vals) / min(vals), float(target), 1.25, 1.45)


def cord_copy_frac(m, cord_units):
    if m.get("no_read"):
        return 0.0
    got = [v for v in (m.get("cord_px") or [])]
    if any(v is None for v in got) or not got:
        return 0.0
    gm, tm = max(got), max(float(x) for x in cord_units)
    fr = [_band(g / gm, float(t) / tm, 0.12 * (float(t) / tm) + 0.02,
                0.12 * (float(t) / tm) + 0.02) for g, t in zip(got, cord_units)]
    return round(sum(fr) / float(len(fr)), 4)


def pendulum_overlay(image, colours, targets, out_path):
    m = pendulum_read(image, colours)
    bgr = _load(image)
    if bgr is None:
        return {"no_read": True, "path": None}
    vis = bgr.copy()
    if not m.get("no_read"):
        for p, t in zip(m["per"], list(targets) + [None] * 8):
            if not p:
                continue
            px, py = int(p["pivot"][0]), int(p["pivot"][1])
            cv2.circle(vis, (px, py), 5, (0, 220, 255), -1)
            for a in p["arms"]:
                if not a:
                    continue
                cv2.line(vis, (px, py), tuple(a["tip"]), (0, 220, 255), 2)
                if t:
                    yy = int(py + a["L"] * (1.0 - float(t)))
                    xx = int(a["tip"][0])
                    cv2.line(vis, (xx - 16, yy), (xx + 16, yy), (255, 90, 90), 3)
            cv2.putText(vis, "%.3f" % p["rise_over_L"], (px - 30, max(16, py - 8)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 0), 2)
        sp = [v for v in m["rise_over_L"] if v]
        if len(sp) >= 2 and min(sp) > 0:
            cv2.putText(vis, "spread max/min = %.2f  order=%s"
                        % (max(sp) / min(sp), ",".join(m["order"])), (10, 24),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
    cv2.imwrite(str(out_path), vis)
    return {"no_read": bool(m.get("no_read")), "path": str(out_path)}


def draw_pendulum_overlay(image, colours, targets):
    import hashlib
    import os as _os
    import tempfile
    d = _os.path.join(tempfile.gettempdir(), "genolympiad_overlay")
    try:
        _os.makedirs(d, exist_ok=True)
    except Exception:
        pass
    h = hashlib.md5(str(image).encode("utf-8", "replace")).hexdigest()[:12]
    try:
        pendulum_overlay(image, colours, targets, _os.path.join(d, "pend_%s.png" % h))
    except Exception:
        pass
    return 1.0

# end of code_ecc4f194366a

# shared code: code_f32b8a000df9
def score_cord_lengths(measured, c):
    """Average how closely the relative cord lengths match the drawn units."""
    return cord_copy_frac(measured, c)
import math

import numpy as np
import cv2

cv2.setNumThreads(2)

_HUE = {"red": [(0, 8), (168, 180)], "orange": [(9, 22)], "yellow": [(23, 36)],
        "green": [(38, 85)], "cyan": [(86, 100)], "blue": [(101, 130)],
        "purple": [(131, 158)], "magenta": [(159, 172)]}


def _load(image, cap=1500):
    a = cv2.imread(str(image), cv2.IMREAD_COLOR)
    if a is None:
        return None
    h, w = a.shape[:2]
    if max(h, w) > cap:
        s = cap / float(max(h, w))
        a = cv2.resize(a, (int(w * s), int(h * s)), interpolation=cv2.INTER_AREA)
    return a


def _band(v, t, core, margin):
    if v is None or t is None:
        return 0.0
    d = abs(float(v) - float(t))
    return round(min(1.0, max(0.0, 1.0 - max(0.0, d - float(core)) / max(float(margin), 1e-9))), 4)


def _logband(got, target, core_ratio=1.25, margin_ratio=1.40):
    if not got or not target or got <= 0 or target <= 0:
        return 0.0
    d = abs(math.log(float(got) / float(target)))
    core = math.log(float(core_ratio))
    margin = math.log(float(margin_ratio)) - core
    return round(min(1.0, max(0.0, 1.0 - max(0.0, d - core) / max(margin, 1e-9))), 4)


def _colour_mask(bgr, hsv, name, smin=80, vmin=40):
    m = np.zeros(hsv.shape[:2], np.uint8)
    for lo, hi in _HUE[str(name)]:
        m |= cv2.inRange(hsv, (int(lo), smin, vmin), (int(min(hi, 179)), 255, 255))
    k = np.ones((3, 3), np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, k)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, k)
    n, lab, st, _ = cv2.connectedComponentsWithStats(m, 8)
    keep = np.zeros_like(m)
    floor = max(50.0, 0.00018 * m.size)
    for i in range(1, n):
        if st[i, cv2.CC_STAT_AREA] >= floor:
            keep[lab == i] = 255
    return keep


def _pivot(mask):
    import numpy as _np
    mu = mask.copy()
    dt = cv2.distanceTransform(mu, cv2.DIST_L2, 5)
    mx = float(dt.max())
    cordm = None
    if mx >= 4.0:
        thr = 0.55 * mx
        core = (dt > thr).astype(_np.uint8) * 255
        if core.any():
            rad = max(3, int(round(thr)) + 2)
            ker = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * rad + 1, 2 * rad + 1))
            grown = cv2.dilate(core, ker)
            cand = cv2.bitwise_and(mu, cv2.bitwise_not(grown))
            if int((cand > 0).sum()) >= 60:
                cordm = cand
    src = cordm if cordm is not None else mu
    ys, xs = _np.nonzero(src)
    if ys.size < 10:
        ys, xs = _np.nonzero(mu)
    ys = ys.astype(_np.float64)
    xs = xs.astype(_np.float64)
    y0 = float(_np.percentile(ys, 0.4))
    band = ys <= y0 + max(5.0, 0.008 * mask.shape[0])
    if int(band.sum()) < 5:
        band = ys <= y0 + 12.0
    return float(_np.mean(xs[band])), y0, cordm


def _lobes(xs, ys, px, py, d, rmax):
    sel = (d >= 0.35 * rmax) & (d <= 0.90 * rmax)
    if int(sel.sum()) < 40:
        return 0
    ang = np.degrees(np.arctan2(xs[sel] - px, np.maximum(ys[sel] - py, 0.0) + 1e-6))
    hist, _ = np.histogram(ang, bins=np.arange(-100.0, 100.1, 2.0))
    if hist.max() <= 0:
        return 0
    live = hist >= max(3.0, 0.10 * float(hist.max()))
    runs, i, n = [], 0, live.size
    while i < n:
        if not live[i]:
            i += 1
            continue
        j = i
        while j + 1 < n and (live[j + 1] or (j + 2 < n and live[j + 2])):
            j += 1
        runs.append((i, j))
        i = j + 1
    total = float(hist.sum())
    return int(sum(1 for a, b in runs if float(hist[a:b + 1].sum()) >= 0.06 * total))


def pendulum_read(image, colours):
    bgr = _load(image)
    if bgr is None:
        return {"no_read": True, "reason": "unreadable_file"}
    H, W = bgr.shape[:2]
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    per = []
    for c in colours:
        m = _colour_mask(bgr, hsv, c)
        ys, xs = np.nonzero(m)
        if ys.size < 150:
            per.append(None)
            continue
        ys = ys.astype(np.float64)
        xs = xs.astype(np.float64)
        px, py, _cordm = _pivot(m)
        d = np.hypot(xs - px, ys - py)
        rmax = float(d.max())
        if rmax < 0.04 * H:
            per.append(None)
            continue
        arms = {}
        for sgn in (-1, 1):
            sel = (xs - px) * sgn > 0.006 * W
            if int(sel.sum()) < 25:
                continue
            i = int(np.argmax(np.where(sel, d, -1.0)))
            L, drop = float(d[i]), float(ys[i] - py)
            if L < 0.03 * H:
                continue
            arms[sgn] = {"L": round(L, 1), "drop": round(drop, 1),
                         "r": round(max(0.0, min(2.0, (L - drop) / L)), 4),
                         "tip": [int(xs[i]), int(ys[i])]}
        if not arms:
            per.append(None)
            continue
        rs = [a["r"] for a in arms.values()]
        per.append({"colour": str(c), "pivot": [round(px, 1), round(py, 1)],
                    "arms": [arms.get(-1), arms.get(1)],
                    "cord_px": round(float(np.mean([a["L"] for a in arms.values()])), 1),
                    "rise_over_L": round(float(np.mean(rs)), 4),
                    "one_sided": len(arms) < 2,
                    "exposures": _lobes(xs, ys, px, py, d, rmax)})
    got = [(p["pivot"][0], p["colour"]) for p in per if p]
    got.sort()
    return {"no_read": False, "H": H, "W": W, "per": per,
            "colours": [str(c) for c in colours],
            "rise_over_L": [(p["rise_over_L"] if p else None) for p in per],
            "cord_px": [(p["cord_px"] if p else None) for p in per],
            "exposures": [(p["exposures"] if p else 0) for p in per],
            "n_found": sum(1 for p in per if p),
            "order": [c for _x, c in got]}


def pendulums_readable_frac(m, k):
    if m.get("no_read"):
        return 0.0
    ok = sum(1 for p in (m.get("per") or []) if p and p.get("rise_over_L") is not None)
    return 1.0 if ok >= max(2, int(k) - 1) else 0.0


def exposures_frac(m, k):
    if m.get("no_read"):
        return 0.0
    e = m.get("exposures") or []
    return round(sum(1 for x in e if int(x) == 2) / float(max(1, int(k))), 4)


def colour_order_frac(m, expected):
    if m.get("no_read"):
        return 0.0
    got = m.get("order") or []
    exp = [str(x) for x in expected]
    if not got:
        return 0.0
    hit = sum(1 for i, c in enumerate(exp) if i < len(got) and got[i] == c)
    return round(hit / float(len(exp)), 4)


def rise_ratio_frac(m, targets):
    if m.get("no_read"):
        return 0.0
    vals = m.get("rise_over_L") or []
    fr = []
    for i, t in enumerate(targets):
        v = vals[i] if i < len(vals) else None
        fr.append(_band(v, float(t), 0.012 + 0.10 * float(t), 0.016 + 0.12 * float(t)))
    return round(sum(fr) / float(max(1, len(targets))), 4)


def rise_spread_frac(m, target):
    if m.get("no_read"):
        return 0.0
    vals = [v for v in (m.get("rise_over_L") or []) if v]
    if len(vals) < 2 or min(vals) <= 0:
        return 0.0
    return _logband(max(vals) / min(vals), float(target), 1.25, 1.45)


def cord_copy_frac(m, cord_units):
    if m.get("no_read"):
        return 0.0
    got = [v for v in (m.get("cord_px") or [])]
    if any(v is None for v in got) or not got:
        return 0.0
    gm, tm = max(got), max(float(x) for x in cord_units)
    fr = [_band(g / gm, float(t) / tm, 0.12 * (float(t) / tm) + 0.02,
                0.12 * (float(t) / tm) + 0.02) for g, t in zip(got, cord_units)]
    return round(sum(fr) / float(len(fr)), 4)


def pendulum_overlay(image, colours, targets, out_path):
    m = pendulum_read(image, colours)
    bgr = _load(image)
    if bgr is None:
        return {"no_read": True, "path": None}
    vis = bgr.copy()
    if not m.get("no_read"):
        for p, t in zip(m["per"], list(targets) + [None] * 8):
            if not p:
                continue
            px, py = int(p["pivot"][0]), int(p["pivot"][1])
            cv2.circle(vis, (px, py), 5, (0, 220, 255), -1)
            for a in p["arms"]:
                if not a:
                    continue
                cv2.line(vis, (px, py), tuple(a["tip"]), (0, 220, 255), 2)
                if t:
                    yy = int(py + a["L"] * (1.0 - float(t)))
                    xx = int(a["tip"][0])
                    cv2.line(vis, (xx - 16, yy), (xx + 16, yy), (255, 90, 90), 3)
            cv2.putText(vis, "%.3f" % p["rise_over_L"], (px - 30, max(16, py - 8)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 0), 2)
        sp = [v for v in m["rise_over_L"] if v]
        if len(sp) >= 2 and min(sp) > 0:
            cv2.putText(vis, "spread max/min = %.2f  order=%s"
                        % (max(sp) / min(sp), ",".join(m["order"])), (10, 24),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
    cv2.imwrite(str(out_path), vis)
    return {"no_read": bool(m.get("no_read")), "path": str(out_path)}


def draw_pendulum_overlay(image, colours, targets):
    import hashlib
    import os as _os
    import tempfile
    d = _os.path.join(tempfile.gettempdir(), "genolympiad_overlay")
    try:
        _os.makedirs(d, exist_ok=True)
    except Exception:
        pass
    h = hashlib.md5(str(image).encode("utf-8", "replace")).hexdigest()[:12]
    try:
        pendulum_overlay(image, colours, targets, _os.path.join(d, "pend_%s.png" % h))
    except Exception:
        pass
    return 1.0

# end of code_f32b8a000df9

# shared code: code_f504fd42b330
def score_rise_ratios(measured, t):
    """Average how closely each pendulum's rise over cord length matches its target."""
    return rise_ratio_frac(measured, t)
import math

import numpy as np
import cv2

cv2.setNumThreads(2)

_HUE = {"red": [(0, 8), (168, 180)], "orange": [(9, 22)], "yellow": [(23, 36)],
        "green": [(38, 85)], "cyan": [(86, 100)], "blue": [(101, 130)],
        "purple": [(131, 158)], "magenta": [(159, 172)]}


def _load(image, cap=1500):
    a = cv2.imread(str(image), cv2.IMREAD_COLOR)
    if a is None:
        return None
    h, w = a.shape[:2]
    if max(h, w) > cap:
        s = cap / float(max(h, w))
        a = cv2.resize(a, (int(w * s), int(h * s)), interpolation=cv2.INTER_AREA)
    return a


def _band(v, t, core, margin):
    if v is None or t is None:
        return 0.0
    d = abs(float(v) - float(t))
    return round(min(1.0, max(0.0, 1.0 - max(0.0, d - float(core)) / max(float(margin), 1e-9))), 4)


def _logband(got, target, core_ratio=1.25, margin_ratio=1.40):
    if not got or not target or got <= 0 or target <= 0:
        return 0.0
    d = abs(math.log(float(got) / float(target)))
    core = math.log(float(core_ratio))
    margin = math.log(float(margin_ratio)) - core
    return round(min(1.0, max(0.0, 1.0 - max(0.0, d - core) / max(margin, 1e-9))), 4)


def _colour_mask(bgr, hsv, name, smin=80, vmin=40):
    m = np.zeros(hsv.shape[:2], np.uint8)
    for lo, hi in _HUE[str(name)]:
        m |= cv2.inRange(hsv, (int(lo), smin, vmin), (int(min(hi, 179)), 255, 255))
    k = np.ones((3, 3), np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, k)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, k)
    n, lab, st, _ = cv2.connectedComponentsWithStats(m, 8)
    keep = np.zeros_like(m)
    floor = max(50.0, 0.00018 * m.size)
    for i in range(1, n):
        if st[i, cv2.CC_STAT_AREA] >= floor:
            keep[lab == i] = 255
    return keep


def _pivot(mask):
    import numpy as _np
    mu = mask.copy()
    dt = cv2.distanceTransform(mu, cv2.DIST_L2, 5)
    mx = float(dt.max())
    cordm = None
    if mx >= 4.0:
        thr = 0.55 * mx
        core = (dt > thr).astype(_np.uint8) * 255
        if core.any():
            rad = max(3, int(round(thr)) + 2)
            ker = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * rad + 1, 2 * rad + 1))
            grown = cv2.dilate(core, ker)
            cand = cv2.bitwise_and(mu, cv2.bitwise_not(grown))
            if int((cand > 0).sum()) >= 60:
                cordm = cand
    src = cordm if cordm is not None else mu
    ys, xs = _np.nonzero(src)
    if ys.size < 10:
        ys, xs = _np.nonzero(mu)
    ys = ys.astype(_np.float64)
    xs = xs.astype(_np.float64)
    y0 = float(_np.percentile(ys, 0.4))
    band = ys <= y0 + max(5.0, 0.008 * mask.shape[0])
    if int(band.sum()) < 5:
        band = ys <= y0 + 12.0
    return float(_np.mean(xs[band])), y0, cordm


def _lobes(xs, ys, px, py, d, rmax):
    sel = (d >= 0.35 * rmax) & (d <= 0.90 * rmax)
    if int(sel.sum()) < 40:
        return 0
    ang = np.degrees(np.arctan2(xs[sel] - px, np.maximum(ys[sel] - py, 0.0) + 1e-6))
    hist, _ = np.histogram(ang, bins=np.arange(-100.0, 100.1, 2.0))
    if hist.max() <= 0:
        return 0
    live = hist >= max(3.0, 0.10 * float(hist.max()))
    runs, i, n = [], 0, live.size
    while i < n:
        if not live[i]:
            i += 1
            continue
        j = i
        while j + 1 < n and (live[j + 1] or (j + 2 < n and live[j + 2])):
            j += 1
        runs.append((i, j))
        i = j + 1
    total = float(hist.sum())
    return int(sum(1 for a, b in runs if float(hist[a:b + 1].sum()) >= 0.06 * total))


def pendulum_read(image, colours):
    bgr = _load(image)
    if bgr is None:
        return {"no_read": True, "reason": "unreadable_file"}
    H, W = bgr.shape[:2]
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    per = []
    for c in colours:
        m = _colour_mask(bgr, hsv, c)
        ys, xs = np.nonzero(m)
        if ys.size < 150:
            per.append(None)
            continue
        ys = ys.astype(np.float64)
        xs = xs.astype(np.float64)
        px, py, _cordm = _pivot(m)
        d = np.hypot(xs - px, ys - py)
        rmax = float(d.max())
        if rmax < 0.04 * H:
            per.append(None)
            continue
        arms = {}
        for sgn in (-1, 1):
            sel = (xs - px) * sgn > 0.006 * W
            if int(sel.sum()) < 25:
                continue
            i = int(np.argmax(np.where(sel, d, -1.0)))
            L, drop = float(d[i]), float(ys[i] - py)
            if L < 0.03 * H:
                continue
            arms[sgn] = {"L": round(L, 1), "drop": round(drop, 1),
                         "r": round(max(0.0, min(2.0, (L - drop) / L)), 4),
                         "tip": [int(xs[i]), int(ys[i])]}
        if not arms:
            per.append(None)
            continue
        rs = [a["r"] for a in arms.values()]
        per.append({"colour": str(c), "pivot": [round(px, 1), round(py, 1)],
                    "arms": [arms.get(-1), arms.get(1)],
                    "cord_px": round(float(np.mean([a["L"] for a in arms.values()])), 1),
                    "rise_over_L": round(float(np.mean(rs)), 4),
                    "one_sided": len(arms) < 2,
                    "exposures": _lobes(xs, ys, px, py, d, rmax)})
    got = [(p["pivot"][0], p["colour"]) for p in per if p]
    got.sort()
    return {"no_read": False, "H": H, "W": W, "per": per,
            "colours": [str(c) for c in colours],
            "rise_over_L": [(p["rise_over_L"] if p else None) for p in per],
            "cord_px": [(p["cord_px"] if p else None) for p in per],
            "exposures": [(p["exposures"] if p else 0) for p in per],
            "n_found": sum(1 for p in per if p),
            "order": [c for _x, c in got]}


def pendulums_readable_frac(m, k):
    if m.get("no_read"):
        return 0.0
    ok = sum(1 for p in (m.get("per") or []) if p and p.get("rise_over_L") is not None)
    return 1.0 if ok >= max(2, int(k) - 1) else 0.0


def exposures_frac(m, k):
    if m.get("no_read"):
        return 0.0
    e = m.get("exposures") or []
    return round(sum(1 for x in e if int(x) == 2) / float(max(1, int(k))), 4)


def colour_order_frac(m, expected):
    if m.get("no_read"):
        return 0.0
    got = m.get("order") or []
    exp = [str(x) for x in expected]
    if not got:
        return 0.0
    hit = sum(1 for i, c in enumerate(exp) if i < len(got) and got[i] == c)
    return round(hit / float(len(exp)), 4)


def rise_ratio_frac(m, targets):
    if m.get("no_read"):
        return 0.0
    vals = m.get("rise_over_L") or []
    fr = []
    for i, t in enumerate(targets):
        v = vals[i] if i < len(vals) else None
        fr.append(_band(v, float(t), 0.012 + 0.10 * float(t), 0.016 + 0.12 * float(t)))
    return round(sum(fr) / float(max(1, len(targets))), 4)


def rise_spread_frac(m, target):
    if m.get("no_read"):
        return 0.0
    vals = [v for v in (m.get("rise_over_L") or []) if v]
    if len(vals) < 2 or min(vals) <= 0:
        return 0.0
    return _logband(max(vals) / min(vals), float(target), 1.25, 1.45)


def cord_copy_frac(m, cord_units):
    if m.get("no_read"):
        return 0.0
    got = [v for v in (m.get("cord_px") or [])]
    if any(v is None for v in got) or not got:
        return 0.0
    gm, tm = max(got), max(float(x) for x in cord_units)
    fr = [_band(g / gm, float(t) / tm, 0.12 * (float(t) / tm) + 0.02,
                0.12 * (float(t) / tm) + 0.02) for g, t in zip(got, cord_units)]
    return round(sum(fr) / float(len(fr)), 4)


def pendulum_overlay(image, colours, targets, out_path):
    m = pendulum_read(image, colours)
    bgr = _load(image)
    if bgr is None:
        return {"no_read": True, "path": None}
    vis = bgr.copy()
    if not m.get("no_read"):
        for p, t in zip(m["per"], list(targets) + [None] * 8):
            if not p:
                continue
            px, py = int(p["pivot"][0]), int(p["pivot"][1])
            cv2.circle(vis, (px, py), 5, (0, 220, 255), -1)
            for a in p["arms"]:
                if not a:
                    continue
                cv2.line(vis, (px, py), tuple(a["tip"]), (0, 220, 255), 2)
                if t:
                    yy = int(py + a["L"] * (1.0 - float(t)))
                    xx = int(a["tip"][0])
                    cv2.line(vis, (xx - 16, yy), (xx + 16, yy), (255, 90, 90), 3)
            cv2.putText(vis, "%.3f" % p["rise_over_L"], (px - 30, max(16, py - 8)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 0), 2)
        sp = [v for v in m["rise_over_L"] if v]
        if len(sp) >= 2 and min(sp) > 0:
            cv2.putText(vis, "spread max/min = %.2f  order=%s"
                        % (max(sp) / min(sp), ",".join(m["order"])), (10, 24),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
    cv2.imwrite(str(out_path), vis)
    return {"no_read": bool(m.get("no_read")), "path": str(out_path)}


def draw_pendulum_overlay(image, colours, targets):
    import hashlib
    import os as _os
    import tempfile
    d = _os.path.join(tempfile.gettempdir(), "genolympiad_overlay")
    try:
        _os.makedirs(d, exist_ok=True)
    except Exception:
        pass
    h = hashlib.md5(str(image).encode("utf-8", "replace")).hexdigest()[:12]
    try:
        pendulum_overlay(image, colours, targets, _os.path.join(d, "pend_%s.png" % h))
    except Exception:
        pass
    return 1.0

# end of code_f504fd42b330

# shared code: code_fa058405e56d
def score_exposures(measured, k):
    """The share of pendulums that show exactly two swing exposures."""
    return exposures_frac(measured, k)
import math

import numpy as np
import cv2

cv2.setNumThreads(2)

_HUE = {"red": [(0, 8), (168, 180)], "orange": [(9, 22)], "yellow": [(23, 36)],
        "green": [(38, 85)], "cyan": [(86, 100)], "blue": [(101, 130)],
        "purple": [(131, 158)], "magenta": [(159, 172)]}


def _load(image, cap=1500):
    a = cv2.imread(str(image), cv2.IMREAD_COLOR)
    if a is None:
        return None
    h, w = a.shape[:2]
    if max(h, w) > cap:
        s = cap / float(max(h, w))
        a = cv2.resize(a, (int(w * s), int(h * s)), interpolation=cv2.INTER_AREA)
    return a


def _band(v, t, core, margin):
    if v is None or t is None:
        return 0.0
    d = abs(float(v) - float(t))
    return round(min(1.0, max(0.0, 1.0 - max(0.0, d - float(core)) / max(float(margin), 1e-9))), 4)


def _logband(got, target, core_ratio=1.25, margin_ratio=1.40):
    if not got or not target or got <= 0 or target <= 0:
        return 0.0
    d = abs(math.log(float(got) / float(target)))
    core = math.log(float(core_ratio))
    margin = math.log(float(margin_ratio)) - core
    return round(min(1.0, max(0.0, 1.0 - max(0.0, d - core) / max(margin, 1e-9))), 4)


def _colour_mask(bgr, hsv, name, smin=80, vmin=40):
    m = np.zeros(hsv.shape[:2], np.uint8)
    for lo, hi in _HUE[str(name)]:
        m |= cv2.inRange(hsv, (int(lo), smin, vmin), (int(min(hi, 179)), 255, 255))
    k = np.ones((3, 3), np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, k)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, k)
    n, lab, st, _ = cv2.connectedComponentsWithStats(m, 8)
    keep = np.zeros_like(m)
    floor = max(50.0, 0.00018 * m.size)
    for i in range(1, n):
        if st[i, cv2.CC_STAT_AREA] >= floor:
            keep[lab == i] = 255
    return keep


def _pivot(mask):
    import numpy as _np
    mu = mask.copy()
    dt = cv2.distanceTransform(mu, cv2.DIST_L2, 5)
    mx = float(dt.max())
    cordm = None
    if mx >= 4.0:
        thr = 0.55 * mx
        core = (dt > thr).astype(_np.uint8) * 255
        if core.any():
            rad = max(3, int(round(thr)) + 2)
            ker = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * rad + 1, 2 * rad + 1))
            grown = cv2.dilate(core, ker)
            cand = cv2.bitwise_and(mu, cv2.bitwise_not(grown))
            if int((cand > 0).sum()) >= 60:
                cordm = cand
    src = cordm if cordm is not None else mu
    ys, xs = _np.nonzero(src)
    if ys.size < 10:
        ys, xs = _np.nonzero(mu)
    ys = ys.astype(_np.float64)
    xs = xs.astype(_np.float64)
    y0 = float(_np.percentile(ys, 0.4))
    band = ys <= y0 + max(5.0, 0.008 * mask.shape[0])
    if int(band.sum()) < 5:
        band = ys <= y0 + 12.0
    return float(_np.mean(xs[band])), y0, cordm


def _lobes(xs, ys, px, py, d, rmax):
    sel = (d >= 0.35 * rmax) & (d <= 0.90 * rmax)
    if int(sel.sum()) < 40:
        return 0
    ang = np.degrees(np.arctan2(xs[sel] - px, np.maximum(ys[sel] - py, 0.0) + 1e-6))
    hist, _ = np.histogram(ang, bins=np.arange(-100.0, 100.1, 2.0))
    if hist.max() <= 0:
        return 0
    live = hist >= max(3.0, 0.10 * float(hist.max()))
    runs, i, n = [], 0, live.size
    while i < n:
        if not live[i]:
            i += 1
            continue
        j = i
        while j + 1 < n and (live[j + 1] or (j + 2 < n and live[j + 2])):
            j += 1
        runs.append((i, j))
        i = j + 1
    total = float(hist.sum())
    return int(sum(1 for a, b in runs if float(hist[a:b + 1].sum()) >= 0.06 * total))


def pendulum_read(image, colours):
    bgr = _load(image)
    if bgr is None:
        return {"no_read": True, "reason": "unreadable_file"}
    H, W = bgr.shape[:2]
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    per = []
    for c in colours:
        m = _colour_mask(bgr, hsv, c)
        ys, xs = np.nonzero(m)
        if ys.size < 150:
            per.append(None)
            continue
        ys = ys.astype(np.float64)
        xs = xs.astype(np.float64)
        px, py, _cordm = _pivot(m)
        d = np.hypot(xs - px, ys - py)
        rmax = float(d.max())
        if rmax < 0.04 * H:
            per.append(None)
            continue
        arms = {}
        for sgn in (-1, 1):
            sel = (xs - px) * sgn > 0.006 * W
            if int(sel.sum()) < 25:
                continue
            i = int(np.argmax(np.where(sel, d, -1.0)))
            L, drop = float(d[i]), float(ys[i] - py)
            if L < 0.03 * H:
                continue
            arms[sgn] = {"L": round(L, 1), "drop": round(drop, 1),
                         "r": round(max(0.0, min(2.0, (L - drop) / L)), 4),
                         "tip": [int(xs[i]), int(ys[i])]}
        if not arms:
            per.append(None)
            continue
        rs = [a["r"] for a in arms.values()]
        per.append({"colour": str(c), "pivot": [round(px, 1), round(py, 1)],
                    "arms": [arms.get(-1), arms.get(1)],
                    "cord_px": round(float(np.mean([a["L"] for a in arms.values()])), 1),
                    "rise_over_L": round(float(np.mean(rs)), 4),
                    "one_sided": len(arms) < 2,
                    "exposures": _lobes(xs, ys, px, py, d, rmax)})
    got = [(p["pivot"][0], p["colour"]) for p in per if p]
    got.sort()
    return {"no_read": False, "H": H, "W": W, "per": per,
            "colours": [str(c) for c in colours],
            "rise_over_L": [(p["rise_over_L"] if p else None) for p in per],
            "cord_px": [(p["cord_px"] if p else None) for p in per],
            "exposures": [(p["exposures"] if p else 0) for p in per],
            "n_found": sum(1 for p in per if p),
            "order": [c for _x, c in got]}


def pendulums_readable_frac(m, k):
    if m.get("no_read"):
        return 0.0
    ok = sum(1 for p in (m.get("per") or []) if p and p.get("rise_over_L") is not None)
    return 1.0 if ok >= max(2, int(k) - 1) else 0.0


def exposures_frac(m, k):
    if m.get("no_read"):
        return 0.0
    e = m.get("exposures") or []
    return round(sum(1 for x in e if int(x) == 2) / float(max(1, int(k))), 4)


def colour_order_frac(m, expected):
    if m.get("no_read"):
        return 0.0
    got = m.get("order") or []
    exp = [str(x) for x in expected]
    if not got:
        return 0.0
    hit = sum(1 for i, c in enumerate(exp) if i < len(got) and got[i] == c)
    return round(hit / float(len(exp)), 4)


def rise_ratio_frac(m, targets):
    if m.get("no_read"):
        return 0.0
    vals = m.get("rise_over_L") or []
    fr = []
    for i, t in enumerate(targets):
        v = vals[i] if i < len(vals) else None
        fr.append(_band(v, float(t), 0.012 + 0.10 * float(t), 0.016 + 0.12 * float(t)))
    return round(sum(fr) / float(max(1, len(targets))), 4)


def rise_spread_frac(m, target):
    if m.get("no_read"):
        return 0.0
    vals = [v for v in (m.get("rise_over_L") or []) if v]
    if len(vals) < 2 or min(vals) <= 0:
        return 0.0
    return _logband(max(vals) / min(vals), float(target), 1.25, 1.45)


def cord_copy_frac(m, cord_units):
    if m.get("no_read"):
        return 0.0
    got = [v for v in (m.get("cord_px") or [])]
    if any(v is None for v in got) or not got:
        return 0.0
    gm, tm = max(got), max(float(x) for x in cord_units)
    fr = [_band(g / gm, float(t) / tm, 0.12 * (float(t) / tm) + 0.02,
                0.12 * (float(t) / tm) + 0.02) for g, t in zip(got, cord_units)]
    return round(sum(fr) / float(len(fr)), 4)


def pendulum_overlay(image, colours, targets, out_path):
    m = pendulum_read(image, colours)
    bgr = _load(image)
    if bgr is None:
        return {"no_read": True, "path": None}
    vis = bgr.copy()
    if not m.get("no_read"):
        for p, t in zip(m["per"], list(targets) + [None] * 8):
            if not p:
                continue
            px, py = int(p["pivot"][0]), int(p["pivot"][1])
            cv2.circle(vis, (px, py), 5, (0, 220, 255), -1)
            for a in p["arms"]:
                if not a:
                    continue
                cv2.line(vis, (px, py), tuple(a["tip"]), (0, 220, 255), 2)
                if t:
                    yy = int(py + a["L"] * (1.0 - float(t)))
                    xx = int(a["tip"][0])
                    cv2.line(vis, (xx - 16, yy), (xx + 16, yy), (255, 90, 90), 3)
            cv2.putText(vis, "%.3f" % p["rise_over_L"], (px - 30, max(16, py - 8)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 0), 2)
        sp = [v for v in m["rise_over_L"] if v]
        if len(sp) >= 2 and min(sp) > 0:
            cv2.putText(vis, "spread max/min = %.2f  order=%s"
                        % (max(sp) / min(sp), ",".join(m["order"])), (10, 24),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
    cv2.imwrite(str(out_path), vis)
    return {"no_read": bool(m.get("no_read")), "path": str(out_path)}


def draw_pendulum_overlay(image, colours, targets):
    import hashlib
    import os as _os
    import tempfile
    d = _os.path.join(tempfile.gettempdir(), "genolympiad_overlay")
    try:
        _os.makedirs(d, exist_ok=True)
    except Exception:
        pass
    h = hashlib.md5(str(image).encode("utf-8", "replace")).hexdigest()[:12]
    try:
        pendulum_overlay(image, colours, targets, _os.path.join(d, "pend_%s.png" % h))
    except Exception:
        pass
    return 1.0

# end of code_fa058405e56d
