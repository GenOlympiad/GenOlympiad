# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# shared code: code_key_pair_frac
def crack_direction_scores(keys, vals, marks, record_box, want):
    """Score each zone on whether its cracks, read as a clock hour, point back to the strike."""
    import math
    wanted = dict(p.split('=') for p in str(want).split('|') if p.count('=') == 1)
    zone_keys = [str(a).strip().upper().replace(' ', '')
          for a in ((keys or {}).get('answers') or [])]
    hour_answers = [str(a) for a in ((vals or {}).get('answers') or [])]
    def boxes_of(n):
        g = (n or {}).get('geometry') if isinstance(n, dict) else None
        return [b for b in (g or []) if isinstance(b, (list, tuple)) and len(b) >= 4]
    def centre(b):
        return ((float(b[0]) + float(b[2])) / 2.0, (float(b[1]) + float(b[3])) / 2.0)
    def hour(v):
        d = ''.join(c for c in str(v) if c.isdigit())
        try:
            h = int(d)
        except (TypeError, ValueError):
            return None
        return h if 1 <= h <= 12 else None
    marker_boxes, record_boxes = boxes_of(marks), boxes_of(record_box)
    record_centre = centre(record_boxes[0]) if record_boxes else None
    zone_scores, notes = {}, []
    for i, (k, v) in enumerate(zip(zone_keys, hour_answers)):
        h = hour(v)
        if record_centre is None or i >= len(marker_boxes) or h is None:
            zone_scores[k] = 0.0
            notes.append('zone %s: the card, the marker box or the hour was not read'
                       % (k or '?'))
            continue
        marker_centre = centre(marker_boxes[i])
        dx, dy = record_centre[0] - marker_centre[0], record_centre[1] - marker_centre[1]
        span = max(abs(float(marker_boxes[i][2]) - float(marker_boxes[i][0])),
                   abs(float(marker_boxes[i][3]) - float(marker_boxes[i][1])))
        if (dx * dx + dy * dy) ** 0.5 < 0.75 * span:
            zone_scores[k] = 1.0
            notes.append('zone %s sits against the card itself, so its cracks run back to it '
                       'wherever they point' % k)
            continue
        want_deg = math.degrees(math.atan2(dx, -dy)) % 360.0
        got_deg = (h % 12) * 30.0
        d = abs((got_deg - want_deg + 180.0) % 360.0 - 180.0)
        zone_scores[k] = 1.0 if d <= 45.0 else (0.5 if d <= 75.0 else 0.0)
        notes.append('zone %s: the card lies toward %.0f degrees on the page and the cracks '
                   'run back toward %.0f, %.0f apart' % (k, want_deg, got_deg, d))
    zones = sorted(wanted)
    return {'a': zone_scores.get(zones[0], 0.0) if zones else 0.0,
            'b': zone_scores.get(zones[1], 0.0) if len(zones) > 1 else 0.0,
            'c': zone_scores.get(zones[2], 0.0) if len(zones) > 2 else 0.0,
            'verdict': '; '.join(notes)}

# end of code_key_pair_frac

# shared code: code_rank_run
def crack_scale_ranks(keys, vals, want, scale):
    """Rank each zone's read crack pattern on the scale, in the pinned zone order."""
    scale_words = [x.strip().lower() for x in str(scale).split('|')]
    zone_order = [x.strip().upper() for x in str(want).split('|')]
    zone_keys = [str(a).strip().upper().replace(' ', '') for a in ((keys or {}).get('answers') or [])]
    value_answers = [str(a).strip().lower() for a in ((vals or {}).get('answers') or [])]
    reads_by_zone = dict(zip(zone_keys, value_answers))
    ranks = []
    for k in zone_order:
        s = reads_by_zone.get(k, '')
        ranks.append(next((float(i) for i, w in enumerate(scale_words) if w and w in s), None))
    return {'seq': ranks if (ranks and all(x is not None for x in ranks)) else [], 'verdict': 'the ringed items read %s along the pinned run' % ranks}

# end of code_rank_run
