# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts, count_listed_items
# end of helpers

# shared code: code_word_set
def distinct_words(node):
    """The distinct lower cased words read, in first seen order."""
    out = []
    for a in ((node or {}).get('answers') or []):
        w = str(a).strip().lower().strip('. ')
        if w and w not in out:
            out.append(w)
    return {'vals': out, 'verdict': 'read %d distinct labels: %s' % (len(out), ', '.join(out))}

# end of code_word_set

# shared code: code_w9face_cropcount
def median_crop_count(node):
    """The median of the numbers read from the cut outs, or refuse if none has one."""
    words = ('zero one two three four five six seven eight nine ten '
             'eleven twelve').split()
    ns = []
    for a in ((node or {}).get('answers') or []):
        t = str(a or '').strip().lower()
        d = ''.join(c if c.isdigit() else ' ' for c in t).split()
        if d:
            ns.append(int(d[0]))
        else:
            hit = [i for i, w in enumerate(words) if w in t.split()]
            if hit:
                ns.append(hit[0])
    if not ns:
        return {'n': -1, 'refused': True, 'unreadable': True,
                'verdict': 'no cut-out came back with a number -> abstain'}
    ns.sort()
    return {'n': ns[len(ns) // 2], 'reads': ns,
            'verdict': 'the cut-outs counted ' + ', '.join(str(x) for x in ns)}

# end of code_w9face_cropcount

# shared code: code_w9face_shapeword
def read_seam_shapes(node):
    """The first straight or curved word read from each cut out, or refuse if none."""
    outs = []
    for a in ((node or {}).get('answers') or []):
        toks = ''.join(c if c.isalpha() else ' ' for c in str(a or '').lower()).split()
        for tok in toks:
            if tok in ('straight', 'curved'):
                outs.append(tok)
                break
    if not outs:
        return {'answers': [], 'refused': True, 'unreadable': True,
                'verdict': 'no cut-out named a seam shape -> abstain'}
    return {'answers': outs, 'n': len(outs),
            'verdict': 'the cut-outs read ' + '|'.join(outs)}

# end of code_w9face_shapeword
