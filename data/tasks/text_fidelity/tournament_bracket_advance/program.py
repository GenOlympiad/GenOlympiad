# code: law_code
def check_bracket_advance(sf1top, ftop, fbot, want_sf1top, want_f0, want_f1, sfw0, sfw1):
    """1.0 if the semi-final slot and both finalists match the bracket, in order."""
    import re
    def norm(s):
        return re.sub(r'[^a-z]', '', str(s).lower())
    if norm(sf1top) != norm(want_sf1top):
        return 0.0
    final_top = norm(ftop); final_bottom = norm(fbot)
    if {final_top, final_bottom} != {norm(sfw0), norm(sfw1)}:
        return 0.0
    if final_top != norm(want_f0) or final_bottom != norm(want_f1):
        return 0.0
    return 1.0

# end of law_code
