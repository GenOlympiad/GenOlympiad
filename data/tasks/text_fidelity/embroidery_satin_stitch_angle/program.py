# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# code: stitch_gap_code
def stitch_gap(keys, runs, want):
    """Largest angle in degrees between a stroke's stitch direction and the one it needs."""
    direction_angles = {'up and down': 0.0, 'lower left to upper right': 45.0,
         'left and right': 90.0, 'upper left to lower right': 135.0}
    want_by_stroke = dict(p.split('=') for p in str(want).split(',') if p.count('=') == 1)
    stroke_keys = [''.join(c for c in str(a) if c.isdigit()) for a in ((keys or {}).get('answers') or [])]
    run_reads = [str(a).strip().lower() for a in ((runs or {}).get('answers') or [])]
    gaps = [90.0] * (len(want_by_stroke) - min(len(stroke_keys), len(run_reads)))
    for k, s in zip(stroke_keys, run_reads):
        t = want_by_stroke.get(k)
        gaps.append(90.0 if (s not in direction_angles or t is None) else abs((direction_angles[s] - float(t) + 90.0) % 180.0 - 90.0))
    worst = max(gaps or [90.0])
    return {'gap': worst, 'verdict': 'the worst stroke has its threads %.0f degrees off the way that stroke demands' % worst}

# end of stitch_gap_code

# code: breaks_code
def count_direction_breaks(marks, joins):
    """Number of joins read as breaking direction, or 99 if not every join was read."""
    reads = [str(a).strip().lower() for a in ((marks or {}).get('answers') or [])]
    good = [v for v in reads if v[:3] == 'fan' or v[:5] == 'break']
    n_breaks = len([1 for v in good if v[:5] == 'break'])
    r = ''.join(c for c in str(joins) if c.isdigit())
    n = n_breaks if (r and len(good) == int(r)) else 99
    return {'n': n, 'seen': len(good),
            'verdict': '%d of the %d joins read change direction along a line' % (n_breaks, len(good))}

# end of breaks_code
