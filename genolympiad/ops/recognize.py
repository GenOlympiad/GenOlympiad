"""Crop operators and single-question reads from the judge VLM, with retries and majority voting."""
from __future__ import annotations
from ._base import register, resolve, majority, as_float
from .. import read_limits as _rguard
import logging

log = logging.getLogger(__name__)

_VLM_READER = None


def set_vlm_reader(fn):
    global _VLM_READER
    _VLM_READER = _rguard.wall_reader(fn, label="vlm reader")


def _reader():
    if _VLM_READER is None:
        raise NotImplementedError(
            "vlm.ask: no reader wired. Call ops.set_vlm_reader(fn) (run_eval --vlm openrouter).")
    return _rguard.wall_reader(_VLM_READER, label="vlm reader")


def _load(img):
    from PIL import Image
    if hasattr(img, "convert"):
        return img
    return Image.open(img).convert("RGB")


@register("crop.full")
def op_crop_full(ctx, step):
    im = _load(resolve(ctx, step["image"]))
    return im


@register("crop.bbox")
def op_crop_bbox(ctx, step):
    im = _load(resolve(ctx, step["image"]))
    x0, y0, x1, y1 = resolve(ctx, step["bbox"])
    W, H = im.size
    if max(x1, y1) <= 1.5:
        x0, y0, x1, y1 = x0 * W, y0 * H, x1 * W, y1 * H
    c = im.crop((int(x0), int(y0), int(x1), int(y1)))
    return c


def _q(ctx, step):
    from ._base import fmt_inline
    return fmt_inline(ctx, step["question"], strict=True)


def _raw_reads(im, q, n, ctx=None, step=None):
    from genolympiad import read_policy
    pol = read_policy.policy_for((ctx or {}).get("task"), (ctx or {}).get("_point"),
                                 (step or {}).get("question"), (step or {}).get("op"))

    from genolympiad import read_limits as _rg
    _scope = _rg.current_scope()

    def call(question):
        try:
            a = _reader()(im, question)
        except NotImplementedError:
            raise
        except Exception:
            log.debug("error ignored in _raw_reads", exc_info=True)
            a = None
        return None if a is None else str(a).strip().lower()

    if pol is None:
        return [call(q) for _ in range(int(n))]

    from genolympiad import judge_vlm as _readers
    votes = int(pol.get("votes", 3))
    stop = bool(pol.get("early_stop_on_agreement", True))
    think = pol.get("thinking_budget", 1024)
    maxtok = pol.get("max_output_tokens", 4096)

    def voted(i):
        with _rg.use_scope(_scope), _readers.read_mode(thinking=think, max_tokens=maxtok):
            return call(read_policy.paraphrase(q, i))

    if not stop or votes < 2:
        return [voted(i) for i in range(votes)]
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=2) as ex:
        reads = list(ex.map(voted, range(2)))
    if reads[0] is not None and reads[0] == reads[1]:
        return reads
    for i in range(2, votes):
        reads.append(voted(i))
        if reads[-1] is not None and reads[-1] == reads[-2]:
            break
    return reads


def _ask_majority(img, q, n, ctx=None, step=None):
    return majority(_raw_reads(_load(img), q, n, ctx, step))


def _blank(v):
    return v is None or (isinstance(v, str) and not v.strip())


def _authored_none_fn():
    try:
        from .evidence_grounding import authored_none
        return authored_none
    except Exception:
        log.debug("error ignored in _authored_none_fn", exc_info=True)
        return None


def _no_read(reason, retried):
    return {"unreadable": True, "empty": True, "no_read": True, "refused": True,
            "refusal": reason, "reask_spent": bool(retried)}


def _held_capture(ans, question, kind):
    return ""


def _refused_coupling_on():
    try:
        from genolympiad import read_limits as _rg
        return False
    except Exception:
        log.debug("error ignored in _refused_coupling_on", exc_info=True)
        return False


def _lints_armed():
    try:
        from genolympiad import read_limits as _rg
        return False
    except Exception:
        log.debug("error ignored in _lints_armed", exc_info=True)
        return False


def _named_no_read(reason, retried):
    try:
        from genolympiad import read_limits as _rg
        hits = _rg.pop_timeouts()
    except Exception:
        log.debug("error ignored in _named_no_read", exc_info=True)
        hits = []
    if hits:
        out = _rg.wall_refusal(hits[-1], "the reader")
        out["reask_spent"] = bool(retried)
        out["wall_timeouts"] = len(hits)
        return out
    return _no_read(reason, retried)


_SCENE_Q_SIG = "does the image actually DEPICT"


def _denumber_scene_q(q):
    import re
    q = re.sub(r"(?i)\bexactly\s+\d+\s*", "", q)
    return q


@register("vlm.ask")
@_rguard.scoped
def op_vlm_ask(ctx, step):
    from genolympiad import read_policy
    from . import question_rules
    q = _q(ctx, step)
    if _SCENE_Q_SIG in q:
        q = _denumber_scene_q(q)
    q = question_rules.with_dash(q, op="vlm.ask",
                               authored_none_fn=_authored_none_fn())
    img = resolve(ctx, step["image"])
    n = step.get("retries", 3)
    a = _ask_majority(img, q, n, ctx, step)
    retried = False
    if _blank(a):
        retried = True
        a = _ask_majority(img, read_policy.retry_wrap(q), n, ctx, step)
    if question_rules.declined(a, q):
        return _no_read("reader DECLINED -- it answered with the decline token this question "
                        "offered it (LAW ), so this window is withheld, not scored", retried)
    if _blank(a):
        return _named_no_read("reader returned no answer", retried)
    _rgd = _held_capture(a, q, "gate")
    if _rgd:
        return _no_read(_rgd, retried)
    return a


def _parse_final_number(s):
    import re
    if s is None:
        return None
    t = str(s)
    t = re.sub(r"(?<=\d),(?=\d{3}(?:\D|$))", "", t)
    t = t.replace(",", ".")
    for pat in (r"\\boxed\{\s*\$?\s*(-?\d+(?:\.\d+)?)",
                r"(?i)final\s*answer[^\d\-]*(-?\d+(?:\.\d+)?)",
                r"(?i)(?:answer|reading|measurement|value|total|result)\s*(?:is|=|:)\s*\$?\s*(-?\d+(?:\.\d+)?)"):
        m = re.search(pat, t)
        if m:
            return float(m.group(1))
    nums = re.findall(r"-?\d+(?:\.\d+)?", t)
    return float(nums[-1]) if nums else None


@register("vlm.read_number")
@_rguard.scoped
def op_vlm_read_number(ctx, step):
    from genolympiad import read_policy
    from . import question_rules
    img = _load(resolve(ctx, step["image"]))
    q = _q(ctx, step)
    q = question_rules.with_dash(q, op="vlm.read_number",
                               authored_none_fn=_authored_none_fn())
    n = int(step.get("retries", 3))

    def _pass(qq):
        raws = list(_raw_reads(img, qq, n, ctx, step))
        vals = [x for x in (_parse_final_number(a) for a in raws) if x is not None]
        return raws, majority(vals)

    raws, v = _pass(q)
    retried = False
    if (v is None and raws and all(_blank(a) for a in raws)):
        retried = True
        raws2, v = _pass(read_policy.retry_wrap(q))
        raws = raws + raws2
    if v is not None:
        return v
    if any(question_rules.declined(a, q) for a in raws):
        return _no_read("reader DECLINED -- it answered with the decline token this question "
                        "offered it (LAW ): withheld, not the model's zero", retried)
    if raws and all(_blank(a) for a in raws):
        return _named_no_read("reader returned no answer to a number read", retried)
    for _a in raws:
        _rgd = _held_capture(_a, q, "value")
        if _rgd:
            return _no_read(_rgd, retried)
    return {"unreadable": True, "empty": True}


@register("vlm.read_seq")
@_rguard.scoped
def op_vlm_read_seq(ctx, step):
    """Read a sequence of n items (majority per position)."""
    import re
    n = int(resolve(ctx, step["n"]))
    digits_only = bool(step.get("digits_only", False))
    as_column = bool(step.get("as_column", False))
    delimiter = step.get("delimiter", None)
    from genolympiad import read_policy
    _img = resolve(ctx, step["image"])
    _q_seq = _q(ctx, step)
    a = _ask_majority(_img, _q_seq, step.get("retries", 3), ctx, step)
    _retried = False
    if _blank(a):
        _retried = True
        a = _ask_majority(_img, read_policy.retry_wrap(_q_seq), step.get("retries", 3), ctx, step)
    if _blank(a):
        return _named_no_read("reader returned no answer to a sequence read", _retried)
    _rgd = _held_capture(a, _q_seq, "seq")
    if _rgd:
        return _no_read(_rgd, _retried)
    if delimiter is not None:
        toks = [t.strip() for t in str(a).strip().split(str(delimiter))]
        toks = [t for t in toks if t]
    else:
        toks = [t for t in re.split(r"[\s,;]+", str(a).strip()) if t]
    if digits_only:
        toks = [t for t in toks if re.fullmatch(r"\d", t)]
    if len(toks) < n:
        return {"unreadable": True, "empty": True, "partial": toks}
    seq = toks[:n]
    return [[t] for t in seq] if as_column else seq


def _parse_grid(text, rows, cols):
    import re
    if text is None:
        return None
    s = str(text)
    grid = []
    for part in re.split(r"[;\n]+", s):
        nums = re.findall(r"-?\d+", part)
        if nums:
            grid.append([int(x) for x in nums])
    if len(grid) == rows and all(len(r) == cols for r in grid):
        return tuple(tuple(r) for r in grid)
    flat = re.findall(r"-?\d+", s)
    if len(flat) == rows * cols:
        return tuple(tuple(int(flat[i * cols + j]) for j in range(cols)) for i in range(rows))
    return None


@register("vlm.read_grid")
@_rguard.scoped
def op_vlm_read_grid(ctx, step):
    from collections import Counter
    img = _load(resolve(ctx, step["image"]))
    shape = resolve(ctx, step.get("shape"))
    rows = int(as_float(resolve(ctx, step.get("rows", shape))) or 0)
    cols = int(as_float(resolve(ctx, step.get("cols", shape))) or 0)
    describe = str(resolve(ctx, step.get("describe", "the matrix")))
    q = (f"The image contains one or more integer matrices written in brackets. Read ONLY {describe}. "
         f"It has exactly {rows} rows and {cols} columns. Report its entries as {rows} rows separated "
         f"by ';', each row {cols} integers separated by single spaces, in reading order "
         f"(left-to-right, then top-to-bottom). Include any minus signs. Output ONLY the numbers and "
         f"';' separators and nothing else — for example '1 2 3; 4 5 6'.")
    grids = []
    _guard_notes = []
    _saw_reading = False
    for _ in range(int(step.get("retries", 3))):
        try:
            a = _reader()(img, q)
        except NotImplementedError:
            raise
        except Exception:
            log.debug("error ignored in op_vlm_read_grid", exc_info=True)
            a = None
        if a is not None:
            _held_note = _held_capture(a, q, "value")
            if _held_note:
                _guard_notes.append(_held_note)
                a = None
            elif str(a).strip():
                _saw_reading = True
        g = _parse_grid(a, rows, cols)
        if g is not None:
            grids.append(g)
    if not grids:
        out = {"values": None, "no_matrix": True, "wrong_shape": True, "illegible": True}
        if _saw_reading:
            if _refused_coupling_on():
                out["illegible_reason"] = (
                    "the reader transcribed a reply but it is not a %dx%d matrix -- the board in "
                    "the image does not read as the requested shape (model side, not an "
                    "evaluator refusal)" % (rows, cols)
                    if _lints_armed() else
                    "reply not classified; no parsable %dx%d matrix -- the answer-side lints "
                    "are not armed on this pass, so this call cannot say whose failure it is"
                    % (rows, cols))
            if _guard_notes:
                out["read_guard"] = list(_guard_notes)
            return out
        if not _refused_coupling_on():
            if _guard_notes:
                out["read_guard"] = list(_guard_notes)
            return out
        out.update(_named_no_read(
            _guard_notes[-1] if _guard_notes else
            ("reader returned no answer at all on any retry for a %dx%d matrix "
             "(no transcript to parse)" % (rows, cols)), False))
        if _guard_notes:
            out["read_guard"] = list(_guard_notes)
        return out
    best = Counter(grids).most_common(1)[0][0]
    return {"values": [list(r) for r in best], "no_matrix": False,
            "wrong_shape": False, "illegible": False}
