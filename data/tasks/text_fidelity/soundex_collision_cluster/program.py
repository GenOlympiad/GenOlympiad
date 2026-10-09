# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# shared code: code_sorted_codes
import re


def sorted_sound_codes(node):
    """The sound codes read off the cards, sorted."""
    rows = []
    for raw in (node or {}).get('answers') or []:
        m = re.search(r'[A-Za-z]\d{3}', str(raw))
        if m:
            rows.append(m.group(0).upper())
    rows.sort()
    return {'seq': '|'.join(rows), 'n': len(rows),
            'verdict': 'the codes were read back as %s' % ('|'.join(rows) or 'nothing')}

# end of code_sorted_codes

# shared code: code_placed_by_sound
import re


def _sound_code(name):
    groups = {'B': '1', 'F': '1', 'P': '1', 'V': '1',
              'C': '2', 'G': '2', 'J': '2', 'K': '2', 'Q': '2', 'S': '2', 'X': '2', 'Z': '2',
              'D': '3', 'T': '3', 'L': '4', 'M': '5', 'N': '5', 'R': '6'}
    s = ''.join(c for c in str(name).upper() if c.isalpha())
    if not s:
        return ''
    out = s[0]
    prev = groups.get(s[0], '')
    for ch in s[1:]:
        if ch in 'HW':
            continue
        fig = groups.get(ch, '')
        if fig and fig != prev:
            out += fig
        prev = fig
        if len(out) == 4:
            break
    return (out + '000')[:4]


def fronts_carry_surname_codes(names, fronts):
    """Card by card, whether the front carries the sound code of the surname."""
    names_read = [str(a) for a in ((names or {}).get('answers') or [])]
    fronts_read = [str(b) for b in ((fronts or {}).get('answers') or [])]
    rows = []
    for i in range(min(len(names_read), len(fronts_read))):
        want = _sound_code(names_read[i])
        m = re.search(r'[A-Za-z]\d{3}', fronts_read[i])
        got = m.group(0).upper() if m else ''
        rows.append('match' if (want and got == want) else 'no')
    return {'seq': '|'.join(rows), 'n': len(rows),
            'verdict': 'card by card the front carries the surname code: %s'
                       % ('|'.join(rows) or 'nothing')}

# end of code_placed_by_sound

# shared code: code_two_books
import re


def cards_match_fronts(cards, fronts):
    """Whether the set of codes on the cards equals the set on the fronts."""
    def shapes(node):
        out = []
        for raw in (node or {}).get('answers') or []:
            m = re.search(r'[A-Za-z]\d{3}', str(raw))
            if m:
                out.append(m.group(0).upper())
        return sorted(set(out))

    card_codes, front_codes = shapes(cards), shapes(fronts)
    seq = '|'.join(card_codes) if card_codes and card_codes == front_codes else 'mismatch'
    return {'seq': seq, 'n': len(card_codes),
            'verdict': 'cards give %s against fronts %s'
                       % ('|'.join(card_codes) or 'nothing', '|'.join(front_codes) or 'nothing')}

# end of code_two_books
