# code: helpers
from genolympiad.task_helpers import sweep_banned_unless_count_disagrees
# end of helpers

# shared code: code_tc
_STRIP = chr(34) + chr(39) + '*_.,:;-([ '


def answer_texts(node):
    return [' '.join(str(a or '').split()).strip() for a in (node or {}).get('answers') or []]


def _one(node):
    for t in answer_texts(node):
        if t and t.lower() != 'none':
            return t
    return ''


def _head(t):
    return str(t or '').strip().lower().lstrip(_STRIP)


def _first(t):
    h = _head(t)
    return h.split()[0].strip(_STRIP) if h.split() else ''


def _digits(t):
    return ''.join(c for c in str(t or '') if c.isdigit())


def _num(t):
    keep = ''.join(c for c in str(t or '') if c.isdigit() or c == '.')
    try:
        return float(keep)
    except ValueError:
        return None


def _alnum(t):
    return ''.join(c for c in str(t or '').lower() if c.isalnum())


def withheld_result(why):
    return {'tag': 'none', 'refused': True, 'verdict': why}


def yes_no_result(ok, why):
    return {'tag': 'yes' if ok else 'no', 'refused': False, 'verdict': why}


def word(node, want):
    t = _first(_one(node))
    if not t:
        return withheld_result('the cut-out came back empty -> abstain, do not book a model zero')
    return yes_no_result(t.startswith(str(want)), 'the reader answered ' + t + ', wanted ' + str(want))


WANT = {'010859;29': '010900;02', '010959;29': '011000;00',
        '011959;29': '012000;00', '011014;15': '011014;16'}


def _tc(t):
    s = str(t or '')
    out = ''
    for c in s:
        if c.isdigit():
            out += c
        elif c == ';':
            out += ';'
    return out


def next_frame_rows(node):
    """Check that all four rows give the correct next drop-frame timecode."""
    seen, bad = [], []
    got = 0
    for a in answer_texts(node):
        parts = [p for p in str(a).replace(',', ' ').split() if any(c.isdigit() for c in p)]
        if len(parts) < 2:
            continue
        k, v = _tc(parts[0]), _tc(parts[1])
        want = WANT.get(k)
        got += 1
        seen.append(k + ' -> ' + v)
        if want is None or v != want:
            bad.append(k + ' gave ' + v)
    if got < 4:
        return withheld_result('only ' + str(got) + ' of 4 rows read back a pair of codes -> abstain')
    return yes_no_result(not bad, '; '.join(seen) + ('  WRONG: ' + '; '.join(bad) if bad else ''))


def monitor_matches_first_row(window_node, node):
    """Check that the monitor timecode equals the next frame written in the first row."""
    shown = _tc(_one(window_node))
    if not shown:
        return withheld_result('the monitor window came back empty -> abstain')
    first = ''
    for a in answer_texts(node):
        parts = [p for p in str(a).replace(',', ' ').split() if any(c.isdigit() for c in p)]
        if len(parts) >= 2 and _tc(parts[0]) == '010859;29':
            first = _tc(parts[1])
    if not first:
        return withheld_result('the first row did not read back -> abstain')
    return yes_no_result(shown == first, 'the monitor shows ' + shown + ' and the first row gives ' + first)

# end of code_tc
