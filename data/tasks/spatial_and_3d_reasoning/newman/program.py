# code: helpers
from genolympiad.task_helpers import to_float
# end of helpers

# code: read_newman_code
import os

_NEW_CACHE = {}
_CIRC_CACHE = {}


def _prep(image, cap=1600):
    import numpy as np
    import cv2
    from PIL import Image
    key = str(image)
    try:
        st = os.stat(str(image))
        key = "%s|%s|%s" % (key, st.st_mtime_ns, st.st_size)
    except Exception:
        pass
    hit = _NEW_CACHE.get(key)
    if hit is not None:
        return hit
    pil = image if hasattr(image, "convert") else Image.open(str(image))
    a = np.asarray(pil.convert("RGB")).astype("uint8")
    H, W = a.shape[:2]
    if max(H, W) > cap:
        s = cap / float(max(H, W))
        a = cv2.resize(a, (max(8, int(W * s)), max(8, int(H * s))),
                       interpolation=cv2.INTER_AREA)
    g = cv2.cvtColor(a, cv2.COLOR_RGB2GRAY)
    if len(_NEW_CACHE) > 16:
        _NEW_CACHE.clear()
    _NEW_CACHE[key] = (a, g)
    return a, g


def _ink(g):
    import cv2
    th = cv2.threshold(g, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    dark = 255 - th
    return dark if dark.mean() < th.mean() else th


def _bandfrac(err, core, margin):
    f = 1.0 - max(0.0, float(err) - float(core)) / max(float(margin), 1e-9)
    return round(min(1.0, max(0.0, f)), 4)


def _adiff(a, b, period=360.0):
    d = abs(float(a) - float(b)) % period
    return min(d, period - d)


def _ring_coverage(ink, cx, cy, R, tol=2.5):
    import math
    H, W = ink.shape
    hits = 0
    for t in range(0, 360, 2):
        a = math.radians(t)
        ok = False
        rr = R - tol
        while rr <= R + tol:
            x = int(round(cx + rr * math.cos(a)))
            y = int(round(cy - rr * math.sin(a)))
            if 0 <= x < W and 0 <= y < H and ink[y, x]:
                ok = True
                break
            rr += 1.0
        hits += 1 if ok else 0
    return hits / 180.0


def find_circles(image, k=1):
    import cv2
    _a, g = _prep(image)
    ckey = None
    try:
        st = os.stat(str(image))
        ckey = (str(image), st.st_mtime_ns, st.st_size, int(k))
        if ckey in _CIRC_CACHE:
            return _CIRC_CACHE[ckey]
    except Exception:
        pass
    ink = _ink(g)
    H, W = g.shape
    m = min(H, W)
    blur = cv2.medianBlur(g, 5)
    best = []
    for p2 in (46, 40, 34, 52, 30):
        c = cv2.HoughCircles(blur, cv2.HOUGH_GRADIENT, dp=1,
                             minDist=int(0.20 * m), param1=110, param2=p2,
                             minRadius=int(0.075 * m), maxRadius=int(0.45 * m))
        if c is None:
            continue
        keep = []
        for v in c[0]:
            cx, cy, r = float(v[0]), float(v[1]), float(v[2])
            bc = (cx, cy, r, _ring_coverage(ink, cx, cy, r))
            for dx in (-6, -3, 0, 3, 6):
                for dy in (-6, -3, 0, 3, 6):
                    for dr in (-8, -4, 0, 4, 8):
                        cov = _ring_coverage(ink, cx + dx, cy + dy, r + dr)
                        if cov > bc[3]:
                            bc = (cx + dx, cy + dy, r + dr, cov)
            if bc[3] < 0.55:
                continue
            if any((bc[0] - x) ** 2 + (bc[1] - y) ** 2 < (0.9 * (bc[2] + rr)) ** 2
                   for x, y, rr, _c in keep):
                continue
            keep.append(bc)
            if len(keep) >= int(k):
                break
        if len(keep) > len(best):
            best = keep
        if len(best) >= int(k):
            break
    best.sort(key=lambda t: t[0])
    out = [(x, y, r) for x, y, r, _c in best]
    if ckey is not None:
        if len(_CIRC_CACHE) > 24:
            _CIRC_CACHE.clear()
        _CIRC_CACHE[ckey] = out
    return out


def _bonds_about(ink, cx, cy, R, cov_floor=0.45):
    import math
    import numpy as np
    H, W = ink.shape

    def cov(theta_deg, r0, r1):
        a = math.radians(90.0 - theta_deg)
        n = hitn = 0
        rr = r0
        while rr < r1:
            x = int(round(cx + rr * math.cos(a)))
            y = int(round(cy - rr * math.sin(a)))
            n += 1
            if 0 <= x < W and 0 <= y < H and ink[y, x]:
                hitn += 1
            rr += 1.5
        return hitn / float(max(1, n))

    inner, outer = [], []
    for t in range(360):
        ci_ = cov(t, 0.28 * R, 0.60 * R)
        co_ = cov(t, 1.12 * R, 1.45 * R)
        if ci_ >= cov_floor:
            inner.append(t)
        if co_ >= cov_floor:
            outer.append(t)

    def cluster(vals, tol=8):
        if not vals:
            return []
        vals = sorted(vals)
        groups, cur = [], [vals[0]]
        for v in vals[1:]:
            if v - cur[-1] <= tol:
                cur.append(v)
            else:
                groups.append(cur)
                cur = [v]
        groups.append(cur)
        if len(groups) > 1 and (groups[0][0] + 360 - groups[-1][-1]) <= tol:
            groups[0] = groups[-1] + [x + 360 for x in groups[0]]
            groups.pop()
        return [round(float(np.mean(gp)) % 360.0, 1) for gp in groups]

    ci, co = cluster(inner), cluster(outer)
    front = [a for a in co if any(_adiff(a, b) < 12 for b in ci)]
    back = [a for a in co if a not in front]
    return sorted(front), sorted(back)


def read_newman(image, n_circles, dihedrals, core=5.0, margin=4.0, cov_floor=0.45):
    """Find each Newman circle and score its bonds and back bond twist against the reference."""
    import numpy as np
    circles = find_circles(image, n_circles)
    if not circles:
        return {"no_read": True, "reason": "no_circle", "n_circles": 0,
                "frac_structure": 0.0, "frac_offset": 0.0, "frac_triad": 0.0,
                "frac_clock_anchor": 0.0}
    _a, g = _prep(image)
    ink = _ink(g)
    target_twists = [float(d) for d in (dihedrals if isinstance(dihedrals, (list, tuple))
                               else [dihedrals])]
    circle_records = []
    for i in range(len(target_twists)):
        if i >= len(circles):
            circle_records.append({"found": False, "structure": 0.0, "offset": 0.0, "triad": 0.0,
                        "clock": 0.0})
            continue
        cx, cy, R = circles[i]
        front, back = _bonds_about(ink, cx, cy, R, cov_floor)
        rec = {"found": True, "circle": [round(cx), round(cy), round(R)],
               "front_deg": front, "back_deg": back,
               "n_front": len(front), "n_back": len(back)}
        rec["structure"] = 1.0 if (len(front) == 3 and len(back) == 3) else 0.0
        if len(front) >= 2:
            gaps = sorted(front)
            devs = []
            for j in range(len(gaps)):
                d = (gaps[(j + 1) % len(gaps)] - gaps[j]) % 360.0
                devs.append(abs(d - 120.0))
            rec["triad_max_dev_deg"] = round(max(devs), 1)
            rec["triad"] = _bandfrac(max(devs), 5.0, 5.0) if len(front) == 3 else 0.0
        else:
            rec["triad_max_dev_deg"] = None
            rec["triad"] = 0.0
        if front:
            phi = float(np.median([a % 120.0 for a in front]))
            rec["front_phase_mod120"] = round(phi, 1)
            rec["clock"] = _bandfrac(min(phi, 120.0 - phi), 6.0, 6.0)
            exp = [(phi + target_twists[i] + 120.0 * k) % 360.0 for k in range(3)]
            rec["expected_back_deg"] = [round(e, 1) for e in exp]
            errs, s = [], 0.0
            for e in exp:
                if back:
                    err = min(_adiff(e, b) for b in back)
                else:
                    err = 180.0
                errs.append(round(err, 1))
                s += _bandfrac(err, core, margin)
            rec["back_errs_deg"] = errs
            rec["offset"] = round(s / float(max(3, len(back))), 4)
            if len(back) == 3 and len(front) == 3:
                rec["offset_mod120"] = round(
                    float(np.median([(b - phi) % 120.0 for b in back])), 1)
        else:
            rec["clock"] = 0.0
            rec["offset"] = 0.0
        circle_records.append(rec)
    n = float(len(target_twists))
    return {"no_read": False, "n_circles": len(circles), "n_circles_gt": len(target_twists),
            "per_circle": circle_records,
            "frac_structure": round(sum(p["structure"] for p in circle_records) / n, 4),
            "frac_offset": round(sum(p["offset"] for p in circle_records) / n, 4),
            "frac_triad": round(sum(p["triad"] for p in circle_records) / n, 4),
            "frac_clock_anchor": round(sum(p["clock"] for p in circle_records) / n, 4)}


def _overlay_path(image, tag):
    import hashlib
    import tempfile
    d = os.path.join(tempfile.gettempdir(), "genolympiad_overlay")
    try:
        os.makedirs(d, exist_ok=True)
    except Exception:
        pass
    h = hashlib.md5(("%s|%s" % (str(image), tag)).encode("utf-8", "replace")).hexdigest()[:12]
    return os.path.join(d, "e9cnew_%s_%s.png" % (tag, h))


def newman_overlay(image, n_circles, dihedrals, tag="newman"):
    """Draw the found circles, bonds and expected back bonds on the image."""
    import math
    import numpy as np
    import cv2
    from PIL import Image
    m = read_newman(image, n_circles, dihedrals)
    a, _g = _prep(image)
    im = np.array(a).copy()
    H, W = im.shape[:2]
    lw = max(2, int(0.0025 * min(H, W)))
    fs = 0.60 * min(W, H) / 1024.0

    def pt(cx, cy, ang, r):
        t = math.radians(90.0 - ang)
        return (int(cx + r * math.cos(t)), int(cy - r * math.sin(t)))

    if not m.get("no_read"):
        for rec in m["per_circle"]:
            if not rec.get("found"):
                continue
            cx, cy, R = rec["circle"]
            cv2.circle(im, (cx, cy), R, (0, 190, 200), max(1, lw - 1))
            for ang in rec.get("front_deg", []):
                cv2.line(im, pt(cx, cy, ang, 0.30 * R), pt(cx, cy, ang, 1.05 * R),
                         (255, 140, 0), lw)
            for ang in rec.get("back_deg", []):
                cv2.line(im, pt(cx, cy, ang, 1.02 * R), pt(cx, cy, ang, 1.40 * R),
                         (220, 0, 200), lw)
            for j, ang in enumerate(rec.get("expected_back_deg", [])):
                cv2.line(im, pt(cx, cy, ang, 1.46 * R), pt(cx, cy, ang, 1.66 * R),
                         (0, 190, 0), lw + 1)
                tx, ty = pt(cx, cy, ang, 1.78 * R)
                cv2.putText(im, "%.0f" % rec["back_errs_deg"][j], (tx - 18, ty + 6),
                            cv2.FONT_HERSHEY_SIMPLEX, fs, (0, 190, 0), lw)
    cap = ["orange = a front bond found (ink inside the rim as well as outside);  magenta = a "
           "back bond found (ink outside only);  green = where the committed twist puts a back "
           "bond, labelled with the error in degrees",
           "projections %d/%d   front+back complete %.2f   twist credit %.2f   front triad "
           "%.2f" % (m.get("n_circles", 0), m.get("n_circles_gt", 0),
                     m.get("frac_structure", 0.0), m.get("frac_offset", 0.0),
                     m.get("frac_triad", 0.0))]
    cfs = min(fs, 0.80 * W / max(len(cap[0]), len(cap[1])) / 9.0)
    lh = int(30 * cfs * 2)
    strip = np.full((2 * lh + 16, W, 3), 18, dtype=im.dtype)
    for i, line in enumerate(cap):
        cv2.putText(strip, line, (10, (i + 1) * lh), cv2.FONT_HERSHEY_SIMPLEX, cfs,
                    (245, 245, 245), max(1, lw - 1))
    im = np.vstack([im, strip])
    p = _overlay_path(image, tag)
    Image.fromarray(im).save(p)
    out = dict(m)
    out["path"] = p
    return out

# end of read_newman_code

# code: f_code
def full_credit(n_circles):
    """Always score 1; the circle count is only recorded."""
    return 1.0

# end of f_code

# code: newman_marks_code
import os

_NEW_CACHE = {}
_CIRC_CACHE = {}


def _prep(image, cap=1600):
    import numpy as np
    import cv2
    from PIL import Image
    key = str(image)
    try:
        st = os.stat(str(image))
        key = "%s|%s|%s" % (key, st.st_mtime_ns, st.st_size)
    except Exception:
        pass
    hit = _NEW_CACHE.get(key)
    if hit is not None:
        return hit
    pil = image if hasattr(image, "convert") else Image.open(str(image))
    a = np.asarray(pil.convert("RGB")).astype("uint8")
    H, W = a.shape[:2]
    if max(H, W) > cap:
        s = cap / float(max(H, W))
        a = cv2.resize(a, (max(8, int(W * s)), max(8, int(H * s))),
                       interpolation=cv2.INTER_AREA)
    g = cv2.cvtColor(a, cv2.COLOR_RGB2GRAY)
    if len(_NEW_CACHE) > 16:
        _NEW_CACHE.clear()
    _NEW_CACHE[key] = (a, g)
    return a, g


def _ink(g):
    import cv2
    th = cv2.threshold(g, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    dark = 255 - th
    return dark if dark.mean() < th.mean() else th


def _bandfrac(err, core, margin):
    f = 1.0 - max(0.0, float(err) - float(core)) / max(float(margin), 1e-9)
    return round(min(1.0, max(0.0, f)), 4)


def _adiff(a, b, period=360.0):
    d = abs(float(a) - float(b)) % period
    return min(d, period - d)


def _ring_coverage(ink, cx, cy, R, tol=2.5):
    import math
    H, W = ink.shape
    hits = 0
    for t in range(0, 360, 2):
        a = math.radians(t)
        ok = False
        rr = R - tol
        while rr <= R + tol:
            x = int(round(cx + rr * math.cos(a)))
            y = int(round(cy - rr * math.sin(a)))
            if 0 <= x < W and 0 <= y < H and ink[y, x]:
                ok = True
                break
            rr += 1.0
        hits += 1 if ok else 0
    return hits / 180.0


def find_circles(image, k=1):
    import cv2
    _a, g = _prep(image)
    ckey = None
    try:
        st = os.stat(str(image))
        ckey = (str(image), st.st_mtime_ns, st.st_size, int(k))
        if ckey in _CIRC_CACHE:
            return _CIRC_CACHE[ckey]
    except Exception:
        pass
    ink = _ink(g)
    H, W = g.shape
    m = min(H, W)
    blur = cv2.medianBlur(g, 5)
    best = []
    for p2 in (46, 40, 34, 52, 30):
        c = cv2.HoughCircles(blur, cv2.HOUGH_GRADIENT, dp=1,
                             minDist=int(0.20 * m), param1=110, param2=p2,
                             minRadius=int(0.075 * m), maxRadius=int(0.45 * m))
        if c is None:
            continue
        keep = []
        for v in c[0]:
            cx, cy, r = float(v[0]), float(v[1]), float(v[2])
            bc = (cx, cy, r, _ring_coverage(ink, cx, cy, r))
            for dx in (-6, -3, 0, 3, 6):
                for dy in (-6, -3, 0, 3, 6):
                    for dr in (-8, -4, 0, 4, 8):
                        cov = _ring_coverage(ink, cx + dx, cy + dy, r + dr)
                        if cov > bc[3]:
                            bc = (cx + dx, cy + dy, r + dr, cov)
            if bc[3] < 0.55:
                continue
            if any((bc[0] - x) ** 2 + (bc[1] - y) ** 2 < (0.9 * (bc[2] + rr)) ** 2
                   for x, y, rr, _c in keep):
                continue
            keep.append(bc)
            if len(keep) >= int(k):
                break
        if len(keep) > len(best):
            best = keep
        if len(best) >= int(k):
            break
    best.sort(key=lambda t: t[0])
    out = [(x, y, r) for x, y, r, _c in best]
    if ckey is not None:
        if len(_CIRC_CACHE) > 24:
            _CIRC_CACHE.clear()
        _CIRC_CACHE[ckey] = out
    return out


def _bonds_about(ink, cx, cy, R, cov_floor=0.45):
    import math
    import numpy as np
    H, W = ink.shape

    def cov(theta_deg, r0, r1):
        a = math.radians(90.0 - theta_deg)
        n = hitn = 0
        rr = r0
        while rr < r1:
            x = int(round(cx + rr * math.cos(a)))
            y = int(round(cy - rr * math.sin(a)))
            n += 1
            if 0 <= x < W and 0 <= y < H and ink[y, x]:
                hitn += 1
            rr += 1.5
        return hitn / float(max(1, n))

    inner, outer = [], []
    for t in range(360):
        ci_ = cov(t, 0.28 * R, 0.60 * R)
        co_ = cov(t, 1.12 * R, 1.45 * R)
        if ci_ >= cov_floor:
            inner.append(t)
        if co_ >= cov_floor:
            outer.append(t)

    def cluster(vals, tol=8):
        if not vals:
            return []
        vals = sorted(vals)
        groups, cur = [], [vals[0]]
        for v in vals[1:]:
            if v - cur[-1] <= tol:
                cur.append(v)
            else:
                groups.append(cur)
                cur = [v]
        groups.append(cur)
        if len(groups) > 1 and (groups[0][0] + 360 - groups[-1][-1]) <= tol:
            groups[0] = groups[-1] + [x + 360 for x in groups[0]]
            groups.pop()
        return [round(float(np.mean(gp)) % 360.0, 1) for gp in groups]

    ci, co = cluster(inner), cluster(outer)
    front = [a for a in co if any(_adiff(a, b) < 12 for b in ci)]
    back = [a for a in co if a not in front]
    return sorted(front), sorted(back)


def read_newman(image, n_circles, dihedrals, core=5.0, margin=4.0, cov_floor=0.45):
    import numpy as np
    circles = find_circles(image, n_circles)
    if not circles:
        return {"no_read": True, "reason": "no_circle", "n_circles": 0,
                "frac_structure": 0.0, "frac_offset": 0.0, "frac_triad": 0.0,
                "frac_clock_anchor": 0.0}
    _a, g = _prep(image)
    ink = _ink(g)
    want = [float(d) for d in (dihedrals if isinstance(dihedrals, (list, tuple))
                               else [dihedrals])]
    per = []
    for i in range(len(want)):
        if i >= len(circles):
            per.append({"found": False, "structure": 0.0, "offset": 0.0, "triad": 0.0,
                        "clock": 0.0})
            continue
        cx, cy, R = circles[i]
        front, back = _bonds_about(ink, cx, cy, R, cov_floor)
        rec = {"found": True, "circle": [round(cx), round(cy), round(R)],
               "front_deg": front, "back_deg": back,
               "n_front": len(front), "n_back": len(back)}
        rec["structure"] = 1.0 if (len(front) == 3 and len(back) == 3) else 0.0
        if len(front) >= 2:
            gaps = sorted(front)
            devs = []
            for j in range(len(gaps)):
                d = (gaps[(j + 1) % len(gaps)] - gaps[j]) % 360.0
                devs.append(abs(d - 120.0))
            rec["triad_max_dev_deg"] = round(max(devs), 1)
            rec["triad"] = _bandfrac(max(devs), 5.0, 5.0) if len(front) == 3 else 0.0
        else:
            rec["triad_max_dev_deg"] = None
            rec["triad"] = 0.0
        if front:
            phi = float(np.median([a % 120.0 for a in front]))
            rec["front_phase_mod120"] = round(phi, 1)
            rec["clock"] = _bandfrac(min(phi, 120.0 - phi), 6.0, 6.0)
            exp = [(phi + want[i] + 120.0 * k) % 360.0 for k in range(3)]
            rec["expected_back_deg"] = [round(e, 1) for e in exp]
            errs, s = [], 0.0
            for e in exp:
                if back:
                    err = min(_adiff(e, b) for b in back)
                else:
                    err = 180.0
                errs.append(round(err, 1))
                s += _bandfrac(err, core, margin)
            rec["back_errs_deg"] = errs
            rec["offset"] = round(s / float(max(3, len(back))), 4)
            if len(back) == 3 and len(front) == 3:
                rec["offset_mod120"] = round(
                    float(np.median([(b - phi) % 120.0 for b in back])), 1)
        else:
            rec["clock"] = 0.0
            rec["offset"] = 0.0
        per.append(rec)
    n = float(len(want))
    return {"no_read": False, "n_circles": len(circles), "n_circles_gt": len(want),
            "per_circle": per,
            "frac_structure": round(sum(p["structure"] for p in per) / n, 4),
            "frac_offset": round(sum(p["offset"] for p in per) / n, 4),
            "frac_triad": round(sum(p["triad"] for p in per) / n, 4),
            "frac_clock_anchor": round(sum(p["clock"] for p in per) / n, 4)}


def _overlay_path(image, tag):
    import hashlib
    import tempfile
    d = os.path.join(tempfile.gettempdir(), "genolympiad_overlay")
    try:
        os.makedirs(d, exist_ok=True)
    except Exception:
        pass
    h = hashlib.md5(("%s|%s" % (str(image), tag)).encode("utf-8", "replace")).hexdigest()[:12]
    return os.path.join(d, "e9cnew_%s_%s.png" % (tag, h))


def newman_overlay(image, n_circles, dihedrals, tag="newman"):
    import math
    import numpy as np
    import cv2
    from PIL import Image
    m = read_newman(image, n_circles, dihedrals)
    a, _g = _prep(image)
    im = np.array(a).copy()
    H, W = im.shape[:2]
    lw = max(2, int(0.0025 * min(H, W)))
    fs = 0.60 * min(W, H) / 1024.0

    def pt(cx, cy, ang, r):
        t = math.radians(90.0 - ang)
        return (int(cx + r * math.cos(t)), int(cy - r * math.sin(t)))

    if not m.get("no_read"):
        for rec in m["per_circle"]:
            if not rec.get("found"):
                continue
            cx, cy, R = rec["circle"]
            cv2.circle(im, (cx, cy), R, (0, 190, 200), max(1, lw - 1))
            for ang in rec.get("front_deg", []):
                cv2.line(im, pt(cx, cy, ang, 0.30 * R), pt(cx, cy, ang, 1.05 * R),
                         (255, 140, 0), lw)
            for ang in rec.get("back_deg", []):
                cv2.line(im, pt(cx, cy, ang, 1.02 * R), pt(cx, cy, ang, 1.40 * R),
                         (220, 0, 200), lw)
            for j, ang in enumerate(rec.get("expected_back_deg", [])):
                cv2.line(im, pt(cx, cy, ang, 1.46 * R), pt(cx, cy, ang, 1.66 * R),
                         (0, 190, 0), lw + 1)
                tx, ty = pt(cx, cy, ang, 1.78 * R)
                cv2.putText(im, "%.0f" % rec["back_errs_deg"][j], (tx - 18, ty + 6),
                            cv2.FONT_HERSHEY_SIMPLEX, fs, (0, 190, 0), lw)
    cap = ["orange = a front bond found (ink inside the rim as well as outside);  magenta = a "
           "back bond found (ink outside only);  green = where the committed twist puts a back "
           "bond, labelled with the error in degrees",
           "projections %d/%d   front+back complete %.2f   twist credit %.2f   front triad "
           "%.2f" % (m.get("n_circles", 0), m.get("n_circles_gt", 0),
                     m.get("frac_structure", 0.0), m.get("frac_offset", 0.0),
                     m.get("frac_triad", 0.0))]
    cfs = min(fs, 0.80 * W / max(len(cap[0]), len(cap[1])) / 9.0)
    lh = int(30 * cfs * 2)
    strip = np.full((2 * lh + 16, W, 3), 18, dtype=im.dtype)
    for i, line in enumerate(cap):
        cv2.putText(strip, line, (10, (i + 1) * lh), cv2.FONT_HERSHEY_SIMPLEX, cfs,
                    (245, 245, 245), max(1, lw - 1))
    im = np.vstack([im, strip])
    p = _overlay_path(image, tag)
    Image.fromarray(im).save(p)
    out = dict(m)
    out["path"] = p
    return out

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


def newman_marks(image, n_circles, dihedrals):
    """Collect overlay marks for the measured bonds and the expected back bonds."""
    import math
    from PIL import Image as _I
    _mk_reset("measured", "want")
    im = image if hasattr(image, "size") else _I.open(str(image))
    IW, IH = float(im.size[0]), float(im.size[1])
    m = read_newman(image, n_circles, dihedrals)
    if m.get("no_read"):
        return {"no_read": True, "n_marks": 0, "reason": m.get("reason")}
    a, _g = _prep(image)
    H, W = int(a.shape[0]), int(a.shape[1])

    def pt(cx, cy, ang, r):
        t = math.radians(90.0 - float(ang))
        return [cx + r * math.cos(t), cy - r * math.sin(t)]
    n = 0
    for rec in (m.get("per_circle") or []):
        if not rec.get("found"):
            continue
        cx, cy, R = [float(v) for v in rec["circle"]]
        _mk("measured", "circles", [cx, cy, 2.0 * R])
        for ang in (rec.get("front_deg") or []):
            _mk("measured", "polylines", [pt(cx, cy, ang, 0.30 * R), pt(cx, cy, ang, 1.05 * R)])
            n += 1
        for ang in (rec.get("back_deg") or []):
            _mk("measured", "polylines", [pt(cx, cy, ang, 1.02 * R), pt(cx, cy, ang, 1.40 * R)])
            n += 1
        for ang in (rec.get("expected_back_deg") or []):
            _mk("want", "polylines", [pt(cx, cy, ang, 1.05 * R), pt(cx, cy, ang, 1.60 * R)])
            n += 1
    if not n:
        return {"no_read": True, "n_marks": 0, "reason": "no_bonds"}
    _mk_scale(max(IW, IH) / float(max(W, H)))
    out = {"no_read": False, "n_bonds": n}
    out.update(_ovmark_pack(im))
    return out

# end of newman_marks_code
