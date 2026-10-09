# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# shared code: code_note_membership
def balloon_note_presence(keys, notes, want):
    """For each expected balloon, whether a note is written beside it or it is bare."""
    def lst(n):
        if isinstance(n, dict):
            n = n.get('answers') or []
        return list(n) if isinstance(n, (list, tuple)) else ([] if n is None else [n])
    keys_read = [''.join(c for c in str(k) if c.isdigit()) for k in lst(keys)]
    notes_read = [str(v).strip().lower() for v in lst(notes)]
    want = [str(w) for w in lst(want)]
    rows = align_by_printed_key([{'key': k, 'v': v} for k, v in zip(keys_read, notes_read)], want)
    got = []
    for i, w in enumerate(want):
        v = (rows[i] or {}).get('v') if i < len(rows) and isinstance(rows[i], dict) else None
        v = '' if v is None else str(v)
        bare = v in ('', 'none', 'no', 'n/a', 'na', '-', '?', 'nothing')
        got.append('%s=%s' % (w, 'bare' if bare else 'noted'))
    return {'s': ','.join(got), 'verdict': 'the balloons read %s' % (','.join(got) or 'nothing')}

# end of code_note_membership

# shared code: code_note_values
def read_carried_figures(keys, notes, want):
    """For each expected balloon, the figure written in its note, digits only."""
    def lst(n):
        if isinstance(n, dict):
            n = n.get('answers') or []
        return list(n) if isinstance(n, (list, tuple)) else ([] if n is None else [n])
    def canon(v):
        t = str(v).strip().lower().replace(' ', '').replace('+/-', '').replace('±', '')
        return ''.join(c for c in t if c.isdigit() or c in '.r')
    keys_read = [''.join(c for c in str(k) if c.isdigit()) for k in lst(keys)]
    notes_read = [canon(v) for v in lst(notes)]
    want = [str(w) for w in lst(want)]
    rows = align_by_printed_key([{'key': k, 'v': v} for k, v in zip(keys_read, notes_read)], want)
    got = []
    for i, w in enumerate(want):
        v = (rows[i] or {}).get('v') if i < len(rows) and isinstance(rows[i], dict) else ''
        got.append('%s=%s' % (w, v or 'none'))
    return {'s': ','.join(got), 'verdict': 'the carried figures read %s' % (','.join(got) or 'nothing')}

# end of code_note_values
