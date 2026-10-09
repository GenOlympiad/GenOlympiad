# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# code: law_code
def check_journey_times(dep, dur, arr, want_dep, want_dur, want_arr):
    """1.0 if departure, duration and arrival match the reference and agree on the clock."""
    import re
    def toM(s):
        m = re.search(r'(\d{1,2})\D+(\d{2})', str(s))
        if not m: return None
        return int(m.group(1))*60 + int(m.group(2))
    depart_min = toM(dep); arrive_min = toM(arr)
    if depart_min is None or arrive_min is None: return 0.0
    try: duration = float(dur)
    except Exception: return 0.0
    if depart_min != toM(want_dep): return 0.0
    if abs(duration - float(want_dur)) > 0.5: return 0.0
    if arrive_min != toM(want_arr): return 0.0
    if (arrive_min - depart_min) % (24*60) != int(round(duration)) % (24*60): return 0.0
    return 1.0

# end of law_code
