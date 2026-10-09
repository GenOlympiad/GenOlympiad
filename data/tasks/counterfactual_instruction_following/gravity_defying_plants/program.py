# code: headcount_code
def m(ans, key):
    if ans is None:
        return 0.0
    a = str(ans).strip().lower()
    k = str(key).strip().lower()
    opp = 'top' if k == 'bottom' else 'bottom'
    if opp in a and k not in a:
        return 0.0
    return 1.0 if k in a else 0.0


def all_plants_match(confirmed_reads, expected, n_want):
    """Score 1 only if the expected number of plants was found and every one hangs as asked."""
    answers = (confirmed_reads or {}).get('answers') or []
    n_items = len(answers)
    try:
        n_want = int(n_want)
    except (TypeError, ValueError):
        n_want = -1
    if n_items == 0:
        return {'frac': 0.0, 'n_items': 0, 'n_ok': 0, 'n_want': n_want,
                'verdict': 'no counted object survived the box acceptance gate -> frac 0.0'}
    n_ok = int(sum(1 for a in answers if m(a, expected) >= 1.0))
    if n_items != n_want:
        return {'frac': 0.0, 'n_items': n_items, 'n_ok': n_ok, 'n_want': n_want,
                'verdict': ('the count found %d confirmed object(s), the prompt demanded %d '
                            '-> frac 0.0' % (n_items, n_want))}
    frac = 1.0 if n_ok == n_items else 0.0
    return {'frac': frac, 'n_items': n_items, 'n_ok': n_ok, 'n_want': n_want,
            'verdict': ('%d of %d objects read "%s" -> frac %.1f'
                        % (n_ok, n_items, str(expected), frac))}

# end of headcount_code
