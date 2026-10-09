# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# shared code: code_b9f3dd0aaa33
def coin_total(coins, values):
    """Sum the face values read from every boxed coin in the return tray."""
    import re
    boxes = list((coins or {}).get('geometry') or [])
    answers = list((values or {}).get('answers') or [])
    if not boxes or len(boxes) != len(answers):
        return {'total': None, 'faces': None, 'unreadable': True}
    faces = []
    for a in answers:
        m = re.search(r'\d+', str(a).replace(',', ''))
        if not m:
            return {'total': None, 'faces': None, 'unreadable': True}
        faces.append(int(m.group(0)))
    return {'total': sum(faces), 'faces': faces, 'n_coins': len(faces), 'unreadable': False}

# end of code_b9f3dd0aaa33

# code: joint_code
def final_state_correct(display, flap_read, change, want_display, want_change):
    """1 if the display, change total and flap state all match the reference, else 0."""
    try:
        display_value = float(display)
        change_value = float(change)
    except Exception:
        return 0.0
    ok_disp = abs(display_value - float(want_display)) < 0.5
    ok_chg = abs(change_value - float(want_change)) < 0.5
    ok_dsp = isinstance(flap_read, str) and flap_read.strip().lower().startswith('yes')
    return 1.0 if (ok_disp and ok_chg and ok_dsp) else 0.0

# end of joint_code
