"""Execute an evaluation plan on one image and record every check, read and overlay."""
from __future__ import annotations

import hashlib
import os
import re
import tempfile

from . import ops as _ops
import logging

log = logging.getLogger(__name__)


def _state_dir():
    d = os.path.join(tempfile.gettempdir(), "genolympiad_agentic")
    os.makedirs(d, exist_ok=True)
    return d


def _state_path(tag, seed):
    h = hashlib.md5(str(seed).encode()).hexdigest()[:10]
    return os.path.join(_state_dir(), f"{tag}_{h}.png")


def _load_rgb(img):
    from PIL import Image
    if hasattr(img, "convert"):
        return img.convert("RGB")
    return Image.open(str(img)).convert("RGB")


def _font(sz):
    from PIL import ImageFont
    here = os.path.dirname(os.path.abspath(__file__))
    for p in (os.path.join(here, "assets", "fonts", "DejaVuSansMono.ttf"),
              os.path.join(here, "assets", "fonts", "DejaVuSans.ttf")):
        if os.path.exists(p):
            return ImageFont.truetype(p, sz)
    for name in ("consola.ttf", "arial.ttf"):
        try:
            return ImageFont.truetype(name, sz)
        except Exception:
            log.debug("error ignored in _font", exc_info=True)
            pass
    return ImageFont.load_default()


def render_coin_boxes(state_path, out, node):
    from PIL import ImageDraw
    import cv2
    import numpy as np
    im = _load_rgb(state_path)
    d = ImageDraw.Draw(im)
    f = _font(max(14, im.width // 60))
    coins = out.get("coins") or []
    COLORS = {"quarter": (60, 200, 255), "nickel": (120, 255, 120),
              "dime": (255, 210, 60), "penny": (255, 120, 60), "?": (200, 200, 200)}
    for i, c in enumerate(coins):
        x, y, r = c["x"], c["y"], c["r"]
        cls = c.get("cls", "?")
        col = COLORS.get(cls, COLORS["?"])
        d.rectangle([x - r, y - r, x + r, y + r], outline=col, width=max(2, im.width // 400))
        d.text((x - r, y - r - f.size - 2), f"{i+1}:{cls[:2]}", fill=col, font=f)
    op = _state_path("coinboxes", (state_path, node.get("id"), len(coins)))
    im.save(op)
    action = f"box step overlaid {len(coins)} coin bboxes (Hough+hue/size classify)"
    return op, action


def render_detect_boxes(state_path, out, node):
    from PIL import ImageDraw
    im = _load_rgb(state_path)
    d = ImageDraw.Draw(im)
    f = _font(max(15, im.width // 55))
    boxes = out.get("boxes") or []
    scores = out.get("scores") or []
    fills = out.get("fills") or []
    lw = max(2, im.width // 380)
    for i, b in enumerate(boxes):
        x0, y0, x1, y1 = [int(v) for v in b]
        s = scores[i] if i < len(scores) else None
        fl = fills[i] if i < len(fills) else None
        d.rectangle([x0, y0, x1, y1], outline=(50, 230, 90), width=lw)
        tag = f"{i+1}"
        if s is not None:
            tag += f":{s:.2f}"
        if fl is not None:
            tag += f"/f{fl:.2f}"
        d.text((x0, max(0, y0 - f.size - 2)), tag, fill=(50, 230, 90), font=f)
    op = _state_path("detbox", (state_path, node.get("id"), len(boxes), out.get("try")))
    im.save(op)
    action = (f"box step boxed {len(boxes)} objects"
              + (f" [try {out.get('try')}]" if out.get("try") is not None else ""))
    return op, action


_CONTRAST_CANDIDATES = ((0, 0, 0), (255, 255, 255),
                        (230, 25, 25), (25, 200, 60), (30, 90, 245), (245, 210, 20),
                        (235, 30, 220), (20, 215, 225), (250, 130, 0), (140, 40, 235))
_CONTRAST_SAMPLES = 400
_CONTRAST_SAMPLE_CAP = 500


def _srgb_to_lab(c):
    out = []
    for v in c[:3]:
        v = v / 255.0
        out.append(v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4)
    r, g, b = out
    x = (0.4124 * r + 0.3576 * g + 0.1805 * b) / 0.95047
    y = (0.2126 * r + 0.7152 * g + 0.0722 * b)
    z = (0.0193 * r + 0.1192 * g + 0.9505 * b) / 1.08883

    def f(t):
        return t ** (1.0 / 3.0) if t > 0.008856 else (7.787 * t + 16.0 / 116.0)
    fx, fy, fz = f(x), f(y), f(z)
    return (116.0 * fy - 16.0, 500.0 * (fx - fy), 200.0 * (fy - fz))


_CAND_LAB = tuple(_srgb_to_lab(c) for c in _CONTRAST_CANDIDATES)


def _stroke_ring_points(path, pad):
    pts = []
    if (isinstance(path, (list, tuple)) and len(path) == 4
            and all(isinstance(v, (int, float)) for v in path)):
        x0, y0, x1, y1 = [float(v) for v in path]
        x0, x1 = min(x0, x1), max(x0, x1)
        y0, y1 = min(y0, y1), max(y0, y1)
        per = 2 * ((x1 - x0) + (y1 - y0))
        step = max(1.0, per / max(1, _CONTRAST_SAMPLES // (2 * pad + 1)))
        t = 0.0
        while t < (x1 - x0):
            pts.append((x0 + t, y0, 0, -1))
            pts.append((x0 + t, y1, 0, 1))
            t += step
        t = 0.0
        while t < (y1 - y0):
            pts.append((x0, y0 + t, -1, 0))
            pts.append((x1, y0 + t, 1, 0))
            t += step
        ring = []
        for (px, py, nx, ny) in pts:
            for k in range(-pad, pad + 1):
                ring.append((px + nx * k, py + ny * k))
        return ring
    for p in (path or []):
        try:
            px, py = float(p[0]), float(p[1])
        except (TypeError, ValueError, IndexError):
            log.debug("error ignored in _stroke_ring_points", exc_info=True)
            continue
        for dx in range(-pad, pad + 1):
            for dy in range(-pad, pad + 1):
                pts.append((px + dx, py + dy))
    return pts


def adaptive_contrast_color(im, path, pad=None, samples=None):
    try:
        W, H = im.size
        if pad is None:
            pad = max(2, min(W, H) // 240)
        ring = _stroke_ring_points(path, int(pad))
        if not ring:
            return (255, 0, 255), (12, 12, 12)
        if len(ring) > _CONTRAST_SAMPLE_CAP:
            k = len(ring) / float(_CONTRAST_SAMPLE_CAP)
            ring = [ring[int(i * k)] for i in range(_CONTRAST_SAMPLE_CAP)]
        px = im.load()
        labs = []
        for (x, y) in ring:
            xi = int(x)
            yi = int(y)
            if 0 <= xi < W and 0 <= yi < H:
                labs.append(_srgb_to_lab(px[xi, yi]))
        if not labs:
            return (255, 0, 255), (12, 12, 12)
        best, best_score = _CONTRAST_CANDIDATES[0], -1.0
        idx = max(0, int(0.05 * (len(labs) - 1)))
        for cand, cl in zip(_CONTRAST_CANDIDATES, _CAND_LAB):
            ds = sorted((cl[0] - l[0]) ** 2 + (cl[1] - l[1]) ** 2 + (cl[2] - l[2]) ** 2
                        for l in labs)
            s = ds[idx]
            if s > best_score:
                best, best_score = cand, s
        return best, _casing(best)
    except Exception:
        log.debug("error ignored in adaptive_contrast_color", exc_info=True)
        return (255, 0, 255), (12, 12, 12)


def box_ink_verdict(image, box_px, min_ink_frac=0.005, ink_thresh=200):
    rep = {"ink_frac": None, "near_blank": False, "note": None}
    try:
        import numpy as np
        from PIL import Image
        im = image if hasattr(image, "convert") else Image.open(image)
        arr = np.asarray(im.convert("L"))
        H, W = arr.shape
        x0, y0, x1, y1 = [float(v) for v in box_px[:4]]
        x0, x1 = sorted((max(0.0, x0), min(float(W), x1)))
        y0, y1 = sorted((max(0.0, y0), min(float(H), y1)))
        ix0, iy0, ix1, iy1 = int(x0), int(y0), max(int(x0) + 1, int(x1)), max(int(y0) + 1, int(y1))
        win = arr[iy0:iy1, ix0:ix1]
        if win.size == 0:
            rep["note"] = "degenerate box"
            return rep
        rep["ink_frac"] = round(float((win < ink_thresh).mean()), 5)
        rep["near_blank"] = rep["ink_frac"] < float(min_ink_frac)
        return rep
    except Exception as e:
        log.debug("error ignored in box_ink_verdict", exc_info=True)
        rep["note"] = "ink verdict not run (%s)" % type(e).__name__
        return rep


def render_read_loc(state_path, out, node):
    from PIL import ImageDraw
    im = _load_rgb(state_path)
    d = ImageDraw.Draw(im)
    f = _font(max(15, im.width // 55))
    boxes = out.get("boxes") or []
    labels = out.get("labels") or []
    lw = max(2, im.width // 300)
    hw = max(1, lw // 2)
    for i, b in enumerate(boxes):
        x0, y0, x1, y1 = [int(v) for v in b[:4]]
        x0, x1 = min(x0, x1), max(x0, x1)
        y0, y1 = min(y0, y1), max(y0, y1)
        x1, y1 = max(x1, x0 + 1), max(y1, y0 + 1)
        col, cas = adaptive_contrast_color(im, (x0, y0, x1, y1))
        d.rectangle([x0 - hw, y0 - hw, x1 + hw, y1 + hw], outline=cas, width=hw)
        d.rectangle([x0, y0, x1, y1], outline=col, width=lw)
        d.rectangle([x0 + lw, y0 + lw, x1 - lw, y1 - lw], outline=cas, width=hw)
        tag = str(labels[i]) if i < len(labels) and labels[i] not in (None, "") else "read %d" % (i + 1)
        tag = tag[:60]
        ty = y0 - f.size - 2
        if ty < 0:
            ty = min(y1 + 2, max(0, im.height - f.size - 2))
        tw = d.textlength(tag, font=f)
        tcol, tcas = adaptive_contrast_color(im, (x0, ty, x0 + tw, ty + f.size))
        for ox, oy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            d.text((x0 + ox, ty + oy), tag, fill=tcas, font=f)
        d.text((x0, ty), tag, fill=tcol, font=f)
    op = _state_path("readloc", (state_path, node.get("id"), len(boxes), tuple(map(str, labels))))
    im.save(op)
    return op, "read-position highlight: %d region(s) the reader says it read from (evidence only)" % len(boxes)


def _luma(c):
    return 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]


def _casing(col):
    return (12, 12, 12) if _luma(col) > 140 else (245, 245, 245)


def _font_cjk(sz):
    from PIL import ImageFont
    for name in ("msyh.ttc", "simhei.ttf", "msjh.ttc", "simsun.ttc",
                 "NotoSansCJKsc-Regular.otf", "NotoSansSC-Regular.otf",
                 "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"):
        try:
            return ImageFont.truetype(name, sz)
        except Exception:
            log.debug("error ignored in _font_cjk", exc_info=True)
            continue
    return None


def _has_cjk(s):
    return any(ord(ch) > 0x2E80 for ch in str(s))


def _wrap_lines(d, lines, fonts, maxw):
    fa, fc = fonts
    out = []
    for ln in lines:
        ln = str(ln)
        f = fc if _has_cjk(ln) else fa
        if f is None:
            continue
        units = list(ln) if _has_cjk(ln) else ln.split(" ")
        join = "" if _has_cjk(ln) else " "
        cur = ""
        for w in units:
            t = (cur + join + w) if cur else w
            if d.textlength(t, font=f) <= maxw or not cur:
                cur = t
            else:
                out.append((cur, f))
                cur = w
        out.append((cur, f))
    return out


import threading as _threading
_LEGEND_TLS = _threading.local()


def _legend_sink():
    if not hasattr(_LEGEND_TLS, "lines"):
        _LEGEND_TLS.lines = []
    return _LEGEND_TLS.lines


def _sink_legend(lines):
    sink = _legend_sink()
    for ln in lines or []:
        s = str(ln).strip()
        if s and s not in sink:
            sink.append(s)


def drain_legends():
    sink = _legend_sink()
    out = list(sink)
    del sink[:]
    return out


def _one_line(d, lines, font, maxw):
    txt = "  ·  ".join(" ".join(str(x).split()) for x in (lines or []) if str(x).strip())
    if not txt:
        return []
    if font is None or d.textlength(txt, font=font) <= maxw:
        return [txt]
    lo, hi = 0, len(txt)
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if d.textlength(txt[:mid] + "…", font=font) <= maxw:
            lo = mid
        else:
            hi = mid - 1
    return [txt[:lo].rstrip() + "…"]


def _bars(im, top_lines, bottom_lines, fs):
    from PIL import Image, ImageDraw
    fs = max(13, min(fs, im.width // 80))
    fonts = (_font(fs), _font_cjk(fs))
    probe = ImageDraw.Draw(im)
    pad, gap = max(6, fs // 2), max(3, fs // 4)
    _sink_legend(bottom_lines)
    maxw = im.width - 2 * pad
    top1 = _one_line(probe, top_lines, fonts[0], maxw)
    tl = _wrap_lines(probe, top1, fonts, maxw)
    bl = []
    th = (len(tl) * (fs + gap) + 2 * pad) if tl else 0
    bh = (len(bl) * (fs + gap) + 2 * pad) if bl else 0
    sheet = Image.new("RGB", (im.width, im.height + th + bh), (18, 20, 26))
    sheet.paste(im, (0, th))
    d = ImageDraw.Draw(sheet)
    y = pad
    for ln, f in tl:
        d.text((pad, y), ln, fill=(240, 243, 250), font=f)
        y += fs + gap
    y = th + im.height + pad
    for ln, f in bl:
        d.text((pad, y), ln, fill=(178, 186, 202), font=f)
        y += fs + gap
    return sheet


def render_grounded_boxes(state_path, out, node):
    from PIL import ImageDraw
    im = _load_rgb(state_path)
    d = ImageDraw.Draw(im)
    W, H = im.size
    boxes = out.get("boxes") or []
    values = out.get("values") or []
    fs = max(15, W // 46)
    f = _font(fs)
    lw = max(3, W // 260)
    hw = max(2, lw // 2)
    for i, b in enumerate(boxes):
        x0, y0, x1, y1 = [int(v) for v in b[:4]]
        x0, x1 = min(x0, x1), max(x0, x1)
        y0, y1 = min(y0, y1), max(y0, y1)
        x1, y1 = max(x1, x0 + 1), max(y1, y0 + 1)
        col, cas = adaptive_contrast_color(im, (x0, y0, x1, y1))
        d.rectangle([x0 - hw, y0 - hw, x1 + hw, y1 + hw], outline=cas, width=hw)
        d.rectangle([x0, y0, x1, y1], outline=col, width=lw)
        d.rectangle([x0 + lw, y0 + lw, x1 - lw, y1 - lw], outline=cas, width=hw)
        v = values[i] if i < len(values) else None
        v = "?" if v in (None, "") else " ".join(str(v).split())
        tag = "%d=%s" % (i + 1, v if len(v) <= 24 else v[:23] + "...")
        tw = d.textlength(tag, font=f)
        cx, cy = x0, y0 - fs - 8
        if cy < 0:
            cy = y0 + 2
        if cx + tw + 10 > W:
            cx = max(0, W - tw - 10)
        d.rectangle([cx, cy, cx + tw + 8, cy + fs + 7], fill=col)
        d.text((cx + 4, cy + 3), tag, fill=cas, font=f)
    im = _bars(im, out.get("caption") or [], out.get("legend") or [], fs)
    op = _state_path("fbboxes", (state_path, node.get("id"), len(boxes),
                                 tuple(map(str, values)), tuple(out.get("caption") or [])))
    im.save(op)
    return op, ("confirmed-box overlay: %d box(es), each numbered with the value its own crop read "
                "(display only)" % len(boxes))


def render_detect_boxes_audit(state_path, out, node):
    from PIL import ImageDraw
    im = _load_rgb(state_path)
    d = ImageDraw.Draw(im)
    f = _font(max(15, im.width // 55))
    boxes = out.get("boxes") or []
    exp = out.get("gt_expected")
    n = len(boxes)
    okm = (abs(n - float(exp)) < 0.5) if exp is not None else None
    col = (50, 230, 90) if (okm is None or okm) else (235, 70, 70)
    lw = max(2, im.width // 380)
    for i, b in enumerate(boxes):
        x0, y0, x1, y1 = [int(v) for v in b]
        d.rectangle([x0, y0, x1, y1], outline=col, width=lw)
        d.text((x0, max(0, y0 - f.size - 2)), str(i + 1), fill=col, font=f)
    if exp is not None:
        gt_txt = str(int(exp)) if float(exp).is_integer() else f"{exp:g}"
        sym = "=" if okm else "!="
        verdict = "OK" if okm else "MISMATCH"
        banner = f"detected {n} {sym} reference {gt_txt}  {verdict}"
        d.rectangle([0, 0, im.width - 1, im.height - 1], outline=col, width=max(3, im.width // 200))
        bw = d.textlength(banner, font=f) + 18
        d.rectangle([8, 8, 8 + bw, 16 + f.size + 8], fill=(20, 22, 28))
        d.text((17, 14), banner, fill=col, font=f)
    op = _state_path("detboxa", (state_path, node.get("id"), len(boxes), exp))
    im.save(op)
    return op, "audit overlay (reference verdict, human-only)"


def render_count_boxes(state_path, out, node):
    from PIL import ImageDraw
    im = _load_rgb(state_path)
    W, H = im.size
    d = ImageDraw.Draw(im)
    f = _font(max(15, im.width // 55))
    boxes = out.get("boxes") or []
    answers = out.get("answers") or []
    expect = out.get("expect")
    k = str(expect).strip().lower() if expect is not None else None
    GREEN, RED, GREY = (50, 230, 90), (235, 70, 70), (170, 176, 188)
    lw = max(2, im.width // 360)
    n_pass = 0
    for i, b in enumerate(boxes):
        x0, y0, x1, y1 = (int(b[0] * W), int(b[1] * H), int(b[2] * W), int(b[3] * H)) \
            if max(b) <= 1.5 else [int(v) for v in b]
        ans = answers[i] if i < len(answers) else None
        a = "" if ans is None else str(ans).strip().lower()
        ok = bool(k) and (k in a)
        n_pass += int(ok)
        col = GREEN if ok else (RED if ans is not None else GREY)
        d.rectangle([x0, y0, x1, y1], outline=col, width=lw)
        tag = f"{i+1}" + (f":{str(ans)[:14]}" if ans is not None else ":?")
        ty = max(0, y0 - f.size - 3)
        tw = d.textlength(tag, font=f)
        d.rectangle([x0, ty, x0 + tw + 8, ty + f.size + 4], fill=(20, 22, 28))
        d.text((x0 + 4, ty + 1), tag, fill=col, font=f)
    src = out.get("source") or "?"
    n_found = out.get("n_found", len(boxes))
    all_ok = (n_pass == n_found and n_found > 0)
    bcol = GREEN if all_ok else RED
    exp_txt = "" if expect is None else f"  expect='{expect}'"
    banner = f"count {n_pass}/{n_found} pass (source={src}){exp_txt}"
    d.rectangle([0, 0, im.width - 1, im.height - 1], outline=bcol, width=max(3, im.width // 220))
    bw = d.textlength(banner, font=f) + 18
    d.rectangle([8, 8, 8 + bw, 16 + f.size + 8], fill=(20, 22, 28))
    d.text((17, 14), banner, fill=bcol, font=f)
    op = _state_path("countbox", (state_path, node.get("id"), len(boxes), n_pass, src))
    im.save(op)
    action = (f"count overlay: {n_pass}/{n_found} instances match expect "
              f"(source={src}; green=match, red=mismatch)")
    return op, action


def render_skeleton(state_path, out, node):
    from PIL import ImageDraw
    im = _load_rgb(state_path)
    d = ImageDraw.Draw(im)
    persons = out.get("persons") or []
    EDGES = [("L_shoulder", "R_shoulder"), ("L_shoulder", "L_elbow"), ("L_elbow", "L_wrist"),
             ("R_shoulder", "R_elbow"), ("R_elbow", "R_wrist"), ("L_shoulder", "L_hip"),
             ("R_shoulder", "R_hip"), ("L_hip", "R_hip"), ("L_hip", "L_knee"), ("L_knee", "L_ankle"),
             ("R_hip", "R_knee"), ("R_knee", "R_ankle"), ("nose", "L_eye"), ("nose", "R_eye")]
    lw = max(2, im.width // 300)
    for p in persons[:1]:
        pts = p["points"]
        x0, y0, x1, y1 = p["bbox"]
        d.rectangle([x0, y0, x1, y1], outline=(255, 220, 40), width=lw)
        for a, b in EDGES:
            if a in pts and b in pts:
                d.line([tuple(pts[a]), tuple(pts[b])], fill=(60, 230, 255), width=lw)
        for name, (px, py) in pts.items():
            r = lw + 1
            d.ellipse([px - r, py - r, px + r, py + r], fill=(255, 80, 80))
        for key, col in (("crown", (0, 255, 0)), ("chin", (255, 0, 255)), ("ankle", (255, 255, 0))):
            xy = out.get(key)
            if xy:
                r = lw + 2
                d.ellipse([xy[0] - r, xy[1] - r, xy[0] + r, xy[1] + r], outline=col, width=lw)
    op = _state_path("skeleton", (state_path, node.get("id"), len(persons)))
    im.save(op)
    action = f"mediapipe overlaid skeleton+bbox ({len(persons)} person)"
    return op, action


def render_contour(state_path, out, node):
    from PIL import ImageDraw
    im = _load_rgb(state_path)
    d = ImageDraw.Draw(im)
    lw = max(2, im.width // 350)
    for seg in (out.get("extracted_edges") or []):
        xl, xr, y = seg
        d.line([(xl, y), (xl, y)], fill=(255, 60, 60), width=lw + 1)
        d.line([(xr, y), (xr, y)], fill=(255, 60, 60), width=lw + 1)
    el = [(s[0], s[2]) for s in (out.get("extracted_edges") or [])]
    er = [(s[1], s[2]) for s in (out.get("extracted_edges") or [])]
    if len(el) > 1:
        d.line(el, fill=(255, 60, 60), width=lw)
        d.line(er, fill=(255, 60, 60), width=lw)
    tl = out.get("target_left") or []
    tr = out.get("target_right") or []
    if len(tl) > 1:
        d.line([tuple(p) for p in tl], fill=(50, 230, 90), width=lw)
        d.line([tuple(p) for p in tr], fill=(50, 230, 90), width=lw)
    op = _state_path("contour", (state_path, node.get("id")))
    im.save(op)
    action = "curve_render overlaid extracted silhouette (red) + target Bezier profile (green)"
    return op, action


def render_crop(state_path, out, node):
    im = _load_rgb(state_path)
    W, H = im.size
    reg = out.get("region")
    if not reg:
        return state_path, "crop: full frame"
    x0, y0, x1, y1 = reg
    if max(x0, y0, x1, y1) <= 1.5:
        x0, y0, x1, y1 = x0 * W, y0 * H, x1 * W, y1 * H
    crop = im.crop((int(x0), int(y0), int(x1), int(y1)))
    op = _state_path("crop", (state_path, node.get("id"), tuple(reg)))
    crop.save(op)
    return op, f"cropped region {[round(v,2) for v in reg]}"


def _norm_tok(s):
    t = str(s).strip().lower().replace(",", "").replace("$", "").replace("%", "")
    try:
        fv = float(t)
        return f"{fv:g}"
    except ValueError:
        log.debug("error ignored in _norm_tok", exc_info=True)
        return t


def render_ocr_words(state_path, out, node):
    from PIL import ImageDraw
    im = _load_rgb(state_path)
    d = ImageDraw.Draw(im)
    f = _font(max(13, im.width // 70))
    words = out.get("word_boxes") or []
    lw = max(2, im.width // 380)
    for w in words:
        x0, y0, x1, y1 = [int(v) for v in w[:4]]
        txt = str(w[4]) if len(w) > 4 else ""
        conf = w[5] if len(w) > 5 else None
        col = (80, 170, 255)
        d.rectangle([x0, y0, x1, y1], outline=col, width=lw)
        label = txt[:24] + (f" {conf:.2f}" if isinstance(conf, float) else "")
        tw = d.textlength(label, font=f)
        ly = max(0, y0 - f.size - 6)
        d.rectangle([x0, ly, x0 + tw + 8, ly + f.size + 5], fill=col)
        d.text((x0 + 4, ly + 2), label, fill=(12, 14, 18), font=f)
    op = _state_path("ocrwords", (state_path, node.get("id"), len(words)))
    im.save(op)
    return op, f"RapidOCR read {len(words)} words (position + text overlaid)"


def render_ocr_words_audit(state_path, out, node):
    from PIL import ImageDraw
    im = _load_rgb(state_path)
    d = ImageDraw.Draw(im)
    f = _font(max(13, im.width // 70))
    words = out.get("word_boxes") or []
    exp = {_norm_tok(t) for t in (out.get("expected_tokens") or []) if str(t).strip()}
    found = set()
    lw = max(2, im.width // 380)
    for w in words:
        x0, y0, x1, y1 = [int(v) for v in w[:4]]
        txt = str(w[4]) if len(w) > 4 else ""
        conf = w[5] if len(w) > 5 else None
        subs = {_norm_tok(x) for x in str(txt).replace(":", " ").split()}
        hit = bool(exp) and bool(subs & exp)
        if hit:
            found |= (subs & exp)
        col = (60, 230, 100) if hit else (80, 170, 255)
        d.rectangle([x0, y0, x1, y1], outline=col, width=lw)
        label = txt[:24] + (f" {conf:.2f}" if isinstance(conf, float) else "")
        tw = d.textlength(label, font=f)
        ly = max(0, y0 - f.size - 6)
        d.rectangle([x0, ly, x0 + tw + 8, ly + f.size + 5], fill=col)
        d.text((x0 + 4, ly + 2), label, fill=(12, 14, 18), font=f)
    action = f"audit overlay: {len(words)} OCR words"
    if exp:
        ok = len(found) == len(exp)
        col = (60, 230, 100) if ok else (235, 70, 70)
        banner = f"reference values found on image: {len(found)}/{len(exp)}"
        bw = d.textlength(banner, font=f) + 18
        d.rectangle([8, 8, 8 + bw, 16 + f.size + 8], fill=(20, 22, 28))
        d.text((17, 14), banner, fill=col, font=f)
        action += f" - reference found {len(found)}/{len(exp)}"
    op = _state_path("ocrwordsa", (state_path, node.get("id"), len(words), len(exp)))
    im.save(op)
    return op, action


_GENERIC_VALUE_SHAPES = [
    r"\d+\.\d{2,}",
    r"[-+]?\d+(?:[.,]\d+)?",
    r"[A-Za-z]",
    r"[A-Za-z]{2,}",
]


def _token_consumed(txt, compiled):
    import re
    t = (txt or "").strip()
    if not t:
        return False
    for rx in compiled:
        try:
            if rx.search(t):
                return True
        except Exception:
            log.debug("error ignored in _token_consumed", exc_info=True)
            continue
    return False


def render_ocr_consumed(state_path, out, node):
    from PIL import ImageDraw
    import re
    im = _load_rgb(state_path)
    d = ImageDraw.Draw(im)
    f = _font(max(12, im.width // 78))
    words = out.get("word_boxes") or []
    patterns = out.get("consume_patterns") or []
    if not patterns:
        patterns = _GENERIC_VALUE_SHAPES
    compiled = []
    for p in patterns:
        try:
            compiled.append(re.compile(p))
        except Exception:
            log.debug("error ignored in render_ocr_consumed", exc_info=True)
            continue
    lw = max(2, im.width // 380)
    n_green = 0
    for w in words:
        try:
            x0, y0, x1, y1 = [int(v) for v in w[:4]]
        except Exception:
            log.debug("error ignored in render_ocr_consumed", exc_info=True)
            continue
        txt = str(w[4]) if len(w) > 4 else ""
        consumed = _token_consumed(txt, compiled)
        if consumed:
            n_green += 1
            col = (60, 220, 110)
            d.rectangle([x0, y0, x1, y1], outline=col, width=lw + 1)
            label = txt[:18]
            if label:
                tw = d.textlength(label, font=f)
                ly = max(0, y0 - f.size - 5)
                d.rectangle([x0, ly, x0 + tw + 6, ly + f.size + 4], fill=col)
                d.text((x0 + 3, ly + 1), label, fill=(10, 12, 16), font=f)
        else:
            col = (150, 156, 168)
            d.rectangle([x0, y0, x1, y1], outline=col, width=1)
    banner = f"green = token consumed by the read ({n_green}/{len(words)}); grey = other text"
    bw = d.textlength(banner, font=f) + 16
    d.rectangle([6, 6, 6 + bw, 12 + f.size + 6], fill=(20, 22, 28))
    d.text((13, 11), banner, fill=(60, 220, 110), font=f)
    op = _state_path("ocrconsumed", (state_path, node.get("id"), len(words), n_green))
    im.save(op)
    return op, f"OCR consumed-token overlay: {n_green}/{len(words)} words entered the read"


def render_grid_cells(state_path, out, node):
    from PIL import ImageDraw
    im = _load_rgb(state_path)
    d = ImageDraw.Draw(im)
    f = _font(max(13, im.width // 70))
    read = out.get("read_grid")
    gtg = out.get("gt_grid")
    bbox = out.get("bbox")
    if not read or not bbox:
        op = _state_path("gridcells", (state_path, node.get("id"), "unreadable"))
        im.save(op)
        return op, "grid state unreadable (no lattice found)"
    x0, y0, x1, y1 = bbox
    R = len(read)
    C = max(len(r) for r in read)
    ch, cw = (y1 - y0) / R, (x1 - x0) / C
    match = total = 0
    lw = max(2, im.width // 500)
    for r in range(R):
        for c in range(len(read[r])):
            gx0, gy0 = x0 + c * cw, y0 + r * ch
            gx1, gy1 = gx0 + cw, gy0 + ch
            rv = read[r][c]
            gv = None
            if gtg and r < len(gtg) and c < len(gtg[r]):
                gv = gtg[r][c]
            if gv is None:
                col = (150, 156, 168)
            else:
                total += 1
                ok = str(rv).strip().lower() == str(gv).strip().lower()
                match += int(ok)
                col = (60, 200, 110) if ok else (235, 70, 70)
            d.rectangle([gx0 + 1, gy0 + 1, gx1 - 1, gy1 - 1], outline=col, width=lw)
            if gv is not None and str(rv).strip().lower() != str(gv).strip().lower():
                d.text((gx0 + 3, gy0 + 2), f"{str(rv)[:3]}|{str(gv)[:3]}", fill=(235, 70, 70), font=f)
    if total:
        ok_all = match == total
        col = (60, 200, 110) if ok_all else (235, 70, 70)
        banner = f"grid read vs reference: {match}/{total} cells match"
        bw = d.textlength(banner, font=f) + 18
        d.rectangle([8, 8, 8 + bw, 16 + f.size + 8], fill=(20, 22, 28))
        d.text((17, 14), banner, fill=col, font=f)
    op = _state_path("gridcells", (state_path, node.get("id"), R, C, match))
    im.save(op)
    return op, f"grid read overlaid: {match}/{total} cells match reference (red = mismatch, read|reference printed)"


RENDERERS = {
    "coin_boxes": render_coin_boxes,
    "detect_boxes": render_detect_boxes,
    "read_loc": render_read_loc,
    "grounded_boxes": render_grounded_boxes,
    "skeleton": render_skeleton,
    "contour": render_contour,
    "crop": render_crop,
    "ocr_words": render_ocr_words,
    "ocr_consumed": render_ocr_consumed,
    "grid_cells": render_grid_cells,
    "detect_boxes_audit": render_detect_boxes_audit,
    "ocr_words_audit": render_ocr_words_audit,
    "count_boxes": render_count_boxes,
    None: None,
}


def _ask(image, question, retries=2):
    from .ops.recognize import _reader
    im = _load_rgb(image)
    reads = []
    for _ in range(int(retries)):
        try:
            a = _reader()(im, question)
        except Exception:
            log.debug("error ignored in _ask", exc_info=True)
            a = None
        if a is not None:
            reads.append(str(a).strip().lower())
    return _ops.majority(reads)


_YES_WORDS = {"yes", "true", "aligned", "correct", "yeah", "yep", "affirmative"}
_NO_WORDS = {"no", "false", "misaligned", "incorrect", "wrong", "nope", "negative"}


def _yes_from(ans, yes_letter="a"):
    if ans is None:
        return None, 0.0
    import re
    s = str(ans).strip().lower()
    if not s:
        return False, 0.0
    yes_letter = str(yes_letter).strip().lower()[:1] or "a"
    no_letter = "b" if yes_letter == "a" else ("a" if yes_letter == "b" else None)
    yes_set = _YES_WORDS | {yes_letter}
    no_set = set(_NO_WORDS) | ({no_letter} if no_letter else set())
    vocab = yes_set | no_set
    toks = sorted(vocab, key=len, reverse=True)
    pat = r"(?<![a-z0-9])(" + "|".join(re.escape(t) for t in toks) + r")(?![a-z0-9])"
    hits = re.findall(pat, s)
    if not hits:
        return False, 0.0
    last = hits[-1]
    verdict = last in yes_set
    return (True, 1.0) if verdict else (False, 0.0)


def _mv_output(steps):
    for s in steps or []:
        if isinstance(s, dict):
            v = s.get("value")
            if isinstance(v, dict) and "verified" in v and "evidence" in v:
                return v
    return None


def _mv_replay_node(nid, verdict, detail, state_img, action):
    return {"id": nid, "kind": "leaf", "input_state": state_img, "action": action,
            "output": None, "state_img": state_img, "verdict": verdict, "score": None,
            "weight": 0.0, "gate": False, "detail": detail, "children": []}


def _mv_replays(mv):
    replays = []
    ev = (mv.get("evidence") or []) if isinstance(mv, dict) else []
    for i, e in enumerate(ev):
        if not isinstance(e, dict):
            continue
        verdict = e.get("verdict")
        brg = e.get("bearing")
        val = e.get("value")
        src = e.get("source")
        conf = verdict == "yes"
        head = ("VLM CONFIRMED red overlay ON the element" if conf
                else ("VLM rejected this candidate" if verdict == "no" else "VLM read unclear"))
        brg_txt = f" at {brg:g}°" if isinstance(brg, (int, float)) else ""
        src_txt = f" [{src}]" if src else ""
        detail = (f"candidate {i + 1}{src_txt}: red ray drawn{brg_txt} (value {val}); "
                  f"asked 'is the red overlay along the element?' -> '{e.get('answer')}' -> {verdict}")
        action = (f"Try {i + 1}: candidate{brg_txt} → VLM '{e.get('answer')}' → "
                  + ("VERIFIED" if conf else ("rejected" if verdict == 'no' else 'unclear')))
        replays.append(_mv_replay_node(f"mv_try{i + 1}", head + brg_txt, detail,
                                       e.get("overlay"), action))
    if isinstance(mv, dict):
        if mv.get("verified"):
            fv = ("overlay-verify verified after %s tries: measurement taken ON the element"
                  % mv.get("tries"))
        else:
            fv = "overlay-verify EXHAUSTED all candidates → hand to VLM direct read (no silent 0)"
        last_img = ev[-1].get("overlay") if ev and isinstance(ev[-1], dict) else None
        replays.append(_mv_replay_node(
            "mv_verdict", ("converged" if mv.get("verified") else "exhausted"),
            fv, last_img, "overlay-verify loop verdict"))
    return replays


def _attach_mv_replays(tr, res):
    try:
        steps = ((res or {}).get("output") or {}).get("steps")
        mv = _mv_output(steps)
        if mv is None:
            return
        replays = _mv_replays(mv)
        if replays:
            tr.setdefault("children", [])
            tr["children"][:0] = replays
    except Exception:
        log.debug("error ignored in _attach_mv_replays", exc_info=True)
        pass


def agentic_score(task, image_path, plan, reference_override=None):
    """Execute a verification-tree `plan` over `image_path`."""
    drain_legends()
    gt = _resolve_gt(task, image_path, reference_override)
    state = {"task": task, "image": image_path, "store": {}, "gt": gt}
    root = _run_node(plan, image_path, state, task)
    conflicts = ([])
    graded = _aggregate(root, task)
    strict = 100.0 if graded is not None and _all_leaves_pass(root) else 0.0
    out = {"id": task.get("id"), "graded": None if graded is None else round(graded, 1),
           "strict": strict, "tree": root}
    try:
        out["rollcall"] = check_rollcall(task, root)
    except Exception as e:
        log.debug("error ignored in agentic_score", exc_info=True)
        out["rollcall"] = {"error": "%s: %s" % (type(e).__name__, e)}
    try:
        mx = mutual_exclusion_scan(root)
        if mx:
            out["mutual_exclusion"] = mx
    except Exception:
        log.debug("error ignored in agentic_score", exc_info=True)
        pass
    held = _evaluator_held(root)
    collapse = []
    try:
        collapse = _content_collapse(task, root, out.get("rollcall"))
    except Exception as e:
        log.debug("error ignored in agentic_score", exc_info=True)
        out["content_collapse_error"] = "%s: %s" % (type(e).__name__, e)
    if collapse and out.get("graded") is not None:
        out["graded"] = None
    if collapse:
        _by_id = _nodes_by_id(root)
        for _lid in collapse:
            _n = _by_id.get(_lid)
            if isinstance(_n, dict):
                if not isinstance(_n.get("output"), dict):
                    _n["output"] = {}
                _n["output"]["content_collapse"] = True
                _n["output"].setdefault("held_reason", _COLLAPSE_HELD_SENTENCE)
        out["graded"], out["strict"] = None, None
        out["status"] = "EVALUATOR_HELD"
        out["escalate"] = True
        out["refused"] = True
        out["content_collapse"] = list(collapse)
        out["held_reason"] = _COLLAPSE_HELD_SENTENCE
        held = list(held) + [i for i in collapse if i not in held]
    if held:
        out["graded"], out["strict"] = None, None
        out["status"], out["evaluator_held"], out["escalate"] = "EVALUATOR_HELD", held, True
        out["refused"] = True
    if conflicts:
        out["graded"], out["strict"] = None, None
        out["conflicts"], out["escalate"] = conflicts, True
    return out


def _evaluator_held(root):
    out = []

    def walk(n):
        o = n.get("output") or {}
        if isinstance(o, dict) and o.get("evaluator_refused") and not o.get("diagnostic"):
            out.append(n.get("id"))
        for ch in n.get("children") or []:
            walk(ch)

    walk(root)
    return out


def _run_node(node, input_state, state, task):
    return _run_node_inner(node, input_state, state, task)


def _run_node_inner(node, input_state, state, task):
    kind = node["kind"]
    tr = {"id": node.get("id", kind), "kind": kind, "input_state": input_state,
          "action": node.get("action", ""), "output": None, "state_img": input_state,
          "verdict": None, "score": None, "weight": float(node.get("weight", 1.0)),
          "gate": bool(node.get("gate", False)), "detail": None, "children": []}

    if kind == "tool":
        out, action, produced = _exec_tool(node, input_state, state, task)
        tr["output"] = _jsonsafe(out)
        tr["action"] = action or tr["action"]
        tr["state_img"] = out.get("state_img_audit") or produced
        if node.get("gate"):
            ok = bool(out.get("gate_ok", True))
            tr["verdict"] = "ok" if ok else "FAIL(precheck)"
            tr["score"] = 1.0 if ok else 0.0
        if node.get("store"):
            state["store"][node["store"]] = out
        for ch in node.get("children", []):
            tr["children"].append(_run_node(ch, produced, state, task))

    elif kind == "vlm":
        q = node["question"]
        ans = _ask(input_state, q, node.get("retries", 2))
        verdict, sc = _yes_from(ans, node.get("yes_letter", "a"))
        tr["action"] = f"asked VLM: {q}"
        tr["output"] = {"answer": ans}
        tr["verdict"] = ("yes" if verdict else "no") if ans is not None else "unread"
        tr["score"] = sc
        tr["detail"] = f"raw='{ans}'"
        if node.get("store"):
            state["store"][node["store"]] = ans
        for ch in node.get("children", []):
            tr["children"].append(_run_node(ch, input_state, state, task))

    elif kind == "fork":
        produced = input_state
        if node.get("render"):
            fn = RENDERERS.get(node["render"])
            if fn:
                produced, tr["action"] = fn(input_state, node.get("render_args", {}), node)
        tr["state_img"] = produced
        tr["action"] = tr["action"] or node.get("action", "fork")
        for ch in node.get("children", []):
            tr["children"].append(_run_node(ch, produced, state, task))

    elif kind == "leaf":
        fn = node["fn"]
        res = fn(state) or {}
        tr["verdict"] = res.get("verdict")
        sc = res.get("score", 0.0)
        tr["score"] = None if sc is None else float(sc)
        tr["detail"] = res.get("detail")
        tr["output"] = _jsonsafe(res.get("output"))
        if res.get("state_img"):
            tr["state_img"] = res["state_img"]
        tr["action"] = node.get("action", "aggregate leaf")
        if res.get("gate_demoted"):
            tr["gate_demoted_frac"] = tr.get("score")
            tr["gate"] = False
            tr["score"] = None
            tr["gate_demoted"] = res["gate_demoted"]
            tr["verdict"] = "WARN (barred from being a door): %s" % (tr.get("verdict") or "")
        if res.get("reread_queue"):
            tr["reread_queue"] = res["reread_queue"]
        _attach_mv_replays(tr, res)

    else:
        raise ValueError(f"unknown node kind {kind}")

    _ev_verdict(tr)
    return tr


def _ev_verdict(tr):
    if tr.get("score") is None and tr.get("verdict") is None:
        return
    out = tr.get("output") if isinstance(tr.get("output"), dict) else {}
    sc = tr.get("score")
    v = "info" if sc is None else ("pass" if float(sc) >= 0.999 else
                                   ("fail" if float(sc) <= 0.001 else "partial"))


def _exec_tool(node, input_state, state, task):
    if "fn" in node:
        ctx = {"image": input_state, "task": task, "gt": state.get("gt", {}), "store": state["store"]}
        out = node["fn"](ctx, node) or {}
        action = node.get("action", "tool")
    else:
        op = node["op"]
        ctx = {"image": input_state, "task": task, "gt": state.get("gt", _gt_of(task))}
        for k, v in (node.get("args") or {}).items():
            ctx[k] = v
        step = {"op": op, "image": input_state, **(node.get("op_args") or {})}
        out = _ops.OPS[op](ctx, step)
        if not isinstance(out, dict):
            out = {"value": out}
        action = node.get("action", f"ran op {op}")

    produced = out.get("state_img") or input_state
    if node.get("render"):
        fn = RENDERERS.get(node["render"])
        if fn:
            produced, r_action = fn(input_state, out, node)
            action = r_action or action
    return out, action, produced


def _gt_of(task):
    vs = task.get("variants")
    if vs:
        return {**(task.get("gt", {})), **(vs[0].get("gt", {}))}
    return task.get("gt", {})


def _resolve_gt(task, image_path, reference_override):
    seed = dict(reference_override or {})
    if not seed and task.get("variants"):
        seed = dict(task["variants"][0].get("gt", {}))
    gtctx = {"image": image_path, "task": task, "gt": seed, **seed}
    gt_flow = (task.get("gt", {}) or {}).get("flow") or []
    if gt_flow:
        try:
            _ops.OPS
            from .engine import _run_flow as _rf
            _rf(gtctx, gt_flow)
        except Exception:
            log.debug("error ignored in _resolve_gt", exc_info=True)
            pass
    gt = {k: v for k, v in gtctx.items() if k not in ("image", "task", "gt")}
    gt.update(seed)
    return gt


def _scored_leaves(node):
    out = []
    if node.get("score") is not None:
        out.append(node)
    for ch in node["children"]:
        out.extend(_scored_leaves(ch))
    return out


def _aggregate(root, task=None):
    leaves = _scored_leaves(root)
    if not leaves:
        return None
    gates = [n for n in leaves if n.get("gate")]
    content = [n for n in leaves if not n.get("gate")]
    gate_prod = 1.0
    for g in gates:
        gate_prod *= g["score"]
    wsum = sum(n["weight"] for n in content)
    if not wsum:
        if task is not None and _content_collapse(task, root):
            return None
        return 100.0 * gate_prod
    mean = sum(n["weight"] * n["score"] for n in content) / wsum
    return 100.0 * mean * gate_prod


def _all_leaves_pass(root):
    for n in _scored_leaves(root):
        if n["score"] < 0.999:
            return False
    return True


_DISPLAY_GEOM_KEYS = {"note_boxes", "staff_lines", "barlines"}
_DISPLAY_GEOM_CAP = 200
_DISPLAY_STEPS_KEYS = {"steps"}
_DISPLAY_STEPS_CAP = 400


def _jsonsafe(o):
    import numpy as np
    if o is None:
        return None
    if isinstance(o, dict):
        clean = {}
        for k, v in o.items():
            if k in ("persons", "_rgb", "coins_raw"):
                clean[k] = f"<{k}:{len(v) if hasattr(v,'__len__') else '?'}>"
            elif k in _DISPLAY_GEOM_KEYS and isinstance(v, (list, tuple)):
                clean[k] = [_jsonsafe(x) for x in v[:_DISPLAY_GEOM_CAP]]
                if len(v) > _DISPLAY_GEOM_CAP:
                    clean[k].append(f"...(+{len(v) - _DISPLAY_GEOM_CAP})")
            elif k in _DISPLAY_STEPS_KEYS and isinstance(v, (list, tuple)):
                clean[k] = [_jsonsafe(x) for x in v[:_DISPLAY_STEPS_CAP]]
                if len(v) > _DISPLAY_STEPS_CAP:
                    clean[k].append(f"...(+{len(v) - _DISPLAY_STEPS_CAP})")
            else:
                clean[k] = _jsonsafe(v)
        return clean
    if isinstance(o, (list, tuple)):
        if len(o) > 40:
            return [_jsonsafe(x) for x in o[:40]] + [f"...(+{len(o)-40})"]
        return [_jsonsafe(x) for x in o]
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return round(float(o), 5)
    if isinstance(o, float):
        return round(o, 5)
    return o


_ROLLCALL_LANDED = "LANDED"
_ROLLCALL_DIAG = "DIAGNOSTIC_NOT_SCORED"
_ROLLCALL_SKIPPED = "SKIPPED"
_ROLLCALL_SKIPPED_ONLY_WHEN = "SKIPPED_ONLY_WHEN"
_ROLLCALL_SKIPPED_LIVE_GT = "SKIPPED_LIVE_GT_OUTAGE"
_SKIP_ONLY_WHEN_REASONS = (None, "", "only_when", "only_when_false", "only_when falsy")
_SKIP_LIVE_GT_REASONS = ("live_gt_unavailable", "live_gt_outage", "skip_on_null")
_ROLLCALL_HELD = "EVALUATOR_REFUSED"
_ROLLCALL_CONFLICT = "EVIDENCE_CONFLICT"
_ROLLCALL_DEMOTED = "GATE_DEMOTED"
_ROLLCALL_UNSCORED = "RAN_BUT_UNSCORED"
_ROLLCALL_MISSING = "UNACCOUNTED"


def mutual_exclusion_scan(root):
    leaves = _scored_leaves(root)
    by_target, out = {}, []
    for n in leaves:
        o = n.get("output") if isinstance(n.get("output"), dict) else {}
        t, v = o.get("target"), o.get("value")
        if t in (None, "", "None") or v in (None, "", "None"):
            continue
        by_target.setdefault(str(t), []).append((n.get("id"), str(v), n.get("score")))
    for t, rows in by_target.items():
        vals = {r[1] for r in rows}
        if len(rows) > 1 and len(vals) > 1:
            out.append({"kind": "same_target_split", "target": t,
                        "checks": [{"id": r[0], "value": r[1], "score": r[2]} for r in rows]})
    gates = [n for n in leaves if n.get("gate")]
    content = [n for n in leaves if not n.get("gate")]
    fired = [n for n in gates if isinstance(n.get("score"), (int, float)) and n["score"] < 0.999]
    if fired and content:
        mean = sum(float(n["score"]) for n in content) / len(content)
        if mean >= 0.5:
            out.append({"kind": "gate_vs_content_split", "content_mean": round(mean, 4),
                        "fired_gates": [n.get("id") for n in fired],
                        "content_checks": [{"id": n.get("id"), "score": n.get("score")}
                                         for n in content]})
    return out


def _nodes_by_id(root):
    out = {}

    def walk(n):
        i = n.get("id")
        if i is not None and i not in out:
            out[i] = n
        for ch in (n.get("children") or []):
            walk(ch)

    walk(root)
    return out


def check_rollcall(task, tree):
    nodes = _nodes_by_id(tree)
    check_recs, unaccounted, gates_missing = [], [], []
    for pt in (task.get("scoring") or []):
        if not isinstance(pt, dict):
            continue
        pid = pt.get("id")
        declared_gate = bool(pt.get("gate"))
        n = nodes.get(pid)
        rec = {"id": pid, "declared_gate": declared_gate,
               "declared_weight": pt.get("weight", 1.0)}
        if n is None:
            rec["state"] = _ROLLCALL_MISSING
            rec["why"] = ("the task declares this scoring point, but the verification tree has no node for it, so the check was never built")
            unaccounted.append(pid)
            if declared_gate:
                gates_missing.append(pid)
            check_recs.append(rec)
            continue
        out = n.get("output") if isinstance(n.get("output"), dict) else {}
        sc = n.get("score")
        rec["score"] = sc
        rec["effective_gate"] = bool(n.get("gate"))
        rec["verdict"] = n.get("verdict")
        if sc is not None:
            rec["state"] = _ROLLCALL_LANDED
        elif n.get("diagnostic") or out.get("diagnostic"):
            rec["state"] = _ROLLCALL_DIAG
            rec["why"] = ("a check with a `^d\\d+_` id or a `d2: true` field is kept as evidence only: it adds no score and does not block the result on either judging path, whatever the task file says about it")
        elif n.get("gate_demoted") or out.get("gate_demoted"):
            rec["state"] = _ROLLCALL_DEMOTED
            rec["why"] = n.get("gate_demoted") or out.get("gate_demoted")
            rec["would_have_scored"] = n.get("gate_demoted_frac")
        elif out.get("evaluator_refused"):
            rec["state"] = _ROLLCALL_HELD
            rec["why"] = out.get("held_reason") or "the reader refused"
        elif out.get("skip_reason") == "evidence_conflict" or n.get("conflict"):
            rec["state"] = _ROLLCALL_CONFLICT
            rec["why"] = n.get("detail") or "the task's own two evaluators disagreed"
        elif out.get("skipped"):
            _sr = out.get("skip_reason")
            _srk = _sr.strip().lower() if isinstance(_sr, str) else _sr
            if _srk in _SKIP_LIVE_GT_REASONS:
                rec["state"] = _ROLLCALL_SKIPPED_LIVE_GT
                rec["why"] = ('the answer key this check needed is produced by the live gt.flow and was unavailable on this run -- nothing about the model was measured')
            elif _srk in _SKIP_ONLY_WHEN_REASONS:
                rec["state"] = _ROLLCALL_SKIPPED_ONLY_WHEN
                rec["why"] = (n.get("detail") or
                              "the point's `only_when` condition is false, so the task says this check "
                              "does not apply to this variant (see `only_when` in engine.score_task)")
            else:
                rec["state"] = _ROLLCALL_SKIPPED
                rec["why"] = ("skipped naming a reason that is not one of the two allowed skips "
                              "(only_when / live-reference outage): %r -- treated as NOT lawfully "
                              "excluded until someone legislates it" % (_sr,))
            rec["skip_reason"] = _sr
        else:
            rec["state"] = _ROLLCALL_UNSCORED
            rec["why"] = ("the node ran and produced no number, and named no reason -- "
                          "treat as unaccounted until it names one")
            unaccounted.append(pid)
            if declared_gate:
                gates_missing.append(pid)
        if declared_gate and rec["state"] in (_ROLLCALL_MISSING, _ROLLCALL_UNSCORED):
            pass
        check_recs.append(rec)
    landed = sum(1 for r in check_recs if r["state"] == _ROLLCALL_LANDED)
    return {"n_declared": len(check_recs), "n_landed": landed, "checks": check_recs,
            "unaccounted": unaccounted, "gates_missing": gates_missing,
            "declared_gates": sum(1 for r in check_recs if r["declared_gate"]),
            "gates_landed": sum(1 for r in check_recs
                                if r["declared_gate"] and r["state"] == _ROLLCALL_LANDED)}


_COLLAPSE_LAWFUL_STATES = (_ROLLCALL_DIAG,
                           _ROLLCALL_SKIPPED_ONLY_WHEN,
                           _ROLLCALL_SKIPPED_LIVE_GT)


def _content_collapse(task, tree, rollcall=None):
    rc = rollcall if rollcall is not None else check_rollcall(task, tree)
    if not isinstance(rc, dict) or not rc.get("checks"):
        return []
    lost = []
    for r in rc["checks"]:
        if r.get("declared_gate"):
            continue
        if r.get("state") in (_ROLLCALL_LANDED,) + _COLLAPSE_LAWFUL_STATES:
            continue
        try:
            if float(r.get("declared_weight") or 0.0) <= 0.0:
                continue
        except (TypeError, ValueError):
            log.debug("error ignored in _content_collapse", exc_info=True)
            pass
        lost.append(r.get("id"))
    return lost


_COLLAPSE_HELD_SENTENCE = (
    "this task's content denominator collapsed -- every declared content checks left the aggregate without a stated reason, so the only survivors were doors. Publishing 100.0 x gate_product here would read a MISSING content measurement as a PERFECT one. Nothing was measured about the model, so nothing is charged to it: the task is withheld."
)


def flatten_questions(tree):
    items = []

    def walk(node):
        sc = node.get("score")
        is_scored = sc is not None
        if is_scored:
            out = node.get("output") or {}
            q = ""
            answer = ""
            if node["kind"] == "vlm":
                q = (node.get("action") or "").replace("asked VLM: ", "")
                answer = str(out.get("answer"))
            elif node["kind"] == "leaf":
                q = ((node.get("output") or {}).get("question")
                     or node.get("action") or node["id"])
                answer = str(node.get("verdict") or "")
            elif node["kind"] == "tool":
                q = node.get("action") or node["id"]
                answer = str(node.get("verdict") or "")
            item = {
                "n": len(items) + 1, "id": node["id"], "kind": node["kind"],
                "action": node.get("action") or "", "question": q, "answer": answer,
                "read": _read_of(node), "target": _target_of(node),
                "weight": node.get("weight"), "gate": node.get("gate"),
                "score": sc, "verdict": node.get("verdict"),
                "detail": node.get("detail"), "state_img": node.get("state_img")}
            if out.get("bearing_source"):
                item["bearing_source"] = out["bearing_source"]
            items.append(item)
        for ch in node["children"]:
            walk(ch)

    walk(tree)
    return items


def _read_of(node):
    v = node.get("verdict")
    d = node.get("detail")
    if node["kind"] == "vlm":
        return f"VLM='{(node.get('output') or {}).get('answer')}'"
    return f"{v}" + (f"  ({d})" if d else "")


def _target_of(node):
    return ""


_TASK_LABELS = {
    "scene_compliance": "Scene check - the picture really shows the requested subject",
    "scene_gate": "Scene check - the picture really shows the requested subject",
    "no_answer_text": "No-printed-answer check - the answer must not be written on the picture",
    "no_text": "No-printed-answer check - the answer must not be written on the picture",
    "anti_text": "No-printed-answer check - the answer must not be written on the picture",
    "headcount": "Per-item check",
    "count_verdict": "Per-item check - final verdict",
    "count_consistency": "Per-item check - repeat reads agree",
    "count_repair": "Per-item check - box step retuning loop",
    "main_count": "How many target objects are in the picture",
    "count_detect": "How many target objects the box step found",
    "grid": "Grid transcription",
    "grid_legible": "Grid is legible",
    "row_count": "Number of rows",
}

_DIAG_ID_RE = re.compile(r"^d\d*_")


def _humanize_id(nid):
    s = _DIAG_ID_RE.sub("", str(nid or "").strip())
    s = s.replace("__", " - ").replace("_", " ").strip()
    s = re.sub(r"\s+", " ", s)
    return (s[:1].upper() + s[1:]) if s else "check"


def _task_label(nid):
    key = str(nid or "")
    if key in _TASK_LABELS:
        return _TASK_LABELS[key]
    base = _DIAG_ID_RE.sub("", key)
    if base in _TASK_LABELS:
        return _TASK_LABELS[base]
    return _humanize_id(key)


