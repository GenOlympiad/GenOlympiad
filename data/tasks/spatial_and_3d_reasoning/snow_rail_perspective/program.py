# code: median3_code
def recession(bx, gt):
    import math
    g = (bx or {}).get('geometry') or []
    if len(g) < 6:
        return {'frac': None, 'no_read': True}
    cy = [(float(b[0]) + float(b[2])) / 2.0 for b in g]
    cx = [(float(b[1]) + float(b[3])) / 2.0 for b in g]
    hy = [abs(float(b[2]) - float(b[0])) for b in g]
    wx = [abs(float(b[3]) - float(b[1])) for b in g]
    if (max(cy) - min(cy)) >= (max(cx) - min(cx)):
        pos, size = cy, wx
    else:
        pos, size = cx, hy
    order = sorted(range(len(pos)), key=lambda i: pos[i])
    k = max(1, len(order) // 3)
    if sum(size[i] for i in order[:k]) > sum(size[i] for i in order[-k:]):
        order = order[::-1]
    cs = [pos[i] for i in order]
    sz = [size[i] for i in order]
    if pos is cy:
        clipped = [(float(b[1]) <= 5.0 or float(b[3]) >= 995.0) for b in g]
    else:
        clipped = [(float(b[0]) <= 5.0 or float(b[2]) >= 995.0) for b in g]
    cl = [clipped[i] for i in order]
    gaps = [abs(cs[i + 1] - cs[i]) for i in range(len(cs) - 1)]
    gaps = [q for q in gaps if q > 1e-6]
    if len(gaps) < 5:
        return {'frac': None, 'no_read': True}
    szq = [sz[i] for i in range(len(sz)) if not cl[i]]
    if len(szq) < 5:
        return {'frac': None, 'no_read': True, 'bad_boxes': True}
    grow = sum(1 for i in range(len(szq) - 1) if szq[i + 1] > szq[i])
    if (grow / float(len(szq) - 1)) < 0.8:
        return {'frac': None, 'no_read': True, 'bad_boxes': True}
    inc = sum(1 for i in range(len(gaps) - 1) if gaps[i + 1] > gaps[i] * 1.02)
    mono = inc / (len(gaps) - 1)
    ratio = gaps[-1] / gaps[0] if gaps[0] > 0 else 0.0
    s_mono = max(0.0, min(1.0, (mono - 0.5) / 0.35))
    s_ratio = max(0.0, min(1.0, (math.log(max(ratio, 1e-6)) - math.log(1.6))
                           / (math.log(4.0) - math.log(1.6))))
    frac = round(s_mono * s_ratio, 4)
    return {'frac': frac, 'no_read': False, 'mono': round(mono, 3),
            'near_over_far_gap': round(ratio, 2), 'n_marks': len(cs)}


def median_recession(bx1, bx2, bx3, reference):
    """The median spacing score over three box reads, withheld if their gap ratios disagree."""
    usable_reads, dropped = [], []
    for b in (bx1, bx2, bx3):
        if not b or b.get('unreadable'):
            dropped.append('refused')
            continue
        r = recession(b, reference)
        if r.get('no_read'):
            dropped.append('bad_boxes' if r.get('bad_boxes') else 'too_few_marks')
            continue
        usable_reads.append(r)
    if len(usable_reads) < 3:
        return {'frac': None, 'no_read': True, 'why': 'fewer than three usable rings',
                'dropped': dropped}
    fracs = sorted(r['frac'] for r in usable_reads)
    ratios = sorted(r['near_over_far_gap'] for r in usable_reads)
    monos = sorted(r['mono'] for r in usable_reads)
    span = (ratios[-1] / ratios[0]) if ratios[0] > 0 else 1e9
    if span > 2.0:
        return {'frac': None, 'no_read': True, 'why': 'the three rings disagree on the far/near '
                'gap ratio by more than 2x -- they did not measure the same set of marks',
                'ratios': ratios, 'span': round(span, 2), 'fracs': fracs}
    return {'frac': fracs[1], 'no_read': False, 'fracs': fracs, 'ratios': ratios, 'monos': monos,
            'span': round(span, 2)}

# end of median3_code
