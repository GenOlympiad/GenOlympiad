# code: view_panels_code

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


def _panels_at(m, H, W, k):
    import numpy as np
    import cv2
    ker = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k))
    d = cv2.dilate(cv2.morphologyEx(m, cv2.MORPH_CLOSE, ker), ker)
    n, lbl, st, ce = cv2.connectedComponentsWithStats(d, 8)
    out = []
    for i in range(1, n):
        sel = (lbl == i) & (m > 0)
        if int(sel.sum()) < 0.0012 * H * W:
            continue
        ys, xs = np.nonzero(sel)
        if xs.size == 0:
            continue
        x0, x1 = int(xs.min()), int(xs.max())
        y0, y1 = int(ys.min()), int(ys.max())
        if (x1 - x0) < 0.04 * W or (y1 - y0) < 0.04 * H:
            continue
        out.append({"x0": x0, "y0": y0, "x1": x1, "y1": y1,
                    "w": x1 - x0 + 1, "h": y1 - y0 + 1,
                    "cx": 0.5 * (x0 + x1), "cy": 0.5 * (y0 + y1), "ink": int(sel.sum()),
                    "_lbl": int(i)})
    out.sort(key=lambda p: -p["w"] * p["h"])
    keep = []
    for p in out:
        inside = any((q["x0"] <= p["x0"] and q["y0"] <= p["y0"]
                      and q["x1"] >= p["x1"] and q["y1"] >= p["y1"]) for q in keep)
        if not inside:
            keep.append(p)
    return keep, lbl


def view_panels(image, n_want=3):
    """Find the front, top and side view panels and compare their shared sizes."""
    import numpy as np
    import cv2
    bgr, gray, m, H, W, OW, OH = _prep(image)
    base = min(H, W)
    got = None
    for f in (0.022, 0.016, 0.030, 0.040, 0.012, 0.055):
        k = int(base * f)
        k = k + 1 if k % 2 == 0 else k
        if k < 5:
            continue
        P, lbl = _panels_at(m, H, W, k)
        if len(P) == n_want:
            got = (P, lbl, f)
            break
        if got is None and len(P) >= 2:
            got = (P, lbl, f)
    if got is None:
        return {"no_read": True, "reason": "no_panels", "n_panels": 0}
    P, lbl, used = got
    if len(P) != n_want:
        return {"no_read": True, "reason": "n_panels_%d_want_%d" % (len(P), n_want),
                "n_panels": len(P)}

    def near_x(a, b):
        return abs(a["cx"] - b["cx"]) < 0.42 * max(a["w"], b["w"])

    def near_y(a, b):
        return abs(a["cy"] - b["cy"]) < 0.42 * max(a["h"], b["h"])

    front = stack = side = None
    for i, a in enumerate(P):
        s_ = [b for j, b in enumerate(P) if j != i and near_x(a, b) and not near_y(a, b)]
        h_ = [b for j, b in enumerate(P) if j != i and near_y(a, b) and not near_x(a, b)]
        if s_ and h_:
            front, stack, side = a, s_[0], h_[0]
            break
    if front is None:
        return {"no_read": True, "reason": "no_cross_layout", "n_panels": len(P),
                "panels": [{k: v for k, v in p.items() if not k.startswith("_")} for p in P]}
    depth_top = float(stack["h"])
    depth_side = float(side["w"])
    denom = 0.5 * (depth_top + depth_side)
    out = {"no_read": False, "n_panels": len(P), "close_frac": used,
           "front": {k: v for k, v in front.items() if not k.startswith("_")},
           "stack": {k: v for k, v in stack.items() if not k.startswith("_")},
           "side": {k: v for k, v in side.items() if not k.startswith("_")},
           "stack_is_above": bool(stack["cy"] < front["cy"]),
           "side_is_right": bool(side["cx"] > front["cx"]),
           "depth_top": round(depth_top, 1), "depth_side": round(depth_side, 1),
           "depth_mismatch": round(abs(depth_top - depth_side) / denom, 4) if denom else None,
           "width_mismatch": round(abs(front["w"] - stack["w"])
                                   / (0.5 * (front["w"] + stack["w"])), 4),
           "height_mismatch": round(abs(front["h"] - side["h"])
                                    / (0.5 * (front["h"] + side["h"])), 4),
           "img_w": W, "img_h": H, "orig_w": OW, "orig_h": OH}
    return out


def side_handedness(image, n_want=3, band=0.30):
    import numpy as np
    vp = view_panels(image, n_want=n_want)
    if vp.get("no_read"):
        return {"no_read": True, "reason": vp.get("reason"), "foot_dir": 0}
    bgr, gray, m, H, W, OW, OH = _prep(image)
    s = vp["side"]
    x0, x1, y0, y1 = s["x0"], s["x1"], s["y0"], s["y1"]
    sub = m[y0:y1 + 1, x0:x1 + 1]
    h, w = sub.shape
    nb = max(4, int(band * h))
    top = sub[:nb]
    bot = sub[h - nb:]
    ys_t, xs_t = np.nonzero(top)
    ys_b, xs_b = np.nonzero(bot)
    if xs_t.size < 20 or xs_b.size < 20:
        return {"no_read": True, "reason": "thin_bands", "foot_dir": 0}
    mt = float(xs_t.mean())
    mb = float(xs_b.mean())
    off = (mb - mt) / float(w)
    d = 1 if off > 0.055 else (-1 if off < -0.055 else 0)
    return {"no_read": False, "foot_offset": round(off, 4), "foot_dir": d,
            "top_mean_x": round(mt / w, 4), "bot_mean_x": round(mb / w, 4),
            "side_is_right": vp["side_is_right"], "stack_is_above": vp["stack_is_above"],
            "panel": s, "img_w": W, "img_h": H, "orig_w": OW, "orig_h": OH}


def panel_overlay(image, tag="panels", want_dir=0):
    import numpy as np
    import cv2
    from PIL import Image
    vp = view_panels(image)
    hd = side_handedness(image)
    pil = _pil(image)
    W0, H0 = pil.size
    im = np.array(pil).copy()
    if not vp.get("no_read"):
        sx, sy = W0 / float(vp["img_w"]), H0 / float(vp["img_h"])
        w = max(2, int(0.004 * min(H0, W0)))
        cols = {"front": (30, 120, 235), "stack": (200, 120, 0), "side": (150, 40, 190)}
        for role in ("front", "stack", "side"):
            p = vp[role]
            cv2.rectangle(im, (int(p["x0"] * sx), int(p["y0"] * sy)),
                          (int(p["x1"] * sx), int(p["y1"] * sy)), cols[role], w)
            cv2.putText(im, role.upper(), (int(p["x0"] * sx), max(18, int(p["y0"] * sy) - 8)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.9 * min(W0, H0) / 1024.0, cols[role], w)
        st, sd = vp["stack"], vp["side"]
        cv2.line(im, (int((st["x0"] - 14) * sx), int(st["y0"] * sy)),
                 (int((st["x0"] - 14) * sx), int(st["y1"] * sy)), (230, 40, 40), w + 2)
        cv2.line(im, (int(sd["x0"] * sx), int((sd["y1"] + 14) * sy)),
                 (int(sd["x1"] * sx), int((sd["y1"] + 14) * sy)), (230, 40, 40), w + 2)
        if not hd.get("no_read"):
            p = vp["side"]
            ymid = int((p["y1"] - 0.12 * p["h"]) * sy)
            xc = int(p["cx"] * sx)
            L = int(0.32 * p["w"] * sx)
            dmeas = hd["foot_dir"] or 1
            cv2.arrowedLine(im, (xc, ymid), (xc + dmeas * L, ymid), (230, 40, 40), w + 1,
                            tipLength=0.3)
            if want_dir:
                cv2.arrowedLine(im, (xc, ymid + int(0.06 * p["h"] * sy)),
                                (xc + int(want_dir) * L, ymid + int(0.06 * p["h"] * sy)),
                                (0, 175, 0), w + 1, tipLength=0.3)
    p = _overlay_path(image, tag)
    Image.fromarray(im).save(p)
    out = dict(vp)
    out["hand"] = hd
    out["path"] = p
    return out

# end of view_panels_code

# code: panel_overlay_marked_code

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


def _panels_at(m, H, W, k):
    import numpy as np
    import cv2
    ker = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k))
    d = cv2.dilate(cv2.morphologyEx(m, cv2.MORPH_CLOSE, ker), ker)
    n, lbl, st, ce = cv2.connectedComponentsWithStats(d, 8)
    out = []
    for i in range(1, n):
        sel = (lbl == i) & (m > 0)
        if int(sel.sum()) < 0.0012 * H * W:
            continue
        ys, xs = np.nonzero(sel)
        if xs.size == 0:
            continue
        x0, x1 = int(xs.min()), int(xs.max())
        y0, y1 = int(ys.min()), int(ys.max())
        if (x1 - x0) < 0.04 * W or (y1 - y0) < 0.04 * H:
            continue
        out.append({"x0": x0, "y0": y0, "x1": x1, "y1": y1,
                    "w": x1 - x0 + 1, "h": y1 - y0 + 1,
                    "cx": 0.5 * (x0 + x1), "cy": 0.5 * (y0 + y1), "ink": int(sel.sum()),
                    "_lbl": int(i)})
    out.sort(key=lambda p: -p["w"] * p["h"])
    keep = []
    for p in out:
        inside = any((q["x0"] <= p["x0"] and q["y0"] <= p["y0"]
                      and q["x1"] >= p["x1"] and q["y1"] >= p["y1"]) for q in keep)
        if not inside:
            keep.append(p)
    return keep, lbl


def view_panels(image, n_want=3):
    import numpy as np
    import cv2
    bgr, gray, m, H, W, OW, OH = _prep(image)
    base = min(H, W)
    got = None
    for f in (0.022, 0.016, 0.030, 0.040, 0.012, 0.055):
        k = int(base * f)
        k = k + 1 if k % 2 == 0 else k
        if k < 5:
            continue
        P, lbl = _panels_at(m, H, W, k)
        if len(P) == n_want:
            got = (P, lbl, f)
            break
        if got is None and len(P) >= 2:
            got = (P, lbl, f)
    if got is None:
        return {"no_read": True, "reason": "no_panels", "n_panels": 0}
    P, lbl, used = got
    if len(P) != n_want:
        return {"no_read": True, "reason": "n_panels_%d_want_%d" % (len(P), n_want),
                "n_panels": len(P)}

    def near_x(a, b):
        return abs(a["cx"] - b["cx"]) < 0.42 * max(a["w"], b["w"])

    def near_y(a, b):
        return abs(a["cy"] - b["cy"]) < 0.42 * max(a["h"], b["h"])

    front = stack = side = None
    for i, a in enumerate(P):
        s_ = [b for j, b in enumerate(P) if j != i and near_x(a, b) and not near_y(a, b)]
        h_ = [b for j, b in enumerate(P) if j != i and near_y(a, b) and not near_x(a, b)]
        if s_ and h_:
            front, stack, side = a, s_[0], h_[0]
            break
    if front is None:
        return {"no_read": True, "reason": "no_cross_layout", "n_panels": len(P),
                "panels": [{k: v for k, v in p.items() if not k.startswith("_")} for p in P]}
    depth_top = float(stack["h"])
    depth_side = float(side["w"])
    denom = 0.5 * (depth_top + depth_side)
    out = {"no_read": False, "n_panels": len(P), "close_frac": used,
           "front": {k: v for k, v in front.items() if not k.startswith("_")},
           "stack": {k: v for k, v in stack.items() if not k.startswith("_")},
           "side": {k: v for k, v in side.items() if not k.startswith("_")},
           "stack_is_above": bool(stack["cy"] < front["cy"]),
           "side_is_right": bool(side["cx"] > front["cx"]),
           "depth_top": round(depth_top, 1), "depth_side": round(depth_side, 1),
           "depth_mismatch": round(abs(depth_top - depth_side) / denom, 4) if denom else None,
           "width_mismatch": round(abs(front["w"] - stack["w"])
                                   / (0.5 * (front["w"] + stack["w"])), 4),
           "height_mismatch": round(abs(front["h"] - side["h"])
                                    / (0.5 * (front["h"] + side["h"])), 4),
           "img_w": W, "img_h": H, "orig_w": OW, "orig_h": OH}
    return out


def side_handedness(image, n_want=3, band=0.30):
    import numpy as np
    vp = view_panels(image, n_want=n_want)
    if vp.get("no_read"):
        return {"no_read": True, "reason": vp.get("reason"), "foot_dir": 0}
    bgr, gray, m, H, W, OW, OH = _prep(image)
    s = vp["side"]
    x0, x1, y0, y1 = s["x0"], s["x1"], s["y0"], s["y1"]
    sub = m[y0:y1 + 1, x0:x1 + 1]
    h, w = sub.shape
    nb = max(4, int(band * h))
    top = sub[:nb]
    bot = sub[h - nb:]
    ys_t, xs_t = np.nonzero(top)
    ys_b, xs_b = np.nonzero(bot)
    if xs_t.size < 20 or xs_b.size < 20:
        return {"no_read": True, "reason": "thin_bands", "foot_dir": 0}
    mt = float(xs_t.mean())
    mb = float(xs_b.mean())
    off = (mb - mt) / float(w)
    d = 1 if off > 0.055 else (-1 if off < -0.055 else 0)
    return {"no_read": False, "foot_offset": round(off, 4), "foot_dir": d,
            "top_mean_x": round(mt / w, 4), "bot_mean_x": round(mb / w, 4),
            "side_is_right": vp["side_is_right"], "stack_is_above": vp["stack_is_above"],
            "panel": s, "img_w": W, "img_h": H, "orig_w": OW, "orig_h": OH}


def panel_overlay(image, tag="panels", want_dir=0):
    import numpy as np
    import cv2
    from PIL import Image
    vp = view_panels(image)
    hd = side_handedness(image)
    pil = _pil(image)
    W0, H0 = pil.size
    im = np.array(pil).copy()
    if not vp.get("no_read"):
        sx, sy = W0 / float(vp["img_w"]), H0 / float(vp["img_h"])
        w = max(2, int(0.004 * min(H0, W0)))
        cols = {"front": (30, 120, 235), "stack": (200, 120, 0), "side": (150, 40, 190)}
        for role in ("front", "stack", "side"):
            p = vp[role]
            cv2.rectangle(im, (int(p["x0"] * sx), int(p["y0"] * sy)),
                          (int(p["x1"] * sx), int(p["y1"] * sy)), cols[role], w)
            _mk("panel_" + role, "rects",
                [0.5 * (p["x0"] + p["x1"]) * sx, 0.5 * (p["y0"] + p["y1"]) * sy,
                 (p["x1"] - p["x0"]) * sx, (p["y1"] - p["y0"]) * sy])
            cv2.putText(im, role.upper(), (int(p["x0"] * sx), max(18, int(p["y0"] * sy) - 8)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.9 * min(W0, H0) / 1024.0, cols[role], w)
        st, sd = vp["stack"], vp["side"]
        cv2.line(im, (int((st["x0"] - 14) * sx), int(st["y0"] * sy)),
                 (int((st["x0"] - 14) * sx), int(st["y1"] * sy)), (230, 40, 40), w + 2)
        _mk("depth_bars", "polylines", [[(st["x0"] - 14) * sx, st["y0"] * sy],
                                        [(st["x0"] - 14) * sx, st["y1"] * sy]])
        cv2.line(im, (int(sd["x0"] * sx), int((sd["y1"] + 14) * sy)),
                 (int(sd["x1"] * sx), int((sd["y1"] + 14) * sy)), (230, 40, 40), w + 2)
        _mk("depth_bars", "polylines", [[sd["x0"] * sx, (sd["y1"] + 14) * sy],
                                        [sd["x1"] * sx, (sd["y1"] + 14) * sy]])
        if not hd.get("no_read"):
            p = vp["side"]
            ymid = int((p["y1"] - 0.12 * p["h"]) * sy)
            xc = int(p["cx"] * sx)
            L = int(0.32 * p["w"] * sx)
            dmeas = hd["foot_dir"] or 1
            cv2.arrowedLine(im, (xc, ymid), (xc + dmeas * L, ymid), (230, 40, 40), w + 1,
                            tipLength=0.3)
            _mk("depth_bars", "polylines", _arrow_pts(xc, ymid, xc + dmeas * L, ymid))
            if want_dir:
                cv2.arrowedLine(im, (xc, ymid + int(0.06 * p["h"] * sy)),
                                (xc + int(want_dir) * L, ymid + int(0.06 * p["h"] * sy)),
                                (0, 175, 0), w + 1, tipLength=0.3)
                _mk("want_foot", "polylines",
                    _arrow_pts(xc, ymid + 0.06 * p["h"] * sy,
                               xc + int(want_dir) * L, ymid + 0.06 * p["h"] * sy))
    p = _overlay_path(image, tag)
    Image.fromarray(im).save(p)
    out = dict(vp)
    out["hand"] = hd
    out["path"] = p
    return out


def panel_overlay_marked(image, tag="panels", want_dir=0):
    """Draw the found view panels and depth bars on the image."""
    _mk_reset("panel_front", "panel_stack", "panel_side", "depth_bars", "want_foot")
    r = dict(panel_overlay(image, tag, want_dir))
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

# end of panel_overlay_marked_code

# code: f_code
def views_on_wanted_sides(above, right, want_above, want_right):
    """1.0 if the top view sits above and the side view to the right as wanted."""
    return 1.0 if (bool(above) == bool(want_above)
                   and bool(right) == bool(want_right)) else 0.0

# end of f_code
