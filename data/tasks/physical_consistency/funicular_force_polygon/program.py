# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# shared code: code_num_set
def read_number_set(cert, texts):
    """Collect the distinct numbers read from the confirmed reaction labels."""
    import re
    vals = []
    confirmed = [str(y).strip().lower().startswith('y') for y in ((cert or {}).get('answers') or [])]
    for i, t in enumerate(((texts or {}).get('answers') or [])):
        m = re.search(r'-?\d+(?:\.\d+)?', str(t))
        if m and (i >= len(confirmed) or confirmed[i]):
            vals.append('%g' % float(m.group(0)))
    seq = ', '.join(sorted(set(vals)))
    return {'seq': seq, 'n': len(set(vals)), 'verdict': 'figures read as: %s' % (seq or 'none')}

# end of code_num_set

# shared code: code_pair_num
def read_tagged_numbers(cert, keys, vals):
    """Collect the distinct tag and number pairs read from the confirmed dip labels."""
    import re
    confirmed = [str(y).strip().lower().startswith('y') for y in ((cert or {}).get('answers') or [])]
    tags = [''.join(str(a).lower().split()).strip('.,:') for a in ((keys or {}).get('answers') or [])]
    rows = []
    for i, t in enumerate(((vals or {}).get('answers') or [])):
        m = re.search(r'-?\d+(?:\.\d+)?', str(t))
        if m and i < len(tags) and tags[i] and (i >= len(confirmed) or confirmed[i]):
            rows.append('%s %g' % (tags[i], float(m.group(0))))
    seq = ', '.join(sorted(set(rows)))
    return {'seq': seq, 'n': len(set(rows)), 'verdict': 'rows read as: %s' % (seq or 'none')}

# end of code_pair_num
