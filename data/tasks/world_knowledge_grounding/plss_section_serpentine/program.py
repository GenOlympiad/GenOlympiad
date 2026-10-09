# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# shared code: code_section_steps
def section_step_agreement(mid, up, dn, lf, want, home):
    """Count how many number steps above, below and left of the school section match."""
    def lst(n):
        if isinstance(n, dict):
            n = n.get('answers') or []
        return list(n) if isinstance(n, (list, tuple)) else ([] if n is None else [n])
    def whole(v):
        d = ''.join(c for c in str(v) if c.isdigit())
        return int(d[:2]) if d else None
    def cls(v):
        w = ''.join(c if c.isalpha() else ' ' for c in str(v).lower())
        if 'more' in w:
            return 'one more'
        if 'less' in w or 'fewer' in w:
            return 'one less'
        if 'neither' in w:
            return 'neither'
        return None
    targets = []
    for x in lst(want):
        c = cls(x)
        if c:
            targets.append(c)
    try:
        school = int(home)
    except (TypeError, ValueError):
        school = -1
    mid_reads = lst(mid)
    school_index = -1
    for i, m in enumerate(mid_reads):
        if whole(m) == school:
            school_index = i
    if school_index < 0 or not targets:
        return {'ok': 0, 'n': 0,
                'verdict': 'no lettered square in the cut-outs carries the number %d' % school}
    got = []
    for arr in (lst(up), lst(dn), lst(lf)):
        got.append(cls(arr[school_index]) if school_index < len(arr) else None)
    agreed = 0
    for i, t in enumerate(targets):
        if i < len(got) and got[i] == t:
            agreed += 1
    return {'ok': agreed, 'n': len(got),
            'verdict': 'above, below and left of section %d the numbers step %s; the survey '
                       'practice wants %s; %d of %d agree'
                       % (school, got, targets, agreed, len(targets))}

# end of code_section_steps

# shared code: code_north_arrow
def north_arrow_match(ans, want):
    """Match the single word read on the north arrow against the reference word."""
    def lst(n):
        if isinstance(n, dict):
            n = n.get('answers') or []
        return list(n) if isinstance(n, (list, tuple)) else ([] if n is None else [n])
    def norm(v):
        s = ''.join(c if c.isalpha() else ' ' for c in str(v).lower())
        return ' '.join(s.split())
    got = []
    for x in lst(ans):
        w = norm(x)
        if w:
            got.append(w)
    t = ''
    for x in lst(want):
        t = norm(x) or t
    good = len(got) == 1 and t != '' and got[0] == t
    return {'state': 'match' if good else 'mismatch', 'n': len(got),
            'verdict': 'the north arrow reads %s, the sheet is laid out for %s'
                       % (' '.join(got) or 'nothing', t or 'nothing')}

# end of code_north_arrow
