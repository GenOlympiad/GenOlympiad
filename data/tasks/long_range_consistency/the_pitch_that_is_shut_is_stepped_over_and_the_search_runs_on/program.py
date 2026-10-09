# code: helpers
from genolympiad.task_helpers import sweep_banned_unless_count_disagrees
# end of helpers

# shared code: code_card
def answer_texts(node):
    return [' '.join(str(a or '').split()).strip() for a in (node or {}).get('answers') or []]


def withheld_result(why):
    return {'tag': 'none', 'refused': True, 'verdict': why}


def yes_no_result(ok, why):
    return {'tag': 'yes' if ok else 'no', 'refused': False, 'verdict': why}


def _toks(t):
    return ''.join(c if c.isalnum() else ' ' for c in str(t or '').lower()).split()


NOTHING = ('no', 'none', 'nothing', 'blank', 'nil', 'empty')


def _pick(t, opts):
    ts = _toks(t)
    if 'not' in ts or 'neither' in ts:
        return None
    hits = []
    for w in ts:
        for o in sorted(opts, key=len, reverse=True):
            ok = (w == o) if len(o) < 3 else w.startswith(o[:3])
            if ok and o not in hits:
                hits.append(o)
                break
    return hits[0] if len(hits) == 1 else None


def _nums(t):
    raw, cur = [], ''
    for c in str(t or '') + ' ':
        if c.isdigit() or (c == '.' and cur and cur[-1].isdigit()):
            cur += c
        elif c == ',' and cur and cur[-1].isdigit():
            continue
        else:
            if cur:
                raw.append(cur)
            cur = ''
    out = []
    for s in raw:
        s = s.rstrip('.')
        if s:
            out.append(float(s))
    return out


def _said_nothing(t):
    ts = _toks(t)
    return bool(ts) and ts[0] in NOTHING and not _nums(t)


def _one_num(node, what):
    a = answer_texts(node)
    if len(a) != 1:
        return None, withheld_result('%d readings came back for %s, so no single figure exists there'
                              % (len(a), what))
    if _said_nothing(a[0]):
        return 'none', None
    n = _nums(a[0])
    if len(n) != 1:
        return None, withheld_result('%d figures were made out for %s: %r' % (len(n), what, a[0]))
    return n[0], None


def _one_of(node, opts, what):
    a = answer_texts(node)
    if len(a) != 1:
        return None, withheld_result('%d readings came back for %s' % (len(a), what))
    g = _pick(a[0], opts)
    if g is None:
        return None, withheld_result('the answer for %s was not one of the words offered: %r'
                              % (what, a[0]))
    return g, None


def _num_set(node, what):
    a = answer_texts(node)
    if len(a) != 1:
        return None, withheld_result('%d readings came back for %s' % (len(a), what))
    v = _nums(a[0])
    if not v:
        if _said_nothing(a[0]):
            return [], None
        return None, withheld_result('nothing that reads as a number was made out on %s: %r'
                              % (what, a[0]))
    return sorted(set(int(round(x)) for x in v)), None


def _seq(vals):
    return '|'.join(str(x) for x in vals)

FREE_PITCHES = [3]
SIXTH_TAG = 4473.0
SHEET_PITCH = 7.0


def check_slate_free_pitches(reads):
    """Check the slate lists exactly the pitches the field is left with free."""
    v, bad = _num_set(reads, 'the slate on the counter')
    if bad is not None:
        return bad
    return yes_no_result(v == FREE_PITCHES, 'the slate names %r as free against the %r the field is '
                                   'actually left with' % (v, FREE_PITCHES))


def check_pitch_six_tag(reads):
    """Check the hook of pitch 06 carries the booking pushed past the shut pitch."""
    v, bad = _one_num(reads, 'the hook of pitch 06')
    if bad is not None:
        return bad
    if v == 'none':
        return yes_no_result(False, 'the hook of pitch 06 was drawn with no tag on it, so the party the '
                           'shut pitch pushed along has gone somewhere else')
    return yes_no_result(abs(v - SIXTH_TAG) < 0.5,
                'the hook of pitch 06 carries booking %s against the %s the step over the shut '
                'pitch puts there' % (v, SIXTH_TAG))


def check_pitch_five_shut(reads):
    """Check the hook of pitch 05 reads as shut."""
    g, bad = _one_of(reads, ['tag', 'shut', 'nothing'], 'the hook of pitch 05')
    if bad is not None:
        return bad
    return yes_no_result(g == 'shut', 'the hook of pitch 05 was read as %s where the field has it shut '
                             'for its hardstanding' % g)


def check_sheet_pitch(reads):
    """Check the booking sheet names the reference pitch for that party."""
    v, bad = _one_num(reads, 'the booking line of that party')
    if bad is not None:
        return bad
    if v == 'none':
        return yes_no_result(False, 'that booking is not on the sheet at all')
    return yes_no_result(abs(v - SHEET_PITCH) < 0.5,
                'the sheet names pitch %s for that booking against the %s the commission pinned'
                % (v, SHEET_PITCH))

# end of code_card
