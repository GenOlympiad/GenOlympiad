# code: plan_frac_code
def wall_type_score(reads, reference):
    """The share of walls read as their reference symbol, capped at 0.25 if any is wrong."""
    want = [str(w).strip().lower() for w in reference['reader_types']]
    n = len(want)
    answers = (reads or {}).get('answers') or []
    got = []
    for a in answers:
        low = str(a).strip().lower()
        word = ''
        for full in ('window', 'wall', 'door', 'stair'):
            if full in low:
                word = full
                break
        got.append(word)
    if len(got) != n:
        return {'frac': 0.0, 'read_n': len(got), 'got': got}
    ok = sum(1 for i in range(n) if got[i] == want[i])
    frac = round(ok / float(n), 4)
    if ok < n:
        frac = min(frac, 0.25)
    return {'frac': frac, 'read_n': n, 'got': got}

# end of plan_frac_code
