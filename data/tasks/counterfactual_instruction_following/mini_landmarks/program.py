# code: headcount_code

def all_pairs_match(confirmed_reads, reference):
    """Score 1 only if the expected number of pairs was found and every person reads as asked."""
    def m(ans, key):
        if ans is None:
            return 0.0
        a = str(ans).strip().lower()
        shorter = ('shorter' in a) or ('smaller' in a) or ('less tall' in a)
        taller = ('taller' in a) or ('bigger' in a) or ('higher' in a)
        want = str(key).strip().lower()
        if want == 'shorter':
            return 1.0 if (shorter and not taller) else 0.0
        return 1.0 if (taller and not shorter) else 0.0

    g = dict(reference or {})
    want = g.get('exp_item')
    n_want = int(g.get('n_objects') or 0)
    ans = (confirmed_reads or {}).get('answers') or []
    n_boxes = len(ans)
    n_match = sum(1 for a in ans if m(a, want) == 1.0)
    frac = 1.0 if (n_boxes == n_want and n_boxes and n_match == n_boxes) else 0.0
    return {'frac': frac, 'n_boxes': n_boxes, 'n_match': n_match, 'n_want': n_want,
            'want': str(want), 'answers': [str(a) for a in ans],
            'verdict': '%d of %d confirmed landmark-person pairs read "%s" (%d demanded) '
                       '-> frac %.1f' % (n_match, n_boxes, want, n_want, frac)}

# end of headcount_code
