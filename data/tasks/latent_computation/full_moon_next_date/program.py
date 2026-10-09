# code: chk_code
def next_full_moon_match(ans, want_wd, want_dom, want_mon):
    """Score 1 when the weekday, day and month in the answer match the reference date."""
    import re
    if ans is None or isinstance(ans, dict):
        return 0.0
    text = str(ans).lower()
    wd = re.search(r'(mon|tue|wed|thu|fri|sat|sun)[a-z]*', text)
    dm = re.search(r'day\s*[=:]?\s*(\d{1,2})', text) or re.search(r'\b(\d{1,2})\b', text)
    mo = re.search(r'(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)', text)
    if wd is None or dm is None or mo is None:
        return 0.0
    ok = (wd.group(1)[:3] == str(want_wd).lower()[:3]
          and int(dm.group(1)) == int(want_dom)
          and mo.group(1) == str(want_mon)[:3].lower())
    return 1.0 if ok else 0.0

# end of chk_code

# code: chk_code_2
def last_full_moon_match(ans, want_dom, want_mon):
    """Score 1 when the day and month in the answer match the last recorded full moon."""
    import re
    if ans is None or isinstance(ans, dict):
        return 0.0
    text = str(ans).lower()
    dm = re.search(r'day\s*[=:]?\s*(\d{1,2})', text) or re.search(r'\b(\d{1,2})\b', text)
    mo = re.search(r'(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)', text)
    if dm is None or mo is None:
        return 0.0
    return 1.0 if (int(dm.group(1)) == int(want_dom) and mo.group(1) == str(want_mon)[:3].lower()) else 0.0

# end of chk_code_2
