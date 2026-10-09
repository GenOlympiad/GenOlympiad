# code: helpers
from genolympiad.task_helpers import count_listed_items
# end of helpers

# shared code: code_927dd4d4c8c4
import re

_COL = {"black": "black", "yellow": "yellow", "gold": "yellow", "amber": "yellow"}


def _answers(r):
    if isinstance(r, dict):
        a = r.get("answers")
        if isinstance(a, list):
            return [str(x or "") for x in a]
        return [str(r.get("answer") or "")]
    return [str(r or "")]


def _updown(t):
    t = str(t or "").strip().lower()
    m = re.search(r"\b(up|upward|upwards|upright|skyward)\b", t)
    n = re.search(r"\b(down|downward|downwards|inverted)\b", t)
    if m and n:
        return "up" if m.start() < n.start() else "down"
    if m:
        return "up"
    if n:
        return "down"
    return None


def _bands(t):
    t = str(t or "").strip().lower()
    seq = []
    for w in re.findall(r"[a-z]+", t):
        c = _COL.get(w)
        if c and (not seq or seq[-1] != c):
            seq.append(c)
    return seq


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


def read_topmark_and_bands(topmark, cones, bands):
    """Read the upper and lower cone directions and the band colours, refusing if unparsed."""
    cone_boxes = _boxes(topmark)
    answers = _answers(cones)
    if len(cone_boxes) != 2 or len(answers) != 2:
        return {"no_read": True, "reason": "topmark_not_two_cones",
                "n_boxes": len(cone_boxes), "n_answers": len(answers)}
    order = sorted(range(2), key=lambda i: 0.5 * (cone_boxes[i][0] + cone_boxes[i][2]))
    cone_dirs = [_updown(answers[i]) for i in order]
    band_colours = _bands((_answers(bands) or [""])[0])
    if cone_dirs[0] is None or cone_dirs[1] is None or len(band_colours) < 2:
        return {"no_read": True, "cones": cone_dirs, "bands": band_colours,
                "reason": "cones_unparsed" if (cone_dirs[0] is None or cone_dirs[1] is None) else "bands_unparsed"}
    return {"no_read": False, "cones": cone_dirs, "bands": band_colours}


def readable_frac(m):
    """Score 1 when both topmark cones and the bands were read, else 0."""
    return 0.0 if m.get("no_read") else 1.0


def cones_frac(m, want):
    """Score 1 when the read cone directions equal the reference ones, upper then lower."""
    if m.get("no_read"):
        return 0.0
    got = [str(v).strip().lower() for v in m["cones"]]
    return 1.0 if got == [str(v).strip().lower() for v in want] else 0.0


def bands_frac(m, want):
    """Score 1 when the read band colours equal the reference bands in order."""
    if m.get("no_read"):
        return 0.0
    got = [str(v).strip().lower() for v in m["bands"]]
    return 1.0 if got == [str(v).strip().lower() for v in want] else 0.0


def both_halves_frac(m, want_cones, want_bands):
    """Score 1 when both the cones and the bands match the reference."""
    if m.get("no_read"):
        return 0.0
    return 1.0 if (cones_frac(m, want_cones) == 1.0 and bands_frac(m, want_bands) == 1.0) else 0.0


def band_structure_frac(m, want):
    """The share of band colours that match the reference position by position."""
    if m.get("no_read"):
        return 0.0
    got = [str(v).strip().lower() for v in m["bands"]]
    want = [str(v).strip().lower() for v in want]
    matched = sum(1 for i, v in enumerate(want) if i < len(got) and got[i] == v)
    return round(matched / float(max(len(want), len(got), 1)), 4)

# end of code_927dd4d4c8c4

# code: topmark_pair_for_readable_code

import re
_WORD_N = {"none": 0, "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5}; _one = lambda node: (list((node or {}).get("answers") or []) or [None])[0]
def _count(t):
    s = str(t if t is not None else "").strip().lower(); d = re.findall(r"[0-9]+", s)
    return int(d[0]) if d else next((_WORD_N[w] for w in re.findall(r"[a-z]+", s) if w in _WORD_N), None)
def topmark_pair_for_readable(tmk, upper, lower, count):
    """Split the boxed topmark into upper and lower halves holding the two cone reads."""
    upper_cone, lower_cone, cone_count = _one(upper), _one(lower), _one(count)
    if upper_cone is None or lower_cone is None or cone_count is None: return {"no_read": True, "refused": True, "reason": "a topmark crop came back blank"}
    if not (boxes := [b for b in ((tmk or {}).get("geometry") or []) if b and len(b) >= 4]): return {"no_read": True, "refused": True, "reason": "the topmark was never boxed"}
    if (n := _count(cone_count)) != 2: return {"no_read": True, "n_cones": n, "reason": "the mast carries %s cone shapes, not two" % n}
    b = [float(v) for v in boxes[0][:4]]; ylo, yhi = min(b[0], b[2]), max(b[0], b[2]); xlo, xhi = min(b[1], b[3]), max(b[1], b[3]); ymid = 0.5 * (ylo + yhi)
    return {"no_read": False, "n_cones": 2, "tm": {"geometry": [[ylo, xlo, ymid, xhi], [ymid, xlo, yhi, xhi]]}, "cn": {"answers": [upper_cone, lower_cone]}, "verdict": "topmark cones read upper=%s lower=%s" % (upper_cone, lower_cone)}

# end of topmark_pair_for_readable_code

# code: hold_readable_code
def hold_readable(m):
    """Hold the read back as unusable when the cones, or all the bands, could not be parsed."""
    result = dict(m) if isinstance(m, dict) else {'no_read': True, 'reason': 'cones_unparsed'}
    reason = result.get('reason')
    if result.get('no_read') and (reason == 'cones_unparsed' or (reason == 'bands_unparsed' and not result.get('bands'))):
        result['refused'] = True
    return result

# end of hold_readable_code

# code: topmark_pair_for_cone_orientation_code

import re
_WORD_N = {"none": 0, "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5}; _one = lambda node: (list((node or {}).get("answers") or []) or [None])[0]
def _count(t):
    s = str(t if t is not None else "").strip().lower(); d = re.findall(r"[0-9]+", s)
    return int(d[0]) if d else next((_WORD_N[w] for w in re.findall(r"[a-z]+", s) if w in _WORD_N), None)
def topmark_pair_for_cone_orientation(tmk, upper, lower, count):
    """Split the boxed topmark into upper and lower halves holding the two cone reads."""
    upper_cone, lower_cone, cone_count = _one(upper), _one(lower), _one(count)
    if upper_cone is None or lower_cone is None or cone_count is None: return {"no_read": True, "refused": True, "reason": "a topmark crop came back blank"}
    if not (boxes := [b for b in ((tmk or {}).get("geometry") or []) if b and len(b) >= 4]): return {"no_read": True, "refused": True, "reason": "the topmark was never boxed"}
    if (n := _count(cone_count)) != 2: return {"no_read": True, "n_cones": n, "reason": "the mast carries %s cone shapes, not two" % n}
    b = [float(v) for v in boxes[0][:4]]; ylo, yhi = min(b[0], b[2]), max(b[0], b[2]); xlo, xhi = min(b[1], b[3]), max(b[1], b[3]); ymid = 0.5 * (ylo + yhi)
    return {"no_read": False, "n_cones": 2, "tm": {"geometry": [[ylo, xlo, ymid, xhi], [ymid, xlo, yhi, xhi]]}, "cn": {"answers": [upper_cone, lower_cone]}, "verdict": "topmark cones read upper=%s lower=%s" % (upper_cone, lower_cone)}

# end of topmark_pair_for_cone_orientation_code

# code: hold_cone_orientation_code
def hold_cone_orientation(m):
    """Hold the read back as unusable when the cones, or all the bands, could not be parsed."""
    result = dict(m) if isinstance(m, dict) else {'no_read': True, 'reason': 'cones_unparsed'}
    reason = result.get('reason')
    if result.get('no_read') and (reason == 'cones_unparsed' or (reason == 'bands_unparsed' and not result.get('bands'))):
        result['refused'] = True
    return result

# end of hold_cone_orientation_code

# code: topmark_pair_for_band_sequence_code

import re
_WORD_N = {"none": 0, "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5}; _one = lambda node: (list((node or {}).get("answers") or []) or [None])[0]
def _count(t):
    s = str(t if t is not None else "").strip().lower(); d = re.findall(r"[0-9]+", s)
    return int(d[0]) if d else next((_WORD_N[w] for w in re.findall(r"[a-z]+", s) if w in _WORD_N), None)
def topmark_pair_for_band_sequence(tmk, upper, lower, count):
    """Split the boxed topmark into upper and lower halves holding the two cone reads."""
    upper_cone, lower_cone, cone_count = _one(upper), _one(lower), _one(count)
    if upper_cone is None or lower_cone is None or cone_count is None: return {"no_read": True, "refused": True, "reason": "a topmark crop came back blank"}
    if not (boxes := [b for b in ((tmk or {}).get("geometry") or []) if b and len(b) >= 4]): return {"no_read": True, "refused": True, "reason": "the topmark was never boxed"}
    if (n := _count(cone_count)) != 2: return {"no_read": True, "n_cones": n, "reason": "the mast carries %s cone shapes, not two" % n}
    b = [float(v) for v in boxes[0][:4]]; ylo, yhi = min(b[0], b[2]), max(b[0], b[2]); xlo, xhi = min(b[1], b[3]), max(b[1], b[3]); ymid = 0.5 * (ylo + yhi)
    return {"no_read": False, "n_cones": 2, "tm": {"geometry": [[ylo, xlo, ymid, xhi], [ymid, xlo, yhi, xhi]]}, "cn": {"answers": [upper_cone, lower_cone]}, "verdict": "topmark cones read upper=%s lower=%s" % (upper_cone, lower_cone)}

# end of topmark_pair_for_band_sequence_code

# code: hold_band_sequence_code
def hold_band_sequence(m):
    """Hold the read back as unusable when the cones, or all the bands, could not be parsed."""
    result = dict(m) if isinstance(m, dict) else {'no_read': True, 'reason': 'cones_unparsed'}
    reason = result.get('reason')
    if result.get('no_read') and (reason == 'cones_unparsed' or (reason == 'bands_unparsed' and not result.get('bands'))):
        result['refused'] = True
    return result

# end of hold_band_sequence_code

# code: topmark_pair_for_both_halves_code

import re
_WORD_N = {"none": 0, "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5}; _one = lambda node: (list((node or {}).get("answers") or []) or [None])[0]
def _count(t):
    s = str(t if t is not None else "").strip().lower(); d = re.findall(r"[0-9]+", s)
    return int(d[0]) if d else next((_WORD_N[w] for w in re.findall(r"[a-z]+", s) if w in _WORD_N), None)
def topmark_pair_for_both_halves(tmk, upper, lower, count):
    """Split the boxed topmark into upper and lower halves holding the two cone reads."""
    upper_cone, lower_cone, cone_count = _one(upper), _one(lower), _one(count)
    if upper_cone is None or lower_cone is None or cone_count is None: return {"no_read": True, "refused": True, "reason": "a topmark crop came back blank"}
    if not (boxes := [b for b in ((tmk or {}).get("geometry") or []) if b and len(b) >= 4]): return {"no_read": True, "refused": True, "reason": "the topmark was never boxed"}
    if (n := _count(cone_count)) != 2: return {"no_read": True, "n_cones": n, "reason": "the mast carries %s cone shapes, not two" % n}
    b = [float(v) for v in boxes[0][:4]]; ylo, yhi = min(b[0], b[2]), max(b[0], b[2]); xlo, xhi = min(b[1], b[3]), max(b[1], b[3]); ymid = 0.5 * (ylo + yhi)
    return {"no_read": False, "n_cones": 2, "tm": {"geometry": [[ylo, xlo, ymid, xhi], [ymid, xlo, yhi, xhi]]}, "cn": {"answers": [upper_cone, lower_cone]}, "verdict": "topmark cones read upper=%s lower=%s" % (upper_cone, lower_cone)}

# end of topmark_pair_for_both_halves_code

# code: hold_both_halves_code
def hold_both_halves(m):
    """Hold the read back as unusable when the cones, or all the bands, could not be parsed."""
    result = dict(m) if isinstance(m, dict) else {'no_read': True, 'reason': 'cones_unparsed'}
    reason = result.get('reason')
    if result.get('no_read') and (reason == 'cones_unparsed' or (reason == 'bands_unparsed' and not result.get('bands'))):
        result['refused'] = True
    return result

# end of hold_both_halves_code

# code: topmark_pair_for_band_structure_code

import re
_WORD_N = {"none": 0, "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5}; _one = lambda node: (list((node or {}).get("answers") or []) or [None])[0]
def _count(t):
    s = str(t if t is not None else "").strip().lower(); d = re.findall(r"[0-9]+", s)
    return int(d[0]) if d else next((_WORD_N[w] for w in re.findall(r"[a-z]+", s) if w in _WORD_N), None)
def topmark_pair_for_band_structure(tmk, upper, lower, count):
    """Split the boxed topmark into upper and lower halves holding the two cone reads."""
    upper_cone, lower_cone, cone_count = _one(upper), _one(lower), _one(count)
    if upper_cone is None or lower_cone is None or cone_count is None: return {"no_read": True, "refused": True, "reason": "a topmark crop came back blank"}
    if not (boxes := [b for b in ((tmk or {}).get("geometry") or []) if b and len(b) >= 4]): return {"no_read": True, "refused": True, "reason": "the topmark was never boxed"}
    if (n := _count(cone_count)) != 2: return {"no_read": True, "n_cones": n, "reason": "the mast carries %s cone shapes, not two" % n}
    b = [float(v) for v in boxes[0][:4]]; ylo, yhi = min(b[0], b[2]), max(b[0], b[2]); xlo, xhi = min(b[1], b[3]), max(b[1], b[3]); ymid = 0.5 * (ylo + yhi)
    return {"no_read": False, "n_cones": 2, "tm": {"geometry": [[ylo, xlo, ymid, xhi], [ymid, xlo, yhi, xhi]]}, "cn": {"answers": [upper_cone, lower_cone]}, "verdict": "topmark cones read upper=%s lower=%s" % (upper_cone, lower_cone)}

# end of topmark_pair_for_band_structure_code

# code: hold_band_structure_code
def hold_band_structure(m):
    """Hold the read back as unusable when the cones, or all the bands, could not be parsed."""
    result = dict(m) if isinstance(m, dict) else {'no_read': True, 'reason': 'cones_unparsed'}
    reason = result.get('reason')
    if result.get('no_read') and (reason == 'cones_unparsed' or (reason == 'bands_unparsed' and not result.get('bands'))):
        result['refused'] = True
    return result

# end of hold_band_structure_code
