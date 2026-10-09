# code: fetch_code
import requests, time
UA={'User-Agent':'GenOlympiad/1.0'}
def fetch_snow_depth(cfg):
    """Fetch the archived noon snow depth in centimetres for the set place and date."""
    lat=cfg['lat']; lon=cfg['lon']; date=cfg['date']
    url=('https://archive-api.open-meteo.com/v1/archive?latitude='+str(lat)+'&longitude='+str(lon)+
         '&start_date='+str(date)+'&end_date='+str(date)+'&hourly=snow_depth&timezone=auto')
    hourly=None
    for _ in range(4):
        try:
            response=requests.get(url,headers=UA,timeout=30); response.raise_for_status()
            hourly=(response.json() or {}).get('hourly')
            if hourly and hourly.get('snow_depth'): break
        except Exception:
            pass
        time.sleep(0.7)
    depth_cm=None
    if hourly:
        for t,v in zip(hourly.get('time') or [], hourly.get('snow_depth') or []):
            if str(t).endswith('T12:00') and v is not None:
                try: depth_cm=round(float(v)*100.0)
                except Exception: depth_cm=None
                break
    return {'depth_cm': depth_cm}
# end of fetch_code
