# code: oblique_metrics_code

def _pil(image):
    from PIL import Image
    return image.convert("RGB") if hasattr(image, "convert") else Image.open(str(image)).convert("RGB")


def _prep(image, cap=1600):
    import numpy as np
    import cv2
    pil = _pil(image)
    rgb = np.asarray(pil)
    OH, OW = rgb.shape[:2]
    bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    H, W = bgr.shape[:2]
    if max(H, W) > cap:
        s = float(cap) / max(H, W)
        bgr = cv2.resize(bgr, (int(W * s), int(H * s)), interpolation=cv2.INTER_AREA)
        H, W = bgr.shape[:2]
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    _, th = cv2.threshold(cv2.GaussianBlur(gray, (3, 3), 0), 0, 255,
                          cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    m = (th > 0).astype(np.uint8)
    if float(m.mean()) > 0.5:
        m = (1 - m).astype(np.uint8)
    return bgr, gray, m, H, W, OW, OH


def _segments(image, min_len_frac=0.06, thr=40, gap=4):
    import math
    import numpy as np
    import cv2
    bgr, gray, m, H, W, _OW, _OH = _prep(image)
    e = cv2.Canny(gray, 50, 150)
    mn = max(12, int(min_len_frac * min(H, W)))
    L = cv2.HoughLinesP(e, 1, np.pi / 720, threshold=thr, minLineLength=mn, maxLineGap=gap)
    out = []
    if L is not None:
        for x1, y1, x2, y2 in L[:, 0, :]:
            out.append((float(x1), float(y1), float(x2), float(y2),
                        math.hypot(float(x2) - float(x1), float(y2) - float(y1))))
    return out, H, W


def _fold(a):
    return ((a + 90.0) % 180.0) - 90.0


def _ang_of(x1, y1, x2, y2):
    import math
    return _fold(math.degrees(math.atan2(y2 - y1, x2 - x1)))


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
    return os.path.join(d, "e4proj_%s_%s.png" % (tag, h))


def _merge_collinear(segs, H, W, ang_tol=3.0, off_tol_frac=0.007):
    import math
    off_tol = off_tol_frac * min(H, W)
    groups = []
    for x1, y1, x2, y2, _L in segs:
        a = _ang_of(x1, y1, x2, y2)
        th = math.radians(a)
        ux, uy = math.cos(th), math.sin(th)
        nx, ny = -uy, ux
        off = x1 * nx + y1 * ny
        t1, t2 = x1 * ux + y1 * uy, x2 * ux + y2 * uy
        lo_, hi_ = min(t1, t2), max(t1, t2)
        hit = None
        for g in groups:
            da = abs(((a - g["a"] + 90.0) % 180.0) - 90.0)
            if da <= ang_tol and abs(off - g["off"]) <= off_tol:
                hit = g
                break
        if hit is None:
            groups.append({"a": a, "off": off, "t0": lo_, "t1": hi_, "n": 1})
        else:
            hit["t0"] = min(hit["t0"], lo_)
            hit["t1"] = max(hit["t1"], hi_)
            hit["n"] += 1
    return [(g["a"], g["t1"] - g["t0"]) for g in groups]


def oblique_metrics(image, min_len_frac=0.05, flat_deg=2.5, dep_lo=18.0, dep_hi=72.0):
    """Measure front edge lengths, depth edge angle and depth ratio from the drawn lines."""
    import math
    import numpy as np
    segs, H, W = _segments(image, 0.5 * min_len_frac)
    lim = min_len_frac * min(H, W)
    hz, vt, dep = [], [], []
    for a, L in _merge_collinear(segs, H, W):
        if L < lim:
            continue
        if abs(a) <= flat_deg:
            hz.append(L)
        elif abs(a) >= 90.0 - flat_deg:
            vt.append(L)
        elif dep_lo <= abs(a) <= dep_hi:
            dep.append((a, L))
    if len(hz) < 2 or len(vt) < 2 or len(dep) < 2:
        return {"no_read": True, "reason": "n_h%d_v%d_d%d" % (len(hz), len(vt), len(dep)),
                "n_h": len(hz), "n_v": len(vt), "n_dep": len(dep)}
    hzp = float(np.percentile(np.array(hz, float), 90))
    vtp = float(np.percentile(np.array(vt, float), 90))
    front = 0.5 * (hzp + vtp)
    DA = np.array([d[0] for d in dep], float)
    DL = np.array([d[1] for d in dep], float)
    dep_len = float(np.percentile(DL, 85))
    med = float(np.median(np.abs(DA)))
    return {"no_read": False, "n_h": len(hz), "n_v": len(vt), "n_dep": len(dep),
            "front_h_p90": round(hzp, 1), "front_v_p90": round(vtp, 1),
            "front_edge": round(front, 1), "front_squareness": round(min(hzp, vtp) / max(hzp, vtp), 4),
            "depth_len_p85": round(dep_len, 1), "depth_len_max": round(float(DL.max()), 1),
            "depth_ang": round(med, 2),
            "depth_ang_spread": round(float(np.percentile(np.abs(np.abs(DA) - med), 80)), 2),
            "depth_ratio": round(dep_len / front, 4),
            "depth_ratio_max": round(float(DL.max()) / front, 4),
            "img_w": W, "img_h": H}


def oblique_overlay(image, tag="oblq"):
    import math
    import numpy as np
    import cv2
    from PIL import Image
    r = oblique_metrics(image)
    pil = _pil(image)
    W0, H0 = pil.size
    im = np.array(pil).copy()
    if not r.get("no_read"):
        s = 0.5 * (W0 / float(r["img_w"]) + H0 / float(r["img_h"]))
        w = max(2, int(0.005 * min(H0, W0)))
        ox, oy = int(0.06 * W0), int(0.95 * H0)
        fe = r["front_edge"] * s
        cv2.line(im, (ox, oy), (ox + int(fe), oy), (30, 120, 235), w)
        th = math.radians(r["depth_ang"])
        dl = r["depth_len_p85"] * s
        cv2.line(im, (ox, oy), (ox + int(dl * math.cos(th)), oy - int(dl * math.sin(th))),
                 (230, 40, 40), w)
        want = 0.5 * fe
        cv2.line(im, (ox, oy), (ox + int(want * math.cos(math.radians(45.0))),
                                oy - int(want * math.sin(math.radians(45.0)))), (0, 175, 0), w)
    p = _overlay_path(image, tag)
    Image.fromarray(im).save(p)
    r = dict(r)
    r["path"] = p
    return r

# end of oblique_metrics_code

# code: f_code
def front_face_check(n_horizontal, n_vertical, squareness):
    """1.0 if two flat and two upright front edges are found and the face is square."""
    return 1.0 if (int(n_horizontal) >= 2 and int(n_vertical) >= 2
                   and float(squareness) >= 0.72) else 0.0

# end of f_code

# code: oblique_overlay_marked_code

def _pil(image):
    from PIL import Image
    return image.convert("RGB") if hasattr(image, "convert") else Image.open(str(image)).convert("RGB")


def _prep(image, cap=1600):
    import numpy as np
    import cv2
    pil = _pil(image)
    rgb = np.asarray(pil)
    OH, OW = rgb.shape[:2]
    bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    H, W = bgr.shape[:2]
    if max(H, W) > cap:
        s = float(cap) / max(H, W)
        bgr = cv2.resize(bgr, (int(W * s), int(H * s)), interpolation=cv2.INTER_AREA)
        H, W = bgr.shape[:2]
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    _, th = cv2.threshold(cv2.GaussianBlur(gray, (3, 3), 0), 0, 255,
                          cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    m = (th > 0).astype(np.uint8)
    if float(m.mean()) > 0.5:
        m = (1 - m).astype(np.uint8)
    return bgr, gray, m, H, W, OW, OH


def _segments(image, min_len_frac=0.06, thr=40, gap=4):
    import math
    import numpy as np
    import cv2
    bgr, gray, m, H, W, _OW, _OH = _prep(image)
    e = cv2.Canny(gray, 50, 150)
    mn = max(12, int(min_len_frac * min(H, W)))
    L = cv2.HoughLinesP(e, 1, np.pi / 720, threshold=thr, minLineLength=mn, maxLineGap=gap)
    out = []
    if L is not None:
        for x1, y1, x2, y2 in L[:, 0, :]:
            out.append((float(x1), float(y1), float(x2), float(y2),
                        math.hypot(float(x2) - float(x1), float(y2) - float(y1))))
    return out, H, W


def _fold(a):
    return ((a + 90.0) % 180.0) - 90.0


def _ang_of(x1, y1, x2, y2):
    import math
    return _fold(math.degrees(math.atan2(y2 - y1, x2 - x1)))


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
    return os.path.join(d, "e4proj_%s_%s.png" % (tag, h))


def _merge_collinear(segs, H, W, ang_tol=3.0, off_tol_frac=0.007):
    import math
    off_tol = off_tol_frac * min(H, W)
    groups = []
    for x1, y1, x2, y2, _L in segs:
        a = _ang_of(x1, y1, x2, y2)
        th = math.radians(a)
        ux, uy = math.cos(th), math.sin(th)
        nx, ny = -uy, ux
        off = x1 * nx + y1 * ny
        t1, t2 = x1 * ux + y1 * uy, x2 * ux + y2 * uy
        lo_, hi_ = min(t1, t2), max(t1, t2)
        hit = None
        for g in groups:
            da = abs(((a - g["a"] + 90.0) % 180.0) - 90.0)
            if da <= ang_tol and abs(off - g["off"]) <= off_tol:
                hit = g
                break
        if hit is None:
            groups.append({"a": a, "off": off, "t0": lo_, "t1": hi_, "n": 1})
        else:
            hit["t0"] = min(hit["t0"], lo_)
            hit["t1"] = max(hit["t1"], hi_)
            hit["n"] += 1
    return [(g["a"], g["t1"] - g["t0"]) for g in groups]


def oblique_metrics(image, min_len_frac=0.05, flat_deg=2.5, dep_lo=18.0, dep_hi=72.0):
    import math
    import numpy as np
    segs, H, W = _segments(image, 0.5 * min_len_frac)
    lim = min_len_frac * min(H, W)
    hz, vt, dep = [], [], []
    for a, L in _merge_collinear(segs, H, W):
        if L < lim:
            continue
        if abs(a) <= flat_deg:
            hz.append(L)
        elif abs(a) >= 90.0 - flat_deg:
            vt.append(L)
        elif dep_lo <= abs(a) <= dep_hi:
            dep.append((a, L))
    if len(hz) < 2 or len(vt) < 2 or len(dep) < 2:
        return {"no_read": True, "reason": "n_h%d_v%d_d%d" % (len(hz), len(vt), len(dep)),
                "n_h": len(hz), "n_v": len(vt), "n_dep": len(dep)}
    hzp = float(np.percentile(np.array(hz, float), 90))
    vtp = float(np.percentile(np.array(vt, float), 90))
    front = 0.5 * (hzp + vtp)
    DA = np.array([d[0] for d in dep], float)
    DL = np.array([d[1] for d in dep], float)
    dep_len = float(np.percentile(DL, 85))
    med = float(np.median(np.abs(DA)))
    return {"no_read": False, "n_h": len(hz), "n_v": len(vt), "n_dep": len(dep),
            "front_h_p90": round(hzp, 1), "front_v_p90": round(vtp, 1),
            "front_edge": round(front, 1), "front_squareness": round(min(hzp, vtp) / max(hzp, vtp), 4),
            "depth_len_p85": round(dep_len, 1), "depth_len_max": round(float(DL.max()), 1),
            "depth_ang": round(med, 2),
            "depth_ang_spread": round(float(np.percentile(np.abs(np.abs(DA) - med), 80)), 2),
            "depth_ratio": round(dep_len / front, 4),
            "depth_ratio_max": round(float(DL.max()) / front, 4),
            "img_w": W, "img_h": H}


def oblique_overlay(image, tag="oblq"):
    import math
    import numpy as np
    import cv2
    from PIL import Image
    r = oblique_metrics(image)
    pil = _pil(image)
    W0, H0 = pil.size
    im = np.array(pil).copy()
    if not r.get("no_read"):
        s = 0.5 * (W0 / float(r["img_w"]) + H0 / float(r["img_h"]))
        w = max(2, int(0.005 * min(H0, W0)))
        ox, oy = int(0.06 * W0), int(0.95 * H0)
        fe = r["front_edge"] * s
        cv2.line(im, (ox, oy), (ox + int(fe), oy), (30, 120, 235), w)
        _mk("front", "polylines", [[ox, oy], [ox + fe, oy]])
        th = math.radians(r["depth_ang"])
        dl = r["depth_len_p85"] * s
        cv2.line(im, (ox, oy), (ox + int(dl * math.cos(th)), oy - int(dl * math.sin(th))),
                 (230, 40, 40), w)
        _mk("depth", "polylines",
            [[ox, oy], [ox + dl * math.cos(th), oy - dl * math.sin(th)]])
        want = 0.5 * fe
        cv2.line(im, (ox, oy), (ox + int(want * math.cos(math.radians(45.0))),
                                oy - int(want * math.sin(math.radians(45.0)))), (0, 175, 0), w)
        _mk("want", "polylines",
            [[ox, oy], [ox + want * math.cos(math.radians(45.0)),
                        oy - want * math.sin(math.radians(45.0))]])
    p = _overlay_path(image, tag)
    Image.fromarray(im).save(p)
    r = dict(r)
    r["path"] = p
    return r


def oblique_overlay_marked(image, tag="oblq"):
    """Draw the measured front edge, depth edge and wanted half depth on the image."""
    _mk_reset("front", "depth", "want")
    r = dict(oblique_overlay(image, tag))
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

# end of oblique_overlay_marked_code
