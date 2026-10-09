# code: tuft_gap_code
def worst_tuft_angle(keys, dirs, want):
    """The largest angle between a tuft direction read and the reference air direction there."""
    bearings = [('top right', 45.0), ('bottom right', 135.0), ('bottom left', 225.0), ('top left', 315.0),
         ('top', 0.0), ('right', 90.0), ('bottom', 180.0), ('left', 270.0)]
    want_of = dict(p.split('=') for p in str(want).split('|') if p.count('=') == 1)
    key_reads = [str(a).strip().upper() for a in ((keys or {}).get('answers') or [])]
    direction_reads = [str(a).strip().lower().replace('-', ' ') for a in ((dirs or {}).get('answers') or [])]
    gaps = [180.0] * (len(want_of) - min(len(key_reads), len(direction_reads)))
    for k, s in zip(key_reads, direction_reads):
        b = next((y for n2, y in bearings if n2 in s), None)
        want_bearing = str(want_of.get(k, '')).strip()
        gaps.append(180.0 if (b is None or not want_bearing.isdigit()) else abs((b - float(want_bearing) + 180.0) % 360.0 - 180.0))
    return {'gap': max(gaps or [180.0]), 'verdict': 'the worst tuft lies %.0f degrees from the way the air must be going there' % max(gaps or [180.0])}

# end of tuft_gap_code

# code: wall_lay_code
def count_wall_tufts_down(node):
    """Count the wall tufts read as lying flat against the wall pointing down."""
    reads = [str(a).strip().lower() for a in ((node or {}).get('answers') or [])]
    n = sum(1 for s in reads if s.startswith('flat against the wall pointing down'))
    return {'n': n, 'read': len(reads), 'verdict': '%d of the %d wall tufts are held flat and pointing down' % (n, len(reads))}

# end of wall_lay_code
