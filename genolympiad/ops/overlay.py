"""Compare an image with a reference overlay and ask the judge VLM about the differences."""
from __future__ import annotations
import hashlib
import os
import tempfile

from ._base import register, resolve
import logging

log = logging.getLogger(__name__)


def _outdir():
    d = os.path.join(tempfile.gettempdir(), "genolympiad_overlay")
    os.makedirs(d, exist_ok=True)
    return d


@register("overlay.compare")
def op_overlay_compare(ctx, step):
    import numpy as np
    from PIL import Image, ImageDraw
    from genolympiad.ops.image_align import align_reference

    img = resolve(ctx, step["image"])
    pil = img.convert("RGB") if hasattr(img, "convert") else Image.open(str(img)).convert("RGB")
    W, H = pil.size

    circles = resolve(ctx, step.get("circles")) or []
    rects = resolve(ctx, step.get("rects")) or []
    polylines = resolve(ctx, step.get("polylines")) or []
    points = resolve(ctx, step.get("points")) or []
    names = resolve(ctx, step.get("labels")) or []
    one_name = resolve(ctx, step.get("label"))
    if one_name and not names:
        names = [str(one_name)] * (len(circles) + len(rects) + len(polylines) + len(points))
    names = [(str(n) if n else None) for n in names]
    ref_anchors = resolve(ctx, step.get("ref_anchors")) or []
    found_anchors = resolve(ctx, step.get("found_anchors")) or []
    mode = resolve(ctx, step.get("mode", "similarity")) or "similarity"
    col_raw = resolve(ctx, step.get("color", [0, 255, 0]))
    invert = isinstance(col_raw, str) and col_raw.strip().lower() == "invert"
    color = (0, 255, 0) if invert else tuple(col_raw or (0, 255, 0))
    width = max(2, int(min(W, H) * float(resolve(ctx, step.get("width_frac", 0.006)) or 0.006)))

    out = {"path": None, "n_circles": len(circles), "n_rects": len(rects),
           "n_polylines": len(polylines), "n_points": len(points),
           "aligned": False, "no_anchors": False}

    src = [[float(p[0]), float(p[1])] for p in ref_anchors]
    dst = [[float(p[0]), float(p[1])] for p in found_anchors]
    n_pair = min(len(src), len(dst))
    src, dst = src[:n_pair], dst[:n_pair]
    if n_pair < 2:
        out["no_anchors"] = True
        p = _save(pil, step, ctx)
        out["path"] = p
        return out

    REF = 1000
    ref_im = Image.new("RGBA", (REF, REF), (0, 0, 0, 0))
    rd = ImageDraw.Draw(ref_im)
    stroke = (int(color[0]), int(color[1]), int(color[2]), 255)
    rw = max(2, int(REF * float(resolve(ctx, step.get("width_frac", 0.006)) or 0.006)))
    for c in circles:
        cxp, cyp, dp = float(c[0]) * REF, float(c[1]) * REF, float(c[2]) * REF
        r = dp / 2.0
        rd.ellipse([cxp - r, cyp - r, cxp + r, cyp + r], outline=stroke, width=rw)
    for rc in rects:
        cxp, cyp = float(rc[0]) * REF, float(rc[1]) * REF
        hw, hh = float(rc[2]) * REF / 2.0, float(rc[3]) * REF / 2.0
        rd.rectangle([cxp - hw, cyp - hh, cxp + hw, cyp + hh], outline=stroke, width=rw)
    for pl in polylines:
        pts = [(float(p[0]) * REF, float(p[1]) * REF) for p in pl if len(p) >= 2]
        if len(pts) >= 2:
            rd.line(pts, fill=stroke, width=rw, joint="curve")
    cs = max(6.0, 0.012 * REF)
    for p in points:
        px_, py_ = float(p[0]) * REF, float(p[1]) * REF
        rd.line([px_ - cs, py_, px_ + cs, py_], fill=stroke, width=rw)
        rd.line([px_, py_ - cs, px_, py_ + cs], fill=stroke, width=rw)

    ref_src = np.array([[p[0] * REF, p[1] * REF] for p in src], dtype=np.float64)
    found_dst = np.array(dst, dtype=np.float64)
    try:
        warped = align_reference(ref_im, ref_src, found_dst, (W, H), mode=mode)
        if invert:
            base = np.asarray(pil.convert("RGB"), dtype=np.uint8)
            mask = np.asarray(warped)[:, :, 3] > 127
            arr = base.copy()
            arr[mask] = 255 - base[mask]
            comp = Image.fromarray(arr, "RGB")
        else:
            comp = Image.alpha_composite(pil.convert("RGBA"), warped).convert("RGB")
        out["aligned"] = True
    except Exception:
        log.debug("error ignored in op_overlay_compare", exc_info=True)
        comp = pil

    out["path"] = _save(comp, step, ctx)
    return out




def _save(im, step, ctx):
    key = f"{resolve(ctx, step.get('image'))}|{id(step)}|{step.get('out','')}"
    h = hashlib.md5(str(key).encode()).hexdigest()[:12]
    path = os.path.join(_outdir(), f"overlay_{h}.png")
    im.save(path)
    return path
