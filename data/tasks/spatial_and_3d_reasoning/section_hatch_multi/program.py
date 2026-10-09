# code: hatch_map_code

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


def _region_angle(m_region, crop_shape):
    import math
    import numpy as np
    import cv2
    ys, xs = np.nonzero(m_region)
    if xs.size < 60:
        return None
    canvas = (255 - (m_region * 255)).astype(np.uint8)
    e = cv2.Canny(canvas, 50, 150)
    h, w = m_region.shape
    L = None
    for frac, thr in ((0.30, 18), (0.18, 14), (0.10, 10)):
        mn = max(8, int(frac * min(h, w)))
        L = cv2.HoughLinesP(e, 1, np.pi / 720, threshold=thr, minLineLength=mn, maxLineGap=3)
        if L is not None and len(L) >= 3:
            break
    if L is None or len(L) < 3:
        return None
    A = np.array([math.degrees(math.atan2(float(b2) - float(b1), float(a2) - float(a1))) % 180.0
                  for a1, b1, a2, b2 in L[:, 0, :]], float)
    dbl = np.deg2rad(A * 2.0)
    dom = (math.degrees(math.atan2(float(np.sin(dbl).mean()),
                                   float(np.cos(dbl).mean()))) / 2.0) % 180.0
    dev = np.minimum((A - dom) % 180.0, (dom - A) % 180.0)
    keep = int((dev < 12.0).sum())
    if keep < 3:
        return None
    th = math.radians(dom)
    perp = (math.cos(th + math.pi / 2), math.sin(th + math.pi / 2))
    proj = xs * perp[0] + ys * perp[1]
    span = float(proj.max() - proj.min())
    pitch = None
    if span > 8:
        hist, edg = np.histogram(proj, bins=max(20, int(span / 2)))
        thr = hist.max() * 0.35
        peaks = []
        for i in range(1, len(hist) - 1):
            if hist[i] >= thr and hist[i] >= hist[i - 1] and hist[i] >= hist[i + 1]:
                c = 0.5 * (edg[i] + edg[i + 1])
                if peaks and abs(c - peaks[-1]) < span * 0.02:
                    continue
                peaks.append(c)
        if len(peaks) >= 3:
            g = np.diff(np.array(peaks, float))
            pitch = float(g.mean())
    return {"angle": round(dom, 2), "n_lines": int(keep), "pitch": (None if pitch is None
                                                                    else round(pitch, 2))}


def hatch_map(image, n_parts=4, min_region_frac=0.006):
    """Find the walled parts, their hatch angles and the angle gaps between touching parts."""
    import math
    import numpy as np
    import cv2
    bgr, gray, m, H, W, OW, OH = _prep(image)
    if float(m.mean()) < 0.02:
        return {"no_read": True, "reason": "almost_no_ink", "n_regions": 0}
    best = None
    for t in (2, 3, 1, 4):
        ker = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * t + 1, 2 * t + 1))
        thick = cv2.dilate(cv2.erode(m, ker), ker)
        frac = float(thick.sum()) / max(1.0, float(m.sum()))
        if not (0.02 <= frac <= 0.80):
            continue
        walls = cv2.dilate(thick, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)))
        interior = (1 - walls).astype(np.uint8)
        n, lbl, st, ce = cv2.connectedComponentsWithStats(interior, 4)
        border = set(np.unique(np.concatenate([lbl[0], lbl[-1], lbl[:, 0], lbl[:, -1]])).tolist())
        regs = []
        for i in range(1, n):
            if i in border:
                continue
            if int(st[i, cv2.CC_STAT_AREA]) < min_region_frac * H * W:
                continue
            regs.append(i)
        if len(regs) >= max(2, n_parts):
            best = (thick, walls, lbl, regs, t)
            break
    if best is None:
        return {"no_read": True, "reason": "no_walled_regions", "n_regions": 0}
    thick, walls, lbl, regs, t = best
    out_regs = []
    n_blank = 0
    for i in regs:
        sel = (lbl == i)
        ys, xs = np.nonzero(sel)
        y0, y1, x0, x1 = int(ys.min()), int(ys.max()), int(xs.min()), int(xs.max())
        strokes = (sel & (m > 0)).astype(np.uint8)[y0:y1 + 1, x0:x1 + 1]
        if float((sel & (m > 0)).sum()) / max(1.0, float(sel.sum())) < 0.02:
            n_blank += 1
            continue
        r = _region_angle(strokes, (y1 - y0 + 1, x1 - x0 + 1))
        if r is None:
            continue
        r.update({"lab": int(i), "x0": x0, "y0": y0, "x1": x1, "y1": y1,
                  "cx": round(0.5 * (x0 + x1) / W, 4), "cy": round(0.5 * (y0 + y1) / H, 4),
                  "area": int(sel.sum())})
        out_regs.append(r)
    if len(out_regs) < max(2, n_parts):
        return {"no_read": True, "reason": "n_hatched_%d_lt_%d" % (len(out_regs), n_parts),
                "n_regions": len(out_regs), "n_blank": n_blank}

    def gap(a, b):
        d = abs(a - b) % 180.0
        return min(d, 180.0 - d)

    rad = max(5, 2 * t + int(0.010 * min(H, W)))
    kad = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * rad + 1, 2 * rad + 1))
    masks = {}
    for r in out_regs:
        masks[r["lab"]] = cv2.dilate((lbl == r["lab"]).astype(np.uint8), kad)
    pairs = []
    for i in range(len(out_regs)):
        for j in range(i + 1, len(out_regs)):
            a, b = out_regs[i], out_regs[j]
            ov = int((masks[a["lab"]] & masks[b["lab"]]).sum())
            if ov < 40:
                continue
            pairs.append({"a": a["lab"], "b": b["lab"], "overlap": ov,
                          "gap": round(gap(a["angle"], b["angle"]), 2)})
    angs = sorted(r["angle"] for r in out_regs)
    clusters = []
    for a in angs:
        if clusters and gap(a, clusters[-1][-1]) <= 12.0:
            clusters[-1].append(a)
        else:
            clusters.append([a])
    if len(clusters) > 1 and gap(clusters[0][0], clusters[-1][-1]) <= 12.0:
        clusters[0] = clusters[-1] + clusters[0]
        clusters.pop()
    sizes = sorted((len(c) for c in clusters), reverse=True)
    return {"no_read": False, "n_regions": len(out_regs), "thick_scale": t, "n_blank": n_blank,
            "regions": out_regs, "pairs": pairs, "n_pairs": len(pairs),
            "min_adjacent_gap": (round(min(p["gap"] for p in pairs), 2) if pairs else None),
            "n_clusters": len(clusters), "cluster_sizes": sizes,
            "angles": [r["angle"] for r in out_regs],
            "img_w": W, "img_h": H, "orig_w": OW, "orig_h": OH}


def hatch_overlay(image, n_parts=4, tag="hatch"):
    import numpy as np
    import cv2
    from PIL import Image
    r = hatch_map(image, n_parts=n_parts)
    pil = _pil(image)
    W0, H0 = pil.size
    im = np.array(pil).copy()
    if not r.get("no_read"):
        sx, sy = W0 / float(r["img_w"]), H0 / float(r["img_h"])
        w = max(2, int(0.003 * min(H0, W0)))
        fs = 0.75 * min(W0, H0) / 1024.0
        pos = {}
        for g in r["regions"]:
            cv2.rectangle(im, (int(g["x0"] * sx), int(g["y0"] * sy)),
                          (int(g["x1"] * sx), int(g["y1"] * sy)), (30, 120, 235), w)
            cx, cy = int(g["cx"] * W0), int(g["cy"] * H0)
            pos[g["lab"]] = (cx, cy)
            cv2.putText(im, "%.0f" % g["angle"], (cx - 22, cy), cv2.FONT_HERSHEY_SIMPLEX, fs,
                        (200, 0, 160), w + 1)
        for p in r["pairs"]:
            col = (230, 40, 40) if p["gap"] < 25.0 else (0, 175, 0)
            cv2.line(im, pos[p["a"]], pos[p["b"]], col, w)
    p = _overlay_path(image, tag)
    Image.fromarray(im).save(p)
    r = dict(r)
    r["path"] = p
    r.pop("regions", None)
    return r

# end of hatch_map_code

# code: f_code
def no_blank_parts(n_blank):
    """1.0 when no part is left without hatching."""
    return 1.0 if int(n_blank) == 0 else 0.0

# end of f_code

# code: f_code_2
def hatch_gap_score(gap):
    """Score the smallest hatch angle gap between touching parts, full at 30 degrees."""
    if gap is None: return 0.0
    gap = float(gap)
    if gap >= 30.0: return 1.0
    if gap <= 12.0: return 0.0
    return round((gap - 12.0) / 18.0, 4)

# end of f_code_2

# code: hatch_overlay_marked_code

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


def _region_angle(m_region, crop_shape):
    import math
    import numpy as np
    import cv2
    ys, xs = np.nonzero(m_region)
    if xs.size < 60:
        return None
    canvas = (255 - (m_region * 255)).astype(np.uint8)
    e = cv2.Canny(canvas, 50, 150)
    h, w = m_region.shape
    L = None
    for frac, thr in ((0.30, 18), (0.18, 14), (0.10, 10)):
        mn = max(8, int(frac * min(h, w)))
        L = cv2.HoughLinesP(e, 1, np.pi / 720, threshold=thr, minLineLength=mn, maxLineGap=3)
        if L is not None and len(L) >= 3:
            break
    if L is None or len(L) < 3:
        return None
    A = np.array([math.degrees(math.atan2(float(b2) - float(b1), float(a2) - float(a1))) % 180.0
                  for a1, b1, a2, b2 in L[:, 0, :]], float)
    dbl = np.deg2rad(A * 2.0)
    dom = (math.degrees(math.atan2(float(np.sin(dbl).mean()),
                                   float(np.cos(dbl).mean()))) / 2.0) % 180.0
    dev = np.minimum((A - dom) % 180.0, (dom - A) % 180.0)
    keep = int((dev < 12.0).sum())
    if keep < 3:
        return None
    th = math.radians(dom)
    perp = (math.cos(th + math.pi / 2), math.sin(th + math.pi / 2))
    proj = xs * perp[0] + ys * perp[1]
    span = float(proj.max() - proj.min())
    pitch = None
    if span > 8:
        hist, edg = np.histogram(proj, bins=max(20, int(span / 2)))
        thr = hist.max() * 0.35
        peaks = []
        for i in range(1, len(hist) - 1):
            if hist[i] >= thr and hist[i] >= hist[i - 1] and hist[i] >= hist[i + 1]:
                c = 0.5 * (edg[i] + edg[i + 1])
                if peaks and abs(c - peaks[-1]) < span * 0.02:
                    continue
                peaks.append(c)
        if len(peaks) >= 3:
            g = np.diff(np.array(peaks, float))
            pitch = float(g.mean())
    return {"angle": round(dom, 2), "n_lines": int(keep), "pitch": (None if pitch is None
                                                                    else round(pitch, 2))}


def hatch_map(image, n_parts=4, min_region_frac=0.006):
    import math
    import numpy as np
    import cv2
    bgr, gray, m, H, W, OW, OH = _prep(image)
    if float(m.mean()) < 0.02:
        return {"no_read": True, "reason": "almost_no_ink", "n_regions": 0}
    best = None
    for t in (2, 3, 1, 4):
        ker = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * t + 1, 2 * t + 1))
        thick = cv2.dilate(cv2.erode(m, ker), ker)
        frac = float(thick.sum()) / max(1.0, float(m.sum()))
        if not (0.02 <= frac <= 0.80):
            continue
        walls = cv2.dilate(thick, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)))
        interior = (1 - walls).astype(np.uint8)
        n, lbl, st, ce = cv2.connectedComponentsWithStats(interior, 4)
        border = set(np.unique(np.concatenate([lbl[0], lbl[-1], lbl[:, 0], lbl[:, -1]])).tolist())
        regs = []
        for i in range(1, n):
            if i in border:
                continue
            if int(st[i, cv2.CC_STAT_AREA]) < min_region_frac * H * W:
                continue
            regs.append(i)
        if len(regs) >= max(2, n_parts):
            best = (thick, walls, lbl, regs, t)
            break
    if best is None:
        return {"no_read": True, "reason": "no_walled_regions", "n_regions": 0}
    thick, walls, lbl, regs, t = best
    out_regs = []
    n_blank = 0
    for i in regs:
        sel = (lbl == i)
        ys, xs = np.nonzero(sel)
        y0, y1, x0, x1 = int(ys.min()), int(ys.max()), int(xs.min()), int(xs.max())
        strokes = (sel & (m > 0)).astype(np.uint8)[y0:y1 + 1, x0:x1 + 1]
        if float((sel & (m > 0)).sum()) / max(1.0, float(sel.sum())) < 0.02:
            n_blank += 1
            continue
        r = _region_angle(strokes, (y1 - y0 + 1, x1 - x0 + 1))
        if r is None:
            continue
        r.update({"lab": int(i), "x0": x0, "y0": y0, "x1": x1, "y1": y1,
                  "cx": round(0.5 * (x0 + x1) / W, 4), "cy": round(0.5 * (y0 + y1) / H, 4),
                  "area": int(sel.sum())})
        out_regs.append(r)
    if len(out_regs) < max(2, n_parts):
        return {"no_read": True, "reason": "n_hatched_%d_lt_%d" % (len(out_regs), n_parts),
                "n_regions": len(out_regs), "n_blank": n_blank}

    def gap(a, b):
        d = abs(a - b) % 180.0
        return min(d, 180.0 - d)

    rad = max(5, 2 * t + int(0.010 * min(H, W)))
    kad = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * rad + 1, 2 * rad + 1))
    masks = {}
    for r in out_regs:
        masks[r["lab"]] = cv2.dilate((lbl == r["lab"]).astype(np.uint8), kad)
    pairs = []
    for i in range(len(out_regs)):
        for j in range(i + 1, len(out_regs)):
            a, b = out_regs[i], out_regs[j]
            ov = int((masks[a["lab"]] & masks[b["lab"]]).sum())
            if ov < 40:
                continue
            pairs.append({"a": a["lab"], "b": b["lab"], "overlap": ov,
                          "gap": round(gap(a["angle"], b["angle"]), 2)})
    angs = sorted(r["angle"] for r in out_regs)
    clusters = []
    for a in angs:
        if clusters and gap(a, clusters[-1][-1]) <= 12.0:
            clusters[-1].append(a)
        else:
            clusters.append([a])
    if len(clusters) > 1 and gap(clusters[0][0], clusters[-1][-1]) <= 12.0:
        clusters[0] = clusters[-1] + clusters[0]
        clusters.pop()
    sizes = sorted((len(c) for c in clusters), reverse=True)
    return {"no_read": False, "n_regions": len(out_regs), "thick_scale": t, "n_blank": n_blank,
            "regions": out_regs, "pairs": pairs, "n_pairs": len(pairs),
            "min_adjacent_gap": (round(min(p["gap"] for p in pairs), 2) if pairs else None),
            "n_clusters": len(clusters), "cluster_sizes": sizes,
            "angles": [r["angle"] for r in out_regs],
            "img_w": W, "img_h": H, "orig_w": OW, "orig_h": OH}


def hatch_overlay(image, n_parts=4, tag="hatch"):
    import numpy as np
    import cv2
    from PIL import Image
    r = hatch_map(image, n_parts=n_parts)
    pil = _pil(image)
    W0, H0 = pil.size
    im = np.array(pil).copy()
    if not r.get("no_read"):
        sx, sy = W0 / float(r["img_w"]), H0 / float(r["img_h"])
        w = max(2, int(0.003 * min(H0, W0)))
        fs = 0.75 * min(W0, H0) / 1024.0
        pos = {}
        for g in r["regions"]:
            cv2.rectangle(im, (int(g["x0"] * sx), int(g["y0"] * sy)),
                          (int(g["x1"] * sx), int(g["y1"] * sy)), (30, 120, 235), w)
            _mk("regions", "rects",
                [0.5 * (g["x0"] + g["x1"]) * sx, 0.5 * (g["y0"] + g["y1"]) * sy,
                 (g["x1"] - g["x0"]) * sx, (g["y1"] - g["y0"]) * sy])
            cx, cy = int(g["cx"] * W0), int(g["cy"] * H0)
            pos[g["lab"]] = (cx, cy)
            cv2.putText(im, "%.0f" % g["angle"], (cx - 22, cy), cv2.FONT_HERSHEY_SIMPLEX, fs,
                        (200, 0, 160), w + 1)
        for p in r["pairs"]:
            same = p["gap"] < 25.0
            col = (230, 40, 40) if same else (0, 175, 0)
            cv2.line(im, pos[p["a"]], pos[p["b"]], col, w)
            _mk("pair_same_direction" if same else "pair_different_direction", "polylines",
                [[pos[p["a"]][0], pos[p["a"]][1]], [pos[p["b"]][0], pos[p["b"]][1]]])
    p = _overlay_path(image, tag)
    Image.fromarray(im).save(p)
    r = dict(r)
    r["path"] = p
    r.pop("regions", None)
    return r


def hatch_overlay_marked(image, n_parts=4, tag="hatch"):
    """Draw the found parts and lines joining touching parts on the image."""
    _mk_reset("regions", "pair_same_direction", "pair_different_direction")
    r = dict(hatch_overlay(image, n_parts, tag))
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

# end of hatch_overlay_marked_code
