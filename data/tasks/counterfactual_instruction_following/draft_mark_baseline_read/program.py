# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# shared code: code_ladder_reading
def check_draught_readings(captions, figures, positions, names, draughts):
    """Worst gap between each close-up's read draught and the draught the record expects."""
    offsets = {'lower half of the figure': 0.025, 'upper half of the figure': 0.075,
           'lower half of the bare gap': 0.125, 'upper half of the bare gap': 0.175}
    def lst(n):
        if isinstance(n, dict):
            n = n.get('answers') or []
        return list(n) if isinstance(n, (list, tuple)) else ([] if n is None else [n])
    def norm(v):
        s = ''.join(c if (c.isalpha() or c == ' ') else ' ' for c in str(v).lower())
        return ' '.join(s.split())
    def figure(v):
        d = ''.join(c for c in str(v) if c.isdigit())
        return float(d[:2]) / 10.0 if len(d) >= 2 else None
    want = [str(k).upper() for k in lst(names)]
    targets = lst(draughts)
    got = align_by_printed_key([{'key': str(k).upper(), 'f': f, 'p': p}
                                for k, f, p in zip(lst(captions), lst(figures), lst(positions))], want)
    worst, obs, exp, say = -1.0, 0.0, 9.99, []
    for i, r in enumerate(got):
        base = figure(r.get('f')) if isinstance(r, dict) else None
        step = offsets.get(norm(r.get('p'))) if isinstance(r, dict) else None
        nm = want[i] if i < len(want) else str(i)
        try:
            t = float(targets[i]) if i < len(targets) else None
        except (TypeError, ValueError):
            t = None
        if base is None or step is None or t is None:
            worst, obs, exp = 9.99, 0.0, 9.99
            say.append('%s: waterline not read' % nm)
            continue
        e = abs(base + step - t)
        say.append('%s: reads %.3f m, the record wants %.3f m, out by %.3f'
                   % (nm, base + step, t, e))
        if e > worst:
            worst, obs, exp = e, base + step, t
    return {'obs': obs, 'exp': exp, 'worst': worst,
            'verdict': '; '.join(say) or 'no draught mark was read'}

# end of code_ladder_reading

# shared code: code_ladder_build
def check_ladder_painting(captions, gap_reads, growth_reads, names):
    """Match if every close-up shows equal bare gaps and figures growing towards the top."""
    def lst(n):
        if isinstance(n, dict):
            n = n.get('answers') or []
        return list(n) if isinstance(n, (list, tuple)) else ([] if n is None else [n])
    def norm(v):
        s = ''.join(c if (c.isalpha() or c == ' ') else ' ' for c in str(v).lower())
        return ' '.join(s.split())
    want = [str(k).upper() for k in lst(names)]
    got = align_by_printed_key([{'key': str(k).upper(), 'g': g, 'd': d}
                                for k, g, d in zip(lst(captions), lst(gap_reads), lst(growth_reads))], want)
    seen, bad, say = 0, [], []
    for i, r in enumerate(got):
        g = norm(r.get('g')) if isinstance(r, dict) else ''
        d = norm(r.get('d')) if isinstance(r, dict) else ''
        nm = want[i] if i < len(want) else str(i)
        if not g or not d:
            bad.append(nm)
            say.append('%s: painted ladder not read' % nm)
            continue
        seen += 1
        if g != 'about the same' or d != 'towards the top':
            bad.append(nm)
        say.append('%s: bare plate %s, figures grow %s' % (nm, g, d))
    good = seen > 0 and seen == len(want) and not bad
    return {'state': 'match' if good else 'mismatch', 'n': seen,
            'verdict': '; '.join(say) + ' | wrong: ' + (' '.join(bad) or 'none')}

# end of code_ladder_build
