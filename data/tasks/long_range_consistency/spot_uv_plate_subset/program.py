# code: helpers
from genolympiad.task_helpers import count_listed_items
# end of helpers

# shared code: code_plate_subset
def check_varnish_plate(edges, back, want_edges, want_back):
    """Whether the plate's black area edges and back third read as the docket wants."""
    def lst(n):
        if isinstance(n, dict):
            n = n.get('answers') or []
        return list(n) if isinstance(n, (list, tuple)) else ([] if n is None else [n])
    def pick(seq, words):
        for v in seq:
            s = ''.join(c for c in str(v).lower() if c.isalpha())
            for w in words:
                if w in s:
                    return w
        return None
    e = pick(lst(edges), ('outlines', 'rectangles'))
    b = pick(lst(back), ('clear', 'black'))
    wanted_edges = str(want_edges).strip().lower()
    wanted_back = str(want_back).strip().lower()
    if e is None or b is None:
        return {'obs': 'unread', 'exp': 'subset drawn',
                'verdict': 'the edges of the black areas or the back third could not be read'}
    ok = (e == wanted_edges and b == wanted_back)
    return {'obs': 'subset drawn' if ok else 'not a subset', 'exp': 'subset drawn',
            'edges': e, 'back': b,
            'verdict': 'edges read as ' + e + ' and the back third read as ' + b
                       + '; the docket wants ' + wanted_edges + ' and ' + wanted_back}

# end of code_plate_subset

# shared code: code_fold_break
def check_fold_break(gap, count, want_gap, want_count):
    """Whether the crease line and black shape count show the plate broken at the fold."""
    def lst(n):
        if isinstance(n, dict):
            n = n.get('answers') or []
        return list(n) if isinstance(n, (list, tuple)) else ([] if n is None else [n])
    g = None
    for v in lst(gap):
        s = ''.join(c for c in str(v).lower() if c.isalpha())
        if 'strip' in s:
            g = 'strip'
            break
        if 'across' in s:
            g = 'across'
            break
    n = None
    for v in lst(count):
        d = ''.join(c for c in str(v) if c.isdigit())
        if d:
            n = int(d[:3])
            break
    try:
        wanted_shapes = int(float(want_count))
    except (TypeError, ValueError):
        wanted_shapes = -1
    wanted_gap = str(want_gap).strip().lower()
    if g is None or n is None:
        return {'obs': 'unread', 'exp': 'broken at the fold',
                'verdict': 'the crease line or the number of black shapes could not be read'}
    ok = (g == wanted_gap and n == wanted_shapes)
    return {'obs': 'broken at the fold' if ok else 'carried over the fold',
            'exp': 'broken at the fold', 'shapes': float(n), 'gap': g,
            'verdict': 'the crease line reads as ' + g + ' with ' + str(n)
                       + ' separate black shapes; the material rule wants ' + wanted_gap
                       + ' and ' + str(wanted_shapes)}

# end of code_fold_break
