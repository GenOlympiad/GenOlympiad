"""Live reference facts, such as sun and moon times, for world-knowledge tasks."""
from __future__ import annotations
import time
import urllib.request
import urllib.parse
import logging

log = logging.getLogger(__name__)

_UA = {"User-Agent": "GenOlympiad/1.0"}


def _get(url: str, timeout: int = 25, retries: int = 3) -> bytes:
    last = None
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers=_UA)
            return urllib.request.urlopen(req, timeout=timeout).read()
        except Exception as e:
            log.debug("error ignored in _get", exc_info=True)
            last = e
            time.sleep(0.6 * (i + 1))
    raise last


_WMO = {
    0: "clear", 1: "clear", 2: "cloudy", 3: "cloudy",
    45: "fog", 48: "fog",
    51: "rain", 53: "rain", 55: "rain", 56: "rain", 57: "rain",
    61: "rain", 63: "rain", 65: "rain", 66: "rain", 67: "rain",
    80: "rain", 81: "rain", 82: "rain",
    71: "snow", 73: "snow", 75: "snow", 77: "snow", 85: "snow", 86: "snow",
    95: "storm", 96: "storm", 99: "storm",
}


def moon_phase_bucket(phase: float) -> str:
    p = float(phase) % 28.0
    if p < 1.0 or p >= 27.0:
        return "new moon"
    if p < 6.0:
        return "waxing crescent"
    if p < 8.0:
        return "first quarter"
    if p < 13.0:
        return "waxing gibbous"
    if p < 15.0:
        return "full moon"
    if p < 20.0:
        return "waning gibbous"
    if p < 22.0:
        return "last quarter"
    return "waning crescent"


def moon_illumination_pct(phase: float) -> float:
    import math
    f = (float(phase) % 29.53) / 29.53
    return round(100.0 * (1.0 - math.cos(2.0 * math.pi * f)) / 2.0, 1)


def _minutes_of_day(dt) -> int:
    return dt.hour * 60 + dt.minute + (1 if dt.second >= 30 else 0)


def compute_sun_moon_almanac(lat: float, lon: float, tz: str, date_iso: str) -> dict:
    import datetime as _dt
    import zoneinfo
    from astral import LocationInfo, moon
    from astral.sun import sun as _sun

    d = _dt.date.fromisoformat(date_iso)
    zi = zoneinfo.ZoneInfo(tz)
    loc = LocationInfo("", "", tz, lat, lon)

    sunrise_hhmm = sunset_hhmm = None
    sunrise_min = sunset_min = day_length_min = None
    try:
        s = _sun(loc.observer, date=d, tzinfo=zi)
        sr, ss = s["sunrise"], s["sunset"]
        sunrise_hhmm = sr.strftime("%H:%M")
        sunset_hhmm = ss.strftime("%H:%M")
        sunrise_min = _minutes_of_day(sr)
        sunset_min = _minutes_of_day(ss)
        day_length_min = sunset_min - sunrise_min
    except Exception:
        log.debug("error ignored in compute_sun_moon_almanac", exc_info=True)
        pass

    phase_num = None
    try:
        phase_num = float(moon.phase(d))
    except Exception:
        log.debug("error ignored in compute_sun_moon_almanac", exc_info=True)
        pass

    return {
        "date": date_iso, "timezone": tz, "lat": lat, "lon": lon,
        "sunrise_hhmm": sunrise_hhmm, "sunset_hhmm": sunset_hhmm,
        "sunrise_min": sunrise_min, "sunset_min": sunset_min,
        "day_length_min": day_length_min,
        "moon_phase_num": (round(phase_num, 2) if phase_num is not None else None),
        "moon_phase": (moon_phase_bucket(phase_num) if phase_num is not None else None),
        "moon_illum_pct": (moon_illumination_pct(phase_num) if phase_num is not None else None),
        "source": "astral (pure-python ephemeris; astral.sun.sun + astral.moon.phase)",
        "computed_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


