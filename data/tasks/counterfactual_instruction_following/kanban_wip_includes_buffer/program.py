# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts, labelled_pairs
# end of helpers

# shared code: code_number_list
def read_distinct_figures(node):
    """The distinct figures read, sorted in numeric order."""
    import re
    seen, vals = set(), []
    for a in (node or {}).get('answers') or []:
        m = re.findall(r'\d+(?:\.\d+)?', str(a).replace(',', ''))
        if not m:
            continue
        figure = ''.join(c for c in m[0] if c.isdigit() or c == '.')
        if '.' in figure:
            figure = figure.rstrip('0').rstrip('.')
        if not figure or figure in seen:
            continue
        seen.add(figure)
        vals.append(figure)
    vals.sort(key=lambda s: (len(s.split('.')[0]), s))
    seq = ' '.join(vals)
    return {'seq': seq or 'nothing read', 'n': len(vals),
            'verdict': 'read %d distinct figures in order: %s' % (len(vals), seq or 'none')}

# end of code_number_list

# shared code: code_ledger_tie
def windows_match_counts(letters, windows, counts):
    """Check each rail's tally window figure against the number of tickets it carries."""
    def digits(raw):
        txt = ''.join(c if c.isdigit() else ' ' for c in str(raw)).split()
        return txt[0].lstrip('0') or '0' if txt else None
    letter_reads = (letters or {}).get('answers') or []
    window_reads = (windows or {}).get('answers') or []
    count_reads = (counts or {}).get('answers') or []
    rows, bad = [], []
    for i, raw in enumerate(letter_reads):
        key = ''.join(c for c in str(raw).lower() if c.isalnum())
        if not key or i >= len(window_reads) or i >= len(count_reads):
            continue
        w, c = digits(window_reads[i]), digits(count_reads[i])
        if w is None or c is None:
            continue
        rows.append(key)
        if w != c:
            bad.append('%s says %s but carries %s' % (key, w, c))
    if not rows:
        return {'txt': 'no rail gave a letter, a window and a count together',
                'verdict': 'the tie could not be taken on any rail'}
    if bad:
        return {'txt': '; '.join(sorted(bad)),
                'verdict': 'the books disagree: %s' % '; '.join(sorted(bad))}
    return {'txt': 'every window agrees with its rail',
            'verdict': 'all %d rails agree with their own tally windows' % len(rows)}

# end of code_ledger_tie
