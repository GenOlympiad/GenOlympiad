# shared code: code_d24cf05d934e
import re
def first_figure(node):
    """The first number in the read, or unreadable."""
    ans = (node or {}).get('answers') or []
    raw = ans[0] if ans else None
    s = str(raw if raw is not None else '').replace(',', '')
    m = re.findall(r'-?\d+(?:\.\d+)?', s)
    return {'v': float(m[0]) if m else None, 'raw': raw, 'unreadable': not m}

# end of code_d24cf05d934e

# code: parse_code
import datetime
def gauge_reading_at_time(record):
    """The gauge stage and discharge nearest the pinned time, from the live water service record."""
    out = {'stage_ft': None, 'discharge_cfs': None}
    target_time = datetime.datetime.fromisoformat('2026-07-16T17:30+00:00')
    series_list = ((record or {}).get('value') or {}).get('timeSeries') or []
    def series(code):
        for s in series_list:
            if s['variable']['variableCode'][0]['value'] == code:
                return s['values'][0]['value']
        return []
    def nearest(vals):
        good = [v for v in vals if v.get('value') not in (None, '', '-999999')]
        if not good: return None
        return min(good, key=lambda v: abs(datetime.datetime.fromisoformat(v['dateTime']).astimezone(datetime.timezone.utc) - target_time.replace(tzinfo=datetime.timezone.utc)))
    stage = nearest(series('00065')); discharge = nearest(series('00060'))
    out['stage_ft'] = round(float(stage['value']), 2) if stage else None
    out['discharge_cfs'] = float(discharge['value']) if discharge else None
    return out
# end of parse_code

# code: cat_code
def flood_category(stage, thresholds):
    """The flood category the stage reaches, from the thresholds."""
    if stage is None or not thresholds: return None
    stage_ft = float(stage)
    order = [('major', thresholds.get('major')), ('moderate', thresholds.get('moderate')),
             ('minor', thresholds.get('minor')), ('action', thresholds.get('action'))]
    for name, c in order:
        threshold = (c or {}).get('stage')
        if threshold is not None and threshold > 0 and stage_ft >= threshold:
            return name
    return 'no_flooding'
# end of cat_code

# code: same_node_code
def pass_through(node):
    """The read, unchanged."""
    return node

# end of same_node_code

# code: flood_rank_code
import re
_FLOOD_RANK = {'no-flooding': 0, 'no flooding': 0, 'none': 0, 'normal': 0, 'no': 0,
               'action': 1, 'minor': 2, 'minor flood': 2, 'moderate': 3,
               'moderate flood': 3, 'major': 4, 'major flood': 4}


def flood_rank(node):
    """The rank of the flood category word read (0 none to 4 major), or unreadable."""
    ans = (node or {}).get('answers') or []
    raw = ans[0] if ans else None
    if raw is None:
        return {'rank': None, 'raw': raw, 'unreadable': True}
    key = str(raw).strip().lower().replace('_', '-')
    r = _FLOOD_RANK.get(key)
    if r is None and key.split():
        r = _FLOOD_RANK.get(key.split()[0])
    if r is None:
        m = re.search(r'(no[- ]?flooding|minor flood|moderate flood|major flood|'
                      r'action|minor|moderate|major)', key)
        if m:
            r = _FLOOD_RANK.get(m.group(1).replace(' ', '-'), _FLOOD_RANK.get(m.group(1)))
    return {'rank': r, 'raw': raw, 'unreadable': r is None}

# end of flood_rank_code
