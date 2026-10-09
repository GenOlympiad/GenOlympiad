# shared code: code_8b32ea8cd69d
def mirror_chain(plate_boxes, side_answers, gt):
    """Order the plates near to far, read each as normal or mirrored, and check that they alternate."""
    REST_RIGHT_WHEN_NORMAL = {'R': True, 'F': True, 'P': True, 'B': True, 'D': True, 'E': True,
                              'K': True, 'L': True, 'N': True, 'H': True}
    right_is_normal = REST_RIGHT_WHEN_NORMAL.get(str(gt.get('letter', 'R')).strip().upper(), True)
    boxes = (plate_boxes or {}).get('geometry') or []
    ans = (side_answers or {}).get('answers') or []
    def classify(a):
        s = str(a or '').strip().lower()
        side = None
        if s.startswith('left') or ' left' in s:
            side = 'left'
        elif s.startswith('right') or ' right' in s:
            side = 'right'
        if side is None:
            return None
        normal = (side == 'right') if right_is_normal else (side == 'left')
        return 'normal' if normal else 'mirrored'
    tiers = []
    for i, b in enumerate(boxes):
        base = float(max(b[0], b[2]))
        h = abs(float(b[2]) - float(b[0]))
        tiers.append((base, h, classify(ans[i] if i < len(ans) else None)))
    tiers.sort(key=lambda z: (-z[0], -z[1]))
    tiers = tiers[:6]
    seq = []
    for base, h, c in tiers:
        if c is None:
            break
        seq.append(c)
    n_read = len(seq)
    alt = n_read >= 2 and all(seq[i] != seq[i - 1] for i in range(1, n_read))
    depth = n_read >= 2 and seq[0] != seq[1] and (n_read < 3 or seq[1] != seq[2])
    odd = [i for i in range(1, n_read, 2)]
    flip = (sum(1 for i in odd if seq[i] == 'mirrored') / float(len(odd))) if odd else 0.0
    return {'K': n_read, 'n_plates': len(boxes), 'chir_seq': seq,
            'f_alt': 1.0 if alt else 0.0, 'f_depth': 1.0 if depth else 0.0,
            'flip_frac': round(float(flip), 4),
            'verdict': 'chain near->far reads %s -> alternation %s, depth (>=2 real flips) %s, '
                       'flip_frac %.2f'
                       % (seq or 'nothing readable', 'OK' if alt else 'BROKEN',
                          'OK' if depth else 'BROKEN', flip)}

# end of code_8b32ea8cd69d

# code: centre_line_for_chain_code

def centre_line_for_chain(plate_boxes, side_answers):
    """The plate boxes in the line down the middle of the corridor, leaving out copies in the side mirrors."""
    boxes = (plate_boxes or {}).get('geometry') or []; ans = (side_answers or {}).get('answers') or []
    pairs = [(boxes[i], ans[i] if i < len(ans) else None) for i in range(len(boxes))]
    if not pairs: return {'b': {'geometry': []}, 'a': {'answers': []}, 'kept': 0, 'dropped': 0, 'verdict': 'no plate boxes to select from'}
    cx = lambda b: (float(b[1]) + float(b[3])) / 2.0; area = lambda b: abs(float(b[2]) - float(b[0])) * abs(float(b[3]) - float(b[1]))
    near = max(pairs, key=lambda p: area(p[0]))[0]
    lo, hi = min(float(near[1]), float(near[3])), max(float(near[1]), float(near[3]))
    keep = [p for p in pairs if lo <= cx(p[0]) <= hi]
    if len(keep) < 2: keep = pairs
    return {'b': {'geometry': [p[0] for p in keep]}, 'a': {'answers': [p[1] for p in keep]}, 'kept': len(keep), 'dropped': len(pairs) - len(keep),
            'verdict': '%d of %d plate boxes stand in the receding line down the middle of the corridor; %d copies seen in the side mirrors were left out of the chain' % (len(keep), len(pairs), len(pairs) - len(keep))}

# end of centre_line_for_chain_code

# code: centre_line_for_flip_code

def centre_line_for_flip(plate_boxes, side_answers):
    """The plate boxes in the line down the middle of the corridor, leaving out copies in the side mirrors."""
    boxes = (plate_boxes or {}).get('geometry') or []; ans = (side_answers or {}).get('answers') or []
    pairs = [(boxes[i], ans[i] if i < len(ans) else None) for i in range(len(boxes))]
    if not pairs: return {'b': {'geometry': []}, 'a': {'answers': []}, 'kept': 0, 'dropped': 0, 'verdict': 'no plate boxes to select from'}
    cx = lambda b: (float(b[1]) + float(b[3])) / 2.0; area = lambda b: abs(float(b[2]) - float(b[0])) * abs(float(b[3]) - float(b[1]))
    near = max(pairs, key=lambda p: area(p[0]))[0]
    lo, hi = min(float(near[1]), float(near[3])), max(float(near[1]), float(near[3]))
    keep = [p for p in pairs if lo <= cx(p[0]) <= hi]
    if len(keep) < 2: keep = pairs
    return {'b': {'geometry': [p[0] for p in keep]}, 'a': {'answers': [p[1] for p in keep]}, 'kept': len(keep), 'dropped': len(pairs) - len(keep),
            'verdict': '%d of %d plate boxes stand in the receding line down the middle of the corridor; %d copies seen in the side mirrors were left out of the chain' % (len(keep), len(pairs), len(pairs) - len(keep))}

# end of centre_line_for_flip_code
