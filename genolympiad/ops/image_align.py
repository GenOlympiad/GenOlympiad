"""Warp a reference picture so its anchor points land on the anchor points found in an image."""
from __future__ import annotations

import numpy as np
from PIL import Image


def _fit_transform(src, dst, mode):
    import cv2
    src = src.astype(np.float64)
    dst = dst.astype(np.float64)
    if mode == "homography":
        if len(src) < 4:
            raise ValueError("homography needs >=4 correspondences")
        M, _ = cv2.findHomography(src, dst, cv2.RANSAC, 5.0)
        return M, "H"
    if mode == "affine":
        if len(src) < 3:
            raise ValueError("affine needs >=3 correspondences")
        M, _ = cv2.estimateAffine2D(src, dst)
        return M, "A"
    if len(src) < 2:
        raise ValueError("similarity needs >=2 correspondences")
    M, _ = cv2.estimateAffinePartial2D(src, dst)
    return M, "A"


def align_reference(ref, ref_anchors, found_anchors, out_size, mode="similarity"):
    """Warp `ref` so `ref_anchors` land on `found_anchors`, on a canvas of `out_size`."""
    import cv2
    M, kind = _fit_transform(ref_anchors, found_anchors, mode)
    arr = np.asarray(ref.convert("RGBA"))
    W, H = out_size
    if kind == "H":
        warped = cv2.warpPerspective(arr, M, (W, H), flags=cv2.INTER_LINEAR)
    else:
        warped = cv2.warpAffine(arr, M, (W, H), flags=cv2.INTER_LINEAR)
    return Image.fromarray(warped, "RGBA")
