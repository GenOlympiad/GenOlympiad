# code: chk_code
def date_matches_reference(answer, want):
    """Score 1 if the read date's year, month and day agree with the use-by date."""
    import re
    if answer is None or isinstance(answer, dict): return 0.0
    months = {'jan':1,'feb':2,'mar':3,'apr':4,'may':5,'jun':6,'jul':7,'aug':8,'sep':9,
              'sept':9,'oct':10,'nov':11,'dec':12,'january':1,'february':2,'march':3,
              'april':4,'june':6,'july':7,'august':8,'september':9,'october':10,
              'november':11,'december':12}
    def toks(s):
        s = str(s).strip().lower()
        nums, mons = [], []
        for w in re.findall(r'[a-z]+', s):
            if w[:4] in months: mons.append(months[w[:4]])
            elif w[:3] in months: mons.append(months[w[:3]])
        for m in re.findall(r'\d+', s):
            nums.append(int(m))
        year = None
        for n in nums:
            if n >= 1900: year = n
        if not mons:
            iso = re.findall(r'\d{4}\D+(\d{1,2})\D+(\d{1,2})', s)
            if iso: mons.append(int(iso[0][0]))
            else:
                dm = re.findall(r'(\d{1,2})\D+(\d{1,2})\D+\d{4}', s)
                if dm: mons.append(int(dm[0][1]))
        day = None
        for n in nums:
            if 1 <= n <= 31 and n != year and (not mons or n != mons[0]):
                day = n; break
        return year, (mons[0] if mons else None), day
    ay, am, ad = toks(answer)
    wy, wm, wd = toks(want)
    if wy is not None and ay != wy: return 0.0
    if wm is not None and am != wm: return 0.0
    if wd is not None and ad is not None and ad != wd: return 0.0
    if wy is None and wm is None: return 0.0
    return 1.0

# end of chk_code
