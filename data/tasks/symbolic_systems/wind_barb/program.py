# code: helpers
from genolympiad.task_helpers import count_listed_items
# end of helpers

# code: window_code
def barb_window(hd):
    """A crop window around the located barb, padded by a quarter of its size on each side."""
    geometry = (hd or {}).get('geometry') or []
    if not geometry:
        return {'bbox': [0.0, 0.0, 1.0, 1.0], 'degenerate': True}
    ymin, xmin, ymax, xmax = [float(v) for v in geometry[0]]
    h, w = ymax - ymin, xmax - xmin
    if h < 20.0 or w < 20.0:
        return {'bbox': [0.0, 0.0, 1.0, 1.0], 'degenerate': True}
    pad_y, pad_x = 0.25 * h, 0.25 * w
    return {'bbox': [round(max(0.0, xmin - pad_x) / 1000.0, 4),
                     round(max(0.0, ymin - pad_y) / 1000.0, 4),
                     round(min(1000.0, xmax + pad_x) / 1000.0, 4),
                     round(min(1000.0, ymax + pad_y) / 1000.0, 4)],
            'degenerate': False}

# end of window_code

# code: seq_match_code
import re
def _first_answer(r):
    if isinstance(r, dict):
        a = r.get('answers') or [None]
        return a[0]
    return r
def _int(a):
    if a is None:
        return None
    ms = re.findall(r'-?\d+', str(a))
    if ms:
        return int(ms[-1])
    w = {'zero': 0, 'none': 0, 'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
         'six': 6, 'seven': 7, 'eight': 8, 'nine': 9}
    t = str(a).strip().lower()
    for k, v in w.items():
        if k in t:
            return v
    return None
def seq_match(a_pen, a_line, a_half, target):
    """Share of pennant, full and half barb counts matching the reference, capped at 0.25 if any miss."""
    pennants, n_line, halves = _int(_first_answer(a_pen)), _int(_first_answer(a_line)), _int(_first_answer(a_half))
    wanted = [int(x) for x in target]
    if pennants is None or n_line is None or halves is None:
        return {'frac': 0.0, 'read': [pennants, n_line, halves], 'want': wanted,
                'why': 'a mark-type count did not read'}
    fulls = n_line - halves
    if fulls < 0:
        fulls = 0
    read = [pennants, fulls, halves]
    n_ok = sum(1 for i in range(len(wanted)) if read[i] == wanted[i])
    frac = round(n_ok / float(len(wanted)), 4)
    if n_ok < len(wanted):
        frac = min(frac, 0.25)
    return {'frac': frac, 'read': read, 'want': wanted, 'lines': n_line}

# end of seq_match_code
