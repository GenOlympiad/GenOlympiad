# shared code: code_d45709842058
def classify_symbol_outline(edge, lines):
    """Name the logic symbol shape from its read back edge and its count of curved lines."""
    edge_text = str(edge or '').strip().lower()
    lines_text = str(lines or '').strip().lower()
    if 'straight' in edge_text or 'flat' in edge_text:
        return 'DSHAPE'
    if 'curv' in edge_text or 'round' in edge_text or 'bulg' in edge_text or 'bow' in edge_text:
        if 'extra' in lines_text or 'two' in lines_text:
            return 'DOUBLE'
        if 'single' in lines_text or 'one' in lines_text:
            return 'SINGLE'
    return 'UNREAD'

# end of code_d45709842058

# shared code: code_07067cb4f255
def _blob(r):
    if isinstance(r, dict):
        a = r.get('answers') or [None]
        return '' if a[0] is None else str(a[0])
    return '' if r is None else str(r)
def y_column(blob, n_rows):
    import re
    data = []
    for line in str(blob).splitlines():
        digs = [t for t in re.split(r'[\s,;|]+', line.strip()) if re.fullmatch(r'[01]', t)]
        if len(digs) >= 2:
            data.append(int(digs[-1]))
    if len(data) < n_rows:
        return None
    return [[d] for d in data[:n_rows]]
def _digs(x):
    import re
    if x is None: return []
    if isinstance(x,(list,tuple)):
        flat = []
        for e in x:
            if isinstance(e,(list,tuple)): flat += [str(t) for t in e]
            else: flat.append(str(e))
        toks = flat
    else:
        toks = re.split(r'[\s,;]+', str(x))
    out = []
    for t in toks:
        t = t.strip()
        if re.fullmatch(r'[01]', t): out.append(int(t))
    return out
def score_output_column(vseq, r2, target):
    """The share of truth table output rows read correctly, capped at 0.25 if any is wrong."""
    wanted = [int(v) for v in target]
    used = 'seq'
    read = vseq if not isinstance(vseq, dict) else None
    if read is None or len(_digs(read)) < len(wanted):
        read = y_column(_blob(r2), len(wanted)); used = 'transcription'
    if read is None:
        return {'frac': 0.0, 'no_read': True, 'used': 'none'}
    read_digits = _digs(read)
    if not wanted:
        return {'frac': 0.0, 'no_read': False, 'used': used}
    rows_right = sum(1 for i in range(len(wanted)) if i < len(read_digits) and read_digits[i] == wanted[i])
    frac = round(rows_right/len(wanted), 4)
    if rows_right < len(wanted):
        frac = min(frac, 0.25)
    return {'frac': frac, 'no_read': False, 'used': used,
            'rows_ok': rows_right, 'rows': len(wanted), 'read': read_digits[:len(wanted)], 'want': wanted}

# end of code_07067cb4f255
