# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# code: heights_code
def _cols(wc):
    bs = sorted([[float(v) for v in b] for b in wc['geometry']],
                key=lambda b: (b[1] + b[3]) / 2.0)
    tops = [min(b[0], b[2]) for b in bs]
    bots = [max(b[0], b[2]) for b in bs]
    base = sorted(bots)[len(bots) // 2]
    return [base - t for t in tops]
def gauge_heights(wc, n):
    """Measure each gauge's water column and its ratio to the tallest, refusing a miscount."""
    if len(wc.get('geometry') or []) != int(n):
        return {'ratios': None, 'heights': None, 'degenerate': True}
    column_heights = _cols(wc)
    tallest = max(column_heights) if column_heights else 0.0
    if tallest <= 2.0 or min(column_heights) <= 2.0:
        return {'ratios': None, 'heights': column_heights, 'degenerate': True}
    return {'ratios': [round(h / tallest, 3) for h in column_heights],
            'heights': [round(h, 1) for h in column_heights], 'degenerate': False}

# end of heights_code

# code: order_score_code
def _cols(wc):
    bs = sorted([[float(v) for v in b] for b in wc['geometry']],
                key=lambda b: (b[1] + b[3]) / 2.0)
    tops = [min(b[0], b[2]) for b in bs]
    bots = [max(b[0], b[2]) for b in bs]
    base = sorted(bots)[len(bots) // 2]
    return [base - t for t in tops]
def order_score(wc, names, target_order):
    """Score 1 when sorting the gauges by water height gives the reference low-to-high order."""
    if len(wc.get('geometry') or []) != len(list(names)):
        return {'frac': 0.0, 'unreadable': True, 'got': None}
    column_heights = _cols(wc)
    if min(column_heights) <= 2.0:
        return {'frac': 0.0, 'unreadable': True, 'got': None}
    got = [p[0] for p in sorted(zip(list(names), column_heights), key=lambda p: p[1])]
    if len(got) != len(list(target_order)):
        return {'frac': 0.0, 'unreadable': True, 'got': got}
    return {'frac': 1.0 if got == list(target_order) else 0.0, 'unreadable': False,
            'got': got, 'heights': [round(h, 1) for h in column_heights]}

# end of order_score_code
