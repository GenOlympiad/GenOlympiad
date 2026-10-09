# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# code: sym_pairs_code
def read_opening_symbols(tag_reads, apex_reads, style_reads):
    """Sorted tag, apex and style triples read from the opening symbols on the elevation."""
    tags = [str(x).strip().lower().replace(' ', '') for x in (tag_reads or {}).get('answers') or []]
    apex = [str(x).strip().lower() for x in (apex_reads or {}).get('answers') or []]
    styles = [str(x).strip().lower() for x in (style_reads or {}).get('answers') or []]
    rows = []
    for i, tag in enumerate(tags):
        e1 = apex[i] if i < len(apex) else '?'
        e2 = styles[i] if i < len(styles) else '?'
        rows.append('%s:%s:%s' % (tag, e1, e2))
    s = '|'.join(sorted(rows))
    return {'canon': s, 'verdict': 'opening symbols read back as %s' % (s or 'nothing')}

# end of sym_pairs_code

# code: sched_pairs_code
def read_schedule_entries(reads):
    """Sorted tag, hinge side and swing triples read from the window schedule lines."""
    rows = []
    for t in (reads or {}).get('answers') or []:
        line = str(t).lower()
        tag = 'w1' if 'w1' in line.replace(' ', '') else ('w2' if 'w2' in line.replace(' ', '') else ('w3' if 'w3' in line.replace(' ', '') else '?'))
        hinge = 'left' if 'left' in line else ('right' if 'right' in line else ('sill' if 'sill' in line else '?'))
        swing = 'inward' if ('inward' in line or 'tilts in' in line) else ('outward' if 'outward' in line else '?')
        rows.append('%s:%s:%s' % (tag, hinge, swing))
    s = '|'.join(sorted(rows))
    return {'canon': s, 'verdict': 'schedule read back as %s' % (s or 'nothing')}

# end of sched_pairs_code
