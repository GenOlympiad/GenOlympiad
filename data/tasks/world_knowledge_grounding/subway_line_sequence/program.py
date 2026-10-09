# code: stations_code

def read_stations(stop_boxes, stop_confirms, stop_names):
    """The names beside the confirmed stops, left to right."""
    def centre_x(b):
        return (float(b[1]) + float(b[3])) / 2.0

    def yes(a):
        return str(a).strip().lower().startswith('y')

    geometry = (stop_boxes or {}).get('geometry') or []
    confirms = (stop_confirms or {}).get('answers') or []
    names_read = (stop_names or {}).get('answers') or []
    stops = []
    for i in range(min(len(geometry), len(confirms))):
        if not yes(confirms[i]):
            continue
        name = str(names_read[i]).strip() if i < len(names_read) and names_read[i] is not None else ''
        stops.append({'box': geometry[i], 'name': name})
    stops.sort(key=lambda s: centre_x(s['box']))
    names = [s['name'] for s in stops if s['name']]
    return {'n': len(names), 'names': names, 'text': ', '.join(names),
            'verdict': '%d stops were framed and individually confirmed; from left to right the '
                       'names printed beside them read %s'
                       % (len(names), ', '.join(names) or 'nothing')}

# end of stations_code

# code: station_seq_exact_code
def stations_in_order(read, target):
    """The share of reference stations read in the same position, capped at 0.25 unless all match."""
    import re
    def toks(s):
        s = re.sub(r"[^a-z0-9]+", " ", str(s).lower())
        return set(w for w in s.split() if w)
    def split_stations(x):
        if x is None: return []
        if isinstance(x, (list, tuple)):
            parts = [str(t) for t in x]
        else:
            parts = re.split(r"[,;\n]+", str(x))
        return [p.strip() for p in parts if p and p.strip()]
    target_words = [toks(s) for s in split_stations(target)]
    got = [toks(s) for s in split_stations(read)]
    if not target_words: return 0.0
    ok = 0
    for i, target_set in enumerate(target_words):
        if i < len(got) and target_set:
            inter = len(got[i] & target_set)
            if inter >= max(1, (len(target_set) + 1) // 2) and got[i]:
                if inter / len(got[i]) >= 0.5:
                    ok += 1
    frac = round(ok / len(target_words), 4)
    if ok < len(target_words): frac = min(frac, 0.25)
    return frac

# end of station_seq_exact_code

# code: count_stations_code
def count_stations(read):
    """The number of station names in the read list, or None."""
    import re
    if read is None or isinstance(read, dict): return None
    s = str(read).strip()
    if not s or 'unreadable' in s.lower(): return None
    parts = [p.strip() for p in re.split(r"[,;\n]+", s) if p and p.strip()]
    return len(parts) if parts else None

# end of count_stations_code
