# code: spacing_code
def line_spacing_deviation(lines, verdicts, reference):
    """How far the worst gap between confirmed painted lines strays from the mean, as a fraction."""
    line_boxes = lines.get('geometry') or []
    answers = (verdicts or {}).get('answers') or []
    kept_boxes = [b for i, b in enumerate(line_boxes)
         if i >= len(answers) or str(answers[i]).strip().lower().startswith('y')]
    n = len(kept_boxes)
    if n != int(reference['n']) or n < 3:
        return {'gap_dev': None, 'n': n, 'n_mismatch': True}
    mean_height = sum(abs(float(b[2]) - float(b[0])) for b in kept_boxes) / n
    mean_width = sum(abs(float(b[3]) - float(b[1])) for b in kept_boxes) / n
    if mean_height >= mean_width:
        centres = sorted((float(b[1]) + float(b[3])) / 2.0 for b in kept_boxes)
    else:
        centres = sorted((float(b[0]) + float(b[2])) / 2.0 for b in kept_boxes)
    gaps = [centres[i + 1] - centres[i] for i in range(n - 1)]
    mean_gap = sum(gaps) / len(gaps)
    if mean_gap <= 0:
        return {'gap_dev': None, 'n': n, 'n_mismatch': True}
    deviation = max(abs(g - mean_gap) for g in gaps) / mean_gap
    return {'gap_dev': round(deviation, 4), 'n': n, 'axis': 'x' if mean_height >= mean_width else 'y',
            'gaps': [round(g, 1) for g in gaps], 'n_mismatch': False}

# end of spacing_code
