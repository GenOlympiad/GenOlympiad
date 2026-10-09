# code: state_code
def plunger_flag_score(capL, capR, flag_answer, reference, min_gap=20.0):
    """Score 1 when the raised plunger and the fallen flag are on the expected sides."""
    def top(node):
        g = (node or {}).get('geometry') or []
        return float(g[0][0]) if len(g) == 1 else None
    left_top, right_top = top(capL), top(capR)
    if left_top is None or right_top is None:
        return {'frac': 0.0, 'up': None, 'why': 'a plunger cap was not read on one of the two dials'}
    if abs(left_top - right_top) < min_gap:
        return {'frac': 0.0, 'up': None, 'gap': round(abs(left_top - right_top), 1),
                'why': 'both plunger caps sit at the same height -- nothing certifies which one is raised'}
    up = 'left' if left_top < right_top else 'right'
    s = str(flag_answer).lower()
    l, r = 'left' in s, 'right' in s
    fallen = 'left' if (l and not r) else ('right' if (r and not l) else None)
    if fallen is None:
        return {'frac': 0.0, 'up': up, 'why': 'the fallen-flag side did not read'}
    ok = (up == reference['up_side'] and fallen == reference['fallen_side'])
    return {'frac': 1.0 if ok else 0.0, 'up': up, 'fallen': fallen,
            'want': [reference['up_side'], reference['fallen_side']], 'gap': round(abs(left_top - right_top), 1)}

# end of state_code
