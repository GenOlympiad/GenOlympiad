# code: helpers
from genolympiad.task_helpers import join_box_reads
# end of helpers

# code: pick_band_code
def band_at_arrow(bars, arw):
    """The scale bar that the class arrow points at, counted from the top."""
    bar_boxes = (bars or {}).get('geometry') or []
    arrow_boxes = (arw or {}).get('geometry') or []
    if not bar_boxes or not arrow_boxes:
        return {'geometry': None, 'no_read': True, 'n_bars': len(bar_boxes)}
    sorted_bars = sorted([[float(v) for v in b] for b in bar_boxes], key=lambda b: (b[0] + b[2]) / 2.0)
    arrow_y = (float(arrow_boxes[0][0]) + float(arrow_boxes[0][2])) / 2.0
    idx = None
    for k, b in enumerate(sorted_bars):
        if b[0] <= arrow_y <= b[2]:
            idx = k
            break
    if idx is None:
        idx = min(range(len(sorted_bars)), key=lambda k: abs((sorted_bars[k][0] + sorted_bars[k][2]) / 2.0 - arrow_y))
    return {'geometry': [sorted_bars[idx]], 'no_read': False, 'band_index': idx + 1,
            'n_bars': len(sorted_bars), 'arrow_y': round(arrow_y, 1)}

# end of pick_band_code

# code: label_ok_code
def check_energy_label(arrow_read, bar_letters_read, bottom_colour_read, reference):
    """1 if the bars read A to G ending in red and the arrow shows the stated class, else 0."""
    def first(node):
        a = (node or {}).get('answers') or []
        return str(a[0]) if a and a[0] is not None else ''

    def letter_of(tok):
        t = tok.strip().upper()
        if not t or 'NONE' in t or t == '-':
            return '-'
        for c in t:
            if 'A' <= c <= 'Z':
                return c
        return '-'
    arrow_class = letter_of(first(arrow_read))
    letters = [letter_of(t) for t in first(bar_letters_read).split(',') if t.strip()]
    if arrow_class == '-' or not letters:
        return {'frac': None, 'no_read': True, 'letters': letters,
                'arrow_class': arrow_class}
    n = int((reference or {}).get('n_bands', 7) or 7)
    expected = [chr(ord('A') + i) for i in range(n)]
    bottom = first(bottom_colour_read).strip().lower()
    ramp_ok = (letters == expected) and ('red' in bottom)
    stated = str((reference or {}).get('stated_class', '')).strip().upper()
    ok = ramp_ok and arrow_class == stated
    return {'frac': 1.0 if ok else 0.0, 'no_read': False, 'letters': letters,
            'arrow_class': arrow_class, 'ramp_ok': ramp_ok, 'bottom_colour': bottom,
            'stated': stated}

# end of label_ok_code
