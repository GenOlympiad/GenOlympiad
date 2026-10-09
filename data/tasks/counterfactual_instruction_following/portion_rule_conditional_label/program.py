# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# shared code: code_pair_map
import re


def weight_to_serving_pairs(labels, vals):
    """Pair each net weight read with its serving line word, as one sorted text."""
    label_answers = (labels or {}).get('answers') or []
    value_answers = (vals or {}).get('answers') or []
    pairs = {}
    for a, b in zip(label_answers, value_answers):
        m = re.search(r'\d+', str(a))
        k = (m.group(0).lstrip('0') or '0') if m else ''
        v = ''.join(c for c in str(b).lower() if c.isalpha())
        if k and v:
            pairs[k] = v
    canon = ' '.join('%s:%s' % (k, pairs[k]) for k in sorted(pairs))
    if not pairs:
        return {'canon': '', 'unreadable': True,
                'verdict': 'no label gave both a net weight and a serving line'}
    return {'canon': canon, 'unreadable': False,
            'verdict': 'read %d labelled entries: %s' % (len(pairs), canon)}

# end of code_pair_map

# shared code: code_number_list
import re


def number_list(node):
    """The first number in each answer, sorted, as one text."""
    vals = []
    for a in (node or {}).get('answers') or []:
        m = re.findall(r'\d+(?:\.\d+)?', str(a).replace(',', ''))
        if m:
            txt = ''.join(c for c in m[0] if c in '0123456789.')
            if '.' in txt:
                txt = txt.rstrip('0').rstrip('.')
            if txt:
                vals.append(txt)
    vals.sort(key=lambda t: (len(t.split('.')[0]), t))
    seq = ' '.join(vals)
    return {'seq': seq or 'nothing read', 'n': len(vals),
            'verdict': 'read %d figures in order: %s' % (len(vals), seq or 'none')}

# end of code_number_list
