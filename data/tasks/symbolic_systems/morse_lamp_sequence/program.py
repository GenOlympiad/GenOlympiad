# code: helpers
from genolympiad.task_helpers import count_listed_items
# end of helpers

# code: slices_code
_WORDS = {'one': 1, 'a single': 1, 'single': 1, 'two': 2, 'three': 3, 'four': 4,
          'five': 5, 'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10}


def _rows_of(txt):
    import re
    s = str(txt if txt is not None else '').strip().lower()
    m = re.search(r'-?\d+', s)
    if m:
        try:
            return int(m.group(0))
        except ValueError:
            return None
    for w, v in _WORDS.items():
        if re.search(r'%s' % w, s):
            return v
    return None


def split_strip_into_frames(strip_box, n, one_row, rows_txt, src, aspect_min):
    """Cut the boxed frame strip into equal columns once both reads agree it is one row."""
    n = int(n)
    one_row_text = str(one_row if one_row is not None else '').strip().lower()
    rows = _rows_of(rows_txt)
    said_many = one_row_text.startswith('n')
    said_one = one_row_text.startswith('y')
    convicted = said_many and (rows is not None and rows >= 2)
    agreed_one = said_one and (rows == 1)
    g = (strip_box or {}).get('geometry') if isinstance(strip_box, dict) else None
    b = (g[0] if (g and isinstance(g[0], (list, tuple))) else g) if g else None
    if convicted:
        return {'geometry': [], 'n': 0, 'convicted': True, 'unreadable': False,
                'rows_read': rows, 'one_row_answer': one_row_text[:16],
                'verdict': 'the frames are not drawn as one horizontal row (the reader answers '
                           '"%s" and counts %s rows), so the single strip of %d equal frames '
                           'the prompt demands is not on the paper' % (one_row_text[:16], rows, n)}
    if not agreed_one:
        return {'geometry': [], 'n': 0, 'convicted': False, 'unreadable': True, 'refused': True,
                'rows_read': rows, 'one_row_answer': one_row_text[:16],
                'verdict': 'the two row witnesses do not agree ("%s" vs %s rows), so the layout '
                           'is uncertain and nothing is scored' % (one_row_text[:16], rows)}
    if not b:
        return {'geometry': [], 'n': 0, 'convicted': False, 'unreadable': True, 'refused': True,
                'rows_read': rows, 'one_row_answer': one_row_text[:16],
                'verdict': 'the strip of frames could not be located'}
    y0, x0, y1, x1 = [float(v) for v in b[:4]]
    W, H = src.size
    aspect = ((x1 - x0) * W) / max(1.0, (y1 - y0) * H)
    return {'geometry': [[y0, x0 + w * i + 0.2 * w, y1, x0 + w * i + 0.8 * w]
                         for w in [(x1 - x0) / float(n)] for i in range(n)],
            'n': n, 'convicted': False, 'unreadable': False, 'aspect': round(aspect, 2),
            'aspect_min': float(aspect_min), 'rows_read': rows,
            'verdict': 'both row witnesses say one row (%.1f wide for its height); the confirmed '
                       'strip was cut into %d equal columns' % (aspect, n)}

# end of slices_code

# code: hamming_code
def score_lamp_frames(read, want, strip):
    """Score the read on and off frames against the reference, losing two shares per mismatch."""
    if (strip or {}).get('convicted'):
        return {'frac': 0.0, 'unreadable': False, 'convicted': True,
                'verdict': (strip or {}).get('verdict')}
    answers = read.get('answers') if isinstance(read, dict) else read
    want = [int(v) for v in (want or [])]
    n = len(want)
    if not answers or n == 0:
        return {'frac': 0.0, 'unreadable': True, 'refused': True}
    got = []
    for a in answers:
        s = str(a).lower()
        ib, id_ = s.find('bright'), s.find('black')
        if ib < 0 and id_ < 0:
            return {'frac': 0.0, 'unreadable': True, 'refused': True}
        if ib < 0:
            got.append(0)
        elif id_ < 0:
            got.append(1)
        else:
            got.append(1 if ib < id_ else 0)
    mismatches = sum(1 for a, b in zip(got, want) if a != b) + abs(len(got) - n)
    return {'frac': round(max(0.0, 1.0 - 2.0 * mismatches / n), 4), 'hamming': mismatches, 'n': n,
            'unreadable': False, 'read': ''.join(str(v) for v in got),
            'want': ''.join(str(v) for v in want)}

# end of hamming_code
