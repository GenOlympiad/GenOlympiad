# code: helpers
from genolympiad.task_helpers import (
    compose_reads, join_answers, line_coverage, panel_slots_verdict)
# end of helpers

# code: jar_reads_code

def _cx(b):
    return (float(b[1]) + float(b[3])) / 2.0


def _cy(b):
    return (float(b[0]) + float(b[2])) / 2.0


def _yes(a):
    return str(a).strip().lower().startswith('y')


def _reading_order(geo, ok, *cols):
    items = []
    for i in range(min(len(geo), len(ok))):
        if not _yes(ok[i]):
            continue
        items.append((geo[i], [(c[i] if i < len(c) else None) for c in cols]))
    items.sort(key=lambda it: _cy(it[0]))
    rows, cur = [], []
    for it in items:
        if cur and abs(_cy(it[0]) - _cy(cur[-1][0])) >= 0.5 * max(
                abs(float(it[0][2]) - float(it[0][0])),
                abs(float(cur[-1][0][2]) - float(cur[-1][0][0]))):
            rows.append(cur)
            cur = []
        cur.append(it)
    if cur:
        rows.append(cur)
    out = []
    for r in rows:
        out.extend(sorted(r, key=lambda it: _cx(it[0])))
    return out


def read_cartons(carton_boxes, carton_confirms, carton_numbers, carton_marks, reference):
    """Read the printed temperature and band of each confirmed carton, left to right."""
    items = _reading_order((carton_boxes or {}).get('geometry') or [],
                           (carton_confirms or {}).get('answers') or [],
                           (carton_numbers or {}).get('answers') or [],
                           (carton_marks or {}).get('answers') or [])
    nums = [str(v[0]) if v[0] is not None else '' for _b, v in items]
    marks = [str(v[1]) if v[1] is not None else '' for _b, v in items]
    return {'nums': nums, 'marks': marks, 'n': len(items),
            'verdict': '%d carriers confirmed by the ring; left to right their cards read %s and '
                       'their trimming reads %s' % (len(items), nums, marks)}

# end of jar_reads_code

# code: strips_code

def vertical_strip_boxes(n):
    """Split the frame into n equal vertical strips, left to right."""
    n = max(1, int(n))
    return [[0, int(round(1000.0 * i / n)), 1000, int(round(1000.0 * (i + 1) / n))]
            for i in range(n)]

# end of strips_code
