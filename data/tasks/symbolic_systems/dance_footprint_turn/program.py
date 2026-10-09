# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# shared code: code_footprint_turns
def worst_turn_error(key_reads, hour_reads, keys, wants):
    """The largest gap between read and wanted turns per beat, either direction allowed."""
    def lst(n):
        if isinstance(n, dict):
            n = n.get('answers') or []
        return list(n) if isinstance(n, (list, tuple)) else ([] if n is None else [n])
    def hour(v):
        d = ''.join(c for c in str(v) if c.isdigit())
        x = int(d) if d and len(d) <= 2 else None
        return x if x is not None and 1 <= x <= 12 else None
    want = [str(x) for x in lst(keys)]
    target_turns = [float(x) for x in lst(wants)]
    got = align_by_printed_key([{'key': x, 'h': v} for x, v in zip(lst(key_reads), lst(hour_reads))], want)
    degs = []
    for row in got:
        r = row if isinstance(row, dict) else {}
        x = hour(r.get('h'))
        if x is None:
            return {'obs': 180.0, 'exp': 0.0, 'verdict': 'a footprint direction was not read'}
        degs.append((x % 12) * 30.0)
    if len(degs) < len(target_turns) + 1:
        return {'obs': 180.0, 'exp': 0.0, 'verdict': 'only %d footprints read' % len(degs)}
    def worst_of(target):
        worst, say = 0.0, []
        for i in range(min(len(degs) - 1, len(target))):
            got_turn = (degs[i + 1] - degs[i]) % 360.0
            d = abs((got_turn - target[i] + 180.0) % 360.0 - 180.0)
            worst = d if d > worst else worst
            say.append('beat %d to %d turns %g against a wanted %g'
                       % (i + 1, i + 2, got_turn, target[i]))
        return worst, say
    wa, sa = worst_of(target_turns)
    wb, sb = worst_of([(360.0 - t) % 360.0 for t in target_turns])
    if wb < wa:
        return {'obs': wb, 'exp': 0.0,
                'verdict': 'the decal carries the sequence turned the opposite way, which the '
                           'wording of the brief leaves open: ' + '; '.join(sb)
                           + ' | worst %g' % wb}
    return {'obs': wa, 'exp': 0.0, 'verdict': '; '.join(sa) + ' | worst %g' % wa}

# end of code_footprint_turns

# shared code: code_footprint_feet
def count_feet_matched(key_reads, foot_reads, keys, wants):
    """Count footprints read as the wanted foot, allowing a start on either foot."""
    def lst(n):
        if isinstance(n, dict):
            n = n.get('answers') or []
        return list(n) if isinstance(n, (list, tuple)) else ([] if n is None else [n])
    def pick(v, opts):
        if v is None:
            return None
        s = ' '.join(str(v).lower().replace('-', ' ').split())
        if s in ('', 'none', 'n a', 'na', 'nil', 'empty', '?', '.'):
            return None
        for o in opts:
            if o in s:
                return o
        return None
    want = [str(x) for x in lst(keys)]
    target_feet = [str(x).lower() for x in lst(wants)]
    got = align_by_printed_key([{'key': x, 'f': v} for x, v in zip(lst(key_reads), lst(foot_reads))], want)
    def count(target):
        n, say = 0, []
        for i, row in enumerate(got):
            r = row if isinstance(row, dict) else {}
            p = pick(r.get('f'), ['left', 'right'])
            t = target[i] if i < len(target) else None
            if p is not None and t is not None and p == t:
                n += 1
            say.append('beat %s reads %r wanted %r' % (want[i] if i < len(want) else i, p, t))
        return n, say
    n1, s1 = count(target_feet)
    n2, s2 = count([('right' if t == 'left' else 'left') for t in target_feet])
    if n2 > n1:
        return {'n': n2, 'asked': len(want),
                'verdict': 'the run starts on the other foot, which the brief leaves open: '
                           + '; '.join(s2)}
    return {'n': n1, 'asked': len(want), 'verdict': '; '.join(s1) or 'nothing was read'}

# end of code_footprint_feet
