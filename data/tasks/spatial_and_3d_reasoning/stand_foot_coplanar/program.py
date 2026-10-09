# code: coplanar_code


def foot_level_spread(foot_read):
    """How far apart the bottom edges of the foot boxes sit, as a share of the frame height."""
    foot_boxes = (foot_read or {}).get('geometry') or []
    if len(foot_boxes) < 3:
        return {'dev_frac': None, 'n_feet': len(foot_boxes), 'ys': [], 'unreadable': True}
    bottom_ys = [float(b[2]) for b in foot_boxes]
    return {'dev_frac': round((max(bottom_ys) - min(bottom_ys)) / 1000.0, 4), 'n_feet': len(bottom_ys),
            'ys': [round(v, 1) for v in bottom_ys], 'unreadable': False}

# end of coplanar_code
