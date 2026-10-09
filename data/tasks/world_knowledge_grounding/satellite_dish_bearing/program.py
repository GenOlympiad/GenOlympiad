# shared code: code_2d107f21565b
def compass_to_degrees(s):
    """Convert an eight point compass word to a bearing in degrees."""
    bearings={'N':0.0,'NE':45.0,'E':90.0,'SE':135.0,'S':180.0,'SW':225.0,'W':270.0,'NW':315.0}
    if s is None: return None
    return bearings.get(str(s).strip().upper())

# end of code_2d107f21565b
