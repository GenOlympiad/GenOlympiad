# code: helpers
from genolympiad.task_helpers import compare_printed_figure
# end of helpers

# code: window_code
def fish_tail_window(far, scl):
    """Build a crop box around the fish tail tip that also spans the scale."""
    tail_box = ((far or {}).get('geometry') or [None])[0]
    scale_box = ((scl or {}).get('geometry') or [None])[0]
    if not tail_box or not scale_box:
        return {'geometry': None, 'degenerate': True}
    fy0, fx0, fy1, fx1 = [float(v) for v in list(tail_box)[:4]]
    sy0, sx0, sy1, sx1 = [float(v) for v in list(scale_box)[:4]]
    w = max(1.0, abs(fx1 - fx0))
    x0 = min(fx0, fx1) - 0.6 * w
    x1 = max(fx0, fx1) + 0.6 * w
    y0 = min(fy0, fy1, sy0, sy1)
    y1 = max(fy0, fy1, sy0, sy1)
    h = max(1.0, y1 - y0)
    b = [max(0.0, y0 - 0.25 * h), max(0.0, x0),
         min(1000.0, y1 + 0.25 * h), min(1000.0, x1)]
    bad = (b[2] - b[0] < 20.0) or (b[3] - b[1] < 20.0)
    return {'geometry': [b], 'box': b, 'degenerate': bad}

# end of window_code

# code: pick_code
import re
def num(node):
    a = (node or {}).get('answers') or [None]
    m = re.search(r'\d+(?:[.,]\d+)?', str(a[0] or ''))
    return float(m.group(0).replace(',', '.')) if m else None
def pick_length(t1, t2):
    """Take the larger of two length reads, flagged when they differ by over 0.6 cm."""
    v1, v2 = num(t1), num(t2)
    if v1 is None or v2 is None:
        return {'cm': None, 'v1': v1, 'v2': v2, 'spread': None, 'degenerate': True}
    spread = abs(v1 - v2)
    return {'cm': max(v1, v2), 'v1': v1, 'v2': v2, 'spread': spread,
            'degenerate': spread > 0.6}

# end of pick_code
