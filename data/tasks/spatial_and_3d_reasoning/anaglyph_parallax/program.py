# code: disparity_field_code

def _pil(image):
    from PIL import Image
    return image.convert("RGB") if hasattr(image, "convert") else Image.open(str(image)).convert("RGB")


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
    return os.path.join(d, "e7bana_%s_%s.png" % (tag, h))


def _band_shift(rgb, box, lag_x=0.08, lag_y=0.035, coh_min=0.20):
    import numpy as np
    import cv2
    H, W = rgb.shape[:2]
    x0 = max(0, int(box[0] * W))
    y0 = max(0, int(box[1] * H))
    x1 = min(W, int(box[2] * W))
    y1 = min(H, int(box[3] * H))
    if x1 - x0 < 48 or y1 - y0 < 48:
        return {"ok": False, "why": "band_too_small", "box_px": [x0, y0, x1, y1]}
    R = rgb[y0:y1, x0:x1, 0].astype(np.float32)
    C = 0.5 * (rgb[y0:y1, x0:x1, 1].astype(np.float32) + rgb[y0:y1, x0:x1, 2].astype(np.float32))
    h, w = R.shape
    s = max(2.0, 0.05 * min(h, w))
    Rh = R - cv2.GaussianBlur(R, (0, 0), s)
    Ch = C - cv2.GaussianBlur(C, (0, 0), s)
    sr = float(Rh.std())
    sc = float(Ch.std())
    if sr < 0.35 or sc < 0.35:
        return {"ok": False, "why": "no_structure", "std_r": round(sr, 3), "std_c": round(sc, 3),
                "box_px": [x0, y0, x1, y1]}
    lx = min(max(4, int(lag_x * W)), (w - 48) // 2)
    ly = min(max(3, int(lag_y * H)), (h - 48) // 2)
    if lx < 3 or ly < 2:
        return {"ok": False, "why": "band_too_small", "box_px": [x0, y0, x1, y1]}
    Rh = (Rh / sr).astype(np.float32)
    Ch = (Ch / sc).astype(np.float32)
    res = cv2.matchTemplate(Rh, Ch[ly:h - ly, lx:w - lx], cv2.TM_CCOEFF_NORMED)
    _mn, mx, _ml, loc = cv2.minMaxLoc(res)
    px, py = int(loc[0]), int(loc[1])
    dx = float(px - lx)
    dy = float(py - ly)
    if 0 < px < res.shape[1] - 1:
        a, b, c = float(res[py, px - 1]), float(res[py, px]), float(res[py, px + 1])
        den = a - 2 * b + c
        if abs(den) > 1e-9 and abs(0.5 * (a - c) / den) <= 1.0:
            dx += 0.5 * (a - c) / den
    if 0 < py < res.shape[0] - 1:
        a, b, c = float(res[py - 1, px]), float(res[py, px]), float(res[py + 1, px])
        den = a - 2 * b + c
        if abs(den) > 1e-9 and abs(0.5 * (a - c) / den) <= 1.0:
            dy += 0.5 * (a - c) / den
    coh = float(mx)
    return {"ok": bool(coh >= float(coh_min)), "why": "" if coh >= float(coh_min) else "incoherent",
            "dx_px": round(dx, 2), "dy_px": round(dy, 2), "coh": round(coh, 3),
            "dx": round(100.0 * dx / W, 3), "dy": round(100.0 * dy / W, 3),
            "std_r": round(sr, 3), "std_c": round(sc, 3), "box_px": [x0, y0, x1, y1]}


def disparity_field(image, script, coh_min=0.20):
    """Measure the colour channel shift inside each scripted object band."""
    import numpy as np
    rgb = np.asarray(_pil(image))
    if rgb.ndim == 2:
        rgb = np.dstack([rgb, rgb, rgb])
    H, W = rgb.shape[:2]
    parts = []
    for it in script:
        m = _band_shift(rgb, it["box"], coh_min=float(coh_min))
        m["name"] = it["name"]
        m["target"] = float(it["target"])
        parts.append(m)
    n_struct = sum(1 for p in parts if p.get("why") not in ("no_structure", "band_too_small"))
    return {"no_read": bool(n_struct == 0), "n_ok": sum(1 for p in parts if p.get("ok")),
            "n_struct": n_struct, "parts": parts, "img_w": W, "img_h": H,
            "d": [(p.get("dx") if p.get("ok") else None) for p in parts],
            "dyv": [(p.get("dy") if p.get("ok") else None) for p in parts]}


def _bandscore(v, t, core, margin):
    if v is None:
        return 0.0
    e = abs(float(v) - float(t))
    core = float(core)
    margin = max(float(margin), 1e-9)
    if e <= core:
        return 1.0
    return round(max(0.0, min(1.0, 1.0 - (e - core) / margin)), 4)


def bands_readable(field):
    """Give 1 if every object band had enough structure to measure, else 0."""
    return 1.0 if int(field["n_struct"]) == len(field["parts"]) else 0.0


def parallax_match_score(field, core, margin):
    """Mean score of each nonzero target object's shift against its target."""
    parts = [p for p in field["parts"] if abs(float(p["target"])) > 1e-9]
    if not parts:
        return 0.0
    total = 0.0
    for p in parts:
        total += _bandscore(p.get("dx") if p.get("ok") else None, p["target"], core, margin)
    return round(total / len(parts), 4)


def depth_order_score(field, sep_min):
    """Share of object pairs whose measured shifts keep the target depth order."""
    parts = field["parts"]
    good = 0
    total = 0
    for i in range(len(parts)):
        for j in range(i + 1, len(parts)):
            ti, tj = float(parts[i]["target"]), float(parts[j]["target"])
            if abs(ti - tj) < 1e-9:
                continue
            total += 1
            di = parts[i].get("dx") if parts[i].get("ok") else None
            dj = parts[j].get("dx") if parts[j].get("ok") else None
            if di is None or dj is None:
                continue
            if (ti - tj) > 0 and (float(di) - float(dj)) >= float(sep_min):
                good += 1
            elif (ti - tj) < 0 and (float(dj) - float(di)) >= float(sep_min):
                good += 1
    return 0.0 if total == 0 else round(float(good) / total, 4)


def parallax_contrast_score(field, core, margin):
    """Score the shift gap between the zero parallax object and the strongest one."""
    parts = field["parts"]
    zs = [p for p in parts if abs(float(p["target"])) <= 1e-9]
    if not zs:
        return 0.0
    z = zs[0]
    mx = max(parts, key=lambda p: abs(float(p["target"])))
    dz = z.get("dx") if z.get("ok") else None
    dm = mx.get("dx") if mx.get("ok") else None
    if dz is None or dm is None:
        return 0.0
    return _bandscore(abs(float(dm)) - abs(float(dz)), abs(float(mx["target"])), core, margin)


def vertical_shift_score(field, core, margin):
    """Score the largest vertical shift between colour channels against zero."""
    shifts = [abs(float(p["dy"])) for p in field["parts"] if p.get("ok")]
    if not shifts:
        return 0.0
    return _bandscore(max(shifts), 0.0, core, margin)


def parallax_overlay(image, script, tag="parallax", mag=8.0, coh_min=0.20):
    import numpy as np
    import cv2
    from PIL import Image
    fld = disparity_field(image, script, coh_min=coh_min)
    pil = _pil(image)
    W0, H0 = pil.size
    foot = max(150, int(0.22 * H0))
    im = np.zeros((H0 + foot, W0, 3), np.uint8)
    im[:H0] = np.array(pil)
    im[H0:] = (16, 16, 18)
    lw = max(2, int(0.003 * min(H0, W0)))
    fs = 0.62 * min(W0, H0) / 1024.0
    YEL = (255, 215, 0)
    WHT = (255, 255, 255)
    parts = fld["parts"]
    imax = max(range(len(parts)), key=lambda k: abs(float(parts[k]["target"])))
    cellw = W0 // max(1, len(parts))
    for k, p in enumerate(parts):
        bx = p.get("box_px") or [0, 0, 10, 10]
        cv2.rectangle(im, (bx[0], bx[1]), (bx[2] - 1, bx[3] - 1), YEL, lw)
        px0 = k * cellw + int(0.03 * cellw)
        py0 = H0 + int(0.10 * foot)
        px1 = (k + 1) * cellw - int(0.03 * cellw)
        py1 = H0 + foot - int(0.06 * foot)
        cv2.rectangle(im, (px0, py0), (px1, py1), (34, 34, 40), -1)
        cv2.rectangle(im, (px0, py0), (px1, py1), YEL, max(1, lw // 2))
        cv2.arrowedLine(im, ((px0 + px1) // 2, py0), ((bx[0] + bx[2]) // 2, bx[3] - 1),
                        YEL, lw, tipLength=0.03)
        star = " *" if k == imax else ""
        meas = ("%+.2f%%" % p["dx"]) if p.get("ok") else "not a shifted copy"
        cv2.putText(im, "%s%s" % (str(p["name"]).upper(), star), (px0 + 10, py0 + int(0.19 * foot)),
                    cv2.FONT_HERSHEY_SIMPLEX, fs, WHT, max(1, lw - 1))
        cv2.putText(im, "measured %s" % meas, (px0 + 10, py0 + int(0.34 * foot)),
                    cv2.FONT_HERSHEY_SIMPLEX, fs * 0.85, YEL, max(1, lw - 1))
        cv2.putText(im, "script   %+.2f%%" % float(p["target"]),
                    (px0 + 10, py0 + int(0.47 * foot)),
                    cv2.FONT_HERSHEY_SIMPLEX, fs * 0.85, WHT, max(1, lw - 1))
        cv2.putText(im, "vertical %s" % (("%+.2f%%" % p["dy"]) if p.get("ok") else "--"),
                    (px0 + 10, py0 + int(0.60 * foot)),
                    cv2.FONT_HERSHEY_SIMPLEX, fs * 0.85, WHT, max(1, lw - 1))
        bx0 = px0 + 10
        room = (px1 - 10) - bx0
        lm = int(min(room, abs(float(p["dx"])) / 100.0 * W0 * float(mag))) if p.get("ok") else 0
        lt = int(min(room, abs(float(p["target"])) / 100.0 * W0 * float(mag)))
        yb = py0 + int(0.70 * foot)
        cv2.rectangle(im, (bx0, yb), (bx0 + max(lm, 2), yb + max(4, int(0.05 * foot))), YEL, -1)
        yb2 = py0 + int(0.79 * foot)
        cv2.rectangle(im, (bx0, yb2), (bx0 + max(lt, 2), yb2 + max(4, int(0.05 * foot))), WHT, -1)
    cv2.putText(im, "yellow bar = measured red-vs-cyan shift, white bar = shift the brief demands"
                    "  (bars x%d)" % int(mag),
                (12, H0 + int(0.06 * foot)), cv2.FONT_HERSHEY_SIMPLEX, fs * 0.8, (200, 200, 205),
                max(1, lw - 1))
    p = _overlay_path(image, tag)
    Image.fromarray(im).save(p)
    out = {"path": p, "n_ok": fld["n_ok"], "d": fld["d"], "dyv": fld["dyv"],
           "no_read": fld["no_read"]}
    return out


# end of disparity_field_code

# code: parallax_overlay_marked_code

def _pil(image):
    from PIL import Image
    return image.convert("RGB") if hasattr(image, "convert") else Image.open(str(image)).convert("RGB")


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
    return os.path.join(d, "e7bana_%s_%s.png" % (tag, h))


def _band_shift(rgb, box, lag_x=0.08, lag_y=0.035, coh_min=0.20):
    import numpy as np
    import cv2
    H, W = rgb.shape[:2]
    x0 = max(0, int(box[0] * W))
    y0 = max(0, int(box[1] * H))
    x1 = min(W, int(box[2] * W))
    y1 = min(H, int(box[3] * H))
    if x1 - x0 < 48 or y1 - y0 < 48:
        return {"ok": False, "why": "band_too_small", "box_px": [x0, y0, x1, y1]}
    R = rgb[y0:y1, x0:x1, 0].astype(np.float32)
    C = 0.5 * (rgb[y0:y1, x0:x1, 1].astype(np.float32) + rgb[y0:y1, x0:x1, 2].astype(np.float32))
    h, w = R.shape
    s = max(2.0, 0.05 * min(h, w))
    Rh = R - cv2.GaussianBlur(R, (0, 0), s)
    Ch = C - cv2.GaussianBlur(C, (0, 0), s)
    sr = float(Rh.std())
    sc = float(Ch.std())
    if sr < 0.35 or sc < 0.35:
        return {"ok": False, "why": "no_structure", "std_r": round(sr, 3), "std_c": round(sc, 3),
                "box_px": [x0, y0, x1, y1]}
    lx = min(max(4, int(lag_x * W)), (w - 48) // 2)
    ly = min(max(3, int(lag_y * H)), (h - 48) // 2)
    if lx < 3 or ly < 2:
        return {"ok": False, "why": "band_too_small", "box_px": [x0, y0, x1, y1]}
    Rh = (Rh / sr).astype(np.float32)
    Ch = (Ch / sc).astype(np.float32)
    res = cv2.matchTemplate(Rh, Ch[ly:h - ly, lx:w - lx], cv2.TM_CCOEFF_NORMED)
    _mn, mx, _ml, loc = cv2.minMaxLoc(res)
    px, py = int(loc[0]), int(loc[1])
    dx = float(px - lx)
    dy = float(py - ly)
    if 0 < px < res.shape[1] - 1:
        a, b, c = float(res[py, px - 1]), float(res[py, px]), float(res[py, px + 1])
        den = a - 2 * b + c
        if abs(den) > 1e-9 and abs(0.5 * (a - c) / den) <= 1.0:
            dx += 0.5 * (a - c) / den
    if 0 < py < res.shape[0] - 1:
        a, b, c = float(res[py - 1, px]), float(res[py, px]), float(res[py + 1, px])
        den = a - 2 * b + c
        if abs(den) > 1e-9 and abs(0.5 * (a - c) / den) <= 1.0:
            dy += 0.5 * (a - c) / den
    coh = float(mx)
    return {"ok": bool(coh >= float(coh_min)), "why": "" if coh >= float(coh_min) else "incoherent",
            "dx_px": round(dx, 2), "dy_px": round(dy, 2), "coh": round(coh, 3),
            "dx": round(100.0 * dx / W, 3), "dy": round(100.0 * dy / W, 3),
            "std_r": round(sr, 3), "std_c": round(sc, 3), "box_px": [x0, y0, x1, y1]}


def disparity_field(image, script, coh_min=0.20):
    import numpy as np
    rgb = np.asarray(_pil(image))
    if rgb.ndim == 2:
        rgb = np.dstack([rgb, rgb, rgb])
    H, W = rgb.shape[:2]
    parts = []
    for it in script:
        m = _band_shift(rgb, it["box"], coh_min=float(coh_min))
        m["name"] = it["name"]
        m["target"] = float(it["target"])
        parts.append(m)
    n_struct = sum(1 for p in parts if p.get("why") not in ("no_structure", "band_too_small"))
    return {"no_read": bool(n_struct == 0), "n_ok": sum(1 for p in parts if p.get("ok")),
            "n_struct": n_struct, "parts": parts, "img_w": W, "img_h": H,
            "d": [(p.get("dx") if p.get("ok") else None) for p in parts],
            "dyv": [(p.get("dy") if p.get("ok") else None) for p in parts]}


def _bandscore(v, t, core, margin):
    if v is None:
        return 0.0
    e = abs(float(v) - float(t))
    core = float(core)
    margin = max(float(margin), 1e-9)
    if e <= core:
        return 1.0
    return round(max(0.0, min(1.0, 1.0 - (e - core) / margin)), 4)


def bands_readable(fld):
    return 1.0 if int(fld["n_struct"]) == len(fld["parts"]) else 0.0


def parallax_match_score(fld, core, margin):
    ps = [p for p in fld["parts"] if abs(float(p["target"])) > 1e-9]
    if not ps:
        return 0.0
    tot = 0.0
    for p in ps:
        tot += _bandscore(p.get("dx") if p.get("ok") else None, p["target"], core, margin)
    return round(tot / len(ps), 4)


def depth_order_score(fld, sep_min):
    ps = fld["parts"]
    good = 0
    tot = 0
    for i in range(len(ps)):
        for j in range(i + 1, len(ps)):
            ti, tj = float(ps[i]["target"]), float(ps[j]["target"])
            if abs(ti - tj) < 1e-9:
                continue
            tot += 1
            di = ps[i].get("dx") if ps[i].get("ok") else None
            dj = ps[j].get("dx") if ps[j].get("ok") else None
            if di is None or dj is None:
                continue
            if (ti - tj) > 0 and (float(di) - float(dj)) >= float(sep_min):
                good += 1
            elif (ti - tj) < 0 and (float(dj) - float(di)) >= float(sep_min):
                good += 1
    return 0.0 if tot == 0 else round(float(good) / tot, 4)


def parallax_contrast_score(fld, core, margin):
    ps = fld["parts"]
    zs = [p for p in ps if abs(float(p["target"])) <= 1e-9]
    if not zs:
        return 0.0
    z = zs[0]
    mx = max(ps, key=lambda p: abs(float(p["target"])))
    dz = z.get("dx") if z.get("ok") else None
    dm = mx.get("dx") if mx.get("ok") else None
    if dz is None or dm is None:
        return 0.0
    return _bandscore(abs(float(dm)) - abs(float(dz)), abs(float(mx["target"])), core, margin)


def vertical_shift_score(fld, core, margin):
    vs = [abs(float(p["dy"])) for p in fld["parts"] if p.get("ok")]
    if not vs:
        return 0.0
    return _bandscore(max(vs), 0.0, core, margin)


def parallax_overlay(image, script, tag="parallax", mag=8.0, coh_min=0.20):
    import numpy as np
    import cv2
    from PIL import Image
    fld = disparity_field(image, script, coh_min=coh_min)
    pil = _pil(image)
    W0, H0 = pil.size
    foot = max(150, int(0.22 * H0))
    im = np.zeros((H0 + foot, W0, 3), np.uint8)
    im[:H0] = np.array(pil)
    im[H0:] = (16, 16, 18)
    lw = max(2, int(0.003 * min(H0, W0)))
    fs = 0.62 * min(W0, H0) / 1024.0
    YEL = (255, 215, 0)
    WHT = (255, 255, 255)
    parts = fld["parts"]
    imax = max(range(len(parts)), key=lambda k: abs(float(parts[k]["target"])))
    cellw = W0 // max(1, len(parts))
    for k, p in enumerate(parts):
        bx = p.get("box_px") or [0, 0, 10, 10]
        cv2.rectangle(im, (bx[0], bx[1]), (bx[2] - 1, bx[3] - 1), YEL, lw)
        _mk("measured_objects", "rects",
            [0.5 * (bx[0] + bx[2] - 1), 0.5 * (bx[1] + bx[3] - 1),
             float(bx[2] - 1 - bx[0]), float(bx[3] - 1 - bx[1])])
        px0 = k * cellw + int(0.03 * cellw)
        py0 = H0 + int(0.10 * foot)
        px1 = (k + 1) * cellw - int(0.03 * cellw)
        py1 = H0 + foot - int(0.06 * foot)
        cv2.rectangle(im, (px0, py0), (px1, py1), (34, 34, 40), -1)
        cv2.rectangle(im, (px0, py0), (px1, py1), YEL, max(1, lw // 2))
        cv2.arrowedLine(im, ((px0 + px1) // 2, py0), ((bx[0] + bx[2]) // 2, bx[3] - 1),
                        YEL, lw, tipLength=0.03)
        star = " *" if k == imax else ""
        meas = ("%+.2f%%" % p["dx"]) if p.get("ok") else "not a shifted copy"
        cv2.putText(im, "%s%s" % (str(p["name"]).upper(), star), (px0 + 10, py0 + int(0.19 * foot)),
                    cv2.FONT_HERSHEY_SIMPLEX, fs, WHT, max(1, lw - 1))
        cv2.putText(im, "measured %s" % meas, (px0 + 10, py0 + int(0.34 * foot)),
                    cv2.FONT_HERSHEY_SIMPLEX, fs * 0.85, YEL, max(1, lw - 1))
        cv2.putText(im, "script   %+.2f%%" % float(p["target"]),
                    (px0 + 10, py0 + int(0.47 * foot)),
                    cv2.FONT_HERSHEY_SIMPLEX, fs * 0.85, WHT, max(1, lw - 1))
        cv2.putText(im, "vertical %s" % (("%+.2f%%" % p["dy"]) if p.get("ok") else "--"),
                    (px0 + 10, py0 + int(0.60 * foot)),
                    cv2.FONT_HERSHEY_SIMPLEX, fs * 0.85, WHT, max(1, lw - 1))
        bx0 = px0 + 10
        room = (px1 - 10) - bx0
        lm = int(min(room, abs(float(p["dx"])) / 100.0 * W0 * float(mag))) if p.get("ok") else 0
        lt = int(min(room, abs(float(p["target"])) / 100.0 * W0 * float(mag)))
        yb = py0 + int(0.70 * foot)
        cv2.rectangle(im, (bx0, yb), (bx0 + max(lm, 2), yb + max(4, int(0.05 * foot))), YEL, -1)
        yb2 = py0 + int(0.79 * foot)
        cv2.rectangle(im, (bx0, yb2), (bx0 + max(lt, 2), yb2 + max(4, int(0.05 * foot))), WHT, -1)
    cv2.putText(im, "yellow bar = measured red-vs-cyan shift, white bar = shift the brief demands"
                    "  (bars x%d)" % int(mag),
                (12, H0 + int(0.06 * foot)), cv2.FONT_HERSHEY_SIMPLEX, fs * 0.8, (200, 200, 205),
                max(1, lw - 1))
    p = _overlay_path(image, tag)
    Image.fromarray(im).save(p)
    out = {"path": p, "n_ok": fld["n_ok"], "d": fld["d"], "dyv": fld["dyv"],
           "no_read": fld["no_read"]}
    return out


def parallax_overlay_marked(image, script, tag="parallax", mag=8.0, coh_min=0.20):
    """Draw the measured parallax overlay and attach marks for the measured objects."""
    _mk_reset("measured_objects")
    r = dict(parallax_overlay(image, script, tag, mag, coh_min))
    src = image if hasattr(image, "size") else str(image)
    r.update(_ovmark_pack(src))
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


# end of parallax_overlay_marked_code
