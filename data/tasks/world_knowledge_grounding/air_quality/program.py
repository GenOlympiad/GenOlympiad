# code: build_code
def build_query_url(lat, lon):
    """The Open-Meteo air quality query URL for the location on 16 July 2026."""
    return ('https://air-quality-api.open-meteo.com/v1/air-quality?latitude=%s&longitude=%s'
            '&hourly=us_aqi,pm2_5,pm10,ozone,nitrogen_dioxide,sulphur_dioxide,carbon_monoxide'
            '&start_date=2026-07-16&end_date=2026-07-16'
            '&timezone=auto') % (lat, lon)
# end of build_code

# code: pick_code
def reading_at_nine_pm(raw):
    """The US AQI and PM2.5 values at 21:00 on 16 July 2026 from the hourly data."""
    hourly = (raw or {}).get('hourly') or {}
    times = hourly.get('time') or []
    target = '2026-07-16T21:00'
    i = times.index(target) if target in times else (len(times) - 1 if times else None)
    return {} if i is None else {'us_aqi': (hourly.get('us_aqi') or [None])[i],
                                 'pm2_5': (hourly.get('pm2_5') or [None])[i]}
# end of pick_code

# code: cat_code
def aqi_category(a):
    """The US AQI category name for an index value."""
    if a is None: return None
    a=float(a)
    if a<=50: return 'good'
    if a<=100: return 'moderate'
    if a<=150: return 'usg'
    if a<=200: return 'unhealthy'
    if a<=300: return 'very unhealthy'
    return 'hazardous'
# end of cat_code

# code: pair_up_code
def join_number_and_category(number, word):
    """Join the number read and the category word read into one string."""
    return '%s, %s' % (str(number).strip(), str(word).strip())

# end of pair_up_code
