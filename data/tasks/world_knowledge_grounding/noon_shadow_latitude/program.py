# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts, frac_of
# end of helpers

# shared code: code_eb63f4c45254
def shadow_to_pole_ratio(pole, shad, src, sdir):
    """The shadow's width in pixels over the pole's height, or zero when no shadow is read."""
    W, H = src.size
    pole_geometry = (pole or {}).get('geometry') or []
    if not pole_geometry:
        return {'ratio': None, 'degenerate': True, 'refusal': 'pole_unreadable'}
    py0, px0, py1, px1 = [float(v) for v in pole_geometry[0]]
    pole_height = abs(py1 - py0) * H / 1000.0
    if pole_height < 20.0:
        return {'ratio': None, 'degenerate': True, 'refusal': 'pole_degenerate'}
    shadow_geometry = (shad or {}).get('geometry') or []
    if not shadow_geometry:
        s = str(sdir or '').strip().lower()
        got = ('left' if 'left' in s else ('right' if 'right' in s else
               ('none' if ('none' in s or 'stub' in s or 'under' in s) else None)))
        if got == 'none':
            return {'ratio': 0.0, 'degenerate': False, 'pole_px': round(pole_height, 1),
                    'shadow_px': 0.0, 'shadow_refused': True,
                    'refusal': 'no_shadow_away_from_foot_confirmed_by_read'}
        return {'ratio': None, 'degenerate': True, 'shadow_refused': True,
                'refusal': 'shadow_seen_%s_but_box_refused' % (got or 'unparsed')}
    sy0, sx0, sy1, sx1 = [float(v) for v in shadow_geometry[0]]
    shadow_length = abs(sx1 - sx0) * W / 1000.0
    return {'ratio': round(shadow_length / pole_height, 4), 'degenerate': False, 'pole_px': round(pole_height, 1),
            'shadow_px': round(shadow_length, 1), 'shadow_refused': False}

# end of code_eb63f4c45254

# code: side_ok_code
def shadow_side_matches(sdir, reference):
    """1 if the read shadow side matches the reference side, else 0."""
    s = str(sdir).strip().lower()
    got = 'left' if 'left' in s else ('right' if 'right' in s else
          ('none' if ('none' in s or 'stub' in s or 'under' in s) else None))
    if got is None: return {'frac': 0.0, 'no_read': True}
    return {'frac': 1.0 if got == str(reference['shadow_side']).lower() else 0.0}

# end of side_ok_code

# code: joint_code
def side_and_length_check(side_text, jlen, reference):
    """1 if the shadow side matches the reference and the length ratio is at least 0.5."""
    s = str(side_text).strip().lower()
    got = 'left' if 'left' in s else ('right' if 'right' in s else
          ('none' if ('none' in s or 'stub' in s or 'under' in s) else None))
    dir_ok = (got is not None and got == str(reference['shadow_side']).lower())
    len_ok = (float(jlen) >= 0.5)
    return 1.0 if (dir_ok and len_ok) else 0.0

# end of joint_code

# code: c_code
def shadow_count_matches(scount, target):
    """1 if the counted shadows equal the reference count, or if either is not a number."""
    try: v=float(scount); t=float(target)
    except (TypeError, ValueError): return 1.0
    return 1.0 if abs(v-t)<0.5 else 0.0

# end of c_code
