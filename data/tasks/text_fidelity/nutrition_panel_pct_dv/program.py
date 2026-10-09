# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# code: law_code
def percent_dv_and_calories(pct, cal, amt, ref, want_pct, want_cal, p, c, ft):
    """1 if the % daily value and calories match the reference and their formulas."""
    try:
        pct_read = int(round(float(pct))); cal_read = int(round(float(cal)))
    except Exception:
        return 0.0
    calc = round(float(amt) / float(ref) * 100)
    if pct_read != int(want_pct) or pct_read != int(calc):
        return 0.0
    atwater = 4*int(p) + 4*int(c) + 9*int(ft)
    if cal_read != int(want_cal) or cal_read != atwater:
        return 0.0
    return 1.0

# end of law_code
