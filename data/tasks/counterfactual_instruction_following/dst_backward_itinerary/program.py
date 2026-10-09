# shared code: code_dst
def clock(node):
    import re
    got = (node or {}).get('answers') if isinstance(node, dict) else None
    s = str((got or [''])[0]).strip().lower()
    if any(w in s for w in ('none', 'blank', 'nil', 'empty', 'unknown', 'n a', 'not ')):
        return ''
    m = re.search(r'(\d{1,2})\s*[:.h]\s*([0-5]\d)', s) or re.search(r'\b(\d{2})([0-5]\d)\b', s)
    return '%02d:%02d' % (int(m.group(1)) % 24, int(m.group(2))) if m else ''


def hours_local_ahead(a, b):
    """How many whole hours the local column stands ahead of the UTC column."""
    x, y = clock(a), clock(b)
    if not x or not y:
        return {'h': -1, 'verdict': 'a clock figure could not be read'}
    d = (int(x[:2]) * 60 + int(x[3:]) - int(y[:2]) * 60 - int(y[3:])) % 1440
    return {'h': d // 60, 'verdict': 'the local column stands %d hour(s) ahead of the utc column' % (d // 60)}


def flightno(node):
    import re
    got = (node or {}).get('answers') if isinstance(node, dict) else None
    return re.sub(r'[^A-Za-z0-9]', '', str((got or [''])[0])).upper()


def pass_matches_row(row_time, pass_time, pass_flight, key):
    """Check the boarding pass time equals the display row time and both match the reference."""
    a, b, f = clock(row_time), clock(pass_time), flightno(pass_flight)
    ok = bool(a) and a == b and (b.replace(':', '') + '|' + f) == str(key)
    return {'s': 'yes' if ok else 'no', 'verdict': 'the row reads %s, the pass reads %s for %s' % (a or 'nothing', b or 'nothing', f or 'nothing')}


def both_columns_read(a, b):
    """Whether both the local and UTC clock figures could be read."""
    x, y = clock(a), clock(b)
    return {'v': 'yes' if (x and y) else 'no',
            'verdict': 'the two columns read %s and %s' % (x or 'nothing', y or 'nothing')}


def read_local_time(node):
    """The time read in the local column as HH:MM."""
    v = clock(node)
    return {'s': v or 'none', 'verdict': 'the local column reads %s' % (v or 'nothing')}

# end of code_dst
