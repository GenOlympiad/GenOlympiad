# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# shared code: code_2ef52f585778
def all_from_set(sticker_count):
    """Score 1 when every confirmed sticker cut-out carries a cube colour."""
    try:
        n = int((sticker_count or {}).get('n'))
        asked = int((sticker_count or {}).get('asked'))
    except Exception:
        return {'frac': 0.0, 'no_read': True, 'refused': True,
                'why': 'the sticker count returned no counts'}
    if asked <= 0:
        return {'frac': 0.0, 'no_read': True, 'refused': True,
                'why': 'the count confirmed no sticker cut-out at all -- nothing to judge'}
    return {'frac': 1.0 if n == asked else 0.0, 'n': n, 'asked': asked, 'no_read': False,
            'verdict': '%d of the %d confirmed cut-outs carry a cube colour' % (n, asked)}

# end of code_2ef52f585778

# shared code: code_3479764cc62f
def sticker_boxes(face, n):
    """Split the confirmed face box, or the whole frame, into an n by n grid of boxes."""
    n = int(n)
    if n <= 0:
        return {'boxes': None, 'n': 0, 'anchor': 'none'}
    face_boxes = (face or {}).get('geometry') or []
    if face_boxes:
        y0, x0, y1, x1 = [float(v) for v in face_boxes[0][:4]]
        anchor = 'confirmed sticker-block box'
    else:
        y0, x0, y1, x1 = 0.0, 0.0, 1000.0, 1000.0
        anchor = 'full frame (ring refused; prompt pins the face filling the frame)'
    if y1 - y0 < 100.0 or x1 - x0 < 100.0:
        y0, x0, y1, x1 = 0.0, 0.0, 1000.0, 1000.0
        anchor = 'full frame (degenerate box)'
    h = (y1 - y0) / float(n)
    w = (x1 - x0) / float(n)
    out = []
    for i in range(n):
        for j in range(n):
            out.append([y0 + h * i, x0 + w * j, y0 + h * (i + 1), x0 + w * (j + 1)])
    return {'boxes': out, 'n': n * n, 'anchor': anchor, 'rect': [y0, x0, y1, x1]}

# end of code_3479764cc62f

# code: face_grid_code
import re
PAL = ['white', 'yellow', 'green', 'blue', 'red', 'orange']
def face_grid(rd, n):
    """Arrange the read sticker colours into an n by n grid, failing if any is missing."""
    n = int(n)
    answers = (rd or {}).get('answers') or []
    stickers = []
    for a in answers:
        colour_words = [w for w in re.findall(r'[a-z]+', str(a or '').lower()) if w in PAL]
        stickers.append(colour_words[-1] if colour_words else '')
    if len(stickers) != n * n or any(c == '' for c in stickers):
        return {'grid': None, 'ok': False, 'read': answers}
    return {'grid': [stickers[i * n:(i + 1) * n] for i in range(n)], 'ok': True, 'read': answers}

# end of face_grid_code
