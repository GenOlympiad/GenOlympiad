# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# shared code: code_cols
def match_flame_colours(keys, ans, want):
    """Check that each numbered box's read flame colour starts with its reference colour."""
    box_numbers = [''.join(c for c in str(k) if c.isdigit())
          for k in (keys or {}).get('answers') or []]
    colours = [str(c).strip().lower() for c in (ans or {}).get('answers') or []]
    reference_table = dict(p.split(':') for p in str(want).split(','))
    got = {box_numbers[i]: colours[i] for i in range(min(len(box_numbers), len(colours)))}
    all_match = len(got) == len(reference_table) and all(got.get(k, '').startswith(v)
                                      for k, v in reference_table.items())
    return {'state': 'match' if all_match else 'off', 'n': len(got),
            'verdict': '; '.join('%s=%s' % (k, got[k]) for k in sorted(got))
                       or 'nothing read'}

# end of code_cols

# shared code: code_nm
def match_line_wavelengths(keys, ans, want):
    """Check that each numbered box's read wavelength falls in its reference range."""
    box_numbers = [''.join(c for c in str(k) if c.isdigit())
          for k in (keys or {}).get('answers') or []]
    wavelengths = [''.join(c for c in str(v) if c.isdigit())
          for v in (ans or {}).get('answers') or []]
    reference_table = dict(p.split(':') for p in str(want).split(','))
    got = {box_numbers[i]: wavelengths[i] for i in range(min(len(box_numbers), len(wavelengths)))}
    def hit(k, rng):
        lo, hi = [int(x) for x in rng.split('-')]
        return got.get(k, '').isdigit() and lo <= int(got[k]) <= hi
    all_match = all(k in got and hit(k, v) for k, v in reference_table.items())
    return {'state': 'match' if all_match else 'off', 'n': len(got),
            'verdict': '; '.join('%s=%s' % (k, got[k]) for k in sorted(got))}

# end of code_nm

# shared code: code_w9face_readhold
def check_reads_present(a, b):
    """Refuse when either the key reads or the value reads came back empty."""
    xs = [x for x in ((a or {}).get('answers') or []) if x]
    ys = [y for y in ((b or {}).get('answers') or []) if y]
    if not xs or not ys:
        return {'refused': True, 'unreadable': True, 'n': len(xs),
                'verdict': 'the cut-outs came back with nothing to pair up -> abstain'}
    return {'refused': False, 'n': len(xs),
            'verdict': '%d keys and %d readings came back' % (len(xs), len(ys))}

# end of code_w9face_readhold

# shared code: code_w9face_wholenm
def whole_nm_values(node):
    """Turn each read wavelength into a whole number of nanometres, blank if none."""
    wavelengths = []
    for a in ((node or {}).get('answers') or []):
        t = ''.join(c if (c.isdigit() or c == '.') else ' ' for c in str(a or ''))
        v = ''
        for tok in t.split():
            try:
                v = str(int(round(float(tok))))
                break
            except ValueError:
                continue
        wavelengths.append(v)
    return {'answers': wavelengths, 'n': len(wavelengths),
            'verdict': 'read as whole nanometres: ' + '|'.join(o or '-' for o in wavelengths)}

# end of code_w9face_wholenm
