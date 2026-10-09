# code: not_flat_readable_code

def _pil(image):
    from PIL import Image
    return image.convert("RGB") if hasattr(image, "convert") else Image.open(str(image)).convert("RGB")


def _rgb(image, cap=1400):
    import numpy as np
    import cv2
    a = np.asarray(_pil(image))
    OH, OW = a.shape[:2]
    if max(OH, OW) > cap:
        s = float(cap) / max(OH, OW)
        a = cv2.resize(a, (int(round(OW * s)), int(round(OH * s))), interpolation=cv2.INTER_AREA)
    return a


def _dist_map(rgb):
    import numpy as np
    import cv2
    lab = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB).astype(np.float32)
    med = np.median(lab.reshape(-1, 3), axis=0)
    d = np.sqrt(((lab - med[None, None, :]) ** 2).sum(axis=2))
    return cv2.GaussianBlur(d, (5, 5), 0)


def _mask_candidates(rgb):
    import numpy as np
    import cv2
    d = _dist_map(rgb)
    mx = float(d.max())
    dn = np.clip(d / (mx if mx > 1e-6 else 1.0) * 255.0, 0, 255).astype(np.uint8)
    ot, _th = cv2.threshold(dn, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    ths = [float(ot) * mx / 255.0]
    ths += [float(np.percentile(d, q)) for q in (85.0, 90.0, 93.0, 95.0, 96.5, 98.0, 99.0, 99.5)]
    seen = []
    for t in ths:
        m = (d >= t).astype(np.uint8)
        f = float(m.mean())
        if f > 0.5:
            m = (1 - m).astype(np.uint8)
            f = 1.0 - f
        if not (0.0012 < f < 0.45):
            continue
        if any(abs(f - g) < 1e-4 for g in seen):
            continue
        seen.append(f)
        yield m


def _clean(m, mode):
    import numpy as np
    import cv2
    H, W = m.shape
    k = max(3, 2 * int(0.004 * min(H, W)) + 1)
    ker = np.ones((k, k), np.uint8)
    if mode == "open":
        return cv2.morphologyEx(m, cv2.MORPH_OPEN, ker)
    er = cv2.erode(m, ker)
    n, lab = cv2.connectedComponents(m, 8)
    if n <= 1:
        return m
    alive = np.zeros(n, np.uint8)
    hit = lab[er > 0]
    if hit.size:
        alive[np.unique(hit)] = 1
    alive[0] = 0
    return alive[lab]


def _blobs(mm, min_area_frac=0.0006):
    import numpy as np
    import cv2
    H, W = mm.shape
    n, lab, st, ce = cv2.connectedComponentsWithStats(mm, 8)
    out = []
    for i in range(1, n):
        x, y, w, h, a = [int(v) for v in st[i]]
        if a < min_area_frac * H * W:
            continue
        if x <= 1 or y <= 1 or x + w >= W - 1 or y + h >= H - 1:
            continue
        out.append({"i": int(i), "x": x, "y": y, "w": w, "h": h, "a": a,
                    "cx": float(ce[i][0]), "cy": float(ce[i][1])})
    return out, lab


def _profile(sel, horiz):
    import numpy as np
    a = (sel > 0)
    if horiz:
        a = a.T
    any_ = a.any(1)
    if not any_.any():
        return np.zeros(0), np.zeros(0)
    first = a.argmax(1)
    last = a.shape[1] - 1 - a[:, ::-1].argmax(1)
    idx = np.nonzero(any_)[0]
    return idx.astype(float), (last[idx] - first[idx] + 1).astype(float)


def _theil_sen(xs, ys):
    import numpy as np
    xs = np.asarray(xs, dtype=float)
    ys = np.asarray(ys, dtype=float)
    if xs.size < 8:
        return None, None
    step = max(1, xs.size // 200)
    xi, yi = xs[::step], ys[::step]
    S = []
    for a in range(xi.size):
        dx = xi[a + 1:] - xi[a]
        dy = yi[a + 1:] - yi[a]
        ok = np.abs(dx) > 1e-9
        if ok.any():
            S.append(dy[ok] / dx[ok])
    if not S:
        return None, None
    sl = float(np.median(np.concatenate(S)))
    return sl, float(np.median(ys - sl * xs))


def _geom(image, far_edge, min_letters=3, max_letters=8):
    import numpy as np
    rgb = _rgb(image)
    H, W = rgb.shape[:2]
    horiz = far_edge in ("right", "left")

    def along_span(b):
        return (b["x"], b["x"] + b["w"] - 1) if horiz else (b["y"], b["y"] + b["h"] - 1)

    why = "no_paint"
    best = None
    for m in _mask_candidates(rgb):
        for cmode in ("open", "recon"):
            mm = _clean(m, cmode)
            bl, lab = _blobs(mm)
            if len(bl) < min_letters:
                why = "blobs_%d" % len(bl)
                continue
            bl.sort(key=lambda b: -b["a"])
            a0, a1 = along_span(bl[0])
            keep = []
            for b in bl:
                c0, c1 = along_span(b)
                ov = max(0, min(a1, c1) - max(a0, c0) + 1)
                if ov >= 0.55 * (a1 - a0 + 1) and b["a"] >= 0.11 * bl[0]["a"]:
                    keep.append(b)
            if not (min_letters <= len(keep) <= max_letters):
                why = "group_%d" % len(keep)
                continue
            keep.sort(key=lambda b: b["cy"] if horiz else b["cx"])
            sel0 = np.zeros_like(mm)
            for b in keep:
                sel0[lab == b["i"]] = 1
            ys0, xs0 = np.nonzero(sel0)
            g0 = int((xs0 if horiz else ys0).min())
            g1 = int((xs0 if horiz else ys0).max())
            sel = np.zeros_like(mm)
            for b in bl:
                c0, c1 = along_span(b)
                if c1 >= g0 and c0 <= g1:
                    sel[lab == b["i"]] = 1
            if horiz:
                sel[:, :g0] = 0
                sel[:, g1 + 1:] = 0
            else:
                sel[:g0] = 0
                sel[g1 + 1:] = 0
            ys, xs = np.nonzero(sel)
            if ys.size < 60:
                why = "thin_ink"
                continue
            t = xs if horiz else ys
            u = ys if horiz else xs
            t0, t1 = int(t.min()), int(t.max())
            if t1 - t0 < 0.10 * min(H, W):
                why = "short_along"
                continue
            pad = int(0.06 * (t1 - t0))
            tt, ww = _profile(sel, horiz)
            msk = (tt >= t0 + pad) & (tt <= t1 - pad)
            tt, ww = tt[msk], ww[msk]
            span = (t1 - pad) - (t0 + pad) + 1
            if tt.size < 20 or tt.size < 0.75 * span:
                why = "profile_gaps"
                continue
            sl, ic = _theil_sen(tt, ww)
            if sl is None:
                why = "no_fit"
                continue
            resid = float(np.median(np.abs(ww - (sl * tt + ic))))
            scale_w = float(np.mean(ww))
            if scale_w <= 1.0 or resid / scale_w > 0.035:
                why = "profile_not_linear"
                continue
            far_t = t1 if far_edge in ("right", "bottom") else t0
            near_t = t0 if far_edge in ("right", "bottom") else t1
            w_far, w_near = sl * far_t + ic, sl * near_t + ic
            if not (w_far > 1.0 and w_near > 1.0):
                why = "degenerate_envelope"
                continue
            cand = {"no_read": False, "rgb": rgb, "sel": sel, "lab": lab, "keep": keep,
                    "horiz": horiz, "ys": ys, "xs": xs, "t": t, "u": u, "t0": t0, "t1": t1,
                    "H": H, "W": W, "lo": t0 + pad, "hi": t1 - pad,
                    "w_far": float(w_far), "w_near": float(w_near), "resid": resid / scale_w,
                    "far_t": far_t, "near_t": near_t, "clean": cmode}
            if best is None or (t1 - t0, -cand["resid"]) > (best["t1"] - best["t0"], -best["resid"]):
                best = cand
    if best is None:
        return {"no_read": True, "reason": why, "n_letters": 0}
    return best


def road_read(image, far_edge="top", d_near=7.0, d_far=16.0):
    """Measure the painted word's letter stretch and how much it widens toward the far edge."""
    import numpy as np
    g = _geom(image, far_edge)
    if g.get("no_read"):
        return {"no_read": True, "reason": g.get("reason"), "n_letters": g.get("n_letters", 0)}
    keep, horiz = g["keep"], g["horiz"]
    t, u, t0, t1 = g["t"], g["u"], g["t0"], g["t1"]
    far_t, near_t = g["far_t"], g["near_t"]
    lab = g["lab"]

    el = []
    for b in keep:
        alen = float(b["w"] if horiz else b["h"])
        clen = float(b["h"] if horiz else b["w"])
        el.append(round(alen / max(1.0, clen), 3))

    lo, hi = g["lo"], g["hi"]
    w_far, w_near = g["w_far"], g["w_near"]
    taper = w_far / w_near

    def _centre_profile(b):
        yy, xx = np.nonzero(lab == b["i"])
        tb = xx if horiz else yy
        ub = yy if horiz else xx
        d = {}
        for v in np.unique(tb):
            s = ub[tb == v]
            if s.size >= 2:
                d[int(v)] = float(s.mean())
        return d

    pa, pb = _centre_profile(keep[0]), _centre_profile(keep[-1])
    st, sd = [], []
    for v in range(lo, hi + 1):
        if v in pa and v in pb:
            st.append(float(v))
            sd.append(abs(pb[v] - pa[v]))
    spread = None
    if len(st) >= 20:
        s2, i2 = _theil_sen(st, sd)
        if s2 is not None:
            f2, n2 = s2 * far_t + i2, s2 * near_t + i2
            if n2 > 1.0 and f2 > 1.0:
                spread = float(f2) / float(n2)

    word_elong = (t1 - t0) / (0.5 * (float(w_far) + float(w_near)))

    scale = (t1 - t0) / float(abs(d_far - d_near)) if d_far != d_near else None
    return {"no_read": False, "n_letters": len(keep), "elong": el,
            "elong_median": round(float(np.median(el)), 3),
            "word_elong": round(word_elong, 4),
            "fit_resid": round(g["resid"], 4),
            "taper": (round(taper, 4) if taper else None),
            "spread": (round(spread, 4) if spread else None),
            "w_far": (round(float(w_far), 1) if w_far else None),
            "w_near": (round(float(w_near), 1) if w_near else None),
            "t0": t0, "t1": t1, "far_t": far_t, "near_t": near_t, "horiz": bool(horiz),
            "px_per_m": (round(scale, 3) if scale else None),
            "img_w": g["W"], "img_h": g["H"],
            "letters": [{k: b[k] for k in ("x", "y", "w", "h", "cx", "cy", "a")} for b in keep]}


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
    return os.path.join(d, "e7banam_%s_%s.png" % (tag, h))


def road_warp(image, far_edge="top", d_near=7.0, d_far=16.0, eye_h=1.15, tag="warp"):
    """Render the painted floor as seen from the given eye height, for a reading check."""
    import numpy as np
    import cv2
    from PIL import Image
    g = _geom(image, far_edge)
    if g.get("no_read"):
        return {"no_read": True, "reason": g.get("reason")}
    sel, horiz = g["sel"], g["horiz"]
    t0, t1, far_t, near_t = g["t0"], g["t1"], g["far_t"], g["near_t"]
    u = g["u"]
    scale = (t1 - t0) / float(abs(d_far - d_near))
    if scale <= 0:
        return {"no_read": True, "reason": "bad_scale"}
    u_c = float(u.mean())

    def ground(col, row):
        tv = float(col if horiz else row)
        uv = float(row if horiz else col)
        Y = d_near + (tv - near_t) * (d_far - d_near) / float(far_t - near_t)
        return (uv - u_c) / scale, Y

    fpx = 1400.0
    src, dst = [], []
    for col, row in ((0.0, 0.0), (g["W"] - 1.0, 0.0), (g["W"] - 1.0, g["H"] - 1.0), (0.0, g["H"] - 1.0)):
        X, Y = ground(col, row)
        Y = max(0.05, Y)
        src.append([col, row])
        dst.append([fpx * X / Y, fpx * eye_h / Y])
    src = np.float32(src)
    dst = np.float32(dst)
    corners = []
    for col, row in ((0.0, float(t0)), (float(g["W"] - 1), float(t0)),
                     (float(g["W"] - 1), float(t1)), (0.0, float(t1))):
        cc, rr = (row, col) if horiz else (col, row)
        X, Y = ground(cc, rr)
        Y = max(0.05, Y)
        corners.append((fpx * X / Y, fpx * eye_h / Y))
    ys, xs = np.nonzero(sel)
    pts = []
    for cc, rr in ((float(xs.min()), float(ys.min())), (float(xs.max()), float(ys.min())),
                   (float(xs.max()), float(ys.max())), (float(xs.min()), float(ys.max()))):
        X, Y = ground(cc, rr)
        Y = max(0.05, Y)
        pts.append((fpx * X / Y, fpx * eye_h / Y))
    ux = [p[0] for p in pts]
    vy = [p[1] for p in pts]
    bw, bh = max(1e-3, max(ux) - min(ux)), max(1e-3, max(vy) - min(vy))
    OW, OH = 1100, 620
    k = min((OW - 120) / bw, (OH - 120) / bh)
    ox, oy = 60 - min(ux) * k, 60 - min(vy) * k
    dst2 = np.float32([[p[0] * k + ox, p[1] * k + oy] for p in dst])
    M = cv2.getPerspectiveTransform(src, dst2)
    ink = (sel * 255).astype(np.uint8)
    warped = cv2.warpPerspective(ink, M, (OW, OH), flags=cv2.INTER_LINEAR, borderValue=0)
    page = 255 - np.clip(warped, 0, 255)
    page = cv2.medianBlur(page.astype(np.uint8), 3)
    p = _overlay_path(image, tag)
    Image.fromarray(np.dstack([page] * 3)).save(p)
    return {"no_read": False, "path": p, "px_per_m": round(scale, 3),
            "u_centre": round(u_c, 1), "out_w": OW, "out_h": OH}


def road_overlay(image, far_edge="top", d_near=7.0, d_far=16.0, eye_h=1.15,
                 want_elong=7.0, want_taper=2.286, tag="gt"):
    """Draw the measured letters and the width taper over the image."""
    import numpy as np
    import cv2
    from PIL import Image
    r = road_read(image, far_edge, d_near, d_far)
    pil = _pil(image)
    W0, H0 = pil.size
    im = np.array(pil).copy()
    if not r.get("no_read"):
        sx, sy = W0 / float(r["img_w"]), H0 / float(r["img_h"])
        lw = max(2, int(0.003 * min(W0, H0)))
        fs = 0.9 * min(W0, H0) / 1100.0
        for b, e in zip(r["letters"], r["elong"]):
            cv2.rectangle(im, (int(b["x"] * sx), int(b["y"] * sy)),
                          (int((b["x"] + b["w"]) * sx), int((b["y"] + b["h"]) * sy)),
                          (40, 120, 245), lw)
            cv2.putText(im, "%.1f" % e, (int(b["x"] * sx), max(20, int(b["y"] * sy) - 8)),
                        cv2.FONT_HERSHEY_SIMPLEX, fs, (40, 120, 245), lw)
        horiz = r["horiz"]
        for name, tv, wv, col in (("far", r["far_t"], r["w_far"], (30, 190, 60)),
                                  ("near", r["near_t"], r["w_near"], (240, 90, 30))):
            if not wv:
                continue
            cen = float(np.mean([b["cy"] if horiz else b["cx"] for b in r["letters"]]))
            a, b2 = cen - wv / 2.0, cen + wv / 2.0
            if horiz:
                p1 = (int(tv * sx), int(a * sy))
                p2 = (int(tv * sx), int(b2 * sy))
                anch = (int(tv * sx), int(max(6, a * sy - 0.06 * H0)))
            else:
                p1 = (int(a * sx), int(tv * sy))
                p2 = (int(b2 * sx), int(tv * sy))
                anch = (int(max(6, a * sx - 0.06 * W0)), int(tv * sy))
            cv2.line(im, p1, p2, col, lw + 2)
            cv2.arrowedLine(im, anch, p1, col, lw + 1, tipLength=0.25)
            cv2.putText(im, "%s %d px" % (name, int(round(wv))),
                        (max(4, anch[0] - int(0.10 * W0)), max(18, anch[1] - 8)),
                        cv2.FONT_HERSHEY_SIMPLEX, fs, col, lw)
    w = road_warp(image, far_edge, d_near, d_far, eye_h, tag="ovwarp")
    strip = int(0.34 * H0)
    canvas = np.full((H0 + strip, W0, 3), 245, np.uint8)
    canvas[:H0] = im
    cv2.line(canvas, (0, H0), (W0, H0), (30, 30, 30), max(2, int(0.003 * H0)))
    if not w.get("no_read"):
        try:
            wp = np.array(Image.open(w["path"]).convert("RGB"))
            pad = int(0.06 * strip)
            th = strip - 2 * pad
            sc = min(th / float(wp.shape[0]), (W0 - 2 * pad) / float(wp.shape[1]))
            wp = cv2.resize(wp, (max(1, int(wp.shape[1] * sc)), max(1, int(wp.shape[0] * sc))),
                            interpolation=cv2.INTER_AREA)
            hh, ww2 = wp.shape[:2]
            y0p, x0p = H0 + (strip - hh) // 2, (W0 - ww2) // 2
            canvas[y0p:y0p + hh, x0p:x0p + ww2] = wp
            cv2.rectangle(canvas, (x0p, y0p), (x0p + ww2, y0p + hh), (40, 120, 245),
                          max(2, int(0.002 * H0)))
        except Exception:
            pass
    cap = 0.75 * min(W0, H0) / 1100.0
    tk = max(1, int(0.0018 * H0))
    cv2.putText(canvas, "the paint warped back to the stated eye point", (12, H0 + 26),
                cv2.FONT_HERSHEY_SIMPLEX, cap, (40, 40, 40), tk)
    if not r.get("no_read"):
        cv2.putText(canvas, "word stretch %.2f (want %.2f)   widening %s (want %.2f)   "
                            "letter fan %s"
                    % (r["word_elong"] or 0.0, want_elong,
                       ("%.2f" % r["taper"]) if r["taper"] else "n/a", want_taper,
                       ("%.2f" % r["spread"]) if r["spread"] else "n/a"),
                    (12, H0 + strip - 14), cv2.FONT_HERSHEY_SIMPLEX, cap * 1.15, (15, 15, 15),
                    tk + 1)
    im = canvas
    p = _overlay_path(image, tag)
    Image.fromarray(im).save(p)
    out = {k: v for k, v in r.items() if k != "letters"}
    out["path"] = p
    return out


def find_word(text, payload):
    """Say whether the target word appears among the words read."""
    import re
    t = "" if text is None else str(text)
    words = [x for x in re.split(r"[^A-Za-z0-9]+", t.upper()) if x]
    target = str(payload).upper()
    return {"hit": bool(target in words), "miss": bool(target not in words),
            "word": (target if target in words else (words[-1] if words else "")),
            "toks": words[:12]}


def word_matches(word, payload):
    """Score 1 when the read word equals the target word."""
    import re
    if isinstance(word, dict):
        return 0.0
    w = re.sub(r"[^A-Za-z0-9]", "", str(word or "")).upper()
    return 1.0 if w == str(payload).upper() else 0.0


def _edit1(a, b):
    if a == b:
        return True
    la, lb = len(a), len(b)
    if abs(la - lb) > 1:
        return False
    if la == lb:
        return sum(1 for x, y in zip(a, b) if x != y) <= 1
    if la > lb:
        a, b, la, lb = b, a, lb, la
    for i in range(lb):
        if b[:i] + b[i + 1:] == a:
            return True
    return False


def not_flat_readable(text, payload):
    """Score 0 if the word reads from straight above, within one letter or reversed."""
    import re
    target = str(payload).upper()
    words = [x for x in re.split(r"[^A-Za-z0-9]+", ("" if text is None else str(text)).upper()) if x]
    for t in words + [x[::-1] for x in words]:
        if len(target) >= 4 and _edit1(t, target):
            return 0.0
        if len(target) < 4 and t == target:
            return 0.0
    return 1.0

# end of not_flat_readable_code

# code: widens_code
def widens(taper, threshold):
    """Score 1 when the far to near width ratio reaches the threshold."""
    return 1.0 if (taper is not None and float(taper) >= float(threshold)) else 0.0

# end of widens_code

# code: ok_code
def was_read(overlay):
    """Score 1 when the overlay measurement found the word, else 0."""
    return 0.0 if overlay.get('no_read') else 1.0

# end of ok_code
