# code: helpers
from genolympiad.task_helpers import join_box_reads, to_float
# end of helpers

# code: read_mercator_code
import os

_MC_CACHE = {}


def _prep(image, cap=1600):
    import numpy as np
    import cv2
    from PIL import Image
    key = str(image)
    try:
        st = os.stat(str(image))
        key = "%s|%s|%s" % (key, st.st_mtime_ns, st.st_size)
    except Exception:
        pass
    hit = _MC_CACHE.get(key)
    if hit is not None:
        return hit
    pil = image if hasattr(image, "convert") else Image.open(str(image))
    a = np.asarray(pil.convert("RGB")).astype("uint8")
    H, W = a.shape[:2]
    if max(H, W) > cap:
        s = cap / float(max(H, W))
        a = cv2.resize(a, (max(8, int(W * s)), max(8, int(H * s))),
                       interpolation=cv2.INTER_AREA)
    g = cv2.cvtColor(a, cv2.COLOR_RGB2GRAY)
    if len(_MC_CACHE) > 16:
        _MC_CACHE.clear()
    _MC_CACHE[key] = (a, g)
    return a, g


def _ink(g):
    import cv2
    th = cv2.threshold(g, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    dark = 255 - th
    return dark if dark.mean() < th.mean() else th


def _bandfrac(err, core, margin):
    f = 1.0 - max(0.0, float(err) - float(core)) / max(float(margin), 1e-9)
    return round(min(1.0, max(0.0, f)), 4)


def parallels(image, n_lines=None, cov_thr=0.55):
    import numpy as np
    _a, g = _prep(image)
    H, W = g.shape
    ink = _ink(g)
    frac = (ink > 0).sum(axis=1).astype("float64") / float(W)
    runs, run = [], None
    for y in range(H):
        if frac[y] > cov_thr:
            run = [y, y] if run is None else [run[0], y]
        elif run is not None:
            runs.append(run)
            run = None
    if run is not None:
        runs.append(run)
    ys = []
    for a, b in runs:
        lo, hi = max(0, a - 2), min(H - 1, b + 2)
        wsum = num = 0.0
        for y in range(lo, hi + 1):
            w = max(0.0, float(frac[y]) - 0.25)
            wsum += w
            num += w * y
        ys.append(num / wsum if wsum > 1e-9 else 0.5 * (a + b))
    merged = []
    for y in ys:
        if merged and y - merged[-1] < 0.012 * H:
            continue
        merged.append(y)
    raw = list(merged)
    kept = [y for y in merged if 0.02 * H <= y <= 0.98 * H]
    if n_lines and len(kept) == int(n_lines) + 2 and len(kept) >= 5:
        gaps = [kept[i + 1] - kept[i] for i in range(len(kept) - 1)]
        if gaps[0] < 0.5 * gaps[1] and gaps[-1] < 0.5 * gaps[-2]:
            kept = kept[1:-1]
    return {"n_rules_raw": len(raw), "n_rules": len(kept), "y": [round(v, 1) for v in kept],
            "y_raw": [round(v, 1) for v in raw], "img_h": H, "img_w": W,
            "span_frac": [round(float(frac[int(round(v))]), 3) for v in kept]}


def _profile_agreement(m, gt, resolvable):
    ok = tot = 0
    for i in range(len(gt) - 1):
        dg = gt[i + 1] - gt[i]
        if abs(dg) / max(1e-9, gt[i]) < resolvable:
            continue
        dm = m[i + 1] - m[i]
        want = 1 if dg > 0 else -1
        got = 0 if abs(dm) / max(1e-9, abs(m[i])) < resolvable else (1 if dm > 0 else -1)
        tot += 1
        ok += 1 if want == got else 0
    return (ok / float(tot)) if tot else 1.0


def read_mercator(image, n_lines, gap_seq, core, margin, symmetric=False, cov_thr=0.55):
    """Measure the drawn parallels and score count, band gaps, profile, ratio, symmetry, width."""
    import numpy as np
    found = parallels(image, n_lines, cov_thr)
    n_lines = int(n_lines)
    want_gaps = [float(x) for x in gap_seq]
    if found["n_rules"] < 3:
        return {"no_read": True, "reason": "few_parallels_%d" % found["n_rules"],
                "n_rules": found["n_rules"], "frac_count": 0.0, "frac_bands": 0.0,
                "frac_profile": 0.0, "frac_ratio": 0.0, "frac_symmetry": 0.0,
                "frac_full_width": 0.0}
    rule_ys = found["y"]
    gaps = [rule_ys[i + 1] - rule_ys[i] for i in range(len(rule_ys) - 1)]
    out = dict(found)
    out["gaps_px"] = [round(v, 1) for v in gaps]
    out["no_read"] = False
    out["frac_count"] = 1.0 if found["n_rules"] == n_lines else 0.0
    out["frac_full_width"] = round(
        sum(1 for s in found["span_frac"] if s >= 0.92) / float(max(1, len(found["span_frac"]))), 4)
    if len(gaps) != len(want_gaps):
        out.update({"frac_bands": 0.0, "frac_profile": 0.0, "frac_symmetry": 0.0,
                    "band_rel_errs": None, "reason": "band_count_%d_vs_%d"
                    % (len(gaps), len(want_gaps))})
    else:
        scale = sum(gaps) / max(1e-9, sum(want_gaps))
        band_errors = [abs(gaps[i] - scale * want_gaps[i]) / max(1e-9, scale * want_gaps[i]) for i in range(len(want_gaps))]
        out["scale_px_per_unit"] = round(scale, 4)
        out["band_rel_errs"] = [round(e, 4) for e in band_errors]
        out["frac_bands"] = round(
            sum(_bandfrac(e, core, margin) for e in band_errors) / float(len(band_errors)), 4)
        out["frac_profile"] = round(_profile_agreement(gaps, want_gaps, 2.0 * core), 4)
        if symmetric:
            n = len(gaps)
            mean = sum(gaps) / float(n)
            symmetry_errors = [abs(gaps[i] - gaps[n - 1 - i]) / max(1e-9, mean) for i in range(n // 2)]
            out["symmetry_rel_errs"] = [round(e, 4) for e in symmetry_errors]
            out["frac_symmetry"] = round(
                sum(_bandfrac(e, core, margin) for e in symmetry_errors) / float(max(1, len(symmetry_errors))), 4)
        else:
            out["frac_symmetry"] = 0.0
    if len(gaps) >= 3:
        r_got = max(gaps) / max(1e-9, min(gaps))
        r_want = max(want_gaps) / max(1e-9, min(want_gaps))
        out["ratio_measured"] = round(r_got, 4)
        out["ratio_committed"] = round(r_want, 4)
        out["frac_ratio"] = _bandfrac(abs(r_got - r_want) / r_want, 3.0 * core, 3.0 * margin)
    else:
        out["frac_ratio"] = 0.0
    return out


def score_latitude_labels(answer, labels):
    """The share of latitude labels read in the reference top to bottom order."""
    import re
    if answer is None:
        return {"no_read": True, "frac": 0.0, "got": []}
    text = str(answer).lower().replace("degrees", " ").replace("deg", " ")
    text = text.replace("°", " ")
    got = []
    for match in re.finditer(r"(-?\d+(?:\.\d+)?)\s*([ns])?", text):
        v = float(match.group(1))
        suffix = match.group(2)
        if suffix == "s":
            v = -abs(v)
        got.append(int(round(v)))
    want = [int(round(float(x))) for x in labels]
    n = max(len(want), len(got))
    n_match = sum(1 for i in range(min(len(want), len(got))) if want[i] == got[i])
    return {"no_read": False, "got": got, "want": want,
            "frac": round(n_match / float(max(1, n)), 4),
            "exact": bool(got == want)}


def _overlay_path(image, tag):
    import hashlib
    import tempfile
    d = os.path.join(tempfile.gettempdir(), "genolympiad_overlay")
    try:
        os.makedirs(d, exist_ok=True)
    except Exception:
        pass
    h = hashlib.md5(("%s|%s" % (str(image), tag)).encode("utf-8", "replace")).hexdigest()[:12]
    return os.path.join(d, "e9cmc_%s_%s.png" % (tag, h))


def mercator_overlay(image, n_lines, gap_seq, core, margin, symmetric=False, tag="merc"):
    """Draw where each parallel should sit beside where it was drawn, labelling band errors."""
    import numpy as np
    import cv2
    from PIL import Image
    measured = read_mercator(image, n_lines, gap_seq, core, margin, symmetric)
    a, _g = _prep(image)
    canvas = np.array(a).copy()
    H, W = canvas.shape[:2]
    line_width = max(2, int(0.0022 * min(H, W)))
    font_scale = 0.55 * min(W, H) / 1024.0
    if not measured.get("no_read") and measured.get("band_rel_errs") is not None:
        ys = measured["y"]
        want_gaps = [float(x) for x in gap_seq]
        scale = measured["scale_px_per_unit"]
        want = [ys[0]]
        for v in want_gaps:
            want.append(want[-1] + scale * v)
        for i, y in enumerate(want):
            cv2.line(canvas, (6, int(y)), (int(0.10 * W), int(y)), (0, 190, 0), line_width)
        for i, y in enumerate(ys):
            cv2.line(canvas, (int(0.90 * W), int(y)), (W - 6, int(y)), (220, 0, 200), line_width)
        for i, e in enumerate(measured["band_rel_errs"]):
            ymid = int(0.5 * (ys[i] + ys[i + 1]))
            colour = (0, 190, 0) if e <= core else ((225, 180, 40) if e <= core + margin
                                                 else (225, 70, 70))
            cv2.line(canvas, (int(0.10 * W), ymid), (int(0.90 * W), ymid), colour, 1)
            cv2.putText(canvas, "%+.0f%%" % (100.0 * e), (int(0.12 * W), ymid - 4),
                        cv2.FONT_HERSHEY_SIMPLEX, font_scale, colour, line_width)
    caption = ["green scale (left) = where the committed ladder puts each parallel after ONE global "
           "scale factor;  magenta scale (right) = the rules actually drawn;  each band is "
           "labelled with its own relative error",
           "rules %s (committed %s)   per-band credit %.2f   profile %.2f   polar/equatorial "
           "%s vs %s" % (measured.get("n_rules"), n_lines, measured.get("frac_bands", 0.0),
                         measured.get("frac_profile", 0.0), measured.get("ratio_measured"),
                         measured.get("ratio_committed"))]
    caption_scale = min(font_scale, 0.80 * W / max(len(caption[0]), len(caption[1])) / 9.0)
    line_height = int(30 * caption_scale * 2)
    strip = np.full((2 * line_height + 16, W, 3), 18, dtype=canvas.dtype)
    for i, line in enumerate(caption):
        cv2.putText(strip, line, (10, (i + 1) * line_height), cv2.FONT_HERSHEY_SIMPLEX, caption_scale,
                    (245, 245, 245), max(1, line_width - 1))
    canvas = np.vstack([canvas, strip])
    path = _overlay_path(image, tag)
    Image.fromarray(canvas).save(path)
    out = dict(measured)
    out["path"] = path
    return out

# end of read_mercator_code

# code: f_code
def full_credit(n_rules):
    """Always score 1; this step only records the number of rules found."""
    return 1.0

# end of f_code
