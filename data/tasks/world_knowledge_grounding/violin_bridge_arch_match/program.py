# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# code: arc_fit_code
def bridge_top_match(shape_read, centre_read, shape_expected, centre_expected):
    """Score whether the read bridge top shape and highest point match the expected ones."""
    shape_answers = [str(v).strip().lower() for v in ((shape_read or {}).get('answers') or [])]
    centre_answers = [str(v).strip().lower() for v in ((centre_read or {}).get('answers') or [])]
    shape = shape_answers[0] if shape_answers else ''
    centre = centre_answers[0] if centre_answers else ''
    return {'shape': 1 if (shape and shape == str(shape_expected).strip().lower()) else 0,
            'centre': 1 if (centre and centre == str(centre_expected).strip().lower()) else 0,
            'verdict': 'the top reads %r and its highest point %r' % (shape or 'nothing', centre or 'nothing')}

# end of arc_fit_code

# code: feet_flush_code
def count_flush_feet(foot_reads):
    """Count the bridge feet read as sitting flush along their whole length."""
    answers = [str(a).strip().lower() for a in ((foot_reads or {}).get('answers') or [])]
    n = sum(1 for s in answers if s.startswith('sitting flush'))
    return {'n': n, 'read': len(answers), 'verdict': '%d of the %d feet are carried along their whole length' % (n, len(answers))}

# end of feet_flush_code
