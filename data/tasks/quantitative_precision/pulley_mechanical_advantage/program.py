# code: helpers
from genolympiad.task_helpers import count_listed_items
# end of helpers

# code: ma_code
def mechanical_advantage_score(segq, load_arrow, effort_arrow, src, reference):
    """Score the rope count and the effort to load arrow length ratio against 1 over n."""
    import math
    import re
    W, H = src.size
    words = {'zero': 0, 'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5, 'six': 6,
             'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10, 'eleven': 11, 'twelve': 12}
    n_seg = None
    for a in ((segq or {}).get('answers') or []):
        t = str(a or '').strip().lower()
        m = re.search(r'\d+', t)
        if m:
            n_seg = int(m.group(0))
            break
        for w, v in words.items():
            if re.search(r'\b' + w + r'\b', t):
                n_seg = v
                break
        if n_seg is not None:
            break

    def box_length(node):
        g = (node or {}).get('geometry')
        if not g:
            return 0.0
        v = list(g[0]) if isinstance(g[0], (list, tuple)) else list(g)
        if len(v) < 4:
            return 0.0
        y0, x0, y1, x1 = [float(t) for t in v[:4]]
        return math.hypot((x1 - x0) * W / 1000.0, (y1 - y0) * H / 1000.0)

    load_length, effort_length = box_length(load_arrow), box_length(effort_arrow)
    n_exp = int(reference['n_expected'])
    out = {'frac': 0.0, 'n_segments': n_seg, 'effort_len': None, 'load_len': None,
           'ratio': None, 'target': None, 'err': None, 'degenerate': True,
           'refused': True}
    if n_seg is None or n_seg < 2 or load_length < 5.0 or effort_length < 1.0:
        return out
    ratio = effort_length / load_length
    target = 1.0 / float(n_exp)
    tol = float(reference['tol'])
    count_ok = 1.0 if n_seg == n_exp else max(0.0, 1.0 - abs(n_seg - n_exp) / float(n_exp))
    err = abs(ratio - target) / target
    f_force = max(0.0, 1.0 - err / (2.5 * tol))
    return {'frac': round(count_ok * f_force, 4), 'n_segments': n_seg,
            'effort_len': round(effort_length / W, 4), 'load_len': round(load_length / W, 4),
            'ratio': round(ratio, 3), 'target': round(target, 3), 'err': round(err, 3),
            'count_ok': round(count_ok, 3), 'degenerate': False}

# end of ma_code
