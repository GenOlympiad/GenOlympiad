# shared code: code_c35dabd68b55
def colour_name(v):
    s = str(v or '').strip().lower()
    for c in ('green', 'red', 'blue', 'white', 'black', 'yellow', 'orange', 'purple', 'pink',
              'brown', 'grey', 'gray'):
        if c in s:
            return c
    return ''


def _yn(v):
    s = str(v or '').strip().lower()
    if s.startswith('y'):
        return 'yes'
    if s.startswith('n'):
        return 'no'
    if 'there is a white' in s or 'has a white' in s:
        return 'yes'
    if 'no white' in s or 'not' in s:
        return 'no'
    return ''


def check_skin_sheet(eye, body, hat, left_sleeve, right_sleeve, reference):
    """Compare each skin region read against the brief, flagging mirrored arm blocks."""
    got = {'eyes': colour_name(eye), 'body': colour_name(body), 'hat': colour_name(hat),
           'left_sleeve_stripe': _yn(left_sleeve), 'right_sleeve_stripe': _yn(right_sleeve)}
    want = {'eyes': str(reference.get('expect_eyes')).lower(),
            'body': str(reference.get('expect_body')).lower(),
            'hat': str(reference.get('expect_hat')).lower(),
            'left_sleeve_stripe': str(reference.get('expect_left_sleeve_stripe')).lower(),
            'right_sleeve_stripe': str(reference.get('expect_right_sleeve_stripe')).lower()}
    ok = {k: (got[k] == want[k]) for k in want}
    n = sum(1 for v in ok.values() if v)
    mirrored = (got['right_sleeve_stripe'] == 'yes' and got['left_sleeve_stripe'] == 'no')
    crash = None
    if mirrored:
        crash = ('sleeve stripe painted into the MIRRORED arm rectangle -- the left arm block and '
                 'the right arm block are on opposite sides of the sheet')
    elif not ok['left_sleeve_stripe'] and got['left_sleeve_stripe'] == 'no' \
            and got['right_sleeve_stripe'] == 'no':
        crash = ('neither arm rectangle carries the sleeve stripe -- the sheet '
                 'was laid out to its own plan, not to the published one')
    elif n < 5:
        crash = 'brief items painted into the wrong rectangles: %r' % (
            [k for k, v in ok.items() if not v],)
    sleeves_ok = 1.0 if (ok['left_sleeve_stripe'] and ok['right_sleeve_stripe']) else 0.0
    return {'read': got, 'want': want, 'ok': ok, 'n_ok': n, 'frac': round(n / 5.0, 4),
            'sleeves_ok': sleeves_ok, 'mirrored': bool(mirrored), 'crash': crash}

# end of code_c35dabd68b55
