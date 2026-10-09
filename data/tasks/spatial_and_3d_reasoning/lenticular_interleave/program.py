# shared code: code_ffb38aedb4a7

def one_set_is(pos_a, neg_a, pos_b, neg_b):
    """1 if one column set shows the asked picture and not the other one, else 0."""
    def yes(v):
        return str(v).strip().lower().startswith(("yes", "true"))

    def no(v):
        return str(v).strip().lower().startswith(("no", "false"))
    return 1.0 if ((yes(pos_a) and no(neg_a)) or (yes(pos_b) and no(neg_b))) else 0.0


def _words(t):
    import re
    return re.sub(r"[^A-Z]", "", str(t or "").upper())


def one_set_reads(text_a, text_b, want, other):
    """1 if one column set's text holds the wanted word and not the other, else 0."""
    text_a_letters, text_b_letters = _words(text_a), _words(text_b)
    w, o = _words(want), _words(other)
    return 1.0 if ((w in text_a_letters and o not in text_a_letters) or (w in text_b_letters and o not in text_b_letters)) else 0.0


def read_ok(page):
    """1 if the lens strips were read for the evidence page, else 0."""
    return 0.0 if page.get("no_read") else 1.0

# end of code_ffb38aedb4a7

# code: lattice_ok_code

def _pil(image):
    from PIL import Image
    return image.convert("RGB") if hasattr(image, "convert") else Image.open(str(image)).convert("RGB")


def _arr(image):
    import numpy as np
    return np.asarray(_pil(image)).astype("float32")


def _out_path(image, tag):
    import hashlib
    import os
    import tempfile
    d = os.path.join(tempfile.gettempdir(), "genolympiad_overlay")
    try:
        os.makedirs(d, exist_ok=True)
    except Exception:
        pass
    h = hashlib.md5(("%s|%s" % (str(image), tag)).encode("utf-8", "replace")).hexdigest()[:12]
    return os.path.join(d, "e7blent_%s_%s.png" % (tag, h))


def _memo():
    import sys
    c = getattr(sys, "_lent_memo", None)
    if c is None:
        c = {}
        try:
            sys._lent_memo = c
        except Exception:
            pass
    return c


def _key(image):
    import os
    try:
        p = str(image)
        if os.path.exists(p):
            st = os.stat(p)
            return (p, int(st.st_size), int(st.st_mtime))
    except Exception:
        pass
    return None


def _coarse_pitch(g, hmin=2, hmax=60):
    import numpy as np
    H, W = g.shape
    step = max(1, H // 320)
    gs = g[::step]
    rows = []
    for h in range(hmin, hmax + 1):
        if 4 * h >= W:
            break
        S = float(np.abs(gs[:, h:] - gs[:, :-h]).mean())
        T = float(np.abs(gs[:, 2 * h:] - gs[:, :-2 * h]).mean())
        rows.append((h, S / max(T, 1e-6)))
    if not rows:
        return None, 0.0
    rmax = max(r[1] for r in rows)
    return next(r[0] for r in rows if r[1] >= 0.85 * rmax), rmax


def strip_lattice(image):
    import math
    import numpy as np
    ck, memo = _key(image), _memo()
    if ck is not None and ("lat", ck) in memo:
        return dict(memo[("lat", ck)])
    g = _arr(image).mean(axis=2)
    H, W = g.shape
    h0, rmax = _coarse_pitch(g)
    if h0 is None:
        return {"no_read": True, "reason": "too_narrow"}
    e = np.abs(g[:, 1:] - g[:, :-1]).mean(axis=0)
    med = float(np.median(e))
    thr = med + 0.35 * (float(np.percentile(e, 99)) - med)
    idx = np.arange(1, len(e) - 1)
    ispeak = (e[1:-1] >= e[:-2]) & (e[1:-1] > e[2:]) & (e[1:-1] > thr)
    peaks = list(idx[ispeak])
    mind = max(2, int(round(0.55 * h0)))
    kept = []
    for p in sorted(peaks, key=lambda q: -e[q]):
        if all(abs(p - q) >= mind for q in kept):
            kept.append(int(p))
    kept.sort()
    if len(kept) < 6:
        return {"no_read": True, "reason": "few_edges", "n_edges": len(kept),
                "h0": int(h0), "ratio": round(rmax, 3), "n_strips": len(kept)}
    raw = np.diff(np.array(kept, dtype="float64"))
    gm = float(np.median(raw))
    if gm < 1.5:
        return {"no_read": True, "reason": "pitch_too_small", "n_strips": 0}
    ok = raw[(raw > 0.40 * gm) & (raw < 2.50 * gm)]
    cv = float(ok.std() / (ok.mean() + 1e-6)) if len(ok) >= 4 else 1.0
    def _comb(p0, p1, dp, f0, f1, df, mod):
        b = None
        pp = p0
        while pp <= p1 + 1e-9:
            ph = f0
            while ph <= f1 + 1e-9:
                pos = np.arange(ph % mod if mod else ph, len(e) - 1, pp)
                sc = float(e[np.round(pos).astype(int)].mean())
                if b is None or sc > b[0]:
                    b = (sc, float(pp), float(ph))
                ph += df
            pp += dp
        return b
    coarse = _comb(gm * 0.85, gm * 1.15, max(0.02, gm * 0.01), 0.0, gm, 0.5, gm)
    fine_ = _comb(max(1.5, coarse[1] - gm * 0.02), coarse[1] + gm * 0.02, max(0.002, gm * 0.0015),
                  coarse[2] - 0.6, coarse[2] + 0.6, 0.05, 0.0)
    _, pit, ph0 = fine_
    ph0 = ph0 % pit
    kp = np.array(kept, dtype="float64")
    kidx = np.round((kp - ph0) / pit)
    res = kp - (ph0 + kidx * pit)
    sel = np.abs(res) < 0.35 * pit
    k0 = math.floor((0.0 - ph0) / pit) - 1
    k1 = math.ceil((float(W - 1) - ph0) / pit) + 1
    kk = np.arange(k0, k1 + 1, dtype="float64")
    edges = ph0 + kk * pit
    if int(sel.sum()) >= 8:
        try:
            co = np.polyfit(kidx[sel], kp[sel], 2)
            cand = np.polyval(co, kk)
            dd = np.diff(cand)
            if dd.min() > 0.6 * pit and dd.max() < 1.6 * pit:
                edges = cand
        except Exception:
            pass
    edges = edges[(edges >= -0.5) & (edges <= W - 1.5)]
    if len(edges) < 8:
        return {"no_read": True, "reason": "lattice_too_short", "n_strips": int(len(edges))}
    lattice_res = float(np.abs(res[sel]).mean()) if int(sel.sum()) else 0.0
    on = np.clip(np.round(edges).astype(int), 0, len(e) - 1)
    contrast = float(e[on].mean() / (med + 1e-6))
    bnd = edges + 1.0
    out = {"no_read": False, "h0": int(h0), "ratio": round(rmax, 3), "n_edges": len(kept),
            "n_strips": int(len(bnd) - 1), "pitch": round(pit, 2),
            "pitch_cv": round(cv, 4),
            "edge_contrast": round(contrast, 3), "lattice_res": round(lattice_res, 3),
           "n_pairs": round((len(bnd) - 1) / 2.0, 1), "W": int(W), "H": int(H),
           "bnd": bnd.tolist()}
    if ck is not None:
        memo[("lat", ck)] = dict(out)
    return out


def deinterleave(image, lat):
    import numpy as np
    a = _arr(image)
    W = a.shape[1]
    bnd = np.array(lat["bnd"])
    cols = [[], []]
    for i in range(len(bnd) - 1):
        x0, x1 = int(round(bnd[i])), int(round(bnd[i + 1]))
        x0, x1 = max(0, x0), min(W, x1)
        if x1 - x0 < 2:
            continue
        t = 1 if (x1 - x0) >= 5 else 0
        cols[i % 2].extend(range(x0 + t, x1 - t))
    if len(cols[0]) < 24 or len(cols[1]) < 24:
        return None, None
    return a[:, np.array(cols[0], dtype=int)], a[:, np.array(cols[1], dtype=int)]


def _blocks(g, k=40):
    import numpy as np
    H, W = g.shape
    ys = np.linspace(0, H, k + 1).astype(int)
    xs = np.linspace(0, W, k + 1).astype(int)
    out = np.zeros((k, k), "float32")
    for i in range(k):
        for j in range(k):
            out[i, j] = g[ys[i]:max(ys[i] + 1, ys[i + 1]), xs[j]:max(xs[j] + 1, xs[j + 1])].mean()
    return out


def _highpass(b):
    import numpy as np
    pad = np.pad(b, 1, mode="edge")
    sm = np.zeros_like(b)
    for i in range(3):
        for j in range(3):
            sm += pad[i:i + b.shape[0], j:j + b.shape[1]]
    return b - sm / 9.0


def _subject(a, k=128):
    import numpy as np
    from PIL import Image
    v = np.asarray(Image.fromarray(a.astype("uint8")).resize((k, k), Image.LANCZOS)).astype("float32")
    r = max(2, k // 12)
    ring = np.concatenate([v[:r].reshape(-1, 3), v[-r:].reshape(-1, 3),
                           v[:, :r].reshape(-1, 3), v[:, -r:].reshape(-1, 3)])
    bg = np.median(ring, axis=0)
    d = np.abs(v - bg).sum(axis=2)
    thr = max(20.0, 0.40 * float(np.percentile(d, 99.0)))
    m = d > thr
    area = float(m.mean())
    if area < 0.004:
        return m, None, area
    ys, xs = np.nonzero(m)
    return m, (float(xs.mean()) / k, float(ys.mean()) / k), area


def pair_stats(A, B):
    import math
    import numpy as np
    n = min(A.shape[1], B.shape[1])
    A, B = A[:, :n], B[:, :n]
    ga, gb = A.mean(axis=2), B.mean(axis=2)
    ba, bb = _blocks(ga), _blocks(gb)
    ha, hb = _highpass(ba), _highpass(bb)
    ka, kb = _blocks(A[:, :, 0]), _blocks(B[:, :, 0])
    unexp = []
    for c in range(3):
        x = _blocks(A[:, :, c]).ravel()
        y = _blocks(B[:, :, c]).ravel()
        sx, sy = float(x.std()), float(y.std())
        if sx < 1e-4 or sy < 1e-4:
            unexp.append(1.0)
            continue
        r = float(((x - x.mean()) * (y - y.mean())).mean() / (sx * sy))
        unexp.append(math.sqrt(max(0.0, 1.0 - r * r)))
    ma, ca, aa = _subject(A)
    mb, cb, ab = _subject(B)
    uni = float((ma | mb).sum())
    iou = float((ma & mb).sum()) / uni if uni > 0 else 1.0
    if ca is None or cb is None:
        dist = 0.0
    else:
        dist = math.hypot(ca[0] - cb[0], ca[1] - cb[1])
    return {"mad": round(float(np.abs(ga - gb).mean()), 2),
            "hp_a": round(float(ha.std()), 3), "hp_b": round(float(hb.std()), 3),
            "iou": round(iou, 4), "unexplained": round(float(sum(unexp) / 3.0), 4),
            "subj_dist": round(dist, 4),
            "cx_a": None if ca is None else round(ca[0], 3),
            "cy_a": None if ca is None else round(ca[1], 3),
            "cx_b": None if cb is None else round(cb[0], 3),
            "cy_b": None if cb is None else round(cb[1], 3),
            "area_a": round(aa, 4), "area_b": round(ab, 4),
            "wa": int(A.shape[1]), "wb": int(B.shape[1])}


def interleave_read(image):
    """Find the lens strips, split the image into its two column sets and compare them."""
    import math
    from PIL import Image
    lat = strip_lattice(image)
    if lat.get("no_read"):
        out = {"no_read": True}
        out.update({k: v for k, v in lat.items() if k != "bnd"})
        return out
    A, B = deinterleave(image, lat)
    if A is None:
        return {"no_read": True, "reason": "thin_column_sets", "n_strips": lat.get("n_strips", 0)}
    out = {"no_read": False}
    out.update({k: v for k, v in lat.items() if k != "bnd"})
    out.update(pair_stats(A, B))
    H, W = int(lat["H"]), int(lat["W"])
    pa, pb = _out_path(image, "setA"), _out_path(image, "setB")
    Image.fromarray(A.astype("uint8")).resize((W, H), Image.LANCZOS).save(pa)
    Image.fromarray(B.astype("uint8")).resize((W, H), Image.LANCZOS).save(pb)
    out["path_a"], out["path_b"] = pa, pb
    return out


def lattice_ok(stats):
    """1 if enough regular, high contrast lens strips were found, else 0."""
    if stats.get("no_read"):
        return 0.0
    return 1.0 if (stats.get("n_strips", 0) >= 12 and float(stats.get("ratio", 0)) >= 1.6
                   and float(stats.get("edge_contrast", 0)) >= 3.0) else 0.0


def both_phases_ok(stats, floor=1.5):
    """1 if both column sets carry real image detail, else 0."""
    if stats.get("no_read"):
        return 0.0
    return 1.0 if (float(stats.get("hp_a", 0)) >= floor and float(stats.get("hp_b", 0)) >= floor) else 0.0


def distinct_ok(stats, iou_max=0.78, unexp_min=0.30):
    """1 if the two column sets show clearly different pictures, else 0."""
    if stats.get("no_read"):
        return 0.0
    return 1.0 if (float(stats.get("iou", 1.0)) <= iou_max
                   and float(stats.get("unexplained", 0.0)) >= unexp_min) else 0.0


def same_area_ok(stats, core=0.15, marg=0.34):
    """How close the two pictures' subjects sit, full credit when nearly coincident."""
    if stats.get("no_read"):
        return 0.0
    d = float(stats.get("subj_dist", 1.0))
    if d <= core:
        return 1.0
    if d >= marg:
        return 0.0
    return round((marg - d) / (marg - core), 4)


def fine_and_even(stats, pairs_full=25.0, pairs_zero=10.0, cv_core=0.12, cv_marg=0.32):
    """Fine strip count score times even strip pitch score."""
    if stats.get("no_read"):
        return 0.0
    p = float(stats.get("n_pairs", 0.0))
    fine = 1.0 if p >= pairs_full else (0.0 if p <= pairs_zero else (p - pairs_zero) / (pairs_full - pairs_zero))
    cv = float(stats.get("pitch_cv", 1.0))
    even = 1.0 if cv <= cv_core else (0.0 if cv >= cv_marg else (cv_marg - cv) / (cv_marg - cv_core))
    return round(fine * even, 4)


def evidence_page(image, tag="lent"):
    import numpy as np
    from PIL import Image, ImageDraw
    m = interleave_read(image)
    src = _pil(image)
    W, H = src.size
    scale = 520.0 / float(W)
    sw, sh = 520, max(1, int(H * scale))
    top = Image.new("RGB", (sw, sh + 56), (255, 255, 255))
    top.paste(src.resize((sw, sh)), (0, 56))
    d = ImageDraw.Draw(top)
    if not m.get("no_read"):
        lat = strip_lattice(image)
        bnd = [b for b in lat["bnd"] if 0 <= b < W]
        for b in bnd:
            x = b * scale
            d.line([(x, 46), (x, 56 + 0.06 * sh)], fill=(230, 0, 190), width=1)
        if len(bnd) > 8:
            i = len(bnd) // 2
            x0, x1 = bnd[i] * scale, bnd[i + 1] * scale
            d.line([(x0, 30), (x1, 30)], fill=(230, 0, 190), width=3)
            d.line([(x0, 24), (x0, 46)], fill=(230, 0, 190), width=2)
            d.line([(x1, 24), (x1, 46)], fill=(230, 0, 190), width=2)
            d.text((min(sw - 150, x1 + 8), 20), "one strip = %.1f px" % float(m["pitch"]),
                   fill=(150, 0, 120))
        d.text((6, 4), "magenta ticks = every measured strip boundary", fill=(150, 0, 120))
    pan = 260
    board = Image.new("RGB", (sw, top.height + pan + 92), (255, 255, 255))
    board.paste(top, (0, 0))
    d2 = ImageDraw.Draw(board)
    y0 = top.height + 22
    if m.get("no_read"):
        d2.text((10, y0), "NO STRIP LATTICE FOUND (%s)" % str(m.get("reason")), fill=(200, 0, 0))
    else:
        for k, (p, name) in enumerate(((m["path_a"], "COLUMN SET 1"), (m["path_b"], "COLUMN SET 2"))):
            sub = Image.open(p).convert("RGB").resize((pan - 16, pan - 16))
            x = 8 + k * (pan)
            board.paste(sub, (x, y0))
            d2.rectangle([x - 1, y0 - 1, x + pan - 16, y0 + pan - 16], outline=(230, 0, 190))
            d2.text((x, y0 + pan - 12), name, fill=(30, 30, 30))
        d2.text((8, y0 + pan + 6),
                "strips=%d  pairs=%.1f  pitch_cv=%.3f  edges x%.1f"
                % (m["n_strips"], m["n_pairs"], m["pitch_cv"], m["edge_contrast"]), fill=(30, 30, 30))
        d2.text((8, y0 + pan + 22),
                "subject overlap iou=%.3f  colour-map residual=%.3f" % (m["iou"], m["unexplained"]),
                fill=(30, 30, 30))
        d2.text((8, y0 + pan + 38),
                "subject centroid gap=%.3f  set energies %.2f / %.2f"
                % (m["subj_dist"], m["hp_a"], m["hp_b"]), fill=(30, 30, 30))
    p = _out_path(image, tag)
    board.save(p)
    out = dict(m)
    out["path"] = p
    return out

# end of lattice_ok_code

# code: evidence_page_marked_code

def _pil(image):
    from PIL import Image
    return image.convert("RGB") if hasattr(image, "convert") else Image.open(str(image)).convert("RGB")


def _arr(image):
    import numpy as np
    return np.asarray(_pil(image)).astype("float32")


def _out_path(image, tag):
    import hashlib
    import os
    import tempfile
    d = os.path.join(tempfile.gettempdir(), "genolympiad_overlay")
    try:
        os.makedirs(d, exist_ok=True)
    except Exception:
        pass
    h = hashlib.md5(("%s|%s" % (str(image), tag)).encode("utf-8", "replace")).hexdigest()[:12]
    return os.path.join(d, "e7blent_%s_%s.png" % (tag, h))


def _memo():
    import sys
    c = getattr(sys, "_lent_memo", None)
    if c is None:
        c = {}
        try:
            sys._lent_memo = c
        except Exception:
            pass
    return c


def _key(image):
    import os
    try:
        p = str(image)
        if os.path.exists(p):
            st = os.stat(p)
            return (p, int(st.st_size), int(st.st_mtime))
    except Exception:
        pass
    return None


def _coarse_pitch(g, hmin=2, hmax=60):
    import numpy as np
    H, W = g.shape
    step = max(1, H // 320)
    gs = g[::step]
    rows = []
    for h in range(hmin, hmax + 1):
        if 4 * h >= W:
            break
        S = float(np.abs(gs[:, h:] - gs[:, :-h]).mean())
        T = float(np.abs(gs[:, 2 * h:] - gs[:, :-2 * h]).mean())
        rows.append((h, S / max(T, 1e-6)))
    if not rows:
        return None, 0.0
    rmax = max(r[1] for r in rows)
    return next(r[0] for r in rows if r[1] >= 0.85 * rmax), rmax


def strip_lattice(image):
    import math
    import numpy as np
    ck, memo = _key(image), _memo()
    if ck is not None and ("lat", ck) in memo:
        return dict(memo[("lat", ck)])
    g = _arr(image).mean(axis=2)
    H, W = g.shape
    h0, rmax = _coarse_pitch(g)
    if h0 is None:
        return {"no_read": True, "reason": "too_narrow"}
    e = np.abs(g[:, 1:] - g[:, :-1]).mean(axis=0)
    med = float(np.median(e))
    thr = med + 0.35 * (float(np.percentile(e, 99)) - med)
    idx = np.arange(1, len(e) - 1)
    ispeak = (e[1:-1] >= e[:-2]) & (e[1:-1] > e[2:]) & (e[1:-1] > thr)
    peaks = list(idx[ispeak])
    mind = max(2, int(round(0.55 * h0)))
    kept = []
    for p in sorted(peaks, key=lambda q: -e[q]):
        if all(abs(p - q) >= mind for q in kept):
            kept.append(int(p))
    kept.sort()
    if len(kept) < 6:
        return {"no_read": True, "reason": "few_edges", "n_edges": len(kept),
                "h0": int(h0), "ratio": round(rmax, 3), "n_strips": len(kept)}
    raw = np.diff(np.array(kept, dtype="float64"))
    gm = float(np.median(raw))
    if gm < 1.5:
        return {"no_read": True, "reason": "pitch_too_small", "n_strips": 0}
    ok = raw[(raw > 0.40 * gm) & (raw < 2.50 * gm)]
    cv = float(ok.std() / (ok.mean() + 1e-6)) if len(ok) >= 4 else 1.0
    def _comb(p0, p1, dp, f0, f1, df, mod):
        b = None
        pp = p0
        while pp <= p1 + 1e-9:
            ph = f0
            while ph <= f1 + 1e-9:
                pos = np.arange(ph % mod if mod else ph, len(e) - 1, pp)
                sc = float(e[np.round(pos).astype(int)].mean())
                if b is None or sc > b[0]:
                    b = (sc, float(pp), float(ph))
                ph += df
            pp += dp
        return b
    coarse = _comb(gm * 0.85, gm * 1.15, max(0.02, gm * 0.01), 0.0, gm, 0.5, gm)
    fine_ = _comb(max(1.5, coarse[1] - gm * 0.02), coarse[1] + gm * 0.02, max(0.002, gm * 0.0015),
                  coarse[2] - 0.6, coarse[2] + 0.6, 0.05, 0.0)
    _, pit, ph0 = fine_
    ph0 = ph0 % pit
    kp = np.array(kept, dtype="float64")
    kidx = np.round((kp - ph0) / pit)
    res = kp - (ph0 + kidx * pit)
    sel = np.abs(res) < 0.35 * pit
    k0 = math.floor((0.0 - ph0) / pit) - 1
    k1 = math.ceil((float(W - 1) - ph0) / pit) + 1
    kk = np.arange(k0, k1 + 1, dtype="float64")
    edges = ph0 + kk * pit
    if int(sel.sum()) >= 8:
        try:
            co = np.polyfit(kidx[sel], kp[sel], 2)
            cand = np.polyval(co, kk)
            dd = np.diff(cand)
            if dd.min() > 0.6 * pit and dd.max() < 1.6 * pit:
                edges = cand
        except Exception:
            pass
    edges = edges[(edges >= -0.5) & (edges <= W - 1.5)]
    if len(edges) < 8:
        return {"no_read": True, "reason": "lattice_too_short", "n_strips": int(len(edges))}
    lattice_res = float(np.abs(res[sel]).mean()) if int(sel.sum()) else 0.0
    on = np.clip(np.round(edges).astype(int), 0, len(e) - 1)
    contrast = float(e[on].mean() / (med + 1e-6))
    bnd = edges + 1.0
    out = {"no_read": False, "h0": int(h0), "ratio": round(rmax, 3), "n_edges": len(kept),
            "n_strips": int(len(bnd) - 1), "pitch": round(pit, 2),
            "pitch_cv": round(cv, 4),
            "edge_contrast": round(contrast, 3), "lattice_res": round(lattice_res, 3),
           "n_pairs": round((len(bnd) - 1) / 2.0, 1), "W": int(W), "H": int(H),
           "bnd": bnd.tolist()}
    if ck is not None:
        memo[("lat", ck)] = dict(out)
    return out


def deinterleave(image, lat):
    import numpy as np
    a = _arr(image)
    W = a.shape[1]
    bnd = np.array(lat["bnd"])
    cols = [[], []]
    for i in range(len(bnd) - 1):
        x0, x1 = int(round(bnd[i])), int(round(bnd[i + 1]))
        x0, x1 = max(0, x0), min(W, x1)
        if x1 - x0 < 2:
            continue
        t = 1 if (x1 - x0) >= 5 else 0
        cols[i % 2].extend(range(x0 + t, x1 - t))
    if len(cols[0]) < 24 or len(cols[1]) < 24:
        return None, None
    return a[:, np.array(cols[0], dtype=int)], a[:, np.array(cols[1], dtype=int)]


def _blocks(g, k=40):
    import numpy as np
    H, W = g.shape
    ys = np.linspace(0, H, k + 1).astype(int)
    xs = np.linspace(0, W, k + 1).astype(int)
    out = np.zeros((k, k), "float32")
    for i in range(k):
        for j in range(k):
            out[i, j] = g[ys[i]:max(ys[i] + 1, ys[i + 1]), xs[j]:max(xs[j] + 1, xs[j + 1])].mean()
    return out


def _highpass(b):
    import numpy as np
    pad = np.pad(b, 1, mode="edge")
    sm = np.zeros_like(b)
    for i in range(3):
        for j in range(3):
            sm += pad[i:i + b.shape[0], j:j + b.shape[1]]
    return b - sm / 9.0


def _subject(a, k=128):
    import numpy as np
    from PIL import Image
    v = np.asarray(Image.fromarray(a.astype("uint8")).resize((k, k), Image.LANCZOS)).astype("float32")
    r = max(2, k // 12)
    ring = np.concatenate([v[:r].reshape(-1, 3), v[-r:].reshape(-1, 3),
                           v[:, :r].reshape(-1, 3), v[:, -r:].reshape(-1, 3)])
    bg = np.median(ring, axis=0)
    d = np.abs(v - bg).sum(axis=2)
    thr = max(20.0, 0.40 * float(np.percentile(d, 99.0)))
    m = d > thr
    area = float(m.mean())
    if area < 0.004:
        return m, None, area
    ys, xs = np.nonzero(m)
    return m, (float(xs.mean()) / k, float(ys.mean()) / k), area


def pair_stats(A, B):
    import math
    import numpy as np
    n = min(A.shape[1], B.shape[1])
    A, B = A[:, :n], B[:, :n]
    ga, gb = A.mean(axis=2), B.mean(axis=2)
    ba, bb = _blocks(ga), _blocks(gb)
    ha, hb = _highpass(ba), _highpass(bb)
    ka, kb = _blocks(A[:, :, 0]), _blocks(B[:, :, 0])
    unexp = []
    for c in range(3):
        x = _blocks(A[:, :, c]).ravel()
        y = _blocks(B[:, :, c]).ravel()
        sx, sy = float(x.std()), float(y.std())
        if sx < 1e-4 or sy < 1e-4:
            unexp.append(1.0)
            continue
        r = float(((x - x.mean()) * (y - y.mean())).mean() / (sx * sy))
        unexp.append(math.sqrt(max(0.0, 1.0 - r * r)))
    ma, ca, aa = _subject(A)
    mb, cb, ab = _subject(B)
    uni = float((ma | mb).sum())
    iou = float((ma & mb).sum()) / uni if uni > 0 else 1.0
    if ca is None or cb is None:
        dist = 0.0
    else:
        dist = math.hypot(ca[0] - cb[0], ca[1] - cb[1])
    return {"mad": round(float(np.abs(ga - gb).mean()), 2),
            "hp_a": round(float(ha.std()), 3), "hp_b": round(float(hb.std()), 3),
            "iou": round(iou, 4), "unexplained": round(float(sum(unexp) / 3.0), 4),
            "subj_dist": round(dist, 4),
            "cx_a": None if ca is None else round(ca[0], 3),
            "cy_a": None if ca is None else round(ca[1], 3),
            "cx_b": None if cb is None else round(cb[0], 3),
            "cy_b": None if cb is None else round(cb[1], 3),
            "area_a": round(aa, 4), "area_b": round(ab, 4),
            "wa": int(A.shape[1]), "wb": int(B.shape[1])}


def interleave_read(image):
    import math
    from PIL import Image
    lat = strip_lattice(image)
    if lat.get("no_read"):
        out = {"no_read": True}
        out.update({k: v for k, v in lat.items() if k != "bnd"})
        return out
    A, B = deinterleave(image, lat)
    if A is None:
        return {"no_read": True, "reason": "thin_column_sets", "n_strips": lat.get("n_strips", 0)}
    out = {"no_read": False}
    out.update({k: v for k, v in lat.items() if k != "bnd"})
    out.update(pair_stats(A, B))
    H, W = int(lat["H"]), int(lat["W"])
    pa, pb = _out_path(image, "setA"), _out_path(image, "setB")
    Image.fromarray(A.astype("uint8")).resize((W, H), Image.LANCZOS).save(pa)
    Image.fromarray(B.astype("uint8")).resize((W, H), Image.LANCZOS).save(pb)
    out["path_a"], out["path_b"] = pa, pb
    return out


def lattice_ok(m):
    if m.get("no_read"):
        return 0.0
    return 1.0 if (m.get("n_strips", 0) >= 12 and float(m.get("ratio", 0)) >= 1.6
                   and float(m.get("edge_contrast", 0)) >= 3.0) else 0.0


def both_phases_ok(m, floor=1.5):
    if m.get("no_read"):
        return 0.0
    return 1.0 if (float(m.get("hp_a", 0)) >= floor and float(m.get("hp_b", 0)) >= floor) else 0.0


def distinct_ok(m, iou_max=0.78, unexp_min=0.30):
    if m.get("no_read"):
        return 0.0
    return 1.0 if (float(m.get("iou", 1.0)) <= iou_max
                   and float(m.get("unexplained", 0.0)) >= unexp_min) else 0.0


def same_area_ok(m, core=0.15, marg=0.34):
    if m.get("no_read"):
        return 0.0
    d = float(m.get("subj_dist", 1.0))
    if d <= core:
        return 1.0
    if d >= marg:
        return 0.0
    return round((marg - d) / (marg - core), 4)


def fine_and_even(m, pairs_full=25.0, pairs_zero=10.0, cv_core=0.12, cv_marg=0.32):
    if m.get("no_read"):
        return 0.0
    p = float(m.get("n_pairs", 0.0))
    fine = 1.0 if p >= pairs_full else (0.0 if p <= pairs_zero else (p - pairs_zero) / (pairs_full - pairs_zero))
    cv = float(m.get("pitch_cv", 1.0))
    even = 1.0 if cv <= cv_core else (0.0 if cv >= cv_marg else (cv_marg - cv) / (cv_marg - cv_core))
    return round(fine * even, 4)


def evidence_page(image, tag="lent"):
    import numpy as np
    from PIL import Image, ImageDraw
    m = interleave_read(image)
    src = _pil(image)
    W, H = src.size
    scale = 520.0 / float(W)
    sw, sh = 520, max(1, int(H * scale))
    top = Image.new("RGB", (sw, sh + 56), (255, 255, 255))
    top.paste(src.resize((sw, sh)), (0, 56))
    d = ImageDraw.Draw(top)
    if not m.get("no_read"):
        lat = strip_lattice(image)
        bnd = [b for b in lat["bnd"] if 0 <= b < W]
        for b in bnd:
            x = b * scale
            d.line([(x, 46), (x, 56 + 0.06 * sh)], fill=(230, 0, 190), width=1)
        if len(bnd) > 8:
            i = len(bnd) // 2
            x0, x1 = bnd[i] * scale, bnd[i + 1] * scale
            d.line([(x0, 30), (x1, 30)], fill=(230, 0, 190), width=3)
            d.line([(x0, 24), (x0, 46)], fill=(230, 0, 190), width=2)
            d.line([(x1, 24), (x1, 46)], fill=(230, 0, 190), width=2)
            d.text((min(sw - 150, x1 + 8), 20), "one strip = %.1f px" % float(m["pitch"]),
                   fill=(150, 0, 120))
        d.text((6, 4), "magenta ticks = every measured strip boundary", fill=(150, 0, 120))
    pan = 260
    board = Image.new("RGB", (sw, top.height + pan + 92), (255, 255, 255))
    board.paste(top, (0, 0))
    d2 = ImageDraw.Draw(board)
    y0 = top.height + 22
    if m.get("no_read"):
        d2.text((10, y0), "NO STRIP LATTICE FOUND (%s)" % str(m.get("reason")), fill=(200, 0, 0))
    else:
        for k, (p, name) in enumerate(((m["path_a"], "COLUMN SET 1"), (m["path_b"], "COLUMN SET 2"))):
            sub = Image.open(p).convert("RGB").resize((pan - 16, pan - 16))
            x = 8 + k * (pan)
            board.paste(sub, (x, y0))
            d2.rectangle([x - 1, y0 - 1, x + pan - 16, y0 + pan - 16], outline=(230, 0, 190))
            d2.text((x, y0 + pan - 12), name, fill=(30, 30, 30))
        d2.text((8, y0 + pan + 6),
                "strips=%d  pairs=%.1f  pitch_cv=%.3f  edges x%.1f"
                % (m["n_strips"], m["n_pairs"], m["pitch_cv"], m["edge_contrast"]), fill=(30, 30, 30))
        d2.text((8, y0 + pan + 22),
                "subject overlap iou=%.3f  colour-map residual=%.3f" % (m["iou"], m["unexplained"]),
                fill=(30, 30, 30))
        d2.text((8, y0 + pan + 38),
                "subject centroid gap=%.3f  set energies %.2f / %.2f"
                % (m["subj_dist"], m["hp_a"], m["hp_b"]), fill=(30, 30, 30))
    p = _out_path(image, tag)
    board.save(p)
    out = dict(m)
    out["path"] = p
    return out


def evidence_page_marked(image, tag="lent"):
    """Build the evidence page and mark the strip boundaries and one strip width."""
    _mk_reset("strip_boundaries", "one_strip_span")
    page = dict(evidence_page(image, tag))
    if not page.get("no_read"):
        lattice = strip_lattice(image)
        W, H = float(lattice["W"]), float(lattice["H"])
        boundaries = [b for b in lattice["bnd"] if 0 <= b < W]
        for b in boundaries:
            _mk("strip_boundaries", "polylines", [[float(b), 0.0], [float(b), 0.06 * H]])
        if len(boundaries) > 8:
            i = len(boundaries) // 2
            _mk("one_strip_span", "polylines",
                [[float(boundaries[i]), 0.075 * H], [float(boundaries[i + 1]), 0.075 * H]])
    src = image if hasattr(image, "size") else str(image)
    page.update(_ovmark_pack(src))
    return page


_MARKS = {}


def _mk_reset(*groups):
    _MARKS.clear()
    for g in groups:
        _MARKS[g] = {"circles": [], "rects": [], "polylines": [], "points": []}


def _mk(group, kind, coords):
    b = _MARKS.setdefault(group, {"circles": [], "rects": [], "polylines": [], "points": []})
    b[kind].append(coords)


def _mk_scale(f):
    f = float(f)
    for b in _MARKS.values():
        b["circles"] = [[c[0] * f, c[1] * f, c[2] * f] for c in b["circles"]]
        b["rects"] = [[r[0] * f, r[1] * f, r[2] * f, r[3] * f] for r in b["rects"]]
        b["polylines"] = [[[p[0] * f, p[1] * f] for p in pl] for pl in b["polylines"]]
        b["points"] = [[p[0] * f, p[1] * f] for p in b["points"]]


def _ell_pts(cx, cy, a, b, deg, n=72):
    import math
    t0 = math.radians(deg)
    ct, st = math.cos(t0), math.sin(t0)
    out = []
    for i in range(n + 1):
        th = 2.0 * math.pi * i / float(n)
        x, y = a * math.cos(th), b * math.sin(th)
        out.append([cx + x * ct - y * st, cy + x * st + y * ct])
    return out


def _arrow_pts(x0, y0, x1, y1, head=0.22):
    import math
    ang = math.atan2(y1 - y0, x1 - x0)
    L = math.hypot(x1 - x0, y1 - y0) * float(head)
    b1 = [x1 - L * math.cos(ang - 0.45), y1 - L * math.sin(ang - 0.45)]
    b2 = [x1 - L * math.cos(ang + 0.45), y1 - L * math.sin(ang + 0.45)]
    return [[x0, y0], [x1, y1], b1, [x1, y1], b2]


def _ovmark_pack(canvas):
    from PIL import Image
    if hasattr(canvas, "size"):
        W, H = canvas.size
    else:
        with Image.open(str(canvas)) as _im:
            W, H = _im.size
    W, H = float(W), float(H)
    M = max(W, H)
    out = {"ref_anchors": [[0.0, 0.0], [W / M, 0.0], [W / M, H / M], [0.0, H / M]],
           "found_anchors": [[0.0, 0.0], [W, 0.0], [W, H], [0.0, H]],
           "mark_canvas": [int(W), int(H)], "n_marks": 0}
    for g, b in _MARKS.items():
        out["mk_" + g] = {
            "circles": [[c[0] / M, c[1] / M, c[2] / M] for c in b["circles"]],
            "rects": [[r[0] / M, r[1] / M, r[2] / M, r[3] / M] for r in b["rects"]],
            "polylines": [[[p[0] / M, p[1] / M] for p in pl] for pl in b["polylines"]],
            "points": [[p[0] / M, p[1] / M] for p in b["points"]],
        }
        out["n_marks"] += sum(len(v) for v in b.values())
    return out

# end of evidence_page_marked_code
