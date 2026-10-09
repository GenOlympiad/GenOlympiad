# code: bearing_gap_code
def smoke_direction_gap(node, want):
    """Angle between the smoke direction read and the expected duct bearing."""
    bearing_of = {'top': 0.0, 'top right': 45.0, 'right': 90.0, 'bottom right': 135.0,
         'bottom': 180.0, 'bottom left': 225.0, 'left': 270.0, 'top left': 315.0}
    answers = (node or {}).get('answers') or []
    s = str(answers[0]).strip().lower().replace('-', ' ') if answers else ''
    if s not in bearing_of:
        return {'gap': 180.0, 'verdict': 'the smoke direction came back as "%s", which is not one of the eight named directions, so it is scored as a full miss' % s}
    gap = abs((bearing_of[s] - float(want) + 180.0) % 360.0 - 180.0)
    return {'gap': gap, 'verdict': 'the smoke runs to the %s of the frame, %.0f degrees off the duct arrow' % (s, gap)}

# end of bearing_gap_code
