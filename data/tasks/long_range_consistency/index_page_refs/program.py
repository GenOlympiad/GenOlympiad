# code: idx_code
def check_index_order(tseq, see_read, reference):
    """Check the terms are in alphabetical order and every see redirect names a real entry."""
    import re
    want_terms_list = [str(x).strip().casefold().rstrip(',') for x in reference['terms_sorted']]
    n = len(want_terms_list)
    got = []
    if isinstance(tseq, (list, tuple)):
        got = [re.sub(r'[^A-Za-z-]', '', str(x)).casefold() for x in tseq]
    order_ok = (len(got) >= n and all(got[i] == want_terms_list[i] for i in range(n)))
    seeers = []
    if not isinstance(see_read, dict):
        seeers = [re.sub(r'[^A-Za-z-]', '', str(x)).casefold()
                  for x in re.split(r'[\s,;]+', str(see_read)) if x]
    entry_set = set(str(x).casefold() for x in reference['entry_terms'])
    tgt_sees = [str(x).casefold() for x in reference['see_targets']]
    sees_ok = (seeers == tgt_sees and all(s in entry_set for s in seeers))
    no_read = (len([g for g in got if g]) < max(2, n // 3))
    return {'frac': 1.0 if (order_ok and sees_ok) else 0.0,
            'no_read': no_read,
            'order': 1.0 if order_ok else 0.0,
            'sees': 1.0 if sees_ok else 0.0,
            'read_terms': got, 'want_terms': want_terms_list,
            'read_sees': seeers, 'want_sees': tgt_sees,
            'why': 'alphabetical order %s (read %s vs sorted %s); redirects %s (read %s, must all '
                   'own an entry line)' % ('OK' if order_ok else 'BROKEN', got, want_terms_list,
                                           'RESOLVE' if sees_ok else 'DANGLING/WRONG', seeers)}

# end of idx_code
