# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# code: heights_code
def wax_heights(cd):
    bs = sorted([[float(v) for v in b] for b in cd['geometry']],
                key=lambda b: (b[1] + b[3]) / 2.0)
    tops = [min(b[0], b[2]) for b in bs]
    bots = [max(b[0], b[2]) for b in bs]
    base = sorted(bots)[len(bots) // 2]
    return [base - t for t in tops]
def candle_heights(candle_boxes, n):
    """Each candle height above the shared base, left to right, as ratios of the tallest."""
    if len(candle_boxes.get('geometry') or []) != int(n):
        return {'ratios': None, 'heights': None, 'degenerate': True}
    hs = wax_heights(candle_boxes)
    m = max(hs) if hs else 0.0
    if m <= 2.0 or min(hs) <= 2.0:
        return {'ratios': None, 'heights': hs, 'degenerate': True}
    return {'ratios': [round(h / m, 3) for h in hs],
            'heights': [round(h, 1) for h in hs], 'degenerate': False}

# end of heights_code

# code: order_score_code
def wax_heights(cd):
    bs = sorted([[float(v) for v in b] for b in cd['geometry']],
                key=lambda b: (b[1] + b[3]) / 2.0)
    tops = [min(b[0], b[2]) for b in bs]
    bots = [max(b[0], b[2]) for b in bs]
    base = sorted(bots)[len(bots) // 2]
    return [base - t for t in tops]
def order_score(candle_boxes, names, target_order):
    """Give 1 if the candles sorted shortest to tallest follow the reference order."""
    if len(candle_boxes.get('geometry') or []) != len(list(names)):
        return {'frac': 0.0, 'unreadable': True, 'got': None}
    heights = wax_heights(candle_boxes)
    if min(heights) <= 2.0:
        return {'frac': 0.0, 'unreadable': True, 'got': None}
    got = [p[0] for p in sorted(zip(list(names), heights), key=lambda p: p[1])]
    if len(got) != len(list(target_order)):
        return {'frac': 0.0, 'unreadable': True, 'got': got}
    return {'frac': 1.0 if got == list(target_order) else 0.0, 'unreadable': False,
            'got': got, 'heights': [round(h, 1) for h in heights]}

# end of order_score_code
