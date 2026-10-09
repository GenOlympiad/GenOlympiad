# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts, map_answer_to_token
# end of helpers

# shared code: code_felling_cuts
def check_felling_cuts(notch, hinge, lay, back, band_ok):
    """Worst angle miss of notch and hinge against the lay, plus two cut facts."""
    def lst(n):
        if isinstance(n, dict):
            n = n.get('answers') or []
        return list(n) if isinstance(n, (list, tuple)) else ([] if n is None else [n])
    def pick(v, opts):
        if v is None:
            return None
        s = ' '.join(str(v).lower().replace('-', ' ').split())
        if s in ('', 'none', 'n a', 'na', 'nil', 'empty', '?', '.'):
            return None
        for o in opts:
            if o in s:
                return o
        return None
    def hour(v):
        d = ''.join(c for c in str(v) if c.isdigit())
        x = int(d) if d and len(d) <= 2 else None
        return x if x is not None and 1 <= x <= 12 else None
    def one(n):
        v = lst(n)
        return v[0] if v else None
    def deg(x):
        return (x % 12) * 30.0
    notch_hour, hinge_hour, lay_hour = hour(one(notch)), hour(one(hinge)), hour(one(lay))
    if notch_hour is None or hinge_hour is None or lay_hour is None:
        return {'obs': 180.0, 'exp': 0.0, 'facts': 0,
                'verdict': 'notch %r hinge %r lay %r not all read' % (notch_hour, hinge_hour, lay_hour)}
    notch_miss = abs((deg(notch_hour) - deg(lay_hour) + 180.0) % 360.0 - 180.0)
    across = abs((deg(hinge_hour) - deg(lay_hour) + 180.0) % 360.0 - 180.0)
    hinge_miss = abs(across - 90.0)
    worst = notch_miss if notch_miss > hinge_miss else hinge_miss
    facts = 0
    back_cut = pick(one(back), ['above the notch floor', 'level with the notch floor',
                          'below the notch floor'])
    if back_cut == 'above the notch floor':
        facts += 1
    band_unbroken = pick(one(band_ok), ['yes', 'no'])
    if band_unbroken == 'yes':
        facts += 1
    return {'obs': worst, 'exp': 0.0, 'facts': facts,
            'verdict': 'notch at %d, hinge at %d, lay at %d; notch miss %g, hinge across %g; '
                       'back cut %r, band unbroken %r' % (notch_hour, hinge_hour, lay_hour, notch_miss, across, back_cut, band_unbroken)}

# end of code_felling_cuts
