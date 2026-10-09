# code: build_code
def price_page_url(code):
    """The archived AAA fuel price page address for the given state code."""
    return ('https://web.archive.org/web/20260716211745/'
            'https://gasprices.aaa.com/?state=' + str(code))

# end of build_code

# code: parse_code
import re
def read_fuel_prices(raw):
    """Read the current average price for each fuel grade from the archived page."""
    out = {}
    s = str(raw or '')
    i = s.find('Current Avg')
    seg = s[i:i+400] if i >= 0 else ''
    nums = re.findall(r'\$([0-9]+\.[0-9]{2,4})', seg)
    vals = [round(float(x), 3) for x in nums[:4]]
    labels = ['regular', 'mid', 'premium', 'diesel']
    for k, v in zip(labels, vals):
        out[k] = v
    out['n'] = len(vals)
    out['ok'] = 1 if len(vals) >= 3 else 0
    return out
# end of parse_code
