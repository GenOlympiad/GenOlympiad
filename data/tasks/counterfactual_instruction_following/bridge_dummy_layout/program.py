# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# code: dummy_side_code
def dummy_side(keys, faces, sides, seat, want):
    """How far the dummy's trump column lies from its seat's right hand, in degrees."""
    side_degrees = {'top': 0.0, 'top right': 45.0, 'right': 90.0, 'bottom right': 135.0,
         'bottom': 180.0, 'bottom left': 225.0, 'left': 270.0, 'top left': 315.0}
    ks = [str(a).strip().upper() for a in ((keys or {}).get('answers') or [])]
    fs = [str(a).strip().lower() for a in ((faces or {}).get('answers') or [])]
    ss = [str(a).strip().lower().replace('-', ' ') for a in ((sides or {}).get('answers') or [])]
    row = dict((k, (f, s)) for k, f, s in zip(ks, fs, ss))
    f, s = row.get(str(seat).strip().upper(), ('none', 'none'))
    angle_gap = 180.0 if f != 'faces' or s not in side_degrees else abs((side_degrees[s] - float(want) + 180.0) % 360.0 - 180.0)
    return {'gap': angle_gap, 'seen': f, 'verdict': 'the hand at %s reads %s and its trump column lies %.0f degrees from that seat own right hand' % (seat, f, angle_gap)}

# end of dummy_side_code

# code: backs_kept_code
def backs_kept(keys, faces, seats, want):
    """Count the listed seats whose hand is read as face down."""
    seats_wanted = [w.strip().upper() for w in str(seats).split(',') if w.strip()]
    seat_reads = [str(a).strip().upper() for a in ((keys or {}).get('answers') or [])]
    face_reads = [str(a).strip().lower() for a in ((faces or {}).get('answers') or [])]
    row = dict(zip(seat_reads, face_reads))
    n = sum(1 for w in seats_wanted if row.get(w) == 'backs')
    return {'n': n, 'asked': len(seats_wanted), 'verdict': '%d of the %d seats still hold their cards face down, against the %s this deal calls for' % (n, len(seats_wanted), want)}

# end of backs_kept_code
