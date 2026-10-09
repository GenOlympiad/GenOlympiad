# shared code: code_bcce2ca09661
def _rows(seq):
    if not isinstance(seq, (list, tuple)) or len(seq) < 9:
        return None
    out = []
    for k in range(3):
        row = []
        for j in range(3):
            t = str(seq[k * 3 + j]).strip()
            if t not in ('0', '1'):
                return None
            row.append(int(t))
        out.append(row)
    return out


def _flip(m):
    return [list(reversed(r)) for r in m]


def _turn(m):
    return [list(reversed(r)) for r in reversed(m)]


def decode(m, table):
    try:
        return ''.join(table[''.join(str(b) for b in r)] for r in m)
    except (KeyError, TypeError):
        return ''


def decode_states(seq, reference):
    """Decode the dot pattern as drawn, flipped, turned and both, and see which spells the word."""
    matrix = _rows(seq)
    if matrix is None:
        return {'unreadable': True, 'crash': 'the nine dots could not be read as solid/hollow'}
    table = dict(reference.get('table') or {})
    word = str(reference.get('word') or '').upper()
    decodes = {'identity': decode(matrix, table), 'flip': decode(_flip(matrix), table),
           'turn': decode(_turn(matrix), table), 'composite': decode(_flip(_turn(matrix)), table)}
    solving_states = [k for k, v in decodes.items() if v == word]
    crash = None
    if decodes['identity'] == word:
        crash = 'cut readable as it lies -- the transform was never applied'
    elif decodes['flip'] == word or decodes['turn'] == word:
        crash = 'only one of the two steps was applied'
    elif not solving_states:
        crash = 'no state of the drawn pattern spells the word'
    return {'unreadable': False, 'matrix': matrix, 'decodes': decodes, 'word': word,
            'composite_ok': 1.0 if decodes['composite'] == word else 0.0,
            'exclusive': 1.0 if solving_states == ['composite'] else 0.0,
            'solves': solving_states, 'crash': crash}

# end of code_bcce2ca09661

# code: crosscheck_code
def solid_count_agrees(n, decoded, reference):
    """1 if the counted solid dots equal the number of solid dots in the read pattern, else 0."""
    matrix = (decoded or {}).get('matrix')
    from_bits = None if not matrix else sum(sum(r) for r in matrix)
    try:
        said = int(float(n))
    except (TypeError, ValueError):
        said = None
    return {'frac': 1.0 if (said is not None and said == from_bits) else 0.0,
            'counted': said, 'from_bits': from_bits, 'gt': reference.get('n_solid')}

# end of crosscheck_code
