# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# code: zone_err_code
def worst_zone_error(keys, zones, reference_map):
    """The largest zone distance between each lantern's read zone and its reference zone."""
    order = 'ABCD'
    zone_map = dict(p.split('=') for p in str(reference_map).split(',') if p.count('=') == 1)
    lantern_keys = [''.join(c for c in str(a) if c.isdigit()) for a in ((keys or {}).get('answers') or [])]
    zone_reads = [str(a).strip().upper()[:1] for a in ((zones or {}).get('answers') or [])]
    errors = [9.0] * (len(zone_map) - min(len(lantern_keys), len(zone_reads)))
    for k, s in zip(lantern_keys, zone_reads):
        t = zone_map.get(k)
        ok = s in order and t in order
        errors.append(abs(order.index(s) - order.index(t)) if ok else 9.0)
    worst = max(errors or [9.0])
    return {'err': worst, 'verdict': 'the worst pool lands %.0f zones away from the zone its own plot line gives it' % worst}

# end of zone_err_code

# code: tilt_token_code
def tilt_token(keys, turns):
    """Join each lantern number with its read tilt into one sorted text token."""
    lantern_keys = [''.join(c for c in str(a) if c.isdigit()) for a in ((keys or {}).get('answers') or [])]
    tilt_reads = [str(a).strip().lower() for a in ((turns or {}).get('answers') or [])]
    n = min(len(lantern_keys), len(tilt_reads))
    parts = ['%s:%s' % (lantern_keys[i], tilt_reads[i][:5] or 'x') for i in range(n) if lantern_keys[i]]
    parts.sort()
    token = '|'.join(parts) if parts else 'NOTHING-READ'
    return {'tok': token, 'seen': len(parts),
            'verdict': 'assembled %d lanterns as %s' % (len(parts), token)}

# end of tilt_token_code
