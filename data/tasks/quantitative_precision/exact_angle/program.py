# code: ang_code
def plank_angle(axis_read, image, target):
    """The plank lean in degrees from horizontal, from the confirmed axis line."""
    import math
    W, H = image.size
    axis_geometry = (axis_read or {}).get('geometry')
    if not axis_geometry or len(axis_geometry) < 4:
        return {'deg': None, 'degenerate': True, 'refused': True, 'why': 'no confirmed plank axis'}
    y0, x0, y1, x1 = [float(v) for v in axis_geometry[:4]]
    ly, lx = y0 * H / 1000.0, x0 * W / 1000.0
    hy, hx = y1 * H / 1000.0, x1 * W / 1000.0
    dx, dy = abs(hx - lx), abs(hy - ly)
    span = math.hypot(dx, dy)
    if span < 0.25 * math.hypot(W, H) or dx < 0.10 * W:
        return {'deg': None, 'degenerate': True, 'refused': span < 0.25 * math.hypot(W, H), 'dx_px': round(dx, 1),
                'dy_px': round(dy, 1), 'span_px': round(span, 1)}
    deg = round(math.degrees(math.atan2(dy, dx)), 2)
    return {'deg': deg, 'dx_px': round(dx, 1), 'dy_px': round(dy, 1),
            'span_px': round(span, 1), 'degenerate': False,
            'caption': 'plank axis as confirmed by the ring: lean %s deg '
                       'vs target %s deg (core 3.0)' % (deg, target),
            'ray': {'confirmed': True, 'geometry': [y0, x0, y1, x1]}}

# end of ang_code
