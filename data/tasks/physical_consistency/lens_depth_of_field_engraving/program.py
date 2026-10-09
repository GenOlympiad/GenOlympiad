# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# shared code: code_dof
def dof_window_match(node, want):
    """Check the two read distances fall in the near and far reference ranges."""
    digit_texts = []
    for a in (node or {}).get('answers') or []:
        digit_texts.append(''.join(c for c in str(a) if c.isdigit() or c == '.'))
    lo1, hi1, lo2, hi2 = [float(x) for x in str(want).split(',')]
    distances = sorted(float(v) for v in digit_texts if v.replace('.', '', 1).isdigit())
    in_range = (len(distances) == 2 and lo1 <= distances[0] <= hi1 and lo2 <= distances[1] <= hi2)
    return {'state': 'match' if in_range else 'off', 'n': len(distances),
            'verdict': 'the two boxes read %s'
                       % (' '.join(str(n) for n in distances) or 'nothing')}

# end of code_dof

# shared code: code_one_word
def one_word_match(node, want):
    """Check that a single word was read and that it starts like the reference word."""
    words = [str(x).strip().lower() for x in (node or {}).get('answers') or []]
    target = str(want).strip().lower()
    matched = len(words) == 1 and bool(target) and words[0].startswith(target[:2])
    return {'state': 'match' if matched else 'off', 'n': len(words),
            'verdict': 'read %s, the optics give %s'
                       % ('|'.join(words) or 'nothing', target)}

# end of code_one_word
