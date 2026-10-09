# code: window_code
def annotation_window(bracket_read):
    """Pad the found bracket box and extend it downward, in 0 to 1 image units."""
    geometry = (bracket_read or {}).get('geometry') or []
    if not geometry:
        return {'bbox': [0.0, 0.0, 1.0, 1.0], 'degenerate': True}
    ymin, xmin, ymax, xmax = [float(v) for v in geometry[0]]
    h, w = ymax - ymin, xmax - xmin
    if h < 5.0 or w < 5.0:
        return {'bbox': [0.0, 0.0, 1.0, 1.0], 'degenerate': True}
    pad_x, pad_y = 0.08 * w, 0.08 * h
    x0 = max(0.0, xmin - pad_x) / 1000.0
    y0 = max(0.0, ymin - pad_y) / 1000.0
    x1 = min(1000.0, xmax + pad_x) / 1000.0
    y1 = min(1000.0, ymax + pad_y + 1.5 * h) / 1000.0
    return {'bbox': [round(x0, 4), round(y0, 4), round(x1, 4), round(y1, 4)],
            'degenerate': False}

# end of window_code

# code: chk_code
import re
def _first_answer(r):
    if isinstance(r, dict):
        a = r.get('answers') or [None]
        return a[0]
    return r
def check_depth(ans, want):
    """1.0 if the depth number read, in digits or words, equals the marked depth."""
    a = _first_answer(ans)
    if a is None:
        return {'frac': 0.0, 'read': None, 'want': int(want)}
    t = str(a).strip().lower().replace(',', '')
    words = {'zero': 0, 'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
             'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10}
    matches = re.findall(r'-?\d+', t)
    got = int(matches[-1]) if matches else None
    if got is None:
        for wname, wval in words.items():
            if wname in t:
                got = int(wval)
                break
    if got is None:
        return {'frac': 0.0, 'read': str(a)[:40], 'want': int(want)}
    return {'frac': 1.0 if got == int(want) else 0.0, 'read': got, 'want': int(want)}

# end of chk_code
