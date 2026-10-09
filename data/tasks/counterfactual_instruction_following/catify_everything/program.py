# code: headcount_code

def count_cat_objects(reference, *nodes):
    """1.0 only if every demanded object is confirmed to carry a cat feature."""
    want = int((reference or {}).get('n_objects') or len(nodes))
    names = list((reference or {}).get('objects') or [])
    rows, out = [], 1.0
    for i, nd in enumerate(nodes):
        ans = ((nd or {}).get('answers') or [None])
        a = str(ans[0] or '').strip().lower()
        nm = names[i] if i < len(names) else 'object %d' % i
        if not a:
            ok, why = 0.0, 'unreadable'
        elif a.startswith('yes'):
            ok, why = 1.0, 'yes'
        else:
            ok, why = 0.0, ('no' if a.startswith('no') else a[:24])
        rows.append('%s=%s' % (nm, why))
        out *= ok
    if len(nodes) != want:
        out = 0.0
    n_yes = sum(1 for r in rows if r.endswith('=yes'))
    return {'frac': round(out, 4), 'n_yes': n_yes, 'n_want': want,
            'per_object': rows,
            'verdict': '%d of %d demanded objects carry a cat feature -> frac %.1f | %s'
                       % (n_yes, want, out, '; '.join(rows))}

# end of headcount_code
