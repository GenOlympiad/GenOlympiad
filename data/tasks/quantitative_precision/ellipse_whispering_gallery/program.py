# code: focal_sum_code
def focal_sum_spread(mark_read, foci_read, mark_colours, foci_colours, image, reference):
    """Score how equal the summed distances to both foci are across the magenta points."""
    import math
    W, H = image.size
    diag = math.hypot(W, H)

    def centres(ring, col, want):
        bs = (ring or {}).get('geometry') or []
        ans = (col or {}).get('answers') or []
        if len(ans) != len(bs):
            return None
        out = []
        for b, a in zip(bs, ans):
            y0, x0, y1, x1 = [float(v) for v in b[:4]]
            w = str(a or '').strip().lower()
            if w.startswith(want):
                out.append(((x0 + x1) / 2.0 * W / 1000.0, (y0 + y1) / 2.0 * H / 1000.0))
        return out

    marks = centres(mark_read, mark_colours, ('magenta', 'pink'))
    foci = centres(foci_read, foci_colours, ('dark', 'black'))
    if marks is None or foci is None:
        return {'frac': 0.0, 'no_read': True, 'refused': True,
                'why': 'a colour read did not answer for every box'}
    min_pts = int((reference or {}).get('min_pts', 3) or 3)
    if len(foci) != 2 or len(marks) < max(2, min_pts - 1):
        return {'frac': 0.0, 'no_read': True, 'refused': True,
                'n_marks': len(marks), 'n_foci': len(foci),
                'answers_marks': [str(a) for a in ((mark_colours or {}).get('answers') or [])],
                'answers_foci': [str(a) for a in ((foci_colours or {}).get('answers') or [])]}
    (f1x, f1y), (f2x, f2y) = foci
    if math.hypot(f2x - f1x, f2y - f1y) < 3.0:
        return {'frac': 0.0, 'no_read': True, 'refused': True,
                'n_marks': len(marks), 'n_foci': len(foci)}
    sums = [(math.hypot(x - f1x, y - f1y) + math.hypot(x - f2x, y - f2y)) / diag
            for x, y in marks]
    if len(marks) < min_pts:
        return {'frac': 0.0, 'no_read': False, 'n_marks': len(marks), 'n_foci': len(foci),
                'sums': [round(s, 4) for s in sums], 'sum_cv': None,
                'why': 'fewer magenta marks than the validity floor'}
    mean = sum(sums) / len(sums)
    var = sum((s - mean) ** 2 for s in sums) / len(sums)
    spread = (var ** 0.5) / mean if mean > 0 else 1.0
    tolerance = float((reference or {}).get('tol', 0.08) or 0.08)
    frac = round(max(0.0, 1.0 - spread / (2.0 * tolerance)), 4)
    return {'frac': frac, 'no_read': False,
            'n_marks': len(marks), 'n_foci': len(foci), 'sums': [round(s, 4) for s in sums],
            'sum_cv': round(spread, 4),
            'verdict': ('%d marks, focal-radii sums CV %.4f against tol %.3f -> frac %.3f'
                        % (len(marks), spread, tolerance, frac)),
            'foci_px': [[round(f1x, 1), round(f1y, 1)], [round(f2x, 1), round(f2y, 1)]],
            'marks_px': [[round(x, 1), round(y, 1)] for x, y in marks]}

# end of focal_sum_code
