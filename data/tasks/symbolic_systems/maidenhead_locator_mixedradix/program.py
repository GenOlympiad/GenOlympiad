# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# shared code: code_code_seq
def read_code_sequence(node, ring=None):
    """Join the codes read in reading order, grouping boxes into lines top to bottom."""
    answers = node.get('answers') if isinstance(node, dict) else None
    answers = list(answers) if isinstance(answers, (list, tuple)) else []
    geometry = ring.get('geometry') if isinstance(ring, dict) else None
    boxes = [b for b in (geometry or []) if isinstance(b, (list, tuple)) and len(b) >= 4]
    items = []
    for i, raw in enumerate(answers):
        joined = ''.join(c for c in str(raw).lower() if c.isalnum())
        if not joined:
            continue
        if i < len(boxes):
            b = boxes[i]
            items.append(((float(b[0]) + float(b[2])) / 2.0,
                          (float(b[1]) + float(b[3])) / 2.0, i, joined))
        else:
            items.append((1000000.0 + i, 0.0, i, joined))
    if boxes and items:
        heights = [abs(float(b[2]) - float(b[0])) for b in boxes]
        half = (sum(heights) / len(heights)) / 2.0
        items.sort(key=lambda t: (t[0], t[1]))
        grouped, cur, y0 = [], [], None
        for cy, cx, i, joined in items:
            if y0 is None or abs(cy - y0) <= half:
                cur.append((cx, i, joined))
                if y0 is None:
                    y0 = cy
            else:
                grouped.append(cur)
                cur, y0 = [(cx, i, joined)], cy
        if cur:
            grouped.append(cur)
        codes = [t for row in grouped for _, _, t in sorted(row)]
    else:
        codes = [t for _, _, _, t in items]
    joined = '|'.join(codes)
    return {'seq': joined, 'n': len(codes), 'verdict': 'codes read as %s' % (joined or 'nothing')}

# end of code_code_seq

# shared code: code_marked_cells
def check_marked_squares(cert, vals, want=None, alt=None):
    """List the grid squares confirmed as marked and check they all are lawful reference squares."""
    confirm_answers = cert.get('answers') if isinstance(cert, dict) else None
    confirm_answers = list(confirm_answers) if isinstance(confirm_answers, (list, tuple)) else []
    value_answers = vals.get('answers') if isinstance(vals, dict) else None
    value_answers = list(value_answers) if isinstance(value_answers, (list, tuple)) else []
    confirmed = [str(x).strip().lower().startswith('y') for x in confirm_answers]
    values = [''.join(c for c in str(x).lower() if c.isalnum()) for x in value_answers]
    rows = [b for i, b in enumerate(values) if b and i < len(confirmed) and confirmed[i]]
    txt = ', '.join(sorted(set(rows)))
    lawful = set()
    for x in (want, alt):
        x = ''.join(c for c in str(x or '').lower() if c.isalnum())
        if x:
            lawful.add(x)
    read_set = set(rows)
    ok = 'yes' if read_set and lawful and read_set <= lawful else 'no'
    return {'seq': txt, 'n': len(rows), 'ok': ok,
            'verdict': '%d marked cells read: %s (lawful cells on the shared line: %s)'
            % (len(rows), txt or 'nothing', ', '.join(sorted(lawful)))}

# end of code_marked_cells
