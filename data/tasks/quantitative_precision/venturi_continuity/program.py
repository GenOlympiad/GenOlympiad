# code: cont_code
def continuity_score(arrow_boxes, gap_boxes, reference):
    """How steady width times arrow length stays across the channel sections, 1 when constant."""
    def cx(b):
        return (float(b[1]) + float(b[3])) / 2.0
    arrows = sorted(arrow_boxes['geometry'], key=cx)
    gaps = sorted(gap_boxes['geometry'], key=cx)
    n = min(len(arrows), len(gaps))
    min_items = int(reference['min_items'])
    if n < min_items:
        return {'frac': 0.0, 'degenerate': True, 'n': n,
                'verdict': 'only %d paired sections resolved, %d required' % (n, min_items)}
    widths = [abs(float(gaps[i][2]) - float(gaps[i][0])) for i in range(n)]
    lengths = [abs(float(arrows[i][3]) - float(arrows[i][1])) for i in range(n)]
    if min(widths) <= 1.0 or min(lengths) <= 1.0:
        return {'frac': 0.0, 'degenerate': True, 'n': n,
                'verdict': 'a section read as zero width or zero arrow length'}
    wmean = sum(widths) / float(n)
    spread = (max(widths) - min(widths)) / wmean
    size_min = float(reference['size_min'])
    if spread < size_min:
        return {'frac': 0.0, 'degenerate': True, 'n': n,
                'widths': [round(w, 1) for w in widths],
                'verdict': 'the channel barely narrows (width spread %.3f < %.3f) -- there is '
                           'no continuity invariant to test' % (spread, size_min)}
    products = [widths[i] * lengths[i] for i in range(n)]
    pmean = sum(products) / float(n)
    if pmean <= 0:
        return {'frac': 0.0, 'degenerate': True, 'n': n, 'verdict': 'degenerate products'}
    variance = sum((p - pmean) ** 2 for p in products) / float(n)
    cv = (variance ** 0.5) / pmean
    tol = float(reference['tol'])
    frac = max(0.0, 1.0 - cv / (2.0 * tol))
    return {'frac': round(frac, 4), 'prod_cv': round(cv, 4), 'n': n, 'degenerate': False,
            'widths': [round(w, 1) for w in widths], 'lengths': [round(l, 1) for l in lengths],
            'products': [round(p, 1) for p in products],
            'verdict': 'width x speed over %d sections varies by CV %.3f (tol %.2f) -> '
                       'frac %.2f' % (n, cv, tol, frac)}

# end of cont_code
