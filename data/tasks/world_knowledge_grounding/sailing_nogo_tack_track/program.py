# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# shared code: code_beat_legs
def check_beat_courses(course_reads):
    """Clear when every course heads northeast or northwest and no two in a row repeat."""
    allowed = ('northeast', 'northwest')
    courses = []
    for raw in (course_reads or {}).get('answers') or []:
        courses.append(''.join(c for c in str(raw).lower() if c.isalpha()))
    into_wind = [t for t in courses if t not in allowed]
    repeats = [i for i in range(1, len(courses)) if courses[i] == courses[i - 1]]
    good = len(courses) >= 2 and not into_wind and not repeats
    return {'state': 'clear' if good else 'blocked', 'n': len(courses), 'verdict': 'legs read %s, legs into the wind: %s' % (' '.join(courses) or 'nothing', ' '.join(into_wind) or 'none')}

# end of code_beat_legs

# shared code: code_sail_side
def check_sail_sides(heading_reads, side_reads, whole_boat_reads):
    """Match when each certified boat carries its sail on the side its heading requires."""
    side_for = {'northeast': 'right', 'northwest': 'left'}
    headings = (heading_reads or {}).get('answers') or []
    side_answers = (side_reads or {}).get('answers') or []
    whole_answers = (whole_boat_reads or {}).get('answers') or []
    if not (len(headings) == len(side_answers) == len(whole_answers)):
        return {'state': 'mismatch', 'n': 0,
                'verdict': 'the three reads returned %d, %d and %d cut-outs, so no boat can be paired with its own leg' % (len(headings), len(side_answers), len(whole_answers))}
    wrong_boats = []
    uncertified = 0
    for i, raw in enumerate(headings):
        if not str(whole_answers[i]).strip().lower().startswith('y'):
            uncertified += 1
            continue
        heading = ''.join(c for c in str(raw).lower() if c.isalpha())
        side = ''.join(c for c in str(side_answers[i]).lower() if c.isalpha())
        if side_for.get(heading) != side:
            wrong_boats.append(str(i + 1))
    n_boats = len(headings) - uncertified
    good = not wrong_boats and uncertified == 0 and n_boats >= 2
    return {'state': 'match' if good else 'mismatch', 'n': n_boats,
            'verdict': '%d of %d cut-outs certified one whole boat, boats whose sail sits on the wrong side: %s' % (n_boats, len(headings), ' '.join(wrong_boats) or 'none')}

# end of code_sail_side
