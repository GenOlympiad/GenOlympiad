# shared code: swcode
def split_sum_error(laps_str, total_str):
    """The gap in seconds between the shown total and the sum of the lap times."""
    def secs(t):
        t = str(t).strip()
        try:
            if ':' in t:
                mm, rest = t.split(':', 1)
                return int(mm) * 60 + float(rest)
            return float(t)
        except Exception:
            return None
    laps = [secs(x) for x in str(laps_str).replace(',', ' ').split()]
    laps = [x for x in laps if x is not None]
    total = secs(total_str)
    if total is None or len(laps) < 2:
        return 999.0
    return round(abs(total - sum(laps)), 3)

# end of swcode
