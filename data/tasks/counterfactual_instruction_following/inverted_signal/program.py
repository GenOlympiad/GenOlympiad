# shared code: code_b1eb8a3453b8
def lamp_colour_matches(answer, expected):
    """Score 1 if the lamp reads the expected colour and not its opposite."""
    if answer is None: return 0.0
    a = str(answer).strip().lower()
    want = str(expected).strip().lower()
    synonyms = {'green':['green'], 'red':['red'], 'amber':['amber','yellow']}
    hit = any(w in a for w in synonyms.get(want, [want]))
    others = {'green':'red','red':'green'}
    bad = others.get(want)
    if bad and bad in a and bad != want: return 0.0
    return 1.0 if hit else 0.0

def _st(ans):
    if ans is None: return None
    a = str(ans).strip().lower()
    if 'unlit' in a or 'not lit' in a or 'dark' in a or 'dull' in a or 'off' in a: return 0
    if 'lit' in a or 'glow' in a or 'bright' in a or a.startswith('on'): return 1
    return None

def lit_lamp_matches(top_read, middle_read, bottom_read, expected):
    """Score 1 if exactly one lamp is lit and it is in the expected position."""
    vals = {'top': _st(top_read), 'middle': _st(middle_read), 'bottom': _st(bottom_read)}
    if any(v is None for v in vals.values()): return 0.0
    on = [k for k, v in vals.items() if v == 1]
    if len(on) != 1: return 0.0
    return 1.0 if on[0] == str(expected).strip().lower() else 0.0

def headcount(*vals):
    out = 1.0
    for v in vals:
        try: out *= float(v)
        except (TypeError, ValueError): out *= 0.0
    return round(out, 4)

# end of code_b1eb8a3453b8
