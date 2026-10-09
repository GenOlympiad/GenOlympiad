# code: helpers
from genolympiad.task_helpers import (
    count_confirmed_cutouts, paint_cells_by_fraction, plan_pinned_grid)
# end of helpers

# code: code_dial
def check_hour_angles(node, expected, tolerance):
    """Count the hour lines whose read angle from noon lies within tolerance of the expected angle."""
    import re
    angle_by_hour = {}
    for a in (node or {}).get('answers') or []:
        f = re.findall(r'\d+(?:\.\d+)?', str(a))
        if len(f) >= 2:
            angle_by_hour[int(float(f[0]))] = float(f[-1])
    seq = [angle_by_hour.get(int(h)) for h, _ in expected]
    deviations = [abs(s - float(v)) if s is not None else 99.0 for s, (h, v) in zip(seq, expected)]
    n = sum(1 for x in deviations if x <= float(tolerance))
    return {'seq': seq, 'dev': [round(x, 2) for x in deviations], 'n_ok': n, 'n_rows': len(angle_by_hour), 'verdict': 'angle from the noon line, hour by hour %s -> %s deg against the %s deg this latitude needs; %d of %d inside +-%s deg' % ([h for h, _ in expected], seq, [v for _, v in expected], n, len(expected), tolerance)}

# end of code_dial
