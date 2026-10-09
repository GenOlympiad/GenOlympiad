"""Measure ink near the edges of a crop window, so a read is not cut off by its own window."""
import numpy as np
import logging

log = logging.getLogger(__name__)

BAND = 3
BLUR = 17
T_MIN, T_MAX = 8.0, 60.0
H_MIN, H_MAX = 8, 90
FILL_LO, FILL_HI = 0.05, 0.85


def _cv2():
    import cv2
    return cv2


def _otsu(a):
    cv2 = _cv2()
    v = np.clip(a, 0, 255).astype(np.uint8)
    t, _ = cv2.threshold(v, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return float(t)


def _ink(gray, x0, y0, x1, y1):
    cv2 = _cv2()
    reg = gray[y0:y1, x0:x1]
    if reg.size == 0 or min(reg.shape) < 8:
        return None
    bg = cv2.blur(reg, (BLUR, BLUR))
    absres = np.abs(reg - bg)
    T = min(T_MAX, max(T_MIN, _otsu(absres)))
    return absres >= T


def _rect(gray, rect):
    H, W = gray.shape
    x0, y0, x1, y1 = [int(round(float(v))) for v in list(rect)[:4]]
    x0, y0 = max(0, x0), max(0, y0)
    x1, y1 = min(W, x1), min(H, y1)
    return (x0, y0, x1, y1) if (x1 - x0 >= 8 and y1 - y0 >= 8) else None


_PAD = 12


def edge_cut(gray, rect, reach=2):
    try:
        r = _rect(gray, rect)
        if r is None:
            return {}
        x0, y0, x1, y1 = r
        H, W = gray.shape[:2]
        pad = max(int(reach) + 1, _PAD)
        out, worst = {}, 0.0
        for side in ("L", "R", "T", "B"):
            if side in ("L", "R"):
                bx = x0 if side == "L" else x1 - 1
                sx0, sx1 = max(0, bx - pad), min(W, bx + pad + 1)
                band = _ink(gray, sx0, y0, sx1, y1)
                if band is None:
                    continue
                ci = bx - sx0
                inside = band[:, ci]
                far = (band[:, max(0, ci - reach):ci] if side == "L"
                       else band[:, ci + 1:ci + 1 + reach])
            else:
                by = y0 if side == "T" else y1 - 1
                sy0, sy1 = max(0, by - pad), min(H, by + pad + 1)
                band = _ink(gray, x0, sy0, x1, sy1)
                if band is None:
                    continue
                ri = by - sy0
                inside = band[ri, :]
                far = (band[max(0, ri - reach):ri, :] if side == "T"
                       else band[ri + 1:ri + 1 + reach, :])
                far = far.T
            if far.size == 0:
                continue
            has_in = inside.astype(bool)
            n_in = int(has_in.sum())
            out["n_" + side] = n_in
            if n_in == 0:
                out[side] = 0.0
                continue
            f = float(int((has_in & far.astype(bool).any(axis=1)).sum())) / float(n_in)
            out[side] = round(f, 4)
            worst = max(worst, f)
        if not any(k in out for k in ("L", "R", "T", "B")):
            return {}
        out["worst"] = round(worst, 4)
        out["inked_borders"] = sum(1 for k in ("L", "R", "T", "B") if out.get("n_" + k, 0) > 0)
        return out
    except Exception:
        log.debug("error ignored in edge_cut", exc_info=True)
        return {}


