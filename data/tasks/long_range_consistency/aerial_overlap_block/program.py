# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts, count_listed_items
# end of helpers

# shared code: code_footprint_spread
def overlap_count_match(num, cnt, wants):
    """Count overlap squares whose cross counts match the wanted counts, both sorted."""
    def as_list(n):
        if isinstance(n, dict):
            n = n.get('answers') or []
        return list(n) if isinstance(n, (list, tuple)) else ([] if n is None else [n])
    def whole(v):
        d = ''.join(c for c in str(v) if c.isdigit())
        return int(d[:2]) if d else None
    labels = [str(t) for t in as_list(num)]
    observed = [whole(x) for x in as_list(cnt)]
    expected = []
    for x in as_list(wants):
        w = whole(x)
        if w is not None:
            expected.append(w)
    counts_read = sorted([o for o in observed if o is not None])[:len(expected)]
    wanted = sorted(expected)
    n_agree = 0
    for i, e in enumerate(wanted):
        if i < len(counts_read) and counts_read[i] == e:
            n_agree += 1
    return {'ok': n_agree, 'n': len(counts_read),
            'verdict': 'squares %s hold %s crosses; the two overlaps want %s; %d of %d agree'
                       % (' '.join(labels) or 'none', counts_read, wanted, n_agree, len(wanted))}

# end of code_footprint_spread

# shared code: code_block_rim
def rim_cut_match(answers, wants):
    """Match when enough squares read as cut by, and clear of, the block outline."""
    def as_list(n):
        if isinstance(n, dict):
            n = n.get('answers') or []
        return list(n) if isinstance(n, (list, tuple)) else ([] if n is None else [n])
    def yes_no(v):
        w = ''.join(c for c in str(v).lower() if c.isalpha())
        return 'yes' if w.startswith('y') else ('no' if w.startswith('n') else None)
    got = [yes_no(x) for x in as_list(answers)]
    wanted = [yes_no(x) for x in as_list(wants)]
    seen = [g for g in got if g]
    n_cut, n_clear = seen.count('yes'), seen.count('no')
    want_cut, want_clear = wanted.count('yes'), wanted.count('no')
    good = len(wanted) > 0 and len(seen) >= len(wanted) and n_cut >= want_cut and n_clear >= want_clear
    return {'state': 'match' if good else 'mismatch', 'n': len(seen),
            'verdict': '%d squares are cut by the block outline and %d stand clear of it; '
                       'the coverage rule wants %d cut and %d clear' % (n_cut, n_clear, want_cut, want_clear)}

# end of code_block_rim
