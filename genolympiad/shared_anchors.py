"""Share one located anchor between checks of the same task and withhold the task when they disagree."""
from __future__ import annotations

import json
import threading
import logging

log = logging.getLogger(__name__)

IOU_HOLD_BELOW = 0.90
_TL = threading.local()


def _norm(box):
    if isinstance(box, dict):
        box = [box.get("x0"), box.get("y0"), box.get("x1"), box.get("y1")]
    x0, y0, x1, y1 = (float(v) for v in list(box)[:4])
    return (min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1))


def iou(a, b):
    """Intersection over union of two boxes."""
    ax0, ay0, ax1, ay1 = _norm(a)
    bx0, by0, bx1, by1 = _norm(b)
    iw = max(0.0, min(ax1, bx1) - max(ax0, bx0))
    ih = max(0.0, min(ay1, by1) - max(ay0, by0))
    inter = iw * ih
    ua = (ax1 - ax0) * (ay1 - ay0) + (bx1 - bx0) * (by1 - by0) - inter
    if ua <= 0.0:
        return 1.0 if (ax0, ay0, ax1, ay1) == (bx0, by0, bx1, by1) else 0.0
    return inter / ua


def min_pairwise_iou(boxes):
    """Worst agreement in a set of reads of ONE anchor."""
    bs = [b for b in boxes if b is not None]
    if len(bs) < 2:
        return None
    return min(iou(bs[i], bs[j]) for i in range(len(bs)) for j in range(i + 1, len(bs)))


def task_reset():
    _TL.store = {}
    _TL.log = []


def _store():
    s = getattr(_TL, "store", None)
    if s is None:
        s = _TL.store = {}
    return s


def _log():
    lg = getattr(_TL, "log", None)
    if lg is None:
        lg = _TL.log = []
    return lg


def key_of(image, primitive, target, extra=None):
    return json.dumps([str(image), str(primitive), target,
                       {k: extra[k] for k in sorted(extra or {})}],
                      sort_keys=True, ensure_ascii=False, default=str)


def put_shared(k, result):
    return result


def record(check_id, target, box, shared=False):
    """Log one anchor this task landed on, for `disagreements()`."""
    try:
        _log().append({"check": check_id, "target": target,
                       "box": None if box is None else list(_norm(box)), "shared": bool(shared)})
    except Exception:
        log.debug("error ignored in record", exc_info=True)
        pass


def anchors():
    return list(_log())


def disagreements(iou_thr=IOU_HOLD_BELOW):
    by_t = {}
    for r in _log():
        if r.get("box") is None:
            continue
        by_t.setdefault(r["target"], []).append(r)
    out = []
    for t, rs in by_t.items():
        if len({tuple(r["box"]) for r in rs}) < 2:
            continue
        m = min_pairwise_iou([r["box"] for r in rs])
        if m is not None and m < iou_thr:
            out.append({"target": t, "checks": [r["check"] for r in rs],
                        "boxes": [r["box"] for r in rs], "min_iou": round(m, 4)})
    return out


