# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# code: law_code
def taper_row_check(dose, day, lastdose, want_dose, want_day, start_iso, day_index):
    """1 if the read dose, date and final dose match the taper schedule, else 0."""
    import datetime
    try:
        dose_read = float(dose); day_read = int(round(float(day))); last_dose_read = float(lastdose)
    except Exception:
        return 0.0
    if abs(dose_read - float(want_dose)) > 0.5:
        return 0.0
    d0 = datetime.date.fromisoformat(str(start_iso))
    want = d0 + datetime.timedelta(days=int(day_index))
    if day_read != want.day:
        return 0.0
    if abs(last_dose_read) > 0.5:
        return 0.0
    return 1.0

# end of law_code
