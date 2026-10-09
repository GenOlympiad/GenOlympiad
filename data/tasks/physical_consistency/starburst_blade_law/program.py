# code: helpers
from genolympiad.task_helpers import count_listed_items
# end of helpers

# code: biggest_for_law_code

WORDS = dict(zip('zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen'.split(), range(17)))
def _num(a):
    s = '' if a is None else str(a); ds = ''.join(c if c.isdigit() else ' ' for c in s).split(); ws = [WORDS[w] for w in ''.join(c if c.isalpha() else ' ' for c in s.lower()).split() if w in WORDS]
    return int(ds[0]) if ds else (ws[0] if ws else None)
def count_in_largest_closeup(closeup_boxes, count_reads):
    """The spike count read in the largest confirmed close-up box, or a refusal."""
    boxes = (closeup_boxes or {}).get('geometry') or []; answers = (count_reads or {}).get('answers') or []; best, area = None, -1.0
    for i in range(len(answers)):
        n = _num(answers[i]); a = 0.0
        if n is not None and i < len(boxes): y0, x0, y1, x1 = [float(v) for v in boxes[i][:4]]; a = abs(y1 - y0) * abs(x1 - x0)
        if n is not None and a > area: best, area = n, a
    if best is None: return {'n': None, 'no_read': True, 'refused': True, 'verdict': 'no close-up gave a usable count'}
    return {'n': best, 'no_read': False, 'n_boxes': len(answers), 'verdict': 'the largest of the %d confirmed close-ups counted %d' % (len(answers), best)}

# end of biggest_for_law_code

# code: c_code
def count_matches(n,t):
 """1 if the count is within 0.5 of the wanted spike count, else 0."""
 try: v=float(n); tt=float(t)
 except: return 0.0
 return 1.0 if abs(v-tt)<0.5 else 0.0

# end of c_code

# code: biggest_for_d1_code

WORDS = dict(zip('zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen'.split(), range(17)))
def _num(a):
    s = '' if a is None else str(a); ds = ''.join(c if c.isdigit() else ' ' for c in s).split(); ws = [WORDS[w] for w in ''.join(c if c.isalpha() else ' ' for c in s.lower()).split() if w in WORDS]
    return int(ds[0]) if ds else (ws[0] if ws else None)
def count_in_largest_closeup(closeup_boxes, count_reads):
    """The spike count read in the largest confirmed close-up box, or a refusal."""
    boxes = (closeup_boxes or {}).get('geometry') or []; answers = (count_reads or {}).get('answers') or []; best, area = None, -1.0
    for i in range(len(answers)):
        n = _num(answers[i]); a = 0.0
        if n is not None and i < len(boxes): y0, x0, y1, x1 = [float(v) for v in boxes[i][:4]]; a = abs(y1 - y0) * abs(x1 - x0)
        if n is not None and a > area: best, area = n, a
    if best is None: return {'n': None, 'no_read': True, 'refused': True, 'verdict': 'no close-up gave a usable count'}
    return {'n': best, 'no_read': False, 'n_boxes': len(answers), 'verdict': 'the largest of the %d confirmed close-ups counted %d' % (len(answers), best)}

# end of biggest_for_d1_code

# code: c_code_2
def count_within_one(n,t):
 """1 if the count is within 1.5 of the wanted spike count, else 0."""
 try: v=float(n); tt=float(t)
 except: return 0.0
 return 1.0 if abs(v-tt)<1.5 else 0.0

# end of c_code_2
