# shared code: code_5ad8f84ed1e1
def mark_positions(dots):
    """Convert each marked dot's box centre to a sorted x value on the plotted axis range."""
    XLO, XHI = -1.2, 1.2
    geometry = (dots or {}).get('geometry') or []
    xs = []
    for b in geometry:
        centre_frac = (float(b[1]) + float(b[3])) / 2.0 / 1000.0
        xs.append(XLO + centre_frac * (XHI - XLO))
    xs.sort()
    return {'n_marks': len(xs), 'xs': [round(v, 3) for v in xs],
            'degenerate': 1 if not xs else 0}

# end of code_5ad8f84ed1e1
