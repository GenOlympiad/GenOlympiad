# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# code: unpaired_code
def count_unpaired_gloves(hands, cols):
    """Count gloves left without a partner of the other hand within each colour."""
    hand_reads = [str(a).strip().lower()[:1] for a in ((hands or {}).get('answers') or [])]
    colour_reads = [str(a).strip().lower() for a in ((cols or {}).get('answers') or [])]
    tally = {}
    for i in range(min(len(hand_reads), len(colour_reads))):
        if hand_reads[i] in ('l', 'r'):
            row = tally.setdefault(colour_reads[i], [0, 0])
            row[0 if hand_reads[i] == 'l' else 1] += 1
    unpaired_count = sum(abs(r[0] - r[1]) for r in tally.values())
    return {'n': unpaired_count, 'seen': len(hand_reads),
            'verdict': '%d glove(s) left with no partner across %d read'
                       % (unpaired_count, len(hand_reads))}

# end of unpaired_code

# code: tally_two_code
def counts_agree(glove_count, tag_count):
    """Answer yes when the glove count and the claim tag count agree and are not zero."""
    a = int((glove_count or {}).get('n') or 0)
    b = int((tag_count or {}).get('n') or 0)
    return {'v': 'yes' if (a > 0 and a == b) else 'no', 'a': a, 'b': b,
            'verdict': 'goods on the table counted %d, claim tags counted %d' % (a, b)}

# end of tally_two_code

# code: tags_uniq_code
def tags_are_unique(node):
    """Answer yes when every tag number reads and no two tags share a number."""
    import re
    vals = []
    for a in ((node or {}).get('answers') or []):
        m = re.search(r'\d+', str(a))
        vals.append(str(int(m.group())) if m else '')
    numbers = [v for v in vals if v]
    n = len(set(numbers))
    ok = 'yes' if (numbers and n == len(numbers) and n == len(vals)) else 'no'
    return {'v': ok, 'n': n, 'asked': len(vals)}

# end of tags_uniq_code
