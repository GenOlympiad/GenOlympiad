# shared code: code_b4572fcfdf27
def _digit(s):
    t = ''.join(ch if ch.isdigit() else ' ' for ch in str(s or ''))
    ds = [int(v) for v in t.split()]
    if ds:
        return ds[-1]
    w = str(s or '').strip().lower()
    for k, v in (('none', 0), ('zero', 0), ('one', 1), ('two', 2), ('three', 3), ('four', 4)):
        if k in w:
            return v
    return None


def _colour(s):
    w = str(s or '').strip().lower()
    for c in ('green', 'yellow', 'amber', 'red', 'white', 'dark', 'none'):
        if c in w:
            return 'yellow' if c == 'amber' else c
    return None


def read_signal_heads(hp, lit_reads, colour_reads, src):
    """Read each signal head's lit lamp count and aspect, largest (nearest) head first."""
    geometry = (hp or {}).get('geometry') or []
    lit_answers = (lit_reads or {}).get('answers') or []
    colour_answers = (colour_reads or {}).get('answers') or []
    if not geometry or len(lit_answers) != len(geometry) or len(colour_answers) != len(geometry):
        return {'no_read': True, 'n_heads': 0, 'aspects': [], 'n_lit': [],
                'reason': 'the signal heads or their lamps did not read'}
    W, H = src.size
    rows = []
    for box, q1, q2 in zip(geometry, lit_answers, colour_answers):
        y0, x0, y1, x1 = [float(v) for v in box]
        w = abs(x1 - x0) * float(W) / 1000.0
        h = abs(y1 - y0) * float(H) / 1000.0
        n = _digit(q1)
        c = _colour(q2)
        if n is None or c is None:
            return {'no_read': True, 'n_heads': 0, 'aspects': [], 'n_lit': [],
                    'reason': 'a head answered neither a lamp count nor a lamp colour'}
        if n <= 0 or c in ('none', 'dark'):
            aspect, n = 'none', 0
        elif n >= 2 and c == 'yellow':
            aspect = 'doubleyellow'
        elif n == 1:
            aspect = c
        else:
            aspect = '%dx%s' % (n, c)
        rows.append({'area': w * h, 'w': round(w, 1), 'h': round(h, 1),
                     'n_lit': int(n), 'aspect': aspect})
    rows.sort(key=lambda r: -r['area'])
    return {'no_read': False, 'n_heads': len(rows),
            'aspects': [r['aspect'] for r in rows],
            'n_lit': [r['n_lit'] for r in rows], 'rows': rows,
            'verdict': 'nearest first: ' + '; '.join('#%d %s (%d lit)'
                       % (i + 1, r['aspect'], r['n_lit']) for i, r in enumerate(rows))}


def head_count_frac(heads_read, n_expected):
    """1 if the number of signal heads read equals the reference count, else 0."""
    return 1.0 if int(heads_read["n_heads"]) == int(n_expected) else 0.0


def lit_count_frac(heads_read, want):
    """The share of heads whose lit lamp count matches the reference, nearest first."""
    got = list(heads_read["n_lit"])
    want = [int(v) for v in want]
    ok = sum(1 for i, v in enumerate(want) if i < len(got) and int(got[i]) == v)
    return round(ok / float(max(len(want), len(got))), 4)


def aspect_seq_frac(heads_read, want):
    """1 if the aspects read nearest first equal the reference sequence, else 0."""
    got = [str(v).strip().lower() for v in heads_read["aspects"]]
    want = [str(v).strip().lower() for v in want]
    return 1.0 if got == want else 0.0

# end of code_b4572fcfdf27

# shared code: code_train_slot
def _digit(s):
    txt = ''.join(ch if ch.isdigit() else ' ' for ch in str(s or ''))
    ds = [int(v) for v in txt.split()]
    if ds:
        return ds[-1]
    w = str(s or '').strip().lower()
    for k, v in (('none', 0), ('zero', 0), ('one', 1), ('two', 2), ('three', 3),
                 ('four', 4), ('five', 5), ('six', 6)):
        if k in w:
            return v
    return None


def occupied_signal(hp, beyond, want):
    """1 if heads minus those beyond the train give the reference signal number, else 0."""
    g = (hp or {}).get('geometry') or []
    n_heads = len(g)
    beyond_count = _digit(beyond)
    if not n_heads or beyond_count is None:
        return {'no_read': True, 'frac': 0.0, 'n_heads': n_heads, 'beyond': beyond_count,
                'reason': 'the signal heads did not ring, or the beyond-count did not read'}
    if beyond_count < 0 or beyond_count > n_heads:
        return {'no_read': True, 'frac': 0.0, 'n_heads': n_heads, 'beyond': beyond_count,
                'reason': 'the beyond-count %d is outside 0..%d' % (beyond_count, n_heads)}
    occupied = n_heads - beyond_count
    ok = 1.0 if str(occupied) == str(want).strip() else 0.0
    return {'no_read': False, 'frac': ok, 'n_heads': n_heads, 'beyond': beyond_count, 'occupied': occupied,
            'verdict': '%d signal heads confirmed, %d of them beyond the train -> the train '
                       'stands beyond signal %d (briefed %s) -> frac %.1f'
                       % (n_heads, beyond_count, occupied, str(want), ok)}

# end of code_train_slot

# code: f_code
def two_or_more_heads(n):
    """1 if at least two signal heads were read, else 0."""
    return 1.0 if int(n) >= 2 else 0.0

# end of f_code
