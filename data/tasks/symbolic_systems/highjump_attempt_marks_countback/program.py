# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# shared code: code_token_seq
def attempts_by_bib(keys, vals, order):
    """Line up each athlete's attempt marks by bib number, in the reference bib order."""
    key_answers = keys.get('answers') if isinstance(keys, dict) else None
    key_answers = list(key_answers) if isinstance(key_answers, (list, tuple)) else []
    value_answers = vals.get('answers') if isinstance(vals, dict) else None
    value_answers = list(value_answers) if isinstance(value_answers, (list, tuple)) else []
    marks_by_bib = {}
    for k, v in zip(key_answers, value_answers):
        bib_digits = ''.join(c for c in str(k) if c.isdigit())
        marks_text = ' '.join(str(v).strip().lower().split())
        if bib_digits and marks_text and bib_digits not in marks_by_bib:
            marks_by_bib[bib_digits] = marks_text
    wanted_bibs = [''.join(c for c in str(p) if c.isdigit()) for p in str(order).split('|')]
    seq = '|'.join(marks_by_bib.get(k, 'unread') for k in wanted_bibs)
    return {'seq': seq, 'n': len(marks_by_bib),
            'verdict': 'attempt rows keyed by their own bib numbers: %s' % (seq or 'nothing')}

# end of code_token_seq

# shared code: code_key_pairs
def pair_keys_with_values(keys, vals):
    """List each key read beside its value, sorted and without repeats."""
    keys_read = [' '.join(str(x).strip().lower().split())
          for x in (keys or {}).get('answers') or []]
    values_read = [' '.join(str(x).strip().lower().split())
          for x in (vals or {}).get('answers') or []]
    rows = [a + ' ' + b for a, b in zip(keys_read, values_read) if a and b]
    txt = ', '.join(sorted(set(rows)))
    return {'seq': txt, 'n': len(rows), 'verdict': 'pairs read: %s' % (txt or 'nothing')}

# end of code_key_pairs
