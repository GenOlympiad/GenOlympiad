# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# code: law_code
def arrival_layover_total_match(arr, lay, total, want_arr, seg_dep, seg_dur, want_lay, want_total):
    """1 if the arrival time, layover and total trip time all match the reference, else 0."""
    import re
    def to_minutes(s):
        m = re.search(r'(\d{1,2}):(\d{2})', str(s))
        if m: return int(m.group(1))*60 + int(m.group(2))
        m2 = re.search(r'(\d+)\s*h\s*(\d{1,2})\s*m', str(s).replace(' ', ''))
        if m2: return int(m2.group(1))*60 + int(m2.group(2))
        return None
    arrival = to_minutes(arr); layover = to_minutes(lay); trip_minutes = to_minutes(total)
    if arrival is None or layover is None or trip_minutes is None:
        return 0.0
    if arrival != ((int(seg_dep) + int(seg_dur)) % (24*60)):
        return 0.0
    if arrival != (int(want_arr) % (24*60)):
        return 0.0
    if layover != int(want_lay):
        return 0.0
    if trip_minutes != int(want_total):
        return 0.0
    return 1.0

# end of law_code
