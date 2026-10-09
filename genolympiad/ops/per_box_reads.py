"""Read one question inside each confirmed bounding box and map the answers back to the image."""
import os
import logging

log = logging.getLogger(__name__)


DEFAULT_PAD = 0.20
MIN_PAD_PX = 8.0


def armed(step):
    return bool((isinstance(step, dict) and step.get("in_boxes") is not None))


def crop_rect(box01k, w, h, pad=DEFAULT_PAD):
    """One box in per-mille [ymin, xmin, ymax, xmax] -> a pixel crop rect (x0, y0, x1, y1)."""
    ymin, xmin, ymax, xmax = [float(v) for v in list(box01k)[:4]]
    x0, x1 = min(xmin, xmax) * w / 1000.0, max(xmin, xmax) * w / 1000.0
    y0, y1 = min(ymin, ymax) * h / 1000.0, max(ymin, ymax) * h / 1000.0
    m = max(MIN_PAD_PX, max(x1 - x0, y1 - y0) * max(0.0, float(pad)))
    return (max(0, int(round(x0 - m))), max(0, int(round(y0 - m))),
            min(int(w), int(round(x1 + m))), min(int(h), int(round(y1 + m))))


def _back_pt(pt_in_crop, rect, w, h):
    cy, cx = float(pt_in_crop[0]), float(pt_in_crop[1])
    fx = rect[0] + (cx / 1000.0) * (rect[2] - rect[0])
    fy = rect[1] + (cy / 1000.0) * (rect[3] - rect[1])
    return [fy * 1000.0 / float(h), fx * 1000.0 / float(w)]


def map_back(kind, geom_in_crop, rect, w, h):
    if geom_in_crop is None:
        return None
    if kind == "point":
        return _back_pt(geom_in_crop, rect, w, h)
    if kind in ("line", "ray"):
        a = _back_pt([geom_in_crop[0], geom_in_crop[1]], rect, w, h)
        b = _back_pt([geom_in_crop[2], geom_in_crop[3]], rect, w, h)
        return a + b
    if kind == "circle":
        c = _back_pt([geom_in_crop[0], geom_in_crop[1]], rect, w, h)
        scale = min(rect[2] - rect[0], rect[3] - rect[1]) / float(min(w, h))
        return [c[0], c[1], float(geom_in_crop[2]) * scale]
    if kind == "boxes":
        return [_back_pt([b[0], b[1]], rect, w, h) + _back_pt([b[2], b[3]], rect, w, h)
                for b in geom_in_crop]
    return geom_in_crop


def boxes_of(src):
    if isinstance(src, dict):
        if src.get("refused"):
            return None
        src = src.get("geometry")
    if not src:
        return None
    return [list(b)[:4] for b in src]


def run_in_boxes(image, kind, target, boxes, workdir, read_fn=None, pad=DEFAULT_PAD,
                 on_miss="refuse", **read_kw):
    from PIL import Image
    if read_fn is None:
        from .evidence_grounding import grounded_read as read_fn

    im = image if hasattr(image, "convert") else Image.open(image).convert("RGB")
    w, h = im.size
    if not boxes:
        return {"geometry": None, "per_box": [], "n_boxes": 0, "n_confirmed": 0,
                "confirmed": False, "refused": True, "unreadable": True,
                "refusal": "no_boxes", "subflow": {"enabled": True, "state": "not_exercised",
                                                   "why": "no confirmed boxes reached the "
                                                          "subflow -- nothing was read"}}

    os.makedirs(workdir, exist_ok=True)
    per_box, geoms = [], []
    for i, b in enumerate(boxes):
        rect = crop_rect(b, w, h, pad)
        entry = {"box_index": i, "box": [round(float(v), 1) for v in list(b)[:4]],
                 "crop": list(rect), "geometry": None, "confirmed": False, "refused": True,
                 "refusal": None}
        if rect[2] - rect[0] < 8 or rect[3] - rect[1] < 8:
            entry["refusal"] = "degenerate_crop"
            per_box.append(entry)
            geoms.append(None)
            continue
        wd = os.path.join(workdir, "box%02d" % i)
        os.makedirs(wd, exist_ok=True)
        cp = os.path.join(wd, "crop.png")
        im.crop(rect).save(cp)
        try:
            r = read_fn(cp, kind, target, wd, **read_kw)
        except Exception as e:
            log.debug("error ignored in run_in_boxes", exc_info=True)
            entry["refusal"] = "%s: %s" % (type(e).__name__, str(e)[:160])
            per_box.append(entry)
            geoms.append(None)
            continue
        g = (r or {}).get("geometry")
        conf = bool((r or {}).get("confirmed")) and not (r or {}).get("refused") and g is not None
        entry["confirmed"] = conf
        entry["refused"] = not conf
        entry["refusal"] = None if conf else ((r or {}).get("refusal") or "sub_read_refused")
        entry["geometry"] = map_back(kind, g, rect, w, h) if conf else None
        for k in ("overlay_img", "point_cert", "transcript"):
            if isinstance(r, dict) and r.get(k) is not None:
                entry[k] = r[k]
        per_box.append(entry)
        geoms.append(entry["geometry"])

    n_ok = sum(1 for e in per_box if e["confirmed"])
    strict = str(on_miss or "refuse").strip().lower() != "mark"
    refused = (n_ok == 0) or (strict and n_ok < len(boxes))
    rep = {"enabled": True, "state": "fail" if refused else "pass",
           "on_miss": "refuse" if strict else "mark",
           "n_boxes": len(boxes), "n_confirmed": n_ok,
           "missed": [e["box_index"] for e in per_box if not e["confirmed"]]}
    if refused and strict and n_ok:
        rep["why"] = ("%d of %d boxes could not be read. A headcount that hands back %d numbers "
                      "where the picture holds %d has not measured the other %d -- "
                      "so the read is refused rather than given an under-counted "
                      "number." % (len(boxes) - n_ok, len(boxes), n_ok, len(boxes),
                                   len(boxes) - n_ok))
    return {"geometry": (None if refused else geoms), "per_box": per_box,
            "n_boxes": len(boxes), "n_confirmed": n_ok,
            "confirmed": not refused, "refused": refused, "unreadable": refused,
            "refusal": ("subflow_incomplete" if refused else None), "subflow": rep}


