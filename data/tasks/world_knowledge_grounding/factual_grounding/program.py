# shared code: code_95d1dfb2a8c0
import re
_MULT = {'t': 1e12, 'trillion': 1e12, 'b': 1e9, 'bn': 1e9, 'billion': 1e9,
         'm': 1e6, 'mm': 1e6, 'million': 1e6, 'k': 1e3, 'thousand': 1e3}
def first_answer(node):
    if isinstance(node, dict):
        a = node.get('answers') or [None]
        return a[0]
    return node
def money_in_usd(node):
    """Read a money amount from the answer in US dollars, applying words like million."""
    answer = first_answer(node)
    if answer is None:
        return {'usd': None, 'bad': True}
    s = str(answer).lower().replace(',', '').replace('$', ' ')
    m = re.search(r'(-?\d+(?:\.\d+)?)\s*([a-z]+)?', s)
    if not m:
        return {'usd': None, 'bad': True}
    x = float(m.group(1))
    suffix = (m.group(2) or '').strip()
    multiplier = _MULT.get(suffix)
    if multiplier is None:
        for w, v in _MULT.items():
            if len(w) > 2 and w in s:
                multiplier = v
                break
    return {'usd': x * (multiplier or 1.0), 'bad': False, 'read': str(answer)[:60]}
def answer_text(node):
    """The first answer as trimmed text, flagged bad when missing."""
    a = first_answer(node)
    return {'v': (None if a is None else str(a).strip()), 'bad': a is None}

# end of code_95d1dfb2a8c0

# code: hq_city_code
def _get(url):
    import requests, time
    for i in range(4):
        try:
            r = requests.get(url, timeout=30, headers={'User-Agent': 'GenOlympiad/1.0'})
            r.raise_for_status()
            return r.json()
        except Exception:
            time.sleep(0.4 * (i + 1))
    return None

def hq_city(cik):
    """The business address city in the company's SEC filing record."""
    d = _get('https://data.sec.gov/submissions/CIK%s.json' % cik)
    try:
        return d['addresses']['business']['city']
    except Exception:
        return None
# end of hq_city_code

# code: revenue_code
def _get(url):
    import requests, time
    for i in range(4):
        try:
            r = requests.get(url, timeout=30, headers={'User-Agent': 'GenOlympiad/1.0'})
            r.raise_for_status()
            return r.json()
        except Exception:
            time.sleep(0.4 * (i + 1))
    return None

def revenue(cik):
    """The latest reported revenue in US dollars from SEC filing data."""
    d = _get('https://data.sec.gov/api/xbrl/companyconcept/CIK%s/us-gaap/Revenues.json' % cik)
    try:
        arr = d['units']['USD']
        return arr[-1]['val'] if arr else None
    except Exception:
        return None
# end of revenue_code

# code: shares_code
def _get(url):
    import requests, time
    for i in range(4):
        try:
            r = requests.get(url, timeout=30, headers={'User-Agent': 'GenOlympiad/1.0'})
            r.raise_for_status()
            return r.json()
        except Exception:
            time.sleep(0.4 * (i + 1))
    return None

def shares(cik):
    """The latest reported count of common shares outstanding from SEC data."""
    d = _get('https://data.sec.gov/api/xbrl/companyconcept/CIK%s/dei/EntityCommonStockSharesOutstanding.json' % cik)
    try:
        arr = d['units']['shares']
        return arr[-1]['val'] if arr else None
    except Exception:
        return None
# end of shares_code

# code: price_code
def _get(url):
    import requests, time
    for i in range(4):
        try:
            r = requests.get(url, timeout=30, headers={'User-Agent': 'GenOlympiad/1.0'})
            r.raise_for_status()
            return r.json()
        except Exception:
            time.sleep(0.4 * (i + 1))
    return None

def price(ticker):
    """The latest market price of the stock from the daily quote."""
    d = _get('https://query1.finance.yahoo.com/v8/finance/chart/%s?interval=1d&range=1d' % ticker)
    try:
        return d['chart']['result'][0]['meta']['regularMarketPrice']
    except Exception:
        return None
# end of price_code

# code: mcap_code
def market_cap(price, shares):
    """Market value as share price times shares outstanding, or None if either is missing."""
    return (price * shares) if (price and shares) else None
# end of mcap_code

# code: founded_code
def _get(url):
    import requests, time
    for i in range(4):
        try:
            r = requests.get(url, timeout=30, headers={'User-Agent': 'GenOlympiad/1.0'})
            r.raise_for_status()
            return r.json()
        except Exception:
            time.sleep(0.4 * (i + 1))
    return None

def founded_year(qid):
    """The four-digit founding year recorded for the company on Wikidata."""
    d = _get('https://www.wikidata.org/wiki/Special:EntityData/%s.json' % qid)
    try:
        t = d['entities'][qid]['claims']['P571'][0]['mainsnak']['datavalue']['value']['time']
    except Exception:
        return None
    import re
    m = re.search(r'\+(\d{4})', t)
    return m.group(1) if m else None
# end of founded_code
