# shared code: code_09f9b218710c
import re


def _answers(r):
    if isinstance(r, dict):
        a = r.get("answers")
        if isinstance(a, list):
            return [str(x or "") for x in a]
        return [str(r.get("answer") or "")]
    return [str(r or "")]


def _pos(t):
    t = str(t or "").strip().lower()
    m = re.search(r"above\s*([1-9])", t) or re.search(r"([1-9])\s*(?:steps?\s*)?above", t)
    if m:
        return 8 + int(m.group(1))
    m = re.search(r"below\s*([1-9])", t) or re.search(r"([1-9])\s*(?:steps?\s*)?below", t)
    if m:
        return -int(m.group(1))
    m = re.search(r"space\s*([1-4])", t) or re.search(r"([1-4])\w*\s+space", t)
    if m:
        return 2 * int(m.group(1)) - 1
    m = re.search(r"line\s*([1-5])", t) or re.search(r"([1-5])\w*\s+line", t)
    if m:
        return 2 * (int(m.group(1)) - 1)
    return None


def _boxes(r):
    g = r.get("geometry") if isinstance(r, dict) else r
    out = []
    for b in (g or []):
        try:
            y0, x0, y1, x1 = [float(v) for v in list(b)[:4]]
        except Exception:
            continue
        out.append([min(y0, y1), min(x0, x1), max(y0, y1), max(x0, x1)])
    return out


def read_staff(heads, pos, n_notes):
    """Pair notehead boxes with their read positions, left to right, as staff steps."""
    head_boxes = _boxes(heads)
    answers = _answers(pos)
    if not head_boxes or len(answers) != len(head_boxes):
        return {"no_read": True, "reason": "ring_and_reads_disagree",
                "n_boxes": len(head_boxes), "n_answers": len(answers)}
    order = sorted(range(len(head_boxes)), key=lambda i: 0.5 * (head_boxes[i][1] + head_boxes[i][3]))
    positions = [_pos(answers[i]) for i in order]
    if all(v is None for v in positions):
        return {"no_read": True, "reason": "positions_unparsed", "raw": [answers[i] for i in order]}
    return {"no_read": False, "n_heads": len(head_boxes), "pos_index": positions,
            "raw": [answers[i] for i in order]}


def readable_frac(m):
    """Score 1 when every notehead came back with a read position."""
    return 0.0 if m.get("no_read") else 1.0


def count_frac(m, n_notes):
    """Score 1 when the number of noteheads equals the expected count."""
    if m.get("no_read"):
        return 0.0
    return 1.0 if int(m.get("n_heads") or 0) == int(n_notes) else 0.0


def positions_frac(m, reference_positions, tol=0.35):
    """The share of noteheads whose staff position is within tolerance of the reference."""
    if m.get("no_read"):
        return 0.0
    wanted = [float(v) for v in reference_positions]
    got = list(m.get("pos_index") or [])
    ok = 0
    for i, want in enumerate(wanted):
        v = got[i] if i < len(got) else None
        if v is not None and abs(float(v) - want) <= float(tol):
            ok += 1
    return round(ok / float(max(1, len(wanted))), 4)


def appearance_frac(m, n_notes, clef):
    """Score 1 when the notehead count is right and the clef check answers yes."""
    if m.get("no_read"):
        return 0.0
    c = str((_answers(clef) or [""])[0]).strip().lower().startswith("y")
    return 1.0 if (int(m.get("n_heads") or 0) == int(n_notes) and c) else 0.0

# end of code_09f9b218710c

# code: staff_hold_code
def flag_unpaired_staff(m):
    """Mark the staff unreadable when noteheads and position reads do not pair up."""
    staff = m or {}
    unread = bool(staff.get('no_read')); positions_unparsed = str(staff.get('reason') or '') == 'positions_unparsed'
    unpaired = unread and not positions_unparsed
    return {'unreadable': unpaired, 'refused': unpaired, 'no_read': unread, 'reason': staff.get('reason'),
            'n_boxes': staff.get('n_boxes'), 'n_answers': staff.get('n_answers'),
            'verdict': ('the reader did not return one answer per confirmed notehead (%s boxes, %s answers), so nothing was established about the staff' % (staff.get('n_boxes'), staff.get('n_answers'))) if unpaired else ('every confirmed notehead was read and not one answer named a line or a space' if unread else 'the staff positions were read')}

# end of staff_hold_code

# code: read_staff_cnt_code
import re
def _staff_step(t):
    return ([b + k * int(m.group(1)) for rx, b, k in ((r'above\s*([1-9])', 8, 1), (r'([1-9])\s*(?:steps?\s*)?above', 8, 1), (r'below\s*([1-9])', 0, -1), (r'([1-9])\s*(?:steps?\s*)?below', 0, -1), (r'space\s*([1-4])', -1, 2), (r'([1-4])\w*\s+space', -1, 2), (r'line\s*([1-5])', -2, 2), (r'([1-5])\w*\s+line', -2, 2)) for m in [re.search(rx, str(t or '').strip().lower())] if m] + [None])[0]
def _ordered_box(q):
    try: v = [float(x) for x in list(q)[:4]]; return [min(v[0], v[2]), min(v[1], v[3]), max(v[0], v[2]), max(v[1], v[3])]
    except Exception: return None
def read_staff_cnt(heads, pos, n_notes):
    """Pair notehead boxes with their read positions, left to right, as staff steps."""
    head_boxes = [v for v in (_ordered_box(q) for q in ((heads.get('geometry') if isinstance(heads, dict) else heads) or [])) if v]; a = pos.get('answers') if isinstance(pos, dict) else None; answers = [str(x or '') for x in a] if isinstance(a, list) else ([str(pos.get('answer') or '')] if isinstance(pos, dict) else [str(pos or '')])
    if not head_boxes or len(answers) != len(head_boxes): return {'no_read': True, 'refused': True, 'reason': 'ring_and_reads_disagree', 'n_boxes': len(head_boxes), 'n_answers': len(answers)}
    order = sorted(range(len(head_boxes)), key=lambda i: 0.5 * (head_boxes[i][1] + head_boxes[i][3])); positions = [_staff_step(answers[i]) for i in order]
    if all(v is None for v in positions): return {'no_read': True, 'refused': True, 'reason': 'positions_unparsed', 'raw': [answers[i] for i in order]}
    return {'no_read': False, 'n_heads': len(head_boxes), 'pos_index': positions, 'raw': [answers[i] for i in order]}

# end of read_staff_cnt_code

# code: read_staff_pos_code
import re
def _staff_step(t):
    return ([b + k * int(m.group(1)) for rx, b, k in ((r'above\s*([1-9])', 8, 1), (r'([1-9])\s*(?:steps?\s*)?above', 8, 1), (r'below\s*([1-9])', 0, -1), (r'([1-9])\s*(?:steps?\s*)?below', 0, -1), (r'space\s*([1-4])', -1, 2), (r'([1-4])\w*\s+space', -1, 2), (r'line\s*([1-5])', -2, 2), (r'([1-5])\w*\s+line', -2, 2)) for m in [re.search(rx, str(t or '').strip().lower())] if m] + [None])[0]
def _ordered_box(q):
    try: v = [float(x) for x in list(q)[:4]]; return [min(v[0], v[2]), min(v[1], v[3]), max(v[0], v[2]), max(v[1], v[3])]
    except Exception: return None
def read_staff_pos(heads, pos, n_notes):
    """Pair notehead boxes with their read positions, left to right, as staff steps."""
    head_boxes = [v for v in (_ordered_box(q) for q in ((heads.get('geometry') if isinstance(heads, dict) else heads) or [])) if v]; a = pos.get('answers') if isinstance(pos, dict) else None; answers = [str(x or '') for x in a] if isinstance(a, list) else ([str(pos.get('answer') or '')] if isinstance(pos, dict) else [str(pos or '')])
    if not head_boxes or len(answers) != len(head_boxes): return {'no_read': True, 'refused': True, 'reason': 'ring_and_reads_disagree', 'n_boxes': len(head_boxes), 'n_answers': len(answers)}
    order = sorted(range(len(head_boxes)), key=lambda i: 0.5 * (head_boxes[i][1] + head_boxes[i][3])); positions = [_staff_step(answers[i]) for i in order]
    if all(v is None for v in positions): return {'no_read': True, 'refused': True, 'reason': 'positions_unparsed', 'raw': [answers[i] for i in order]}
    return {'no_read': False, 'n_heads': len(head_boxes), 'pos_index': positions, 'raw': [answers[i] for i in order]}

# end of read_staff_pos_code

# code: read_staff_form_code
import re
def _staff_step(t):
    return ([b + k * int(m.group(1)) for rx, b, k in ((r'above\s*([1-9])', 8, 1), (r'([1-9])\s*(?:steps?\s*)?above', 8, 1), (r'below\s*([1-9])', 0, -1), (r'([1-9])\s*(?:steps?\s*)?below', 0, -1), (r'space\s*([1-4])', -1, 2), (r'([1-4])\w*\s+space', -1, 2), (r'line\s*([1-5])', -2, 2), (r'([1-5])\w*\s+line', -2, 2)) for m in [re.search(rx, str(t or '').strip().lower())] if m] + [None])[0]
def _ordered_box(q):
    try: v = [float(x) for x in list(q)[:4]]; return [min(v[0], v[2]), min(v[1], v[3]), max(v[0], v[2]), max(v[1], v[3])]
    except Exception: return None
def read_staff_form(heads, pos, n_notes):
    """Pair notehead boxes with their read positions, left to right, as staff steps."""
    head_boxes = [v for v in (_ordered_box(q) for q in ((heads.get('geometry') if isinstance(heads, dict) else heads) or [])) if v]; a = pos.get('answers') if isinstance(pos, dict) else None; answers = [str(x or '') for x in a] if isinstance(a, list) else ([str(pos.get('answer') or '')] if isinstance(pos, dict) else [str(pos or '')])
    if not head_boxes or len(answers) != len(head_boxes): return {'no_read': True, 'refused': True, 'reason': 'ring_and_reads_disagree', 'n_boxes': len(head_boxes), 'n_answers': len(answers)}
    order = sorted(range(len(head_boxes)), key=lambda i: 0.5 * (head_boxes[i][1] + head_boxes[i][3])); positions = [_staff_step(answers[i]) for i in order]
    if all(v is None for v in positions): return {'no_read': True, 'refused': True, 'reason': 'positions_unparsed', 'raw': [answers[i] for i in order]}
    return {'no_read': False, 'n_heads': len(head_boxes), 'pos_index': positions, 'raw': [answers[i] for i in order]}

# end of read_staff_form_code
