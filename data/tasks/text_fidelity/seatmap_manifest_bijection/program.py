# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# code: law_code
import re
def seat(s):
    m=re.search(r'(\d+)\s*([A-Fa-f])', str(s))
    return (int(m.group(1)), m.group(2).upper()) if m else None
def shaded(s):
    if s is None or isinstance(s, dict): return set()
    t=str(s).upper()
    if 'NONE' in t: return set()
    return set(ch for ch in t if ch in 'ABCDEF')
def seats_shaded_on_map(code0, code1, row0, row1, r0, l0, r1, l1):
    """1 if both sampled codes read right and their seats are shaded on the map."""
    s0=seat(code0); s1=seat(code1)
    if s0 is None or s1 is None: return 0.0
    if s0 != (int(r0), str(l0).upper()) or str(l0).upper() not in shaded(row0): return 0.0
    if s1 != (int(r1), str(l1).upper()) or str(l1).upper() not in shaded(row1): return 0.0
    return 1.0

# end of law_code

# code: reconcile_code
import re


def _ans(x):
    if isinstance(x, dict):
        return x.get('answers') or []
    return list(x or [])


def _codes(answers):
    best = []
    for a in answers:
        got = re.findall(r'(?<![0-9A-Za-z])(\d{1,2})\s*([A-Fa-f])(?![A-Za-z0-9])',
                         str(a or ''))
        seq = ['%d%s' % (int(r), c.upper()) for r, c in got]
        if len(seq) > len(best):
            best = seq
    return best


def _rows(answers):
    best = {}
    for a in answers:
        cur = {}
        for chunk in re.split(r'[;\n]+', str(a or '')):
            m = re.match(r'\s*(?:row\s*)?(\d{1,2})\s*[:.\-]\s*(.*)$', chunk,
                         re.I)
            if not m:
                continue
            tail = m.group(2).upper()
            lets = set() if 'NONE' in tail else set(ch for ch in tail if ch in 'ABCDEF')
            cur[int(m.group(1))] = lets
        if len(cur) > len(best):
            best = cur
    return best


def reconcile(list_read, list_read2, map_read, n):
    """Compare the listed seat codes with the shaded seats on the map and list breaches."""
    a1 = _ans(list_read)
    a2 = _ans(list_read2)
    codes = _codes(a1 + a2)
    k1 = len(_codes(a1))
    k2 = len(_codes(a2))
    rows = _rows(_ans(map_read))
    occ_set = set('%d%s' % (r, c) for r, ls in rows.items() for c in ls)
    occ = sum(len(v) for v in rows.values())
    listed = len(codes)
    dup = listed - len(set(codes))
    out = {'declared_passengers': int(n), 'seat_codes_transcribed': listed,
           'witness_counts': [k1, k2],
           'distinct_codes': len(set(codes)), 'duplicate_codes': dup,
           'map_rows_transcribed': len(rows), 'occupied_cells': occ,
           'occupied_minus_listed': occ - listed,
           'listed_codes_not_shaded': sorted(set(codes) - occ_set)[:12],
           'shaded_cells_not_listed': sorted(occ_set - set(codes))[:12]}
    if listed < int(n) - 4 or len(rows) < 10:
        if k1 and k2 and abs(k1 - k2) <= 6 and len(rows) >= 10:
            out['uncertain'] = False
            out['breaches'] = ['sheet prints %d seat-code lines against %d declared'
                              % (listed, int(n))]
            out['verdict'] = 'sheet_short'
            return out
        out['uncertain'] = True
        out['refused'] = True
        out['verdict'] = 'transcription_incomplete'
        return out
    out['uncertain'] = False
    breaches = []
    if dup > 2:
        breaches.append('%d duplicate seat codes in the list' % dup)
    if abs(occ - listed) > 4:
        breaches.append('%d occupied cells vs %d listed passengers' % (occ, listed))
    out['breaches'] = breaches
    out['verdict'] = 'consistent' if not breaches else 'broken'
    return out
# end of reconcile_code
