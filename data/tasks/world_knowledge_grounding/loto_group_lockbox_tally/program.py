# shared code: map_code

import re

def normalise(s):
    return " ".join(str(s or "").lower().replace("-", " ").replace("*", "").replace("_", " ").split())

def _wb(tok, hay, start=0):
    m = re.compile(r"(?<![a-z0-9])%s(?![a-z0-9])" % re.escape(normalise(tok))).search(hay, start)
    return m.start() if m else -1

def match_listed_state(ans, table):
    a = normalise(ans)
    hit = [s for s, keys in table.items() if any(normalise(k) in a for k in keys)]
    if len(hit) == 1:
        return {"state": hit[0], "refused": False}
    return {"state": None, "refused": True}

_NUMWORD = {"zero":0,"one":1,"two":2,"three":3,"four":4,"five":5,"six":6,"seven":7,"eight":8,
            "nine":9,"ten":10,"eleven":11,"twelve":12,"thirteen":13,"fourteen":14,"fifteen":15,
            "sixteen":16}

def count_of(ans):
    a = normalise(ans)
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


def locks_match_tags(a_locks, a_tags):
    """Whether the lock count on the hasp equals the tag count, with at least two of each."""
    lock_read = count_of(a_locks)
    tag_read = count_of(a_tags)
    if lock_read["refused"] or tag_read["refused"] or lock_read["state"] is None or tag_read["state"] is None:
        return {"state": None, "refused": True, "counts": [lock_read["state"], tag_read["state"]]}
    locks, tags = int(lock_read["state"]), int(tag_read["state"])
    if locks != tags:
        return {"state": "mismatch", "refused": False, "counts": [locks, tags]}
    if locks < 2:
        return {"state": "too_few", "refused": False, "counts": [locks, tags]}
    return {"state": "match", "refused": False, "counts": [locks, tags]}



def rack_count(a_rack):
    """The count of items on the rack stated in the answer, or a refusal."""
    return count_of(a_rack)

# end of map_code
