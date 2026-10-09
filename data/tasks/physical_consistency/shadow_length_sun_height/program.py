# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# code: shadow_ratio_code
def shadow_ratio(pole_read, shadow_read, frame):
    """Shadow length over pole height in pixels, from the first pole and shadow boxes."""
    W, H = frame.size
    def box(n):
        g = (n or {}).get('geometry') or []
        return [float(v) for v in g[0]] if g else None
    pole_box, shadow_box = box(pole_read), box(shadow_read)
    if not pole_box or not shadow_box:
        return {'ratio': None, 'no_read': True}
    pole_px = abs(pole_box[2] - pole_box[0]) * H / 1000.0
    shadow_px = abs(shadow_box[3] - shadow_box[1]) * W / 1000.0
    if pole_px < 1.0 or shadow_px < 1.0:
        return {'ratio': None, 'no_read': True}
    return {'ratio': round(shadow_px / pole_px, 4), 'no_read': False,
            'pole_px': round(pole_px, 1), 'shadow_px': round(shadow_px, 1)}

# end of shadow_ratio_code

# code: c_code
def shadow_count_matches(count, target):
    """Score 1 if the shadow count read equals the reference count, also 1 if unreadable."""
    try: value=float(count); t=float(target)
    except (TypeError, ValueError): return 1.0
    return 1.0 if abs(value-t)<0.5 else 0.0

# end of c_code
