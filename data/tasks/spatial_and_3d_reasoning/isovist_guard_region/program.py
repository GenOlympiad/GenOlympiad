# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# shared code: code_leak_tally
def count_leaking_walls(node):
    """Count the walls whose yellow shading touches both sides."""
    answers = [str(x).strip().lower() for x in (node or {}).get('answers') or []]
    leaks = sum(1 for w in answers if w.startswith('y'))
    return {'split': 'leak:%d|of:%d' % (leaks, len(answers)),
            'verdict': 'yellow shading touches both sides of %d of the %d walls' % (leaks, len(answers))}

# end of code_leak_tally

# shared code: code_first_word
def first_word(node):
    """The first answer lowercased with only its letters kept."""
    answers = (node or {}).get('answers') or []
    w = str(answers[0] if answers else '').strip().lower()
    w = ''.join(ch for ch in w if ch.isalpha())
    return {'tok': w, 'verdict': 'first answer token = %s' % (w or '(empty)')}

# end of code_first_word
