# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# shared code: code_sentry_mate
def check_sentry_mate(caption_reads):
    """Whether the caption's king, sentry and black king squares give a legal checkmate."""
    import re
    squares = re.findall(r'([a-h][1-8])', ' '.join(str(a) for a in ((caption_reads or {}).get('answers') or [])).lower())
    if len(squares) < 3:
        return {'ok': 'no', 'verdict': 'caption yielded fewer than three squares'}
    wk, st, bk = [(ord(t[0]) - 97, int(t[1]) - 1) for t in squares[:3]]
    adj = lambda a, b: max(abs(a[0] - b[0]), abs(a[1] - b[1])) == 1
    blks = lambda t: (wk[0] == st[0] == t[0] and min(st[1], t[1]) < wk[1] < max(st[1], t[1])) or (wk[1] == st[1] == t[1] and min(st[0], t[0]) < wk[0] < max(st[0], t[0]))
    sen = lambda t: t != st and ((adj(st, t) and st[0] != t[0] and st[1] != t[1]) or ((st[0] == t[0] or st[1] == t[1]) and not blks(t)))
    esc = [(bk[0] + dx, bk[1] + dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1) if (dx or dy) and 0 <= bk[0] + dx <= 7 and 0 <= bk[1] + dy <= 7]
    free = [e for e in esc if e != wk and not adj(wk, e) and not sen(e) and not (e == st and adj(wk, st))]
    ok = 'yes' if sen(bk) and not free and not adj(wk, bk) and len({wk, st, bk}) == 3 else 'no'
    return {'ok': ok, 'verdict': 'check on the black king: %s; open flight squares: %d; legal placement: %s; mate: %s' % ('yes' if sen(bk) else 'no', len(free), 'yes' if (len({wk, st, bk}) == 3 and not adj(wk, bk)) else 'no', ok)}

# end of code_sentry_mate
