# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts, map_answer_to_token
# end of helpers

# shared code: code_size_pairs
def read_piece_sizes(node):
    """The distinct width by length pairs marked on the pattern pieces."""
    import re
    rows = []
    for raw in (node or {}).get('answers') or []:
        nums = re.findall(r'\d+(?:\.\d+)?', str(raw).replace(',', ''))
        if len(nums) >= 2:
            pair = sorted(float(x) for x in nums[:2])
            rows.append('%g x %g' % (pair[0], pair[1]))
    sizes = ', '.join(sorted(set(rows)))
    return {'seq': sizes or 'nothing read', 'n': len(rows), 'verdict': 'the pieces are marked %s' % (sizes or 'nothing')}

# end of code_size_pairs

# shared code: code_token_set
def distinct_answers(node):
    """The distinct answers read, lowercased with only letters and digits kept."""
    seen = set()
    for a in (node or {}).get('answers') or []:
        w = ''.join(c for c in str(a).lower() if c.isalnum())
        if w:
            seen.add(w)
    joined = ' '.join(sorted(seen))
    return {'seq': joined or 'nothing read', 'n': len(seen),
            'verdict': 'read %d distinct answers: %s' % (len(seen), joined or 'none')}

# end of code_token_set
