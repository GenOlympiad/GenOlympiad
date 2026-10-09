# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# shared code: code_bulb_lay
def score_bulb_pockets(k, a, b, c, keys, wa, wb, use):
    """Count pockets with the right bulb lie, enough cover, and the right face where scored."""
    def lst(n):
        if isinstance(n, dict):
            n = n.get('answers') or []
        return list(n) if isinstance(n, (list, tuple)) else ([] if n is None else [n])
    def word(v, opts):
        s = ' '.join(str(v).lower().replace('-', ' ').split())
        for o in opts:
            if o in s:
                return o
        return None
    want = [str(x) for x in lst(keys)]
    ea, eb = lst(wa), lst(wb)
    on = [str(u).lower() for u in lst(use)]
    got = align_by_printed_key([{'key': x, 'a': p, 'b': q, 'c': r}
                                for x, p, q, r in zip(lst(k), lst(a), lst(b), lst(c))], want)
    n, say = 0, []
    for i, row in enumerate(got):
        nm = want[i] if i < len(want) else str(i)
        r = row if isinstance(row, dict) else {}
        pa = word(r.get('a'), ['on its side', 'nose up', 'nose down'])
        ta = str(ea[i]).lower() if i < len(ea) else None
        if pa is not None and pa == ta:
            n += 1
        say.append('%s lies %r against a wanted %r' % (nm, pa, ta))
        if str(r.get('c')).strip().lower().startswith('y'):
            n += 1
            say.append('%s carries cover deeper than the bulb' % nm)
        else:
            say.append('%s cover not confirmed' % nm)
        if i < len(on) and on[i].startswith('y'):
            pb = word(r.get('b'), ['toward the path', 'away from the path'])
            tb = str(eb[i]).lower() if i < len(eb) else None
            if pb is not None and pb == tb:
                n += 1
            say.append('%s flat face %r against a wanted %r' % (nm, pb, tb))
    return {'n': n, 'checks': 2 * len(want) + sum(1 for u in on if u.startswith('y')),
            'verdict': '; '.join(say) or 'no pocket was read'}

# end of code_bulb_lay
