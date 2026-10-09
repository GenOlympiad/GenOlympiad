# shared code: code_d126a94f8d66
def _tally(cc, colours):
    alias = {'turquoise': 'cyan', 'teal': 'cyan', 'aqua': 'cyan',
             'pink': 'magenta', 'violet': 'purple', 'gold': 'yellow',
             'lime': 'green', 'amber': 'orange'}
    ans = (cc or {}).get('answers') or []
    cnt = dict((c, 0) for c in colours)
    other = 0
    for a in ans:
        s = str(a or '').strip().lower()
        hit = None
        for w in s.replace('/', ' ').replace('-', ' ').split():
            w = w.strip('.,;:!?()')
            w = alias.get(w, w)
            if w in cnt:
                hit = w
                break
        if hit is None:
            other += 1
        else:
            cnt[hit] += 1
    return cnt, other, len(ans)

def check_uniform_counts(colour_reads, colours, m, min_colours):
    """1.0 when every colour used appears exactly m times and enough colours appear."""
    counts, other, n = _tally(colour_reads, colours)
    if n == 0:
        return {'frac': 0.0, 'no_read': True, 'verdict': 'no object was read'}
    used = dict((c, v) for c, v in counts.items() if v > 0)
    detail = ', '.join('%s=%d' % (c, v) for c, v in sorted(used.items()))
    if other > 0:
        return {'frac': 0.0, 'no_read': False, 'n_other': other,
                'verdict': '%d object(s) are off-palette (%s) -> universal quantifier fails'
                           % (other, detail)}
    if len(used) < int(min_colours):
        return {'frac': 0.0, 'no_read': False,
                'verdict': 'only %d colours used, spec floor %d (%s)'
                           % (len(used), int(min_colours), detail)}
    ok = all(v == int(m) for v in used.values())
    return {'frac': 1.0 if ok else 0.0, 'no_read': False,
            'verdict': 'every colour must appear exactly %d times; read %s -> %s'
                       % (int(m), detail, 'uniform' if ok else 'NOT uniform')}

def colour_coverage(colour_reads, colours, min_colours):
    """1.0 if enough colours are used, else a third less for each colour missing."""
    counts, other, n = _tally(colour_reads, colours)
    if n == 0:
        return {'frac': 0.0, 'no_read': True, 'verdict': 'no object was read'}
    k = sum(1 for v in counts.values() if v > 0)
    K = int(min_colours)
    frac = 1.0 if k >= K else max(0.0, 1.0 - (K - k) / 3.0)
    return {'frac': round(frac, 4), 'no_read': False, 'kinds': k,
            'verdict': '%d different colours used, spec floor %d' % (k, K)}

# end of code_d126a94f8d66

# code: hold_uniform_multiplicity_p6_u_code
def hold_uniform_multiplicity_p6_u(result):
    """Withhold the result when no object colour was read."""
    withheld = bool((result or {}).get('no_read'))
    return {'no_read': withheld, 'refused': withheld}

# end of hold_uniform_multiplicity_p6_u_code

# code: hold_kind_coverage_p6_k_code
def hold_kind_coverage_p6_k(result):
    """Withhold the result when no object colour was read."""
    withheld = bool((result or {}).get('no_read'))
    return {'no_read': withheld, 'refused': withheld}

# end of hold_kind_coverage_p6_k_code

# code: hold_uniform_multiplicity_p8_u_code
def hold_uniform_multiplicity_p8_u(result):
    """Withhold the result when no object colour was read."""
    withheld = bool((result or {}).get('no_read'))
    return {'no_read': withheld, 'refused': withheld}

# end of hold_uniform_multiplicity_p8_u_code

# code: hold_kind_coverage_p8_k_code
def hold_kind_coverage_p8_k(result):
    """Withhold the result when no object colour was read."""
    withheld = bool((result or {}).get('no_read'))
    return {'no_read': withheld, 'refused': withheld}

# end of hold_kind_coverage_p8_k_code
