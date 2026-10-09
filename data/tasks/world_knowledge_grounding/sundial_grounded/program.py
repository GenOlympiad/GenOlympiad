# code: d2deg_code
def compass_to_degrees(s):
    """Convert a compass direction such as NE into degrees clockwise from north."""
    bearings = {'N':0.0,'NE':45.0,'E':90.0,'SE':135.0,'S':180.0,'SW':225.0,'W':270.0,'NW':315.0}
    if s is None:
        return None
    return bearings.get(str(s).strip().upper())
# end of d2deg_code
