# code: window_code
def lamp_strip_window(strip_box):
    """Pad the boxed lamp strip into a crop window, or use the whole frame if it is tiny."""
    g = (strip_box or {}).get('geometry') or []
    if not g:
        return {'bbox': [0.0, 0.0, 1.0, 1.0], 'whole_frame': True}
    ymin, xmin, ymax, xmax = [float(v) for v in g[0][:4]]
    h, w = abs(ymax - ymin), abs(xmax - xmin)
    if h < 10.0 or w < 10.0:
        return {'bbox': [0.0, 0.0, 1.0, 1.0], 'whole_frame': True}
    py, px = 0.30 * h, 0.05 * w
    return {'bbox': [round(max(0.0, min(xmin, xmax) - px) / 1000.0, 4),
                     round(max(0.0, min(ymin, ymax) - py) / 1000.0, 4),
                     round(min(1000.0, max(xmin, xmax) + px) / 1000.0, 4),
                     round(min(1000.0, max(ymin, ymax) + py) / 1000.0, 4)],
            'whole_frame': False}

# end of window_code

# code: led_bits_code
def score_lamp_bits(lamps, lamp_states, reference):
    """Read the lamps left to right as lit or dark bits and lose credit per wrong bit."""
    want = [int(x) for x in reference['bits']]
    n = len(want)
    boxes = (lamps or {}).get('geometry') or []
    answers = (lamp_states or {}).get('answers') or []
    if not boxes or len(answers) != len(boxes):
        return {'frac': 0.0, 'read': None, 'why': 'no confirmed lamp boxes'}
    pairs = []
    for b, a in zip(boxes, answers):
        xc = (float(b[1]) + float(b[3])) / 2.0
        s = str(a or '').strip().lower()
        if ('unlit' in s or 'dark' in s or 'not lit' in s or 'off' in s
                or 'black' in s):
            bit = 0
        elif 'lit' in s or 'glow' in s or 'bright' in s or s.startswith('on'):
            bit = 1
        else:
            bit = None
        pairs.append((xc, bit))
    pairs.sort(key=lambda p: p[0])
    got = [p[1] for p in pairs]
    if any(g is None for g in got):
        return {'frac': 0.0, 'read': got, 'why': 'a lamp did not read lit/dark'}
    h = sum(1 for a, b in zip(got, want) if a != b) + abs(len(got) - n)
    return {'frac': round(max(0.0, 1.0 - 2.0 * h / n), 4), 'read': got,
            'want': want, 'hamming': h,
            'verdict': 'lamp row %s vs required %s -> %d wrong bit(s)'
                       % (''.join(str(x) for x in got),
                          ''.join(str(x) for x in want), h)}

# end of led_bits_code
