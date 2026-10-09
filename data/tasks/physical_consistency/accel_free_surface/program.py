# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# shared code: code_44cca20cfc55

def container_phrases(node):
    """Name each found container by its position, left to right or top to bottom."""
    bs = []
    for b in ((node or {}).get("geometry") or []):
        try:
            y0, x0, y1, x1 = [float(v) for v in b[:4]]
        except Exception:
            continue
        cx, cy = (x0 + x1) / 2.0, (y0 + y1) / 2.0
        if any(abs(cx - p[0]) < 1.0 and abs(cy - p[1]) < 1.0 for p in bs):
            continue
        bs.append([cx, cy])
    if not bs:
        return {"c0": "container", "c1": "container", "c2": "container", "c3": "container",
                "c4": "container"}
    xs = [b[0] for b in bs]
    ys = [b[1] for b in bs]
    across = (max(xs) - min(xs)) >= (max(ys) - min(ys))
    bs.sort(key=(lambda b: b[0]) if across else (lambda b: b[1]))
    n = len(bs)
    if across:
        names = ["leftmost", "second from the left", "third from the left",
                 "fourth from the left", "fifth from the left"]
    else:
        names = ["topmost", "second from the top", "third from the top",
                 "fourth from the top", "fifth from the top"]
    out = {}
    for i in range(5):
        out["c%d" % i] = ("the %s container in the picture" % names[i]) if i < n else "container"
    return out

# end of code_44cca20cfc55

# code: f_code

import math
import struct


def image_width_height(image):
    try:
        if hasattr(image, "size") and not isinstance(image, (str, bytes)):
            w, h = image.size
            return float(w), float(h)
    except Exception:
        pass
    try:
        with open(str(image), "rb") as fh:
            head = fh.read(64)
            if head[:8] == b"\x89PNG\r\n\x1a\n":
                w, h = struct.unpack(">II", head[16:24])
                return float(w), float(h)
            fh.seek(0)
            data = fh.read()
        i = 2
        while i < len(data) - 9:
            if data[i] != 0xFF:
                i += 1
                continue
            mark = data[i + 1]
            if 0xC0 <= mark <= 0xCF and mark not in (0xC4, 0xC8, 0xCC):
                h, w = struct.unpack(">HH", data[i + 5:i + 9])
                return float(w), float(h)
            i += 2 + struct.unpack(">H", data[i + 2:i + 4])[0]
    except Exception:
        pass
    return None, None


def _distinct(bs, thr=0.85):
    kept = []
    for b in bs:
        dup = False
        for k in kept:
            ix = max(0.0, min(b["x1"], k["x1"]) - max(b["x0"], k["x0"]))
            iy = max(0.0, min(b["y1"], k["y1"]) - max(b["y0"], k["y0"]))
            inter = ix * iy
            ua = (b["x1"] - b["x0"]) * (b["y1"] - b["y0"])
            ub = (k["x1"] - k["x0"]) * (k["y1"] - k["y0"])
            if inter > 0 and inter / max(1e-9, ua + ub - inter) >= thr:
                dup = True
                break
        if not dup:
            kept.append(b)
    return kept


def bodies(node):
    bs = []
    for b in ((node or {}).get("geometry") or []):
        try:
            y0, x0, y1, x1 = [float(v) for v in b[:4]]
        except Exception:
            continue
        if y1 - y0 <= 0 or x1 - x0 <= 0:
            continue
        bs.append({"cx": (x0 + x1) / 2.0, "cy": (y0 + y1) / 2.0, "x0": x0, "x1": x1,
                   "y0": y0, "y1": y1})
    bs = _distinct(bs)
    if not bs:
        return []
    xs = [b["cx"] for b in bs]
    ys = [b["cy"] for b in bs]
    across = (max(xs) - min(xs)) >= (max(ys) - min(ys))
    bs.sort(key=(lambda b: b["cx"]) if across else (lambda b: b["cy"]))
    return bs


def _side(ans):
    s = str(ans or "").lower()
    if "level" in s or "flat" in s or "neither" in s or "same" in s:
        return 0
    if "left" in s:
        return 1
    if "right" in s:
        return -1
    return None


def tilts(image, bod, sd, lines):
    bs = bodies(bod)
    ans = list((sd or {}).get("answers") or [])
    W, H = image_width_height(image)
    out = {"n_found": len(bs), "tilt": [], "sign": [], "n_lines": 0}
    for i, b in enumerate(bs):
        out["sign"].append(_side(ans[i]) if i < len(ans) else None)
    for i in range(len(bs)):
        g = (lines[i] or {}).get("geometry") if i < len(lines) else None
        if not g or len(g) < 4 or not W:
            out["tilt"].append(None)
            continue
        y0, x0, y1, x1 = [float(v) for v in g[:4]]
        px0, py0 = x0 * W / 1000.0, y0 * H / 1000.0
        px1, py1 = x1 * W / 1000.0, y1 * H / 1000.0
        if px1 < px0:
            px0, py0, px1, py1 = px1, py1, px0, py0
        if abs(px1 - px0) < 1e-6:
            out["tilt"].append(None)
            continue
        out["tilt"].append(round(math.degrees(math.atan2(py1 - py0, px1 - px0)), 2))
        out["n_lines"] += 1
    return out


def count_liquid_bodies(image, bod, sd, lines, k):
    """1 if at least the required number of liquid bodies were found."""
    measured = tilts(image, bod, sd, lines)
    ok = 1.0 if int(measured["n_found"]) >= int(k) else 0.0
    return {"frac": ok, "verdict": "liquid bodies confirmed %d vs required %d -> frac %s"
            % (measured["n_found"], int(k), ok)}

# end of f_code

# code: f_code_2

import math
import struct


def image_width_height(image):
    try:
        if hasattr(image, "size") and not isinstance(image, (str, bytes)):
            w, h = image.size
            return float(w), float(h)
    except Exception:
        pass
    try:
        with open(str(image), "rb") as fh:
            head = fh.read(64)
            if head[:8] == b"\x89PNG\r\n\x1a\n":
                w, h = struct.unpack(">II", head[16:24])
                return float(w), float(h)
            fh.seek(0)
            data = fh.read()
        i = 2
        while i < len(data) - 9:
            if data[i] != 0xFF:
                i += 1
                continue
            mark = data[i + 1]
            if 0xC0 <= mark <= 0xCF and mark not in (0xC4, 0xC8, 0xCC):
                h, w = struct.unpack(">HH", data[i + 5:i + 9])
                return float(w), float(h)
            i += 2 + struct.unpack(">H", data[i + 2:i + 4])[0]
    except Exception:
        pass
    return None, None


def _distinct(bs, thr=0.85):
    kept = []
    for b in bs:
        dup = False
        for k in kept:
            ix = max(0.0, min(b["x1"], k["x1"]) - max(b["x0"], k["x0"]))
            iy = max(0.0, min(b["y1"], k["y1"]) - max(b["y0"], k["y0"]))
            inter = ix * iy
            ua = (b["x1"] - b["x0"]) * (b["y1"] - b["y0"])
            ub = (k["x1"] - k["x0"]) * (k["y1"] - k["y0"])
            if inter > 0 and inter / max(1e-9, ua + ub - inter) >= thr:
                dup = True
                break
        if not dup:
            kept.append(b)
    return kept


def bodies(node):
    bs = []
    for b in ((node or {}).get("geometry") or []):
        try:
            y0, x0, y1, x1 = [float(v) for v in b[:4]]
        except Exception:
            continue
        if y1 - y0 <= 0 or x1 - x0 <= 0:
            continue
        bs.append({"cx": (x0 + x1) / 2.0, "cy": (y0 + y1) / 2.0, "x0": x0, "x1": x1,
                   "y0": y0, "y1": y1})
    bs = _distinct(bs)
    if not bs:
        return []
    xs = [b["cx"] for b in bs]
    ys = [b["cy"] for b in bs]
    across = (max(xs) - min(xs)) >= (max(ys) - min(ys))
    bs.sort(key=(lambda b: b["cx"]) if across else (lambda b: b["cy"]))
    return bs


def _side(ans):
    s = str(ans or "").lower()
    if "level" in s or "flat" in s or "neither" in s or "same" in s:
        return 0
    if "left" in s:
        return 1
    if "right" in s:
        return -1
    return None


def tilts(image, bod, sd, lines):
    bs = bodies(bod)
    ans = list((sd or {}).get("answers") or [])
    W, H = image_width_height(image)
    out = {"n_found": len(bs), "tilt": [], "sign": [], "n_lines": 0}
    for i, b in enumerate(bs):
        out["sign"].append(_side(ans[i]) if i < len(ans) else None)
    for i in range(len(bs)):
        g = (lines[i] or {}).get("geometry") if i < len(lines) else None
        if not g or len(g) < 4 or not W:
            out["tilt"].append(None)
            continue
        y0, x0, y1, x1 = [float(v) for v in g[:4]]
        px0, py0 = x0 * W / 1000.0, y0 * H / 1000.0
        px1, py1 = x1 * W / 1000.0, y1 * H / 1000.0
        if px1 < px0:
            px0, py0, px1, py1 = px1, py1, px0, py0
        if abs(px1 - px0) < 1e-6:
            out["tilt"].append(None)
            continue
        out["tilt"].append(round(math.degrees(math.atan2(py1 - py0, px1 - px0)), 2))
        out["n_lines"] += 1
    return out


def score_surface_tilts(image, bod, sd, lines, target_tilts, core_rel, core_min, marg_rel, marg_min):
    """Average closeness of each traced surface tilt to its reference angle."""
    measured = tilts(image, bod, sd, lines)
    tilts_read = measured["tilt"]
    n = 0
    s = 0.0
    per_vessel = []
    for i in range(len(target_tilts)):
        t = float(target_tilts[i])
        if abs(t) < 1e-6:
            continue
        n += 1
        try:
            v = float(tilts_read[i])
        except Exception:
            per_vessel.append(0.0)
            continue
        c = max(float(core_min), float(core_rel) * abs(t))
        g = max(float(marg_min), float(marg_rel) * abs(t))
        q = max(0.0, min(1.0, 1.0 - max(0.0, abs(v - t) - c) / max(g, 1e-9)))
        per_vessel.append(round(q, 4))
        s += q
    frac = round(s / n, 4) if n else 0.0
    return {"frac": frac, "tilt_deg": tilts_read, "targets": list(target_tilts), "per_vessel": per_vessel,
            "verdict": "surface tilts (deg, + = left end higher) %s vs %s -> frac %s"
            % (tilts_read, list(target_tilts), frac)}

# end of f_code_2

# code: f_code_3

import math
import struct


def image_width_height(image):
    try:
        if hasattr(image, "size") and not isinstance(image, (str, bytes)):
            w, h = image.size
            return float(w), float(h)
    except Exception:
        pass
    try:
        with open(str(image), "rb") as fh:
            head = fh.read(64)
            if head[:8] == b"\x89PNG\r\n\x1a\n":
                w, h = struct.unpack(">II", head[16:24])
                return float(w), float(h)
            fh.seek(0)
            data = fh.read()
        i = 2
        while i < len(data) - 9:
            if data[i] != 0xFF:
                i += 1
                continue
            mark = data[i + 1]
            if 0xC0 <= mark <= 0xCF and mark not in (0xC4, 0xC8, 0xCC):
                h, w = struct.unpack(">HH", data[i + 5:i + 9])
                return float(w), float(h)
            i += 2 + struct.unpack(">H", data[i + 2:i + 4])[0]
    except Exception:
        pass
    return None, None


def _distinct(bs, thr=0.85):
    kept = []
    for b in bs:
        dup = False
        for k in kept:
            ix = max(0.0, min(b["x1"], k["x1"]) - max(b["x0"], k["x0"]))
            iy = max(0.0, min(b["y1"], k["y1"]) - max(b["y0"], k["y0"]))
            inter = ix * iy
            ua = (b["x1"] - b["x0"]) * (b["y1"] - b["y0"])
            ub = (k["x1"] - k["x0"]) * (k["y1"] - k["y0"])
            if inter > 0 and inter / max(1e-9, ua + ub - inter) >= thr:
                dup = True
                break
        if not dup:
            kept.append(b)
    return kept


def bodies(node):
    bs = []
    for b in ((node or {}).get("geometry") or []):
        try:
            y0, x0, y1, x1 = [float(v) for v in b[:4]]
        except Exception:
            continue
        if y1 - y0 <= 0 or x1 - x0 <= 0:
            continue
        bs.append({"cx": (x0 + x1) / 2.0, "cy": (y0 + y1) / 2.0, "x0": x0, "x1": x1,
                   "y0": y0, "y1": y1})
    bs = _distinct(bs)
    if not bs:
        return []
    xs = [b["cx"] for b in bs]
    ys = [b["cy"] for b in bs]
    across = (max(xs) - min(xs)) >= (max(ys) - min(ys))
    bs.sort(key=(lambda b: b["cx"]) if across else (lambda b: b["cy"]))
    return bs


def _side(ans):
    s = str(ans or "").lower()
    if "level" in s or "flat" in s or "neither" in s or "same" in s:
        return 0
    if "left" in s:
        return 1
    if "right" in s:
        return -1
    return None


def tilts(image, bod, sd, lines):
    bs = bodies(bod)
    ans = list((sd or {}).get("answers") or [])
    W, H = image_width_height(image)
    out = {"n_found": len(bs), "tilt": [], "sign": [], "n_lines": 0}
    for i, b in enumerate(bs):
        out["sign"].append(_side(ans[i]) if i < len(ans) else None)
    for i in range(len(bs)):
        g = (lines[i] or {}).get("geometry") if i < len(lines) else None
        if not g or len(g) < 4 or not W:
            out["tilt"].append(None)
            continue
        y0, x0, y1, x1 = [float(v) for v in g[:4]]
        px0, py0 = x0 * W / 1000.0, y0 * H / 1000.0
        px1, py1 = x1 * W / 1000.0, y1 * H / 1000.0
        if px1 < px0:
            px0, py0, px1, py1 = px1, py1, px0, py0
        if abs(px1 - px0) < 1e-6:
            out["tilt"].append(None)
            continue
        out["tilt"].append(round(math.degrees(math.atan2(py1 - py0, px1 - px0)), 2))
        out["n_lines"] += 1
    return out


def score_slope_ratio(image, bod, sd, lines, target_tilts, idx, target, core_rel=0.25, marg_rel=0.15):
    """Closeness of the steepest to shallowest slope ratio to the reference ratio."""
    measured = tilts(image, bod, sd, lines)
    tilts_read = measured["tilt"]
    v = []
    for i in idx:
        try:
            v.append(abs(float(tilts_read[int(i)])))
        except Exception:
            return {"frac": 0.0, "verdict": "a surface needed for the spread could not be "
                    "measured -> frac 0.0", "tilt_deg": tilts_read}
    if len(v) < 2 or min(v) <= 1e-6:
        return {"frac": 0.0, "verdict": "fewer than two measurable slopes -> frac 0.0",
                "tilt_deg": tilts_read}
    ratio = max(v) / min(v)
    t = float(target)
    c = float(core_rel) * t
    g = max(float(marg_rel) * t, 1e-9)
    frac = round(max(0.0, min(1.0, 1.0 - max(0.0, abs(ratio - t) - c) / g)), 4)
    return {"frac": frac, "tilt_deg": tilts_read,
            "verdict": "steepest/shallowest slope %.4f vs %s -> frac %s" % (ratio, t, frac)}

# end of f_code_3

# code: f_code_4

import math
import struct


def image_width_height(image):
    try:
        if hasattr(image, "size") and not isinstance(image, (str, bytes)):
            w, h = image.size
            return float(w), float(h)
    except Exception:
        pass
    try:
        with open(str(image), "rb") as fh:
            head = fh.read(64)
            if head[:8] == b"\x89PNG\r\n\x1a\n":
                w, h = struct.unpack(">II", head[16:24])
                return float(w), float(h)
            fh.seek(0)
            data = fh.read()
        i = 2
        while i < len(data) - 9:
            if data[i] != 0xFF:
                i += 1
                continue
            mark = data[i + 1]
            if 0xC0 <= mark <= 0xCF and mark not in (0xC4, 0xC8, 0xCC):
                h, w = struct.unpack(">HH", data[i + 5:i + 9])
                return float(w), float(h)
            i += 2 + struct.unpack(">H", data[i + 2:i + 4])[0]
    except Exception:
        pass
    return None, None


def _distinct(bs, thr=0.85):
    kept = []
    for b in bs:
        dup = False
        for k in kept:
            ix = max(0.0, min(b["x1"], k["x1"]) - max(b["x0"], k["x0"]))
            iy = max(0.0, min(b["y1"], k["y1"]) - max(b["y0"], k["y0"]))
            inter = ix * iy
            ua = (b["x1"] - b["x0"]) * (b["y1"] - b["y0"])
            ub = (k["x1"] - k["x0"]) * (k["y1"] - k["y0"])
            if inter > 0 and inter / max(1e-9, ua + ub - inter) >= thr:
                dup = True
                break
        if not dup:
            kept.append(b)
    return kept


def bodies(node):
    bs = []
    for b in ((node or {}).get("geometry") or []):
        try:
            y0, x0, y1, x1 = [float(v) for v in b[:4]]
        except Exception:
            continue
        if y1 - y0 <= 0 or x1 - x0 <= 0:
            continue
        bs.append({"cx": (x0 + x1) / 2.0, "cy": (y0 + y1) / 2.0, "x0": x0, "x1": x1,
                   "y0": y0, "y1": y1})
    bs = _distinct(bs)
    if not bs:
        return []
    xs = [b["cx"] for b in bs]
    ys = [b["cy"] for b in bs]
    across = (max(xs) - min(xs)) >= (max(ys) - min(ys))
    bs.sort(key=(lambda b: b["cx"]) if across else (lambda b: b["cy"]))
    return bs


def _side(ans):
    s = str(ans or "").lower()
    if "level" in s or "flat" in s or "neither" in s or "same" in s:
        return 0
    if "left" in s:
        return 1
    if "right" in s:
        return -1
    return None


def tilts(image, bod, sd, lines):
    bs = bodies(bod)
    ans = list((sd or {}).get("answers") or [])
    W, H = image_width_height(image)
    out = {"n_found": len(bs), "tilt": [], "sign": [], "n_lines": 0}
    for i, b in enumerate(bs):
        out["sign"].append(_side(ans[i]) if i < len(ans) else None)
    for i in range(len(bs)):
        g = (lines[i] or {}).get("geometry") if i < len(lines) else None
        if not g or len(g) < 4 or not W:
            out["tilt"].append(None)
            continue
        y0, x0, y1, x1 = [float(v) for v in g[:4]]
        px0, py0 = x0 * W / 1000.0, y0 * H / 1000.0
        px1, py1 = x1 * W / 1000.0, y1 * H / 1000.0
        if px1 < px0:
            px0, py0, px1, py1 = px1, py1, px0, py0
        if abs(px1 - px0) < 1e-6:
            out["tilt"].append(None)
            continue
        out["tilt"].append(round(math.degrees(math.atan2(py1 - py0, px1 - px0)), 2))
        out["n_lines"] += 1
    return out


def score_higher_ends(image, bod, sd, lines, target_tilts, dead):
    """Share of vessels whose higher surface end matches the reference side."""
    measured = tilts(image, bod, sd, lines)
    sides = measured["sign"]
    n = 0
    ok = 0
    for i in range(len(target_tilts)):
        n += 1
        t = float(target_tilts[i])
        want_side = 0 if abs(t) <= float(dead) else (1 if t > 0 else -1)
        read_side = sides[i] if i < len(sides) else None
        if read_side is not None and int(read_side) == want_side:
            ok += 1
    frac = round(ok / float(n), 4) if n else 0.0
    return {"frac": frac, "sides": sides,
            "verdict": "higher end per vessel (1=left, -1=right, 0=level) %s vs the key's signs "
            "-> frac %s" % (sides, frac)}

# end of f_code_4

# code: f_code_5

import math
import struct


def image_width_height(image):
    try:
        if hasattr(image, "size") and not isinstance(image, (str, bytes)):
            w, h = image.size
            return float(w), float(h)
    except Exception:
        pass
    try:
        with open(str(image), "rb") as fh:
            head = fh.read(64)
            if head[:8] == b"\x89PNG\r\n\x1a\n":
                w, h = struct.unpack(">II", head[16:24])
                return float(w), float(h)
            fh.seek(0)
            data = fh.read()
        i = 2
        while i < len(data) - 9:
            if data[i] != 0xFF:
                i += 1
                continue
            mark = data[i + 1]
            if 0xC0 <= mark <= 0xCF and mark not in (0xC4, 0xC8, 0xCC):
                h, w = struct.unpack(">HH", data[i + 5:i + 9])
                return float(w), float(h)
            i += 2 + struct.unpack(">H", data[i + 2:i + 4])[0]
    except Exception:
        pass
    return None, None


def _distinct(bs, thr=0.85):
    kept = []
    for b in bs:
        dup = False
        for k in kept:
            ix = max(0.0, min(b["x1"], k["x1"]) - max(b["x0"], k["x0"]))
            iy = max(0.0, min(b["y1"], k["y1"]) - max(b["y0"], k["y0"]))
            inter = ix * iy
            ua = (b["x1"] - b["x0"]) * (b["y1"] - b["y0"])
            ub = (k["x1"] - k["x0"]) * (k["y1"] - k["y0"])
            if inter > 0 and inter / max(1e-9, ua + ub - inter) >= thr:
                dup = True
                break
        if not dup:
            kept.append(b)
    return kept


def bodies(node):
    bs = []
    for b in ((node or {}).get("geometry") or []):
        try:
            y0, x0, y1, x1 = [float(v) for v in b[:4]]
        except Exception:
            continue
        if y1 - y0 <= 0 or x1 - x0 <= 0:
            continue
        bs.append({"cx": (x0 + x1) / 2.0, "cy": (y0 + y1) / 2.0, "x0": x0, "x1": x1,
                   "y0": y0, "y1": y1})
    bs = _distinct(bs)
    if not bs:
        return []
    xs = [b["cx"] for b in bs]
    ys = [b["cy"] for b in bs]
    across = (max(xs) - min(xs)) >= (max(ys) - min(ys))
    bs.sort(key=(lambda b: b["cx"]) if across else (lambda b: b["cy"]))
    return bs


def _side(ans):
    s = str(ans or "").lower()
    if "level" in s or "flat" in s or "neither" in s or "same" in s:
        return 0
    if "left" in s:
        return 1
    if "right" in s:
        return -1
    return None


def tilts(image, bod, sd, lines):
    bs = bodies(bod)
    ans = list((sd or {}).get("answers") or [])
    W, H = image_width_height(image)
    out = {"n_found": len(bs), "tilt": [], "sign": [], "n_lines": 0}
    for i, b in enumerate(bs):
        out["sign"].append(_side(ans[i]) if i < len(ans) else None)
    for i in range(len(bs)):
        g = (lines[i] or {}).get("geometry") if i < len(lines) else None
        if not g or len(g) < 4 or not W:
            out["tilt"].append(None)
            continue
        y0, x0, y1, x1 = [float(v) for v in g[:4]]
        px0, py0 = x0 * W / 1000.0, y0 * H / 1000.0
        px1, py1 = x1 * W / 1000.0, y1 * H / 1000.0
        if px1 < px0:
            px0, py0, px1, py1 = px1, py1, px0, py0
        if abs(px1 - px0) < 1e-6:
            out["tilt"].append(None)
            continue
        out["tilt"].append(round(math.degrees(math.atan2(py1 - py0, px1 - px0)), 2))
        out["n_lines"] += 1
    return out


def score_one_level(image, bod, sd, lines, idx, tol):
    """1 if the chosen vessel reads level and all the others read tilted."""
    measured = tilts(image, bod, sd, lines)
    sides = measured["sign"]
    i = int(idx)
    chosen_side = sides[i] if i < len(sides) else None
    flat = 1.0 if chosen_side == 0 else 0.0
    rest = []
    for k in range(len(sides)):
        if k == i:
            continue
        rest.append(1.0 if (sides[k] is not None and sides[k] != 0) else 0.0)
    other = sum(rest) / len(rest) if rest else 1.0
    frac = round(flat * other, 4)
    return {"frac": frac, "sides": sides,
            "verdict": "vessel %d level=%s, the others tilted %s -> frac %s"
            % (i, chosen_side == 0, other, frac)}

# end of f_code_5

# code: f_code_6

import math
import struct


def image_width_height(image):
    try:
        if hasattr(image, "size") and not isinstance(image, (str, bytes)):
            w, h = image.size
            return float(w), float(h)
    except Exception:
        pass
    try:
        with open(str(image), "rb") as fh:
            head = fh.read(64)
            if head[:8] == b"\x89PNG\r\n\x1a\n":
                w, h = struct.unpack(">II", head[16:24])
                return float(w), float(h)
            fh.seek(0)
            data = fh.read()
        i = 2
        while i < len(data) - 9:
            if data[i] != 0xFF:
                i += 1
                continue
            mark = data[i + 1]
            if 0xC0 <= mark <= 0xCF and mark not in (0xC4, 0xC8, 0xCC):
                h, w = struct.unpack(">HH", data[i + 5:i + 9])
                return float(w), float(h)
            i += 2 + struct.unpack(">H", data[i + 2:i + 4])[0]
    except Exception:
        pass
    return None, None


def _distinct(bs, thr=0.85):
    kept = []
    for b in bs:
        dup = False
        for k in kept:
            ix = max(0.0, min(b["x1"], k["x1"]) - max(b["x0"], k["x0"]))
            iy = max(0.0, min(b["y1"], k["y1"]) - max(b["y0"], k["y0"]))
            inter = ix * iy
            ua = (b["x1"] - b["x0"]) * (b["y1"] - b["y0"])
            ub = (k["x1"] - k["x0"]) * (k["y1"] - k["y0"])
            if inter > 0 and inter / max(1e-9, ua + ub - inter) >= thr:
                dup = True
                break
        if not dup:
            kept.append(b)
    return kept


def bodies(node):
    bs = []
    for b in ((node or {}).get("geometry") or []):
        try:
            y0, x0, y1, x1 = [float(v) for v in b[:4]]
        except Exception:
            continue
        if y1 - y0 <= 0 or x1 - x0 <= 0:
            continue
        bs.append({"cx": (x0 + x1) / 2.0, "cy": (y0 + y1) / 2.0, "x0": x0, "x1": x1,
                   "y0": y0, "y1": y1})
    bs = _distinct(bs)
    if not bs:
        return []
    xs = [b["cx"] for b in bs]
    ys = [b["cy"] for b in bs]
    across = (max(xs) - min(xs)) >= (max(ys) - min(ys))
    bs.sort(key=(lambda b: b["cx"]) if across else (lambda b: b["cy"]))
    return bs


def _side(ans):
    s = str(ans or "").lower()
    if "level" in s or "flat" in s or "neither" in s or "same" in s:
        return 0
    if "left" in s:
        return 1
    if "right" in s:
        return -1
    return None


def tilts(image, bod, sd, lines):
    bs = bodies(bod)
    ans = list((sd or {}).get("answers") or [])
    W, H = image_width_height(image)
    out = {"n_found": len(bs), "tilt": [], "sign": [], "n_lines": 0}
    for i, b in enumerate(bs):
        out["sign"].append(_side(ans[i]) if i < len(ans) else None)
    for i in range(len(bs)):
        g = (lines[i] or {}).get("geometry") if i < len(lines) else None
        if not g or len(g) < 4 or not W:
            out["tilt"].append(None)
            continue
        y0, x0, y1, x1 = [float(v) for v in g[:4]]
        px0, py0 = x0 * W / 1000.0, y0 * H / 1000.0
        px1, py1 = x1 * W / 1000.0, y1 * H / 1000.0
        if px1 < px0:
            px0, py0, px1, py1 = px1, py1, px0, py0
        if abs(px1 - px0) < 1e-6:
            out["tilt"].append(None)
            continue
        out["tilt"].append(round(math.degrees(math.atan2(py1 - py0, px1 - px0)), 2))
        out["n_lines"] += 1
    return out


def score_surface_tilts(image, bod, sd, lines, target_tilts, core_rel, core_min, marg_rel, marg_min):
    """Average closeness of each traced surface tilt to its reference angle."""
    measured = tilts(image, bod, sd, lines)
    tilts_read = measured["tilt"]
    n = 0
    s = 0.0
    for i in range(len(target_tilts)):
        t = float(target_tilts[i])
        if abs(t) < 1e-6:
            continue
        n += 1
        try:
            v = float(tilts_read[i])
        except Exception:
            continue
        c = max(float(core_min), float(core_rel) * abs(t))
        g = max(float(marg_min), float(marg_rel) * abs(t))
        s += max(0.0, min(1.0, 1.0 - max(0.0, abs(v - t) - c) / max(g, 1e-9)))
    frac = round(s / n, 4) if n else 0.0
    return {"frac": frac, "tilt_deg": tilts_read, "sides": measured["sign"], "targets": list(target_tilts),
            "verdict": "surfaces traced %d of %d; tilts %s vs key %s; higher end %s"
            % (measured["n_lines"], measured["n_found"], tilts_read, list(target_tilts), measured["sign"])}

# end of f_code_6
