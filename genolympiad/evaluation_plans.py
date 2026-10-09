"""Build the evaluation plan (the tree of checks) for a task from its evaluation program."""
from __future__ import annotations

import copy
import os
import logging

log = logging.getLogger(__name__)


_D_OPS = {"cv.color_grid", "cv.binary_grid", "cv.bordered_binary_grid", "cv.cell_digits",
          "cv.stone_grid", "vlm.read_grid", "compare.grid", "vlm.read_stone_grid"}


def _point_ops(pt):
    return [s.get("op") for s in pt.get("flow", []) if s.get("op")]


def _task_ops(task):
    ops = set()
    for pt in task.get("scoring", []):
        ops.update(_point_ops(pt))
    return ops


def template_of(task):
    ops = _task_ops(task)
    if ops & _D_OPS:
        return "D"
    if any(o.startswith("compute.") for o in ops):
        return "F"
    return "E"


_OCR_OUTPUT_OPS = ("ocr.read", "ocr.read_rows", "ocr.page_words", "ocr.mirror_word")

import re as _re_at
_RUNCODE_REGEX_RX = _re_at.compile(
    r"""re\.(?:findall|search|match|fullmatch|finditer)\s*\(\s*(?:r?)(?P<q>['"])(?P<pat>.*?)(?P=q)""",
    _re_at.DOTALL)


_ALPHA_CONSUME_SIGNALS = (".isalpha(", "[^a-z]", "[^a-za-z]", "[a-z]+", "sorted(")
_ALPHA_WORD_SHAPE = r"[A-Za-z]{2,}"


def _harvest_consume_patterns(flow):
    pats = []
    wants_alpha = False
    for s in flow or []:
        if not isinstance(s, dict):
            continue
        if s.get("op") == "run.code" and isinstance(s.get("code"), str):
            code = s["code"]
            for m in _RUNCODE_REGEX_RX.finditer(code):
                p = m.group("pat")
                if p and p not in pats:
                    pats.append(p)
            low = code.lower()
            if any(sig in low for sig in _ALPHA_CONSUME_SIGNALS):
                wants_alpha = True
    if wants_alpha and _ALPHA_WORD_SHAPE not in pats:
        pats.append(_ALPHA_WORD_SHAPE)
    return pats


def _overlay_strip(panels):
    try:
        import tempfile
        from PIL import Image, ImageDraw, ImageFont
    except Exception:
        log.debug("error ignored in _overlay_strip", exc_info=True)
        return None
    good = []
    for lbl, p in panels:
        try:
            good.append((lbl, Image.open(p).convert("RGB")))
        except Exception:
            log.debug("error ignored in _overlay_strip", exc_info=True)
            continue
    if not good:
        return None
    if len(good) == 1:
        return panels[0][1]
    try:
        font = ImageFont.truetype("arial.ttf", 22)
    except Exception:
        log.debug("error ignored in _overlay_strip", exc_info=True)
        font = ImageFont.load_default()
    W = max(im.width for _, im in good)
    bar = 34
    scaled = []
    for lbl, im in good:
        if im.width != W:
            im = im.resize((W, max(1, int(im.height * W / im.width))), Image.LANCZOS)
        scaled.append((lbl, im))
    H = sum(im.height + bar for _, im in scaled)
    sheet = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(sheet)
    y = 0
    for i, (lbl, im) in enumerate(scaled):
        d.rectangle([0, y, W, y + bar], fill=(20, 20, 20))
        d.text((8, y + 5), "%d/%d  %s" % (i + 1, len(scaled), lbl), fill=(255, 255, 255), font=font)
        sheet.paste(im, (0, y + bar))
        y += im.height + bar
    out = os.path.join(tempfile.mkdtemp(prefix="fbstrip_"), "overlay_strip.png")
    sheet.save(out)
    return out


_LOC_KEY_RE = _re_at.compile(r"(^|_)(read_)?loc$", _re_at.I)
_OVERLAY_OPS = {"vlm.grounded_read": None,
                "vlm.ray_hits": "ray extension",
                "vlm.compose_ray_target": "composed final overlay",
                "headcount.detect_confirmed": "confirmed detection boxes",
                "vlm.ref_match": "reference comparison pages",
                "ref.compose": "reference comparison page"}


def _boxes_of(cd, image):
    if not isinstance(cd, dict):
        return None
    raw = None
    for k in ("boxes", "geometry", "box", "bbox"):
        v = cd.get(k)
        if not (isinstance(v, (list, tuple)) and v):
            continue
        if isinstance(v[0], (list, tuple)) and len(v[0]) >= 4:
            raw = [list(b)[:4] for b in v]
        elif len(v) >= 4 and all(isinstance(x, (int, float)) and not isinstance(x, bool)
                                 for x in v[:4]):
            raw = [list(v[:4])]
        if raw:
            break
    if not raw:
        return None
    try:
        from PIL import Image
        with Image.open(image) as im:
            W, H = im.size
    except Exception:
        log.debug("error ignored in _boxes_of", exc_info=True)
        return None
    top = max(abs(float(c)) for b in raw for c in b)
    sx, sy = (W, H) if top <= 1.5 else ((W / 1000.0, H / 1000.0) if top <= 1000 else (1.0, 1.0))
    return [[b[1] * sx, b[0] * sy, b[3] * sx, b[2] * sy] for b in raw]


_GATE_LABEL_RE = _re_at.compile(r"\[(coverage|tight_purity|point_on_target|circle_centre|"
                                r"ray_direction|trace|content_match|content_match_giant)\]")

_COLOUR_LEGEND = [
    "Outline colour is picked PER BOX for maximum visibility on what that box actually lies on: "
    "of 10 candidates (black, white + 8 saturated), the one whose 5th-percentile CIELAB distance "
    "to a ring of pixels along the stroke is largest, plus a counter-luminance casing on both "
    "sides. Colour carries NO verdict - every box ranks equal; the green/grey split on older "
    "pages was an inv_color threshold artefact (measured), not a meaning. Display only.",
    '10 +8 '
    'CIELAB 5 '
    '/ inv_color '
    '',
]


def _gate_ticket(cd):
    seen = {}
    for row in (cd.get("transcript") or []):
        try:
            q, ans = row[0], row[1]
        except Exception:
            log.debug("error ignored in _gate_ticket", exc_info=True)
            continue
        m = _GATE_LABEL_RE.search(str(q))
        if not m:
            continue
        left = str(ans).split("->")[0]
        votes = [v for v in left.split("/") if str(v).strip()]
        yes = sum(1 for v in votes if str(v).strip().lower().startswith("y"))
        if votes:
            seen[m.group(1)] = "%s %d/%d" % (m.group(1), yes, len(votes))
    return [seen[k] for k in ("coverage", "tight_purity", "point_on_target", "circle_centre",
                              "ray_direction", "trace", "content_match", "content_match_giant")
            if k in seen]


def _fmt_inline_report(ctx, s):
    try:
        from .ops._base import fmt_inline
        return fmt_inline(ctx, s, strict=False)
    except Exception:
        log.debug("error ignored in _fmt_inline_report", exc_info=True)
        return s


def _crop_values_for(flow, ctx, src_out):
    for s in flow:
        if not (isinstance(s, dict) and s.get("op") == "vlm.crop_read"):
            continue
        ref = s.get("boxes")
        if not (isinstance(ref, str) and (ref == src_out or ref.startswith(src_out + "."))):
            continue
        cd = ctx.get(s.get("out")) if s.get("out") else None
        ans = cd.get("answers") if isinstance(cd, dict) else None
        if isinstance(ans, list):
            q = s.get("question")
            return ans, (_fmt_inline_report(ctx, q) if isinstance(q, str) else None)
    return None, None


def _fb_box_panel(s, cd, pt, ctx, image):
    if image is None or s.get("primitive", "boxes") != "boxes":
        return None
    geom = cd.get("geometry")
    if not (isinstance(geom, (list, tuple)) and geom
            and isinstance(geom[0], (list, tuple)) and len(geom[0]) >= 4):
        return None
    try:
        from PIL import Image
        with Image.open(image) as im:
            W, H = im.size
    except Exception:
        log.debug("error ignored in _fb_box_panel", exc_info=True)
        return None
    px = [[b[1] * W / 1000.0, b[0] * H / 1000.0, b[3] * W / 1000.0, b[2] * H / 1000.0]
          for b in geom]
    out_name = s.get("out") or "read"
    vals, _q = _crop_values_for([x for x in (pt.get("flow") or []) if isinstance(x, dict)],
                                ctx, out_name)
    n_read = sum(1 for v in (vals or []) if v not in (None, ""))
    tgt = s.get("target")
    tgt = _fmt_inline_report(ctx, tgt) if isinstance(tgt, str) else \
        (str(tgt) if tgt is not None else "target")
    ticket = _gate_ticket(cd) or ["ticket not recorded"]
    caption = ['%s · %d box(es) · "%s" · %s · %d tries%s'
               % (out_name, len(px), tgt[:56], " + ".join(ticket),
                  int(cd.get("tries") or 0),
                  (" · %d/%d read" % (n_read, len(px))) if vals is not None else " · no values")]
    if vals is None:
        legend = ["#k = box number only (same order the scorer used); this leaf has no per-box "
                  "crop read, so no value is claimed."]
        legend.append('#k = crop_read')
    else:
        legend = ["#k=v -> box k + the answer its own crop read (majority vote) gave; "
                  "? = the trace has no reading for that box."]
        legend.append('#k= → k + crop_read'
                      '? = no reading of this box in the trace.')
    legend.extend(_COLOUR_LEGEND)
    try:
        from . import evaluation_tree as _A
        return _A.RENDERERS["grounded_boxes"](
            image, {"boxes": px, "values": vals, "caption": caption, "legend": legend},
            {"id": "%s_fbbox" % out_name})[0]
    except Exception:
        log.debug("error ignored in _fb_box_panel", exc_info=True)
        return None


def _derived_read_panel(s, pt, ctx, image):
    from . import ops as _o
    ref = s.get("boxes")
    if image is None or not isinstance(ref, str) or not s.get("out"):
        return None
    if s.get("image") not in _page_aliases_display([x for x in (pt.get("flow") or [])
                                                    if isinstance(x, dict)]):
        return None
    src = _o.resolve(ctx, ref)
    geom = src.get("geometry") if isinstance(src, dict) else src
    if not (isinstance(geom, (list, tuple)) and geom
            and isinstance(geom[0], (list, tuple)) and len(geom[0]) >= 4):
        return None
    cd = ctx.get(s["out"])
    vals = cd.get("answers") if isinstance(cd, dict) else None
    if not isinstance(vals, list):
        return None
    draw_on = image
    if s.get("image") != "image":
        try:
            cand = _o.resolve(ctx, s.get("image"))
            if isinstance(cand, str) and os.path.exists(cand):
                draw_on = cand
        except Exception:
            log.debug("error ignored in _derived_read_panel", exc_info=True)
            pass
    try:
        from PIL import Image
        with Image.open(draw_on) as im:
            W, H = im.size
    except Exception:
        log.debug("error ignored in _derived_read_panel", exc_info=True)
        return None
    px = [[b[1] * W / 1000.0, b[0] * H / 1000.0, b[3] * W / 1000.0, b[2] * H / 1000.0]
          for b in geom]
    n_read = sum(1 for v in vals if v not in (None, ""))
    caption = ["%s · %d box(es) read · derived from '%s' by this leaf's own code · %d/%d read"
               % (s["out"], len(px), ref, n_read, len(px))]
    legend = ["#k=v -> box k of the read list + its own crop-read answer (majority vote). "
              "These are the readings the score was computed from.",
              '#k= → k + crop_read']
    legend.extend(_COLOUR_LEGEND)
    try:
        from . import evaluation_tree as _A
        return _A.RENDERERS["grounded_boxes"](
            draw_on, {"boxes": px, "values": vals, "caption": caption, "legend": legend},
            {"id": "%s_cropbox" % s["out"]})[0]
    except Exception:
        log.debug("error ignored in _derived_read_panel", exc_info=True)
        return None


def _grounded_panels(pt, ctx, image=None):
    panels = []
    ring_outs = set()
    for s in pt.get("flow", []):
        if not isinstance(s, dict):
            continue
        out = s.get("out")
        cd = ctx.get(out) if out else None
        op = s.get("op")
        if op in _OVERLAY_OPS:
            if isinstance(cd, dict) and cd.get("overlay_img"):
                kindtxt = _OVERLAY_OPS[op] or s.get("primitive", "boxes")
                img_p = None
                if op == "vlm.grounded_read":
                    try:
                        img_p = _fb_box_panel(s, cd, pt, ctx, image)
                    except Exception:
                        log.debug("error ignored in _grounded_panels", exc_info=True)
                        img_p = None
                    if img_p:
                        ring_outs.add(out)
                panels.append(("%s (%s)" % (out or "read", kindtxt),
                               img_p or cd["overlay_img"]))
            continue
        if op == "vlm.crop_read" and isinstance(s.get("boxes"), str):
            if str(s["boxes"]).split(".")[0] not in ring_outs:
                try:
                    dp = _derived_read_panel(s, pt, ctx, image)
                except Exception:
                    log.debug("error ignored in _grounded_panels", exc_info=True)
                    dp = None
                if dp:
                    panels.append(("%s (crop reads)" % s.get("out", "read"), dp))
            continue
        if out and _LOC_KEY_RE.search(str(out)) and image is not None:
            boxes = _boxes_of(cd, image)
            if boxes:
                try:
                    from . import evaluation_tree as _A
                    rend = _A.RENDERERS.get("read_loc") or _A.RENDERERS["detect_boxes"]
                    ov = rend(image, {"boxes": boxes}, {"id": "%s_loc" % out})[0]
                    panels.append(("%s (read position)" % out, ov))
                except Exception:
                    log.debug("error ignored in _grounded_panels", exc_info=True)
                    pass
    return panels


_PAGE_ALIAS_OPS = ("crop.full",)
_PAGE_ALIAS_PATH_OPS = ("overlay.compare",)
_READLOC_ASK2 = (
    'Look at this picture. Another person answered this question about it:\n"%s"\n\n'
    "You do not have to answer the question. Mark the ONE place in the picture that a person "
    "would have to look at to answer it — draw the smallest box that contains that printed "
    "number / pointer / marking and the label next to it.\n"
    'Output STRICT JSON only: {"box_2d":[ymin,xmin,ymax,xmax]} normalized 0-1000.')
_LOC_IOU_MIN = 0.5
_VERIFY_ASK = ("This is a small cut-out from a bigger picture.\n"
               "What value is printed inside this cut-out? Copy it exactly as it is printed — "
               "just the value itself, nothing else. If nothing is printed inside it, "
               "answer: none.")
_FLAG_UNSTABLE = ''
_FLAG_VALUE = ''
_FLAG_TARGET = ''
_FLAG_UNPROVED = ''
_REREAD_THINK = 1024
_REREAD_MAXTOK = 4096
_READLOC_ASK = (
    'Someone was asked this question about this picture:\n"%s"\n\n'
    "Do NOT answer that question. Just show WHERE in the picture its answer is written or shown: "
    "put one tight box around that exact spot (the printed number / the pointer / the marking "
    "itself, together with the label right beside it). If several places would answer it, box the "
    "one a reader would use.\n"
    'Output STRICT JSON only: {"box_2d":[ymin,xmin,ymax,xmax]} normalized 0-1000.')


def _page_aliases(flow):
    names = {"image"}
    for _ in range(3):
        for s in flow:
            if (isinstance(s, dict) and s.get("op") in _PAGE_ALIAS_OPS
                    and s.get("image") in names and s.get("out")):
                names.add(s["out"])
    return names


def _page_aliases_display(flow):
    names = set(_page_aliases(flow))
    for _ in range(3):
        for s in flow:
            if (isinstance(s, dict) and s.get("op") in _PAGE_ALIAS_PATH_OPS
                    and s.get("image") in names and s.get("out")):
                names.add(s["out"] + ".path")
    return names


def _readloc_targets(pt):
    if _is_diagnostic_leaf(pt.get("id"), pt):
        return []
    flow = [s for s in (pt.get("flow") or []) if isinstance(s, dict)]
    pages = _page_aliases(flow)
    hits = []
    for s in flow:
        op = s.get("op")
        if op == "vlm.read_number":
            if s.get("image") in pages and s.get("question") is not None:
                hits.append(s)
        elif op == "vlm.crop_read":
            if "boxes" in s or s.get("image") not in pages or not s.get("out"):
                continue
            o = s["out"]
            for c in flow:
                if not str(c.get("op", "")).startswith("compare."):
                    continue
                val = c.get("value")
                if not (isinstance(val, str) and (val == o or val.startswith(o + "."))):
                    continue
                t = c.get("target")
                if isinstance(t, (int, float)) and not isinstance(t, bool):
                    hits.append(s)
                    break
                if isinstance(t, str) and t.startswith("gt."):
                    hits.append(s)
                    break
    return hits


def _readloc_question(ctx, step):
    try:
        from .ops.recognize import _q
        q = _q(ctx, step)
    except Exception:
        log.debug("error ignored in _readloc_question", exc_info=True)
        q = _fmt_inline_report(ctx, step.get("question"))
    if isinstance(q, str) and q.strip():
        return q.strip()
    return None


def _readloc_numeric_target(ctx, pt, step):
    if step.get("op") != "vlm.crop_read":
        return True
    from . import ops as _ops
    o = step.get("out")
    for c in pt.get("flow") or []:
        if not (isinstance(c, dict) and str(c.get("op", "")).startswith("compare.")):
            continue
        val = c.get("value")
        if not (isinstance(val, str) and (val == o or val.startswith(o + "."))):
            continue
        t = c.get("target")
        if not isinstance(t, str):
            return isinstance(t, (int, float)) and not isinstance(t, bool)
        try:
            rv = _ops.resolve(ctx, t)
        except Exception:
            log.debug("error ignored in _readloc_numeric_target", exc_info=True)
            rv = None
        if isinstance(rv, (int, float)) and not isinstance(rv, bool):
            return True
    return False


def _readloc_crop(image, box01k, pad=0.20):
    import tempfile
    from PIL import Image
    from .ops.evidence_grounding import crop_pad_px, magnify_crop
    im = Image.open(image).convert("RGB") if not hasattr(image, "convert") else image.convert("RGB")
    W, H = im.size
    c = magnify_crop(im.crop(crop_pad_px(box01k, W, H, pad)))
    if min(c.size) < 4:
        return None, None
    p = os.path.join(tempfile.mkdtemp(prefix="readloc_"), "crop.png")
    c.save(p)
    thumb = None
    try:
        import io as _io, base64 as _b64
        t = c.copy()
        t.thumbnail((220, 220))
        buf = _io.BytesIO()
        t.save(buf, "JPEG", quality=60)
        thumb = {"__img__": True, "w": c.width, "h": c.height,
                 "b64": _b64.b64encode(buf.getvalue()).decode("ascii")}
    except Exception:
        log.debug("error ignored in _readloc_crop", exc_info=True)
        thumb = None
    return p, thumb


def _iou(a, b):
    ay0, ax0, ay1, ax1 = [float(v) for v in a[:4]]
    by0, bx0, by1, bx1 = [float(v) for v in b[:4]]
    ay0, ay1 = min(ay0, ay1), max(ay0, ay1)
    ax0, ax1 = min(ax0, ax1), max(ax0, ax1)
    by0, by1 = min(by0, by1), max(by0, by1)
    bx0, bx1 = min(bx0, bx1), max(bx0, bx1)
    iw = max(0.0, min(ax1, bx1) - max(ax0, bx0))
    ih = max(0.0, min(ay1, by1) - max(ay0, by0))
    inter = iw * ih
    ua = (ax1 - ax0) * (ay1 - ay0) + (bx1 - bx0) * (by1 - by0) - inter
    return (inter / ua) if ua > 0 else 0.0


def _union_box(a, b):
    return [min(a[0], b[0]), min(a[1], b[1]), max(a[2], b[2]), max(a[3], b[3])]


def _locate_two_votes(image, q):
    from .ops.evidence_grounding import _ask as _fb_ask, _parse as _fb_parse, geom_legal

    def one(ask):
        try:
            txt = _fb_ask(image, ask % q, think=256)
        except Exception:
            log.debug("error ignored in _locate_two_votes", exc_info=True)
            return None
        bs = _fb_parse("boxes", txt or "")
        if not bs:
            return None
        ok, _bad = geom_legal("boxes", bs[:1])
        return bs[0] if ok else None

    a, b = one(_READLOC_ASK), one(_READLOC_ASK2)
    if a is None and b is None:
        return None, "none", ' box_2d'
    if a is None or b is None:
        return (a or b), "single", '/'
    v = _iou(a, b)
    if v >= _LOC_IOU_MIN:
        return _union_box(a, b), "stable", 'IoU %.2f' % v
    return a, "unstable", 'IoU %.2f' % v


def _value_matches(read_val, transcript):
    if transcript is None:
        return None
    t = str(transcript).strip()
    if not t:
        return None
    tl = t.lower()
    if tl in ("none", "nothing", "n/a", "na", "-", ''):
        return False
    if read_val is None or isinstance(read_val, (dict, list, tuple, bool)):
        return None
    if isinstance(read_val, (int, float)):
        import re as _re
        want = float(read_val)
        nums = [float(x) for x in _re.findall(r"-?\d+(?:\.\d+)?", tl.replace(",", ""))]
        if not nums:
            return False
        return any(abs(n - want) < 1e-6 for n in nums)
    r = str(read_val).strip().lower()
    if not r:
        return None
    return (r in tl) or (tl in r)


_CNT_HOWMANY = _CNT_VERB = None
_CNT_TAIL = (r"(?=\s*(?:[,.;:!?()\[\]/']|--|$|\b(?:is|are|was|were|do|does|did|can|could|will|would|"
             r"has|have|had|that|which|who|whose|you|it|they|there|here|in|on|at|of|under|below|"
             r"above|beside|inside|within|between|across|along|from|to|and|or|but|with|per|by|"
             r"into|onto|over|actually|really|currently|right|now|together|total|altogether|"
             r"lying|sitting|standing|drawn|shown|visible|threaded|stacked|placed|resting|"
             r"hanging|printed|marked|labelled|labeled|one|each|every|"
             r"stand|stands|remain|remains|remaining|radiate|radiates|appear|appears|cross|"
             r"crosses|run|runs|meet|meets|hold|holds|cover|covers|list|lists|carry|carries|"
             r"break|breaks|form|forms|sit|belong|belongs|reach|reaches|point|points|show|shows|"
             r"say|says|go|goes|come|comes|make|makes|take|takes|look|looks|face|faces|touch|"
             r"touches|join|joins|connect|connects|contain|contains|"
             r"wide|tall|high|long|deep|apart|away|left|right)\b))")
_CNT_BODY = r"([A-Za-z][A-Za-z0-9-]*(?:\s+[A-Za-z][A-Za-z0-9-]*){0,3}?)"
_CNT_LEAD = ("the", "a", "an", "all", "any", "those", "these", "that", "this", "its",
             "their", "real", "actual", "physical", "individual", "separate", "single")
_CNT_BAD_HEAD = frozenset(("of", "them", "they", "it", "us", "you", "other", "others", "many",
                           "more", "most", "such", "time", "times", "way", "ways", "kind",
                           "kinds", "sort", "sorts", "type", "types", "thing", "things"))
_CNT_VETO = None


def _cnt_veto_rx():
    global _CNT_VETO
    if _CNT_VETO is None:
        import re as _r
        _CNT_VETO = _r.compile(
            r"(?i)(?:\b(?:read|report|transcribe|copy)\b[^.?!]{0,80}?"
            r"\b(?:printed|caption|that states|written)\b"
            r"|\bdoes\s+it\s+say\b|\bit\s+says\b|\bcaption\s+(?:prints|states|says)\b)")
    return _CNT_VETO


def _cnt_rx():
    global _CNT_HOWMANY, _CNT_VERB
    if _CNT_HOWMANY is None:
        import re as _r
        _CNT_HOWMANY = _r.compile(r"(?i)\bhow\s+many\s+" + _CNT_BODY + _CNT_TAIL)
        _CNT_VERB = _r.compile(r"(?i)\bcount(?:ing)?\s+(?:up\s+)?"
                               r"(?:the|all|each|every|only|just)\s+" + _CNT_BODY + _CNT_TAIL)
    return _CNT_HOWMANY, _CNT_VERB


def _in_parens(text, i):
    depth = 0
    for k, ch in enumerate(text):
        if k >= i:
            break
        if ch == "(":
            depth += 1
        elif ch == ")" and depth:
            depth -= 1
    return depth > 0


def _count_population(question):
    if not isinstance(question, str) or not question.strip():
        return None
    try:
        if _cnt_veto_rx().search(question):
            return None
        m = None
        for rx in _cnt_rx():
            for cand in rx.finditer(question):
                if not _in_parens(question, cand.start()):
                    m = cand
                    break
            if m is not None:
                break
    except Exception:
        log.debug("error ignored in _count_population", exc_info=True)
        return None
    if not m:
        return None
    words = [w for w in " ".join(m.group(1).split()).split() if w]
    while words and words[0].lower() in _CNT_LEAD:
        words = words[1:]
    if not words or len(words) > 4:
        return None
    if words[0].lower() in _CNT_BAD_HEAD:
        return None
    phrase = " ".join(words)
    if len(phrase) < 3 or not any(c.isalpha() for c in phrase):
        return None
    return phrase


def _count_zero(val):
    if isinstance(val, bool) or not isinstance(val, (int, float)):
        return False
    return float(val) == 0.0


def _count_proof(crop, pop, ask):
    a1 = ask(crop, _VERIFY_TARGET_ASK % pop, think=0)
    m1 = _target_matches(a1)
    if m1 is not True:
        return m1, (None if a1 is None else str(a1))
    a2 = ask(crop, _VERIFY_TARGET_HELD_ASK % pop, think=0)
    m2 = _target_matches(a2)
    return m2, "%s / %s" % (a1, "None" if a2 is None else a2)


def _target_matches(transcript):
    if transcript is None:
        return None
    t = str(transcript).strip().lower()
    if not t:
        return None
    if t.startswith("y"):
        return True
    if t.startswith("none"):
        return None
    if t.startswith("n"):
        return False
    return None


_REDRAW_WHY_BLANK = "landed on blank paper (nothing is printed inside it)"
_REDRAW_WHY_WRONG = "landed on the wrong spot (what is printed there does not match the answer)"
_REDRAW_ASK = (
    'Earlier, a reader was asked this question about this picture:\n"%s"\n'
    "The answer it read was: %s.\n"
    "But the box it drew to show WHERE it read that %s.\n"
    "Look at the picture again and draw ONE tight box around the exact printed spot that shows "
    "that answer — the number / label / row itself, together with the label right beside it.\n"
    'Output STRICT JSON only: {"box_2d":[ymin,xmin,ymax,xmax]} normalized 0-1000.')
_REDRAW_VERIFY_NUM = ("This is a small cut-out from a bigger picture. Is the number %s printed "
                      "inside this cut-out? Answer yes or no only.")
_REDRAW_VERIFY_TXT = ("This is a small cut-out from a bigger picture. Does it show %s? "
                      "Answer yes or no only.")
_REDRAW_WHY_ABSENT = "does not show %s the reader was counting"
_VERIFY_TARGET_ASK = ("This is a small cut-out from a bigger picture.\n"
                      "Can you see %s in this cut-out? Answer yes or no only.")
_VERIFY_TARGET_HELD_ASK = ("This is a small cut-out from a bigger picture.\n"
                           "Are %s well inside this cut-out, away from its edges? "
                           "Answer yes or no only.")
_REDRAW_ASK_COUNT = (
    'Earlier, a reader was asked this question about this picture:\n"%s"\n'
    "The answer it gave was: %s.\n"
    "But the box it drew to show WHERE it looked %s.\n"
    "Look at the picture again and draw ONE tight box around %s it was supposed to look at — "
    "all of them together, and nothing else.\n"
    'Output STRICT JSON only: {"box_2d":[ymin,xmin,ymax,xmax]} normalized 0-1000.')
_REDRAW_ASK_NOVALUE = (
    'Earlier, a reader was asked this question about this picture:\n"%s"\n'
    "But the box it drew to show WHERE it found the answer %s.\n"
    "Look at the picture again and draw ONE tight box around the exact spot a person would have "
    "to look at to answer that question.\n"
    'Output STRICT JSON only: {"box_2d":[ymin,xmin,ymax,xmax]} normalized 0-1000.')
_REDRAW_ASK_COUNT_NOVALUE = (
    'Earlier, a reader was asked this question about this picture:\n"%s"\n'
    "But the box it drew to show WHERE it looked %s.\n"
    "Look at the picture again and draw ONE tight box around %s it was supposed to look at — "
    "all of them together, and nothing else.\n"
    'Output STRICT JSON only: {"box_2d":[ymin,xmin,ymax,xmax]} normalized 0-1000.')
_VERIFY_QUESTION_ASK = ("This is a small cut-out from a bigger picture.\n"
                        'Someone was asked this about the bigger picture:\n"%s"\n'
                        "Is the place a person would look at to answer that question inside this "
                        "cut-out? Answer yes or no only.")


def _redraw_val_text(val):
    from .question_lint import quotable
    return quotable(val)


def _readloc_redraw(image, question, val, key, box01k, why, pop=None):
    audit = {"why": why, "redrew": False, "verified": None, "kept": False,
             "read_class": "count" if pop else "printed"}
    if pop:
        audit["proof_target"] = pop
    try:
        pass
        from . import evaluation_tree as _A
        from .ops.evidence_grounding import _ask as _fb_ask, _parse as _fb_parse, geom_legal

        def _px(b):
            p = _boxes_of({"boxes": [b]}, image)
            return p[0] if p else None
        vtxt = _redraw_val_text(val)
        p0 = _px(box01k)
        if p0:
            pass
        q0txt = question or "(question unavailable)"
        if pop and vtxt is not None:
            ask = _REDRAW_ASK_COUNT % (q0txt, vtxt, why, pop)
        elif pop:
            ask = _REDRAW_ASK_COUNT_NOVALUE % (q0txt, why, pop)
        elif vtxt is None:
            ask = _REDRAW_ASK_NOVALUE % (q0txt, why)
        else:
            ask = _REDRAW_ASK % (q0txt, vtxt, why)
        txt = _fb_ask(image, ask, think=256)
        bs = _fb_parse("boxes", txt or "")
        ok, _bad = geom_legal("boxes", bs[:1]) if bs else (False, None)
        nb = bs[0] if (bs and ok) else None
        if nb is None:
            audit["note"] = "redraw gave no usable box_2d"
            return None, audit
        audit["redrew"] = True
        p1 = _px(nb)
        if p1:
            pass
        if pop:
            vq = "%s\n+ AND +\n%s" % (_VERIFY_TARGET_ASK % pop, _VERIFY_TARGET_HELD_ASK % pop)
        elif vtxt is None:
            vq = _VERIFY_QUESTION_ASK % q0txt
        elif isinstance(val, (int, float)) and not isinstance(val, bool):
            vq = _REDRAW_VERIFY_NUM % vtxt
        else:
            vq = _REDRAW_VERIFY_TXT % vtxt
        ans, ok = None, None
        try:
            cp, _th = _readloc_crop(image, nb)
            if cp:
                if pop:
                    ok, ans = _count_proof(cp, pop, _fb_ask)
                else:
                    ans = _fb_ask(cp, vq, think=0)
                try:
                    import shutil as _sh
                    _sh.rmtree(os.path.dirname(cp), ignore_errors=True)
                except Exception:
                    log.debug("error ignored in _readloc_redraw", exc_info=True)
                    pass
        except Exception:
            log.debug("error ignored in _readloc_redraw", exc_info=True)
            ans, ok = None, None
        yes = (ok is True) if pop else (bool(ans) and str(ans).strip().lower().startswith("y"))
        audit["verified"] = (True if yes else (False if ans else None))
        if yes and p1:
            audit["kept"] = True
            return nb, audit
        if p1:
            pass
        return None, audit
    except Exception as e:
        log.debug("error ignored in _readloc_redraw", exc_info=True)
        audit["note"] = "redraw loop not run (%s)" % type(e).__name__
        return None, audit


_LOC_UNRELIABLE = ("reader's location self-report unreliable, not shown"
                   ' → ')


def _tag_slug(tag):
    if not tag:
        return ""
    known = {'': "reread"}
    s = known.get(str(tag))
    if s is None:
        import re as _r
        s = _r.sub(r"[^A-Za-z0-9]+", "_", str(tag)).strip("_").lower() or "tag"
    return s


def _readloc_pass(pt, ctx, image, targets, tag="", key_suffix="_loc", numeric_only=True,
                  ev_role=None):
    panels, rows, states = [], [], []
    pre = ("[%s] " % tag) if tag else ""
    try:
        from .ops.evidence_grounding import _ask as _fb_ask
    except Exception as e:
        log.debug("error ignored in _readloc_pass", exc_info=True)
        return panels, [{"out": "read_loc", "value": {"note": '%s%s'
                                                              % (pre, type(e).__name__)}}], states
    for s in targets:
        out = s.get("out") or "read"
        key = "%s%s" % (out, key_suffix) + (("_" + _tag_slug(tag)) if tag else "")
        if key in ctx:
            continue
        val = ctx.get(out)
        label = "read %s" % _fmt(val) if val is not None and not isinstance(val, dict) else "read here"
        box, lstat, ldetail, qtext, pop = None, "none", None, None, None
        try:
            if numeric_only and not _readloc_numeric_target(ctx, pt, s):
                lstat, ldetail = "skip", ' crop_read '
            else:
                q = _readloc_question(ctx, s)
                if not q:
                    lstat, ldetail = "none", ''
                else:
                    qtext = q
                    p = _count_population(q)
                    pop = ("the " + p) if p else None
                    box, lstat, ldetail = _locate_two_votes(image, q)
        except Exception as e:
            log.debug("error ignored in _readloc_pass", exc_info=True)
            box, lstat, ldetail = None, "none", "%s: %s" % (type(e).__name__, e)
        if box is None:
            ctx[key] = {"boxes": None, "unlocated": True, "display_only": True, "note": ldetail}
            rows.append({"out": key, "value": {"note": '%s%s' % (pre, ldetail or "unknown"),
                                               "display_only": True}})
            if lstat != "skip":
                states.append({"loc": lstat, "match": None, "flags": [], "suppressed": False})
            continue
        match, vraw, thumb = None, None, None
        zero_pop = bool(pop) and _count_zero(val)
        if not zero_pop:
            try:
                cp, thumb = _readloc_crop(image, box)
                if cp:
                    if pop:
                        match, vraw = _count_proof(cp, pop, _fb_ask)
                    else:
                        vraw = _fb_ask(cp, _VERIFY_ASK, think=0)
                        match = _value_matches(val, vraw)
                    try:
                        import shutil as _sh
                        _sh.rmtree(os.path.dirname(cp), ignore_errors=True)
                    except Exception:
                        log.debug("error ignored in _readloc_pass", exc_info=True)
                        pass
            except Exception as e:
                log.debug("error ignored in _readloc_pass", exc_info=True)
                match, vraw = None, "%s: %s" % (type(e).__name__, e)
        flags = []
        bad_flag = _FLAG_TARGET if pop else _FLAG_VALUE
        if lstat == "unstable":
            flags.append(_FLAG_UNSTABLE)
        if match is False:
            flags.append(bad_flag)
        elif (match is None and lstat != "unstable"):
            flags.append(_FLAG_UNPROVED)
        state = {"loc": lstat, "match": match, "flags": flags, "suppressed": False}
        states.append(state)
        proved_txt = (('%s AND'
                       % pop[4:]) if pop else '')
        if zero_pop:
            note = (' 0%s → '
                    '54' % pop[4:])
        elif match is True and lstat == "stable":
            note = '%s' % proved_txt
        elif match is True:
            note = '%s%s' % (proved_txt, _FLAG_UNSTABLE)
        elif match is False:
            note = '%s → ' % bad_flag
        elif lstat == "unstable":
            note = '%s → ' % _FLAG_UNSTABLE
        else:
            note = _FLAG_UNPROVED + ' #44 '
        loop_audit, suppressed = None, False
        try:
            from . import evaluation_tree as _A
            _px0 = _boxes_of({"boxes": [box]}, image)
            iv = _A.box_ink_verdict(image, _px0[0]) if _px0 else {"near_blank": False}
            why = None if zero_pop else (
                _REDRAW_WHY_BLANK if iv.get("near_blank")
                else ((_REDRAW_WHY_ABSENT % pop) if (match is False and pop)
                      else (_REDRAW_WHY_WRONG if match is False else None)))
            if why:
                q0 = qtext or _readloc_question(ctx, s) or ""
                nb, loop_audit = _readloc_redraw(image, q0, val, key, box, why, pop=pop)
                if nb is not None:
                    box = nb
                    note += ('%s→ — '
                             '' % why)
                    label += " (redrawn)"
                else:
                    suppressed = True
                    note += '%s→ %s' % (why, _LOC_UNRELIABLE)
        except Exception:
            log.debug("error ignored in _readloc_pass", exc_info=True)
            loop_audit, suppressed = None, False
        state["suppressed"] = bool(suppressed)
        ctx[key] = ({"boxes": None, "display_only": True, "read": _fmt(val),
                     "loc_status": lstat, "value_match": match, "suppressed": True}
                    if suppressed else
                    {"boxes": [box], "display_only": True, "read": _fmt(val),
                     "loc_status": lstat, "value_match": match,
                     "redrawn": bool(loop_audit and loop_audit.get("kept"))})
        row = {"box_2d": [round(float(c), 1) for c in box[:4]], "read": _fmt(val),
               "display_only": True, "note": pre + note, "locate": lstat}
        if suppressed:
            row["not_drawn"] = True
        if loop_audit:
            row["redraw_loop"] = loop_audit
        if ldetail:
            row["locate_detail"] = ldetail
        row["proof"] = ("not_applicable" if zero_pop else
                        {True: "match", False: "mismatch", None: "unreadable"}[match])
        row["read_class"] = "count" if pop else "printed"
        if pop:
            row["proof_target"] = pop
            row["proof_asks"] = 2
        if zero_pop:
            row["zero_population"] = True
        if vraw:
            row["crop_says"] = str(vraw)[:80]
        if thumb:
            row["crop"] = thumb
        rows.append({"out": key, "value": row})
        try:
            px = None if suppressed else _boxes_of({"boxes": [box]}, image)
            if px:
                from . import evaluation_tree as _A
                node = {"id": key} if ev_role is None else {"id": key, "role": ev_role}
                ov = _A.RENDERERS["read_loc"](image, {"boxes": px, "labels": [label]}, node)[0]
                mark = (({True: '', False: '',
                          None: ''} if pop else
                         {True: '', False: '', None: ''})[match]
                        + ('' if lstat == "unstable" else ""))
                panels.append(('%s%s — %s' % (pre, out, mark), ov))
        except Exception:
            log.debug("error ignored in _readloc_pass", exc_info=True)
            pass
    return panels, rows, states


_MINVIS_OPS = ("vlm.ask", "vlm.read_number", "vlm.crop_read", "vlm.read_seq")


def _is_load_bearing(pt):
    if _is_diagnostic_leaf(pt.get("id"), pt):
        return False
    if pt.get("gate"):
        return False
    try:
        return float(pt.get("weight", 1.0)) > 0.0
    except (TypeError, ValueError):
        log.debug("error ignored in _is_load_bearing", exc_info=True)
        return False


def _minvis_targets(pt):
    if not ((_is_load_bearing(pt))):
        return []
    flow = [s for s in (pt.get("flow") or []) if isinstance(s, dict)]
    pages = _page_aliases(flow)
    already = {id(s) for s in _readloc_targets(pt)}
    hits = []
    for s in flow:
        if id(s) in already or s.get("op") not in _MINVIS_OPS:
            continue
        if s.get("op") == "vlm.crop_read" and "boxes" in s:
            continue
        if s.get("image") not in pages or not s.get("question") or not s.get("out"):
            continue
        hits.append(s)
    return hits


def _minvis_expected(ctx, pt, step, seen=None, sole=False):
    from . import ops as _ops
    o = step.get("out")
    if o:
        for c in pt.get("flow") or []:
            if not (isinstance(c, dict) and str(c.get("op", "")).startswith("compare.")):
                continue
            val = c.get("value")
            if not (isinstance(val, str) and (val == o or val.startswith(o + "."))):
                continue
            try:
                return _ops.resolve(ctx, c.get("target"))
            except Exception:
                log.debug("error ignored in _minvis_expected", exc_info=True)
                return None
    if sole and isinstance(seen, dict):
        return seen.get("target")
    return None


def _minvis_actual(val):
    if isinstance(val, dict):
        ans = val.get("answers")
        if isinstance(ans, list) and ans:
            return ans[0] if len(ans) == 1 else ans
        for k in ("answer", "value", "text"):
            if val.get(k) is not None:
                return val[k]
        return None
    return val


def _minvis_seq_text(v):
    if not isinstance(v, (list, tuple)):
        return v
    flat = [x[0] if isinstance(x, (list, tuple)) and len(x) == 1 else x for x in v]
    if any(isinstance(x, (list, tuple, dict)) for x in flat):
        return v
    return " ".join(str(x) for x in flat)


def _minvis_mark(expected, actual):
    if expected is None or actual is None or isinstance(actual, (dict, list, tuple)):
        return "", None
    try:
        fa, fe = float(actual), float(expected)
        ok = abs(fa - fe) < 1e-9
    except (TypeError, ValueError):
        log.debug("error ignored in _minvis_mark", exc_info=True)
        ok = str(actual).strip().lower() == str(expected).strip().lower()
    return ("✅" if ok else "❌"), ("pass" if ok else "fail")


def _minvis_label(out, val, exp, mark):
    if exp is None:
        return '%s %s' % (out, _fmt(val))
    return '%s %s / %s %s' % (out, _fmt(val), _fmt(exp), mark)


def _minvis_pass(pt, ctx, image, targets, seen=None):
    panels, rows = [], []
    try:
        from .ops.evidence_grounding import _ask as _fb_ask, _parse as _fb_parse, geom_legal
        from . import evaluation_tree as _A
        pass
    except Exception:
        log.debug("error ignored in _minvis_pass", exc_info=True)
        return panels, rows
    for s in targets:
        out = s.get("out") or "read"
        key = "%s_box" % out
        if key in ctx:
            continue
        val = _minvis_actual(ctx.get(out))
        exp = _minvis_expected(ctx, pt, s, seen=seen, sole=(len(targets) == 1))
        if val is None and len(targets) == 1 and isinstance(seen, dict):
            val = seen.get("value")
        if s.get("op") == "vlm.read_seq":
            val = _minvis_seq_text(val)
            exp = _minvis_seq_text(exp)
        mark, verdict = _minvis_mark(exp, val)
        box, note = None, None
        try:
            q = _readloc_question(ctx, s)
            if not q:
                note = ''
            else:
                txt = _fb_ask(image, _READLOC_ASK % q, think=256)
                bs = _fb_parse("boxes", txt or "")
                ok, _bad = geom_legal("boxes", bs[:1]) if bs else (False, None)
                box = bs[0] if (bs and ok) else None
                if box is None:
                    note = ' box_2d'
        except Exception as e:
            log.debug("error ignored in _minvis_pass", exc_info=True)
            note = "%s: %s" % (type(e).__name__, e)
        label = _minvis_label(out, val, exp, mark)
        if box is None:
            ctx[key] = {"boxes": None, "unlocated": True, "display_only": True, "note": note}
            rows.append({"out": key, "value": {"note": '[] %s' % (note or "unknown"),
                                               "display_only": True, "read": _fmt(val),
                                               "expected": _fmt(exp)}})
            continue
        base_note = '[] '
        loop_audit, suppressed = None, False
        try:
            px = _boxes_of({"boxes": [box]}, image)
            iv = _A.box_ink_verdict(image, px[0]) if px else {"near_blank": False}
            if iv.get("near_blank"):
                q0 = _readloc_question(ctx, s) or ""
                _p = _count_population(q0)
                nb, loop_audit = _readloc_redraw(image, q0, val, "minvis.%s" % out, box,
                                                 _REDRAW_WHY_BLANK,
                                                 pop=(("the " + _p) if _p else None))
                if nb is not None:
                    box = nb
                    px = _boxes_of({"boxes": [box]}, image)
                    base_note += ('%s→ — '
                                  '' % _REDRAW_WHY_BLANK)
                    label += " (redrawn)"
                else:
                    suppressed = True
                    base_note += '%s→ %s' % (_REDRAW_WHY_BLANK, _LOC_UNRELIABLE)
        except Exception:
            log.debug("error ignored in _minvis_pass", exc_info=True)
            loop_audit, suppressed = None, False
            px = _boxes_of({"boxes": [box]}, image)
        ctx[key] = ({"boxes": None, "display_only": True, "read": _fmt(val),
                     "expected": _fmt(exp), "minvis": True, "suppressed": True}
                    if suppressed else
                    {"boxes": [box], "display_only": True, "read": _fmt(val),
                     "expected": _fmt(exp), "minvis": True,
                     "redrawn": bool(loop_audit and loop_audit.get("kept"))})
        row_val = {
            "box_2d": [round(float(c), 1) for c in box[:4]], "read": _fmt(val),
            "expected": _fmt(exp), "mark": mark or None, "display_only": True,
            "note": base_note}
        if suppressed:
            row_val["not_drawn"] = True
        if loop_audit:
            row_val["redraw_loop"] = loop_audit
        rows.append({"out": key, "value": row_val})
        try:
            if px and not suppressed:
                ov = _A.RENDERERS["read_loc"](image, {"boxes": px, "labels": [label]},
                                              {"id": key})[0]
                panels.append(('%s — %s'
                               % (out, '' if (loop_audit and
                                                              loop_audit.get("kept")) else ""),
                               ov))
                for b in px:
                    pass
        except Exception:
            log.debug("error ignored in _minvis_pass", exc_info=True)
            pass
    return panels, rows


_BOX_CHECK_FLAG = ("box_ring_flag: the read position could not prove itself on a single-box "
                  "cut-out, but this leaf's own compare/code chain had already established its "
                  "value from reads its own guards accepted -- the check is an evaluator, so it "
                  'files a flag and moves no score')

_BOX_HELD_REASON = ("evaluator_refused: the read position could not prove itself and this leaf "
                    "had no independent chain to fall back on -- nothing was measured, so nothing "
                    'is charged to the model; the task is withheld, because a failure of the '
                    "evaluator is never booked as a model failure")

_ADJUDICATION_OP_PREFIXES = ("compare.", "combine.", "logic.", "law.", "grid.", "board.", "check.")
_ADJUDICATION_OPS_EXACT = ("run.code", "compute.verify")
_READ_OP_PREFIXES = ("vlm.", "cv.", "detect.", "ocr.", "compute.", "recognize.", "headcount.", "pose.")


def _is_adjudication_step(op):
    op = str(op or "")
    return op in _ADJUDICATION_OPS_EXACT or op.startswith(_ADJUDICATION_OP_PREFIXES)


_EVALUATOR_REFUSED = "evaluator_refused"


def _box_independent_proof(pt, ctx):
    flow = [s for s in (pt.get("flow") or []) if isinstance(s, dict)]
    if not any(_is_adjudication_step(s.get("op")) for s in flow):
        return False
    for s in flow:
        out = s.get("out")
        if not out or not str(s.get("op") or "").startswith(_READ_OP_PREFIXES):
            continue
        v = ctx.get(out)
        if v is None:
            return False
        if isinstance(v, dict) and any(v.get(k) is True for k in
                                       ("unreadable", "refused", "degenerate", "none", "empty")):
            return False
    return True


def _cropwindow_panels(pt, ctx, image):
    panels = []
    if not image:
        return panels
    try:
        from PIL import Image
        from .ops.evidence_grounding import crop_pad_px, _CROP_PAD
        from . import ops as _ops
        from . import evaluation_tree as _A
        with Image.open(image) as im:
            W, H = im.size
    except Exception:
        log.debug("error ignored in _cropwindow_panels", exc_info=True)
        return panels
    for s in pt.get("flow") or []:
        if not (isinstance(s, dict) and s.get("op") == "vlm.crop_read" and "boxes" in s):
            continue
        try:
            src = _ops.resolve(ctx, s["boxes"]) if isinstance(s["boxes"], str) else s["boxes"]
            if isinstance(src, dict):
                continue
            boxes = list(src or [])
            if not boxes or not all(isinstance(b, (list, tuple)) and len(b) >= 4 for b in boxes):
                continue
            pad = float(s.get("pad", _CROP_PAD))
            px = [list(crop_pad_px(b, W, H, pad)) for b in boxes]
            out = s.get("out") or "crop_read"
            ans = ctx.get(out)
            labels = []
            for i in range(len(px)):
                a = None
                if isinstance(ans, dict) and isinstance(ans.get("answers"), list) \
                        and i < len(ans["answers"]):
                    a = ans["answers"][i]
                labels.append("%d: %s" % (i + 1, "—" if a in (None, "") else str(a)[:18]))
            ov = _A.RENDERERS["read_loc"](image, {"boxes": px, "labels": labels},
                                          {"id": "%s_cropwin" % out})[0]
            panels.append(('%s — pad=%.2f' % (out, pad), ov))
        except Exception:
            log.debug("error ignored in _cropwindow_panels", exc_info=True)
            continue
    return panels


def _reread_flow(pt, ctx):
    from genolympiad import read_policy
    flow = copy.deepcopy(pt.get("flow") or [])
    for s in flow:
        if not (isinstance(s, dict) and str(s.get("op", "")).startswith("vlm.") and s.get("question")):
            continue
        try:
            q = _readloc_question(ctx, s)
        except Exception:
            log.debug("error ignored in _reread_flow", exc_info=True)
            q = None
        if q:
            s["question"] = read_policy.paraphrase(q, 1)
    return flow


def _readloc_cycle(pt, state, ctx, frac, reason, seen, run_once, is_diag):
    res = {"panels": [], "rows": [], "adopted": None, "flag": None, "audit": {}, "refuse": None}
    image = state.get("image")
    if not image:
        return res
    res["panels"] += _cropwindow_panels(pt, ctx, image)
    try:
        mt = _minvis_targets(pt)
        if mt:
            mp, mr = _minvis_pass(pt, ctx, image, mt, seen=seen)
            res["panels"] += mp
            res["rows"] += mr
            res.setdefault("audit", {})["minvis"] = len(mt)
    except Exception as e:
        log.debug("error ignored in _readloc_cycle", exc_info=True)
        res["rows"].append({"out": "read_box", "value": {
            "note": '[] %s' % type(e).__name__}})
    targets = _readloc_targets(pt)
    if not targets:
        return res
    p1, r1, st1 = _readloc_pass(pt, ctx, image, targets)
    res["panels"] += p1
    res["rows"] += r1
    res["audit"].update({"locate": [s["loc"] for s in st1], "match": [s["match"] for s in st1],
                         "reread": False})

    def flags_of(states):
        seen_f, outl = set(), []
        for s in states:
            for f in s["flags"]:
                if f not in seen_f:
                    seen_f.add(f)
                    outl.append(f)
        return outl

    res["flag"] = ''.join(flags_of(st1)) or None
    if not any(s["match"] is False for s in st1):
        return res
    res["audit"]["reread"] = True
    try:
        ctx2, frac2, reason2, seen2 = run_once(_reread_flow(pt, ctx), thinking=True)
    except Exception as e:
        log.debug("error ignored in _readloc_cycle", exc_info=True)
        res["rows"].append({"out": "read_reread", "value": {
            "note": '%s→ 54 '
                    % type(e).__name__}})
        return res
    res["audit"]["reread_frac"] = None if frac2 is None else round(float(frac2), 4)
    res["audit"]["reread_reason"] = reason2
    if reason2 is not None:
        res["rows"].append({"out": "read_reread", "value": {
            "note": '/%s→ 54 ' % reason2}})
        return res
    p2, r2, st2 = _readloc_pass(pt, ctx2, image, targets, tag='')
    res["panels"] += p2
    res["rows"] += r2
    res["audit"]["reread_locate"] = [s["loc"] for s in st2]
    res["audit"]["reread_match"] = [s["match"] for s in st2]
    mode = "verified"
    proved = any(s["match"] is True for s in st2) and not any(s["match"] is False for s in st2)
    take = proved
    res["audit"]["adopt_mode"] = mode
    res["audit"]["reread_proved"] = proved
    res["rows"].append({"out": "read_reread", "value": {
        "note": (' verified' if take else
                 ' verified'),
        "frac_before": None if frac is None else round(float(frac), 4),
        "frac_reread": round(float(frac2), 4),
        "adopt_rule": mode}})
    if take:
        res["adopted"] = (ctx2, frac2, reason2, seen2)
        res["flag"] = ''.join(flags_of(st2)) or None
    else:
        res["flag"] = ''.join(flags_of(st1)) or _FLAG_VALUE
    return res


_GT_KEY_RX = _re_at.compile(r"""gt\s*(?:\[\s*['"]([A-Za-z_]\w*)['"]\s*\]|"""
                            r"""\.get\(\s*['"]([A-Za-z_]\w*)['"])""")
_VERDICT_TEXT_KEYS = ("verdict", "caption", "sentence", "explain")
_VERDICT_SKIP_KEYS = {"frac", "score", "credit", "unreadable"}


def _num(v):
    try:
        f = float(v)
    except (TypeError, ValueError):
        log.debug("error ignored in _num", exc_info=True)
        return str(v)
    if f == int(f) and abs(f) < 1e12:
        return "%d" % int(f) if abs(f) >= 1 or f == 0 else ("%.1f" % f)
    return ("%.3f" % f).rstrip("0").rstrip(".")


def _fracfmt(frac):
    try:
        f = float(frac)
    except (TypeError, ValueError):
        log.debug("error ignored in _fracfmt", exc_info=True)
        return str(frac)
    return "%.1f" % f if f == int(f) else _num(f)


_SCORE_VS_ONE = _re_at.compile(r"^\s*[\d.]+\s+vs\.?\s+1(?:\.0+)?\s*$", _re_at.I)


def _leaf_label_for(pt):
    try:
        from . import evaluation_tree as _A
        return (_A._task_label((pt or {}).get("id")) or "").strip()
    except Exception:
        log.debug("error ignored in _leaf_label_for", exc_info=True)
        return ""


def _runcode_verdict(ctx, pt, frac):
    steps = [s for s in pt.get("flow", [])
             if isinstance(s, dict) and s.get("op") == "run.code" and s.get("out")]
    if not steps:
        return None
    s = steps[-1]
    out = ctx.get(s["out"])
    parts = []
    if isinstance(out, dict):
        for k in _VERDICT_TEXT_KEYS:
            v = out.get(k)
            if isinstance(v, str) and len(v.strip()) >= 12 and " " in v.strip():
                txt = v.strip()
                return txt if "frac" in txt else "%s -> frac %s" % (txt, _fracfmt(frac))
        for k, val in out.items():
            if k in _VERDICT_SKIP_KEYS or len(parts) >= 4:
                continue
            if isinstance(val, bool):
                if val:
                    parts.append("%s true" % k)
            elif isinstance(val, (int, float)):
                parts.append("%s %s" % (k, _num(val)))
            elif isinstance(val, str) and 0 < len(val) <= 32:
                parts.append("%s %s" % (k, val))
            elif (isinstance(val, (list, tuple)) and 0 < len(val) <= 4
                  and all(isinstance(x, (int, float, str)) and not isinstance(x, bool)
                          for x in val)):
                parts.append("%s [%s]" % (k, ", ".join(_num(x) if isinstance(x, (int, float))
                                                       else str(x) for x in val)))
    elif isinstance(out, (int, float)) and not isinstance(out, bool):
        parts.append("%s %s" % (_leaf_label_for(pt) or "reading", _num(out)))
    if not parts:
        return None
    gtd = ctx.get("gt") or {}
    keys = []
    for m in _GT_KEY_RX.finditer(s.get("code") or ""):
        k = m.group(1) or m.group(2)
        if k and k not in keys and isinstance(gtd.get(k), (int, float)) \
                and not isinstance(gtd.get(k), bool):
            keys.append(k)
    txt = ", ".join(parts)
    if keys:
        txt += " vs " + ", ".join("%s %s" % (k, _num(gtd[k])) for k in keys[:3])
    return "%s -> frac %s" % (txt, _fracfmt(frac))


def _is_diagnostic_leaf(pt_id, pt=None):
    try:
        from .engine import _is_diagnostic_leaf as _e
        return _e(pt_id, pt)
    except Exception:
        log.debug("error ignored in _is_diagnostic_leaf", exc_info=True)
        import re as _re2
        if isinstance(pt, dict) and pt.get("d2"):
            return True
        return bool(isinstance(pt_id, str) and _re2.match(r"^d\d+_", pt_id))


def _scored_leaf_fn(point):
    pt = copy.deepcopy(point)
    is_diag = _is_diagnostic_leaf(point.get("id"), point)

    def fn(state):
        from .engine import _run_flow
        from . import ops as _ops
        ctx = {"image": state["image"], "task": state["task"], "gt": state["gt"],
               "_point": pt.get("id")}
        cond = pt.get("only_when")
        if cond is not None and not _ops.resolve(ctx, cond):
            return {"verdict": "skipped (only_when)", "score": None, "detail": f"only_when {cond} falsy",
                    "output": {"skipped": True}}
        try:
            from .engine import live_outage_skip as _los
            _gtflow = ((state.get("task") or {}).get("gt") or {}).get("flow") or []
            _live = {s["out"] for s in _gtflow if isinstance(s, dict) and "out" in s}
            if _live:
                from .ops import fetch as _fetch
                if _los(state.get("task") or {}, pt, state.get("gt") or {}, _live,
                        _fetch.fetch_failed()):
                    return {"verdict": "skipped (live answer-key unavailable)", "score": None,
                            "detail": "the live reference returned nothing for this point's answer "
                                      "key -- an outage on the benchmark's side is never charged "
                                      "to the model (task notes: outage SKIPS the point)",
                            "output": {"skipped": True, "skip_reason": "live_gt_unavailable"}}
        except Exception:
            log.debug("error ignored in _scored_leaf_fn", exc_info=True)
            pass

        def run_once(flow=None, thinking=False):
            """-> (ctx, frac, reason, seen) for ONE execution of this point's flow."""
            c = {"image": state["image"], "task": state["task"], "gt": state["gt"],
                 "_point": pt.get("id")}
            try:
                if thinking:
                    from . import judge_vlm as _readers
                    with _readers.read_mode(thinking=_REREAD_THINK, max_tokens=_REREAD_MAXTOK):
                        f, sn = _run_flow(c, flow if flow is not None else pt["flow"])
                else:
                    f, sn = _run_flow(c, flow if flow is not None else pt["flow"])
                if hasattr(f, "reason"):
                    if getattr(f, "evaluator", False):
                        c["_evaluator_refusal"] = f.reason
                    return c, 0.0, f.reason, sn
                sc = _ops.resolve(c, pt["score"])
                return c, (float(sc) if sc is not None else 0.0), None, sn
            except Exception as e:
                log.debug("error ignored in _scored_leaf_fn", exc_info=True)
                return c, 0.0, f"op_error:{type(e).__name__}:{e}", {}

        ctx, frac, reason, seen = run_once()
        try:
            cycle = _readloc_cycle(pt, state, ctx, frac, reason, seen, run_once, is_diag)
        except Exception as _e:
            log.debug("error ignored in _scored_leaf_fn", exc_info=True)
            cycle = {"panels": [], "adopted": None, "flag": None, "audit": {},
                     "rows": [{"out": "read_loc",
                               "value": {"note": '%s' % type(_e).__name__}}]}
        if cycle.get("adopted"):
            ctx, frac, reason, seen = cycle["adopted"]
        held_reason = (ctx.get("_evaluator_refusal"))
        box_flag = None
        if cycle.get("refuse") and reason is None:
            if _box_independent_proof(pt, ctx):
                box_flag = _BOX_CHECK_FLAG
            elif not is_diag:
                held_reason = _BOX_HELD_REASON
        held = bool(held_reason) and not is_diag
        loc_panels, loc_rows, loc_flag = cycle["panels"], cycle["rows"], cycle.get("flag")
        loc_audit = cycle.get("audit") or {}
        if box_flag:
            loc_flag = (loc_flag + " | " + box_flag) if loc_flag else box_flag
            loc_audit = dict(loc_audit)
            loc_audit["box_ring_flag"] = True
        if pt.get("premise_gate") and pt.get("gate") and not is_diag:
            frac = 1.0 if frac >= 0.5 else 0.0
        v = seen.get("value")
        t = seen.get("target")
        reads = []
        steps = []
        bands = []
        first_q = None
        for s in pt.get("flow", []):
            if not isinstance(s, dict):
                continue
            if str(s.get("op", "")).startswith("vlm.") and s.get("question"):
                qt = _fmt_inline_report(ctx, s["question"])
                if isinstance(qt, str) and qt:
                    if first_q is None:
                        first_q = qt
                    reads.append('[Q: "' + qt + '"]')
                    steps.append({"q": qt})
            o = s.get("out")
            if o and o in ctx:
                reads.append(f"{o}={_fmt(ctx[o])}")
                sval = ctx[o]
                try:
                    from PIL.Image import Image as _PILImage
                    if isinstance(sval, _PILImage):
                        import io as _io, base64 as _b64
                        _th = sval.convert("RGB").copy()
                        _th.thumbnail((220, 220))
                        _buf = _io.BytesIO()
                        _th.save(_buf, "JPEG", quality=60)
                        sval = {"__img__": True, "w": sval.width, "h": sval.height,
                                "b64": _b64.b64encode(_buf.getvalue()).decode("ascii")}
                except Exception:
                    log.debug("error ignored in _scored_leaf_fn", exc_info=True)
                    pass
                steps.append({"out": o, "value": sval, "op": s.get("op")})
            if str(s.get("op", "")).startswith("compare."):
                try:
                    bv = _ops.resolve(ctx, s.get("value"))
                except Exception:
                    log.debug("error ignored in _scored_leaf_fn", exc_info=True)
                    bv = None
                try:
                    bt = _ops.resolve(ctx, s.get("target"))
                except Exception:
                    log.debug("error ignored in _scored_leaf_fn", exc_info=True)
                    bt = None
                bent = {"op": s["op"], "out": s.get("out"),
                        "value_ref": s.get("value") if isinstance(s.get("value"), str) else None,
                        "value": bv, "target": bt,
                        "sub": (ctx.get(s.get("out")) if s.get("out") in ctx else None)}
                for kk in ("core", "margin", "core_abs", "margin_abs", "core_rel", "margin_rel", "tol"):
                    if kk in s:
                        try:
                            bent[kk] = _ops.resolve(ctx, s[kk])
                        except Exception:
                            log.debug("error ignored in _scored_leaf_fn", exc_info=True)
                            bent[kk] = s[kk]
                bands.append(bent)
            if s.get("op") == "run.code" and s.get("call"):
                reads.append(f"[checker: {s['call']}]")
                steps.append({"checker": s["call"]})
        steps.extend(loc_rows)
        rtxt = "  ".join(reads)
        verdict = (f"{_fmt(v)} vs {_fmt(t)}" if v is not None or t is not None
                   else ("crash: " + str(reason) if reason else (rtxt or "scored")))
        if reason is None and ((v is None and t is None) or _SCORE_VS_ONE.match(verdict)):
            try:
                rcv = _runcode_verdict(ctx, pt, frac)
            except Exception:
                log.debug("error ignored in _scored_leaf_fn", exc_info=True)
                rcv = None
            if rcv:
                verdict = rcv
        state_img = None
        panels = _grounded_panels(pt, ctx, image=state.get("image"))
        if panels:
            state_img = _overlay_strip(panels) or panels[0][1]
        for s in pt.get("flow", []):
            if state_img:
                break
            if isinstance(s, dict) and s.get("op") == "headcount.detect_ask":
                cd = ctx.get(s.get("out")) if s.get("out") else None
                if isinstance(cd, dict) and cd.get("boxes") and not cd.get("unreadable"):
                    try:
                        from . import evaluation_tree as _A
                        state_img = _A.RENDERERS["count_boxes"](
                            state["image"], cd, {"id": pt.get("id", "headcount")})[0]
                    except Exception:
                        log.debug("error ignored in _scored_leaf_fn", exc_info=True)
                        state_img = None
                break
        if not state_img:
            for s in pt.get("flow", []):
                if not (isinstance(s, dict) and s.get("op") in _OCR_OUTPUT_OPS):
                    continue
                od = ctx.get(s.get("out")) if s.get("out") else None
                boxes = od.get("word_boxes") if isinstance(od, dict) else None
                if boxes:
                    try:
                        from . import evaluation_tree as _A
                        rout = {"word_boxes": boxes,
                                "consume_patterns": _harvest_consume_patterns(pt.get("flow", []))}
                        state_img = _A.RENDERERS["ocr_consumed"](
                            state["image"], rout, {"id": pt.get("id", "ocr")})[0]
                    except Exception:
                        log.debug("error ignored in _scored_leaf_fn", exc_info=True)
                        state_img = None
                    break
        if loc_panels:
            try:
                stacked = _overlay_strip(([(' (scored evidence)', state_img)] if state_img
                                          else []) + loc_panels)
                state_img = stacked or state_img or loc_panels[0][1]
            except Exception:
                log.debug("error ignored in _scored_leaf_fn", exc_info=True)
                pass
        res = {"verdict": (("diagnostic (not scored): " + verdict) if is_diag else verdict),
               "score": (None if is_diag else round(frac, 4)),
               "detail": (reason if reason else (("flow reads: " + rtxt) if rtxt else None)),
               "output": {"frac": round(frac, 4), "value": _fmt(v), "target": _fmt(t),
                          "reads": rtxt or None, "steps": steps or None, "question": first_q,
                          "bands": bands or None,
                          "read_loc": loc_rows or None,
                          "read_loc_flag": loc_flag,
                          "read_loc_audit": loc_audit or None}}
        if seen.get("target_band_text"):
            res["output"]["target_band"] = seen["target_band_text"]
        if loc_flag:
            res["detail"] = ((res["detail"] + "  ") if res["detail"] else "") + '%s' % loc_flag
        if is_diag:
            res["output"]["diagnostic"] = True
            res["output"]["skip_reason"] = "diagnostic_evidence_only"
        if held:
            res["score"] = None
            res["verdict"] = _EVALUATOR_REFUSED
            res["detail"] = held_reason
            res["output"]["skipped"] = True
            res["output"]["skip_reason"] = _EVALUATOR_REFUSED
            res["output"]["evaluator_refused"] = True
            res["output"]["held_reason"] = held_reason
        if ((pt.get("gate") and not is_diag and not held and isinstance(frac, (int, float)) and float(frac) < 0.999)):
            try:
                from . import check_agreement as _xc
                _xv = _xc.verdict(ctx, seen)
            except Exception:
                log.debug("error ignored in _scored_leaf_fn", exc_info=True)
                _xv = None
            if _xv and _xv["rule"] == _xc.RULE_DECIDE:
                res["gate_demoted"] = _xv["detail"]
                res["output"]["gate_demoted"] = _xv["detail"]
                res["output"]["crosscheck"] = _xv
            elif _xv:
                res["reread_queue"] = _xv["detail"]
                res["output"]["reread_queue"] = _xv["detail"]
                res["output"]["crosscheck"] = _xv
            if not res.get("gate_demoted"):
                try:
                    from . import easy_question as _sg
                    _sv = _sg.verdict(ctx, pt, state["image"])
                except Exception:
                    log.debug("error ignored in _scored_leaf_fn", exc_info=True)
                    _sv = None
                if _sv:
                    res["gate_demoted"] = _sv["detail"]
                    res["output"]["gate_demoted"] = _sv["detail"]
                    res["output"]["scene_no_branch"] = _sv
        if state_img:
            res["state_img"] = state_img
        return res
    return fn


def _fmt(v):
    if v is None:
        return None
    if isinstance(v, (list, set, tuple)):
        try:
            return str(sorted(v))
        except TypeError:
            log.debug("error ignored in _fmt", exc_info=True)
            return str(list(v))
    if isinstance(v, float):
        return f"{v:.3f}"
    if isinstance(v, (str, int, bool)):
        return str(v)
    try:
        if hasattr(v, "size") and hasattr(v, "mode"):
            w, h = v.size
            return f"image {w}x{h}"
        if hasattr(v, "shape"):
            return f"array {tuple(v.shape)}"
    except Exception:
        log.debug("error ignored in _fmt", exc_info=True)
        pass
    return type(v).__name__


def _scored_leaf(point, tid=None):
    is_diag = _is_diagnostic_leaf(point.get("id"), point)
    kind_txt = ("DIAGNOSTIC evidence leaf (d-prefix or `d2` field): read recorded, NOT scored, NOT a gate"
                if is_diag
                else ("premise gate: violated ⇒ item scores 0" if point.get("premise_gate")
                      else ("gate: multiplies the item score" if point.get("gate")
                            else f"scored point, weight {point.get('weight', 1.0):g}")))
    return {"kind": "leaf", "id": (tid or point["id"]), "fn": _scored_leaf_fn(point),
            "weight": float(point.get("weight", 1.0)),
            "gate": (False if is_diag else bool(point.get("gate", False))),
            "diagnostic": is_diag,
            "action": f"run this point's own read→compare flow from the task JSON ({kind_txt})"}


def _task_content_weight(task):
    return sum(float(pt.get("weight", 1.0)) for pt in task.get("scoring", [])
               if not pt.get("gate", False)) or 1.0


def _tree_state_weight(task, n_leaves, cap_frac=0.25):
    if n_leaves <= 0:
        return 0.0
    budget = cap_frac * _task_content_weight(task)
    per = min(0.8, budget / n_leaves)
    import math
    return math.floor(per * 1e4) / 1e4


def _vlm_score_leaf(node_id, question, action, weight, yes_letter="a", state_store=None,
                    only_when_store=None):
    def fn(state):
        c = None
        if only_when_store is not None or state_store is not None:
            c = state["store"].get(only_when_store or state_store) or {}
        if only_when_store is not None and (c.get("unreadable") or c.get("gate_ok") is False):
            return {"verdict": "state unreadable -> dropped", "score": None,
                    "detail": f"{only_when_store} not gate_ok; tree-state leaf excluded"}
        from . import evaluation_tree as _A
        img = ((state["store"].get(state_store) or {}).get("state_img") if state_store else None) \
            or state["image"]
        ans = _A._ask(img, question, retries=2)
        ok, sc = _A._yes_from(ans, yes_letter)
        return {"verdict": ("yes" if ok else "no") if ans is not None else "unread",
                "score": (None if ans is None else float(sc)),
                "detail": f"Q: {question} | raw='{ans}'",
                "output": {"answer": ans, "question": question}, "state_img": img}
    return {"kind": "leaf", "id": node_id, "fn": fn, "weight": float(weight), "gate": False,
            "action": action, "_scored_state_leaf": True}


def _grid_dims(task):
    gt = _gt_of_task(task)
    refs = []
    for pt in task.get("scoring", []):
        for s in pt.get("flow", []):
            if s.get("op") == "compare.grid" and isinstance(s.get("target"), str):
                refs.append(s["target"])
    for ref in refs:
        key = ref.split(".", 1)[1] if ref.startswith("gt.") else ref
        val = gt.get(key)
        if isinstance(val, list) and val and isinstance(val[0], list):
            return len(val), len(val[0])
    return None


def _gt_of_task(task):
    vs = task.get("variants")
    base = dict(task.get("gt", {}) or {})
    if vs:
        base.update(vs[0].get("gt", {}) or {})
    return base


def _d_state_leaves(task, per_w):
    leaves = [_vlm_score_leaf(
        "grid_legible",
        ("Does this image show a clean rectangular GRID of cells (rows and columns with visible "
         "gridlines), each cell holding one value? Answer 'a' if a clean grid is drawn, 'b' if it is "
         "malformed, blank, or not a grid."),
        "tree-state: a clean rectangular grid was drawn", per_w, yes_letter="a")]
    dims = _grid_dims(task)
    if dims:
        r, c = dims
        leaves.append(_vlm_score_leaf(
            "grid_shape",
            (f"Count the rows and columns of the grid in this image. Does the grid have EXACTLY {r} "
             f"rows and {c} columns of cells? Answer 'a' if it is a {r}x{c} grid, 'b' if the number of "
             f"rows or columns is different."),
            f"tree-state: grid is {r}x{c} as demanded", per_w, yes_letter="a"))
    return leaves


_GRID_STATE_OPS = ("cv.binary_grid", "cv.bordered_binary_grid", "cv.color_grid",
                   "cv.stone_grid", "cv.cell_digits")


def _grid_state_tool(task):
    gstep = tstep = None
    for pt in task.get("scoring", []):
        for s in pt.get("flow", []):
            if isinstance(s, dict) and s.get("op") in _GRID_STATE_OPS and gstep is None:
                gstep = dict(s)
                for s2 in pt.get("flow", []):
                    if isinstance(s2, dict) and str(s2.get("op", "")).startswith("compare.") and "target" in s2:
                        tstep = s2
                        break
        if gstep:
            break
    if gstep is None:
        return None

    def fn(ctx, node):
        from . import ops as _ops
        from . import evaluation_tree as _A
        out = {}
        try:
            step = dict(gstep)
            step["image"] = ctx["image"]
            res = _ops.OPS[step["op"]](ctx, step)
            out["read_grid"] = (res or {}).get("grid")
            out["unreadable"] = bool((res or {}).get("unreadable"))
        except Exception as e:
            log.debug("error ignored in _grid_state_tool", exc_info=True)
            return {"unreadable": True, "state_img": ctx["image"],
                    "error": f"{type(e).__name__}:{e}"[:120]}
        try:
            if tstep is not None:
                out["gt_grid"] = _ops.resolve(ctx, tstep["target"])
        except Exception:
            log.debug("error ignored in _grid_state_tool", exc_info=True)
            pass
        if not out.get("gt_grid"):
            rg = out.get("read_grid") or []
            for k, v in sorted((ctx.get("gt") or {}).items()):
                if (isinstance(v, list) and v and all(isinstance(r, (list, str)) for r in v)
                        and len(v) in (len(rg), len(rg) - 1)):
                    vv = [list(r) if isinstance(r, str) else r for r in v]
                    if rg and abs(len(vv[0]) - len(rg[0])) <= 1:
                        out["gt_grid"] = vv
                        out["gt_grid_key"] = k
                        break
        try:
            import numpy as np
            from PIL import Image
            arr = np.asarray(Image.open(ctx["image"]).convert("L")).astype("float32")
            nonbg = np.argwhere(arr < 235)
            if len(nonbg):
                yx0 = nonbg.min(axis=0)
                yx1 = nonbg.max(axis=0) + 1
                out["bbox"] = [int(yx0[1]), int(yx0[0]), int(yx1[1]), int(yx1[0])]
        except Exception:
            log.debug("error ignored in _grid_state_tool", exc_info=True)
            pass
        out["state_img"] = ctx["image"]
        try:
            out["state_img_audit"] = _A.RENDERERS["grid_cells"](
                ctx["image"], out, {"id": "grid_state"})[0]
        except Exception:
            log.debug("error ignored in _grid_state_tool", exc_info=True)
            pass
        return out
    return {"kind": "tool", "id": "grid_state", "fn": fn, "store": "gridstate", "weight": 0.0,
            "action": "grid state: task's own CV grid read vs reference, per-cell overlay"}


def _plan_D(task, make_grid_state=True):
    children = []
    if make_grid_state:
        gtool = _grid_state_tool(task)
        if gtool is not None:
            children.append(gtool)
        n_leaves = 1 + (1 if _grid_dims(task) else 0)
        per_w = _tree_state_weight(task, n_leaves)
        children.extend(_d_state_leaves(task, per_w))
    for pt in task["scoring"]:
        children.append(_scored_leaf(pt))
    return {"kind": "fork", "id": "grid", "action": "D: grid-transcription verification",
            "children": children}


def _plan_E(task):
    return {"kind": "fork", "id": "ocr", "action": "E: text/OCR verification",
            "children": [_scored_leaf(pt) for pt in task["scoring"]]}


_F_VISIBLE_CHECKS = {
    "compute.dice_sum": "dice showing pips",
    "compute.domino_pips": "domino tiles with pips",
    "compute.coin_tally": "coins laid out",
    "compute.pennant_row": "a row of pennant flags",
    "compute.semaphore_row": "semaphore flag figures",
    "compute.flag_hoist": "signal flags on a hoist",
    "compute.turtle_path": "a drawn path / trail",
    "compute.cad_panel": "an engineering drawing panel",
}


def _f_visible_noun(task):
    ops = _task_ops(task)
    for op, noun in _F_VISIBLE_CHECKS.items():
        if op in ops:
            return noun
    return None


def _plan_F(task, make_check_state=True):
    children = []
    noun = _f_visible_noun(task) if make_check_state else None
    if noun:
        per_w = _tree_state_weight(task, 1)
        children.append(_vlm_score_leaf(
            "check_input_legible",
            (f"Does this image clearly show {noun} as a clean, single, unambiguous scene (as opposed to "
             f"a blank, garbled, or doubled figure)? Answer 'a' if {noun} is clearly and cleanly shown, "
             f"'b' if it is blank, garbled, or absent."),
            f"tree-state: {noun} clearly shown (check input legible)", per_w, yes_letter="a"))
    for pt in task["scoring"]:
        children.append(_scored_leaf(pt))
    return {"kind": "fork", "id": "check_net", "action": "F: deterministic check",
            "children": children}


_BUILDERS = {"D": _plan_D, "E": _plan_E, "F": _plan_F}


_OCR_FAMILY = ("ocr.", "table.", "read.matrix", "braille.", "music.read", "cv.cell_digits")


def _wants_ocr_state(task):
    import re
    rx = re.compile(r"transcrib|printed|written|character|digit|label|displayed|value shown", re.I)
    for pt in task.get("scoring", []):
        for s in pt.get("flow", []):
            if not isinstance(s, dict):
                continue
            op = str(s.get("op", ""))
            if op.startswith(_OCR_FAMILY):
                return True
            if op in ("vlm.read_number", "vlm.read_seq", "vlm.read_grid"):
                q = s.get("question")
                if isinstance(q, str) and not q.startswith("gt.") and rx.search(q):
                    return True
            if op == "vlm.ask" and pt.get("id") != "scene_compliance":
                q = s.get("question")
                if isinstance(q, str) and "transcrib" in q.lower():
                    return True
    return False


def _ocr_state_tool():
    def fn(ctx, node):
        from . import evaluation_tree as _A
        try:
            from .readers.table_reader import _rapid
            res, _el = _rapid()(ctx["image"])
            words = []
            for box, txt, conf in (res or []):
                xs = [p[0] for p in box]
                ys = [p[1] for p in box]
                words.append((int(min(xs)), int(min(ys)), int(max(xs)), int(max(ys)),
                              str(txt).strip(), float(conf)))
        except Exception as e:
            log.debug("error ignored in _ocr_state_tool", exc_info=True)
            return {"n_words": 0, "unreadable": True, "state_img": ctx["image"],
                    "error": f"{type(e).__name__}:{e}"[:120]}
        out = {"word_boxes": [(w[0], w[1], w[2], w[3], w[4][:24], round(w[5], 3)) for w in words],
               "n_words": len(words), "unreadable": len(words) == 0}
        try:
            from . import ops as _opsmod
            toks = set()
            for pt in (ctx.get("task") or {}).get("scoring", []):
                for s in pt.get("flow", []):
                    if isinstance(s, dict) and "target" in s and str(s.get("op", "")).startswith("compare."):
                        try:
                            tv = _opsmod.resolve(ctx, s["target"])
                        except Exception:
                            log.debug("error ignored in _ocr_state_tool", exc_info=True)
                            continue
                        if isinstance(tv, (int, float, str)) and str(tv).strip():
                            toks.add(str(tv).strip())
            out["expected_tokens"] = sorted(toks)
        except Exception:
            log.debug("error ignored in _ocr_state_tool", exc_info=True)
            pass
        try:
            state_img = _A.RENDERERS["ocr_words"](ctx["image"], out, {"id": "ocr_state"})[0]
        except Exception:
            log.debug("error ignored in _ocr_state_tool", exc_info=True)
            state_img = ctx["image"]
        out["state_img"] = state_img
        try:
            out["state_img_audit"] = _A.RENDERERS["ocr_words_audit"](
                ctx["image"], out, {"id": "ocr_state"})[0]
        except Exception:
            log.debug("error ignored in _ocr_state_tool", exc_info=True)
            pass
        return out
    return {"kind": "tool", "id": "ocr_state", "fn": fn, "store": "ocr",
            "weight": 0.0, "action": "OCR state: RapidOCR word positions + text overlaid"}


_READ_FAMILIES = [
    (("vlm.grounded_read",), "grounded_read", "grounded reads (propose -> overlay -> verify)"),
    (("vlm.ray_hits",), "ray_hits", "ray-extension intersection reads"),
    (("vlm.crop_read",), "crop_read", "atomic per-crop reads"),
    (("headcount.",), "headcount", "confirmed per-instance headcount"),
    (("detect.",), "detect", "open-vocabulary detection"),
    (("pose.",), "pose", "skeleton/pose estimation"),
    (("ocr.", "table.", "braille.", "music.read"), "text_read", "printed-text reading"),
    (("cv.", "segment.", "rw."), "pixel_measure", "pixel measurement"),
    (("compute.",), "check_net", "deterministic check"),
    (("vlm.read_grid", "vlm.read_number", "vlm.read_seq", "vlm.ask"), "vlm_ask",
     "direct visual questions"),
]


def _root_label(task, template_letter):
    ops = _task_ops(task)
    hits = []
    for pats, slug, phrase in _READ_FAMILIES:
        if any(o == p or (p.endswith(".") and o.startswith(p)) for o in ops for p in pats):
            hits.append((slug, phrase))
    if not hits:
        return None, None
    tail = " -> code adjudication" if "run.code" in ops else ""
    rid = "_and_".join(s for s, _ in hits[:2])
    action = ("reads: " + " + ".join(p for _, p in hits[:3]) + tail
              + " (template %s route)" % template_letter)
    return rid, action


def plan_for_task(task, template=None, diagnostics=True):
    t = template or template_of(task)
    builder = _BUILDERS[t]
    if t in ("D", "F"):
        plan = builder(task, make_state_flag(t, diagnostics))
    else:
        plan = builder(task)
    if diagnostics and _wants_ocr_state(task):
        try:
            plan.setdefault("children", []).insert(0, _ocr_state_tool())
        except Exception:
            log.debug("error ignored in plan_for_task", exc_info=True)
            pass
    try:
        rid, raction = _root_label(task, t)
        if rid:
            plan["id"], plan["action"] = rid, raction
    except Exception:
        log.debug("error ignored in plan_for_task", exc_info=True)
        pass
    return plan


def make_state_flag(t, diagnostics):
    return bool(diagnostics)
