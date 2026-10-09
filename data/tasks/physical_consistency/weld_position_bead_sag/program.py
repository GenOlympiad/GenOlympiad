# shared code: code_keyed_pairs
def pair_codes_with_reads(keys, vals):
    """Pair each coupon's stamped two-letter code with the first word read for it."""
    codes = [''.join(c for c in str(k or '').lower() if c.isalpha())[:2]
          for k in (keys or {}).get('answers') or []]
    first_words = [str(v or '').strip().lower().split()[0] if str(v or '').strip() else ''
          for v in (vals or {}).get('answers') or []]
    rows = {}
    for i, k in enumerate(codes):
        if k and k not in rows:
            rows[k] = first_words[i] if i < len(first_words) and first_words[i] else 'nothing'
    if not rows:
        return {'seq': 'none', 'refused': True,
                'verdict': 'no coupon cut-out came back with a stamped code -> abstain'}
    seq = '|'.join('%s=%s' % (k, rows[k]) for k in sorted(rows))
    return {'seq': seq, 'verdict': 'the board reads %s' % seq}

# end of code_keyed_pairs
