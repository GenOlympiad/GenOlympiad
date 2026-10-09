# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# shared code: code_codes
def plan_codes_match(code_reads, want):
    """Whether the position codes read on the plan equal the reference set."""
    got = sorted(''.join(c for c in str(a) if c.isdigit())
                 for a in (code_reads or {}).get('answers') or [])
    expected = sorted(w.strip() for w in str(want).split(','))
    return {'state': 'match' if got == expected else 'off', 'n': len(got),
            'verdict': 'the plan carries %s' % (' '.join(got) or 'nothing')}

# end of code_codes

# shared code: code_rows
def codes_match_row_labels(code_reads, label_reads):
    """Whether each of the three codes carries the row number of the label it stands over."""
    cs = [''.join(c for c in str(a) if c.isdigit())
          for a in (code_reads or {}).get('answers') or []]
    ls = [''.join(c for c in str(a) if c.isdigit())
          for a in (label_reads or {}).get('answers') or []]
    n = min(len(cs), len(ls))
    ok = n == 3 and all(len(cs[i]) == 6 and cs[i][2:4] == ls[i].zfill(2)
                        for i in range(n))
    return {'state': 'match' if ok else 'off', 'n': n,
            'verdict': '; '.join('%s stands over %s' % (cs[i], ls[i])
                                 for i in range(n)) or 'nothing read'}

# end of code_rows
