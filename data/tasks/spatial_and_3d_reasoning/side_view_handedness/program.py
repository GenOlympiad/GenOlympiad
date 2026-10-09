# shared code: code_4f1ccf443f93

def image_size(p):
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
    return 1000.0, 1000.0


def arrange_views(panel_boxes, image):
    """Find the front, stacked and side views among the three panel boxes and compare the depth they share."""
    W, H = image_size(image)
    geometry = ((panel_boxes or {}).get('geometry')) or []
    if len(geometry) != 3:
        return {'no_read': True, 'reason': 'n_panels_%d_want_3' % len(geometry), 'n_panels': len(geometry)}
    views = []
    for b in geometry:
        v = [float(x) for x in b]
        y0, y1 = min(v[0], v[2]) * H / 1000.0, max(v[0], v[2]) * H / 1000.0
        x0, x1 = min(v[1], v[3]) * W / 1000.0, max(v[1], v[3]) * W / 1000.0
        views.append({'x0': x0, 'x1': x1, 'y0': y0, 'y1': y1, 'w': x1 - x0, 'h': y1 - y0,
                  'cx': 0.5 * (x0 + x1), 'cy': 0.5 * (y0 + y1),
                  'mille': [int(round(q)) for q in v]})

    def near_x(a, b):
        return abs(a['cx'] - b['cx']) < 0.42 * max(a['w'], b['w'])

    def near_y(a, b):
        return abs(a['cy'] - b['cy']) < 0.42 * max(a['h'], b['h'])

    front = stack = side = None
    for i, a in enumerate(views):
        s_ = [b for j, b in enumerate(views) if j != i and near_x(a, b) and not near_y(a, b)]
        h_ = [b for j, b in enumerate(views) if j != i and near_y(a, b) and not near_x(a, b)]
        if s_ and h_:
            front, stack, side = a, s_[0], h_[0]
            break
    if front is None:
        return {'no_read': True, 'reason': 'no_cross_layout', 'n_panels': 3}
    depth_top = float(stack['h'])
    depth_side = float(side['w'])
    mean_depth = 0.5 * (depth_top + depth_side)
    if mean_depth <= 0 or min(depth_top, depth_side, front['w'], front['h']) <= 0:
        return {'no_read': True, 'reason': 'degenerate_panel', 'n_panels': 3}
    depth_mismatch = abs(depth_top - depth_side) / mean_depth
    width_mismatch = abs(front['w'] - stack['w']) / (0.5 * (front['w'] + stack['w']))
    height_mismatch = abs(front['h'] - side['h']) / (0.5 * (front['h'] + side['h']))
    above = bool(stack['cy'] < front['cy'])
    right = bool(side['cx'] > front['cx'])
    return {'no_read': False, 'n_panels': 3,
            'stack_is_above': above, 'side_is_right': right,
            'depth_top': round(depth_top, 1), 'depth_side': round(depth_side, 1),
            'depth_mismatch': round(depth_mismatch, 4),
            'width_mismatch': round(width_mismatch, 4), 'height_mismatch': round(height_mismatch, 4),
            'side_box': [side['mille']], 'front_box': [front['mille']],
            'stack_box': [stack['mille']],
            'verdict': ('one depth, measured twice: stacked view %.0f px tall vs side view '
                        '%.0f px wide -> %.1f%% apart; stacked partner %s the front view, '
                        'side partner to its %s; shared width off %.1f%%, shared height off '
                        '%.1f%%'
                        % (depth_top, depth_side, 100.0 * depth_mismatch, 'above' if above else 'below',
                           'right' if right else 'left', 100.0 * width_mismatch, 100.0 * height_mismatch))}

# end of code_4f1ccf443f93

# code: f_code
def views_on_wanted_sides(above, right, want_above, want_right):
    """1.0 if the stacked view is above or below and the side view left or right as wanted."""
    return 1.0 if (bool(above) == bool(want_above)
                   and bool(right) == bool(want_right)) else 0.0

# end of f_code

# code: f_code_2
def side_view_shows_l_shape(l_answer):
    """Whether the side panel shows an L shape (upright and foot)."""
    answer = str(((l_answer or {}).get('answers') or [None])[0] or '').strip().lower()
    ok = answer.startswith('y')
    return {'frac': 1.0 if ok else 0.0, 'answer': answer,
            'verdict': 'the side panel %s an L shape (upright + foot) -> frac %s'
                       % ('shows' if ok else 'does NOT show', '1.0' if ok else '0.0')}

# end of f_code_2

# code: f_code_3
def foot_points_wanted_way(foot_answer, want):
    """Whether the foot in the side view points to the side the named view demands."""
    answer = str(((foot_answer or {}).get('answers') or [None])[0] or '').strip().lower()
    got = -1 if 'left' in answer else (1 if 'right' in answer else 0)
    want_dir = int(want)
    ok = (got != 0 and got == want_dir)
    return {'frac': 1.0 if ok else 0.0, 'foot_dir': got, 'want_dir': want_dir,
            'verdict': 'the foot in the side view sticks out to the %s; the view from the named side demands %s -> frac %s'
                       % ({-1: 'LEFT', 1: 'RIGHT', 0: 'neither side (unread)'}[got],
                          {-1: 'LEFT', 1: 'RIGHT'}[want_dir], '1.0' if ok else '0.0')}

# end of f_code_3

# code: show_code
def show_views_verdict(vp):
    """Pass the view measurement on with a full score, for display."""
    return {'frac': 1.0, 'verdict': vp.get('verdict')}

# end of show_code
