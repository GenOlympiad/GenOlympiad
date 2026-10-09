# shared code: code_joinw
def join_rows(key_reads, value_reads, nmin):
    """Pair each row's town name with its read value, sorted, if at least nmin rows pair up."""
    keys = [''.join(c for c in str(a).lower() if c.isalpha())
          for a in ((key_reads or {}).get('answers') or [])]
    values = [''.join(c for c in str(a).lower() if c.isalnum() or c == '.')
          for a in ((value_reads or {}).get('answers') or [])]
    n = min(len(keys), len(values))
    out = [keys[i] + '=' + values[i] for i in range(n) if keys[i] and values[i]]
    if len(out) < nmin:
        return {'seq': 'none', 'unreadable': True, 'refused': True,
                'verdict': 'only %d rows could be joined to a printed name' % len(out)}
    out = sorted(out)
    return {'seq': '|'.join(out), 'verdict': 'the board reads ' + '|'.join(out)}

# end of code_joinw

# shared code: code_geoband
def towns_off_band(town_reads, latitude_reads):
    """Count towns whose geomagnetic latitude is over four degrees from the expected figure."""
    import re
    EXPECTED = {'tromso': 67.0, 'churchill': 69.0, 'yakutsk': 51.0, 'moscow': 51.0}
    BAND = 4.0
    towns = [''.join(c for c in str(a).lower() if c.isalpha())
          for a in ((town_reads or {}).get('answers') or [])]
    latitudes = []
    for a in ((latitude_reads or {}).get('answers') or []):
        m = re.search(r'-?\d+(?:\.\d+)?', str(a))
        latitudes.append(float(m.group(0)) if m else None)
    n = min(len(towns), len(latitudes))
    pairs = [(towns[i], latitudes[i]) for i in range(n) if towns[i] and latitudes[i] is not None]
    if len(pairs) < 4:
        return {'token': 'none', 'unreadable': True, 'refused': True,
                'verdict': 'only %d rows carried a town and a figure' % len(pairs)}
    off_band = [t for t, v in pairs if t not in EXPECTED or abs(v - EXPECTED[t]) > BAND]
    return {'token': 'allwithin' if not off_band else 'off%d' % len(off_band),
            'verdict': '%d of %d towns are outside the four-degree band'
                       % (len(off_band), len(pairs))}

# end of code_geoband

# shared code: code_selfagree
def marks_match_figures(latitude_reads, mark_reads, cutoff):
    """Count rows whose tick or cross contradicts its own latitude against the cutoff."""
    import re
    latitudes = []
    for a in ((latitude_reads or {}).get('answers') or []):
        m = re.search(r'-?\d+(?:\.\d+)?', str(a))
        latitudes.append(float(m.group(0)) if m else None)
    marks = [''.join(c for c in str(a).lower() if c.isalpha())
          for a in ((mark_reads or {}).get('answers') or [])]
    n = min(len(latitudes), len(marks))
    pairs = [(latitudes[i], marks[i]) for i in range(n) if latitudes[i] is not None and marks[i]]
    if len(pairs) < 4:
        return {'token': 'none', 'unreadable': True, 'refused': True,
                'verdict': 'only %d rows carried both a figure and a mark' % len(pairs)}
    bad = [g for g, k in pairs if (g >= cutoff) != (k == 'tick')]
    return {'token': 'agree' if not bad else 'contradict%d' % len(bad),
            'verdict': '%d of %d rows contradict their own printed figure'
                       % (len(bad), len(pairs))}

# end of code_selfagree
