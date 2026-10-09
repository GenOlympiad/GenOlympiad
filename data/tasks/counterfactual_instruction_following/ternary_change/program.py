# code: helpers
from genolympiad.task_helpers import count_listed_items
# end of helpers

# code: cols_code
def column_windows(heading_boxes, heading_confirms, heading_values):

    """Turn the confirmed column headings into column windows below them, left to right."""
    def yes(a):
        return str(a).strip().lower().startswith('y')

    def num(a):
        t = ''
        for ch in str(a if a is not None else ''):
            if ch.isdigit():
                t += ch
            elif t:
                break
        return int(t) if t else None

    geometry = (heading_boxes or {}).get('geometry') or []
    confirms = (heading_confirms or {}).get('answers') or []
    values = (heading_values or {}).get('answers') or []
    heads = []
    for i in range(min(len(geometry), len(confirms))):
        if not yes(confirms[i]):
            continue
        b = [float(v) for v in geometry[i][:4]]
        heads.append({'cx': (b[1] + b[3]) / 2.0, 'bottom': max(b[0], b[2]),
                      'den': num(values[i]) if i < len(values) else None})
    heads.sort(key=lambda h: h['cx'])
    if not heads:
        return {'no_plan': True, 'refused': True, 'geometry': [], 'dens': [], 'n': 0,
                'reason': 'no printed column heading was confirmed'}
    top = min(990.0, max(h['bottom'] for h in heads) + 5.0)
    wins = []
    for k in range(len(heads)):
        left = 0.0 if k == 0 else (heads[k - 1]['cx'] + heads[k]['cx']) / 2.0
        right = 1000.0 if k == len(heads) - 1 else (heads[k]['cx'] + heads[k + 1]['cx']) / 2.0
        wins.append([top, left, 1000.0, right])
    return {'no_plan': False, 'refused': False, 'geometry': wins,
            'dens': [h['den'] for h in heads], 'n': len(heads),
            'verdict': '%d confirmed headings -> %d column windows'
                       % (len(heads), len(wins))}

# end of cols_code

# code: coin_counted_code
WORDS = {'zero': 0, 'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5, 'six': 6,
         'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10}


def _num(a):
    if a is None:
        return None
    buf = ''
    for ch in str(a):
        if ch.isdigit():
            buf += ch
        elif buf:
            break
    if buf:
        return int(buf)
    for w in ''.join(ch if ch.isalpha() else ' ' for ch in str(a).lower()).split():
        if w in WORDS:
            return WORDS[w]
    return None


def coin_counted(windows, coin_counts):
    """Add the coins counted in each column to the coin value its heading names."""
    dens = (windows or {}).get('dens') or []
    answers = (coin_counts or {}).get('answers') or []
    counts = {27: 0, 9: 0, 3: 0, 1: 0}
    stray, named = 0, 0
    for i in range(min(len(dens), len(answers))):
        n = _num(answers[i])
        if n is None:
            return {'v0': None, 'v1': None, 'v2': None, 'v3': None, 'no_read': True,
                    'refused': True, 'verdict': 'one column could not be counted'}
        if dens[i] in counts:
            counts[dens[i]] += n
            named += 1
        else:
            stray += n
    if named == 0:
        return {'v0': 0, 'v1': 0, 'v2': 0, 'v3': 0, 'no_read': False, 'stray': stray,
                'verdict': 'no column heading named a coin of this currency, so no column of '
                           '27, 9, 3 or 1 holds anything'}
    return {'v0': counts[27], 'v1': counts[9], 'v2': counts[3], 'v3': counts[1],
            'no_read': False, 'n_cols': len(dens), 'stray': stray,
            'verdict': '%d labelled columns were counted one by one, giving 27-coins %d, '
                       '9-coins %d, 3-coins %d, 1-coins %d (%d coins sat under a heading this '
                       'currency has no coin for)'
                       % (len(dens), counts[27], counts[9], counts[3], counts[1], stray)}

# end of coin_counted_code

# code: chk_code
def chk(v0, v1, v2, v3, w0, w1, w2, w3):
    reads, want = (v0, v1, v2, v3), (w0, w1, w2, w3)
    def num(a):
        if a is None or isinstance(a, dict):
            return None
        try:
            return int(round(float(a)))
        except (TypeError, ValueError):
            return None
    got = [num(r) for r in reads]
    if any(g is None for g in got):
        return {'frac': None, 'no_read': True, 'refused': True, 'got': got}
    prod = 1.0
    for g, w in zip(got, want):
        prod *= 1.0 if g == int(w) else 0.0
    return {'frac': prod, 'no_read': False, 'got': got,
            'want': [int(w) for w in want]}

# end of chk_code
