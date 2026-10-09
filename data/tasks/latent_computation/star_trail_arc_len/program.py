# code: arc_span_code

def median_arc_span(image):
    """Fit a circle to each bright star trail and return the median arc they sweep, in degrees."""
    import math, numpy as np, cv2
    if image is None:
        return {'span': None, 'no_read': True}
    if hasattr(image, 'convert'):
        bgr = cv2.cvtColor(np.array(image.convert('RGB')), cv2.COLOR_RGB2BGR)
    elif isinstance(image, np.ndarray):
        bgr = image
    else:
        bgr = cv2.imread(str(image))
    if bgr is None:
        return {'span': None, 'no_read': True}
    H, W = bgr.shape[:2]; diag = float(np.hypot(H, W))
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    threshold = (float(gray.max()) + float(gray.mean())) / 2.0
    mask = (gray > threshold).astype(np.uint8)
    if hasattr(cv2, 'ximgproc'):
        mask = (cv2.ximgproc.thinning((mask * 255).astype(np.uint8)) > 0).astype(np.uint8)
    n_components, labels, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)
    spans = []
    for i in range(1, n_components):
        ys, xs = np.where(labels == i)
        if len(xs) < 20: continue
        w = stats[i, 2]; h = stats[i, 3]
        if math.hypot(w, h) < 0.035 * diag: continue
        x = xs.astype(np.float64); y = ys.astype(np.float64)
        A = np.column_stack([x, y, np.ones_like(x)]); bb = -(x*x + y*y)
        try: sol, *_ = np.linalg.lstsq(A, bb, rcond=None)
        except Exception: continue
        D, E, F = sol; cx = -D/2.0; cy = -E/2.0; r2 = cx*cx + cy*cy - F
        if r2 <= 0: continue
        r = float(np.sqrt(r2)); rr = np.hypot(x-cx, y-cy); residual = float(np.std(rr)/max(r,1e-6))
        if r > 3.0*diag or residual > 0.05: continue
        angles = np.arctan2(y-cy, x-cx); a = np.sort(angles)
        gaps = np.diff(np.concatenate([a, [a[0] + 2*math.pi]])); k = int(gaps.argmax())
        unwrapped = np.concatenate([a[k+1:], a[:k+1] + 2*math.pi]); unwrapped = unwrapped - unwrapped[0]
        lo, hi = np.percentile(unwrapped, [1.0, 99.0]); spans.append(math.degrees(hi - lo))
    if len(spans) < 4:
        return {'span': None, 'no_read': True}
    return {'span': float(np.median(spans)), 'no_read': False}

# end of arc_span_code
