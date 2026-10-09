# code: row_digits_code

def row_digits(key_boxes, key_confirms, key_values):
    """The digits on the confirmed keys, read from left to right."""
    import re

    def cx(b):
        return (float(b[1]) + float(b[3])) / 2.0

    def yes(a):
        return str(a).strip().lower().startswith('y')

    geometry = (key_boxes or {}).get('geometry') or []
    confirms = (key_confirms or {}).get('answers') or []
    values = (key_values or {}).get('answers') or []
    keys = []
    for i in range(min(len(geometry), len(confirms))):
        if not yes(confirms[i]):
            continue
        m = re.search(r'\d', str(values[i] if i < len(values) else ''))
        keys.append({'box': geometry[i], 'digit': m.group() if m else 'none'})
    keys.sort(key=lambda k: cx(k['box']))
    digits = [k['digit'] for k in keys]
    return {'digits': digits, 'n': len(digits), 'asked': len(confirms),
            'verdict': '%d of %d framed candidates were confirmed to hold exactly one whole key; '
                       'left to right their printed digits read %s'
                       % (len(digits), len(confirms), ' '.join(digits) if digits else '(nothing)')}

# end of row_digits_code

# code: seq_match_code
def seq_match(read, target):
    """The share of digits matching the reference order, capped at 0.25 on any miss."""
    def norm(tok):
        return str(tok).strip().upper().replace(' ', '')
    def toks(x):
        if x is None: return []
        if isinstance(x, str):
            import re
            return [norm(target_tokens) for target_tokens in re.split(r'[\s,;]+', x) if target_tokens.strip()]
        return [norm(target_tokens) for target_tokens in x if str(target_tokens).strip()]
    read_tokens=toks(read); target_tokens=toks(target)
    if not target_tokens: return 0.0
    ok=sum(1 for i in range(len(target_tokens)) if i<len(read_tokens) and read_tokens[i]==target_tokens[i])
    frac=round(ok/len(target_tokens),4)
    if ok < len(target_tokens): frac=min(frac, 0.25)
    return frac

# end of seq_match_code
