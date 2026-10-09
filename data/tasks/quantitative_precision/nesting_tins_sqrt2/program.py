# code: confirmed_code
def confirmed_bowls(bowls, vet_reads):
    """Keep only the bowl boxes the vetting answers confirm as one whole bowl."""
    geometry = (bowls or {}).get('geometry') or []
    answers = (vet_reads or {}).get('answers') or []
    keep = [list(b) for i, b in enumerate(geometry)
            if i < len(answers) and str(answers[i]).strip().lower().startswith('y')]
    return {'geometry': keep, 'n': len(keep), 'asked': len(answers),
            'degenerate': len(keep) < 2, 'refused': len(keep) < 2,
            'verdict': '%d of the %d offered rectangles confirmed one whole bowl'
                       % (len(keep), len(answers))}

# end of confirmed_code

# code: chain_code
def bowl_size_chain(bowls, n):
    """Bowl heights left to right as fractions of the largest, and the largest-to-smallest ratio."""
    n = int(n)
    geometry = bowls.get('geometry') or []
    if len(geometry) < 2:
        return {'seq': None, 'span': 0.0, 'bad': True, 'refused': True, 'n_read': len(geometry)}
    rows = []
    for b in geometry:
        ymin, xmin, ymax, xmax = [float(v) for v in b]
        rows.append(((xmin + xmax) / 2.0, abs(ymax - ymin), abs(xmax - xmin)))
    rows.sort(key=lambda r: r[0])
    heights = [r[1] for r in rows]
    hi = max(heights); lo = min(heights)
    if hi <= 1.0 or lo <= 1e-6:
        return {'seq': None, 'span': 0.0, 'bad': True, 'refused': True, 'n_read': len(geometry)}
    return {'seq': [round(x / hi, 4) for x in heights], 'span': round(hi / lo, 4),
            'bad': False, 'n_read': len(geometry), 'py': [round(x, 1) for x in heights],
            'px': [round(r[2], 1) for r in rows]}

# end of chain_code
