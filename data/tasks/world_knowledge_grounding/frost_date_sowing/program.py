# shared code: code_frost_dates
def frost_dates_check(spring_read, fall_read, sowing_read, want):
    """Turn the three written dates into days of the year and compare them with local normals."""
    month_names = 'jan feb mar apr may jun jul aug sep oct nov dec'.split()
    month_starts = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]
    def day_of_year(n):
        s = str((((n or {}).get('answers') or [''])[0])).lower()
        m = [i for i, k in enumerate(month_names) if k in s]
        g = [int(x) for x in ''.join(e if e.isdigit() else ' ' for e in s).split() if 0 < int(x) < 32]
        return month_starts[m[0]] + g[0] if m and g else None
    days = [day_of_year(spring_read), day_of_year(fall_read), day_of_year(sowing_read)]
    n_ok = sum(1 for x, y in zip(days, want) if x is not None and abs(x - y) <= 12)
    gap = (days[1] - days[2]) if (days[1] is not None and days[2] is not None) else -999
    return {'n_ok': n_ok, 'gap': gap, 'rows': days, 'verdict': 'days of the year read %s; %d of 2 frost dates sit within 12 days of the local normals; the sowing date stands %d days before the first fall frost the sheet itself carries' % (days, n_ok, gap)}

# end of code_frost_dates
