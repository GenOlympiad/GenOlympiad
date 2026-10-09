# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# shared code: code_one_label
def parting_label_matches(node, want):
    """Match if exactly one caption is read and it equals the reference view."""
    captions = [str(a).strip().upper().replace(' ', '')
           for a in (node or {}).get('answers') or []]
    expected = str(want).strip().upper().replace(' ', '')
    ok = len(captions) == 1 and captions[0] == expected
    return {'state': 'match' if ok else 'off', 'n': len(captions),
            'verdict': 'read %s, wanted %s' % ('|'.join(captions) or 'nothing', expected)}

# end of code_one_label

# shared code: code_order
def order(node, want):
    got = [str(a).strip().upper().replace(' ', '')
           for a in (node or {}).get('answers') or []]
    exp = [w.strip().upper() for w in str(want).split(',')]
    return {'state': 'match' if got == exp else 'off', 'n': len(got),
            'verdict': 'the view reads %s, the rows give %s'
                       % (' '.join(got) or 'nothing', ' '.join(exp))}

# end of code_order

# shared code: code_row_map
def map_hole_rows(labels, bands, slopes):
    """Each hole label's band (upper or lower) and slope (level or sloping)."""
    UP = ('upper', 'top', 'above')
    LO = ('lower', 'bottom', 'below')
    LV = ('level', 'flat', 'horizontal')
    SL = ('slop', 'slant', 'climb', 'rise', 'rising', 'tilt', 'diagonal')
    if not isinstance(labels, dict):
        labels = {}
    if not isinstance(bands, dict):
        bands = {}
    if not isinstance(slopes, dict):
        slopes = {}

    def words(node):
        return [' '.join(str(a or '').lower().split()) for a in (node.get('answers') or [])]

    hole_labels = [''.join(c for c in str(a or '').lower() if c.isalnum())
          for a in (labels.get('answers') or [])]
    band_words, slope_words = words(bands), words(slopes)
    by_label = {}
    for i, k in enumerate(hole_labels):
        if not k:
            continue
        b = band_words[i] if i < len(band_words) else ''
        s = slope_words[i] if i < len(slope_words) else ''
        band = 'upper' if any(w in b for w in UP) else (
            'lower' if any(w in b for w in LO) else 'unread')
        slope = 'level' if any(w in s for w in LV) else (
            'sloping' if any(w in s for w in SL) else 'unread')
        if k not in by_label:
            by_label[k] = band + ' ' + slope
    if not by_label:
        return {'seq': 'no reading', 'refused': True,
                'verdict': 'no hole cut-out came back with its label -> abstain'}
    seq = '|'.join('%s=%s' % (k, by_label[k]) for k in sorted(by_label))
    return {'seq': seq, 'n': len(by_label),
            'verdict': 'bound by the printed hole label: ' + seq}

# end of code_row_map
