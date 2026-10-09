# code: n_yes_code
def count_confirmed_rows(node):
    """Count the letter rows confirmed by a yes answer."""
    answers = (node or {}).get('answers') or []
    return {'n_rows': sum(1 for a in answers if str(a).strip().lower().startswith('y')),
            'asked': len(answers)}

# end of n_yes_code

# code: prog_code
def row_size_ratios(row_boxes, confirm_reads, target, n_expected):
    """Height ratios of neighbouring confirmed rows and the worst miss from the target."""
    answers = (confirm_reads or {}).get('answers') or []
    items = []
    for i, b in enumerate((row_boxes or {}).get('geometry') or []):
        box = [float(v) for v in b]
        ok = (i < len(answers)) and str(answers[i]).strip().lower().startswith('y')
        items.append((box, ok))
    items.sort(key=lambda z: z[0][0])
    n_confirmed = sum(1 for z in items if z[1])
    target_ratio = float(target)
    pairs, skipped = [], 0
    for k in range(len(items) - 1):
        (ba, oka), (bb, okb) = items[k], items[k + 1]
        if not (oka and okb):
            skipped += 1
            continue
        ha, hb = abs(ba[2] - ba[0]), abs(bb[2] - bb[0])
        if min(ha, hb) < 4.0:
            skipped += 1
            continue
        pairs.append(max(ha, hb) / min(ha, hb))
    out = {'n_rows': n_confirmed, 'n_proposed': len(items), 'n_expected': int(n_expected or 0),
           'n_pairs': len(pairs), 'pairs_dropped': skipped,
           'ratios': [round(x, 3) for x in pairs]}
    if len(pairs) < 2:
        out.update({'max_ratio_err': None, 'degenerate': True})
        return out
    out.update({'max_ratio_err': round(max(abs(x - target_ratio) for x in pairs), 4),
                'degenerate': False})
    return out

# end of prog_code
