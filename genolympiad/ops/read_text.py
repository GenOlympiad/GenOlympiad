"""Read printed text with OCR."""
from __future__ import annotations
from ._base import register, resolve
import logging

log = logging.getLogger(__name__)


def _pil(img):
    from PIL import Image
    if hasattr(img, "convert"):
        return img.convert("RGB")
    import numpy as np
    if isinstance(img, np.ndarray):
        return Image.fromarray(img[..., ::-1] if img.ndim == 3 else img).convert("RGB")
    return Image.open(img).convert("RGB")


def _bgr(img):
    import numpy as np
    import cv2
    if hasattr(img, "convert"):
        return cv2.cvtColor(np.array(img.convert("RGB")), cv2.COLOR_RGB2BGR)
    if isinstance(img, np.ndarray):
        return img
    arr = cv2.imread(str(img))
    return arr


def _path_of(img):
    if isinstance(img, str):
        return img
    return None


def _word_boxes_from(res):
    boxes = list(getattr(res, "boxes", []) or [])
    if boxes:
        out = []
        for b in boxes:
            if len(b) >= 6:
                out.append([int(b[0]), int(b[1]), int(b[2]), int(b[3]), str(b[4]), float(b[5])])
        return out
    out = []
    for w in (getattr(res, "words", []) or []):
        if len(w) >= 3:
            cx, cy = int(w[0]), int(w[1])
            out.append([cx - 14, cy - 8, cx + 14, cy + 8, str(w[2]),
                        float(w[3]) if len(w) > 3 else 0.0])
    return out


@register("ocr.read")
def op_ocr_read(ctx, step):
    from genolympiad.readers.table_reader import read_tables, TableReadResult
    img = resolve(ctx, step["image"])
    path = _path_of(img)
    if path is None:
        import tempfile, os
        fd, path = tempfile.mkstemp(suffix=".png"); os.close(fd)
        _pil(img).save(path)
    try:
        res = read_tables(path, borderless=True)
    except Exception:
        log.debug("error ignored in op_ocr_read", exc_info=True)
        res = TableReadResult(abstain=True, reason="read_tables_raised")
    words = list(getattr(res, "words", []) or [])
    tables = list(getattr(res, "tables", []) or [])
    text = " ".join(w[2] for w in words if len(w) >= 3 and w[2])
    no_read = bool(getattr(res, "abstain", False)) or (not words and not tables)
    wb = _word_boxes_from(res)
    return {"result": res, "words": words, "tables": tables, "text": text,
            "empty": (text == ""), "no_read": no_read, "unreadable": no_read,
            "word_boxes": wb}


