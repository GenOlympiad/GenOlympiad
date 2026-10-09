"""Evidence grounding: propose bounding boxes, helping lines or points, draw them and confirm them with the judge VLM."""
import json, os, re, shutil, tempfile, time
from PIL import Image, ImageDraw, ImageFont

from ._base import register, resolve
from genolympiad import judge_vlm, read_policy
from genolympiad import read_limits
from . import completeness_policy
from . import question_rules
from . import edge_ink
from . import line_check
from . import point_check
from . import per_box_reads
from . import box_admission
import logging

log = logging.getLogger(__name__)


_RENDER_KEYS = ("overlay_img", "state_img", "state_img_audit")
_AUDIT_KEEP_LAST = True
_RETAIN_ROOT = os.path.join(tempfile.gettempdir(), "genolympiad_evidence", str(os.getpid()))


class MemPng(str):

    __slots__ = ("pil",)

    def __new__(cls, path, pil):
        o = str.__new__(cls, str(path))
        o.pil = pil
        return o


def _emit_png(img, path):
    return MemPng(path, img)


def _send(x):
    pil = getattr(x, "pil", None)
    if pil is None:
        return x
    try:
        return pil.convert("RGB")
    except Exception:
        log.debug("error ignored in _send", exc_info=True)
        return pil


def _load(x):
    pil = getattr(x, "pil", None)
    if pil is not None:
        return pil.convert("RGB")
    return Image.open(str(x)).convert("RGB")


def _materialise(x, dst=None):
    pil = getattr(x, "pil", None)
    if pil is None:
        return x
    target = str(dst or x)
    try:
        d = os.path.dirname(target)
        if d:
            os.makedirs(d, exist_ok=True)
        pil.save(target)
        return target
    except Exception:
        log.debug("error ignored in _materialise", exc_info=True)
        return x


from genolympiad import temp_files as _janitor


def _own_tmp(path):
    try:
        if _janitor is not None:
            _janitor.own(path)
    except Exception:
        log.debug("error ignored in _own_tmp", exc_info=True)
        pass
    return path


def _norm(p):
    return os.path.normcase(os.path.abspath(str(p)))


def _remap(obj, mapping):
    if isinstance(obj, str):
        return mapping.get(_norm(obj), obj)
    if isinstance(obj, dict):
        return {k: _remap(v, mapping) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_remap(v, mapping) for v in obj]
    if isinstance(obj, tuple):
        return tuple(_remap(v, mapping) for v in obj)
    return obj


def _keep_set_mem(payload):
    keep = []
    if not isinstance(payload, dict):
        return keep
    for k in _RENDER_KEYS:
        v = payload.get(k)
        for p in (v if isinstance(v, list) else [v]):
            if isinstance(p, MemPng):
                keep.append(p)
    if _AUDIT_KEEP_LAST and not keep:
        ev = payload.get("evidence")
        if isinstance(ev, list) and ev and isinstance(ev[-1], MemPng):
            keep.append(ev[-1])
    return keep


def retire_workdir(wd, payload=None):
    try:
        mapping = {}
        for src in _keep_set_mem(payload):
            dst = os.path.join(_RETAIN_ROOT, os.path.basename(str(wd) or "mem"),
                               os.path.basename(str(src)))
            got = _materialise(src, dst)
            if got != src:
                mapping[_norm(src)] = got
                if _janitor is not None:
                    _janitor.own(got)
        out = _remap(payload, mapping) if mapping else payload
    except Exception:
        log.debug("error ignored in retire_workdir", exc_info=True)
        out = payload
    if wd and os.path.isdir(wd):
        shutil.rmtree(wd, ignore_errors=True)
    return out


class HeldRead(str):
    """A read that never produced an answer."""
    refused = True
    reason = "reader_hard_fail"


class ReadHeld(BaseException):
    refused = True

    def __init__(self, question, votes, reason="reader_hard_fail"):
        BaseException.__init__(self, "read held (%s): %s" % (reason, str(question)[:160]))
        self.question, self.votes, self.reason = question, votes, reason

    def payload(self, **extra):
        out = {"refused": True, "unreadable": True, "refusal": self.reason,
               "held": {"reason": self.reason, "question": str(self.question)[:400],
                        "votes": ["<held>" if getattr(v, "refused", False) else str(v)
                                  for v in (self.votes or [])]}}
        out.update(extra)
        return out


def _current_reader():
    fn = None
    try:
        from . import recognize as _recognize
        fn = getattr(_recognize, "_VLM_READER", None)
    except Exception:
        log.debug("error ignored in _current_reader", exc_info=True)
        fn = None
    return fn if fn is not None else judge_vlm.current()


def _ask(img, q, think=512, held=False):
    with judge_vlm.read_mode(thinking=think, max_tokens=2048):
        a = read_limits.wall_reader(_current_reader(), label="check reader")(_send(img), q)
    if a is None:
        return HeldRead() if held else None
    return str(a).strip()


def _gate(img, q, votes=3):
    vs = [_ask(img, read_policy.paraphrase(q, k), held=True) for k in range(votes)]
    if any(getattr(v, "refused", False) for v in vs):
        raise ReadHeld(q, vs)
    yes = sum(1 for v in vs if v and v.lower().startswith("y"))
    return yes * 2 > votes, vs


def _font(size=26):
    try:
        return ImageFont.truetype("arial.ttf", size)
    except Exception:
        log.debug("error ignored in _font", exc_info=True)
        return ImageFont.load_default()


_PRIM_JSON = {
    "ray": '{"point":[y,x]} anchors',
    "line": '{"line":[y0,x0,y1,x1]} (the two ENDPOINTS of %s%s)',
    "point": '{"point":[y,x]} (the exact location of %s%s)',
    "circle": '{"box_2d":[ymin,xmin,ymax,xmax]} (a TIGHT bounding box around %s%s)',
    "boxes": '[{"box_2d":[ymin,xmin,ymax,xmax]}, ...] (one tight box per %s)',
}
_PRIM_JSON_ARTICLE = ("line", "point", "circle")


def prim_json_fmt(kind, desc):
    fmt = _PRIM_JSON[kind]
    if kind in _PRIM_JSON_ARTICLE:
        return fmt % (question_rules.the_prefix(desc), desc)
    return (fmt % desc) if "%s" in fmt else fmt


def _knorm(s):
    return re.sub(r"[^0-9a-z]+", "", str(s).lower())


_K_BOX = ("box2d", "box", "bbox", "boundingbox", "boundingbox2d", "boxes")
_K_LINE = ("line", "line2d", "lines")
_K_POINT = ("point", "point2d", "points")
_K_CIRCLE = ("circle", "circle2d", "circles")


def _kget(obj, aliases):
    if not isinstance(obj, dict):
        return None
    norm = {}
    for k, v in obj.items():
        nk = _knorm(k)
        if nk not in norm:
            norm[nk] = v
    for a in aliases:
        if a in norm:
            return norm[a]
    return None


def _unwrap(v):
    if isinstance(v, (list, tuple)) and len(v) == 1 and isinstance(v[0], (list, tuple)):
        return v[0]
    return v


def _nums(v, n):
    if not isinstance(v, (list, tuple)) or len(v) < n:
        return None
    try:
        out = [float(x) for x in v[:n]]
    except (TypeError, ValueError):
        log.debug("error ignored in _nums", exc_info=True)
        return None
    return out


def _parse(kind, txt):
    m = re.search(r"[\[{].*[\]}]", txt or "", re.S)
    if not m:
        return None
    try:
        obj = json.loads(m.group(0))
    except Exception:
        log.debug("error ignored in _parse", exc_info=True)
        return None
    try:
        if kind == "line":
            v = _unwrap(_kget(obj, _K_LINE)) if isinstance(obj, dict) else obj
            return _nums(v, 4)
        if kind == "point":
            v = _unwrap(_kget(obj, _K_POINT)) if isinstance(obj, dict) else obj
            return _nums(v, 2)
        if kind == "circle":
            box = _unwrap(_kget(obj, _K_BOX)) if isinstance(obj, dict) else None
            v = _unwrap(_kget(obj, _K_CIRCLE)) if isinstance(obj, dict) else obj
            if box is None and _nums(v, 4) is not None and len(v) == 4:
                box, v = v, None
            if box is not None:
                b = _nums(box, 4)
                if b is None:
                    return None
                y0, x0, y1, x1 = b
                return [(y0 + y1) / 2.0, (x0 + x1) / 2.0, (abs(y1 - y0) + abs(x1 - x0)) / 4.0]
            return _nums(v, 3)
        if kind == "boxes":
            def _is_box_list(v):
                return isinstance(v, (list, tuple)) and len(v) == 4 and _nums(v, 4) is not None

            arr = None
            if isinstance(obj, list):
                arr = [obj] if _is_box_list(obj) else obj
            elif isinstance(obj, dict):
                top = _kget(obj, _K_BOX)
                if isinstance(top, list) and not _is_box_list(top):
                    arr = top
                elif top is None:
                    for w in obj.values():
                        if isinstance(w, list) and w:
                            arr = w
                            break
            if arr is None:
                arr = [obj]
            out = []
            for o in arr:
                v = _unwrap(_kget(o, _K_BOX)) if isinstance(o, dict) else o
                b = _nums(v, 4)
                if b is None or len(v) != 4:
                    continue
                y0, x0, y1, x1 = b
                out.append([min(y0, y1), min(x0, x1), max(y0, y1), max(x0, x1)])
            return out or None
    except Exception:
        log.debug("error ignored in _parse", exc_info=True)
        return None
    return None


_COORD_MAX = 1000.0
_COORD_EPS = 0.5
RANGE_OBJECTION = ("the coordinates must be inside 0-1000 (normalized per-mille of THIS "
                   "image), not pixels, and the shape must not be degenerate")


def _finite(v):
    try:
        f = float(v)
    except (TypeError, ValueError):
        log.debug("error ignored in _finite", exc_info=True)
        return None
    if f != f or f in (float("inf"), float("-inf")):
        return None
    return f


def _in_range(v):
    f = _finite(v)
    return f is not None and -_COORD_EPS <= f <= _COORD_MAX + _COORD_EPS


def _clamp01k(v):
    return min(_COORD_MAX, max(0.0, float(v)))


def geom_legal(kind, geom):
    if geom is None:
        return False, "output was not parseable JSON"
    k = "line" if kind == "ray" else kind
    try:
        if k == "point":
            if len(geom) < 2 or not all(_in_range(v) for v in geom[:2]):
                return False, RANGE_OBJECTION
            return True, None
        if k == "line":
            if len(geom) < 4 or not all(_in_range(v) for v in geom[:4]):
                return False, RANGE_OBJECTION
            y0, x0, y1, x1 = [float(v) for v in geom[:4]]
            if abs(y1 - y0) < 1e-6 and abs(x1 - x0) < 1e-6:
                return False, "the two endpoints were identical (a zero-length line marks nothing)"
            return True, None
        if k == "circle":
            if len(geom) < 3 or not all(_in_range(v) for v in geom[:3]):
                return False, RANGE_OBJECTION
            if float(geom[2]) <= 0.0:
                return False, "the circle had zero radius"
            return True, None
        if k == "boxes":
            if not isinstance(geom, (list, tuple)) or not len(geom):
                return False, "no boxes were returned"
            for b in geom:
                if not isinstance(b, (list, tuple)) or len(b) < 4:
                    return False, RANGE_OBJECTION
                if not all(_in_range(v) for v in b[:4]):
                    return False, RANGE_OBJECTION
                ymin, xmin, ymax, xmax = [float(v) for v in b[:4]]
                if ymax - ymin <= 0 or xmax - xmin <= 0:
                    return False, "a rectangle had zero width or zero height"
            return True, None
    except (TypeError, ValueError):
        log.debug("error ignored in geom_legal", exc_info=True)
        return False, RANGE_OBJECTION
    return True, None


def clamp_geom(kind, geom):
    k = "line" if kind == "ray" else kind
    if geom is None:
        return None
    if k == "boxes":
        return [[_clamp01k(v) for v in b[:4]] for b in geom]
    return [_clamp01k(v) for v in geom]


CTX_FORMAT_OBJECTION = ('reply with FOUR ACTUAL INTEGERS, e.g. {"box_2d":[120,340,660,890]} -- '
                        "never echo the placeholder words ymin/xmin/ymax/xmax")


def redraw_opening(dk):
    """('A contrasting-colour', '<noun>', 'is') for this primitive."""
    return ("A contrasting-colour", dk, "is")


def redraw_trace_target(desc):
    return "the %s" % desc


def placeholder_echoed(txt):
    return bool(False)
CTX_TOO_SMALL = ("the box was far too small to be that container: it must frame the WHOLE %s "
                 "together with everything the question names around it, not a close-up of one "
                 "small part inside it")
CTX_TOO_TIGHT = ("the previous crop was too tight -- asked inside it, the target could not be "
                 "seen at all. Give a much WIDER box that keeps the %s and its surroundings in "
                 "view")
_CTX_MIN_AREA = 0.04
_CTX_LONG_SIDE = 0.60
_CTX_LONG_AREA = 0.02
_CTX_FILL_SUSPECT = 0.60
_NOT_VISIBLE = re.compile(
    r"(not\s+(visible|present|shown)|is\s+not\s+in\s+th(is|e)\s+image|"
    r"(cannot|can\s?not|can't|unable to)\s+(see|find|locate|identify)|"
    r"there\s+is\s+no\b|no\s+\w[\w\s\-]{0,40}\s+(is\s+)?(visible|present))", re.I)


def ctx_size_ok(box01k):
    y0, x0, y1, x1 = [float(v) for v in box01k[:4]]
    w, h = abs(x1 - x0) / 1000.0, abs(y1 - y0) / 1000.0
    if w * h < _CTX_MIN_AREA and not (max(w, h) >= _CTX_LONG_SIDE and w * h >= _CTX_LONG_AREA):
        return False, ("the box covers only %.0f%% x %.0f%% of the picture" % (w * 100, h * 100))
    return True, None


def _ctx_parse(txt):
    s = txt or ""
    m = re.search(r"\[\s*-?\d+(?:\.\d+)?(?:\s*[,\s]\s*-?\d+(?:\.\d+)?){3}\s*\]", s)
    if not m:
        why = ("the answer echoed the placeholder words instead of numbers"
               if re.search(r"\b[xy](min|max)\b", s, re.I)
               else "the answer carried no four-number box_2d list")
        return None, why
    v = [float(x) for x in re.findall(r"-?\d+(?:\.\d+)?", m.group(0))][:4]
    if len(v) < 4:
        return None, "the four-number box could not be parsed"
    y0, x0, y1, x1 = v
    box = [min(y0, y1), min(x0, x1), max(y0, y1), max(x0, x1)]
    ok, why = geom_legal("boxes", [box])
    return (box, None) if ok else (None, why)


def _context_crop(base, im, context, workdir, W, H, transcript, budget, objection=None, tag=0):
    while budget > 0:
        budget -= 1
        qc = ('Locate %s%s. Output STRICT JSON only: {"box_2d":[ymin,xmin,ymax,xmax]} '
              'normalized 0-1000.' % (question_rules.the_prefix(context), context))
        if objection:
            qc += "\nYour previous answer was rejected: %s. %s" % (objection, CTX_FORMAT_OBJECTION)
        rc = _ask(base, qc, think=512)
        transcript.append((qc, rc))
        box, why = _ctx_parse(rc)
        if box is not None:
            ok, why = ctx_size_ok(box)
            if ok:
                cb = (int(box[1] * W / 1000), int(box[0] * H / 1000),
                      int(box[3] * W / 1000), int(box[2] * H / 1000))
                cb = (max(0, cb[0]), max(0, cb[1]), min(W, cb[2]), min(H, cb[3]))
                if cb[2] - cb[0] > 40 and cb[3] - cb[1] > 40:
                    zoom = im.crop(cb)
                    if min(zoom.size) < 700:
                        zoom = zoom.resize((zoom.width * 2, zoom.height * 2), Image.LANCZOS)
                    zp = os.path.join(workdir, "context_zoom.png" if not tag
                                      else "context_zoom_%d.png" % tag)
                    zp = _emit_png(zoom, zp)
                    return zp, cb, budget
                why = "the box was only %dx%d pixels" % (cb[2] - cb[0], cb[3] - cb[1])
            else:
                why = why + "; " + (CTX_TOO_SMALL % context)
        transcript.append(("(context attempt %d rejected)" % (tag + 1), why))
        objection = why
        tag += 1
    transcript.append(("(context)", "context degraded to full frame -- the container could not be "
                                    "located after the retries (%s)" % (objection or "no proposal")))
    return base, (0, 0, W, H), 0


def _fill_frac(kind, geom):
    if kind == "boxes" and geom:
        ys = [v for b in geom for v in (b[0], b[2])]
        xs = [v for b in geom for v in (b[1], b[3])]
    elif kind == "circle" and geom:
        ys, xs = [geom[0] - geom[2], geom[0] + geom[2]], [geom[1] - geom[2], geom[1] + geom[2]]
    else:
        return None
    return ((max(ys) - min(ys)) / 1000.0, (max(xs) - min(xs)) / 1000.0)


def inv_color(im, box_px):
    vals = [_finite(v) for v in box_px]
    if any(v is None for v in vals):
        return (255, 0, 255)
    x0, y0, x1, y1 = [int(v) for v in vals]
    x0, x1 = min(x0, x1), max(x0, x1)
    y0, y1 = min(y0, y1), max(y0, y1)
    x0 = min(max(0, x0), max(0, im.width - 1))
    y0 = min(max(0, y0), max(0, im.height - 1))
    x1 = max(x0 + 1, min(im.width, x1))
    y1 = max(y0 + 1, min(im.height, y1))
    patch = im.crop((x0, y0, x1, y1)).resize((8, 8))
    px = list(patch.getdata())
    r = sum(p[0] for p in px) // len(px)
    g = sum(p[1] for p in px) // len(px)
    b = sum(p[2] for p in px) // len(px)
    inv = (255 - r, 255 - g, 255 - b)
    if max(inv) - min(inv) < 40 and all(80 < c < 176 for c in inv):
        cands = [(255, 0, 255), (0, 255, 0), (255, 128, 0), (0, 128, 255)]
        inv = max(cands, key=lambda c: abs(c[0] - r) + abs(c[1] - g) + abs(c[2] - b))
    return inv


def _adaptive_pair(im, path):
    try:
        from genolympiad.evaluation_tree import adaptive_contrast_color
        return adaptive_contrast_color(im, path)
    except Exception:
        log.debug("error ignored in _adaptive_pair", exc_info=True)
        return (255, 0, 255), (12, 12, 12)


def _seg_pts(p, n=60):
    x0, y0, x1, y1 = [float(v) for v in p]
    return [(x0 + (x1 - x0) * i / float(n), y0 + (y1 - y0) * i / float(n)) for i in range(n + 1)]


def _ring_pts(cx, cy, r, n=72):
    import math as _math
    return [(cx + r * _math.cos(2 * _math.pi * i / n), cy + r * _math.sin(2 * _math.pi * i / n))
            for i in range(n)]


def _halo_text(d, xy, s, col, cas, font):
    x, y = xy
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            if dx or dy:
                d.text((x + dx, y + dy), s, fill=cas, font=font)
    d.text((x, y), s, fill=col, font=font)


def _pen_for_path(im, path, box_px, adaptive=None):
    if True if adaptive is None else adaptive:
        return _adaptive_pair(im, path)
    return inv_color(im, box_px), None


def _draw(kind, geom, im):
    ov = im.copy()
    d = ImageDraw.Draw(ov)
    W, H = im.size

    def reg(x0, y0, x1, y1, pad=8):
        return (min(x0, x1) - pad, min(y0, y1) - pad, max(x0, x1) + pad, max(y0, y1) + pad)

    if kind == "line":
        y0, x0, y1, x1 = geom
        p = [x0 * W / 1000, y0 * H / 1000, x1 * W / 1000, y1 * H / 1000]
        col, cas = _pen_for_path(im, _seg_pts(p), reg(p[0], p[1], p[2], p[3]), True)
        if cas is not None:
            d.line(p, fill=cas, width=10)
            d.line(p, fill=col, width=6)
        else:
            d.line(p, fill=col, width=6)
    elif kind == "point":
        y, x = geom
        px, py = x * W / 1000, y * H / 1000
        r = 12.0
        col, cas = _pen_for_path(im, _ring_pts(px, py, r),
                                 (px - r - 4, py - r - 4, px + r + 4, py + r + 4), True)
        if cas is not None:
            d.ellipse([px - r, py - r, px + r, py + r], outline=cas, width=9)
            d.ellipse([px - r, py - r, px + r, py + r], outline=col, width=5)
        else:
            d.ellipse([px - r, py - r, px + r, py + r], outline=col, width=5)
    elif kind == "circle":
        cy, cx, r = geom
        px, py, pr = cx * W / 1000, cy * H / 1000, r * min(W, H) / 1000
        col, cas = _pen_for_path(im, _ring_pts(px, py, pr, 96),
                                 (px - pr, py - pr, px + pr, py + pr), True)
        if cas is not None:
            d.ellipse([px - pr, py - pr, px + pr, py + pr], outline=cas, width=9)
            d.ellipse([px - pr, py - pr, px + pr, py + pr], outline=col, width=5)
        else:
            d.ellipse([px - pr, py - pr, px + pr, py + pr], outline=col, width=5)
    elif kind == "boxes":
        for i, (ymin, xmin, ymax, xmax) in enumerate(geom):
            bx = [xmin * W / 1000, ymin * H / 1000, xmax * W / 1000, ymax * H / 1000]
            col, cas = _pen_for_path(im, (bx[0], bx[1], bx[2], bx[3]),
                                     (bx[0], bx[1], bx[2], bx[3]), True)
            if cas is not None:
                d.rectangle(bx, outline=cas, width=8)
                d.rectangle(bx, outline=col, width=4)
                _halo_text(d, (bx[0] + 4, bx[1] + 4), str(i + 1), col, cas, _font())
            else:
                d.rectangle(bx, outline=col, width=4)
                d.text((bx[0] + 4, bx[1] + 4), str(i + 1), fill=col, font=_font())
    return ov


def pen_word(rgb):
    try:
        r, g, b = [max(0, min(255, int(round(float(c))))) for c in tuple(rgb)[:3]]
    except Exception:
        log.debug("error ignored in pen_word", exc_info=True)
        return "contrasting-colour"
    mx, mn = max(r, g, b), min(r, g, b)
    v = mx / 255.0
    s = 0.0 if mx == 0 else (mx - mn) / float(mx)
    if s < 0.18:
        return ("white" if v > 0.85 else "light grey" if v > 0.60 else
                "grey" if v > 0.30 else "dark grey" if v > 0.12 else "black")
    c = float(mx - mn)
    if mx == r:
        h = 60.0 * (((g - b) / c) % 6.0)
    elif mx == g:
        h = 60.0 * (((b - r) / c) + 2.0)
    else:
        h = 60.0 * (((r - g) / c) + 4.0)
    w = ("red" if (h < 15.0 or h >= 345.0) else "orange" if h < 45.0 else
         "yellow" if h < 70.0 else "green" if h < 165.0 else "cyan" if h < 195.0 else
         "blue" if h < 255.0 else "purple" if h < 285.0 else
         "magenta" if h < 320.0 else "pink")
    return ("dark " + w) if v < 0.45 else w


def pen_phrase(col, cas=None, kindword="line"):
    w = pen_word(col)
    if cas is None:
        return "%s %s" % (w, kindword)
    cw = pen_word(cas)
    return ("%s %s" % (w, kindword)) if cw == w else ("%s %s outlined in %s"
                                                      % (w, kindword, cw))


def pen_style_phrase(kind, geom, im, kindword=None):
    kw = kindword or ("line" if kind in ("line", "ray") else str(kind))
    try:
        W, H = im.size
        if kind in ("line", "ray"):
            y0, x0, y1, x1 = geom
            p = [x0 * W / 1000, y0 * H / 1000, x1 * W / 1000, y1 * H / 1000]
            box = (min(p[0], p[2]) - 8, min(p[1], p[3]) - 8,
                   max(p[0], p[2]) + 8, max(p[1], p[3]) + 8)
            col, cas = _pen_for_path(im, _seg_pts(p), box)
            return pen_phrase(col, cas, kw)
    except Exception:
        log.debug("error ignored in pen_style_phrase", exc_info=True)
        pass
    return "contrasting-colour %s" % kw


def _style_bind(gqs, kind, geom, im):
    if not any(callable(q) for _lbl, q in gqs):
        return gqs
    ph = pen_style_phrase(kind, geom, im)
    return [(lbl, (q(ph) if callable(q) else q)) for lbl, q in gqs]


_TINY_BOX_AREA = 0.0015
_PANO_FRAME_FRAC = 0.25
_PANO_BOX_MULT = 8.0


_LAYOUT_MARGIN = 1.5
_LAYOUT_MIN_N = 2


def _centres(boxes):
    out = []
    for b in boxes or []:
        y0, x0, y1, x1 = [float(v) for v in list(b)[:4]]
        out.append(((y0 + y1) / 2.0, (x0 + x1) / 2.0))
    return out


def _spread(vals):
    return (max(vals) - min(vals)) if vals else 0.0


def transpose_boxes(boxes):
    return [[float(b[1]), float(b[0]), float(b[3]), float(b[2])] for b in (boxes or [])]


def layout_fix(boxes, layout):
    lay = str(layout or "").strip().lower()
    if lay not in ("row", "column") or len(boxes or []) < _LAYOUT_MIN_N:
        return list(boxes or []), False, None
    c = _centres(boxes)
    sy, sx = _spread([p[0] for p in c]), _spread([p[1] for p in c])
    along, across = (sx, sy) if lay == "row" else (sy, sx)
    if across > along * _LAYOUT_MARGIN:
        return (transpose_boxes(boxes), True,
                "layout=%s but the answered set spreads %.0f across vs %.0f along: the two "
                "coordinate axes are swapped, transposed" % (lay, across, along))
    return list(boxes), False, ("layout=%s consistent (%.0f along vs %.0f across)"
                                % (lay, along, across))


def sort_reading_order(boxes, layout=None):
    bs = list(boxes or [])
    if len(bs) < 2:
        return bs, list(range(len(bs)))
    col = str(layout or "").strip().lower() == "column"
    c = _centres(bs)
    prim = [p[1] if col else p[0] for p in c]
    sec = [p[0] if col else p[1] for p in c]
    sizes = sorted((abs(float(b[3]) - float(b[1])) if col else abs(float(b[2]) - float(b[0])))
                   for b in bs)
    band = max(1e-6, sizes[len(sizes) // 2]) * 0.6
    idx = sorted(range(len(bs)), key=lambda i: prim[i])
    out, start = [], None
    band_items = []
    for i in idx:
        if start is None or (prim[i] - start) <= band:
            if start is None:
                start = prim[i]
            band_items.append(i)
        else:
            out += sorted(band_items, key=lambda j: sec[j])
            band_items, start = [i], prim[i]
    out += sorted(band_items, key=lambda j: sec[j])
    return [bs[i] for i in out], out


def boxes_bbox_frac(geom):
    if not geom:
        return 0.0
    ys = [v for b in geom for v in (float(b[0]), float(b[2]))]
    xs = [v for b in geom for v in (float(b[1]), float(b[3]))]
    return ((max(ys) - min(ys)) / 1000.0) * ((max(xs) - min(xs)) / 1000.0)


def is_tiny_boxes(geom):
    return bool(geom) and boxes_bbox_frac(geom) < _TINY_BOX_AREA


_GIANT_AREA_MULT = 5.0
_GIANT_MIN_N = 3
_GIANT_ASK_CAP = 2


def box_area_frac(box):
    return ((abs(float(box[2]) - float(box[0])) / 1000.0)
            * (abs(float(box[3]) - float(box[1])) / 1000.0))


def giant_boxes(geom, mult=_GIANT_AREA_MULT, min_n=_GIANT_MIN_N, cap=_GIANT_ASK_CAP):
    if not geom or len(geom) < min_n:
        return []
    areas = [box_area_frac(b) for b in geom]
    s = sorted(areas)
    n = len(s)
    med = s[n // 2] if n % 2 else 0.5 * (s[n // 2 - 1] + s[n // 2])
    if med <= 0:
        return []
    over = [i for i, v in enumerate(areas) if v > mult * med]
    over.sort(key=lambda i: -areas[i])
    return over[:cap]


def panorama_region(bbox_px, W, H, ctx_box=None):
    x0, y0, x1, y1 = [float(v) for v in bbox_px]
    side = _PANO_FRAME_FRAC ** 0.5
    ww = min(float(W), max(side * W, _PANO_BOX_MULT * (x1 - x0)))
    hh = min(float(H), max(side * H, _PANO_BOX_MULT * (y1 - y0)))
    cx, cy = (x0 + x1) / 2.0, (y0 + y1) / 2.0
    rx0, ry0 = cx - ww / 2.0, cy - hh / 2.0
    rx0 = min(max(0.0, rx0), max(0.0, W - ww))
    ry0 = min(max(0.0, ry0), max(0.0, H - hh))
    r = [rx0, ry0, rx0 + ww, ry0 + hh]
    if ctx_box:
        c = [float(v) for v in ctx_box]
        r = [min(r[0], c[0]), min(r[1], c[1]), max(r[2], c[2]), max(r[3], c[3])]
    return (max(0, int(r[0])), max(0, int(r[1])), min(W, int(r[2])), min(H, int(r[3])))


CONTENT_Q = ("The RIGHT panel has a small contrasting-colour rectangle drawn on the picture "
             "(numbered 1); the LEFT panel shows the same view without it. That rectangle is very "
             "small, so look carefully at the area it encloses. In ONE short sentence: what is "
             "inside that rectangle? Name the object that is actually there -- and if the "
             "rectangle encloses no distinct object, say instead which surface or background is "
             "inside it.")

_STOP = set("""
the a an of on in at to for from with by as is are was were be been it its their there and or but
not no only just very whole entire each every some any which what where when who while than then
this that these those them they you your our my me he she we us into onto over under above below
near next beside inside within around against along across between behind front back rear top
bottom side left right upper lower middle centre center corner edge end part portion piece area
region zone spot place position section half quarter
box boxes rectangle rectangles marker markers ring rings outline outlines drawn drawing draw
overlay overlays panel panels image picture photo photograph frame view scene shown shows show
showing visible seen see appears appear appearing look looks looking contains containing contain
enclosed enclosing encloses labelled labeled label number numbered colour color coloured colored
contrasting highlighted marked mark
small large big little tiny huge long short tall wide narrow thin thick round oval flat
red green blue yellow black white grey gray brown orange purple pink silver gold golden dark
light bright pale shiny
object objects thing things something anything stuff sort kind type
""".split())

_NEG_SPLIT = re.compile(r"\b(?:not|never|rather\s+than|instead\s+of|excluding|except|ignore|"
                        r"ignoring|avoid)\b", re.I)
_HEAD_SPLIT = re.compile(r"\s--\s|[;(:]|,")
_PREP_CUT = re.compile(r"\b(?:of|on|in|at|above|below|under|beneath|near|next|beside|inside|"
                       r"within|behind|between|along|across|that|which|sitting|standing|lying|"
                       r"printed|drawn|marked|attached|belonging)\b", re.I)


_CROP_PAD = 0.20
_CROP_PAD_MIN_PX = 6
_CROP_LEGACY_FLOOR = 200
_CROP_SHORT_FLOOR = 96
_CROP_SHORT_TARGET = 192


def glyph_floor_px(im, box01k, W, H, pad=_CROP_PAD):
    shipped = crop_pad_px(box01k, W, H, pad)
    return shipped, 0, None


def crop_pad_px(box01k, W, H, pad=_CROP_PAD, min_margin_px=None):
    ymin, xmin, ymax, xmax = [float(v) for v in list(box01k)[:4]]
    x0, x1 = min(xmin, xmax) * W / 1000.0, max(xmin, xmax) * W / 1000.0
    y0, y1 = min(ymin, ymax) * H / 1000.0, max(ymin, ymax) * H / 1000.0
    m = max(float(_CROP_PAD_MIN_PX), max(x1 - x0, y1 - y0) * max(0.0, float(pad)))
    if min_margin_px:
        m = max(m, float(min_margin_px))
    return (max(0, int(round(x0 - m))), max(0, int(round(y0 - m))),
            min(W, int(round(x1 + m))), min(H, int(round(y1 + m))))


def magnify_crop(c, floor=_CROP_SHORT_FLOOR, target=_CROP_SHORT_TARGET):
    """Upscale a small crop so its short side reaches the target size."""
    w, h = c.size
    s = min(w, h)
    if s <= 0:
        return c
    f = 2.0 if s < _CROP_LEGACY_FLOOR else 1.0
    if s < floor:
        import math as _m
        f = max(f, float(_m.ceil(float(target) / float(s))))
    if f <= 1.0:
        return c
    if f > 4.0:
        c = c.resize((max(1, int(round(w * 2))), max(1, int(round(h * 2)))), Image.LANCZOS)
        w, h = c.size
        f = f / 2.0
    return c.resize((max(1, int(round(w * f))), max(1, int(round(h * f)))), Image.LANCZOS)


def _sing(w):
    if len(w) > 4 and w.endswith("ies"):
        return w[:-3] + "y"
    if len(w) > 4 and w.endswith("es") and w[-3] in "sxzh":
        return w[:-2]
    if len(w) > 3 and w.endswith("s") and not w.endswith("ss"):
        return w[:-1]
    return w


def _content_words(s):
    return set(_sing(w) for w in re.findall(r"[a-z0-9]+", (s or "").lower())
               if len(w) >= 3 and w not in _STOP and _sing(w) not in _STOP)


def positive_target(t):
    return _NEG_SPLIT.split(str(t or ""))[0]


def target_core_words(target):
    pos = positive_target(target)
    head = _HEAD_SPLIT.split(pos)[0]
    for cand in (_PREP_CUT.split(head)[0], head, pos):
        ws = _content_words(cand)
        if ws:
            return ws
    return set()


def _tok_match(a, b):
    a, b = (w[:-1] + "ie" if w.endswith("y") else w for w in (a, b))
    if a == b:
        return True
    return len(a) >= 5 and len(b) >= 5 and a[:5] == b[:5]


def content_matches(answer, target):
    if not str(answer or "").strip():
        return False, ("asked what that rectangle actually encloses, the verifier gave no answer, "
                       "so an empty rectangle cannot be ruled out")
    want = target_core_words(target)
    if not want:
        return True, "no distinctive words in the target sentence to compare against"
    got = _content_words(answer)
    hits = sorted(w for w in want if any(_tok_match(g, w) for g in got))
    if hits:
        return True, "the answer names %s" % "/".join(hits[:3])
    return False, ("asked what that rectangle actually encloses, the verifier answered \"%s\" -- "
                   "that is not the %s, so the rectangle is on the wrong thing (or on nothing)"
                   % (str(answer).strip()[:160], "/".join(sorted(want)[:4])))


CONTENT_Q_GIANT = ("The RIGHT panel has a large contrasting-colour rectangle drawn on the picture "
                   "(numbered 1); the LEFT panel shows the same view without it. That rectangle is "
                   "unusually large, so look carefully at EVERYTHING it encloses. In ONE short "
                   "sentence: what is inside that rectangle? Name what is actually there -- and if "
                   "the rectangle encloses SEVERAL separate objects rather than one single object, "
                   "say so and say how many.")

_MULTI_WORDS = set("""
group groups cluster clusters bunch bunches batch batches collection collections set sets
row rows column columns array arrays grid pile piles stack stacks heap heaps crowd swarm flock
herd several multiple many numerous various assorted both together handful couple pair dozen
two three four five six seven eight nine ten eleven twelve
""".split())
_SPELLED = {"two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8,
            "nine": 9, "ten": 10, "eleven": 11, "twelve": 12, "couple": 2, "pair": 2, "dozen": 12}
_MULTI_WINDOW = 4


def describes_group(answer, target):
    want = target_core_words(target)
    if not want:
        return False, None
    tgt = set(re.sub(r"[^a-z0-9]+", " ", str(target or "").lower()).split())
    toks = re.sub(r"[^a-z0-9]+", " ", str(answer or "").lower()).split()
    for i, t in enumerate(toks):
        n = _SPELLED.get(t, 2 if (t.isdigit() and 2 <= int(t) <= 999) else None)
        if t in tgt or (t not in _MULTI_WORDS and n is None):
            continue
        if n is not None and n < 2:
            continue
        for nxt in toks[i + 1:i + 1 + _MULTI_WINDOW]:
            if any(_tok_match(_sing(nxt), w) for w in want):
                return True, t
    return False, None


def content_matches_giant(answer, target):
    if not str(answer or "").strip():
        return False, ("asked what that large rectangle encloses, the verifier gave no answer, "
                       "so a rectangle roped around a whole group cannot be ruled out")
    grouped, marker = describes_group(answer, target)
    if grouped:
        return False, ("asked what that rectangle encloses, the verifier answered \"%s\" -- "
                       "\"%s\" says it holds SEVERAL of them, so this one rectangle is roped "
                       "around a GROUP rather than a single %s (over-coverage: the mirror of the "
                       "#20 empty box)" % (str(answer).strip()[:160], marker, str(target)[:60]))
    ok, why = content_matches(answer, target)
    if not ok:
        return False, why
    return True, "%s, and describes a single object" % why


def _region(kind, geom, W, H, pad=0.12, ctx_box=None):
    if kind == "point":
        cy, cx = geom[0] * H / 1000.0, geom[1] * W / 1000.0
        half = 0.20 * max(W, H)
        return (max(0, int(cx - half)), max(0, int(cy - half)),
                min(W, int(cx + half)), min(H, int(cy + half)))
    if kind == "line":
        if ctx_box:
            cx0, cy0, cx1, cy1 = [float(v) for v in list(ctx_box)[:4]]
            return (max(0, int(min(cx0, cx1))), max(0, int(min(cy0, cy1))),
                    min(W, int(max(cx0, cx1))), min(H, int(max(cy0, cy1))))
        return (0, 0, int(W), int(H))
    if kind == "circle":
        cy, cx, r = geom
        ys, xs = [cy - r, cy + r], [cx - r, cx + r]
    else:
        ys = [v for b in geom for v in (b[0], b[2])]
        xs = [v for b in geom for v in (b[1], b[3])]
    x0, x1 = min(xs) * W / 1000, max(xs) * W / 1000
    y0, y1 = min(ys) * H / 1000, max(ys) * H / 1000
    if kind == "boxes":
        if is_tiny_boxes(geom):
            return panorama_region((x0, y0, x1, y1), W, H, ctx_box)
        pw = max((x1 - x0) * 0.35, 0.10 * max(W, H))
        ph = max((y1 - y0) * 0.35, 0.10 * max(W, H))
        return (max(0, int(x0 - pw)), max(0, int(y0 - ph)),
                min(W, int(x1 + pw)), min(H, int(y1 + ph)))
    pw, ph = max((x1 - x0), 60) * pad + 30, max((y1 - y0), 60) * pad + 30
    return (max(0, int(x0 - pw)), max(0, int(y0 - ph)),
            min(W, int(x1 + pw)), min(H, int(y1 + ph)))


def _sheet(im, ov, region, path, magnify=False):
    a = im.crop(region)
    b = ov.crop(region)
    if magnify and 0 < a.width < 1024:
        s = 1024.0 / a.width
        a = a.resize((1024, max(1, int(a.height * s))), Image.LANCZOS)
        b = b.resize((1024, max(1, int(b.height * s))), Image.LANCZOS)
    elif min(a.size) < 260:
        a = a.resize((a.width * 2, a.height * 2), Image.LANCZOS)
        b = b.resize((b.width * 2, b.height * 2), Image.LANCZOS)
    if a.width > 1100:
        s = 1100.0 / a.width
        a = a.resize((1100, int(a.height * s)), Image.LANCZOS)
        b = b.resize((1100, int(b.height * s)), Image.LANCZOS)
    W, H = a.size
    sheet = Image.new("RGB", (W * 2 + 24, H + 40), "white")
    sheet.paste(a, (0, 40))
    sheet.paste(b, (W + 24, 40))
    d = ImageDraw.Draw(sheet)
    d.text((6, 6), "ORIGINAL", fill=(0, 0, 0), font=_font(22))
    d.text((W + 30, 6), "TRACED", fill=(200, 0, 0), font=_font(22))
    try:
        pass
    except Exception:
        log.debug("error ignored in _sheet", exc_info=True)
        pass
    path = _emit_png(sheet, path)
    return path


_DEDUPE_IOU = 0.5
_INC_TRY_CAP = 6
_INC_ZERO_STREAK = 2


_NO_REDRAW_N = 10
NO_REDRAW_NOTE = ("multi-box set verified, diagnosis no-op, full-redraw forbidden "
                  "-> honest refusal")


def redraw_forbidden(kind, geom):
    try:
        return kind == "boxes" and geom is not None and len(geom) >= _NO_REDRAW_N
    except TypeError:
        log.debug("error ignored in redraw_forbidden", exc_info=True)
        return False


def _iou01k(a, b):
    ay0, ax0, ay1, ax1 = [float(v) for v in list(a)[:4]]
    by0, bx0, by1, bx1 = [float(v) for v in list(b)[:4]]
    ih = max(0.0, min(ay1, by1) - max(ay0, by0))
    iw = max(0.0, min(ax1, bx1) - max(ax0, bx0))
    inter = ih * iw
    ua = (ay1 - ay0) * (ax1 - ax0) + (by1 - by0) * (bx1 - bx0) - inter
    return inter / ua if ua > 0 else 0.0


def dedupe_boxes(boxes, thr=_DEDUPE_IOU):
    """Drop boxes that overlap an already-kept one by more than `thr` (first kept wins)."""
    keep = []
    for b in boxes or []:
        if all(_iou01k(b, k) < thr for k in keep):
            keep.append(b)
    return keep


def merge_boxes(kept, extra, thr=_DEDUPE_IOU):
    out = list(kept or [])
    added = 0
    for b in extra or []:
        if all(_iou01k(b, k) < thr for k in out):
            out.append(b)
            added += 1
    return out, added


def admit_to_kept(kept, extra, thr=_DEDUPE_IOU, provenance="", transcript=None, info=None):
    return box_admission.admit(kept, extra, merge_boxes, thr, provenance, transcript, info)


def _legal_boxes(cand):
    out = []
    for b in cand or []:
        if geom_legal("boxes", [b])[0]:
            out.append(clamp_geom("boxes", [b])[0])
    return out


def _ab_pick(ans):
    s = str(ans or "").upper()
    m = re.search(r"\b(?:SET|PANEL|PROPOSAL|OPTION)\s+([AB])\b", s)
    if m:
        return m.group(1)
    m = re.match(r"^\W*([AB])\b", s)
    if m:
        return m.group(1)
    m = re.search(r"\b([AB])\b", s)
    return m.group(1) if m else None


INC_RESIDUAL_Q = ('This picture already has %d contrasting-colour numbered rectangles drawn on it, '
                  'one around each %s that has already been found. Some may have been MISSED. '
                  'Output STRICT JSON only: [{"box_2d":[ymin,xmin,ymax,xmax]}, ...] normalized '
                  '0-1000 of THIS image, with ONE entry for each %s that still has NO rectangle '
                  'around it. Do NOT repeat any %s that already has a rectangle. If every one of '
                  'them already has a rectangle, output [].')


def incremental_propose_boxes(im, seed, tdesc, workdir, transcript, cap=_INC_TRY_CAP,
                         zero_streak=_INC_ZERO_STREAK, thr=_DEDUPE_IOU):
    """Add bounding boxes for missed instances, try by try, until the judge VLM finds no more."""
    kept = dedupe_boxes(_legal_boxes(seed), thr)
    zeros = 0
    tries = 0
    for r in range(int(cap)):
        tries = r + 1
        ov = _draw("boxes", kept, im)
        p = os.path.join(workdir, "increment_r%d.png" % r)
        p = _emit_png(ov, p)
        q = INC_RESIDUAL_Q % (len(kept), tdesc, tdesc, tdesc)
        raw = _ask(p, q, think=1024)
        cand = _legal_boxes(_parse("boxes", raw) or [])
        kept, added = admit_to_kept(kept, cand, thr, "incremental residual", transcript)
        if transcript is not None:
            transcript.append(("%s [increment try %d]" % (q, r + 1), raw))
            transcript.append(("(increment try %d)" % (r + 1),
                               "%d residual boxes offered, %d were new after the IoU>%.2f dedupe "
                               "-> %d boxes in hand" % (len(cand), added, thr, len(kept))))
        if added == 0:
            zeros += 1
            if zeros >= int(zero_streak):
                if transcript is not None:
                    transcript.append(("(increment)", "verified: %d consecutive tries added "
                                                      "nothing" % zeros))
                break
        else:
            zeros = 0
    else:
        if transcript is not None:
            transcript.append(("(increment)", "stopped at the try cap (%d tries)" % int(cap)))
    return kept, {"tries": tries, "n": len(kept)}


DIAG_BOXES_Q = ('The picture has contrasting-colour numbered rectangles drawn on it. Each '
                'rectangle should TIGHTLY enclose exactly %s%s, and every %s in the picture '
                'must have a rectangle of its own. List every problem you can see. Output STRICT '
                'JSON only:\n[{"issue":"misaligned"|"phantom"|"missed"|"multiple","box":<the '
                'rectangle number or null>,"fix_box_2d":[ymin,xmin,ymax,xmax] or null}, ...]\n'
                'Rules: "misaligned"/"multiple" MUST name the rectangle number AND give the '
                'corrected box for the single %s it should enclose; "phantom" names a rectangle '
                'to delete and needs no fix box; "missed" gives a new box for %s%s that has none. '
                'Coordinates normalized 0-1000 of THIS image. If there are no problems, output [].')


DEL_CHECK_Q = ("This picture is a close-up crop taken from a bigger photograph. Is there %s%s in "
               "it? Answer with the single word yes or no only.")

_ARTICLES = frozenset(("the", "a", "an"))
_LEADING_ARTICLE_RE = re.compile(r"^(the|a|an)\s+", re.I)


class _Stripped(str):
    __slots__ = ("article",)

    def __new__(cls, value, article):
        o = str.__new__(cls, value)
        o.article = str(article or "").lower()
        return o

    def __reduce__(self):
        return (_Stripped, (str(self), self.article))


def strip_leading_article(desc):
    if not isinstance(desc, str):
        return desc
    m = _LEADING_ARTICLE_RE.match(desc)
    if not m:
        return desc
    rest = desc[m.end():].strip()
    if not rest:
        return desc
    if _LEADING_ARTICLE_RE.match(rest) or rest.strip().lower() in _ARTICLES:
        return desc
    return _Stripped(rest, m.group(1))


assert "Is there %s%s in " in DEL_CHECK_Q, ": DEL_CHECK_Q lost its article slot"


def del_check_question(desc):
    desc = question_rules.crop_target(desc)
    shipped = "an " if getattr(desc, "article", None) == "an" else "a "
    return DEL_CHECK_Q % (question_rules.article_prefix(desc, shipped), desc)


_DIM_FACTOR = 0.38
_DIM_FRAME_PX = 3
_DIM_FRAME_RGB = (0, 255, 0)


def frame_and_dim(crop_img, box, px, W, H):
    try:
        from PIL import Image as _I, ImageDraw as _ID
        im2 = crop_img.convert("RGB")
        cw, ch = im2.size
        sx = cw / max(1.0, float(px[2] - px[0]))
        sy = ch / max(1.0, float(px[3] - px[1]))
        y0, x0, y1, x1 = [float(v) for v in list(box)[:4]]
        bx0 = (x0 / 1000.0 * W - px[0]) * sx
        by0 = (y0 / 1000.0 * H - px[1]) * sy
        bx1 = (x1 / 1000.0 * W - px[0]) * sx
        by1 = (y1 / 1000.0 * H - px[1]) * sy
        ix0, iy0 = int(round(max(0, min(cw, bx0)))), int(round(max(0, min(ch, by0))))
        ix1, iy1 = int(round(max(0, min(cw, bx1)))), int(round(max(0, min(ch, by1))))
        if ix1 - ix0 < 2 or iy1 - iy0 < 2:
            return crop_img
        out = _I.eval(im2, lambda v: int(v * _DIM_FACTOR))
        out.paste(im2.crop((ix0, iy0, ix1, iy1)), (ix0, iy0))
        _ID.Draw(out).rectangle([ix0, iy0, ix1 - 1, iy1 - 1], outline=_DIM_FRAME_RGB,
                                width=_DIM_FRAME_PX)
        return out
    except Exception:
        log.debug("error ignored in frame_and_dim", exc_info=True)
        return crop_img


def confirm_deletion(im, box, tdesc, workdir, tag, transcript, votes=3, pad=_CROP_PAD):
    W, H = im.size
    c = magnify_crop(im.crop(crop_pad_px(box, W, H, pad)))
    p = os.path.join(workdir, "delcheck_%s.png" % tag)
    p = _emit_png(c, p)
    q = del_check_question(tdesc)
    vs = [_ask(p, read_policy.paraphrase(q, k)) for k in range(int(votes))]
    nos = sum(1 for v in vs if v and str(v).strip().lower().startswith("n"))
    ok = (len(vs) == int(votes) and nos == int(votes))
    if transcript is not None:
        transcript.append(
            ("%s [delete_check %s] (unanimous %d/%d 'no' required before a rectangle is deleted, "
             "#31 -- the mirror of the #12 rescue rule)" % (q, tag, int(votes), int(votes)),
             "%s -> %s" % ("/".join(str(v) for v in vs),
                           "delete" if ok else "KEEP (the vote is not unanimous)")))
    return ok, vs


def diagnose_repair(im, geom, tdesc, workdir, tag, transcript, thr=_DEDUPE_IOU, votes=3):
    ov = _draw("boxes", geom, im)
    p = os.path.join(workdir, "diagnose_r%s.png" % tag)
    p = _emit_png(ov, p)
    q = DIAG_BOXES_Q % (question_rules.one_prefix(tdesc), tdesc, tdesc, tdesc,
                        question_rules.a_prefix(tdesc), tdesc)
    raw = _ask(p, q, think=1024)
    if transcript is not None:
        transcript.append(("%s [structured diagnosis, try %s]" % (q, tag), raw))
    m = re.search(r"\[.*\]", raw or "", re.S)
    if not m:
        return None
    try:
        issues = json.loads(m.group(0))
    except Exception:
        log.debug("error ignored in diagnose_repair", exc_info=True)
        return None
    if not isinstance(issues, list) or not issues:
        return None
    drop, pending = set(), []
    for it in issues:
        if not isinstance(it, dict):
            continue
        issue = str(it.get("issue", "")).strip().lower()
        bn = it.get("box")
        fx = it.get("fix_box_2d")
        fxb = None
        if isinstance(fx, (list, tuple)) and len(fx) >= 4:
            v = _nums(fx, 4)
            if v is not None:
                cand = [min(v[0], v[2]), min(v[1], v[3]), max(v[0], v[2]), max(v[1], v[3])]
                fxb = (clamp_geom("boxes", [cand])[0] if geom_legal("boxes", [cand])[0] else None)
        if issue == "phantom" and isinstance(bn, int):
            drop.add(bn)
        elif issue in ("misaligned", "multiple") and isinstance(bn, int):
            drop.add(bn)
            if fxb:
                pending.append((bn, fxb))
        elif issue == "missed" and fxb:
            pending.append((None, fxb))
    approved, refused = set(), set()
    for bn in sorted(n for n in drop if isinstance(n, int) and 1 <= n <= len(geom)):
        ok, _vs = confirm_deletion(im, geom[bn - 1], tdesc, workdir,
                                   "r%s_b%d" % (tag, bn), transcript, votes=votes)
        (approved if ok else refused).add(bn)
    add = [b for bn, b in pending if bn is None or bn in approved]
    new = [b for i, b in enumerate(geom) if (i + 1) not in approved]
    new, n_added = admit_to_kept(new, add, thr, "diagnosis repair", transcript)
    if transcript is not None:
        transcript.append(("(diagnosis repair try %s)" % tag,
                           "%d rectangle(s) deleted, %d corrected/added -> %d boxes%s; the "
                           "repaired set is re-proposed and must pass the same unchanged gate"
                           % (len(approved), n_added, len(new),
                              ("; %d proposed deletion(s) REFUSED by the %d/%d per-box vote and "
                               "kept" % (len(refused), int(votes), int(votes)))
                              if refused else "")))
    if not new or new == list(geom):
        return None
    return new


_DIAG_LEAF_ID = re.compile(r"^d\d+_")


def diagnostic_leaf(point):
    if not isinstance(point, dict):
        return False
    return bool(point.get("d2")) or bool(_DIAG_LEAF_ID.match(str(point.get("id") or "")))


def point_of(ctx):
    pid = (ctx or {}).get("_point")
    if not pid:
        return None
    for pt in (((ctx or {}).get("task") or {}).get("scoring") or []):
        if isinstance(pt, dict) and pt.get("id") == pid:
            return pt
    return None


def resolve_propose_boxes(propose_boxes, expected_n=None, observed_n=None, diagnostic=False):
    nom = str(propose_boxes or "vlm").strip().lower()
    return "incremental" if nom == "incremental" else "vlm"


_SWEEP_TRY_CAP = 8
_SWEEP_STALL = 2
_REPEAT_DEGEN_N = 4
_SWEEP_COUNT_SLACK = 2

SWEEP_RESIDUAL_Q = (
    "This picture has %d contrasting-colour numbered rectangles drawn on it, one around each "
    "%s found so far. Look carefully across the WHOLE picture, including the edges and corners: "
    "is there any %s NOT yet inside a rectangle? If yes, output STRICT JSON only: "
    '[{"box_2d":[ymin,xmin,ymax,xmax]}, ...] normalized 0-1000 of THIS image, one entry for '
    "each missed %s -- never repeat one that already has a rectangle. If every %s is already "
    "inside a rectangle, answer with the single word no.")
SWEEP_COUNT_Q = ("How many of these are in this picture: %s? Count carefully across the whole "
                 "picture. Answer with just the number.")
SWEEP_DIRECTED_Q = (
    "An independent count found about %d %s in this picture, but only %d are inside the "
    "numbered rectangles shown. So some may still be WITHOUT a rectangle. Search the whole "
    "picture, working left to right, top to bottom. Output STRICT JSON only: "
    '[{"box_2d":[ymin,xmin,ymax,xmax]}, ...] normalized 0-1000 of THIS image, one entry per '
    "%s that has NO rectangle yet -- never repeat one that already has a rectangle. If you "
    "are certain every %s is already inside a rectangle, answer with the single word no.")
SWEEP_QUAD_Q = (
    "This picture is divided into four quarters by the thin magenta cross lines. Look ONLY at "
    "the %s quarter. Is there any %s in that quarter NOT inside a rectangle? If yes, output "
    'STRICT JSON only: [{"box_2d":[ymin,xmin,ymax,xmax]}, ...] normalized 0-1000 of the WHOLE '
    "picture, one entry per missed %s in that quarter. If every %s in that quarter is inside "
    "a rectangle, answer with the single word no.")
_SWEEP_QUAD_MAX = 2

SWEEP_SEAM_Q = (
    "This picture has a thin magenta cross drawn across it. Look ONLY at the %s of the picture "
    "-- %s. Ignore everything outside it. Is there any %s in that part NOT inside a rectangle? "
    'If yes, output STRICT JSON only: [{"box_2d":[ymin,xmin,ymax,xmax]}, ...] normalized 0-1000 '
    "of the WHOLE picture, one entry per missed %s there. If every %s in that part is already "
    "inside a rectangle, answer with the single word no.")
_SEAM_HALVES = (("TOP HALF", "everything above the horizontal magenta line, left and right of "
                             "the vertical one alike"),
                ("BOTTOM HALF", "everything below the horizontal magenta line, left and right of "
                                "the vertical one alike"),
                ("LEFT HALF", "everything left of the vertical magenta line, above and below the "
                              "horizontal one alike"),
                ("RIGHT HALF", "everything right of the vertical magenta line, above and below "
                               "the horizontal one alike"))


def _sweep_quadrant_pass(im, kept, tdesc, workdir, transcript, evidence, tag, thr,
                         reverse=False, exempt=None, halves=False):
    from PIL import ImageDraw
    ov = _draw("boxes", kept, im)
    d = ImageDraw.Draw(ov)
    W, H = ov.size
    d.line([(W // 2, 0), (W // 2, H)], fill=(255, 0, 255), width=3)
    d.line([(0, H // 2), (W, H // 2)], fill=(255, 0, 255), width=3)
    p = os.path.join(workdir, "sweep_quad_%s.png" % tag)
    p = _emit_png(ov, p)
    if evidence is not None:
        evidence.append(p)
    names = (_SEAM_HALVES if halves
             else ("TOP-LEFT", "TOP-RIGHT", "BOTTOM-LEFT", "BOTTOM-RIGHT"))
    added, all_no = 0, True
    rec = {"quarters": [], "added": 0, "grid": "halves" if halves else "quarters"}
    for qi, entry in enumerate(names):
        if halves:
            qname, qwhere = entry
            q = SWEEP_SEAM_Q % (qname, qwhere, tdesc, tdesc, tdesc)
        else:
            qname = entry
            q = SWEEP_QUAD_Q % (qname, tdesc, tdesc, tdesc)
        raw = _ask(p, q, think=1024)
        if transcript is not None:
            transcript.append(("%s [sweep quadrant %s]" % (q, qname), raw))
        if _sweep_all_boxed(raw):
            rec["quarters"].append({"q": qname, "answer": "no"})
            continue
        cand = [b for b in _legal_boxes(_parse("boxes", raw) or [])
                if not _sweep_giant(b, kept)]
        got = 0
        n_boxed_hit = 0
        n_vet_rej = 0
        n_vet_silent = 0
        for bi, b in enumerate(cand):
            if any(_iou01k(b, k) >= thr for k in kept):
                n_boxed_hit += 1
                continue
            if _covered_by(b, kept):
                n_boxed_hit += 1
                continue
            ok, _a = _sweep_vet_box(im, b, tdesc, workdir,
                                    "quad%s_%s_b%d" % (tag, qname, bi + 1), transcript,
                                    exempt=exempt)
            idb = "sweep.quad%s.%s.%d" % (tag, qname, bi + 1)
            if ok:
                kept2, nadd = admit_to_kept(kept, [b], thr,
                                            "quadrant %s candidate" % qname, transcript)
                del kept[:]
                kept.extend(kept2)
                got += nadd
            else:
                n_vet_rej += 1
                if _a is None or not str(_a).strip():
                    n_vet_silent += 1
        clean = (got == 0 and n_vet_rej == 0 and cand and n_boxed_hit == len(cand))
        adjudicated = False
        if (not clean and reverse and got == 0 and cand and n_vet_rej > 0 and n_vet_silent == 0 and (n_vet_rej + n_boxed_hit) == len(cand)):
            clean, adjudicated = True, True
        if not clean:
            all_no = False
        qrow = {"q": qname, "offered": len(cand), "added": got,
                "already_boxed_hits": n_boxed_hit, "vet_rejected": n_vet_rej,
                "clean": bool(clean)}
        if n_vet_silent:
            qrow["vet_silent"] = n_vet_silent
        if adjudicated:
            qrow["adjudicated"] = True
            if transcript is not None:
                transcript.append(
                    ("(sweep quadrant %s / %s)" % (tag, qname),
                     'the quarter named %d candidate violation(s) and the per-crop vet refuted every one of them on its own magnified crop -- on a REVERSE sweep that is adjudicated evidence of cleanliness, not a stall, so this quarter counts as answering no' % n_vet_rej))
        rec["quarters"].append(qrow)
        added += got
    rec["added"] = added
    if transcript is not None:
        transcript.append(("(sweep %s pass %s)" % ("seam" if halves else "quadrant", tag),
                           "four %s checks: %d added; %s" %
                           ("half-picture" if halves else "quarter", added,
                            "ALL regions clean (answered no, or offered only "
                            "provably already-boxed content)" if all_no else
                            "at least one region added or had a vet-rejected offer")))
    return added, all_no, rec


def sweep_on(v):
    return str(v if v is not None else "").strip().lower() in ("1", "true", "yes", "on",
                                                               "exhaustive")


def repeat_degenerate(text, n=_REPEAT_DEGEN_N):
    raw = str(text or "")
    lines = [ln.strip() for ln in raw.splitlines() if ln.strip()]
    run, prev = 1, None
    for ln in lines:
        if prev is not None and ln == prev:
            run += 1
            if run >= n and len(ln) >= 3:
                return ln
        else:
            run = 1
        prev = ln
    toks = re.sub(r"\s+", " ", raw).strip().split(" ")
    for plen in range(1, 11):
        if plen * n > len(toks):
            break
        for i in range(0, len(toks) - plen * n + 1):
            ph = toks[i:i + plen]
            if len(" ".join(ph)) < 3:
                continue
            k = 1
            while toks[i + k * plen: i + (k + 1) * plen] == ph:
                k += 1
            if k >= n:
                return " ".join(ph)
    return None


_VET_CTX_PAD = 10
_VET_CTX_MAXW = 720


def _vet_context_panel(im, box, crop):
    ctx = _draw("boxes", [box], im)
    W, H = ctx.size
    if max(W, H) > _VET_CTX_MAXW:
        s = float(_VET_CTX_MAXW) / float(max(W, H))
        ctx = ctx.resize((max(1, int(W * s)), max(1, int(H * s))), Image.LANCZOS)
    cw, ch = crop.size
    xw, xh = ctx.size
    h = max(ch, xh)
    out = Image.new("RGB", (cw + _VET_CTX_PAD + xw, h), (255, 255, 255))
    out.paste(crop, (0, (h - ch) // 2))
    out.paste(ctx, (cw + _VET_CTX_PAD, (h - xh) // 2))
    return out


_VET_CTX_Q = ("The LEFT panel is a close-up cut-out of one spot in the photograph on the RIGHT, "
              "and that same spot is outlined on the right so you can see what surrounds it. "
              "Look at the LEFT panel, using the RIGHT panel to see where it came from. "
              "Is there %s%s in it? Answer with the single word yes or no only.")


def _sweep_vet_box(im, box, tdesc, workdir, tag, transcript, exempt=None):
    W, H = im.size
    c = magnify_crop(im.crop(crop_pad_px(box, W, H, _CROP_PAD)))
    ctx_panel = True
    if ctx_panel:
        try:
            c = _vet_context_panel(im, box, c)
        except Exception:
            log.debug("error ignored in _sweep_vet_box", exc_info=True)
            ctx_panel = False
    p = os.path.join(workdir, "sweepvet_%s.png" % tag)
    p = _emit_png(c, p)
    if ctx_panel:
        q = sweep_vet_question_full(tdesc, exempt)
    else:
        q = sweep_vet_question(tdesc, exempt)
    a = _ask(p, q)
    ok = bool(a and str(a).strip().lower().startswith("y"))
    if transcript is not None:
        transcript.append(("%s [sweep vet %s]" % (q, tag),
                           "%s -> %s" % (a, "keep" if ok else "reject (not %s%s)"
                                         % (question_rules.a_prefix(tdesc), tdesc))))
    return ok, a


def _sweep_all_boxed(raw):
    s = str(raw or "").strip().lower()
    if not s:
        return False
    if re.match(r"^\W*(no|none)\b", s) and not re.match(r"^\W*no[,.\s]+(there|i)\b.*\byes\b", s):
        return True
    m = re.search(r"\[\s*\]", s)
    return bool(m) and "box_2d" not in s


def _median(vals):
    v = sorted(vals)
    return v[len(v) // 2] if v else None


def _sweep_count_read(im, tdesc, workdir, transcript, votes=3, offset=0):
    q = SWEEP_COUNT_Q % tdesc
    ns, raws = [], []
    for k in range(int(votes)):
        a = _ask(im, read_policy.paraphrase(q, int(offset) + k))
        raws.append(None if a is None else str(a)[:60])
        m = re.search(r"\d+", str(a or ""))
        if m:
            ns.append(int(m.group(0)))
    n = _median(ns)
    if transcript is not None:
        transcript.append(("%s [sweep count cross-check%s]" % (q, " recount" if offset else ""),
                           "%s -> median %s" % ("/".join(str(x) for x in raws), n)))
    return n, raws


def _inside_frac(a, b):
    ay0, ax0, ay1, ax1 = [float(v) for v in list(a)[:4]]
    by0, bx0, by1, bx1 = [float(v) for v in list(b)[:4]]
    ih = max(0.0, min(ay1, by1) - max(ay0, by0))
    iw = max(0.0, min(ax1, bx1) - max(ax0, bx0))
    return (ih * iw) / max(1e-9, (ay1 - ay0) * (ax1 - ax0))


def _sweep_giant(box, kept):
    if (box_admission.giant_backstop(box)[0] and not any(_iou01k(box, k) >= _DEDUPE_IOU for k in kept or [])):
        return True
    if len(kept) < _GIANT_MIN_N:
        return False
    med = _median([_area01k(b) for b in kept])
    return med is not None and med > 0 and _area01k(box) > _GIANT_AREA_MULT * med


def _area01k(b):
    y0, x0, y1, x1 = [float(v) for v in list(b)[:4]]
    return max(0.0, y1 - y0) * max(0.0, x1 - x0)


def _covered_by(b, kept, frac=0.8):
    kept = list(kept or [])
    for i, k in enumerate(kept):
        if box_admission.shield_disqualified(k, kept[:i] + kept[i + 1:])[0]:
            continue
        y0, x0 = max(float(b[0]), float(k[0])), max(float(b[1]), float(k[1]))
        y1, x1 = min(float(b[2]), float(k[2])), min(float(b[3]), float(k[3]))
        inter = max(0.0, y1 - y0) * max(0.0, x1 - x0)
        if inter / max(1e-9, _area01k(b)) >= frac:
            return True
    return False


def _stall_partial_consensus(info, kept, n_count, why, im=None, rnd=0, transcript=None):
    if info.get("complete"):
        return bool(info.get("complete"))
    n = len(kept)
    if n < 1 or n_count is None:
        return False
    try:
        if abs(int(n_count) - n) > _SWEEP_COUNT_SLACK:
            return False
    except (TypeError, ValueError):
        log.debug("error ignored in _stall_partial_consensus", exc_info=True)
        return False
    tail = [rr for rr in (info.get("tries") or [])
            if isinstance(rr, dict) and "added" in rr][-_SWEEP_STALL:]
    if len(tail) < _SWEEP_STALL or any(rr.get("added") for rr in tail):
        return False
    info["complete"] = True
    info["certificate"] = "stall_partial_consensus"
    info["degraded_exit"] = True
    info["degraded_reason"] = why
    info["terminal_answer"] = ("no terminal 'no'; certified on partial consensus "
                               "(%d boxes, independent count read %s)" % (n, n_count))
    if im is not None:
        pass
    if transcript is not None:
        transcript.append(("(sweep)",
                           "DEGRADED EXIT: the completeness check never reached a terminal "
                           "'no' (%s), but the whole-set coverage question had already "
                           "passed and the check's own independent count read (%s) agrees "
                           "with the %d kept boxes both ways -- partial consensus, so the "
                           "set is certified and marked degraded rather than the whole check "
                           "being refused. Nothing was added in the stalled tries."
                           % (why, n_count, n)))
    return True


def _revsweep_adjudicated_exit(info, kept, n_count, why, im=None, rnd=0, transcript=None):
    if info.get("complete"):
        return bool(info.get("complete"))
    if kept:
        return False
    offered = vetoed = added = silent = 0
    for rr in info.get("tries") or []:
        if not isinstance(rr, dict):
            continue
        if "offered" in rr:
            offered += int(rr.get("offered") or 0)
            vetoed += int(rr.get("vetoed") or 0)
            added += int(rr.get("added") or 0)
            silent += int(rr.get("vet_silent") or 0)
        q = rr.get("quadrant") or rr.get("quadrant_last_resort")
        if isinstance(q, dict):
            added += int(q.get("added") or 0)
            for qq in q.get("quarters") or []:
                if not isinstance(qq, dict):
                    continue
                offered += int(qq.get("offered") or 0)
                vetoed += int(qq.get("vet_rejected") or 0)
                silent += int(qq.get("vet_silent") or 0)
    if added or silent or vetoed < 1 or offered != vetoed:
        return False
    info["complete"] = True
    info["certificate"] = "adjudicated_exhaustion"
    info["degraded_exit"] = True
    info["degraded_reason"] = why
    info["adjudicated"] = {"claims_offered": offered, "claims_refuted": vetoed, "added": 0}
    if n_count is not None:
        info["count_impeached"] = n_count
    info["terminal_answer"] = ("no terminal 'no'; every one of the %d claimed violations was "
                               "examined on its own crop and refuted" % offered)
    if im is not None:
        pass
    if transcript is not None:
        transcript.append(
            ("(reverse sweep)",
             "DEGRADED EXIT: the check never reached a terminal 'no' (%s), but every one of the "
             "%d violations it claimed was bought a per-crop vet read and REFUTED on its own "
             "magnified crop, and nothing ever joined the set. That is adjudicated evidence of "
             "cleanliness rather than incapacity, so the empty set is certified and marked "
             "degraded instead of the whole check being refused. The whole-frame count read (%s) "
             "is recorded as impeached by those adjudications, never silently dropped."
             % (why, offered, n_count)))
    return True


def exhaustive_sweep(im, boxes, tdesc, workdir, transcript, evidence=None,
                     cap=_SWEEP_TRY_CAP, thr=_DEDUPE_IOU,
                     reverse=False, exempt=None):
    kept = dedupe_boxes(_legal_boxes(boxes), thr)
    info = {"enabled": True, "complete": False, "tries": [], "n_start": len(kept),
            "n_added": 0, "n_final": len(kept),
            "terminal_answer": None, "count_check": None}
    n_count, _craws = _sweep_count_read(im, tdesc, workdir, transcript)
    info["count_check"] = n_count
    directed = False
    deficit_probed = False
    quad_used = 0
    stall = 0
    cov_streak = 0
    vetref_streak = 0
    for r in range(1, int(cap) + 1):
        ov = _draw("boxes", kept, im)
        p = os.path.join(workdir, "sweep_r%d.png" % r)
        p = _emit_png(ov, p)
        if evidence is not None:
            evidence.append(p)
        rrec = {"try": r, "n_before": len(kept), "offered": 0, "vetoed": 0, "added": 0}


        if directed and n_count is not None:
            q = SWEEP_DIRECTED_Q % (n_count, tdesc, len(kept), tdesc, tdesc)
        else:
            q = SWEEP_RESIDUAL_Q % (len(kept), tdesc, tdesc, tdesc, tdesc)
        raw = _ask(p, q, think=1024)
        if transcript is not None:
            transcript.append(("%s [sweep try %d]" % (q, r), raw))
        if _sweep_all_boxed(raw):
            if n_count is not None and n_count > len(kept) + _SWEEP_COUNT_SLACK \
                    and "count_recount" not in info:
                n2, _r2 = _sweep_count_read(im, tdesc, workdir, transcript, offset=3)
                info["count_recount"] = n2
                if n2 is not None:
                    n_count = min(n_count, n2)
                    info["count_check_final"] = n_count
            if n_count is not None and n_count > len(kept) + _SWEEP_COUNT_SLACK:
                rrec["answer"] = None if raw is None else str(raw)[:120]
                rrec["count_contradiction"] = {"count_read": n_count, "n_boxed": len(kept)}
                if quad_used < _SWEEP_QUAD_MAX:
                    quad_used += 1
                    qadd, all_no, qrec = _sweep_quadrant_pass(
                        im, kept, tdesc, workdir, transcript, evidence, "r%d" % r, thr,
                        reverse=reverse, exempt=exempt)
                    rrec["quadrant"] = qrec
                    info["tries"].append(rrec)
                    if qadd == 0 and all_no:
                        info["complete"] = True
                        info["certificate"] = "quadrant_no"
                        info["count_impeached"] = n_count
                        info["terminal_answer"] = "no (all four quarters, region-wise)"
                        if transcript is not None:
                            transcript.append(("(sweep)",
                                               "all four quarters answered no and added "
                                               "nothing -> completeness certified by region "
                                               "evidence with %d boxes (whole-frame count "
                                               "read ~%s impeached, recorded)"
                                               % (len(kept), n_count)))
                        break
                    if qadd > 0:
                        stall = 0
                        directed = True
                        continue
                else:
                    info["tries"].append(rrec)
                directed = True
                stall += 1
                if transcript is not None:
                    transcript.append(("(sweep)",
                                       "try %d: 'all boxed' at %d boxes vs count read ~%d "
                                       "-- unresolved, next try asks the DIRECTED deficit "
                                       "question" % (r, len(kept), n_count)))
                if stall >= _SWEEP_STALL + 1:
                    if not _stall_partial_consensus(
                            info, kept, n_count,
                            "count contradiction unresolved", im=im, rnd=r,
                            transcript=transcript) \
                            and not (reverse and _revsweep_adjudicated_exit(
                                info, kept, n_count, "count contradiction unresolved",
                                im=im, rnd=r, transcript=transcript)):
                        if transcript is not None:
                            transcript.append(("(sweep)",
                                               "the contradiction would not resolve (no region "
                                               "evidence, no additions) -> the completeness check "
                                               "cannot certify this set, so the read is refused"))
                    break
                continue
            if ((not deficit_probed and n_count is not None and n_count > len(kept))):
                deficit_probed = True
                n_before_probe = len(kept)
                info["deficit_probe"] = {"count_read": n_count, "n_boxed": n_before_probe}
                if transcript is not None:
                    transcript.append(("(sweep)",
                                       completeness_policy.deficit_probe_note(n_count, n_before_probe)))
                qd = SWEEP_DIRECTED_Q % (n_count, tdesc, len(kept), tdesc, tdesc)
                rawd = _ask(p, qd, think=1024)
                if transcript is not None:
                    transcript.append(("%s [recall deficit probe, try %d]" % (qd, r), rawd))
                dadd = 0
                for bi, b in enumerate([x for x in _legal_boxes(_parse("boxes", rawd) or [])
                                        if not _sweep_giant(x, kept)]):
                    if any(_iou01k(b, k) >= thr for k in kept) or _covered_by(b, kept):
                        continue
                    idb = "sweep.deficit.%d" % (bi + 1)
                    okd, _ad = _sweep_vet_box(im, b, tdesc, workdir, "def_b%d" % (bi + 1),
                                              transcript, exempt=exempt)
                    if okd:
                        kept, nadd = admit_to_kept(kept, [b], thr, "recall deficit probe",
                                                   transcript, info)
                        dadd += nadd
                info["deficit_probe"]["added"] = dadd
                if transcript is not None:
                    transcript.append(("(sweep)",
                                       completeness_policy.deficit_result_note(n_count, n_before_probe,
                                                                     dadd)))
                if dadd:
                    rrec["answer"] = None if raw is None else str(raw)[:120]
                    rrec["deficit_probe_added"] = dadd
                    info["tries"].append(rrec)
                    stall = 0
                    continue
            if empty_quad_due(reverse, kept, quad_used, info, n_count):
                quad_used += 1
                qadd, qrec = _empty_quad_confirm(
                    im, kept, tdesc, workdir, transcript, evidence, thr, exempt,
                    "no+count_consistent", r, n_count)
                info["empty_quadrant_confirm"] = qrec
                if qadd:
                    rrec["answer"] = None if raw is None else str(raw)[:120]
                    rrec["empty_quadrant_added"] = qadd
                    info["tries"].append(rrec)
                    stall = 0
                    if transcript is not None:
                        transcript.append(
                            ("(reverse sweep)",
                             "the quarter-by-quarter pass found %d thing(s) the whole-frame ask "
                             "reported as absent. The absence claim is withdrawn for this try "
                             "and the check continues on the grown set." % qadd))
                    continue
            info["complete"] = True
            info["certificate"] = "no+count_consistent"
            info["terminal_answer"] = None if raw is None else str(raw)[:200]
            rrec["answer"] = info["terminal_answer"]
            info["tries"].append(rrec)
            if transcript is not None:
                transcript.append(("(sweep)",
                                   "try %d: the reader answered that every %s is boxed "
                                   "(consistent with the independent count read %s) -> "
                                   "completeness certified with %d boxes"
                                   % (r, tdesc, n_count, len(kept))))
            break
        cand = [b for b in _legal_boxes(_parse("boxes", raw) or [])
                if not _sweep_giant(b, kept)]
        rrec["offered"] = len(cand)
        added = 0
        n_covered = 0
        for bi, b in enumerate(cand):
            if any(_iou01k(b, k) >= thr for k in kept):
                continue
            if _covered_by(b, kept):
                n_covered += 1
                continue
            idb = "sweep.r%d.%d" % (r, bi + 1)
            ok, _a = _sweep_vet_box(im, b, tdesc, workdir, "r%d_b%d" % (r, bi + 1), transcript)
            if ok:
                kept, nadd = admit_to_kept(kept, [b], thr, "whole-frame sweep try %d" % r,
                                           transcript, info)
                added += nadd
            else:
                rrec["vetoed"] += 1
                if _a is None or not str(_a).strip():
                    rrec["vet_silent"] = rrec.get("vet_silent", 0) + 1
        rrec["added"] = added
        covered_only = (added == 0 and rrec["vetoed"] == 0 and n_covered > 0)
        cov_streak = cov_streak + 1 if covered_only else 0
        vetref_only = (added == 0 and rrec["vetoed"] > 0 and cand
                       and not rrec.get("vet_silent"))
        vetref_streak = vetref_streak + 1 if vetref_only else 0
        if n_covered:
            rrec["covered_skipped"] = n_covered
            if transcript is not None:
                transcript.append(("(sweep)",
                                   "try %d: %d offered box(es) lie inside already-kept boxes "
                                   "-> covered-content fragments, skipped without a read"
                                   % (r, n_covered)))
        info["tries"].append(rrec)
        if added == 0:
            stall += 1
            if cov_streak >= 2 and (n_count is None or
                                    n_count <= len(kept) + _SWEEP_COUNT_SLACK):
                info["complete"] = True
                info["certificate"] = "covered_exhaustion+count_consistent"
                info["terminal_answer"] = ("every offered box lies inside kept boxes, "
                                           "two tries running")
                if transcript is not None:
                    transcript.append(("(sweep)",
                                       "completeness certified by covered exhaustion: %d boxes,"
                                       " count read %s agrees" % (len(kept), n_count)))
                break
            if (reverse and vetref_streak >= 2):
                if empty_quad_due(reverse, kept, quad_used, info, n_count):
                    quad_used += 1
                    qadd, qrec = _empty_quad_confirm(
                        im, kept, tdesc, workdir, transcript, evidence, thr, exempt,
                        "vet_refuted_exhaustion", r, n_count)
                    info["empty_quadrant_confirm"] = qrec
                    if qadd:
                        stall = 0
                        vetref_streak = 0
                        if transcript is not None:
                            transcript.append(
                                ("(reverse sweep)",
                                 "the quarter-by-quarter pass found %d thing(s) the whole-frame "
                                 "proposal never offered. The vet refuted the wrong rectangles, "
                                 "not the picture -- the absence claim is withdrawn and the check "
                                 "continues on the grown set." % qadd))
                        continue
                info["complete"] = True
                info["certificate"] = "vet_refuted_exhaustion"
                if n_count is not None and n_count > len(kept) + _SWEEP_COUNT_SLACK:
                    info["count_impeached"] = n_count
                info["terminal_answer"] = ("every claimed violation was examined on its own "
                                           "crop and refuted, two tries running")
                if transcript is not None:
                    transcript.append(("(sweep)",
                                       "reverse sweep certified by vet-refuted exhaustion: "
                                       "%d tries of claims, every one rejected on its own "
                                       "magnified crop, nothing joined (count read %s "
                                       "recorded%s)"
                                       % (r, n_count,
                                          ", impeached by the per-crop adjudications"
                                          if "count_impeached" in info else "")))
                break
            if stall >= _SWEEP_STALL:
                if quad_used < _SWEEP_QUAD_MAX:
                    quad_used += 1
                    qadd, all_no, qrec = _sweep_quadrant_pass(
                        im, kept, tdesc, workdir, transcript, evidence, "stall%d" % r, thr,
                        reverse=reverse)
                    info["tries"].append({"try": r, "quadrant_last_resort": qrec})
                    if qadd == 0 and all_no:
                        info["complete"] = True
                        info["certificate"] = "quadrant_no"
                        if n_count is not None and n_count > len(kept) + _SWEEP_COUNT_SLACK:
                            info["count_impeached"] = n_count
                        info["terminal_answer"] = "no (all four quarters, region-wise)"
                        if transcript is not None:
                            transcript.append(("(sweep)",
                                               "stall resolved by region evidence: all four "
                                               "quarters answered no -> completeness certified "
                                               "with %d boxes" % len(kept)))
                        break
                    if qadd > 0:
                        stall = 0
                        continue
                if not _stall_partial_consensus(
                        info, kept, n_count,
                        "%d consecutive tries claimed a miss that yielded no vetted box"
                        % stall, im=im, rnd=r, transcript=transcript) \
                        and not (reverse and _revsweep_adjudicated_exit(
                            info, kept, n_count,
                            "%d consecutive tries claimed a miss that yielded no vetted box"
                            % stall, im=im, rnd=r, transcript=transcript)):
                    if transcript is not None:
                        transcript.append(("(sweep)",
                                           "STALLED: %d consecutive tries claimed a miss but "
                                           "yielded no vetted box -> the completeness check cannot "
                                           "certify this set, so the read is refused rather than "
                                           "given a made-up number" % stall))
                break
        else:
            stall = 0
    else:
        if not _stall_partial_consensus(
                info, kept, n_count, "try cap %d reached without a terminal 'no'" % int(cap),
                im=im, rnd=int(cap), transcript=transcript) \
                and not (reverse and _revsweep_adjudicated_exit(
                    info, kept, n_count, "try cap %d reached without a terminal 'no'"
                    % int(cap), im=im, rnd=int(cap), transcript=transcript)):
            if transcript is not None:
                transcript.append(("(sweep)",
                                   "try cap %d reached without an explicit all-boxed answer -> "
                                   "completeness NOT certified" % int(cap)))
    info["n_added"] = len(kept) - info["n_start"]
    info["n_final"] = len(kept)
    return kept, info


_REVSWEEP_FOUND_CAP = "forbidden content found here"


_SHRUG_TOKENS = frozenset((
    "none", "nothing", "n/a", "na", "nil", "null", "no answer", "no value", "no reading",
    "not visible", "not legible", "not readable", "unreadable", "illegible", "unknown",
    "unclear", "cannot tell", "can't tell", "cannot read", "can't read", "cannot determine",
    "indeterminate", "no text", "blank", "empty", "-", "--", "---", "?", "??",
))

_AUTHORED_NONE_RE = re.compile(
    r"\b(?:answer|write|reply|say|respond|report|put|use|state|give)\b[^.?!]{0,80}?"
    r"[\"'`]?\b(none|nothing|blank|empty|n/?a|unknown)\b", re.I)


_ANSWER_SLOT = (r"(?=\s*(?:[.,;:!?)\]\"'`]|$|\bif\b|\bor\b|\band\b|\binstead\b|\bonly\b"
                r"|\bwhen\b|\bwhenever\b|\bfor\b|\bunless\b))")
_AUTHORED_NONE_STRICT_RE = re.compile(_AUTHORED_NONE_RE.pattern + _ANSWER_SLOT, re.I)


def authored_none(question):
    rx = (_AUTHORED_NONE_STRICT_RE)
    return bool(rx.search(str(question or "")))


def is_shrug(ans, question):
    if (ans is None or authored_none(question)):
        return False
    s = str(ans).strip().strip(".;,:!").strip().lower()
    return s in _SHRUG_TOKENS


def derive_exempt(ctx, step):
    ex = step.get("exempt")
    if ex:
        return list(ex)
    return []


def compose_exempt(tdesc, exempt):
    return tdesc


def sweep_vet_question(tdesc, exempt=None):
    return del_check_question(tdesc)


def del_check_question_full(desc):
    shipped = "an " if getattr(desc, "article", None) == "an" else "a "
    return _VET_CTX_Q % (question_rules.article_prefix(desc, shipped), desc)


def sweep_vet_question_full(tdesc, exempt=None):
    return del_check_question_full(tdesc)


def empty_quad_due(reverse, kept, quad_used, info, n_count=None):

    return bool(absence_quad_trigger(kept, n_count)) and _quad_budget_ok(reverse, quad_used, info)


def absence_quad_trigger(kept, n_count):
    if not kept:
        return "empty_set"
    try:
        if n_count is not None and int(n_count) > len(kept) + _SWEEP_COUNT_SLACK:
            return "count_deficit"
    except (TypeError, ValueError):
        log.debug("error ignored in absence_quad_trigger", exc_info=True)
        return None
    return None


def _quad_budget_ok(reverse, quad_used, info):
    return bool(False)


def _empty_quad_confirm(im, kept, tdesc, workdir, transcript, evidence, thr, exempt, at, r,
                        n_count):
    trig, n_kept0 = absence_quad_trigger(kept, n_count), len(kept)
    if transcript is not None:
        transcript.append(
            ("(reverse sweep)",
             "ABSENCE CONFIRMATION (at the `%s` exit): the check is about to publish "
             "an absence of %s off %d confirmed box(es), while its own independent count read "
             "said %s (trigger: %s). Before an absence is published the four quarters are each "
             "asked their own question -- refuting the rectangles the locator DID offer proves "
             "nothing about the object it never offered, and a certificate may overrule the "
             "check's own count only if it has region evidence."
             % (at, tdesc, n_kept0, n_count, trig)))
    qadd, qall_no, qrec = _sweep_quadrant_pass(
        im, kept, tdesc, workdir, transcript, evidence, "empty_%s_r%d" % (at[:12], r), thr,
        reverse=True, exempt=exempt)
    qrec["all_no"] = bool(qall_no)
    qrec["at_certificate"] = at
    qrec["count_check_at_exit"] = n_count
    qrec["trigger"] = trig
    qrec["n_kept_at_exit"] = n_kept0
    return qadd, qrec


def absent_ok_on(v):
    return str(v if v is not None else "").strip().lower() in ("1", "true", "yes", "on")


def reverse_sweep_read(im, tdesc, workdir, transcript, evidence, allow=0,
                       nom_info=None, nom_sheets=None, exempt=None):
    try:
        allow_n = max(0, int(allow or 0))
    except (TypeError, ValueError):
        log.debug("error ignored in reverse_sweep_read", exc_info=True)
        allow_n = 0
    transcript.append(("(reverse sweep)",
                       "absence read: the completeness check starts from "
                       "ZERO boxes, so try 1 is the residual ask itself; an empty vetted set "
                       "is a LEGAL answer and `clean` = (confirmed <= allow %d)" % allow_n))
    kept, info = exhaustive_sweep(im, [], tdesc, workdir, transcript, evidence,
                                  reverse=True, exempt=exempt)
    info["reverse_sweep"] = True
    n = len(kept)
    base = {"sweep": info, "read_craft": "reverse_sweep_basic", "absent_ok": True,
            "allow": allow_n, "n_confirmed": n, "transcript": transcript,
            "box_proposal": nom_info, "box_proposal_evidence": nom_sheets}
    if not info.get("complete"):
        transcript.append(("(reverse sweep stop)",
                           "the completeness check could not reach a terminal 'no' -> honest "
                           "refusal, never a published 'nothing here' off a reader who still claims a miss"))
        base.update({"geometry": None, "confirmed": False, "refused": True, "clean": None,
                     "tries": len(info.get("tries") or []), "evidence": evidence,
                     "overlay_img": None, "iteration_imgs": evidence,
                     "refusal": "reverse_sweep_incomplete"})
        return base
    clean = (n <= allow_n)
    if (not clean and info.get("degraded_exit")):
        _cert = info.get("certificate")
        transcript.append(("(reverse sweep stop)",
                           "DEGRADED EXIT MAY NOT CONVICT: the completeness check never reached a "
                           "terminal 'no' (certificate %r, %s) and would have published a "
                           "conviction off %d vetted box(es). anything unproven "
                           "abstains, never convicts -- so this check is REFUSED, not fired. A "
                           "degraded certificate is still allowed to certify a CLEAN set; it is "
                           "the positive claim that needs a complete check."
                           % (_cert, info.get("degraded_reason"), n)))
        base.update({"geometry": None, "confirmed": False, "refused": True, "clean": None,
                     "tries": len(info.get("tries") or []), "evidence": evidence,
                     "overlay_img": None, "iteration_imgs": evidence,
                     "refusal": "degraded_exit_conviction_barred",
                     "degraded_exit_barred": {"certificate": _cert,
                                              "degraded_reason": info.get("degraded_reason"),
                                              "n_confirmed": n, "allow": allow_n}})
        return base
    if n:
        pass
    ov = _draw("boxes", kept, im) if n else im.copy()
    full = os.path.join(workdir, "confirmed.png")
    full = _emit_png(ov, full)
    evidence.append(full)
    transcript.append(("(reverse sweep verdict)",
                       "%d vetted %s survived the sweep (allow %d) -> %s"
                       % (n, tdesc, allow_n, "clean" if clean else _REVSWEEP_FOUND_CAP)))
    base.update({"geometry": kept, "confirmed": True, "refused": False,
                 "clean": ("yes" if clean else "no"),
                 "tries": len(info.get("tries") or []), "evidence": evidence,
                 "overlay_img": full, "iteration_imgs": evidence[:-1]})
    return base


_TIGHT_EDGES = (("top", 0), ("left", 1), ("bottom", 2), ("right", 3))
_TIGHT_RELOCATE_Q = (
    'This is a cut-out picture. Somewhere in it there is %s%s. Give the box that just contains the '
    'whole %s and nothing more -- its edges should sit exactly on the outermost edge of the %s, '
    'not on the edge of this picture. Reply with ONLY a JSON object in exactly this form, for '
    'example: {"box_2d": [12, 34, 567, 890]} . The four numbers are, in order, the top, the left, '
    'the bottom and the right of the box, each running from 0 at the top (or left) edge of this '
    'picture to 1000 at the bottom (or right) edge. Give your own four numbers, no other text.')
_TIGHT_EDGE_Q = (
    'This is a cut-out picture showing %s%s. Look at the %s edge of the picture and choose the one '
    'statement that is true:\n'
    '(a) there is empty background between the %s and the %s edge -- it does not reach that edge;\n'
    '(b) the %s reaches the %s edge and is cut off by it, so part of it is outside the picture.\n'
    'Answer with the single letter a or b only.')


_SINGULAR_CONTAIN = 0.98
_SINGULAR_MATCH_IOU = 0.70
_SINGULAR_MARGIN = 0.25


def _singular_tie_break(offered, certified, expected_n):
    try:
        want = int(expected_n)
    except (TypeError, ValueError):
        log.debug("error ignored in _singular_tie_break", exc_info=True)
        return None
    if not certified or not offered or len(certified) != want or len(offered) <= want:
        return None
    used = set()
    for c in certified:
        best, second, bi = -1.0, -1.0, None
        for i, b in enumerate(offered):
            if i in used:
                continue
            v = _iou01k(c, b)
            if v > best or (v == best and bi is not None
                            and [float(x) for x in list(b)[:4]]
                            < [float(x) for x in list(offered[bi])[:4]]):
                if bi is not None and best > second:
                    second = best
                best, bi = v, i
            elif v > second:
                second = v
        if bi is None or best < _SINGULAR_MATCH_IOU \
                or (best - max(second, 0.0)) < _SINGULAR_MARGIN:
            return None
        b = offered[bi]
        if max(_inside_frac(c, b), _inside_frac(b, c)) < _SINGULAR_CONTAIN:
            return None
        used.add(bi)
    return [list(c) for c in certified]


_FIT_PT_TRIES = 3
_FIT_PT_TRIES_EP = 2
_FIT_PT_HALF = 0.08
_FIT_CIRCLE_GROW = 0.07
_FIT_RAY_JUMP_DEG = 8.0

_FIT_PT_QH = (
    'This is a cut-out picture. Somewhere in it is the %s. Choose the one statement that is '
    'true:\n(a) it lies in the LEFT half of this picture;\n(b) it lies in the RIGHT half of '
    'this picture.\nAnswer with the single letter a or b only.')
_FIT_PT_QV = (
    'This is a cut-out picture. Somewhere in it is the %s. Choose the one statement that is '
    'true:\n(a) it lies in the TOP half of this picture;\n(b) it lies in the BOTTOM half of '
    'this picture.\nAnswer with the single letter a or b only.')
_FIT_SIDE_Q = (
    'A contrasting-colour straight line is drawn on this image along the %s. Looking along the '
    'drawn line from its start to its end, choose the one statement that is true:\n'
    '(a) the %s is on the LEFT side of the line;\n(b) the %s is on the RIGHT side of the line.\n'
    'Answer with the single letter a or b only.')


def _fit_ask_ab(img, q, transcript, label, escalate=True):
    votes = []
    a1 = _ask(img, q, think=0)
    votes.append(a1)
    pick = _ab_pick(a1)
    if pick == "B" and escalate:
        for k in (1, 2):
            votes.append(_ask(img, read_policy.paraphrase(q, k), think=0))
        picks = [_ab_pick(v) for v in votes]
        pick = "B" if picks.count("B") > picks.count("A") else ("A" if picks.count("A") else None)
    if transcript is not None:
        transcript.append(("%s [%s]" % (q, label),
                           "%s -> %s" % ("/".join(str(v) for v in votes), pick or "?")))
    return pick, votes


def fit_point_geom(im, pt01k, tdesc, workdir, transcript, tag,
                   tries=_FIT_PT_TRIES, half_frac=_FIT_PT_HALF):
    W, H = im.size
    y, x = float(pt01k[0]) * H / 1000.0, float(pt01k[1]) * W / 1000.0
    x0_, y0_ = x, y
    rep = {"enabled": True, "reads": 0, "tries": 0, "moved_px": 0.0}
    half = half_frac * max(W, H)
    for r in range(int(tries)):
        cx0, cy0 = max(0.0, x - half), max(0.0, y - half)
        cx1, cy1 = min(float(W), x + half), min(float(H), y + half)
        if cx1 - cx0 < 24 or cy1 - cy0 < 24:
            break
        crop = magnify_crop(im.crop((int(cx0), int(cy0), int(cx1), int(cy1))))
        p = os.path.join(workdir, "fit_pt_%s_r%d.png" % (tag, r))
        p = _emit_png(crop, p)
        ph, vh = _fit_ask_ab(p, _FIT_PT_QH % tdesc, transcript,
                             "fit_point %s try %d horizontal" % (tag, r + 1), escalate=False)
        pv, vv = _fit_ask_ab(p, _FIT_PT_QV % tdesc, transcript,
                             "fit_point %s try %d vertical" % (tag, r + 1), escalate=False)
        rep["reads"] += 2
        rep["tries"] = r + 1
        if ph == "A":
            x = cx0 + (cx1 - cx0) * 0.25
        elif ph == "B":
            x = cx0 + (cx1 - cx0) * 0.75
        if pv == "A":
            y = cy0 + (cy1 - cy0) * 0.25
        elif pv == "B":
            y = cy0 + (cy1 - cy0) * 0.75
        half /= 2.0
    rep["moved_px"] = round(((x - x0_) ** 2 + (y - y0_) ** 2) ** 0.5, 1)
    new = [_clamp01k(y * 1000.0 / H), _clamp01k(x * 1000.0 / W)]
    return new, rep


def _fit_point_gate(im, pt01k, tdesc, workdir, transcript, tag, votes=3):
    W, H = im.size
    ov = _draw("point", pt01k, im)
    sheet = _sheet(im, ov, _region("point", pt01k, W, H),
                   os.path.join(workdir, "fit_pt_%s_verify.png" % tag))
    q = ("The RIGHT panel has a contrasting-colour ring marker drawn on the image; the "
         "LEFT panel shows the same region WITHOUT the drawing. That marker is meant to "
         "mark the %s. Is the marked spot -- the middle of that little ring -- sitting "
         "ON the %s? Judge only WHERE the spot sits: the marker's size and shape do not "
         "matter and it does not have to cover or trace the target. yes/no" % (tdesc, tdesc))
    ok, vraw = _gate(sheet, q, votes)
    if transcript is not None:
        transcript.append(("%s [fit_point %s re-gate]" % (q, tag),
                           "%s -> %s" % ("/".join(str(v) for v in vraw), "yes" if ok else "no")))
    return ok


def fit_point_confirmed(im, geom, tdesc, workdir, transcript, tag="p"):
    new, rep = fit_point_geom(im, geom, tdesc, workdir, transcript, tag)
    W, H = im.size
    if rep["moved_px"] < 0.003 * max(W, H):
        rep["verdict"] = "unchanged"
        return list(geom), rep
    rep["reads"] += 3
    if _fit_point_gate(im, new, tdesc, workdir, transcript, tag):
        rep["verdict"] = "adopted"
        return new, rep
    rep["verdict"] = "reverted"
    if transcript is not None:
        transcript.append(("(fit_point %s)" % tag,
                           "refined point failed the re-gate -- pre-craft geometry restored "
                           "(reverting is the shipped behaviour, never a new number)"))
    return list(geom), rep


def circle_relocation_legal(prev_cyxr, next_box01k, r_lo=0.2, r_hi=2.0, aspect_max=1.6):
    ocy, ocx, orr = [float(v) for v in prev_cyxr[:3]]
    y0, x0, y1, x1 = [float(v) for v in next_box01k[:4]]
    ncy, ncx = (y0 + y1) / 2.0, (x0 + x1) / 2.0
    nr = (abs(y1 - y0) + abs(x1 - x0)) / 4.0
    if ((ncy - ocy) ** 2 + (ncx - ocx) ** 2) ** 0.5 > max(orr, 1e-6):
        return False, "the relocated centre falls outside the old circle (jump guard)"
    if not (r_lo * orr <= nr <= r_hi * orr):
        return False, "the relocated radius changed by %.2fx" % (nr / max(orr, 1e-6))
    w, h = max(abs(x1 - x0), 1e-6), max(abs(y1 - y0), 1e-6)
    if max(w / h, h / w) > aspect_max:
        return False, "the relocated tight box is not square enough to be a disc (%.2f:1)" \
            % max(w / h, h / w)
    return True, None


def fit_circle_geom(im, geom, tdesc, workdir, transcript, tag="c"):
    W, H = im.size
    cy, cx, r = [float(v) for v in geom[:3]]
    rep = {"enabled": True, "reads": 0, "relocate": "skipped", "edges": {}, "pass": True,
           "before": [round(cy, 1), round(cx, 1), round(r, 1)]}
    prev_box = [cy - r, cx - r, cy + r, cx + r]
    try:
        x0, y0, x1, y1 = crop_pad_px(prev_box, W, H, 0.35)
        if x1 - x0 >= 24 and y1 - y0 >= 24:
            crop = magnify_crop(im.crop((x0, y0, x1, y1)))
            p = os.path.join(workdir, "fit_circ_%s_reloc.png" % tag)
            p = _emit_png(crop, p)
            _reloc_q = _TIGHT_RELOCATE_Q % (question_rules.a_prefix(tdesc),
                                            tdesc, tdesc, tdesc)
            raw = _ask(p, _reloc_q, think=256)
            rep["reads"] += 1
            if transcript is not None:
                transcript.append((_reloc_q + " [fit_circle relocation]", raw))
            bs = _parse("boxes", raw or "")
            if bs and geom_legal("boxes", bs[:1])[0]:
                by0, bx0, by1, bx1 = [float(v) for v in bs[0][:4]]
                cw, ch = float(x1 - x0), float(y1 - y0)
                nb = [(y0 + by0 * ch / 1000.0) * 1000.0 / H,
                      (x0 + bx0 * cw / 1000.0) * 1000.0 / W,
                      (y0 + by1 * ch / 1000.0) * 1000.0 / H,
                      (x0 + bx1 * cw / 1000.0) * 1000.0 / W]
                ok, why = circle_relocation_legal([cy, cx, r], nb)
                if ok:
                    cy, cx = (nb[0] + nb[2]) / 2.0, (nb[1] + nb[3]) / 2.0
                    r = (abs(nb[2] - nb[0]) + abs(nb[3] - nb[1])) / 4.0
                    rep["relocate"] = "adopted"
                else:
                    rep["relocate"] = "rejected"
                    rep["relocate_note"] = why
            else:
                rep["relocate"] = "unusable"
    except Exception as e:
        log.debug("error ignored in fit_circle_geom", exc_info=True)
        rep["relocate"] = "error"
        rep["relocate_note"] = "%s: %s" % (type(e).__name__, e)

    def _square_crop():
        rpx = r * min(W, H) / 1000.0
        pxc, pyc = cx * W / 1000.0, cy * H / 1000.0
        sq = (int(round(pxc - rpx)), int(round(pyc - rpx)),
              int(round(pxc + rpx)) + 1, int(round(pyc + rpx)) + 1)
        sq = (max(0, sq[0]), max(0, sq[1]), min(W, sq[2]), min(H, sq[3]))
        if sq[2] - sq[0] < 8 or sq[3] - sq[1] < 8:
            return None
        return magnify_crop(im.crop(sq))

    def _edge_pass(names, tagx):
        crop = _square_crop()
        if crop is None:
            return {n: None for n in names}
        p = os.path.join(workdir, "fit_circ_%s_%s.png" % (tag, tagx))
        p = _emit_png(crop, p)
        out = {}
        for name in names:
            pick, votes = _fit_ask_ab(
                p, _TIGHT_EDGE_Q % (question_rules.a_prefix(tdesc), tdesc, name,
                                    tdesc, name, tdesc, name), transcript,
                "fit_circle %s edge %s" % (tag, name))
            rep["reads"] += len(votes)
            out[name] = None if pick is None else (pick == "B")
        return out

    names = [n for n, _ in _TIGHT_EDGES]
    cuts = _edge_pass(names, "edges")
    rep["edges"] = dict(cuts)
    bad = [n for n, v in cuts.items() if v is True]
    if bad:
        r *= (1.0 + _FIT_CIRCLE_GROW)
        rep["backoff"] = list(bad)
        re_cuts = _edge_pass(bad, "edges_bk")
        rep["edges_after_backoff"] = dict(re_cuts)
        still = [n for n in bad if re_cuts.get(n) is True]
        if still:
            rep["pass"] = False
            rep["still_cut"] = still
    rep["after"] = [round(cy, 1), round(cx, 1), round(r, 1)]
    if transcript is not None:
        transcript.append(("(fit_circle %s)" % tag,
                           "relocate=%s, edges=%s -> %s" %
                           (rep["relocate"],
                            ", ".join("%s:%s" % (n, {True: "cut", False: "clear", None: "?"}[v])
                                      for n, v in cuts.items()),
                            "pass" if rep["pass"] else
                            "FAIL (still cut: %s)" % ", ".join(rep.get("still_cut", [])))))
    return [_clamp01k(cy), _clamp01k(cx), min(_COORD_MAX, max(0.1, r))], rep


FIT_CIRCLE_REFUSAL_NOTE = (
    "the fit-craft radius vote found the bright core still cut by the circle's own bounding square after the one allowed outward retreat: this circle's radius IS the scoring tolerance, so the read REFUSES rather than publish a boundary it cannot vouch for")


def _ray_deg(g):
    import math as _m
    return _m.degrees(_m.atan2(float(g[2]) - float(g[0]), float(g[3]) - float(g[1])))


def fit_ray_line(im, geom, kind, target, tdesc, workdir, transcript,
                 side_anchor=None, votes=3):
    W, H = im.size
    rep = {"enabled": True, "reads": 0, "verdict": "unchanged"}
    if kind == "ray" and isinstance(target, (list, tuple)) and len(target) >= 2:
        d_end0, d_end1 = ("the exact %s" % target[1], "the exact %s" % target[0])
    else:
        d_end0 = "exact TAIL (back end) of the %s" % tdesc
        d_end1 = "exact TIP (front end) of the %s" % tdesc
    length_frac = max(abs(float(geom[3]) - float(geom[1])) / 1000.0,
                      abs(float(geom[2]) - float(geom[0])) / 1000.0)
    half = min(0.06, max(0.03, 0.15 * length_frac))
    p0, r0 = fit_point_geom(im, [geom[0], geom[1]], d_end0, workdir, transcript, "e0",
                            tries=_FIT_PT_TRIES_EP, half_frac=half)
    p1, r1 = fit_point_geom(im, [geom[2], geom[3]], d_end1, workdir, transcript, "e1",
                            tries=_FIT_PT_TRIES_EP, half_frac=half)
    rep["reads"] += r0["reads"] + r1["reads"]
    new = [p0[0], p0[1], p1[0], p1[1]]
    rep["end_moved_px"] = [r0["moved_px"], r1["moved_px"]]
    if geom_legal("line", new)[0] is False or max(r0["moved_px"], r1["moved_px"]) \
            < 0.003 * max(W, H):
        return list(geom), rep
    rep["deg_before"] = round(_ray_deg(geom), 1)
    rep["deg_after"] = round(_ray_deg(new), 1)
    swing = abs((rep["deg_after"] - rep["deg_before"] + 180.0) % 360.0 - 180.0)
    rep["swing_deg"] = round(swing, 1)
    if swing > _FIT_RAY_JUMP_DEG:
        rep["verdict"] = "reverted"
        if transcript is not None:
            transcript.append(("(fit_%s)" % kind,
                               "endpoint refinement swung the line %.1f deg (> %.0f deg jump "
                               "guard) -- pre-craft geometry restored; the craft refines, it "
                               "never re-aims" % (swing, _FIT_RAY_JUMP_DEG)))
        return list(geom), rep
    ov = _draw("line", new, im)
    sheet = _sheet(im, ov, (0, 0, W, H), os.path.join(workdir, "fit_line_verify.png"))
    if kind == "ray":
        q = ("The RIGHT panel has a contrasting-colour straight line drawn on the image; the "
             "LEFT panel shows the same picture without it. That line is meant to run along "
             "the %s. Does the drawn line lie along it and point the same way? Judge the "
             "DIRECTION and the alignment only -- a line that is somewhat longer or shorter "
             "than the thing it follows is fine. yes/no" % tdesc)
    else:
        q = ("The RIGHT panel has a contrasting-colour line drawn to trace the %s; the LEFT panel "
             "shows the same region WITHOUT the drawing. Comparing both: does the red drawing "
             "trace the %s accurately (right position, right direction, right extent)? "
             "yes/no" % (tdesc, tdesc))
    ok, vraw = _gate(sheet, q, votes)
    rep["reads"] += votes
    if transcript is not None:
        transcript.append(("%s [fit_%s re-gate]" % (q, kind),
                           "%s -> %s" % ("/".join(str(v) for v in vraw), "yes" if ok else "no")))
    if not ok:
        rep["verdict"] = "reverted"
        if transcript is not None:
            transcript.append(("(fit_%s)" % kind,
                               "refined endpoints failed the re-gate (swing %.1f deg) -- "
                               "pre-craft geometry restored" % swing))
        return list(geom), rep
    if side_anchor:
        pa, _ra = fit_point_geom(im, [(new[0] + new[2]) / 2.0, (new[1] + new[3]) / 2.0],
                                 "centre of the %s" % side_anchor, workdir, transcript,
                                 "anchor", tries=1, half_frac=0.25)
        rep["reads"] += _ra["reads"]
        ovl = _draw("line", new, im)
        pl = os.path.join(workdir, "fit_line_side.png")
        pl = _emit_png(ovl, pl)
        pick, votes_raw = _fit_ask_ab(
            pl, _FIT_SIDE_Q % (tdesc, side_anchor, side_anchor), transcript,
            "fit_%s side self-check" % kind)
        rep["reads"] += len(votes_raw)
        ux, uy = (new[3] - new[1]) * W, (new[2] - new[0]) * H
        vx, vy = (pa[1] - new[1]) * W, (pa[0] - new[0]) * H
        geo_side = "A" if (ux * vy - uy * vx) > 0 else "B"
        rep["side_check"] = {"vlm": pick, "geometry": geo_side,
                             "agree": (pick == geo_side) if pick else None}
        if pick and pick != geo_side:
            rep["verdict"] = "reverted"
            if transcript is not None:
                transcript.append(("(fit_%s)" % kind,
                                   "side self-check disagrees with the drawn line's own "
                                   "geometry -- pre-craft geometry restored"))
            return list(geom), rep
    rep["verdict"] = "adopted"
    return new, rep


_ATOM_WHOLE_Q = (
    "The RIGHT panel has contrasting-colour rectangle(s) drawn on the image; the LEFT panel "
    "shows the same region without them. Each rectangle is meant to be an UPRIGHT BOUNDING BOX "
    "around %s%s. Look at what is INSIDE each rectangle. Is the WHOLE of the %s inside it, with "
    "no part of it left outside the rectangle? Extra room around it does not matter, and the "
    "rectangle's shape or angle does not matter -- answer only about whether all of the %s is "
    "inside. yes/no")
_ATOM_EMPTY_Q = (
    "The RIGHT panel has contrasting-colour rectangle(s) drawn on the image; the LEFT panel "
    "shows the same region without them. Is ANY of those rectangles EMPTY -- nothing but plain "
    "background inside it, no %s in it at all? Answer yes only if a rectangle really is empty. "
    "yes/no")
_ATOM_WRONG_Q = (
    "The RIGHT panel has contrasting-colour rectangle(s) drawn on the image; the LEFT panel "
    "shows the same region without them. Is ANY of those rectangles drawn around SOMETHING "
    "ELSE -- a different object that is not %s%s? Being a bit too big or a bit off-centre is "
    "NOT something else. Answer yes only if a rectangle is on a different thing. yes/no")


def purity_atomic_regate(sheet, tdesc, votes, transcript):
    rep = {"enabled": True, "atoms": []}

    def atom(label, q, want_yes):
        okq, vraw = _gate(sheet, q, votes)
        got = okq if want_yes else (not okq)
        rep["atoms"].append({"atom": label, "want": "yes" if want_yes else "no",
                             "votes": [None if v is None else str(v)[:24] for v in vraw],
                             "pass": bool(got)})
        if transcript is not None:
            transcript.append(
                ("%s [tight_purity atom: %s, majority of %d, want %s]"
                 % (q, label, votes, "yes" if want_yes else "no"),
                 "%s -> %s" % ("/".join(str(v) for v in vraw), "pass" if got else "fail")))
        return bool(got)

    ok = atom("whole_inside", _ATOM_WHOLE_Q % (question_rules.a_prefix(tdesc), tdesc,
                                               tdesc, tdesc), True)
    ok = atom("not_empty", _ATOM_EMPTY_Q % tdesc, False) and ok
    ok = atom("not_wrong_thing",
              _ATOM_WRONG_Q % (question_rules.a_prefix(tdesc), tdesc), False) and ok
    rep["pass"] = bool(ok)
    return bool(ok), rep


_OBJ_UNPARSEABLE = "output was not parseable JSON"


def grounded_read(image, kind, target, workdir, retries=3, votes=3, expected_n=None,
                  context=None, propose_boxes="vlm", metric_box=False,
                  tightness=None, layout=None, sort=None, fit_side_anchor=None, sweep=None,
                  absent_ok=None, allow=0, diagnostic=None, exempt=None):
    im = image if hasattr(image, "convert") else Image.open(image).convert("RGB")
    im = im.convert("RGB")
    os.makedirs(workdir, exist_ok=True)
    base = os.path.join(workdir, "src.png")
    base = _emit_png(im, base)
    W, H = im.size
    transcript, evidence = [], []
    objection = ""
    nom_diag = bool(diagnostic)
    nom = resolve_propose_boxes(propose_boxes, expected_n, diagnostic=nom_diag)
    nom_active = (nom != "vlm") and kind == "boxes"
    nom_done = False
    nom_info = {"mode": nom, "used": False}
    nom_sheets = []
    pending_geom = None
    purity_ok_geom = None
    purity_ok_try = None
    pt_cert_rep = None
    try:
        _exp_n = int(expected_n) if expected_n is not None else None
    except (TypeError, ValueError):
        log.debug("error ignored in grounded_read", exc_info=True)
        _exp_n = None
    ndesc = strip_leading_article(
        target if isinstance(target, str)
        else " / ".join(str(t) for t in (target or [])) or "object")
    if nom != "vlm" or str(propose_boxes or "vlm").strip().lower() != "vlm":
        transcript.append(("(box_proposal route)",
                           "propose_boxes=%s%s" % (nom, "" if kind == "boxes" else
                                              " (ignored: only the boxes primitive proposes)")))
    if absent_ok_on(absent_ok):
        if kind == "boxes":
            return reverse_sweep_read(im,
                                      compose_exempt(
                                          (target if isinstance(target, str) else ndesc), exempt),
                                      workdir, transcript, evidence, allow=allow,
                                      nom_info=nom_info, nom_sheets=nom_sheets,
                                      exempt=exempt)
        transcript.append(("(reverse sweep)",
                           "`absent_ok` is a BOXES-primitive parameter; primitive '%s' ignores "
                           "it and reads exactly as before" % kind))
    ask_img, cbox = base, (0, 0, W, H)
    ctx_budget, ctx_tag = 0, 0
    use_context = bool(context) and kind in ("boxes", "point", "circle", "line")
    if use_context:
        ctx_budget = 3
        ask_img, cbox, ctx_budget = _context_crop(base, im, context, workdir, W, H,
                                                  transcript, ctx_budget)
        ctx_tag = 3 - ctx_budget

    def map_back(pt_yx):
        cy, cx = pt_yx
        fx = cbox[0] + (cx / 1000.0) * (cbox[2] - cbox[0])
        fy = cbox[1] + (cy / 1000.0) * (cbox[3] - cbox[1])
        return [fy * 1000.0 / H, fx * 1000.0 / W]

    prev_ov = None
    prev_geom = None
    _last_ask = None
    _empty_tries = 0
    _shape_log = []

    def _recontext(why):
        nonlocal ask_img, cbox, ctx_budget, ctx_tag, prev_ov, prev_geom
        transcript.append(("(context invalidated)", why))
        if ctx_budget > 0:
            ask_img, cbox, ctx_budget = _context_crop(
                base, im, context, workdir, W, H, transcript, ctx_budget,
                objection=(CTX_TOO_TIGHT % context), tag=ctx_tag)
            ctx_tag += 1
        else:
            ask_img, cbox = base, (0, 0, W, H)
            transcript.append(("(context)", "context degraded to full frame -- no attempts left "
                                            "to widen the container"))
        prev_ov, prev_geom = None, None

    for rnd in range(retries):
        props = []
        raws = []
        ctx_suspect = False
        servo_turn = (prev_ov is not None and prev_geom is not None and rnd % 2 == 1)
        if servo_turn and redraw_forbidden(kind, prev_geom):
            servo_turn = False
            transcript.append(("(try %d servo skipped)" % (rnd + 1),
                               "%d boxes >= %d: the whole-set redraw servo is forbidden "
                               "(gate noise floor at high box counts) -- this try re-proposes "
                               "from scratch instead of redrawing the verified set"
                               % (len(prev_geom), _NO_REDRAW_N)))
        if pending_geom is not None:
            geom = pending_geom
            pending_geom = None
            transcript.append(("(try %d proposal)" % (rnd + 1),
                               "the diagnosis-repaired set (%d boxes) from the previous try"
                               % len(geom)))
        elif servo_turn:
            dk = "line" if kind == "ray" else kind
            desc = (tdesc if 'tdesc' in dir() else
                    (target if isinstance(target, str) else "pointer"))
            fmt = prim_json_fmt(dk, desc)
            _lead, _noun, _verb = redraw_opening(dk)
            qc = ("%s %s %s drawn on this image attempting to trace %s, but it is "
                  "not accurate: %s. Output the CORRECTED %s as STRICT JSON only: %s, coordinates "
                  "normalized 0-1000 of THIS image, so the drawing would fit exactly."
                  % (_lead, _noun, _verb, redraw_trace_target(desc),
                     objection or "slightly off", dk, fmt))
            raw = _ask(prev_ov, qc, think=1024)
            transcript.append((qc, raw))
            raws.append(raw)
            geom = _parse("line" if kind == "ray" else kind, raw)
            if geom is None:
                geom = prev_geom
        elif kind == "ray":
            tip_d, piv_d = target if isinstance(target, (tuple, list)) else (
                "tip of the %s" % target, "pivot/centre the %s rotates around" % target)
            qf = ('Locate the instrument FACE/DIAL that %s%s belongs to. Output STRICT '
                  'JSON only: {"box_2d":[ymin,xmin,ymax,xmax]} normalized 0-1000.'
                  % (question_rules.the_prefix(tip_d), tip_d))
            rf = _ask(base, qf, think=512)
            transcript.append((qf, rf))
            mf = re.search(r"\[\s*\d+[\s,]+\d+[\s,]+\d+[\s,]+\d+\s*\]", rf or "")
            crop_box = None
            if mf:
                try:
                    ymin, xmin, ymax, xmax = [float(v) for v in json.loads(mf.group(0))]
                    crop_box = (int(xmin * W / 1000), int(ymin * H / 1000),
                                int(xmax * W / 1000), int(ymax * H / 1000))
                except Exception:
                    log.debug("error ignored in grounded_read", exc_info=True)
                    crop_box = None
            if crop_box and crop_box[2] > crop_box[0] + 40 and crop_box[3] > crop_box[1] + 40:
                zoom = im.crop(crop_box)
                if min(zoom.size) < 700:
                    zoom = zoom.resize((zoom.width * 2, zoom.height * 2), Image.LANCZOS)
                zp = os.path.join(workdir, "zoom_r%d.png" % rnd)
                zp = _emit_png(zoom, zp)
                ask_img, zw, zh = zp, zoom.width, zoom.height
            else:
                ask_img, zw, zh = base, W, H
                crop_box = (0, 0, W, H)
                transcript.append(("(context)", "context degraded to full frame -- the evaluator "
                                                "face could not be boxed this try"))
            qa = ('Locate the exact %s. Output STRICT JSON only: {"point":[y,x]} '
                  'normalized 0-1000.%s' % (tip_d,
                  ("\nPrevious attempt rejected: %s." % objection) if objection else ""))
            qb = ('Locate the exact %s. Output STRICT JSON only: {"point":[y,x]} '
                  'normalized 0-1000.' % piv_d)
            ra, rb = _ask(ask_img, qa, think=1024), _ask(ask_img, qb, think=1024)
            transcript += [(qf, rf), (qa, ra), (qb, rb)]
            pa, pb = _parse("point", ra), _parse("point", rb)

            def back(pt):
                cy, cx = pt
                fx = crop_box[0] + (cx / 1000.0) * (crop_box[2] - crop_box[0])
                fy = crop_box[1] + (cy / 1000.0) * (crop_box[3] - crop_box[1])
                return [fy * 1000.0 / H, fx * 1000.0 / W]
            geom = None
            if pa and pb:
                A, B = back(pa), back(pb)
                geom = [B[0], B[1], A[0], A[1]]
        elif kind == "line" and rnd >= 1:
            qa = ('Locate the exact TIP (front end) of %s%s. Output STRICT JSON only: '
                  '{"point":[y,x]} normalized 0-1000.%s'
                  % (question_rules.the_prefix(target), target,
                     ("\nPrevious attempt rejected: %s." % objection) if objection else ""))
            qb = ('Locate the exact TAIL (back end) of %s%s. Output STRICT JSON only: '
                  '{"point":[y,x]} normalized 0-1000.'
                  % (question_rules.the_prefix(target), target))
            ra, rb = _ask(base, qa, think=1024), _ask(base, qb, think=1024)
            transcript += [(qa, ra), (qb, rb)]
            pa, pb = _parse("point", ra), _parse("point", rb)
            geom = [pb[0], pb[1], pa[0], pa[1]] if (pa and pb) else None
        else:
            q = ("Locate %s%s in this image. Output STRICT JSON only: %s, coordinates "
                 "normalized to 0-1000.%s" % (question_rules.the_prefix(target), target,
                                              prim_json_fmt(kind, target),
                                              ("\nYour previous attempt was rejected: %s. "
                                               "Draw it correctly this time." % objection)
                                              if objection else ""))
            if kind in ("circle", "point"):
                props = []
                for k3 in range(3):
                    r3 = _ask(ask_img, read_policy.paraphrase(q, k3), think=1024)
                    transcript.append((q if k3 == 0 else "(vote %d)" % (k3 + 1), r3))
                    raws.append(r3)
                    g3 = _parse(kind, r3)
                    ok3, why3 = geom_legal(kind, g3)
                    if g3 and ok3:
                        props.append(clamp_geom(kind, g3))
                    elif g3:
                        transcript.append(("(vote %d rejected)" % (k3 + 1), why3))
                        objection = why3
                if props:
                    def _d(a, b):
                        n = 2 if kind == "circle" else min(len(a), len(b))
                        return sum(abs(a[i] - b[i]) for i in range(n))
                    geom = min(props, key=lambda p: sum(_d(p, q) for q in props))
                else:
                    geom = None
            else:
                qa = q
                _last_ask = qa
                raw = _ask(ask_img, qa, think=1024)
                transcript.append((qa, raw))
                raws.append(raw)
                geom = _parse(kind, raw)
                if nom_active and not nom_done:
                    nom_done = True
                    nom_info["used"] = True
                    aim = im if ask_img == base else _load(ask_img)
                    vlm_set = _legal_boxes(_parse("boxes", raw) or [])
                    won, info = incremental_propose_boxes(aim, vlm_set, ndesc, workdir, transcript)
                    nom_info.update(info)
                    geom = won or None
            if geom is not None and ask_img != base:
                ff = _fill_frac(kind, geom)
                if ff and min(ff) >= _CTX_FILL_SUSPECT:
                    ctx_suspect = True
            if geom is not None and ask_img != base:
                def _to_frame(g):
                    if kind == "boxes":
                        return [map_back([b[0], b[1]]) + map_back([b[2], b[3]]) for b in g]
                    if kind == "point":
                        return map_back(g)
                    if kind == "circle":
                        c = map_back([g[0], g[1]])
                        scale = min(cbox[2] - cbox[0], cbox[3] - cbox[1]) / float(min(W, H))
                        return [c[0], c[1], g[2] * scale]
                    if kind == "line":
                        return map_back([g[0], g[1]]) + map_back([g[2], g[3]])
                    return g
                geom = _to_frame(geom)
                props = [_to_frame(p) for p in props]
        if geom is None:
            objection = _OBJ_UNPARSEABLE
            if placeholder_echoed(raws[-1] if raws else None):
                objection = ("the answer echoed the placeholder words instead of numbers. %s"
                             % CTX_FORMAT_OBJECTION)
                transcript.append(
                    ("(try %d: placeholder echo)" % (rnd + 1),
                     "the reader repeated the prompt's own placeholder words "
                     "(ymin/xmin/ymax/xmax) instead of writing coordinates. That is a WRITING "
                     "failure, not a seeing failure -- measured on this class, the echoed "
                     "coordinates were correct -- so the next try is asked for the format "
                     "explicitly, the same repair the container ask has always had."))
            nv = [r for r in raws if r and _NOT_VISIBLE.search(r)]
            if use_context and ask_img != base and nv:
                _recontext("asked inside the context crop the reader answered: %s"
                           % (str(nv[0])[:180]))
            continue
        ok_g, why_g = geom_legal(kind, geom)
        if not ok_g:
            transcript.append(("(try %d voided)" % (rnd + 1),
                               "%s -- proposal %s" % (why_g, json.dumps(geom))))
            objection = why_g
            props = [p for p in props if geom_legal(kind, p)[0]]
            continue
        geom = clamp_geom(kind, geom)
        props = [clamp_geom(kind, p) for p in props if geom_legal(kind, p)[0]]
        if layout and kind == "boxes":
            geom, flipped, lnote = layout_fix(geom, layout)
            if flipped:
                geom = clamp_geom(kind, geom)
                props = [layout_fix(p, layout)[0] for p in props]
                transcript.append(("(layout self-check)", lnote))
            if str(sort or "").strip().lower() == "reading_order":
                geom = sort_reading_order(geom, layout)[0]
        if kind == "boxes" and expected_n is not None and len(geom) != expected_n:
            _adopt = None
            if ((purity_ok_geom and _exp_n is not None and len(geom) > _exp_n and not sweep_on(sweep) and not metric_box and not fit_side_anchor)):
                _adopt = _singular_tie_break(geom, purity_ok_geom, _exp_n)
            if _adopt is not None:
                _rep = {"enabled": True, "expected_n": _exp_n, "offered_n": len(geom),
                        "certified_try": purity_ok_try, "adopted_try": rnd + 1,
                        "coverage_impeached_by": "expected_n=%d (authored spec cardinality)"
                                                 % _exp_n,
                        "rule": "highest-IoU one-to-one match against the set the shipped "
                                "tight_purity vote already passed; ties to the "
                                "lexicographically smallest box; nothing new proposed",
                        "offered_boxes": [[round(float(v), 1) for v in list(b)[:4]]
                                          for b in geom][:12]}
                _ov = _draw("boxes", _adopt, im)
                _full = os.path.join(workdir, "confirmed.png")
                _full = _emit_png(_ov, _full)
                evidence.append(_full)
                transcript.append(
                    ("(singular tie-break)",
                     "the correction step returned %d rectangles where the spec declares %d. The %d box(es) the shipped tight_purity vote confirmed in try %s are ALL still among them (highest-IoU one-to-one, >= %.2f), so the surplus is a fact about how many things the target PHRASE names, not a defect of the rectangle: the over-count is booked as diagnosis, the coverage vote is recorded as impeached by the spec's own cardinality, and the already-confirmed set stands unchanged. Nothing was proposed, moved or invented."
                     % (len(geom), _exp_n, _exp_n, purity_ok_try, _DEDUPE_IOU)))
                return {"geometry": _adopt, "confirmed": True, "refused": False,
                        "tries": rnd + 1, "evidence": evidence, "transcript": transcript,
                        "overlay_img": _full, "iteration_imgs": evidence[:-1],
                        "box_proposal": nom_info, "box_proposal_evidence": nom_sheets,
                        "degraded_exit": True, "plural_ambiguous_target": _rep}
            objection = "found %d boxes but the spec says %d" % (len(geom), expected_n)
            continue
        dkind = "line" if kind == "ray" else kind
        tdesc = strip_leading_article(
            target if isinstance(target, str)
            else "pointer from %s to %s" % (target[1], target[0]))
        cands = [geom]
        if kind in ("circle", "point") or (dkind == "boxes" and nom_active):
            for p in props:
                if p != geom and p not in cands:
                    cands.append(p)
        if dkind == "boxes":
            _upright = ("Each rectangle is meant to be an UPRIGHT BOUNDING BOX around %s%s -- an "
                        "upright rectangle that just contains it, so a tilted, round or irregular "
                        "object still gets an upright rectangle. Judge only enclosure, not the "
                        "rectangle's shape or angle." % (question_rules.one_prefix(tdesc), tdesc))
            gqs = [
                ("coverage",
                 "The RIGHT panel has contrasting-colour rectangle(s) drawn on the image; the LEFT "
                 "panel shows the same region without them. %s Look across the whole region: does "
                 "EVERY %s there have a rectangle on it, with none of them left unboxed? "
                 "yes/no" % (_upright, tdesc)),
                ("tight_purity",
                 "The RIGHT panel has contrasting-colour rectangle(s) drawn on the image; the LEFT "
                 "panel shows the same region without them. %s Does EVERY rectangle tightly enclose "
                 "%s%s -- the whole of it, with little extra? A little slack is fine, but answer "
                 "no if any rectangle is empty (only background inside), sits somewhere else, or is "
                 "drawn around something that is not %s%s. yes/no"
                 % (_upright, question_rules.one_prefix(tdesc), tdesc,
                    question_rules.a_prefix(tdesc), tdesc)),
            ]
        elif kind == "ray":
            gqs = [("ray_direction",
                    "The RIGHT panel has a contrasting-colour straight line drawn on the image; the "
                    "LEFT panel shows the same picture without it. That line is meant to run along "
                    "the %s. Does the drawn line lie along it and point the same way? Judge the "
                    "DIRECTION and the alignment only -- a line that is somewhat longer or shorter "
                    "than the thing it follows is fine. yes/no" % tdesc)]
        elif dkind == "circle":
            gqs = [("circle_centre",
                    "The RIGHT panel has a contrasting-colour circle drawn on the image; the LEFT "
                    "panel shows the same region WITHOUT the drawing. That circle is meant to mark "
                    "the %s. Is the CENTRE of the circle sitting on the %s, roughly at its middle? "
                    "The circle's exact size does not matter -- answer no only if its centre is off "
                    "the target. yes/no" % (tdesc, tdesc))]
        elif dkind == "point":
            gqs = [("point_on_target",
                    "The RIGHT panel has a contrasting-colour ring marker drawn on the image; the "
                    "LEFT panel shows the same region WITHOUT the drawing. That marker is meant to "
                    "mark the %s. Is the marked spot -- the middle of that little ring -- sitting "
                    "ON the %s? Judge only WHERE the spot sits: the marker's size and shape do not "
                    "matter and it does not have to cover or trace the target. yes/no"
                    % (tdesc, tdesc))]
        else:
            gqs = [("trace",
                    "The RIGHT panel has a contrasting-colour %s drawn to trace the %s; the LEFT panel "
                    "shows the same region WITHOUT the drawing. Comparing both: does the red drawing "
                    "trace the %s accurately (right position, right direction, right extent)? "
                    "yes/no" % ("line" if dkind == "line" else dkind, tdesc, tdesc))]
        sheet, ov, votes_raw = None, None, []
        content_note = None
        for ci, cand in enumerate(cands):
            ov = _draw(dkind, cand, im)
            _ev_idb = "grounding.r%d.c%d" % (rnd + 1, ci + 1)
            tiny = (dkind == "boxes") and is_tiny_boxes(cand)
            vregion = ((0, 0, W, H) if kind in ("ray", "line")
                       else _region(dkind, cand, W, H,
                                    ctx_box=(cbox if (use_context and ask_img != base) else None)))
            sheet = _sheet(im, ov, vregion,
                           os.path.join(workdir, "verify_r%d_%d.png" % (rnd, ci)),
                           magnify=tiny)
            evidence.append(sheet)
            ok, votes_raw, failed = True, [], []
            _record_only = ((()))
            purity_atoms_rep = None
            for qlabel, gq1 in _style_bind(gqs, dkind, cand, im):
                ok1, vraw = _gate(sheet, gq1, votes)
                yes1 = sum(1 for v in vraw if v and str(v).lower().startswith("y"))
                if ci:
                    ok1 = (yes1 == len(vraw) and len(vraw) == votes)
                votes_raw += list(vraw)
                transcript.append(
                    ("%s [%s]%s" % (gq1, qlabel, "" if not ci else " (rescue candidate %d, "
                                    "unanimous %d/%d required)" % (ci + 1, votes, votes)),
                     "%s -> %s" % ("/".join(str(v) for v in vraw), "yes" if ok1 else "no")))
                if (not ok1 and qlabel == "tight_purity" and ci == 0 and dkind == "boxes"):
                    try:
                        _ok_at, purity_atoms_rep = purity_atomic_regate(
                            sheet, tdesc, votes, transcript)
                    except Exception as _e:
                        log.debug("error ignored in grounded_read", exc_info=True)
                        _ok_at = False
                        purity_atoms_rep = {"enabled": True,
                                            "error": "%s: %s" % (type(_e).__name__, _e)}
                    if _ok_at:
                        ok1 = True
                        transcript.append(
                            ("(tight_purity atomic re-gate)",
                             'the compound purity ask voted no, but its OWN three disqualifiers -- whole of the target inside / no empty rectangle / nothing on a different object -- each passed on its own majority, so the check is confirmed on the criterion the shipped question actually states'))
                    else:
                        transcript.append(
                            ("(tight_purity atomic re-gate)",
                             "the atomic disqualifiers did NOT come back clean -- the shipped "
                             "refusal stands"))
                if not ok1:
                    if qlabel in _record_only:
                        transcript.append(
                            ("(%s -- recorded, not load-bearing)" % qlabel,
                             "this ask voted no and the verdict is UNCHANGED. re-measured it "
                             "on box step candidates and it accepted 10 of 18 deliberate 34 px "
                             "errors -- two "
                             "independent measurements agreeing that it carries almost no "
                             "information about position, so it may not refuse a candidate. The "
                             "34 px judgement is made by arithmetic instead "
                             "(`ring_cert.role_exact`, 1 px, no vote). See "
                             "`point_check.RECORD_ONLY`."))
                    else:
                        ok = False
                        failed.append(qlabel)
            if ((dkind == "boxes" and ci == 0 and not ok and failed == ["coverage"] and _exp_n is not None and len(cand) == _exp_n)):
                purity_ok_geom = [list(b) for b in cand]
                purity_ok_try = rnd + 1
            if ok and tiny and len(cand) == 1:
                craw = _ask(sheet, CONTENT_Q, think=512)
                cok, creason = content_matches(craw, tdesc)
                transcript.append(
                    ("%s [content_match]%s" % (CONTENT_Q, "" if not ci else
                                               " (rescue candidate %d)" % (ci + 1)),
                     "%s -> %s (%s)" % (craw, "yes" if cok else "no", creason)))
                if not cok:
                    ok = False
                    failed.append("content_match")
                    content_note = creason
            if ok and dkind == "boxes":
                for gi in giant_boxes(cand):
                    gsheet = _sheet(im, _draw("boxes", [cand[gi]], im),
                                    _region("boxes", [cand[gi]], W, H),
                                    os.path.join(workdir, "giant_r%d_%d_b%d.png" % (rnd, ci, gi)))
                    evidence.append(gsheet)
                    graw = _ask(gsheet, CONTENT_Q_GIANT, think=512)
                    gok, greason = content_matches_giant(graw, tdesc)
                    transcript.append(
                        ("%s [content_match_giant, box %d of %d: %.2f%% of the frame vs a set "
                         "median of %.2f%%]%s"
                         % (CONTENT_Q_GIANT, gi + 1, len(cand), 100.0 * box_area_frac(cand[gi]),
                            100.0 * sorted(box_area_frac(b) for b in cand)[len(cand) // 2],
                            "" if not ci else " (rescue candidate %d)" % (ci + 1)),
                         "%s -> %s (%s)" % (graw, "yes" if gok else "no", greason)))
                    if not gok:
                        ok = False
                        failed.append("content_match_giant")
                        content_note = greason
                        break
            swept_before = None
            if (not ok) and dkind == "boxes" and sweep_on(sweep) and failed == ["coverage"]:
                transcript.append(("(sweep coverage repair)",
                                   "purity passed and only coverage failed -> the completeness "
                                   "sweep takes over recall for this candidate"))
                try:
                    grown, rep_before = exhaustive_sweep(
                        im, cand, tdesc, workdir, transcript, evidence)
                except Exception as e:
                    log.debug("error ignored in grounded_read", exc_info=True)
                    grown, rep_before = cand, {"enabled": True, "complete": False,
                                            "error": "%s: %s" % (type(e).__name__,
                                                                 str(e)[:160])}
                    transcript.append(("(sweep error)", rep_before["error"]))
                if (rep_before or {}).get("complete"):
                    ov = _draw(dkind, grown, im)
                    sheet = _sheet(im, ov, (0, 0, W, H),
                                   os.path.join(workdir, "verify_sweep_r%d_%d.png" % (rnd, ci)))
                    evidence.append(sheet)
                    ok2, failed2 = True, []
                    for qlabel, gq1 in gqs:
                        okq, vraw = _gate(sheet, gq1, votes)
                        votes_raw += list(vraw)
                        transcript.append(
                            ("%s [%s, re-gate after sweep repair]" % (gq1, qlabel),
                             "%s -> %s" % ("/".join(str(v) for v in vraw),
                                           "yes" if okq else "no")))
                        if not okq:
                            ok2 = False
                            failed2.append(qlabel)
                    if ok2:
                        ok, failed = True, []
                        cand = list(grown)
                        swept_before = rep_before
                    else:
                        failed = failed2
                        transcript.append(("(sweep coverage repair)",
                                           "the swept set still failed the gate (%s) -> this "
                                           "try is rejected" % ",".join(failed2)))
                else:
                    transcript.append(("(sweep coverage repair)",
                                       "the sweep could not certify completeness for this "
                                       "candidate -> this try is rejected"))
            geom = cand
            if ok:
                tight_rep = None
                fit_rep = None
                if dkind in ("circle", "point", "line"):
                    try:
                        if dkind == "circle":
                            geom2, fit_rep = fit_circle_geom(im, geom, tdesc, workdir,
                                                             transcript)
                            if fit_rep.get("pass") is False:
                                transcript.append(("(fit_craft stop)", FIT_CIRCLE_REFUSAL_NOTE))
                                return {"geometry": None, "confirmed": False, "refused": True,
                                        "tries": rnd + 1, "evidence": evidence,
                                        "transcript": transcript, "overlay_img": None,
                                        "iteration_imgs": evidence,
                                        "refusal": "fit_craft_circle_cut",
                                        "fit_craft": fit_rep, "box_proposal": nom_info,
                                        "box_proposal_evidence": nom_sheets}
                            geom = geom2
                        elif dkind == "point":
                            geom, fit_rep = fit_point_confirmed(im, geom, tdesc, workdir,
                                                                transcript)
                        else:
                            geom, fit_rep = fit_ray_line(im, geom, kind,
                                                         target, tdesc, workdir, transcript,
                                                         side_anchor=fit_side_anchor)
                    except Exception as e:
                        log.debug("error ignored in grounded_read", exc_info=True)
                        fit_rep = {"enabled": True, "error": "%s: %s" % (type(e).__name__, e)}
                    if fit_rep and not fit_rep.get("error"):
                        ov = _draw(dkind, geom, im)
                sweep_rep = None
                if dkind == "boxes" and sweep_on(sweep) and swept_before is not None:
                    sweep_rep = swept_before
                elif dkind == "boxes" and sweep_on(sweep):
                    n_before_sweep = len(geom)
                    geom_before_sweep = list(geom)
                    try:
                        geom, sweep_rep = exhaustive_sweep(
                            im, geom, tdesc, workdir, transcript, evidence)
                    except Exception as e:
                        log.debug("error ignored in grounded_read", exc_info=True)
                        sweep_rep = {"enabled": True, "complete": False,
                                     "error": "%s: %s" % (type(e).__name__, str(e)[:160])}
                        transcript.append(("(sweep error)", sweep_rep["error"]))
                    if (sweep_rep or {}).get("complete") and len(geom) != n_before_sweep:
                        ov = _draw(dkind, geom, im)
                        sheet = _sheet(im, ov, (0, 0, W, H),
                                       os.path.join(workdir, "verify_postsweep_r%d.png" % rnd))
                        evidence.append(sheet)
                        for qlabel, gq1 in gqs:
                            okq, vraw = _gate(sheet, gq1, votes)
                            transcript.append(
                                ("%s [%s, re-gate after sweep growth]" % (gq1, qlabel),
                                 "%s -> %s" % ("/".join(str(v) for v in vraw),
                                               "yes" if okq else "no")))
                            if not okq:
                                sweep_rep["regate_failed"] = qlabel
                                transcript.append(("(sweep stop)",
                                                   "the grown set failed the %s re-gate -> "
                                                   "honest refusal" % qlabel))
                                return {"geometry": None, "confirmed": False, "refused": True,
                                        "tries": rnd + 1, "evidence": evidence,
                                        "transcript": transcript, "overlay_img": None,
                                        "iteration_imgs": evidence,
                                        "refusal": "sweep_regate_failed",
                                        "sweep": sweep_rep, "box_proposal": nom_info,
                                        "box_proposal_evidence": nom_sheets}
                    if not (sweep_rep or {}).get("complete"):
                        transcript.append(("(sweep stop)",
                                           "the completeness check could not certify the set "
                                           "(no terminal 'no') -> honest refusal "
                                           "rather than an under-counted number"))
                        return {"geometry": None, "confirmed": False, "refused": True,
                                "tries": rnd + 1, "evidence": evidence,
                                "transcript": transcript, "overlay_img": None,
                                "iteration_imgs": evidence, "refusal": "sweep_incomplete",
                                "sweep": sweep_rep, "box_proposal": nom_info,
                                "box_proposal_evidence": nom_sheets}
                    ov = _draw(dkind, geom, im)
                full = os.path.join(workdir, "confirmed.png")
                full = _emit_png(ov, full)
                evidence.append(full)
                res = {"geometry": geom, "confirmed": True, "refused": False,
                       "tries": rnd + 1, "evidence": evidence, "transcript": transcript,
                       "overlay_img": full, "iteration_imgs": evidence[:-1],
                       "box_proposal": nom_info, "box_proposal_evidence": nom_sheets}
                if tight_rep is not None:
                    res["tightness"] = tight_rep
                if pt_cert_rep is not None:
                    res["point_cert"] = pt_cert_rep
                if purity_atoms_rep is not None:
                    res["purity_atoms"] = purity_atoms_rep
                if fit_rep is not None:
                    res["fit_craft"] = fit_rep
                if sweep_rep is not None:
                    res["sweep"] = sweep_rep
                    res["read_craft"] = "sweep_count"
                return res
            geom = cands[0]
        ov = _draw(dkind, geom, im)
        diag = _ask(sheet, "In ONE short sentence: how does the drawn overlay deviate from "
                           "the %s? (shifted which way / wrong angle / wrong endpoints / "
                           "wrong size?)" % tdesc)
        transcript.append(("(diagnosis)", diag))
        _fail_txt = {"coverage": "some %s has no rectangle on it" % tdesc,
                     "tight_purity": "a rectangle is empty, loose or on the wrong thing",
                     "point_on_target": "the marked spot is not sitting on the %s" % tdesc,
                     "content_match": content_note or
                     "the rectangle does not enclose the %s" % tdesc,
                     "content_match_giant": content_note or
                     "one rectangle is roped around a whole group of %s instead of a single "
                     "one -- split it" % tdesc,
                     "line_hug": line_check.FAIL_TXT["line_hug"] % tdesc,
                     "line_ends": line_check.FAIL_TXT["line_ends"] % tdesc,
                     "line_contact": line_check.FAIL_TXT["line_contact"] % tdesc,
                     "pt_in_ring": point_check.FAIL_TXT["pt_in_ring"] % tdesc,
                     "pt_visible": point_check.FAIL_TXT["pt_visible"] % tdesc,
                     "pt_consensus": "the independent reads of the %s did not land in the same "
                                     "place, so there is no agreed spot to mark" % tdesc}
        pre = "; ".join(_fail_txt.get(f, f) for f in (failed or []))
        objection = ((pre + ("; " + diag if diag else "")) if pre
                     else (diag or ("verifier vote %s" % "/".join(str(v) for v in votes_raw))))
        prev_ov = os.path.join(workdir, "ov_r%d.png" % rnd)
        prev_ov = _emit_png(ov, prev_ov)
        prev_geom = geom
        if nom_active and dkind == "boxes" and rnd + 1 < retries:
            rep = diagnose_repair(im, geom, ndesc, workdir, rnd + 1, transcript, votes=votes)
            if rep is not None:
                pending_geom = rep
            elif redraw_forbidden(dkind, geom):
                transcript.append(("",
                                   "%s (%d boxes >= %d; the whole-set redraw servo is closed and "
                                   "the diagnosis has no incremental repair left)"
                                   % (NO_REDRAW_NOTE, len(geom), _NO_REDRAW_N)))
                return {"geometry": None, "confirmed": False, "refused": True,
                        "tries": rnd + 1, "evidence": evidence, "transcript": transcript,
                        "overlay_img": None, "iteration_imgs": evidence,
                        "refusal": "no_redraw_32",
                        "box_proposal": nom_info, "box_proposal_evidence": nom_sheets}
        if use_context and ctx_suspect and ask_img != base:
            _recontext("the proposal filled the context crop (>= %d%% of it in both directions) "
                       "and the gate rejected it: the crop is the target, not its container"
                       % int(_CTX_FILL_SUSPECT * 100))
    _why = ("the acceptance gate was never satisfied in %d tries" % retries)
    if _shape_log:
        _c = {s: _shape_log.count(s) for s in set(_shape_log)}
        _why = ("%d of %d tries produced nothing to draw (%s)"
                % (len(_shape_log), retries,
                   ", ".join("%s x%d" % (k, v) for k, v in sorted(_c.items()))))
        if _empty_tries == len(_shape_log) == retries:
            _why += ('; every try the reader ANSWERED and answered an empty set -- it is claiming this picture holds none of the target. The check does not turn that claim into a zero: the task is withheld.')
    transcript.append(("(diagnosis)", "tries exhausted: %s" % _why))
    return {"geometry": None, "confirmed": False, "refused": True,
            "tries": retries, "evidence": evidence, "transcript": transcript,
            "overlay_img": None, "iteration_imgs": evidence,
            "refusal": "tries_exhausted", "tries_exhausted": {
                "retries": retries, "answer_shapes": list(_shape_log),
                "empty_tries": _empty_tries, "why": _why},
            "box_proposal": nom_info, "box_proposal_evidence": nom_sheets}


def _text(ctx, ref):
    if not isinstance(ref, str):
        return ref
    from ._base import fmt_inline
    return fmt_inline(ctx, ref, strict=True)


@register("vlm.grounded_read")
@read_limits.scoped
def op_grounded_read(ctx, step):
    try:
        return _op_grounded_read(ctx, step)
    except ReadHeld as e:
        log.debug("error ignored in op_grounded_read", exc_info=True)
        return e.payload(geometry=None, confirmed=False, tries=0, evidence=[],
                         iteration_imgs=[], overlay_img=None,
                         transcript=[("(evaluator)", str(e))])


def _op_grounded_read(ctx, step):
    import tempfile
    from .. import shared_anchors
    img = resolve(ctx, step["image"])
    tgt = step["target"]
    tgt = _text(ctx, tgt) if isinstance(tgt, str) else [_text(ctx, t) for t in tgt]
    if per_box_reads.armed(step):
        import tempfile as _tf
        _bx = per_box_reads.boxes_of(resolve(ctx, step["in_boxes"]))
        _wd = _own_tmp(_tf.mkdtemp(prefix="fbsub_"))
        _kw = {}
        for _k, _v in (("retries", int(step.get("retries", 3))),
                       ("votes", int(step.get("votes", 3)))):
            _kw[_k] = _v
        for _k in ("expected_n", "allow"):
            if step.get(_k) is not None:
                _kw[_k] = resolve(ctx, step[_k])
        for _k in ("context",):
            if step.get(_k):
                _kw[_k] = _text(ctx, step[_k])
        for _k in ("propose_boxes", "metric_box", "tightness", "layout", "sort", "sweep",
                   "absent_ok"):
            if step.get(_k) is not None:
                _kw[_k] = step[_k]
        try:
            _out = per_box_reads.run_in_boxes(img, step.get("primitive", "boxes"), tgt, _bx, _wd,
                                            pad=float(step.get("pad",
                                                                per_box_reads.DEFAULT_PAD)),
                                            on_miss=step.get("on_miss", "refuse"), **_kw)
        except BaseException:
            shutil.rmtree(_wd, ignore_errors=True)
            raise
        _out["unreadable"] = _out["refused"]
        return retire_workdir(_wd, _out)
    _ak = shared_anchors.key_of(img, step.get("primitive", "boxes"), tgt,
                            {k: step.get(k) for k in
                             ("retries", "votes", "expected_n", "context", "propose_boxes",
                              "metric_box", "tightness", "layout", "sort",
                              "fit_side_anchor", "sweep", "absent_ok", "allow")})
    _pt = point_of(ctx)
    _leg = (_pt.get("id") if isinstance(_pt, dict) else _pt)
    wd = _own_tmp(tempfile.mkdtemp(prefix="fbread_"))
    try:
        r = grounded_read(img, step.get("primitive", "boxes"), tgt,
                          wd, retries=int(step.get("retries", 3)),
                          votes=int(step.get("votes", 3)),
                          expected_n=resolve(ctx, step.get("expected_n"))
                          if step.get("expected_n") else None,
                          context=_text(ctx, step.get("context"))
                          if step.get("context") else None,
                          propose_boxes=step.get("propose_boxes", "vlm"),
                          metric_box=bool(step.get("metric_box", False)),
                          tightness=step.get("tightness"),
                          layout=step.get("layout"), sort=step.get("sort"),
                          fit_side_anchor=_text(ctx, step.get("fit_side_anchor"))
                          if step.get("fit_side_anchor") else None,
                          sweep=step.get("sweep"),
                          absent_ok=step.get("absent_ok"),
                          allow=resolve(ctx, step.get("allow")) if step.get("allow") is not None
                          else 0,
                          diagnostic=diagnostic_leaf(point_of(ctx)),
                          exempt=derive_exempt(ctx, step))
    except BaseException:
        shutil.rmtree(wd, ignore_errors=True)
        raise
    r["unreadable"] = r["refused"]
    out = retire_workdir(wd, r)
    _g2 = out.get("geometry") if isinstance(out, dict) else None
    shared_anchors.record(_leg, tgt if isinstance(tgt, str) else json.dumps(tgt),
                      _g2[0] if isinstance(_g2, list) and len(_g2) == 1 else None)
    if isinstance(out, dict) and not out.get("refused"):
        shared_anchors.put_shared(_ak, out)
    return out


@register("vlm.crop_read")
@read_limits.scoped
def op_crop_read(ctx, step):
    import tempfile
    from collections import Counter as _C
    layout_note = None
    order = None
    if "boxes" in step:
        src = resolve(ctx, step["boxes"])
        boxes = src.get("geometry") if isinstance(src, dict) else src
        if not boxes:
            return {"answers": None, "unreadable": True}
        if step.get("layout"):
            boxes, flipped, layout_note = layout_fix(boxes, step["layout"])
            if flipped:
                boxes = [clamp_geom("boxes", [b])[0] for b in boxes]
        if str(step.get("sort", "")).strip().lower() == "reading_order":
            boxes, order = sort_reading_order(boxes, step.get("layout"))
    else:
        boxes = [[0, 0, 1000, 1000]]
    img = resolve(ctx, step["image"])
    im = img if hasattr(img, "convert") else Image.open(img).convert("RGB")
    im = im.convert("RGB")
    W, H = im.size
    q = _text(ctx, step["question"])
    q = question_rules.with_dash(q, op="vlm.crop_read", authored_none_fn=authored_none)
    votes = int(step.get("votes", 3))
    pad = float(step.get("pad", _CROP_PAD))
    wd = _own_tmp(tempfile.mkdtemp(prefix="cropread_"))
    answers, crops, degen_notes = [], [], []
    clip_notes, reask_notes, win_notes = [], [], []
    shrug_notes = []
    guard_notes = []
    cut_notes = []
    try:
        def _cut_and_ask(box, px, i, tag):
            c = magnify_crop(im.crop(px))
            c = frame_and_dim(c, box, px, W, H)
            cp = _emit_png(c, os.path.join(wd, "c%d%s.png" % (i, tag)))
            vs, dg = [], []
            for k in range(votes):
                v = _ask(cp, read_policy.paraphrase(q, k))
                ph = repeat_degenerate(v)
                if ph:
                    v2 = _ask(cp, read_policy.paraphrase(q, k + votes + 1))
                    ph2 = repeat_degenerate(v2)
                    dg.append({"box": i + 1, "vote": k + 1, "phrase": ph[:80],
                               "recovered": not bool(ph2)})
                    v = None if ph2 else v2
                vs.append(v)
            vals = [v for v in vs if v]
            return cp, c, vs, dg, (_C(vals).most_common(1)[0][0] if vals else None)

        for i, box in enumerate(boxes):
            px, gh, gray = glyph_floor_px(im, box, W, H, pad)
            cp, c, vs, degen, ans = _cut_and_ask(box, px, i, "")
            cut_rep = None
            if gray is not None:
                cut_rep = edge_ink.edge_cut(gray, px) or None
                if cut_rep is not None:
                    cut_notes.append({"box": i + 1, **cut_rep})
            clip_note = None
            from . import recognize as _recog
            reasked = False
            _shrug_in = is_shrug(ans, q)
            _shrug_txt = str(ans)[:60] if _shrug_in else None
            _guard_hit = None
            _guard_text = None
            _guard_rule = None
            _guard_reason = ""
            if ans is None or _shrug_in:
                reasked = True
                _q_save = q
                try:
                    q = read_policy.retry_wrap(_q_save)
                    _cp3, c3, vs3, degen3, ans3 = _cut_and_ask(box, px, i, "r")
                finally:
                    q = _q_save
                if ans3 is not None and not is_shrug(ans3, q):
                    cp, c, vs, ans = _cp3, c3, vs3, ans3
                    _shrug_in = False
                    _guard_hit = None
                elif _shrug_in:
                    ans = None
                degen = degen + degen3
            elif _shrug_in:
                ans = None
            if _shrug_txt is not None:
                shrug_notes.append({"box": i + 1, "shrug": _shrug_txt,
                                    "recovered": ans is not None})
            if _guard_text is not None:
                guard_notes.append({"box": i + 1, "text": _guard_text,
                                    "rule": _guard_rule,
                                    "reason": _guard_reason,
                                    "recovered": ans is not None and not _guard_hit})
            answers.append(ans)
            crops.append(cp)
            if degen:
                degen_notes.extend(degen)
            if clip_note is not None:
                clip_notes.append(clip_note)
            if reasked:
                reask_notes.append({"box": i + 1, "recovered": ans is not None})
            if gh > 0:
                win_notes.append({"box": i + 1, "glyph_h": gh,
                                  "window_px": [int(v) for v in px]})
    except BaseException:
        shutil.rmtree(wd, ignore_errors=True)
        raise
    out = {"answers": answers, "crops": crops,
           "unreadable": any(a is None for a in answers)}
    if out["unreadable"]:
        out["refused"] = True
        out["refusal"] = "reader returned no answer on %d of %d window(s)" % (
            sum(1 for a in answers if a is None), len(answers))
        _sh = [s for s in shrug_notes if not s.get("recovered")]
        if _sh:
            out["refusal"] += (' -- %d of them answered with a bare shrug the question never offered (%s) and were still a shrug after the retry'
                               % (len(_sh), ", ".join("box %d %r" % (s["box"], s["shrug"])
                                                      for s in _sh[:4])))
        _guard_count = [g for g in guard_notes if not g.get("recovered")]
        if _guard_count:
            out["refusal"] += (' -- %d of them returned a template slot or refusal prose instead of a reading (%s) and were still that after the retry'
                               % (len(_guard_count), ", ".join("box %d %r [%s]"
                                                        % (g["box"], g["text"], g["rule"])
                                                        for g in _guard_count[:4])))
    _wall = read_limits.pop_timeouts()
    if _wall:
        out["wall_timeouts"] = len(_wall)
    if _wall and out.get("refused"):
        out["unreadable"] = True
        out["refusal"] = ('%s -- and %d reader call(s) on this check were cut off by the wall clock (%s). The task is withheld.'
                          % (out.get("refusal") or "reader hung on this check", len(_wall),
                             _wall[-1]))
    if cut_notes:
        out["edge_cut"] = cut_notes
    if shrug_notes:
        out["shrug_capture"] = shrug_notes
    if guard_notes:
        out["read_guard"] = guard_notes
    if reask_notes:
        out["empty_reask"] = reask_notes
    if win_notes:
        out["text_window"] = win_notes
    if clip_notes:
        out["glyph_clip"] = clip_notes
    if degen_notes:
        out["repeat_degenerate"] = degen_notes
    if layout_note is not None:
        out["layout_check"] = layout_note
        out["boxes_used"] = [[round(float(v), 1) for v in b[:4]] for b in boxes]
    if order is not None:
        out["read_order"] = order
    return retire_workdir(wd, out)


@register("vlm.compose_ray_target")
def op_compose_ray_target(ctx, step):
    import math
    import tempfile
    ray = resolve(ctx, step["ray"])
    if not isinstance(ray, dict) or not ray.get("confirmed"):
        return {"overlay_img": None, "unreadable": False}
    img = resolve(ctx, step["image"])
    im = img if hasattr(img, "convert") else Image.open(img).convert("RGB")
    im = im.convert("RGB")
    W, H = im.size
    ov = im.copy()
    d = ImageDraw.Draw(ov)
    py, px, ty, tx = ray["geometry"]
    p0 = (px * W / 1000.0, py * H / 1000.0)
    p1 = (tx * W / 1000.0, ty * H / 1000.0)
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    n = max(math.hypot(dx, dy), 1e-6)
    ux, uy = dx / n, dy / n
    lcol = inv_color(im, (min(p0[0], p1[0]) - 10, min(p0[1], p1[1]) - 10,
                          max(p0[0], p1[0]) + 10, max(p0[1], p1[1]) + 10))
    for s in range(0, int((W + H) / 26), 2):
        a = (p1[0] + ux * 26 * s, p1[1] + uy * 26 * s)
        b = (p1[0] + ux * 26 * (s + 1), p1[1] + uy * 26 * (s + 1))
        d.line([a, b], fill=lcol, width=5)
    d.line([p0, p1], fill=lcol, width=7)
    circ = resolve(ctx, step.get("circle")) if step.get("circle") else None
    if isinstance(circ, dict) and circ.get("confirmed") and circ.get("geometry"):
        cy, cx, r = circ["geometry"]
        qx, qy, qr = cx * W / 1000.0, cy * H / 1000.0, r * min(W, H) / 1000.0
        ccol = inv_color(im, (qx - qr, qy - qr, qx + qr, qy + qr))
        d.ellipse([qx - qr, qy - qr, qx + qr, qy + qr], outline=ccol, width=6)
    cap = resolve(ctx, step.get("caption")) if step.get("caption") else None
    if isinstance(cap, dict):
        cap = "deviation %s deg -> frac %s" % (cap.get("deg_off"), cap.get("frac"))
    elif isinstance(cap, str) and "{" in cap:
        cap = _text(ctx, step["caption"])
    if cap:
        d.rectangle([0, H - 44, W, H], fill=(0, 0, 0))
        d.text((10, H - 38), str(cap), fill=(255, 255, 255), font=_font(24))
    tol = resolve(ctx, step.get("tolerance")) if step.get("tolerance") else None
    wd = _own_tmp(tempfile.mkdtemp(prefix="rayviz_"))
    p = os.path.join(wd, "final_overlay.png")
    p = _emit_png(ov, p)
    return retire_workdir(wd, {"overlay_img": p, "unreadable": False})


