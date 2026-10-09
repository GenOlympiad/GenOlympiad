# code: n_yes_code
def count_confirmed_tips(confirms, boxes):
    """Count branch tips confirmed yes, dropping boxes that mostly overlap one already kept."""
    answers = (confirms or {}).get('answers') or []
    geometry = (boxes or {}).get('geometry') if isinstance(boxes, dict) else (boxes or [])
    geometry = geometry or []

    def area(b):
        return max(0.0, b[2] - b[0]) * max(0.0, b[3] - b[1])

    def iou_small(a, b):
        y0 = max(a[0], b[0]); x0 = max(a[1], b[1])
        y1 = min(a[2], b[2]); x1 = min(a[3], b[3])
        inter = max(0.0, y1 - y0) * max(0.0, x1 - x0)
        m = min(area(a), area(b))
        return 0.0 if m <= 0 else inter / m

    kept, n_duplicates, n = [], 0, 0
    for i, a in enumerate(answers):
        yes = str(a).strip().lower().startswith('y')
        b = geometry[i] if i < len(geometry) else None
        if b is not None and len(b) >= 4:
            b = [float(b[0]), float(b[1]), float(b[2]), float(b[3])]
            if any(iou_small(b, k) > 0.5 for k in kept):
                n_duplicates += 1
                continue
            kept.append(b)
        if yes:
            n += 1
    return {'n': n, 'asked': len(answers), 'duplicates_dropped': n_duplicates}

# end of n_yes_code
