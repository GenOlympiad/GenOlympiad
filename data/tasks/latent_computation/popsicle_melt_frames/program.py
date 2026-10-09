# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# shared code: code_42ce12033d49
def popsicle_heights(oh, n):
    """Popsicle heights from left to right, and each as a share of the tallest."""
    boxes = oh.get('geometry') if isinstance(oh, dict) else oh
    if not boxes or len(boxes) != int(n):
        return {'heights': None, 'ratios': None, 'no_read': True}
    rows = []
    for b in boxes:
        ymin, xmin, ymax, xmax = [float(v) for v in b[:4]]
        rows.append((0.5 * (xmin + xmax), abs(ymax - ymin)))
    rows.sort(key=lambda r: r[0])
    height_list = [r[1] for r in rows]
    tallest = max(height_list)
    if tallest <= 5.0:
        return {'heights': None, 'ratios': None, 'no_read': True}
    return {'heights': [round(h, 3) for h in height_list],
            'ratios': [round(h / tallest, 3) for h in height_list], 'no_read': False}

# end of code_42ce12033d49

# code: order_score_code
def order_score(read, names, target_order):
    """Score 1 when the names ordered from shortest to tallest match the target order."""
    try:
        if isinstance(read, (list, tuple)) and read and all(isinstance(x,(int,float)) for x in read):
            pairs = sorted(zip(names, read), key=lambda p: p[1])
            got = [p[0] for p in pairs]
        else:
            import re
            letters = [t.upper() for t in re.findall(r'[A-Za-z]', str(read))]
            got = [t for t in letters if t in names]
        if len(got) != len(target_order):
            return {'frac': 0.0, 'unreadable': True}
        return {'frac': 1.0 if got == list(target_order) else 0.0, 'unreadable': False}
    except Exception:
        return {'frac': 0.0, 'unreadable': True}
# end of order_score_code
