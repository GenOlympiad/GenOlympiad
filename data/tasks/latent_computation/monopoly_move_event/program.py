# code: square_code

def _ans(node, i=0):
    if isinstance(node, dict):
        a = node.get('answers') or []
        return a[i] if i < len(a) else None
    return node


def _boxes(node):
    if isinstance(node, dict):
        g = node.get('geometry')
        return list(g) if g else []
    return list(node or [])


def _cx(b):
    return (float(b[1]) + float(b[3])) / 2.0


def _cy(b):
    return (float(b[0]) + float(b[2])) / 2.0


def landing_square(square_read):
    """The square number read from the answer, if any."""
    import re
    s = str(_ans(square_read) or '')
    m = re.search(r'\d{1,2}', s)
    return {'n': int(m.group(0)) if m else None, 'said': s.strip()[:60],
            'no_read': m is None}

# end of square_code

# code: exactly_one_code

def _ans(node, i=0):
    if isinstance(node, dict):
        a = node.get('answers') or []
        return a[i] if i < len(a) else None
    return node


def _boxes(node):
    if isinstance(node, dict):
        g = node.get('geometry')
        return list(g) if g else []
    return list(node or [])


def _cx(b):
    return (float(b[1]) + float(b[3])) / 2.0


def _cy(b):
    return (float(b[0]) + float(b[2])) / 2.0


def one_token_framed(token_boxes):
    """Yes if exactly one token was boxed and confirmed on the board."""
    n = len(_boxes(token_boxes))
    return {'s': 'yes' if n == 1 else 'no', 'n': n,
            'verdict': '%d token(s) were framed and confirmed on the board' % n}

# end of exactly_one_code
