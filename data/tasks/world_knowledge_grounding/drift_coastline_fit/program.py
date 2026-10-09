# code: notch_letter_code

def _cy(b):
    return (float(b[0]) + float(b[2])) / 2.0


def _cx(b):
    return (float(b[1]) + float(b[3])) / 2.0


def _h(b):
    return abs(float(b[2]) - float(b[0]))


def _w(b):
    return abs(float(b[3]) - float(b[1]))


def _yes(a):
    return str(a).strip().lower().startswith('y')


def _kept(bx, cf):
    geo = (bx or {}).get('geometry') or []
    ok = (cf or {}).get('answers') or []
    return [i for i in range(min(len(geo), len(ok))) if _yes(ok[i])]


def notch_letter(spot_boxes, spot_confirms, letter_reads, shape_reads, reference):
    """The letter of the one confirmed coast spot that curves away from the seam."""
    kept = _kept(spot_boxes, spot_confirms)
    letters = (letter_reads or {}).get('answers') or []
    shapes = (shape_reads or {}).get('answers') or []
    seen = []
    for i in kept:
        import re
        letter_chars = re.findall(r'[A-Za-z]', str(letters[i] if i < len(letters) else ''))
        s = str(shapes[i] if i < len(shapes) else '').strip().lower()
        away = ('away' in s) or ('notch' in s) or ('bay' in s) or ('inward' in s)
        out = ('out' in s) or ('bulge' in s) or ('toward' in s)
        seen.append({'letter': (letter_chars[-1].upper() if letter_chars else ''),
                     'shape': 'away' if (away and not out) else ('out' if out else '')})
    hits = [s['letter'] for s in seen if s['shape'] == 'away' and s['letter']]
    return {'letter': hits[0] if len(hits) == 1 else '',
            'n': len(seen), 'spots': seen,
            'verdict': '%d marked spots confirmed by the ring; they read %s, so the single spot '
                       'where the coast curves away from the seam is %s'
                       % (len(seen), [(s['letter'] or '?') + ':' + (s['shape'] or '?')
                                      for s in seen], hits[0] if len(hits) == 1 else 'not unique')}

# end of notch_letter_code
