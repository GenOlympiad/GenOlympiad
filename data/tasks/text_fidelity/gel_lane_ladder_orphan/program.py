# code: helpers
from genolympiad.task_helpers import sweep_holds_nothing_banned
# end of helpers

# shared code: code_gel
def _clean(node):
    out = []
    for raw in (node or {}).get('answers') or []:
        t = ' '.join(str(raw or '').lower().split()).strip(' .,:-')
        if t and t != 'none':
            out.append(t)
    return out
def sample_order_matches(lanes, rows, ladder):
    """Whether the gel labels, ladder removed, read in the same order as the table rows."""
    gel_labels, table_rows = _clean(lanes), _clean(rows)
    if not gel_labels or not table_rows:
        return {'tag': 'no', 'refused': True,
                'verdict': 'the lane labels or the table rows came back empty -> abstain'}
    keep = [x for x in gel_labels if x != str(ladder).lower()]
    return {'tag': 'yes' if keep == table_rows else 'no',
            'verdict': 'lanes left to right: %s; table rows top to bottom: %s'
                       % (', '.join(keep), ', '.join(table_rows))}
def ladder_left_out_of_table(lanes, rows, ladder, want):
    """Whether the ladder is on the gel but not in the table, which lists the samples."""
    gel_labels, table_rows = _clean(lanes), _clean(rows)
    if not gel_labels or not table_rows:
        return {'tag': 'no', 'refused': True,
                'verdict': 'the lane labels or the table rows came back empty -> abstain'}
    ladder_key = str(ladder).lower()
    ok = ladder_key in gel_labels and ladder_key not in table_rows and ','.join(sorted(set(table_rows))) == str(want)
    return {'tag': 'yes' if ok else 'no',
            'verdict': 'the table lists %s' % ', '.join(sorted(set(table_rows)))}

# end of code_gel
