# code: headcount_code
SYN = {
  'blue': ['blue', 'navy', 'royal blue', 'cobalt', 'azure', 'sky blue', 'light blue'],
  'white': ['white', 'off-white', 'off white', 'ivory', 'cream', 'pale grey', 'pale gray'],
}


def m(ans, key):
    if ans is None:
        return 0.0
    a = str(ans).strip().lower()
    vivid = ['red', 'orange', 'yellow', 'green', 'purple', 'brown', 'magenta', 'pink']
    if any(v in a for v in vivid):
        return 0.0
    words = SYN.get(str(key).lower(), [str(key).lower()])
    return 1.0 if any(w in a for w in words) else 0.0


NAME_SYN = {
  'hydrant': ['hydrant'],
  'postbox': ['postbox', 'post box', 'post-box', 'mailbox', 'mail box', 'letterbox',
              'letter box', 'pillar box'],
  'aubergine': ['aubergine', 'eggplant', 'brinjal'],
  'corn': ['corn', 'maize', 'cob'],
  'ladybird': ['ladybird', 'ladybug', 'lady bug', 'lady beetle'],
  'pepper': ['chilli', 'chili', 'chile', 'pepper'],
  'cone': ['cone'],
  'leaf': ['leaf', 'leaves'],
  'bus': ['bus', 'coach'],
  'extinguisher': ['extinguisher'],
  'sunflower': ['sunflower', 'flower'],
  'sign': ['stop sign', 'sign'],
  'basketball': ['basketball', 'ball'],
}
_DROP = ('a ', 'an ', 'the ')


def _norm(s):
    t = str(s or '').strip().lower()
    for d in _DROP:
        if t.startswith(d):
            t = t[len(d):]
    return ' '.join(w for w in t.replace('-', ' ').split() if w not in ('of',))


def _keys(name):
    n = _norm(name)
    head = n.split()[-1] if n.split() else n
    ks = [n] + list(NAME_SYN.get(head, [head]))
    return [k for k in ks if k]


def _match(answer, name):
    a = _norm(answer)
    if not a:
        return False
    for k in _keys(name):
        if k in a or (len(a.split()) <= 3 and a.split()[-1] == k):
            return True
    return False


def score_two_colour_objects(name_reads, colour_reads, objects, expects, n_demanded):
    """Full credit only if every demanded object is found and painted its demanded colour."""
    ids = (name_reads or {}).get('answers') or []
    cols = (colour_reads or {}).get('answers') or []
    n_items = min(len(ids), len(cols))
    objects = list(objects or [])
    expects = list(expects or [])
    try:
        n_demanded = int(n_demanded)
    except (TypeError, ValueError):
        n_demanded = -1
    if n_items == 0:
        return {'frac': 0.0, 'n_items': 0, 'n_ok': 0, 'n_want': n_demanded, 'unnamed': [],
                'verdict': 'no object box survived the acceptance gate -> frac 0.0'}
    if n_items != n_demanded or len(objects) != n_demanded or len(expects) != n_demanded:
        return {'frac': 0.0, 'n_items': n_items, 'n_ok': 0, 'n_want': n_demanded, 'unnamed': [],
                'verdict': ('the count found %d confirmed object(s), the prompt demanded %d '
                            '-> frac 0.0' % (n_items, n_demanded))}
    order = sorted(range(n_demanded), key=lambda i: -len(_norm(objects[i]).split()))
    used, pair, unnamed = set(), {}, []
    for i in order:
        hit = None
        for j in range(n_items):
            if j in used:
                continue
            if _match(ids[j], objects[i]):
                hit = j
                break
        if hit is None:
            unnamed.append(_norm(objects[i]))
        else:
            used.add(hit)
            pair[i] = hit
    if unnamed:
        return {'frac': 0.0, 'n_items': n_items, 'n_ok': 0, 'n_want': n_demanded,
                'unnamed': unnamed, 'read_as': [str(x) for x in ids],
                'verdict': ('demanded object(s) %s were not found among the %d objects drawn '
                            '(read as %s) -> frac 0.0'
                            % (', '.join(unnamed), n_items, '; '.join(str(x) for x in ids)))}
    hits = [(objects[i], expects[i], cols[pair[i]], m(cols[pair[i]], expects[i]))
            for i in range(n_demanded)]
    n_ok = int(sum(1 for h in hits if h[3] >= 1.0))
    frac = 1.0 if n_ok == n_items else 0.0
    bad = ['%s drawn %s (demanded %s)' % (_norm(h[0]), h[2], h[1]) for h in hits if h[3] < 1.0]
    return {'frac': frac, 'n_items': n_items, 'n_ok': n_ok, 'n_want': n_demanded, 'unnamed': [],
            'verdict': ('%d of %d objects carry their demanded palette colour -> frac %.1f%s'
                        % (n_ok, n_items, frac,
                           ('; off-palette: ' + ', '.join(bad)) if bad else ''))}

# end of headcount_code
