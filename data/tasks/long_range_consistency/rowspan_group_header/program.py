# code: helpers
from genolympiad.task_helpers import count_as_read, count_confirmed_cutouts
# end of helpers

# code: span_law_code
def _geo(r):
    if isinstance(r, dict):
        return r.get('geometry') or []
    return r or []
def _first_answer(r):
    if isinstance(r, dict):
        a = r.get('answers') or [None]
        return a[0]
    return r
def first_int(a):
    import re
    m = re.findall(r'\d+', str(a))
    return int(m[0]) if m else None
def group_header_spans(categories, nlabel, nrow, reference):
    """Score 1 when each merged category box spans as many rows as its group has items."""
    category_boxes = [[float(v) for v in b] for b in _geo(categories)]
    want = [int(x) for x in reference['spans']]
    n = len(want)
    total = sum(want)
    label_count = first_int(_first_answer(nlabel))
    row_count = first_int(_first_answer(nrow))
    if not category_boxes or label_count is None or row_count is None:
        return {'frac': 0.0, 'no_read': True,
                'verdict': 'the category cells or the row counts could not be read'}
    if label_count != n:
        return {'frac': 0.0, 'no_read': False, 'spans': None, 'labels': label_count, 'rows': row_count,
                'verdict': ('%d category labels are printed in the CATEGORY column but the '
                            'table has %d categories -- the header is not written once per '
                            'group -> frac 0.0' % (label_count, n))}
    if row_count != total:
        return {'frac': 0.0, 'no_read': False, 'spans': None, 'labels': label_count, 'rows': row_count,
                'verdict': ('the table prints %d item rows, the spec lists %d -> frac 0.0'
                            % (row_count, total))}
    if len(category_boxes) != n:
        return {'frac': 0.0, 'no_read': False, 'spans': None, 'labels': label_count, 'rows': row_count,
                'verdict': ('%d merged CATEGORY cells were located for %d categories '
                            '-> frac 0.0' % (len(category_boxes), n))}
    category_boxes.sort(key=lambda b: b[0])
    heights = [b[2] - b[0] for b in category_boxes]
    if min(heights) <= 0:
        return {'frac': 0.0, 'no_read': True, 'verdict': 'a degenerate category cell box'}
    pitch = sum(heights) * 1.0 / row_count
    measured_spans = [h / pitch for h in heights]
    offsets = [abs(measured_spans[i] - want[i]) for i in range(n)]
    ok = all(o <= 0.4 for o in offsets)
    spans = [round(m, 2) for m in measured_spans]
    worst = max(range(n), key=lambda i: offsets[i])
    verdict = ('merged CATEGORY cells measure %s row-heights, group sizes %s -> frac %s'
               % (spans, want, 1.0 if ok else 0.0))
    if not ok:
        verdict += ('; the %s cell covers %.2f rows, not %d'
                    % (reference['cats'][worst], measured_spans[worst], want[worst]))
    return {'frac': 1.0 if ok else 0.0, 'no_read': False, 'spans': spans,
            'labels': label_count, 'rows': row_count, 'verdict': verdict}

# end of span_law_code
