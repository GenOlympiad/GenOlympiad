# code: phase_code
def stagger_offset_score(low, up, reference):
    """Score how close the upper bricks sit to the midpoints between lower bricks."""
    def cx(b):
        return (float(b[1]) + float(b[3])) / 2.0
    lower_centres = sorted(cx(b) for b in (low.get('geometry') or []))
    upper_centres = sorted(cx(b) for b in (up.get('geometry') or []))
    if len(lower_centres) < 3 or len(upper_centres) < 2:
        return {'frac': 0.0, 'degenerate': True, 'refused': True, 'n_lower': len(lower_centres), 'n_upper': len(upper_centres),
                'caption': 'degenerate read (need >=3 lower and >=2 upper row marks)'}
    gaps = [lower_centres[i + 1] - lower_centres[i] for i in range(len(lower_centres) - 1)]
    gaps.sort()
    m = len(gaps)
    pitch = gaps[m // 2] if m % 2 else (gaps[m // 2 - 1] + gaps[m // 2]) / 2.0
    if pitch < 4.0:
        return {'frac': 0.0, 'degenerate': True, 'refused': True, 'n_lower': len(lower_centres), 'n_upper': len(upper_centres),
                'caption': 'degenerate read (lower-row pitch collapsed)'}
    mids = [(lower_centres[i] + lower_centres[i + 1]) / 2.0 for i in range(len(lower_centres) - 1)]
    offsets = sorted(min(abs(x - u) for x in mids) for u in upper_centres)
    k = len(offsets)
    offset = (offsets[k // 2] if k % 2 else (offsets[k // 2 - 1] + offsets[k // 2]) / 2.0) / pitch
    tolerance = float(reference['tol'])
    f = max(0.0, 1.0 - offset / tolerance)
    return {'frac': round(f, 4), 'degenerate': False, 'n_lower': len(lower_centres), 'n_upper': len(upper_centres),
            'pitch': round(pitch, 2), 'offset': round(offset, 4),
            'caption': 'upper marks sit %.3f of a pitch from the lower-pair midpoints '
                       '(0 = exact half-pitch stagger, 0.5 = stacked straight above; tol %.2f)'
                       % (offset, tolerance)}

# end of phase_code
