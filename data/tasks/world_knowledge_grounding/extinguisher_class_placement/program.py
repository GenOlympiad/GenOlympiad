# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# shared code: code_extinguisher_class
def check_extinguisher_letters(letter, room, table):
    """Compare each extinguisher's class letter with the one its room requires."""
    letters = ((letter or {}).get('answers') or [])
    rooms = ((room or {}).get('answers') or [])
    def required_letter(r):
        return ([v for k, v in table if k in str(r).strip().lower()] or [None])[0]
    required = [required_letter(r) for r in rooms]
    read = [str(x).strip().lower()[:1] for x in letters]
    n_right = sum(1 for w, g in zip(required, read) if w and g == w)
    n_wrong = sum(1 for w, g in zip(required, read) if w and g != w)
    n_lettered = sum(1 for g in read if g in ('a', 'b', 'c', 'd', 'k'))
    return {'n_ok': n_right, 'n_bad': n_wrong, 'n_lettered': n_lettered, 'n': len(required), 'want': required,
            'verdict': 'rooms read %s -> letters required %s, letters read %s: %d right, %d wrong, %d cylinders carry a real class letter' % (rooms, required, read, n_right, n_wrong, n_lettered)}

# end of code_extinguisher_class
