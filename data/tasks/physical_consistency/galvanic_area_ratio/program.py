# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# shared code: code_galvanic
def first_answer(node):
    ans = node.get('answers') if isinstance(node, dict) else None
    ans = list(ans) if isinstance(ans, (list, tuple)) else []
    return str(ans[0] if ans else '').strip().lower()

def _part(node):
    s = first_answer(node)
    return 'panel' if 'panel' in s else ('fasteners' if 'fasten' in s else '?')

def _depth(node):
    s = first_answer(node)
    return 'through' if 'through' in s else ('surface' if 'surface' in s else '?')

def _where(node):
    s = first_answer(node)
    if 'contact' in s:
        return 'contact'
    if 'spread' in s:
        return 'spread'
    return '?'

def attacked_parts_score(read_a, read_b, contact_a, want_a, want_b, want_where):
    """The share of three reads that match: the part eaten on each sample and where A is worst."""
    part_a, part_b, where_read = _part(read_a), _part(read_b), _where(contact_a)
    hits = (1 if part_a == want_a else 0) + (1 if part_b == want_b else 0) + (1 if where_read == str(want_where).strip().lower() else 0)
    return {'a': part_a, 'b': part_b, 'where_a': where_read, 'hits': hits, 'frac': hits / 3.0,
            'verdict': 'sample A eats its %s (worst %s), sample B eats its %s' % (part_a, where_read, part_b)}

def attack_depth_order(read_a, read_b, want_a, want_b):
    """Whether the attack depth read on each sample matches the expected depth."""
    depth_a, depth_b = _depth(read_a), _depth(read_b)
    ok = (depth_a == want_a and depth_b == want_b)
    return {'a': depth_a, 'b': depth_b,
            'verdict': 'small-anode-worse' if ok else 'not-ordered',
            'note': 'A reads %s, B reads %s' % (depth_a, depth_b)}

# end of code_galvanic
