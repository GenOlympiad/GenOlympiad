# shared code: code_drift_bearing
def check_drift_bearings(time_reads, direction_reads, hours, set_degrees):
    """The worst angle between each hour's joining line and the stream's set direction."""
    def lst(n):
        if isinstance(n, dict):
            n = n.get('answers') or []
        return list(n) if isinstance(n, (list, tuple)) else ([] if n is None else [n])
    def key(v):
        return ''.join(c for c in str(v) if c.isdigit())
    pts = ['up', 'up and right', 'right', 'down and right', 'down', 'down and left',
           'left', 'up and left']
    def deg(v):
        w = ' '.join(str(v).strip().lower().split())
        return pts.index(w) * 45.0 if w in pts else None
    want = [key(h) for h in lst(hours)]
    try:
        target = float(set_degrees)
    except (TypeError, ValueError):
        target = None
    rows = [{'key': key(k), 'd': d} for k, d in zip(lst(time_reads), lst(direction_reads))]
    got = align_by_printed_key(rows, want)
    seen, worst, obs, say = 0, -1.0, 0.0, []
    for i, r in enumerate(got):
        d = deg(r.get('d')) if isinstance(r, dict) else None
        k = want[i] if i < len(want) else str(i)
        if d is None or target is None:
            say.append('%s: joining line not read' % k)
            continue
        seen += 1
        e = abs((d - target + 180.0) % 360.0 - 180.0)
        say.append('%s: line runs %g, stream sets %g, off by %g' % (k, d, target, e))
        if e > worst:
            worst, obs = e, d
    if seen != len(want) or target is None:
        return {'obs': 180.0, 'exp': 0.0, 'worst': 180.0, 'n': seen,
                'verdict': '; '.join(say) + ' | fewer than every hour was read'}
    return {'obs': obs, 'exp': target, 'worst': worst, 'n': seen,
            'verdict': '; '.join(say)}

# end of code_drift_bearing

# shared code: code_drift_span
def check_drift_spans(time_reads, length_reads, hours, miles):
    """The worst gap between each hour's line length in squares and the stream's drift."""
    def lst(n):
        if isinstance(n, dict):
            n = n.get('answers') or []
        return list(n) if isinstance(n, (list, tuple)) else ([] if n is None else [n])
    def key(v):
        return ''.join(c for c in str(v) if c.isdigit())
    def num(v):
        s = ''.join(c for c in str(v) if c.isdigit() or c == '.')
        try:
            return float(s)
        except (TypeError, ValueError):
            return None
    want = [key(h) for h in lst(hours)]
    target = num(miles)
    rows = [{'key': key(k), 'l': l} for k, l in zip(lst(time_reads), lst(length_reads))]
    got = align_by_printed_key(rows, want)
    seen, worst, obs, say = 0, -1.0, 99.0, []
    for i, r in enumerate(got):
        v = num(r.get('l')) if isinstance(r, dict) else None
        k = want[i] if i < len(want) else str(i)
        if v is None or target is None:
            say.append('%s: span not read' % k)
            continue
        seen += 1
        e = abs(v - target)
        say.append('%s: line spans %g squares, one hour of stream wants %g' % (k, v, target))
        if e > worst:
            worst, obs = e, v
    if seen != len(want) or target is None:
        return {'obs': 99.0, 'exp': target if target is not None else 0.0, 'worst': 99.0,
                'n': seen, 'verdict': '; '.join(say) + ' | fewer than every hour was read'}
    return {'obs': obs, 'exp': target, 'worst': worst, 'n': seen, 'verdict': '; '.join(say)}

# end of code_drift_span

# shared code: code_hour_labels
def read_hour_labels(time_reads):
    """The four digit hour labels read on the plot, in reading order."""
    def lst(n):
        if isinstance(n, dict):
            n = n.get('answers') or []
        return list(n) if isinstance(n, (list, tuple)) else ([] if n is None else [n])
    out, say = [], []
    for v in lst(time_reads):
        d = ''.join(c for c in str(v) if c.isdigit())
        if len(d) == 4:
            out.append(d)
            say.append('plot lettered %s' % d)
    return {'obs': out, 'n': len(out),
            'verdict': '; '.join(say) or 'no hourly plot was lettered'}

# end of code_hour_labels
