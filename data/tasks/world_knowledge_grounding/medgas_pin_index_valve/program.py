# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# code: yokes_home_code
def check_yoke_seats(keys, seats, want):
    """Whether every yoke sits the way the reference seat list says, with the count."""
    wanted = dict(p.split('=') for p in str(want).split(',') if p.count('=') == 1)
    keys_read = [str(a).strip().upper() for a in ((keys or {}).get('answers') or [])]
    seats_read = [str(a).strip().lower() for a in ((seats or {}).get('answers') or [])]
    seat_by_key = dict(zip(keys_read, seats_read))
    n = sum(1 for k in wanted if seat_by_key.get(k.strip().upper(), '') == wanted[k].strip().lower())
    return {'ok': 'yes' if wanted and n == len(wanted) else 'no', 'n': n,
            'verdict': '%d of the %d yokes sit the way the pin index leaves them'
                       % (n, len(wanted))}

# end of yokes_home_code

# code: shoulder_code_code
def check_shoulder_colours(keys, cols, want):
    """Whether every cylinder shoulder has the colour the code gives its gas, with the count."""
    wanted = dict(p.split('=') for p in str(want).split(',') if p.count('=') == 1)
    keys_read = [str(a).strip().upper() for a in ((keys or {}).get('answers') or [])]
    colours_read = [str(a).strip().lower() for a in ((cols or {}).get('answers') or [])]
    colour_by_key = dict(zip(keys_read, colours_read))
    n = sum(1 for k in wanted if colour_by_key.get(k.strip().upper(), '') == wanted[k].strip().lower())
    return {'ok': 'yes' if wanted and n == len(wanted) else 'no', 'n': n,
            'verdict': '%d of the %d shoulders carry the finish the code gives their gas'
                       % (n, len(wanted))}

# end of shoulder_code_code
