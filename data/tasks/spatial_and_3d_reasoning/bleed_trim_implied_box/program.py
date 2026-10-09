# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# shared code: code_bleed_tally
def count_bleed_corners(reads):
    """Count the corners where the picture runs past the marks and where it stops."""
    answers = [str(x).strip().lower() for x in (reads or {}).get('answers') or []]
    n_continues = sum(1 for w in answers if w.startswith('c'))
    n_stops = sum(1 for w in answers if w.startswith('s'))
    return {'split': 'continues:%d|stops:%d' % (n_continues, n_stops),
            'verdict': 'the picture runs past the marks at %d corner(s) and stops at %d' % (n_continues, n_stops)}

# end of code_bleed_tally
