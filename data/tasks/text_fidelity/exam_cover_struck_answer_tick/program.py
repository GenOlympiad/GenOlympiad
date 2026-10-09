# code: helpers
from genolympiad.task_helpers import sweep_holds_nothing_banned
# end of helpers

# shared code: code_pairmap
def map_number_to_word(keys, vals):
    """Key each read word to its question number and list them in number order."""
    numbers = [''.join(c for c in str(k or '') if c.isdigit()) for k in (keys or {}).get('answers') or []]
    words = [' '.join(str(v or '').lower().split()).strip(' .,:;') for v in (vals or {}).get('answers') or []]
    rows = {}
    for i, k in enumerate(numbers):
        if k and k not in rows:
            w = words[i].split()[0] if i < len(words) and words[i] else 'nothing'
            rows[k] = w
    if not rows:
        return {'seq': 'none', 'refused': True,
                'verdict': 'no cut-out came back with a number to key on -> abstain'}
    seq = '|'.join('%s=%s' % (k, rows[k]) for k in sorted(rows, key=lambda x: int(x)))
    return {'seq': seq, 'verdict': 'the reads key back as %s' % seq}

# end of code_pairmap
