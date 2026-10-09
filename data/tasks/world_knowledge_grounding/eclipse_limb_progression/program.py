# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# shared code: code_limb_walk
def worst_bite_error(cap, run, names, wants):
    """The worst gap between a panel's read bite direction and its reference limb angle."""
    pts = ['north', 'northeast', 'east', 'southeast', 'south', 'southwest', 'west',
           'northwest']
    def lst(n):
        if isinstance(n, dict):
            n = n.get('answers') or []
        return list(n) if isinstance(n, (list, tuple)) else ([] if n is None else [n])
    def deg(v):
        w = ''.join(c for c in str(v).lower() if c.isalpha())
        return pts.index(w) * 45.0 if w in pts else None
    def off(a, b):
        return abs((a - b + 180.0) % 360.0 - 180.0)
    want = [str(k).upper().replace(' ', '') for k in lst(names)]
    targets = lst(wants)
    got = align_by_printed_key([{'key': str(k).upper().replace(' ', ''), 'd': d}
                                for k, d in zip(lst(cap), lst(run))], want)
    worst, obs, exp, notes = -1.0, 180.0, 0.0, []
    for i, r in enumerate(got):
        d = deg(r.get('d')) if isinstance(r, dict) else None
        panel_name = want[i] if i < len(want) else str(i)
        try:
            t = float(targets[i]) if i < len(targets) else None
        except (TypeError, ValueError):
            t = None
        if d is None or t is None:
            worst, obs, exp = 180.0, 180.0, 0.0
            notes.append('%s: the bite was not read' % panel_name)
            continue
        if t < 0:
            t = 0.0 if off(d, 0.0) <= off(d, 180.0) else 180.0
        error = off(d, t)
        notes.append('%s: the bite lies %g, the phase wants %g, off by %g' % (panel_name, d, t, error))
        if error > worst:
            worst, obs, exp = error, d, t
    return {'obs': obs, 'exp': exp, 'worst': worst,
            'verdict': '; '.join(notes) or 'no panel was read'}

# end of code_limb_walk

# shared code: code_phase_disc
def phase_disc_match(ans, want):
    """Match the single phase read on the moon disc against the reference phase."""
    def lst(n):
        if isinstance(n, dict):
            n = n.get('answers') or []
        return list(n) if isinstance(n, (list, tuple)) else ([] if n is None else [n])
    def cls(v):
        w = ''.join(c if c.isalpha() else ' ' for c in str(v).lower())
        for k in ['none', 'crescent', 'half', 'most', 'all']:
            if k in w:
                return k
        return None
    got = []
    for x in lst(ans):
        c = cls(x)
        if c:
            got.append(c)
    t = None
    for x in lst(want):
        t = cls(x) or t
    good = len(got) == 1 and t is not None and got[0] == t
    return {'state': 'match' if good else 'mismatch', 'n': len(got),
            'verdict': 'the phase disc reads %s, an eclipse day wants %s'
                       % (' '.join(got) or 'nothing', t or 'nothing')}

# end of code_phase_disc
