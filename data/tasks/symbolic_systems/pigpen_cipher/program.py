# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# shared code: code_33bd3dd6b054

def score_decoded_word(decoded, reference):
    """Score 1 when the decoded word equals the reference word; also give the per-glyph share."""
    target = reference["target"]
    letters = list(decoded.get("letters") or [])
    word = "".join(letters)
    n = len(target)
    correct = sum(1 for i in range(n) if i < len(letters) and letters[i] == target[i])
    return {"word": word, "frac": 1.0 if word == target else 0.0,
            "per_glyph": round(correct / n, 4) if n else 0.0}

# end of code_33bd3dd6b054

# shared code: code_48b611b5b451

import re


def _psig(ans):
    if ans is None:
        return None
    s = str(ans).lower()
    no_dot = ("no dot" in s) or ("without a dot" in s) or ("no-dot" in s)
    dot = ("dot" in s) and not no_dot
    if any(k in s for k in ("wedge", "v-shape", "v shape", "chevron", "triangle", "arrow")):
        d = None
        if re.search(r"open\w*\s*(up|top|upward)", s) or "points down" in s:
            d = "up"
        elif re.search(r"open\w*\s*(down|bottom|downward)", s) or "points up" in s:
            d = "down"
        elif re.search(r"open\w*\s*left", s) or "points right" in s:
            d = "left"
        elif re.search(r"open\w*\s*right", s) or "points left" in s:
            d = "right"
        if d is None:
            return None
        return "wedge:" + d + ("|dot" if dot else "")
    sides = []
    if re.search(r"\btop\b", s):
        sides.append("T")
    if re.search(r"\bbottom\b", s):
        sides.append("B")
    if re.search(r"\bleft\b", s):
        sides.append("L")
    if re.search(r"\bright\b", s):
        sides.append("R")
    if not sides:
        return None
    return "|".join(sorted(sides)) + ("|dot" if dot else "")


def _pl(sig, table):
    for L, ss in table.items():
        if ss == sig:
            return L
    return None


def decode_glyphs(glyph_reads, reference):
    """Turn each read glyph shape into its letter through the reference table, '?' if unknown."""
    answers = glyph_reads.get("answers") if isinstance(glyph_reads, dict) else glyph_reads
    n = int(reference["n_letters"])
    table = reference["sig_table"]
    if not answers:
        return {"letters": [], "unreadable": True}
    letters = [(_pl(_psig(a), table) or "?") for a in list(answers)[:n]]
    while len(letters) < n:
        letters.append("?")
    return {"letters": letters, "unreadable": (not any(L != "?" for L in letters))}

# end of code_48b611b5b451

# shared code: code_c184151f6e8a

def order_glyph_boxes(geometry, n):
    """Order the found glyph boxes, refusing unless exactly the expected number were found."""
    n = int(n)
    if not geometry or not isinstance(geometry, (list, tuple)):
        return {"boxes": None, "no_read": True}
    boxes = [[float(v) for v in g[:4]] for g in geometry
         if isinstance(g, (list, tuple)) and len(g) >= 4]
    if len(boxes) != n:
        return {"boxes": None, "no_read": True, "n_found": len(boxes)}
    boxes.sort(key=lambda z: z[1])
    return {"boxes": boxes, "no_read": False, "n_found": len(boxes)}

# end of code_c184151f6e8a
