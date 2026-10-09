# shared code: code_joinw
def join_rows(name_reads, value_reads, min_rows):
    """Join each printed name to the value read beside it, sorted, refusing below a minimum."""
    names = [''.join(c for c in str(a).lower() if c.isalpha())
          for a in ((name_reads or {}).get('answers') or [])]
    values = [''.join(c for c in str(a).lower() if c.isalnum() or c == '.')
          for a in ((value_reads or {}).get('answers') or [])]
    n = min(len(names), len(values))
    out = [names[i] + '=' + values[i] for i in range(n) if names[i] and values[i]]
    if len(out) < min_rows:
        return {'seq': 'none', 'unreadable': True, 'refused': True,
                'verdict': 'only %d rows could be joined to a printed name' % len(out)}
    out = sorted(out)
    return {'seq': '|'.join(out), 'verdict': 'the board reads ' + '|'.join(out)}

# end of code_joinw

# shared code: code_gaugeagree
def gauge_matches_road(gauge_reads, road_reads, home_gauge):
    """Whether each wagon stands on the pit road exactly when its chalked gauge is foreign."""
    import re
    gauges = []
    for a in ((gauge_reads or {}).get('answers') or []):
        m = re.search(r'\d+', str(a))
        gauges.append(int(m.group(0)) if m else None)
    roads = [''.join(c for c in str(a).lower() if c.isalpha())
          for a in ((road_reads or {}).get('answers') or [])]
    n = min(len(gauges), len(roads))
    pairs = [(gauges[i], roads[i]) for i in range(n) if gauges[i] is not None and roads[i]]
    if len(pairs) < 4:
        return {'token': 'none', 'unreadable': True, 'refused': True,
                'verdict': 'only %d wagons carried both a figure and a road' % len(pairs)}
    bad = [g for g, r in pairs if (g != home_gauge) != (r == 'pit')]
    return {'token': 'agree' if not bad else 'contradict%d' % len(bad),
            'verdict': '%d of %d wagons stand on the wrong road for their own chalk'
                       % (len(bad), len(pairs))}

# end of code_gaugeagree

# shared code: code_wordset
def wordset(reads):
    """The distinct words copied out of the cut-outs, sorted and joined."""
    out = []
    for a in ((reads or {}).get('answers') or []):
        t = ''.join(c for c in str(a).lower() if c.isalnum())
        if t:
            out.append(t)
    if not out:
        return {'seq': 'none', 'unreadable': True, 'refused': True,
                'verdict': 'nothing could be copied out of the cut-outs'}
    out = sorted(set(out))
    return {'seq': '|'.join(out), 'verdict': 'the cut-outs read ' + '|'.join(out)}

# end of code_wordset
