# code: helpers
from genolympiad.task_helpers import frac_of
# end of helpers

# code: count_candles_code

def count_confirmed_candles(candle_boxes, candle_confirms):
    """Count the framed candidates confirmed to hold exactly one whole candlestick."""
    def yes(a):
        return str(a).strip().lower().startswith('y')
    geometry = (candle_boxes or {}).get('geometry') or []
    answers = (candle_confirms or {}).get('answers') or []
    n = sum(1 for i in range(min(len(geometry), len(answers))) if yes(answers[i]))
    return {'n': n, 'asked': len(answers),
            'verdict': '%d of %d framed candidates were confirmed to hold exactly one whole '
                       'candlestick' % (n, len(answers))}

# end of count_candles_code

# code: candles_code

def read_candles(candle_boxes, candle_confirms, colour, above, below):
    """The colour and the wick above and below of each confirmed candlestick, left to right."""
    def centre_x(b):
        return (float(b[1]) + float(b[3])) / 2.0

    def yes(a):
        return str(a).strip().lower().startswith('y')

    geometry = (candle_boxes or {}).get('geometry') or []
    confirms = (candle_confirms or {}).get('answers') or []
    colours = (colour or {}).get('answers') or []
    above_answers = (above or {}).get('answers') or []
    below_answers = (below or {}).get('answers') or []
    items = []
    for i in range(min(len(geometry), len(confirms))):
        if not yes(confirms[i]):
            continue
        items.append({'box': geometry[i],
                      'colour': colours[i] if i < len(colours) else None,
                      'above': above_answers[i] if i < len(above_answers) else None,
                      'below': below_answers[i] if i < len(below_answers) else None})
    items.sort(key=lambda c: centre_x(c['box']))

    def say(key):
        return ', '.join(str(c[key]) for c in items) or 'nothing'

    return {'n': len(items),
            'signs': [c['colour'] for c in items],
            'above': [c['above'] for c in items],
            'below': [c['below'] for c in items],
            'verdict': '%d candlesticks were framed and individually confirmed; left to right '
                       'their rectangles read %s, the thin line goes above the top edge %s, and '
                       'below the bottom edge %s'
                       % (len(items), say('colour'), say('above'), say('below'))}

# end of candles_code

# code: contains_code
def wicks_on_both_sides(above, below):
    """Whether every candlestick's thin line goes both above and below its body."""
    def yes_no(t):
        s = str(t).strip().lower()
        if s.startswith('y') or s.startswith('true'):
            return True
        if s.startswith('n') or s.startswith('false'):
            return False
        return None

    above_flags = [yes_no(t) for t in (above if isinstance(above, (list, tuple)) else [])]
    below_flags = [yes_no(t) for t in (below if isinstance(below, (list, tuple)) else [])]
    n = min(len(above_flags), len(below_flags))
    if n == 0 or any(x is None for x in above_flags[:n]) or any(x is None for x in below_flags[:n]):
        return {'frac': 0.0, 'no_read': True, 'above': above_flags, 'below': below_flags}
    per = [1 if (above_flags[i] and below_flags[i]) else 0 for i in range(n)]
    return {'frac': 1.0 if all(per) else 0.0, 'no_read': False, 'per_candle': per,
            'above': above_flags[:n], 'below': below_flags[:n]}

# end of contains_code

# code: frac_code
def direction_share(seq, wanted):
    """The share of candlesticks whose up or down direction matches the reference sequence."""
    def norm(t):
        s = str(t).strip().lower()
        if s.startswith('u') or 'green' in s: return 'up'
        if s.startswith('d') or 'red' in s: return 'down'
        return s
    directions = [norm(t) for t in seq]
    if len(directions) != len(wanted):
        return 0.0
    return sum(1 for a, b in zip(directions, wanted) if a == b) / len(wanted)
# end of frac_code
