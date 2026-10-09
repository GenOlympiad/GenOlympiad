# shared code: map_code

import re

def normalise(s):
    return " ".join(str(s or "").lower().replace("-", " ").replace("*", "").replace("_", " ").split())

def _wb(tok, hay, start=0):
    m = re.compile(r"(?<![a-z0-9])%s(?![a-z0-9])" % re.escape(normalise(tok))).search(hay, start)
    return m.start() if m else -1

def match_listed_state(answer, table):
    """The one table state whose key phrases appear in the answer, else a refusal."""
    a = normalise(answer)
    matches = [s for s, keys in table.items() if any(normalise(k) in a for k in keys)]
    if len(matches) == 1:
        return {"state": matches[0], "refused": False}
    return {"state": None, "refused": True}

_NUMWORD = {"zero":0,"one":1,"two":2,"three":3,"four":4,"five":5,"six":6,"seven":7,"eight":8,
            "nine":9,"ten":10,"eleven":11,"twelve":12,"thirteen":13,"fourteen":14,"fifteen":15,
            "sixteen":16}

def count_of(answer):
    """The count the answer states, preferring a boxed or final-answer number."""
    a = normalise(answer)
    if not a:
        return {"state": None, "refused": True}
    W = r"\b(" + "|".join(sorted(_NUMWORD, key=len, reverse=True)) + r")\b"
    for pat in (r"\\boxed\s*\{\s*(\d{1,3})\s*\}",
                r"(?:final\s+answer|the\s+answer)\s*(?:is|:|=)?\s*\$?\s*(\d{1,3})(?![\d.])"):
        mm = list(re.finditer(pat, a))
        if mm:
            return {"state": int(mm[-1].group(1)), "refused": False}
    for pat in (r"(?:there\s+are|there\s+is|total\s+of|answer\s+is|count\s+is|"
                r"altogether[^\d]{0,12}|in\s+total[^\d]{0,12})\s*(\d{1,3})\b",
                r"\b(\d{1,3})\s+(?:separate|distinct|individual)\b"):
        mm = list(re.finditer(pat, a))
        if mm:
            return {"state": int(mm[-1].group(1)), "refused": False}
    mm = list(re.finditer(r"(?:there\s+are|there\s+is|total\s+of|answer\s+is|count\s+is)\s*" + W, a))
    if mm:
        return {"state": _NUMWORD[mm[-1].group(1)], "refused": False}
    stripped = re.sub(r"(?:(?<=\s)|^)\d{1,2}\s*[.)]\s+(?=[a-z*])", " ", a)
    nums = [int(x) for x in re.findall(r"(?<![\d.])(\d{1,3})(?![\d.])", stripped)]
    words = [_NUMWORD[w] for w in re.findall(W, stripped)]
    if nums:
        return {"state": (nums[-1] if len(set(nums)) > 1 else nums[0]), "refused": False}
    if words:
        return {"state": (words[-1] if len(set(words)) > 1 else words[0]), "refused": False}
    return {"state": None, "refused": True}

def _seq_hit(a, want):
    pos = -1
    for tok in want:
        alts = [tok] if isinstance(tok, str) else list(tok)
        best = None
        for one in alts:
            i = _wb(one, a, pos + 1)
            if i >= 0 and (best is None or i < best):
                best = i
        if best is None:
            return False
        pos = best
    return True

def seq_of(ans, forms):
    a = normalise(ans)
    if not a:
        return {"state": None, "refused": True}
    hit = [s for s, want in forms.items() if _seq_hit(a, want)]
    if len(hit) == 1:
        return {"state": hit[0], "refused": False}
    return {"state": None, "refused": True}

T_PART2 = {'square_flag': ['square', 'rectangular', 'oblong', 'four sided'], 'pennant': ['triangular', 'pennant', 'tapering', 'triangle']}

# end of map_code
