# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts, select_item_numbers
# end of helpers

# code: numset_code
def read_line_numbers(node):
    """Collect the distinct line numbers read, sorted, as a comma-separated list."""
    keep = set()
    for raw in (node or {}).get('answers') or []:
        txt = ''.join(ch if ch.isdigit() else ' ' for ch in str(raw or ''))
        for tok in txt.split():
            keep.add(tok.lstrip('0') or '0')
    seq = ', '.join(sorted(keep, key=lambda s: (len(s), s)))
    return {'seq': seq, 'n': len(keep),
            'verdict': 'the printed lines set in from the left read back as %s' % (seq or 'none')}

# end of numset_code
