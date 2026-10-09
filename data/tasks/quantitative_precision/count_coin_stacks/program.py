# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# code: n_yes_code
def count_confirmed_stacks(node, boxes):
    """Count the boxes confirmed as coin stacks, folding near duplicate boxes."""
    answers = (node or {}).get('answers') or []
    geometry = (boxes or {}).get('geometry') or []
    def iou(a, b):
        ay0, ax0, ay1, ax1 = a[0], a[1], a[2], a[3]
        by0, bx0, by1, bx1 = b[0], b[1], b[2], b[3]
        iy0, ix0 = max(ay0, by0), max(ax0, bx0)
        iy1, ix1 = min(ay1, by1), min(ax1, bx1)
        ih, iw = max(0.0, iy1 - iy0), max(0.0, ix1 - ix0)
        inter = ih * iw
        ua = max(0.0, ay1 - ay0) * max(0.0, ax1 - ax0)
        ub = max(0.0, by1 - by0) * max(0.0, bx1 - bx0)
        den = ua + ub - inter
        return (inter / den) if den > 0 else 0.0
    kept, duplicates = [], 0
    for i, a in enumerate(answers):
        if not str(a).strip().lower().startswith('y'):
            continue
        b = geometry[i] if i < len(geometry) else None
        if b is not None and any(iou(b, k) >= 0.70 for k in kept):
            duplicates += 1
            continue
        if b is not None:
            kept.append(b)
        else:
            kept.append([0, 0, 0, 0])
    return {'n': len(kept), 'asked': len(answers), 'duplicates_folded': duplicates}

# end of n_yes_code
