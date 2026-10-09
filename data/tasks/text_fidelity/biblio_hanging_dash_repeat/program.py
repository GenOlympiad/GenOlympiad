# shared code: code_entry_rows
def entry_rows(year_reads, page_reads, rule, name, pages, years):
    """Count entries with their own pages and a dash for the name exactly where it repeats."""
    grp = lambda x: ''.join(c if c.isdigit() else ' ' for c in str(x)).split()
    years_read = [(grp(x) + [''])[0][:4] for x in ((year_reads or {}).get('answers') or [])]
    pages_read = ['-'.join(grp(x)[-2:]) if len(grp(x)) > 1 else '' for x in ((page_reads or {}).get('answers') or [])]
    yn = lambda nd: [str(x).strip().lower().startswith('y') for x in ((nd or {}).get('answers') or [])]
    rule_flags, name_flags = yn(rule), yn(name)
    want = {str(w) for w in (years or [])}
    key = {(grp(k) + [''])[0][:4]: '-'.join(grp(w)[-2:]) for k, w in dict(pages or {}).items()}
    good = [i for i, k in enumerate(years_read) if k in key and i < min(len(pages_read), len(rule_flags), len(name_flags))
            and pages_read[i] == key[k] and rule_flags[i] == (k in want) and name_flags[i] != rule_flags[i]]
    return {'ok': len(good), 'asked': len(years_read),
            'verdict': '%d of the %d entries carry their own pages and stand down exactly where the name repeats' % (len(good), len(years_read))}

# end of code_entry_rows

# shared code: code_yes_vote
def yes_vote(node):
    """The majority yes or no answer across the cut-outs, or none if none answered."""
    ans = [str(x).strip().lower() for x in ((node or {}).get('answers') or [])]
    yes = sum(1 for a in ans if a.startswith('y'))
    no = sum(1 for a in ans if a.startswith('n'))
    v = 'yes' if yes > no else ('no' if no else 'none')
    return {'v': v, 'asked': len(ans),
            'verdict': '%d of the %d cut-outs answered yes and %d answered no' % (yes, len(ans), no)}

# end of code_yes_vote
