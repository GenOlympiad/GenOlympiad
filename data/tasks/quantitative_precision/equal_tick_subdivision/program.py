# code: n_yes_code
def count_confirmed_marks(node):
    """Count the confirmed tick marks and the segments they divide the bar into."""
    answers = (node or {}).get('answers') or []
    n = sum(1 for a in answers if str(a).strip().lower().startswith('y'))
    return {'n_marks': n, 'asked': len(answers), 'n_segments': n + 1}

# end of n_yes_code

# code: spacing_code
def tick_spacing_error(bar_node, mark_node, mark_confirms, src, ratio):
    """The largest gap between measured and reference segment shares, read either way."""
    W, H = src.size
    b = [float(v) for v in bar_node['geometry'][0]]
    by0, by1 = min(b[0], b[2]), max(b[0], b[2])
    bx0, bx1 = min(b[1], b[3]), max(b[1], b[3])
    horiz = (bx1 - bx0) * W >= (by1 - by0) * H
    lo, hi = (bx0, bx1) if horiz else (by0, by1)
    L = hi - lo
    answers = (mark_confirms or {}).get('answers') or []
    mark_positions = []
    for i, q in enumerate((mark_node or {}).get('geometry') or []):
        if i < len(answers) and str(answers[i]).strip().lower().startswith('y'):
            mark_positions.append(float((q[1] + q[3]) / 2.0 if horiz else (q[0] + q[2]) / 2.0))
    total = float(sum(ratio))
    target_shares = [r / total for r in ratio]
    if L < 100.0 or len(mark_positions) != len(target_shares) - 1:
        vague = [a for a in answers if str(a).strip().lower()[:1] not in ('y', 'n')]
        return {'max_frac_err': None, 'degenerate': True,
                'refused': bool(L < 100.0 or vague or not answers),
                'n_marks': len(mark_positions), 'want_marks': len(target_shares) - 1}
    mark_positions.sort()
    cuts = [lo] + mark_positions + [hi]
    segment_shares = [(cuts[i + 1] - cuts[i]) / L for i in range(len(cuts) - 1)]
    forward_err = max(abs(a - b) for a, b in zip(segment_shares, target_shares))
    reverse_err = max(abs(a - b) for a, b in zip(segment_shares, target_shares[::-1]))
    return {'max_frac_err': round(min(forward_err, reverse_err), 4),
            'seg_fracs': [round(f, 4) for f in segment_shares], 'degenerate': False}

# end of spacing_code
