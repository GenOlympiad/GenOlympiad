# shared code: code_blank_facts
def check_blank_sizes(confirms, texts):
    """Say if the confirmed outside, inside and gap sizes all exceed their limits."""
    import re
    ok = [str(y).strip().lower().startswith('y') for y in ((confirms or {}).get('answers') or [])]
    sizes = {}
    for i, t in enumerate(((texts or {}).get('answers') or [])):
        s = str(t).strip().lower()
        k = 'gap' if 'gap' in s else ('inside' if 'insi' in s else ('outside' if 'outs' in s else ''))
        n = re.findall(r'\d+(?:\.\d+)?', s)
        if k and n and (i >= len(ok) or ok[i]):
            sizes[k] = float(n[-1])
    v = sizes.get('outside', 0) > 400 and sizes.get('inside', 0) > 114 and sizes.get('gap', 0) > 5
    return {'val': 'grown and open' if v else 'not grown', 'verdict': 'blank read as %s' % sorted(sizes.items())}

# end of code_blank_facts

# shared code: code_pulled_pitch
def pulled_lead(confirms, texts):
    """The lead in mm the listed blank would pull to, from its outside size and gap angle."""
    import re, math
    ok = [str(y).strip().lower().startswith('y') for y in ((confirms or {}).get('answers') or [])]
    sizes = {}
    for i, t in enumerate(((texts or {}).get('answers') or [])):
        s = str(t).strip().lower()
        k = 'gap' if 'gap' in s else ('inside' if 'insi' in s else ('outside' if 'outs' in s else ''))
        if k and (i >= len(ok) or ok[i]) and re.findall(r'\d+(?:\.\d+)?', s):
            sizes[k] = float(re.findall(r'\d+(?:\.\d+)?', s)[-1])
    p = math.radians(360.0 - sizes.get('gap', 0.0)) * sizes.get('outside', 0.0) / 2.0
    p = math.sqrt(max(p * p - (math.pi * 400.0) ** 2, 0.0))
    return {'val': round(p, 1), 'verdict': 'the listed ring would pull to a lead of %.0f mm' % p}

# end of code_pulled_pitch
