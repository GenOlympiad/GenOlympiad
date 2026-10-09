# code: helpers
from genolympiad.task_helpers import check_permitted_characters, count_confirmed_cutouts
# end of helpers

# code: dedup_code
def collision_suffix_check(node):
    """Whether the clashing name appears once bare and once with the -2 suffix."""
    seen = [str(t or '').strip().lower() for t in (node or {}).get('answers') or []]
    base = 'quayside crane inspectio'
    bare = sum(1 for t in seen if t == base)
    tail = sum(1 for t in seen if t == base + '-2')
    state = 'ok' if bare == 1 and tail == 1 else 'bad'
    return {'state': state, 'rows': len(seen), 'verdict': 'the cut name appears %d time(s) bare and %d time(s) with the -2 tail -> %s' % (bare, tail, state)}

# end of dedup_code

# code: junk_code
def trailing_mark_fixes(node):
    """Count the two names that had to lose a trailing mark and came back exactly right."""
    seen = [str(t or '').strip().lower() for t in (node or {}).get('answers') or []]
    want = ['berth 4 mooring test', 'lifeboat drill briefing']
    hit = sum(1 for w in want if w in seen)
    return {'n': hit, 'rows': len(seen), 'verdict': '%d of the 2 names that had to lose a trailing mark came back exactly right' % hit}

# end of junk_code
