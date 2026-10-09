# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts, count_listed_items
# end of helpers

# code: lee_gap_code
def lee_aspect_gap(count_read, aspect_read, want_n, want_deg):
    """Degrees from the loaded aspect to the toned fan middle, 180 if the sector count is wrong."""
    bearings = {'n': 0.0, 'ne': 45.0, 'e': 90.0, 'se': 135.0,
         's': 180.0, 'sw': 225.0, 'w': 270.0, 'nw': 315.0}
    count = ''.join(x for x in str((((count_read or {}).get('answers') or ['0'])[0])) if x.isdigit())
    aspect = str((((aspect_read or {}).get('answers') or ['none'])[0])).strip().lower().replace(' ', '')
    want_count = ''.join(x for x in str(want_n) if x.isdigit())
    want_bearing = ''.join(x for x in str(want_deg) if x.isdigit())
    gap = 180.0 if count != (want_count or 'x') or aspect not in bearings or not want_bearing else abs((bearings[aspect] - float(want_bearing) + 180.0) % 360.0 - 180.0)
    return {'gap': gap, 'sectors': count, 'aspect': aspect, 'verdict': 'tone covers %s sectors and the middle of the toned fan reads %s, %.0f degrees from the loaded aspect' % (count or 'no', aspect or 'nothing', gap)}

# end of lee_gap_code

# code: band_stop_code
def band_stops_inside(band_count_read, outer_read, want_n):
    """Whether the tone covers the expected number of bands and the outermost band is clear."""
    count = ''.join(x for x in str((((band_count_read or {}).get('answers') or ['0'])[0])) if x.isdigit())
    outer = str((((outer_read or {}).get('answers') or ['no'])[0])).strip().lower()
    want_count = ''.join(x for x in str(want_n) if x.isdigit())
    ok = 'yes' if count == (want_count or 'x') and outer.startswith('y') else 'no'
    return {'ok': ok, 'rings': count, 'outer_clear': outer, 'verdict': 'tone reaches %s of the 3 rings and the outermost ring is clear: %s' % (count or 'none', outer or 'unknown')}

# end of band_stop_code
