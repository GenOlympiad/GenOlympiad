# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# shared code: code_7bb2f09d18f9
def count_touching(candidates, pair_answers):
    """Count the candidate pairs confirmed as touching, nearest first, each item in at most one pair."""
    idx = (candidates or {}).get('idx') or []
    answers = (pair_answers or {}).get('answers') or []
    dists = (candidates or {}).get('dists') or []
    hole = any((k >= len(answers)) or (answers[k] is None) or (not str(answers[k]).strip())
               for k in range(len(idx)))
    order = sorted(range(len(idx)), key=lambda k: dists[k] if k < len(dists) else 9.9)
    used, pairs = set(), 0
    for k in order:
        if k >= len(answers) or not str(answers[k] or '').strip().lower().startswith('y'):
            continue
        i, j = idx[k]
        if i in used or j in used:
            continue
        used.add(i); used.add(j); pairs += 1
    n_items = (candidates or {}).get('n_items') or 0
    return {'pairs': pairs, 'items': n_items, 'clumps': n_items - pairs,
            'asked': len(idx), 'read_hole': bool(hole)}

# end of code_7bb2f09d18f9

# shared code: code_e19b0b6686e1
def candidate_pairs(boxes_node, crop_node, reach=1.6):
    """Pair each confirmed item with its mutual nearest neighbour when they are close enough to touch."""
    geometry = (boxes_node or {}).get('geometry') or []
    answers = (crop_node or {}).get('answers') or []
    items = []
    for i, box in enumerate(geometry):
        if i < len(answers) and str(answers[i]).strip().lower().startswith('y'):
            y0, x0, y1, x1 = box[0], box[1], box[2], box[3]
            items.append({'cy': (y0 + y1) / 2.0, 'cx': (x0 + x1) / 2.0,
                       'sz': (abs(x1 - x0) * abs(y1 - y0)) ** 0.5,
                       'box': [min(y0, y1), min(x0, x1), max(y0, y1), max(x0, x1)]})
    n = len(items)
    if n == 0:
        return {'n_items': 0, 'boxes': [], 'idx': [], 'dists': []}
    sizes = sorted(o['sz'] for o in items)
    median_size = sizes[len(sizes) // 2] or 1.0
    def distance(a, b):
        return ((a['cy'] - b['cy']) ** 2 + (a['cx'] - b['cx']) ** 2) ** 0.5
    near = []
    for i in range(n):
        best, best_dist = None, None
        for j in range(n):
            if i == j:
                continue
            dist = distance(items[i], items[j])
            if best_dist is None or dist < best_dist:
                best, best_dist = j, dist
        near.append((best, best_dist))
    out_boxes, idx, dists = [], [], []
    for i in range(n):
        j, dist = near[i]
        if j is None or j <= i:
            continue
        if near[j][0] != i:
            continue
        if dist > reach * median_size:
            continue
        a, b = items[i]['box'], items[j]['box']
        out_boxes.append([min(a[0], b[0]), min(a[1], b[1]), max(a[2], b[2]), max(a[3], b[3])])
        idx.append([i, j])
        dists.append(round(dist / median_size, 3))
    return {'n_items': n, 'boxes': out_boxes, 'idx': idx, 'dists': dists}

# end of code_e19b0b6686e1

# code: hold_clump_count_tal_code
def hold_clump_count(tally):
    """Withhold the clump count when a pair read did not come back."""
    read_hole = bool((tally or {}).get('read_hole'))
    return {'read_hole': read_hole, 'refused': read_hole}

# end of hold_clump_count_tal_code

# code: hold_touching_pair_count_tal_code
def hold_touching_pair_count(tally):
    """Withhold the touching-pair count when a pair read did not come back."""
    read_hole = bool((tally or {}).get('read_hole'))
    return {'read_hole': read_hole, 'refused': read_hole}

# end of hold_touching_pair_count_tal_code
