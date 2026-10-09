# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# shared code: code_flip_tally
def count_side_flips(node):
    """Count adjacent print pairs whose arch side changes."""
    sides = [str(x).strip().lower()[:1] for x in (node or {}).get('answers') or []]
    pairs = max(len(sides) - 1, 0)
    flips = sum(1 for i in range(pairs) if sides[i] and sides[i + 1] and sides[i] != sides[i + 1])
    return {'split': 'flips:%d|of:%d' % (flips, pairs),
            'verdict': '%d of the %d adjacent print pairs change arch side' % (flips, pairs)}

# end of code_flip_tally
