# shared code: code_45e0025b631e
def match_intervals(classes, required):
    req = list(required)
    got = list(classes)
    n = 0
    for c in got:
        if c in req:
            req.remove(c)
            n += 1
    exact = 1.0 if (n == len(required) and len(got) == len(required)) else 0.0
    return n, exact, len(got), len(required)


def exact_interval_score(m, required):
    """Score 1 when the upper notes form exactly the required intervals above the bass."""
    if m.get("no_read"):
        return 0.0
    n, exact, n_got, n_required = match_intervals(list(m.get("classes") or []), list(required))
    return float(exact)


def interval_match_share(m, required):
    """The share of required intervals found, over the larger of found and required."""
    if m.get("no_read"):
        return 0.0
    n, exact, n_got, n_required = match_intervals(list(m.get("classes") or []), list(required))
    denom = max(n_required, n_got)
    return round(n / float(denom), 4) if denom else 0.0


def upper_count_score(m, n_req):
    """Score 1 when the number of upper notes equals the expected count."""
    if m.get("no_read"):
        return 0.0
    return 1.0 if int(m.get("n_upper") or 0) == int(n_req) else 0.0


def stacked_chord_score(m):
    """Score 1 when the upper notes lie within two staff spaces of each other sideways."""
    if m.get("no_read"):
        return 0.0
    return 1.0 if float(m.get("chord_spread_sp") or 0.0) <= 2.0 else 0.0


def figure_count_score(m, n_fig):
    """Score 1 when the number of figure glyphs under the bass equals the expected count."""
    if m.get("no_read"):
        return 0.0
    return 1.0 if int(m.get("n_figure_glyphs") or 0) == int(n_fig) else 0.0



# end of code_45e0025b631e

# code: read_figured_bass_code

def _pil(image):
    from PIL import Image
    if hasattr(image, "convert"):
        return image.convert("RGB")
    return Image.open(str(image)).convert("RGB")


def _binarize(gray):
    import cv2
    m = cv2.threshold(cv2.GaussianBlur(gray, (3, 3), 0), 0, 255,
                      cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
    if float((m > 0).mean()) > 0.5:
        m = 255 - m
    return m


def _skew_angle(gray):
    import numpy as np
    import cv2
    H, W = gray.shape[:2]
    s = 700.0 / max(H, W) if max(H, W) > 700 else 1.0
    g = cv2.resize(gray, (int(W * s), int(H * s)), interpolation=cv2.INTER_AREA) if s != 1.0 \
        else gray
    ink = _binarize(g)
    h, w = ink.shape

    def score(a):
        M = cv2.getRotationMatrix2D((w / 2.0, h / 2.0), a, 1.0)
        r = cv2.warpAffine(ink, M, (w, h), flags=cv2.INTER_NEAREST, borderValue=0)
        return float(np.var(r.sum(axis=1) / 255.0))

    best, bs = 0.0, -1.0
    for a in np.arange(-6.0, 6.01, 0.5):
        v = score(float(a))
        if v > bs:
            bs, best = v, float(a)
    for a in np.arange(best - 0.5, best + 0.51, 0.1):
        v = score(float(a))
        if v > bs:
            bs, best = v, float(a)
    return best


def _ink(image):
    import numpy as np
    import cv2
    rgb = np.asarray(_pil(image))
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    ang = _skew_angle(gray)
    if abs(ang) > 0.12:
        H, W = gray.shape[:2]
        M = cv2.getRotationMatrix2D((W / 2.0, H / 2.0), ang, 1.0)
        gray = cv2.warpAffine(gray, M, (W, H), flags=cv2.INTER_CUBIC,
                              borderValue=int(np.median(gray)))
    return _binarize(gray), gray, gray.shape[0], gray.shape[1], round(ang, 2)


def _staves(ink, W, H):
    import numpy as np
    import cv2
    hlen = max(40, W // 10)
    horiz = cv2.morphologyEx(ink, cv2.MORPH_OPEN,
                             cv2.getStructuringElement(cv2.MORPH_RECT, (hlen, 1)))
    rowsum = horiz.sum(axis=1) / 255.0
    peak = float(rowsum.max()) if rowsum.size else 0.0
    if peak < 0.05 * W:
        return None
    rows = np.where(rowsum > 0.45 * peak)[0]
    if rows.size == 0:
        return None
    lines = []
    start = prev = int(rows[0])
    for y in rows[1:]:
        y = int(y)
        if y - prev <= 3:
            prev = y
        else:
            lines.append((start + prev) / 2.0)
            start = prev = y
    lines.append((start + prev) / 2.0)
    lines = sorted(lines)
    if len(lines) < 10:
        return None
    gaps = np.diff(lines)
    med = float(np.median(gaps))
    small = float(np.median(gaps[gaps <= med * 1.8]))
    if small <= 0:
        return None
    systems, cur = [], [lines[0]]
    for i, g in enumerate(gaps):
        if g > 2.0 * small:
            systems.append(cur)
            cur = [lines[i + 1]]
        else:
            cur.append(lines[i + 1])
    systems.append(cur)
    systems = [s for s in systems if len(s) == 5]
    if len(systems) < 2:
        return None
    systems.sort(key=lambda s: s[0])
    band = np.zeros(W)
    for s in (systems[0], systems[-1]):
        for y in s:
            band = band + (horiz[int(round(y))] > 0)
    onx = np.where(band > 0)[0]
    if onx.size == 0:
        return None
    return systems[0], systems[-1], horiz, int(onx.min()), int(onx.max())


def _heads(ink, horiz, sp, x_lo, H, W):
    import numpy as np
    import cv2
    staff = cv2.dilate(horiz, cv2.getStructuringElement(cv2.MORPH_RECT, (1, 3)))
    res = cv2.bitwise_and(ink, cv2.bitwise_not(staff))
    k = max(3, int(round(sp * 0.32)) | 1)
    res = cv2.morphologyEx(res, cv2.MORPH_CLOSE,
                           cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k)))
    m = (res > 0).astype(np.uint8)
    n, lbl, st, ce = cv2.connectedComponentsWithStats(m, 8)
    left_zone = x_lo
    for i in range(1, n):
        x, y, w, h, a = st[i]
        if h >= 2.2 * sp and x <= x_lo + 4.0 * sp:
            left_zone = max(left_zone, x + w)
    keep = m.copy()
    blobs = []
    for i in range(1, n):
        x, y, w, h, a = st[i]
        if (ce[i][0] <= left_zone + 0.3 * sp) or (w <= 0.55 * sp and h >= 1.6 * sp) or h >= 4.5 * sp:
            keep[lbl == i] = 0
        else:
            blobs.append([int(x), int(y), int(w), int(h), int(a), float(ce[i][0]), float(ce[i][1])])

    heads = []
    inv = (keep == 0).astype(np.uint8)
    hn, hl, hs, hc = cv2.connectedComponentsWithStats(inv, 4)
    for i in range(1, hn):
        x, y, w, h, a = hs[i]
        if x == 0 or y == 0 or x + w >= W or y + h >= H:
            continue
        if not (0.30 * sp * sp <= a <= 1.20 * sp * sp):
            continue
        if not (0.45 * sp <= w <= 1.30 * sp and 0.45 * sp <= h <= 1.30 * sp):
            continue
        cx, cy = float(hc[i][0]), float(hc[i][1])
        yy = int(round(cy))
        if not (0 <= yy < H):
            continue
        x0 = int(max(0, cx - 1.5 * sp))
        x1 = int(min(W, cx + 1.5 * sp))
        row = np.where(keep[yy, x0:x1] > 0)[0]
        if row.size == 0 or (row.max() - row.min() + 1) < 1.05 * sp:
            continue
        heads.append({"cx": cx, "cy": cy, "src": "hole"})

    used = [False] * len(blobs)
    for i, b in enumerate(blobs):
        if used[i]:
            continue
        gx0, gy0, gx1, gy1 = b[0], b[1], b[0] + b[2] - 1, b[1] + b[3] - 1
        used[i] = True
        for j, c in enumerate(blobs):
            if used[j]:
                continue
            oy = min(gy1, c[1] + c[3] - 1) - max(gy0, c[1]) + 1
            if oy < 0.60 * min(gy1 - gy0 + 1, c[3]):
                continue
            gap = max(gx0, c[0]) - min(gx1, c[0] + c[2] - 1)
            if gap > 0.55 * sp:
                continue
            used[j] = True
            gx0, gy0 = min(gx0, c[0]), min(gy0, c[1])
            gx1, gy1 = max(gx1, c[0] + c[2] - 1), max(gy1, c[1] + c[3] - 1)
        gw, gh = gx1 - gx0 + 1, gy1 - gy0 + 1
        if not (0.60 * sp <= gh <= 1.40 * sp and 0.95 * sp <= gw <= 2.60 * sp):
            continue
        if gw / float(gh) < 1.15:
            continue
        heads.append({"cx": 0.5 * (gx0 + gx1), "cy": 0.5 * (gy0 + gy1), "src": "blob"})

    heads.sort(key=lambda d: (d["cy"], d["cx"]))
    out = []
    for hd in heads:
        if any(abs(hd["cx"] - o["cx"]) < 0.80 * sp and abs(hd["cy"] - o["cy"]) < 0.55 * sp
               for o in out):
            continue
        out.append(hd)
    return out, keep, left_zone


def _figure_glyphs(ink, lower, bass_cx, sp, H, W):
    import numpy as np
    import cv2
    y0 = int(min(H - 1, lower[-1] + 0.45 * sp))
    y1 = int(min(H, lower[-1] + 5.0 * sp))
    x0 = int(max(0, bass_cx - 3.2 * sp))
    x1 = int(min(W, bass_cx + 3.2 * sp))
    if y1 - y0 < 4 or x1 - x0 < 4:
        return {"n": 0, "boxes": []}
    sub = (ink[y0:y1, x0:x1] > 0).astype(np.uint8)
    n, lbl, st, ce = cv2.connectedComponentsWithStats(sub, 8)
    boxes = []
    for i in range(1, n):
        x, y, w, h, a = st[i]
        if a < 0.05 * sp * sp:
            continue
        if not (0.20 * sp <= w <= 2.2 * sp and 0.55 * sp <= h <= 2.6 * sp):
            continue
        boxes.append([int(x0 + x), int(y0 + y), int(w), int(h)])
    boxes.sort(key=lambda b: b[1])
    return {"n": len(boxes), "boxes": boxes}


def read_figured_bass(image, n_upper_expected=2):
    """Find the grand staff, bass note and upper notes, and each interval above the bass."""
    import numpy as np
    out = {"no_read": True, "reason": None}
    try:
        ink, gray, H, W, skew = _ink(image)
    except Exception:
        out["reason"] = "unloadable"
        return out
    out["skew_deg"] = skew
    staves = _staves(ink, W, H)
    if staves is None:
        out["reason"] = "no_grand_staff"
        return out
    upper, lower, horiz, x_lo, x_hi = staves
    staff_space = 0.5 * ((upper[-1] - upper[0]) + (lower[-1] - lower[0])) / 4.0
    if staff_space < 6:
        out["reason"] = "staff_too_small"
        return out
    heads, keep, left_zone = _heads(ink, horiz, staff_space, x_lo, H, W)
    mid = 0.5 * (upper[-1] + lower[0])
    up = [h for h in heads if h["cy"] < mid]
    lo = [h for h in heads if h["cy"] >= mid]
    if not lo:
        out.update({"reason": "no_bass_note", "sp": round(staff_space, 2), "n_upper": len(up)})
        return out
    if not up:
        out.update({"reason": "no_upper_notes", "sp": round(staff_space, 2), "n_lower": len(lo)})
        return out

    def pos(cy, s):
        return int(round((s[-1] - cy) / ((s[-1] - s[0]) / 8.0)))

    lo.sort(key=lambda d: -d["cy"])
    bass = lo[0]
    bass_p = pos(bass["cy"], lower)
    bass_d = bass_p - 10
    ups = []
    for h in up:
        p = pos(h["cy"], upper)
        ups.append({"cx": h["cx"], "cy": h["cy"], "pos": p, "dia": p + 2, "src": h["src"]})
    ups.sort(key=lambda d: d["dia"])
    steps = [u["dia"] - bass_d for u in ups]
    classes = [(s % 7) if s > 0 else -1 for s in steps]
    up_spread = ((max(u["cx"] for u in ups) - min(u["cx"] for u in ups)) / staff_space) if len(ups) > 1 else 0.0
    fig = _figure_glyphs(ink, lower, bass["cx"], staff_space, H, W)
    out.update({"no_read": False, "reason": None, "sp": round(staff_space, 2),
                "upper_lines": [round(v, 1) for v in upper],
                "lower_lines": [round(v, 1) for v in lower],
                "bass_pos": bass_p, "bass_dia": bass_d,
                "bass_cx": round(bass["cx"], 1), "bass_cy": round(bass["cy"], 1),
                "upper_pos": [u["pos"] for u in ups], "upper_dia": [u["dia"] for u in ups],
                "upper_cx": [round(u["cx"], 1) for u in ups],
                "upper_cy": [round(u["cy"], 1) for u in ups],
                "n_upper": len(ups), "n_lower": len(lo),
                "steps": steps, "classes": classes,
                "chord_spread_sp": round(up_spread, 2),
                "n_figure_glyphs": fig["n"], "figure_boxes": fig["boxes"],
                "n_expected": int(n_upper_expected), "img_w": W, "img_h": H,
                "left_zone": int(left_zone)})
    return out



# end of read_figured_bass_code

# code: gt_overlay_code
def reference_overlay(image, m, required, bass_asked=None, tag="e7bfb"):
    """Draw the read bass and upper notes, coloured by whether each interval is required."""
    import hashlib
    import os
    import tempfile
    import numpy as np
    import cv2
    d = os.path.join(tempfile.gettempdir(), "genolympiad_overlay")
    try:
        os.makedirs(d, exist_ok=True)
    except Exception:
        pass
    h = hashlib.md5(("%s|%s" % (str(image), str(tag))).encode("utf-8", "replace")).hexdigest()[:12]
    path = os.path.join(d, "e7bfb_%s_%s.png" % (tag, h))
    try:
        from PIL import Image
        pil = image.convert("RGB") if hasattr(image, "convert") \
            else Image.open(str(image)).convert("RGB")
        bgr = cv2.cvtColor(np.asarray(pil), cv2.COLOR_RGB2BGR).copy()
    except Exception:
        return {"overlay": None, "note": "unloadable"}
    if m.get("no_read"):
        cv2.putText(bgr, "NO READ: %s" % str(m.get("reason")), (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 220), 2, cv2.LINE_AA)
        cv2.imwrite(path, bgr)
        return {"overlay": path, "note": "no_read"}
    H, W = bgr.shape[:2]
    sp = float(m.get("sp") or 10.0)
    lw = max(2, int(round(sp / 12.0)))
    for name, col in (("upper_lines", (200, 140, 40)), ("lower_lines", (200, 140, 40))):
        for y in (m.get(name) or []):
            cv2.line(bgr, (0, int(round(y))), (W - 1, int(round(y))), col, 1, cv2.LINE_AA)
    fs = sp / 46.0
    tk = max(1, lw - 1)
    orange = (20, 130, 235)
    bx, by = int(round(m["bass_cx"])), int(round(m["bass_cy"]))
    cv2.ellipse(bgr, (bx, by), (int(1.05 * sp), int(0.80 * sp)), 0, 0, 360, orange, lw, cv2.LINE_AA)
    cv2.arrowedLine(bgr, (int(bx - 4.2 * sp), int(by + 2.2 * sp)),
                    (int(bx - 1.15 * sp), int(by + 0.15 * sp)), orange, lw, cv2.LINE_AA,
                    tipLength=0.25)
    _label(bgr, "bass read here, staff pos %d" % int(m["bass_pos"]),
           int(bx - 4.6 * sp), int(by + 2.9 * sp), orange, fs, tk, W, anchor_right=True)
    if bass_asked is not None:
        cv2.putText(bgr, "prompt asked for bass staff pos %d, drawn at %d -- ANCHOR NOT SCORED"
                    % (int(bass_asked), int(m["bass_pos"])),
                    (int(0.02 * W), int(0.085 * H)), cv2.FONT_HERSHEY_SIMPLEX, sp / 46.0,
                    (90, 90, 90), tk, cv2.LINE_AA)
    req = list(required)
    for i, (ux, uy) in enumerate(zip(m.get("upper_cx") or [], m.get("upper_cy") or [])):
        ux, uy = int(round(ux)), int(round(uy))
        cls = (m.get("classes") or [None] * 9)[i]
        ok = cls in req
        if ok:
            req.remove(cls)
        col = (40, 160, 40) if ok else (30, 30, 220)
        cv2.ellipse(bgr, (ux, uy), (int(1.05 * sp), int(0.80 * sp)), 0, 0, 360, col, lw, cv2.LINE_AA)
        txt = "%s above bass" % _ordinal(cls)
        (tw, th), _ = cv2.getTextSize(txt, cv2.FONT_HERSHEY_SIMPLEX, fs, tk)
        right = (ux + 4.3 * sp + tw) < W - 4
        if right:
            cv2.line(bgr, (int(ux + 1.15 * sp), uy), (int(ux + 4.0 * sp), uy), col, tk, cv2.LINE_AA)
            cv2.putText(bgr, txt, (int(ux + 4.3 * sp), int(uy + 0.28 * sp)),
                        cv2.FONT_HERSHEY_SIMPLEX, fs, col, tk, cv2.LINE_AA)
        else:
            cv2.line(bgr, (int(ux - 1.15 * sp), uy), (int(ux - 4.0 * sp), uy), col, tk, cv2.LINE_AA)
            cv2.putText(bgr, txt, (int(max(4, ux - 4.3 * sp - tw)), int(uy + 0.28 * sp)),
                        cv2.FONT_HERSHEY_SIMPLEX, fs, col, tk, cv2.LINE_AA)
        cv2.line(bgr, (bx, by - int(0.8 * sp)), (ux, uy + int(0.8 * sp)), col, 1, cv2.LINE_AA)
    cv2.putText(bgr, "figure requires: %s above the bass that was drawn"
                % ", ".join(_ordinal(c) for c in required),
                (int(0.02 * W), int(0.05 * H)), cv2.FONT_HERSHEY_SIMPLEX, sp / 42.0,
                (20, 20, 20), tk, cv2.LINE_AA)
    cv2.imwrite(path, bgr)
    return {"overlay": path, "classes": list(m.get("classes") or []),
            "required": list(required), "note": "drawn"}


def _label(bgr, txt, x, y, col, fs, tk, W, anchor_right=False):
    import cv2
    (tw, th), _ = cv2.getTextSize(txt, cv2.FONT_HERSHEY_SIMPLEX, fs, tk)
    x = int(x - tw) if anchor_right else int(x)
    x = max(4, min(x, W - tw - 4))
    cv2.putText(bgr, txt, (x, int(y)), cv2.FONT_HERSHEY_SIMPLEX, fs, col, tk, cv2.LINE_AA)


def _ordinal(c):
    if c is None or c < 0:
        return "not above the bass"
    return {0: "8ve", 1: "2nd", 2: "3rd", 3: "4th", 4: "5th", 5: "6th", 6: "7th"}.get(int(c),
                                                                                      str(c))

# end of gt_overlay_code
