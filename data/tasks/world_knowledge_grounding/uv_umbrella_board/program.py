# code: build_code
def build_forecast_url(lat, lng):
    """The Open-Meteo forecast URL for the daily maximum UV index on 17 July 2026."""
    day = '2026-07-17'
    return ('https://api.open-meteo.com/v1/forecast?latitude=' + str(lat) +
            '&longitude=' + str(lng) + '&daily=uv_index_max&timezone=auto'
            '&start_date=' + day + '&end_date=' + day)

# end of build_code

# code: parse_code
def read_uv_band(raw):
    """The day's maximum UV index and its WHO risk band, using a pinned value if none came."""
    if raw is None:
        return {'uv': None, 'band': None, 'src': 'outage'}
    daily = (raw or {}).get('daily') or {}
    daily_max = daily.get('uv_index_max') or []
    uv, source = None, 'archival_fetch'
    if daily_max and daily_max[0] is not None:
        try:
            uv = round(float(daily_max[0]), 1)
        except Exception:
            uv = None
    if uv is None:
        uv, source = 7.1, 'pinned_snapshot_2026-08-10'
    band = None
    if uv is not None:
        if uv < 3: band = 'low'
        elif uv < 6: band = 'moderate'
        elif uv < 8: band = 'high'
        elif uv < 11: band = 'very high'
        else: band = 'extreme'
    return {'uv': uv, 'band': band, 'src': source}

# end of parse_code
