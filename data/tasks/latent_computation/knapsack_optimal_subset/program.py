# shared code: code_1cd9796c0777

import itertools
import re


def _s(x):
    if isinstance(x, (list, tuple)):
        return " ".join(str(t) for t in x)
    return str(x if x is not None else "")


def read_tags(ans, letters):
    allowed = [str(l).strip().lower() for l in letters]
    if isinstance(ans, (list, tuple)):
        chunks = [str(t).lower() for t in ans]
    else:
        chunks = re.split(r"[;\n]+", _s(ans).lower())
    out = {}
    for chunk in chunks:
        m = re.search(r"(?<![a-z0-9])([a-z])(?![a-z])", chunk)
        nums = re.findall(r"\d+", chunk)
        if m and len(nums) >= 2 and m.group(1) in allowed and m.group(1) not in out:
            out[m.group(1)] = (int(nums[0]), int(nums[1]))
    return out if len(out) == len(allowed) else None


def read_letters(ans, letters):
    s = _s(ans).strip().lower()
    if not s:
        return None
    allowed = set(str(l).strip().lower() for l in letters)
    toks = [t for t in re.split(r"[^a-z0-9]+", s) if t]
    if any(t in ("none", "nothing", "empty") for t in toks):
        return []
    return sorted({t for t in toks if len(t) == 1 and t in allowed})


def knap_opt(items, cap):
    best, wits = -1, []
    for r in range(len(items) + 1):
        for combo in itertools.combinations(items, r):
            if sum(c[1] for c in combo) > cap:
                continue
            val = sum(c[2] for c in combo)
            if val > best:
                best, wits = val, [frozenset(c[0] for c in combo)]
            elif val == best:
                wits.append(frozenset(c[0] for c in combo))
    return best, wits


def check_basket_choice(tags_ans, cap_ans, inside_ans, outside_ans, letters):
    """Compare the basket's items with the best choice under the budget, from the tags read."""
    letters = [str(l).strip().lower() for l in letters]
    tags = read_tags(tags_ans, letters)
    cap_numbers = re.findall(r"\d+", _s(cap_ans))
    inside = read_letters(inside_ans, letters)
    outside = read_letters(outside_ans, letters)
    if tags is None or not cap_numbers or inside is None or outside is None or (not inside and not outside):
        return {"unreadable": True, "law": 0.0, "share": 0.0, "capacity": 0.0,
                "conservation": 0.0, "inside": None, "opt": None, "load": None, "cap": None}
    cap = int(cap_numbers[0])
    items = [(l, tags[l][0], tags[l][1]) for l in letters]
    best, optima = knap_opt(items, cap)
    optimal_sets = [set(w) for w in optima]
    inside_set, outside_set = set(inside), set(outside)
    load = sum(tags[l][0] for l in inside_set)
    law = 1.0 if inside_set in optimal_sets else 0.0
    share = max(sum(1.0 for l in letters if (l in inside_set) == (l in w)) / len(letters)
                for w in optimal_sets)
    conservation = 1.0 if ((inside_set | outside_set) == set(letters) and not (inside_set & outside_set)) else 0.0
    capacity = 1.0 if load <= cap else 0.0
    return {"unreadable": False, "law": law, "share": round(share, 4),
            "capacity": capacity, "conservation": conservation,
            "inside": sorted(inside_set), "opt": sorted(optimal_sets[0]), "load": load, "cap": cap,
            "best_value": best, "n_optima": len(optimal_sets)}

# end of code_1cd9796c0777

# code: cover_code

import difflib
import re


def _c(s):
    return re.sub(r"[^a-z0-9]", "", str(s).lower())


def line_coverage(txt, lines):
    s = _c(txt)
    lines = list(lines or [])
    if not lines:
        return 0.0
    ok = 0
    for ln in lines:
        t = _c(ln)
        if not t:
            ok += 1
            continue
        if t in s:
            ok += 1
            continue
        best, n = 0.0, len(t)
        step = max(1, n // 8)
        for i in range(0, max(1, len(s) - n + 1), step):
            best = max(best, difflib.SequenceMatcher(a=t, b=s[i:i + n + 3]).ratio())
        ok += 1 if best >= 0.82 else 0
    return round(ok / float(len(lines)), 4)


def _join(rr):
    if isinstance(rr, dict):
        parts = rr.get('answers') or []
    elif isinstance(rr, (list, tuple)):
        parts = list(rr)
    else:
        parts = [rr]
    keep = []
    for x in parts:
        s = str(x).strip() if x is not None else ''
        if s and s.lower() != 'none':
            keep.append(s)
    return ' '.join(keep)


def cover(reads, lines):
    """The share of expected lines found in the joined read text."""
    text = _join(reads)
    if not text:
        return {'unreadable': True, 'frac': 0.0, 'text': ''}
    return {'unreadable': False, 'frac': line_coverage(text, lines), 'text': text}

# end of cover_code

# code: split_zones_code
def split_zones(tags, zones):
    """Sort the tag letters into inside and outside the basket by the zone read for each."""
    import re
    tag_reads = list((tags or {}).get('answers') or [])
    zone_reads = list((zones or {}).get('answers') or [])
    inside, outside = [], []
    for tag, z in zip(tag_reads, zone_reads):
        m = re.search(r'(?<![A-Za-z])([A-Za-z])(?![A-Za-z])', str(tag))
        if m:
            (inside if str(z).strip().lower().startswith('in') else outside).append(m.group(1))
    return {'inside': sorted(inside), 'outside': sorted(outside), 'n': len(tag_reads)}

# end of split_zones_code
