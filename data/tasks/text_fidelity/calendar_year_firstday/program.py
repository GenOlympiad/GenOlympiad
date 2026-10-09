# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# shared code: code_feee0e153ff9
_WD = ('mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun')
def _first_answer(r):
    if isinstance(r, dict):
        a = r.get('answers') or [None]
        return a[0]
    return r
def month_starts_on_weekday(ans, month, want_wd):
    """1 if the 1st of the month sits under its true weekday column, else 0."""
    import re
    a = _first_answer(ans)
    if a is None:
        return {'frac': 0.0, 'verdict': 'the %s grid could not be read' % month,
                'read': None}
    got = None
    for w in re.findall(r'[A-Za-z]+', str(a)):
        if w[:3].lower() in _WD:
            got = w[:3].lower()
            break
    want = str(want_wd).strip()[:3].lower()
    if got is None:
        return {'frac': 0.0,
                'verdict': 'no weekday header was named above the 1 of %s (reader said %r)'
                           % (month, str(a)[:60]), 'read': None}
    ok = (got == want)
    return {'frac': 1.0 if ok else 0.0,
            'verdict': 'the 1 of %s sits under %s, calendar-true %s -> frac %s'
                       % (month, got.title(), want.title(), 1.0 if ok else 0.0),
            'read': got}

# end of code_feee0e153ff9
