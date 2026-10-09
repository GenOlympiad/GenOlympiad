# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts, count_enumerated_items
# end of helpers

# code: band_sum_code
def sum_strip_counts(node, what):
    """Add up the first number read in each strip, refusing if any strip has none."""
    import re
    answers = (node or {}).get('answers') or []
    if not answers: return {'n': -1, 'unread': True, 'refused': True, 'verdict': 'no strip was read'}
    counts = []
    for a in answers:
        m = re.findall(r'\d+', str(a if a is not None else ''))
        if not m: return {'n': -1, 'unread': True, 'refused': True, 'verdict': 'a strip answered with no number -> nothing was counted'}
        counts.append(int(m[0]))
    return {'n': sum(counts), 'per_strip': counts, 'unread': False, 'verdict': '%s counted strip by strip: %s = %d' % (what, ' + '.join(str(v) for v in counts), sum(counts))}

# end of band_sum_code

# code: sparse_code
def yes_score(node):
    """1 if the answer starts with yes, else 0, refusing when nothing was read."""
    answers = (node or {}).get('answers') or []
    if not answers or answers[0] is None:
        return {'none': True, 'refused': True}
    return 1.0 if str(answers[0]).strip().lower().startswith('y') else 0.0

# end of sparse_code
