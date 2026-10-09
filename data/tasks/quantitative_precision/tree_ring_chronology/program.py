# shared code: ringcode

def ring_check(rings, n_target, n_droughts, count_tol):
    """Score the ring count within tolerance times the match of the narrow drought rings."""
    if not isinstance(rings, dict) or rings.get('unreadable') or rings.get('n_rings') is None:
        return {'count_ok': 0.0, 'drought_ok': 0.0, 'joint': 0.0, 'n': None, 'no_read': True}
    n = int(rings['n_rings']); N = int(n_target)
    core = float(count_tol); margin = 2.0 * core
    count_ok = max(0.0, 1.0 - max(0.0, abs(n - N) - core) / max(margin, 1e-9))
    n_narrow = int(rings.get('n_narrow') or 0); K = int(n_droughts)
    if n_narrow == K:
        drought_ok = 1.0
    elif abs(n_narrow - K) == 1:
        drought_ok = 0.35
    else:
        drought_ok = 0.0
    joint = round(count_ok * drought_ok, 4)
    return {'count_ok': round(count_ok, 4), 'drought_ok': round(drought_ok, 4), 'joint': joint,
            'n': n, 'n_narrow': n_narrow, 'no_read': False}

# end of ringcode

# code: read_rings_code

import numpy as np
from genolympiad.ops import resolve


def _load_gray(img):
    from PIL import Image
    if hasattr(img, "convert"):
        arr = np.asarray(img.convert("L"))
    else:
        arr = np.asarray(Image.open(img).convert("L"))
    return arr.astype(np.float32)


def _count_minima(profile, min_depth):
    p = profile
    n = len(p)
    if n < 8:
        return []
    minima = []
    i = 2
    while i < n - 2:
        w0, w1 = max(0, i - 3), min(n, i + 4)
        if p[i] == p[w0:w1].min() and p[i] <= p[w0:w1].max() - min_depth:
            minima.append(i)
            i += 3
        else:
            i += 1
    return minima


def op_radial_rings(ctx, step):
    import cv2
    gray = _load_gray(resolve(ctx, step["image"]))
    H, W = gray.shape[:2]
    n_rays = int(step.get("n_rays", 24))
    min_depth_frac = float(step.get("min_depth_frac", 0.28))
    smooth = int(step.get("smooth", 5))
    r_inner_skip = float(step.get("r_inner_skip", 0.04))
    fail = {"n_rings": None, "gaps_norm": None, "min_gap_ratio": None, "unreadable": True}

    g = cv2.GaussianBlur(gray, (0, 0), 1.2)

    dark = np.clip(255.0 - g, 0, None)
    ys, xs = np.mgrid[0:H, 0:W]
    tot = float(dark.sum()) or 1.0
    cy = float((dark * ys).sum() / tot)
    cx = float((dark * xs).sum() / tot)
    cy = min(max(cy, 0.35 * H), 0.65 * H)
    cx = min(max(cx, 0.35 * W), 0.65 * W)

    r_max = 0.92 * min(H, W) / 2.0
    r0 = r_inner_skip * r_max
    n_samp = int(r_max)
    radii = np.linspace(r0, r_max, n_samp)

    counts = []
    gap_seqs = []
    contrasts = []
    for k in range(n_rays):
        ang = 2.0 * np.pi * k / n_rays
        xr = cx + radii * np.cos(ang)
        yr = cy + radii * np.sin(ang)
        inb = (xr >= 0) & (xr < W) & (yr >= 0) & (yr < H)
        if inb.sum() < 8:
            continue
        prof = g[yr[inb].astype(int), xr[inb].astype(int)].astype(np.float32)
        if smooth > 1:
            ker = np.ones(smooth) / smooth
            prof = np.convolve(prof, ker, mode="same")
        contrast = float(prof.max() - prof.min())
        contrasts.append(contrast)
        if contrast < 15.0:
            continue
        mins = _count_minima(prof, min_depth_frac * contrast)
        counts.append(len(mins))
        if len(mins) >= 2:
            gseq = np.diff(np.array(mins, dtype=float))
            gap_seqs.append(gseq)

    if len(counts) < max(4, n_rays // 3):
        return fail
    if np.median(contrasts) < 15.0:
        return fail

    n_rings = int(round(float(np.median(counts))))
    if n_rings < 2:
        return fail

    if gap_seqs:
        target_len = int(round(float(np.median([len(s) for s in gap_seqs]))))
        aligned = [s for s in gap_seqs if len(s) == target_len]
        if aligned:
            med_gaps = np.median(np.vstack(aligned), axis=0)
        else:
            med_gaps = max(gap_seqs, key=len)
    else:
        med_gaps = np.array([])

    narrow_thr = float(step.get("narrow_thr", 0.62))
    if med_gaps.size:
        gmax = float(med_gaps.max()) or 1.0
        gaps_norm = [round(float(x) / gmax, 3) for x in med_gaps]
        gmed = float(np.median(med_gaps)) or 1.0
        min_gap_ratio = round(float(med_gaps.min()) / gmed, 3)
        flags = [g <= narrow_thr * gmed for g in med_gaps]
        n_narrow = 0
        narrow_ords = []
        i = 0
        while i < len(flags):
            if flags[i]:
                n_narrow += 1
                narrow_ords.append(i + 1)
                while i < len(flags) and flags[i]:
                    i += 1
            else:
                i += 1
    else:
        gaps_norm = []
        min_gap_ratio = None
        n_narrow = 0
        narrow_ords = []

    return {"n_rings": n_rings, "gaps_norm": gaps_norm,
            "min_gap_ratio": min_gap_ratio, "n_narrow": n_narrow,
            "narrow_ords": narrow_ords, "unreadable": False}


def read_rings(image_path):
    """Count the growth rings and the narrow ones along 32 radial rays across the cut."""
    return op_radial_rings({'image': image_path}, {'image': 'image', 'n_rays': 32})

# end of read_rings_code
