# code: helpers
from genolympiad.task_helpers import sweep_banned_unless_count_disagrees
# end of helpers

# shared code: code_card
def answer_texts(node):
    return [' '.join(str(a or '').split()).strip() for a in (node or {}).get('answers') or []]


def _word(t, opts):
    ws = ''.join(c if c.isalpha() else ' ' for c in str(t or '').lower()).split()
    for o in sorted(opts, key=len, reverse=True):
        if o in ws:
            return o
    return None


def _keep(t, ok):
    return ''.join(c for c in str(t or '').lower() if c in ok)


def withheld_result(why):
    return {'tag': 'none', 'refused': True, 'verdict': why}


def yes_no_result(ok, why):
    return {'tag': 'yes' if ok else 'no', 'refused': False, 'verdict': why}


ALNUM = 'abcdefghijklmnopqrstuvwxyz0123456789'
EXPECT = ['crp', 'lft1', 'lft2', 'tft', 'ue1', 'ue2']
LEFT = '3'


def _rack(lb):
    raw = answer_texts(lb)
    if not raw:
        return None, withheld_result('no cut-out over the rack came back at all -> abstain rather '
                              'than zero the card')
    ks = []
    for x in raw:
        k = _keep(x, ALNUM)
        if not k:
            return None, withheld_result('a cut-out over a tube came back with no label on it, so '
                                  'the rack was not read -> abstain rather than zero the card')
        ks.append(k)
    return sorted(set(ks)), None


def test_tubes_match(label_reads):
    """Yes if the labelled test tubes are exactly the six expected portions."""
    labels, stop = _rack(label_reads)
    if stop:
        return stop
    got = sorted(k for k in labels if not k.startswith('retain'))
    return yes_no_result(got == EXPECT, 'the tubes carrying test labels read back as %s'
                % (','.join(got) or 'nothing'))


def one_retained_tube(label_reads):
    """Yes if exactly one tube is labelled as the retained sample."""
    labels, stop = _rack(label_reads)
    if stop:
        return stop
    kept = sorted(k for k in labels if k.startswith('retain'))
    return yes_no_result(len(kept) == 1, 'tubes labelled for a retained sample: %s'
                % (','.join(kept) or 'none'))


def _firstnum(v):
    out = ''
    for ch in str(v or ''):
        if ch.isdigit():
            out += ch
        elif out:
            break
    return out


def stock_level_matches(level_read):
    """Yes if the stock tube surface reads at the expected graduation."""
    answers = answer_texts(level_read)
    if not answers or not answers[0]:
        return withheld_result('nothing came back from the cut-out over the stock tube')
    graduation = _firstnum(answers[0])
    if not graduation:
        return withheld_result('the cut-out over the stock tube came back with no graduation figure '
                        'in it -> abstain rather than zero the card')
    return yes_no_result(graduation == LEFT, 'the surface in the stock tube reads back on the %s graduation' % graduation)

# end of code_card
