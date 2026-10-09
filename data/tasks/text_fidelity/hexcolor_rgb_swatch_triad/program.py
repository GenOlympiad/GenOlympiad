# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# shared code: code_three_notations_agree
import re


def three_notations_agree(hexes, decs, inks):
    """Per swatch, whether the decimal triple and colour name agree with its hex value."""
    def rows_of(node):
        return [str(a) for a in ((node or {}).get('answers') or [])]

    hex_reads, decimal_reads, ink_reads = rows_of(hexes), rows_of(decs), rows_of(inks)
    rows = []
    for i in range(min(len(hex_reads), len(decimal_reads), len(ink_reads))):
        m = re.search(r'(?<![0-9A-Za-z])[0-9A-Fa-f]{6}(?![0-9A-Za-z])', hex_reads[i])
        if not m:
            rows.append('unread')
            continue
        v = m.group(0).upper()
        chan = [int(v[0:2], 16), int(v[2:4], 16), int(v[4:6], 16)]
        want = ','.join(str(c) for c in chan)
        got = ','.join(re.findall(r'\d+', decimal_reads[i])[:3])
        hi, lo = max(chan), min(chan)
        if hi == lo:
            hue = 0.0
        elif hi == chan[0]:
            hue = 60.0 * (((chan[1] - chan[2]) / float(hi - lo)) % 6)
        elif hi == chan[1]:
            hue = 60.0 * (((chan[2] - chan[0]) / float(hi - lo)) + 2)
        else:
            hue = 60.0 * (((chan[0] - chan[1]) / float(hi - lo)) + 4)
        name = 'red'
        for edge, word in ((20, 'red'), (45, 'orange'), (70, 'yellow'), (160, 'green'),
                           (260, 'blue'), (340, 'purple'), (360, 'red')):
            if hue < edge:
                name = word
                break
        said = ''.join(c for c in ink_reads[i].strip().lower() if c.isalpha())
        rows.append('agree' if (got == want and said == name) else 'no')
    return {'seq': '|'.join(rows), 'n': len(rows),
            'verdict': 'swatch by swatch the three notations close as %s'
                       % ('|'.join(rows) or 'nothing')}

# end of code_three_notations_agree

# shared code: code_triples
def decimal_triples_by_position(node, swatch_boxes):
    """The decimal triples read per swatch, ordered left to right by box position."""
    def boxes_of(n):
        g = n.get('geometry') if isinstance(n, dict) else None
        return [b for b in (g or []) if isinstance(b, (list, tuple)) and len(b) >= 4]
    ans = node.get('answers') if isinstance(node, dict) else None
    ans = list(ans) if isinstance(ans, (list, tuple)) else []
    boxes = boxes_of(swatch_boxes)
    rows = []
    for i, raw in enumerate(ans):
        nums = ''.join(c if c.isdigit() else ' ' for c in str(raw)).split()
        if len(nums) >= 3:
            cx = (float(boxes[i][1]) + float(boxes[i][3])) / 2.0 if i < len(boxes) else 1000000.0
            rows.append((cx, i, ','.join(str(int(v)) for v in nums[:3])))
    rows.sort()
    seq = '|'.join(r for _, _, r in rows)
    return {'seq': seq, 'n': len(rows),
            'verdict': 'the decimal lines read %s left to right by their own ring positions' % (seq or 'nothing')}

# end of code_triples

# shared code: code_names
def colour_names_by_position(node, swatch_boxes):
    """The colour names read per swatch, ordered left to right by box position."""
    def boxes_of(n):
        g = n.get('geometry') if isinstance(n, dict) else None
        return [b for b in (g or []) if isinstance(b, (list, tuple)) and len(b) >= 4]
    ans = node.get('answers') if isinstance(node, dict) else None
    ans = list(ans) if isinstance(ans, (list, tuple)) else []
    boxes = boxes_of(swatch_boxes)
    rows = []
    for i, raw in enumerate(ans):
        word = ''.join(c for c in str(raw).strip().lower() if c.isalpha())
        if word:
            cx = (float(boxes[i][1]) + float(boxes[i][3])) / 2.0 if i < len(boxes) else 1000000.0
            rows.append((cx, i, word))
    rows.sort()
    seq = '|'.join(w for _, _, w in rows)
    return {'seq': seq, 'n': len(rows),
            'verdict': 'the swatches read back as %s left to right by their own ring positions' % (seq or 'nothing')}

# end of code_names

# shared code: code_hexes
import re


def hex_values_by_position(node, swatch_boxes):
    """The hex values read per swatch, ordered left to right by box position."""
    def boxes_of(n):
        g = n.get('geometry') if isinstance(n, dict) else None
        return [b for b in (g or []) if isinstance(b, (list, tuple)) and len(b) >= 4]
    ans = node.get('answers') if isinstance(node, dict) else None
    ans = list(ans) if isinstance(ans, (list, tuple)) else []
    boxes = boxes_of(swatch_boxes)
    rows = []
    for i, raw in enumerate(ans):
        m = re.search(r'(?<![0-9A-Za-z])[0-9A-Fa-f]{6}(?![0-9A-Za-z])', str(raw))
        if m:
            cx = (float(boxes[i][1]) + float(boxes[i][3])) / 2.0 if i < len(boxes) else 1000000.0
            rows.append((cx, i, m.group(0).upper()))
    rows.sort()
    seq = '|'.join(v for _, _, v in rows)
    return {'seq': seq, 'n': len(rows),
            'verdict': 'the book values read %s left to right by their own ring positions' % (seq or 'nothing')}

# end of code_hexes
