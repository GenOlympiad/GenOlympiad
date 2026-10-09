# code: dial_grid_code
def read_dial_digits(gauge_read, digit_read, reference):
    """The digit each dial pointer reads, sorted left to right."""
    import re
    geometry = gauge_read.get('geometry') or []
    answers = digit_read.get('answers') or []
    rows = []
    for i, box in enumerate(geometry):
        a = str(answers[i] if i < len(answers) else '' or '')
        nums = re.findall(r'\d+(?:\.\d+)?', a)
        digit = None
        if nums:
            v = float(nums[-1])
            if 0 <= v <= 9:
                digit = int(round(v))
        x_centre = (float(box[1]) + float(box[3])) / 2.0
        rows.append((x_centre, digit))
    rows.sort(key=lambda r: r[0])
    digits = [digit for _, digit in rows]
    return {'grid': [[digit] for digit in digits], 'digits': digits,
            'n_boxes': len(geometry), 'n_dials': reference.get('n_dials'),
            'answers': [str(x)[:24] for x in answers]}

# end of dial_grid_code
