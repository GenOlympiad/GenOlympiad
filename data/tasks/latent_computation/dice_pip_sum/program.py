# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts, count_listed_items
# end of helpers

# code: pip_tally_code
def sum_top_faces(reads):
    """Sum the pips read on the dice top faces, ignoring reads outside 1 to 6."""
    import re
    answers = (reads or {}).get('answers') or []
    faces = []
    for a in answers:
        m = re.search(r'\d+', str(a))
        v = int(m.group()) if m else 0
        faces.append(v if 1 <= v <= 6 else 0)
    kept = [v for v in faces if v]
    return {'total': sum(kept), 'n': len(kept), 'asked': len(answers), 'faces': faces}

# end of pip_tally_code
