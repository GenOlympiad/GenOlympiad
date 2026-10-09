# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# shared code: code_pair_cover
def pairings_cover_all(keys, names, want, teams):
    """Whether the match lines read contain every pairing of the clubs once, with each club's match count."""
    def as_list(n):
        if isinstance(n, dict):
            n = n.get('answers') or []
        return list(n) if isinstance(n, (list, tuple)) else ([] if n is None else [n])
    clubs = [str(t).strip().upper() for t in as_list(teams)]
    round_keys = [''.join(c for c in str(k) if c.isdigit()) for k in as_list(keys)]
    rows = align_by_printed_key([{'key': k, 'v': str(v)} for k, v in zip(round_keys, as_list(names))],
                                [str(w) for w in as_list(want)])
    flat = []
    for r in rows:
        got = [w.strip().upper() for w in
               str((r or {}).get('v') or '').replace(';', ',').split(',')]
        got = [w for w in got if w in clubs]
        flat += [tuple(sorted(got[i:i + 2])) for i in range(0, len(got) - 1, 2)]
    flat = [p for p in flat if len(p) == 2 and p[0] != p[1]]
    full = set()
    for i in range(len(clubs)):
        for j in range(i + 1, len(clubs)):
            full.add(tuple(sorted((clubs[i], clubs[j]))))
    matches_per_club = dict((t, 0) for t in clubs)
    for p in flat:
        for t in p:
            matches_per_club[t] = matches_per_club.get(t, 0) + 1
    state = 'complete' if (flat and set(flat) == full) else 'short'
    s = 'cover=%s,%s' % (state, ','.join('%s=%d' % (t, matches_per_club[t]) for t in clubs))
    return {'s': s, 'played': len(flat),
            'verdict': '%d match lines read, %d of the %d pairings present'
                       % (len(flat), len(set(flat)), len(full))}

# end of code_pair_cover

# shared code: code_pair_clash
def pairings_clash(keys, names, want, teams):
    """Whether any pairing repeats or any club plays twice in one round."""
    def as_list(n):
        if isinstance(n, dict):
            n = n.get('answers') or []
        return list(n) if isinstance(n, (list, tuple)) else ([] if n is None else [n])
    clubs = [str(t).strip().upper() for t in as_list(teams)]
    round_keys = [''.join(c for c in str(k) if c.isdigit()) for k in as_list(keys)]
    rows = align_by_printed_key([{'key': k, 'v': str(v)} for k, v in zip(round_keys, as_list(names))],
                                [str(w) for w in as_list(want)])
    flat, twice_in_round = [], False
    for r in rows:
        got = [w.strip().upper() for w in
               str((r or {}).get('v') or '').replace(';', ',').split(',')]
        got = [w for w in got if w in clubs]
        if len(got) != len(set(got)):
            twice_in_round = True
        flat += [tuple(sorted(got[i:i + 2])) for i in range(0, len(got) - 1, 2)]
    flat = [p for p in flat if len(p) == 2 and p[0] != p[1]]
    twice = len(flat) != len(set(flat))
    ok = bool(flat) and not twice and not twice_in_round
    return {'state': 'clean' if ok else 'clash', 'played': len(flat),
            'verdict': '%d match lines read, repeated pairing %s, club twice in a round %s'
                       % (len(flat), 'yes' if twice else 'no', 'yes' if twice_in_round else 'no')}

# end of code_pair_clash

# shared code: code_bye_permutation
def byes_cover_all_clubs(keys, outs, want, teams):
    """Whether every round names one club sitting out and every club sits out once."""
    def as_list(n):
        if isinstance(n, dict):
            n = n.get('answers') or []
        return list(n) if isinstance(n, (list, tuple)) else ([] if n is None else [n])
    clubs = [str(t).strip().upper() for t in as_list(teams)]
    round_keys = [''.join(c for c in str(k) if c.isdigit()) for k in as_list(keys)]
    want = [str(w) for w in as_list(want)]
    rows = align_by_printed_key([{'key': k, 'v': str(v).strip().upper()}
                                 for k, v in zip(round_keys, as_list(outs))], want)
    got = [str((r or {}).get('v') or '').strip().upper() for r in rows]
    named = [g for g in got if g in clubs]
    ok = len(named) == len(want) and len(set(named)) == len(clubs)
    return {'state': 'match' if ok else 'mismatch', 'n': len(named),
            'verdict': 'sitting-out lines read %s' % (', '.join(got) or 'nothing')}

# end of code_bye_permutation
