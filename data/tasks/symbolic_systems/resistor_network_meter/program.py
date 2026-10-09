# code: gauge_code
def width_height(p):
    try:
        with open(p, 'rb') as f:
            head = f.read(32)
        if head[:8] == b'\x89PNG\r\n\x1a\n':
            import struct
            w, h = struct.unpack('>II', head[16:24])
            if w > 0 and h > 0:
                return float(w), float(h)
    except Exception:
        pass
    return 1.0, 1.0


def read_needle_value(needle, reference, image):
    """Turn the needle bearing on the ohmmeter dial into the resistance it points at."""
    import math
    W, H = width_height(image) if isinstance(image, str) else (1.0, 1.0)
    out = {'value': None, 'bearing': None, 'degenerate': False, 'caption': 'needle unread'}
    g = (needle or {}).get('geometry')
    if not g or len(g) < 4:
        out['degenerate'] = True
        return out
    py, px, ty, tx = [float(v) for v in g[:4]]
    dx = (tx - px) * W / 1000.0
    dy = (ty - py) * H / 1000.0
    if math.hypot(dx, dy) < 8.0:
        out['degenerate'] = True
        return out
    bearing = math.degrees(math.atan2(dx, -dy)) % 360.0
    vmin = float(reference.get('vmin', 0.0) or 0.0)
    vmax = float(reference.get('vmax', 1000.0) or 1000.0)
    start = float(reference.get('start_deg', 0.0) or 0.0)
    sweep = float(reference.get('sweep_deg', 360.0) or 360.0)
    f = ((bearing - start) % 360.0) / max(1e-6, sweep)
    value = vmin + f * (vmax - vmin)
    out.update({'value': round(value, 2), 'bearing': round(bearing, 2),
                'caption': 'needle %.1f deg -> %.1f ohm (target %.1f)'
                           % (bearing, value, float(reference.get('req', 0.0) or 0.0))})
    try:
        _core = float(reference.get('band_core', 0.0) or 0.0)
        _marg = float(reference.get('band_margin', 0.0) or 0.0)
        _req = float(reference.get('req', 0.0) or 0.0)
        _span = (vmax - vmin) or 1.0
        if _core + _marg > 0 and W > 1.0:
            _b = [(start + (_req + s * (_core + _marg) - vmin) / _span * sweep) % 360.0
                  for s in (-1.0, 1.0)]
            out['_tolerance_viz'] = [
                {'shape': 'sector',
                 'pivot': [px * W / 1000.0, py * H / 1000.0],
                 'edges_deg': _b,
                 'radius_px': round(max(math.hypot(dx, dy) * 1.15, 40.0), 1),
                 'caption': 'the needle had to point between these two dashed edges to score '
                            'anything; full marks only close to the required value',
                 'label': 'scoring boundary'}]
    except Exception:
        pass
    return out

# end of gauge_code
