# shared code: code_ball
def _one(node):
    for raw in (node or {}).get('answers') or []:
        t = ' '.join(str(raw or '').lower().split()).strip(' .,:-')
        if t and t != 'none':
            return t
    return ''
def _all(node):
    out = []
    for raw in (node or {}).get('answers') or []:
        out.append(' '.join(str(raw or '').lower().split()).strip(' .,:-'))
    return out
def _num(t):
    keep = ''
    neg = False
    s = str(t or '')
    for i, ch in enumerate(s):
        if ch.isdigit() or ch == '.':
            keep += ch
        elif ch == '-' and not keep:
            neg = True
        elif keep:
            break
    try:
        v = float(keep)
    except ValueError:
        return None
    return -v if neg else v
def _head(t):
    w = str(t or '').split()
    return w[0] if w else ''
def _norm(t):
    keep = ''
    for ch in str(t or '').lower():
        if ch.isalnum():
            keep += ch
    return keep
def _rawone(node):
    for raw in (node or {}).get('answers') or []:
        t = str(raw or '').strip()
        if t and t.lower() != 'none':
            return t
    return ''
def _lines(node):
    out = []
    for raw in (node or {}).get('answers') or []:
        for part in str(raw or '').replace('\r', '\n').split('\n'):
            t = ' '.join(part.split()).strip()
            if t:
                out.append(t)
    return out
def _first(node):
    a = _all(node)
    return a[0] if a else ''
def _yes(t):
    return _norm(t).startswith('yes')
def _no(t):
    h = _norm(t)
    return h.startswith('no') or h.startswith('none') or h.startswith('nothing')
def _hold(msg, **extra):
    d = {'tag': 'no', 'refused': True, 'verdict': msg}
    d.update(extra)
    return d
def _say(ok, msg, **extra):
    d = {'tag': 'yes' if ok else 'no', 'refused': False, 'verdict': msg}
    d.update(extra)
    return d

def _where(t):
    w = _norm(t)
    for k, v in (('middle', 'middle'), ('centre', 'middle'), ('center', 'middle'),
                 ('halfway', 'halfway'), ('half', 'halfway'),
                 ('rim', 'rim'), ('edge', 'rim'), ('outer', 'rim')):
        if k in w:
            return v
    return None


def reflection_shows_van(seen, named):
    """Whether the ball's reflection shows the van, abstaining if a read is missing."""
    seen_text, named_text = _one(seen), _one(named)
    if not seen_text:
        return _hold('the presence question about the ball did not come back -> abstain')
    if _no(seen_text):
        return _say(False, 'nothing that looks like the van appears anywhere in the ball')
    if not named_text:
        return _hold('the ball was said to hold the van but nothing was quoted back '
                     '-> abstain')
    return _say('van' in _norm(named_text) or 'vehicle' in _norm(named_text) or 'lorry' in _norm(named_text)
                or 'truck' in _norm(named_text),
                'the reflection was read back as %s' % named_text, said=named_text)


def check_reflection_radii(van, wall):
    """Whether the van reads in the middle of the ball and the wall at its rim."""
    van_place, wall_place = _where(_one(van)), _where(_one(wall))
    if van_place is None or wall_place is None:
        return _hold('one of the two radius questions did not come back as one of the three '
                     'offered answers -> abstain', van=van_place, wall=wall_place)
    return _say(van_place == 'middle' and wall_place == 'rim',
                'the van reads %s and the wall reads %s; on a mirror ball the thing behind the '
                'camera lands in the middle and the thing the camera faces is squeezed into the '
                'rim' % (van_place, wall_place), van=van_place, wall=wall_place)


def check_reflection_sides(crane, marquee):
    """Whether the crane reads on the left of the ball and the marquee on the right."""
    a, b = _norm(_one(crane)), _norm(_one(marquee))
    if not a or not b:
        return _hold('one of the two side questions did not come back -> abstain')
    ok_a = a.startswith('left')
    ok_b = b.startswith('right')
    if not (a.startswith('left') or a.startswith('right')):
        return _hold('the crane side came back as %s, which is neither left nor right '
                     '-> abstain' % a)
    if not (b.startswith('left') or b.startswith('right')):
        return _hold('the marquee side came back as %s, which is neither left nor right '
                     '-> abstain' % b)
    return _say(ok_a and ok_b,
                'the crane reads %s and the marquee reads %s' % (a, b), crane=a, marquee=b)

# end of code_ball

# shared code: code_sweepgate
def _sg_txt(v):
    return ' '.join(str('' if v is None else v).split()).strip()


def _sg_head(v):
    return _sg_txt(v).lower().lstrip('*_"\'.,:;-([ ')


def _sg_yes(v):
    return _sg_head(v).startswith('yes')


def _sg_no(v):
    h = _sg_head(v)
    return h.startswith('no') or h.startswith('none') or h.startswith('nothing')


def scan_for_forbidden_content(sweep, named, banned):
    """Whether any box the sweep found is confirmed to hold something the picture must not show."""
    sweep = sweep or {}
    geom = list(sweep.get('geometry') or [])
    try:
        n = int(sweep.get('n_confirmed') or 0)
    except Exception:
        n = 0
    if not n:
        n = len(geom)
    try:
        allow = int(sweep.get('allow') or 0)
    except Exception:
        allow = 0
    if n <= allow:
        return {'clean': 'yes', 'refused': False, 'boxes': n, 'hits': 0, 'unproven': 0,
                'verdict': 'the sweep put no rectangle on anything, so the premise holds'}
    named_reads = list((named or {}).get('answers') or [])
    banned_reads = list((banned or {}).get('answers') or [])
    hits, cleared, unproven, seen = [], 0, 0, []
    for i in range(n):
        v = _sg_txt(named_reads[i]) if i < len(named_reads) else ''
        b = _sg_txt(banned_reads[i]) if i < len(banned_reads) else ''
        got = bool(v) and not _sg_no(v)
        seen.append('%d=%s' % (i + 1, (v or '(no value came back)')[:70]))
        if _sg_yes(b) and got:
            hits.append(i + 1)
        elif _sg_no(b) or (v and not got):
            cleared += 1
        else:
            unproven += 1
    read_back = ' | '.join(seen)
    if len(hits) > allow:
        return {'clean': 'no', 'refused': False, 'boxes': n, 'hits': len(hits),
                'unproven': unproven, 'read_back': read_back,
                'verdict': 'rectangle %s was read back and confirmed to hold what the page is '
                           'not allowed to carry -- %s'
                           % (','.join(str(h) for h in hits), read_back)}
    if unproven:
        return {'clean': None, 'refused': True, 'boxes': n, 'hits': 0, 'unproven': unproven,
                'read_back': read_back,
                'verdict': '%d of %d rectangles could not be read back, so the accusation is '
                           'unproven -> abstain rather than zero the card -- %s'
                           % (unproven, n, read_back)}
    return {'clean': 'yes', 'refused': False, 'boxes': n, 'hits': 0, 'unproven': 0,
            'read_back': read_back,
            'verdict': 'every rectangle was read back and none of them holds what the page is '
                       'not allowed to carry -- %s' % read_back}


def sweepgate2(sw, named, banned, carrier):
    sw = sw or {}
    geom = list(sw.get('geometry') or [])
    try:
        n = int(sw.get('n_confirmed') or 0)
    except Exception:
        n = 0
    if not n:
        n = len(geom)
    try:
        allow = int(sw.get('allow') or 0)
    except Exception:
        allow = 0
    if n <= allow:
        return {'clean': 'yes', 'refused': False, 'boxes': n, 'hits': 0, 'unproven': 0,
                'corroborated': 0, 'uncorroborated': 0,
                'verdict': 'the sweep put no rectangle on anything, so the premise holds'}
    va = list((named or {}).get('answers') or [])
    ba = list((banned or {}).get('answers') or [])
    ca = list((carrier or {}).get('answers') or [])
    hits, unsettled, cleared, unproven, seen, why = [], [], 0, 0, [], []
    denied = 0
    for i in range(n):
        v = _sg_txt(va[i]) if i < len(va) else ''
        b = _sg_txt(ba[i]) if i < len(ba) else ''
        c = _sg_txt(ca[i]) if i < len(ca) else ''
        got = bool(v) and not _sg_no(v)
        seen.append('%d=%s' % (i + 1, (v or '(no value came back)')[:70]))
        if _sg_yes(b) and got:
            if _sg_yes(c):
                hits.append(i + 1)
                why.append('%d: both wordings say the page is not allowed to carry this' % (i + 1))
            elif _sg_no(c):
                cleared += 1
                denied += 1
                why.append('%d: the second wording says this belongs on the page, so the first '
                           'read stands uncorroborated and does not convict' % (i + 1))
            else:
                unsettled.append(i + 1)
                why.append('%d: the second wording did not come back, so the accusation is '
                           'neither stood up nor knocked down' % (i + 1))
        elif _sg_no(b) or (v and not got):
            cleared += 1
        else:
            unproven += 1
    read_back = ' | '.join(seen)
    note = '; '.join(why)
    if len(hits) > allow:
        return {'clean': 'no', 'refused': False, 'boxes': n, 'hits': len(hits),
                'unproven': unproven, 'corroborated': len(hits), 'unsettled': len(unsettled),
                'denied': denied, 'read_back': read_back, 'corroboration': note,
                'verdict': 'rectangle %s was read back and TWO independently worded reads BOTH '
                           'confirm it holds what the page is not allowed to carry -- %s'
                           % (','.join(str(h) for h in hits), read_back)}
    if unproven or len(hits) + len(unsettled) > allow:
        return {'clean': None, 'refused': True, 'boxes': n, 'hits': 0,
                'unproven': unproven + len(unsettled), 'corroborated': len(hits),
                'unsettled': len(unsettled),
                'denied': denied, 'read_back': read_back, 'corroboration': note,
                'verdict': '%d of %d rectangles were left unproven -- either nothing came back, '
                           'or one wording accused it and the other never answered -- so the '
                           'card abstains rather than being zeroed -- %s'
                           % (unproven + len(unsettled), n, read_back)}
    return {'clean': 'yes', 'refused': False, 'boxes': n, 'hits': 0, 'unproven': 0,
            'corroborated': len(hits), 'unsettled': len(unsettled), 'denied': denied,
            'read_back': read_back, 'corroboration': note,
            'verdict': 'no rectangle was stood up by both wordings, so nothing on the page is '
                       'shown to be what it is not allowed to carry -- %s' % read_back}

# end of code_sweepgate
