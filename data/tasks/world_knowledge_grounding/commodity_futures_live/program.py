# code: build_code
import requests, time
UA={'User-Agent':'GenOlympiad/1.0'}
P1=1784030400; P2=1784304000; INST=1784214000
def price_near_session(sym):
    for _ in range(4):
        try:
            u=('https://query1.finance.yahoo.com/v8/finance/chart/'+str(sym)+'?period1=%d&period2=%d&interval=1h'%(P1,P2))
            res=requests.get(u,headers=UA,timeout=25).json()['chart']['result'][0]
            ts=res.get('timestamp') or []; cl=res['indicators']['quote'][0]['close']
            cand=[(x,c) for x,c in zip(ts,cl) if c is not None and x<=P2]
            if cand: return min(cand,key=lambda tc:abs(tc[0]-INST))[1]
        except Exception:
            pass
        time.sleep(0.7)
    return None
def fetch_spot_prices(_):
    """Gold, silver and crude futures prices near the session time, and the gold to silver ratio."""
    gold=price_near_session('GC=F'); silver=price_near_session('SI=F'); wti=price_near_session('CL=F')
    ratio=(gold/silver) if (gold and silver) else None
    return {'gold': round(gold,2) if gold else None,
            'silver': round(silver,2) if silver else None,
            'wti': round(wti,2) if wti else None,
            'ratio': round(ratio,2) if ratio else None}
# end of build_code
