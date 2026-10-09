# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# code: rating_code
def position_score(label_read, pose, digits):
    """Half for a carton position figure allowed overhead, half for the underside pose."""
    import re
    s = str((label_read.get('answers') or [''])[0] or '').upper()
    m = re.search(r'(\d{4})', s)
    class_code = m.group(1) if m else ''
    pose_word = str((pose.get('answers') or [''])[0] or '').strip().lower()
    points = (1.0 if (class_code and class_code[2] in list(digits)) else 0.0) + (1.0 if pose_word.startswith('underside') else 0.0)
    return {'frac': points / 2.0, 'marking': s or 'none', 'pose': pose_word or 'none',
            'verdict': 'carton reads %s so its position figure is %s ; the man is working on the %s' % (s or 'none', class_code[2:3] or '?', pose_word or 'none')}

# end of rating_code

# code: current_code
def current_check(label_read, lamp, table):
    """Whether the lit current lamp is one the table allows for this electrode."""
    import re
    s = str((label_read.get('answers') or [''])[0] or '').upper()
    m = re.search(r'(\d{4})', s)
    allowed = [str(x).lower() for x in (table.get(m.group(1)[3], []) if m else [])]
    lamp_word = str((lamp.get('answers') or [''])[0] or '').strip().lower().replace(' ', '')
    return {'ok': 'yes' if (lamp_word and lamp_word in allowed) else 'no', 'allowed': allowed, 'setting': lamp_word or 'none',
            'verdict': 'carton reads %s ; that covering runs on %s ; the lit lamp is %s' % (s or 'none', '/'.join(allowed) or 'nothing', lamp_word or 'none')}

# end of current_code
