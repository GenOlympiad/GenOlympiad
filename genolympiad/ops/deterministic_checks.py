"""Deterministic scoring checks computed from grounded evidence."""
from __future__ import annotations


from ._base import register, resolve
import logging

log = logging.getLogger(__name__)


def _bgr(img):
    import cv2
    import numpy as np
    if img is None:
        return None
    if hasattr(img, "convert"):
        return cv2.cvtColor(np.asarray(img.convert("RGB")), cv2.COLOR_RGB2BGR)
    return cv2.imread(str(img))


def _pil(img):
    from PIL import Image
    if img is None:
        return None
    if hasattr(img, "convert"):
        return img.convert("RGB")
    return Image.open(str(img)).convert("RGB")


@register("compute.mirror_closure")
def op_mirror_closure(ctx, step):
    pts = resolve(ctx, step.get("points"))
    axes = resolve(ctx, step.get("axes"))
    tol = float(resolve(ctx, step.get("tol", 0.06)) or 0.06)
    cov_n = resolve(ctx, step.get("coverage_n"))
    out = {"frac": 0.0, "unreadable": False, "no_axes": False,
           "n_points": 0, "closed": False}
    if not isinstance(pts, (list, tuple)) or len(pts) == 0:
        out["unreadable"] = True
        return out
    P = []
    for p in pts:
        try:
            P.append((float(p[0]), float(p[1])))
        except (TypeError, ValueError, IndexError):
            log.debug("error ignored in op_mirror_closure", exc_info=True)
            continue
    out["n_points"] = len(P)
    if not P:
        out["unreadable"] = True
        return out
    if not isinstance(axes, (list, tuple)) or len(axes) == 0:
        out["no_axes"] = True
        out["unreadable"] = True
        return out

    def _mirror(p, axis):
        kind, m = str(axis[0]), float(axis[1])
        x, y = p
        return (2 * m - x, y) if kind == "x" else (x, 2 * m - y)

    per_axis = []
    for axis in axes:
        matched = 0
        for p in P:
            mp = _mirror(p, axis)
            if any((mp[0] - q[0]) ** 2 + (mp[1] - q[1]) ** 2 <= tol * tol for q in P):
                matched += 1
        per_axis.append(matched / len(P))
    frac = min(per_axis) if per_axis else 0.0
    if cov_n:
        try:
            frac *= min(1.0, len(P) / float(cov_n))
        except (TypeError, ValueError, ZeroDivisionError):
            log.debug("error ignored in op_mirror_closure", exc_info=True)
            pass
    out["frac"] = round(float(frac), 4)
    out["closed"] = bool(frac >= 0.999)
    return out
