# shared code: code_6acd14695e1d

def _segs(image, min_frac):
    import math
    import numpy as np
    import cv2
    from PIL import Image
    if hasattr(image, "convert"):
        pil = image.convert("RGB")
    else:
        pil = Image.open(str(image)).convert("RGB")
    bgr = cv2.cvtColor(np.asarray(pil), cv2.COLOR_RGB2BGR)
    H, W = bgr.shape[:2]
    g = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    e = cv2.Canny(g, 50, 150)
    segs = cv2.HoughLinesP(e, 1, np.pi / 720, threshold=55,
                           minLineLength=int(min_frac * min(H, W)), maxLineGap=6)
    out = []
    if segs is not None:
        for s in segs[:, 0, :]:
            x1, y1, x2, y2 = map(float, s)
            out.append((x1, y1, x2, y2, math.hypot(x2 - x1, y2 - y1)))
    return out, H, W


def vertical_lean(image, min_len_frac=0.18, max_off_deg=42.0):
    import math
    import numpy as np
    segs, H, W = _segs(image, min_len_frac)
    leans, wts = [], []
    for x1, y1, x2, y2, L in segs:
        if L < min_len_frac * H:
            continue
        ang = math.degrees(math.atan2(x2 - x1, -(y2 - y1)))
        ang = ((ang + 90) % 180) - 90
        if abs(ang) > max_off_deg:
            continue
        xm = (x1 + x2) / 2.0
        if abs(xm - W / 2.0) < 0.05 * W:
            continue
        side = 1.0 if xm < W / 2.0 else -1.0
        leans.append(ang * side)
        wts.append(L)
    n = len(leans)
    if n < 5:
        return {"no_read": True, "reason": "n_vert_%d" % n, "n_vert": n, "verdict": None}
    a = np.array(leans, float)
    w = np.array(wts, float)
    med = float(np.median(a))
    mean = float(np.sum(a * w) / np.sum(w))
    spread = float(np.percentile(np.abs(a - med), 75))
    if med >= 2.5:
        v = "converge_up"
    elif med <= -2.5:
        v = "converge_down"
    else:
        v = "parallel"
    return {"no_read": False, "n_vert": n, "median_inward": round(med, 2),
            "mean_inward": round(mean, 2), "spread": round(spread, 2),
            "abs_median": round(abs(med), 2), "verdict": v}


def vert_lean_overlay(image, tag="vlean"):
    import math
    import numpy as np
    import cv2
    from PIL import Image
    import hashlib
    import os
    import tempfile
    r = vertical_lean(image)
    pil = image.convert("RGB") if hasattr(image, "convert") else Image.open(str(image)).convert("RGB")
    W0, H0 = pil.size
    im = np.array(pil).copy()
    segs, H, W = _segs(image, 0.18)
    sx, sy = W0 / float(W), H0 / float(H)
    wd = max(2, int(0.004 * min(H0, W0)))
    for x1, y1, x2, y2, L in segs:
        if L < 0.18 * H:
            continue
        ang = math.degrees(math.atan2(x2 - x1, -(y2 - y1)))
        ang = ((ang + 90) % 180) - 90
        if abs(ang) > 42.0:
            continue
        cv2.line(im, (int(x1 * sx), int(y1 * sy)), (int(x2 * sx), int(y2 * sy)), (230, 40, 40), wd)
        _mk("measured_uprights", "polylines", [[x1 * sx, y1 * sy], [x2 * sx, y2 * sy]])
    cv2.line(im, (int(W0 * 0.5), int(H0 * 0.06)), (int(W0 * 0.5), int(H0 * 0.94)), (0, 175, 0), wd)
    _mk("true_plumb", "polylines", [[W0 * 0.5, H0 * 0.06], [W0 * 0.5, H0 * 0.94]])
    d = os.path.join(tempfile.gettempdir(), "genolympiad_overlay")
    try:
        os.makedirs(d, exist_ok=True)
    except Exception:
        pass
    h = hashlib.md5(("%s|%s" % (str(image), tag)).encode("utf-8", "replace")).hexdigest()[:12]
    p = os.path.join(d, "e4proj_%s_%s.png" % (tag, h))
    Image.fromarray(im).save(p)
    r = dict(r)
    r["path"] = p
    return r


def vert_lean_overlay_marked(image, tag="vlean"):
    """Draw the measured upright edges and a true plumb line, with overlay marks."""
    _mk_reset("measured_uprights", "true_plumb")
    r = dict(vert_lean_overlay(image, tag))
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

# end of code_6acd14695e1d

# shared code: code_986f2a94960b

def _segs(image, min_frac):
    import math
    import numpy as np
    import cv2
    from PIL import Image
    if hasattr(image, "convert"):
        pil = image.convert("RGB")
    else:
        pil = Image.open(str(image)).convert("RGB")
    bgr = cv2.cvtColor(np.asarray(pil), cv2.COLOR_RGB2BGR)
    H, W = bgr.shape[:2]
    g = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    e = cv2.Canny(g, 50, 150)
    segs = cv2.HoughLinesP(e, 1, np.pi / 720, threshold=55,
                           minLineLength=int(min_frac * min(H, W)), maxLineGap=6)
    out = []
    if segs is not None:
        for s in segs[:, 0, :]:
            x1, y1, x2, y2 = map(float, s)
            out.append((x1, y1, x2, y2, math.hypot(x2 - x1, y2 - y1)))
    return out, H, W


def vertical_lean(image, min_len_frac=0.18, max_off_deg=42.0):
    """Median inward lean of the upright edges, and whether they converge up or down."""
    import math
    import numpy as np
    segs, H, W = _segs(image, min_len_frac)
    leans, wts = [], []
    for x1, y1, x2, y2, L in segs:
        if L < min_len_frac * H:
            continue
        ang = math.degrees(math.atan2(x2 - x1, -(y2 - y1)))
        ang = ((ang + 90) % 180) - 90
        if abs(ang) > max_off_deg:
            continue
        xm = (x1 + x2) / 2.0
        if abs(xm - W / 2.0) < 0.05 * W:
            continue
        side = 1.0 if xm < W / 2.0 else -1.0
        leans.append(ang * side)
        wts.append(L)
    n = len(leans)
    if n < 5:
        return {"no_read": True, "reason": "n_vert_%d" % n, "n_vert": n, "verdict": None}
    a = np.array(leans, float)
    w = np.array(wts, float)
    med = float(np.median(a))
    mean = float(np.sum(a * w) / np.sum(w))
    spread = float(np.percentile(np.abs(a - med), 75))
    if med >= 2.5:
        v = "converge_up"
    elif med <= -2.5:
        v = "converge_down"
    else:
        v = "parallel"
    return {"no_read": False, "n_vert": n, "median_inward": round(med, 2),
            "mean_inward": round(mean, 2), "spread": round(spread, 2),
            "abs_median": round(abs(med), 2), "verdict": v}


def vert_lean_overlay(image, tag="vlean"):
    import math
    import numpy as np
    import cv2
    from PIL import Image
    import hashlib
    import os
    import tempfile
    r = vertical_lean(image)
    pil = image.convert("RGB") if hasattr(image, "convert") else Image.open(str(image)).convert("RGB")
    W0, H0 = pil.size
    im = np.array(pil).copy()
    segs, H, W = _segs(image, 0.18)
    sx, sy = W0 / float(W), H0 / float(H)
    wd = max(2, int(0.004 * min(H0, W0)))
    for x1, y1, x2, y2, L in segs:
        if L < 0.18 * H:
            continue
        ang = math.degrees(math.atan2(x2 - x1, -(y2 - y1)))
        ang = ((ang + 90) % 180) - 90
        if abs(ang) > 42.0:
            continue
        cv2.line(im, (int(x1 * sx), int(y1 * sy)), (int(x2 * sx), int(y2 * sy)), (230, 40, 40), wd)
    cv2.line(im, (int(W0 * 0.5), int(H0 * 0.06)), (int(W0 * 0.5), int(H0 * 0.94)), (0, 175, 0), wd)
    d = os.path.join(tempfile.gettempdir(), "genolympiad_overlay")
    try:
        os.makedirs(d, exist_ok=True)
    except Exception:
        pass
    h = hashlib.md5(("%s|%s" % (str(image), tag)).encode("utf-8", "replace")).hexdigest()[:12]
    p = os.path.join(d, "e4proj_%s_%s.png" % (tag, h))
    Image.fromarray(im).save(p)
    r = dict(r)
    r["path"] = p
    return r

# end of code_986f2a94960b

# code: f_code
def downward_lean_score(median_lean):
    """Score how far the median lean shows edges converging downward, full at 4.5 degrees."""
    if median_lean is None: return 0.0
    return round(max(0.0, min(1.0, (-float(median_lean) - 1.5) / 3.0)), 4)

# end of f_code
