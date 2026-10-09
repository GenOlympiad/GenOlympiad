# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# shared code: code_precision_ratio
def marker_hit_rate(node):
    """The share of asked shaded tiles that really hold a marker."""
    answers = (node or {}).get('answers') or []
    n = sum(1 for a in answers if str(a).strip().lower().startswith('y'))
    return {'r': n / float(max(1, len(answers))), 'n': n, 'asked': len(answers),
            'verdict': '%d of the %d shaded tiles asked really hold a marker -> hit rate %.3f'
                       % (n, len(answers), n / float(max(1, len(answers))))}

# end of code_precision_ratio

# shared code: code_corner_marker_tally
def corner_marker_check(node, wanted_corners, total):
    """Yes when every marker reads as corner or middle and the corner count is as wanted."""
    raw_answers = (node or {}).get('answers') if isinstance(node, dict) else None
    positions = [str(x).strip().lower() for x in (raw_answers if isinstance(raw_answers, (list, tuple)) else [])]
    n_corner = sum(1 for x in positions if x.startswith('c'))
    n_middle = sum(1 for x in positions if x.startswith('m'))
    ok = len(positions) == int(total) and n_corner + n_middle == len(positions) and n_corner == int(wanted_corners)
    return {'ok': 'yes' if ok else 'no', 'n_corner': n_corner, 'n_middle': n_middle, 'asked': len(positions),
            'verdict': '%d markers read: %d sit by a tile corner, %d sit near a tile middle'
                       % (len(positions), n_corner, n_middle)}

# end of code_corner_marker_tally
