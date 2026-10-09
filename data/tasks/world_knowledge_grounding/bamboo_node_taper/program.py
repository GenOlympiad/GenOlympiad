# code: internodes_code

def _cy(b):
    return (float(b[0]) + float(b[2])) / 2.0


def _cx(b):
    return (float(b[1]) + float(b[3])) / 2.0


def _h(b):
    return abs(float(b[2]) - float(b[0]))


def _w(b):
    return abs(float(b[3]) - float(b[1]))


def _yes(a):
    return str(a).strip().lower().startswith('y')


def _kept(bx, cf):
    geo = (bx or {}).get('geometry') or []
    ok = (cf or {}).get('answers') or []
    return [i for i in range(min(len(geo), len(ok))) if _yes(ok[i])]


def internodes(node_boxes, node_confirms, label_boxes, label_confirms, label_values, reference):
    """Fit the ruler scale from read ruler numbers and list the gaps between joint rings."""
    import re
    vertical = str((reference or {}).get('node_axis') or 'vertical').strip().lower() == 'vertical'

    def along(b):
        return _cy(b) if vertical else _cx(b)

    label_geometry = (label_boxes or {}).get('geometry') or []
    label_answers = (label_values or {}).get('answers') or []
    pairs = []
    for i in _kept(label_boxes, label_confirms):
        m = re.search(r'-?\d+(?:\.\d+)?', str(label_answers[i] if i < len(label_answers) else ''))
        if m:
            pairs.append((along(label_geometry[i]), float(m.group())))
    if len(pairs) < 2:
        return {'gaps': '', 'unread': True, 'refused': True,
                'verdict': 'fewer than two ruler numbers were confirmed and read, so no scale '
                           'could be fitted -> honest refusal'}
    n = float(len(pairs))
    sx = sum(p[0] for p in pairs)
    sy = sum(p[1] for p in pairs)
    sxx = sum(p[0] * p[0] for p in pairs)
    sxy = sum(p[0] * p[1] for p in pairs)
    denominator = n * sxx - sx * sx
    if abs(denominator) < 1e-9:
        return {'gaps': '', 'unread': True, 'refused': True,
                'verdict': 'the confirmed ruler numbers all sit at the same place, so no scale '
                           'could be fitted -> honest refusal'}
    slope = (n * sxy - sx * sy) / denominator
    intercept = (sy - slope * sx) / n

    node_geometry = (node_boxes or {}).get('geometry') or []
    node_positions = sorted(slope * along(node_geometry[i]) + intercept for i in _kept(node_boxes, node_confirms))
    if len(node_positions) < 2:
        return {'gaps': '', 'unread': True,
                'verdict': 'fewer than two joint rings were confirmed -> no gap to measure'}
    gaps = [round(node_positions[i + 1] - node_positions[i], 2) for i in range(len(node_positions) - 1)]
    return {'gaps': ', '.join(('%g' % g) for g in gaps), 'list': gaps,
            'n_nodes': len(node_positions), 'n_marks': len(pairs), 'unread': False,
            'verdict': '%d joint rings and %d ruler numbers confirmed by the rings; on the fitted '
                       'ruler scale the joints stand at %s, so the internode gaps from base to '
                       'tip are %s'
                       % (len(node_positions), len(pairs), [round(v, 2) for v in node_positions], gaps)}

# end of internodes_code
