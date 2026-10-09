# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# shared code: code_lux
def check_lux_readings(keys, vals):
    """Match if the near meter reads 800 lux and the far one a fifth to three tenths of it."""
    distances = [''.join(c for c in str(k) if c.isdigit() or c == '.')
          for k in (keys or {}).get('answers') or []]
    values = [''.join(c for c in str(v) if c.isdigit())
          for v in (vals or {}).get('answers') or []]
    by_distance = {distances[i]: values[i] for i in range(min(len(distances), len(values)))}
    a, b = by_distance.get('1.0', ''), by_distance.get('2.0', '')
    ok = (a.isdigit() and b.isdigit() and int(a) == 800
          and 0.20 <= int(b) / 800.0 <= 0.30)
    return {'state': 'match' if ok else 'off', 'n': len(by_distance),
            'verdict': 'near reads %s, far reads %s'
                       % (a or 'nothing', b or 'nothing')}

# end of code_lux

# shared code: code_cards
def check_target_tones(keys, tone):
    """Match if the near target reads light and the far target reads dark."""
    distances = [''.join(c for c in str(k) if c.isdigit() or c == '.')
          for k in (keys or {}).get('answers') or []]
    tones = [str(t).strip().lower()[:1] for t in (tone or {}).get('answers') or []]
    by_distance = {distances[i]: tones[i] for i in range(min(len(distances), len(tones)))}
    ok = len(by_distance) == 2 and by_distance.get('1.0') == 'l' and by_distance.get('2.0') == 'd'
    return {'state': 'match' if ok else 'off', 'n': len(by_distance),
            'verdict': 'near card %s, far card %s'
                       % (by_distance.get('1.0', 'unread'), by_distance.get('2.0', 'unread'))}

# end of code_cards
