# code: divs_code
def division_error(section_boxes, section_confirms, strip, ideal):
    """The worst gap between the read division points along the bar and the ideal equal parts."""
    boxes = [[float(v) for v in b] for b in
             ((section_boxes.get('geometry') if isinstance(section_boxes, dict) else section_boxes) or [])]
    answers = (section_confirms.get('answers') if isinstance(section_confirms, dict) else section_confirms) or []
    keep = [b for b, a in zip(boxes, answers)
            if str(a).strip().lower().startswith('yes')]
    strip_box = [float(v) for v in strip['geometry'][0]]
    L, R = min(strip_box[1], strip_box[3]), max(strip_box[1], strip_box[3])
    T, B = min(strip_box[0], strip_box[2]), max(strip_box[0], strip_box[2])
    if R - L < 50.0:
        return {'err': 1.0, 'degenerate': True, 'refused': True,
                'why': 'strip span degenerate'}
    if (B - T) > 0.30 * (R - L):
        return {'err': 1.0, 'degenerate': True, 'refused': True,
                'why': 'strip box is not a flat bar (h/w %.2f)' % ((B - T) / (R - L))}
    sections = sorted(keep, key=lambda b: (b[1] + b[3]) / 2.0)
    wanted = [float(v) for v in ideal]
    if not sections:
        return {'err': 1.0, 'degenerate': True, 'refused': True,
                'why': 'no section of the bar was confirmed'}
    if len(sections) != len(wanted) + 1:
        return {'err': 1.0, 'n': max(0, len(sections) - 1), 'fracs': [],
                'count_mismatch': True, 'degenerate': False,
                'why': '%d sections of bar were confirmed; %d equal parts were asked for'
                       % (len(sections), len(wanted) + 1)}
    xs = []
    for i in range(len(sections) - 1):
        edge = (max(sections[i][1], sections[i][3]) + min(sections[i + 1][1], sections[i + 1][3])) / 2.0
        xs.append((edge - L) / (R - L))
    xs.sort()
    return {'err': round(max(abs(a - b) for a, b in zip(xs, wanted)), 4),
            'n': len(xs), 'fracs': [round(x, 4) for x in xs],
            'count_mismatch': False, 'degenerate': False}

# end of divs_code
