# code: set_match_code
def fret_match_share(read, target):
    """The share of reference fret numbers found in the read tab, each one matched once."""
    def toks(x):
        if x is None: return []
        if isinstance(x, str):
            return [t for t in x.replace(',', ' ').replace('/', ' ').split() if t]
        return [str(t).strip() for t in x if str(t).strip()]
    r=toks(read); t=toks(target)
    if not t: return 0.0
    remaining=list(r); matched=0
    for tok in t:
        if tok in remaining: remaining.remove(tok); matched+=1
    return round(matched/len(t),4)

# end of set_match_code

# code: count_tokens_code
def count_tokens(a):
    """Count the space-separated numbers read from the tab, or None if unreadable."""
    if a is None or isinstance(a, dict): return None
    s=str(a).strip()
    if not s or 'unreadable' in s.lower(): return None
    tokens=[t for t in s.split() if t.strip()]
    return len(tokens) if tokens else None

# end of count_tokens_code
