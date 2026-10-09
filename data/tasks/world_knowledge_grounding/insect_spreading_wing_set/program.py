# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# code: perp_dev_code
def worst_wing_skew(bodies, wings, total):
    """The worst angle by which a pair of wings departs from square to its own body."""
    direction_deg = {'up and down': 0.0, 'lower left to upper right': 45.0,
         'left and right': 90.0, 'upper left to lower right': 135.0}
    body_dirs = [str(a).strip().lower() for a in ((bodies or {}).get('answers') or [])]
    wing_dirs = [str(a).strip().lower() for a in ((wings or {}).get('answers') or [])]
    deviations = [90.0 if (b not in direction_deg or w not in direction_deg) else abs(abs((direction_deg[w] - direction_deg[b] + 90.0) % 180.0 - 90.0) - 90.0)
         for b, w in zip(body_dirs, wing_dirs)]
    total_digits = ''.join(c for c in str(total) if c.isdigit())
    worst = max(deviations) if (deviations and total_digits and len(deviations) >= int(total_digits)) else 90.0
    return {'dev': worst, 'seen': len(deviations),
            'verdict': 'the worst pair of wings lies %.0f degrees away from square to its own body' % worst}

# end of perp_dev_code

# code: off_height_code
def count_off_height(marks, total):
    """Count pins whose label sits at a different height, or 99 if not every pin was read."""
    reads = [str(a).strip().lower() for a in ((marks or {}).get('answers') or [])]
    valid = [v for v in reads if v[:5] == 'level' or v[:5] == 'diffe']
    n_different = len([1 for v in valid if v[:5] == 'diffe'])
    total_digits = ''.join(c for c in str(total) if c.isdigit())
    n = n_different if (total_digits and len(valid) == int(total_digits)) else 99
    return {'n': n, 'seen': len(valid),
            'verdict': '%d of the %d pins read carry their labels at a different height' % (n_different, len(valid))}

# end of off_height_code
