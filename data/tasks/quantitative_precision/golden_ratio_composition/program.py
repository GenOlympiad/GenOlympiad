# shared code: code_5634f03fd86e


def horizon_and_object(sky, subject):
    """The horizon's height up the frame and the object's centre across it, as fractions."""
    sky_geometry = (sky or {}).get('geometry') or []
    object_geometry = (subject or {}).get('geometry') or []
    if not sky_geometry or not object_geometry:
        return {'horizon_frac_up': None, 'object_frac_left': None, 'unreadable': True}
    sky_box = [float(v) for v in list(sky_geometry[0])[:4]]
    object_box = [float(v) for v in list(object_geometry[0])[:4]]
    return {'horizon_frac_up': round(1.0 - sky_box[2] / 1000.0, 4),
            'object_frac_left': round((object_box[1] + object_box[3]) / 2000.0, 4), 'unreadable': False}

# end of code_5634f03fd86e

# shared code: goldcode

def golden_joint(placement, target, tol):
    """Product of how close the horizon and the object sit to the golden-ratio line."""
    if not isinstance(placement, dict) or placement.get('unreadable') or placement.get('horizon_frac_up') is None or placement.get('object_frac_left') is None:
        return {'joint': 0.0, 'hz': None, 'col': None, 'no_read': True}
    centre = float(target); core_tol = float(tol); margin = 1.5 * core_tol
    def band(v):
        d = abs(float(v) - centre)
        return max(0.0, 1.0 - max(0.0, d - core_tol) / margin)
    horizon_score = band(placement['horizon_frac_up']); column_score = band(placement['object_frac_left'])
    return {'joint': round(horizon_score * column_score, 4), 'hz': round(horizon_score, 4), 'col': round(column_score, 4),
            'hz_frac': placement['horizon_frac_up'], 'col_frac': placement['object_frac_left'], 'no_read': False}

# end of goldcode
