# code: count_units_code

def count_confirmed_rays(bx, cf):

    """Count the boxed candidates confirmed as one whole ray, merging heavy overlaps."""
    def yes(a):
        return str(a).strip().lower().startswith('y')

    def iou(a, b):
        ay0, ax0, ay1, ax1 = [float(v) for v in a[:4]]
        by0, bx0, by1, bx1 = [float(v) for v in b[:4]]
        ih = max(0.0, min(ay1, by1) - max(ay0, by0))
        iw = max(0.0, min(ax1, bx1) - max(ax0, bx0))
        inter = ih * iw
        ua = max(0.0, ay1 - ay0) * max(0.0, ax1 - ax0)
        ub = max(0.0, by1 - by0) * max(0.0, bx1 - bx0)
        den = ua + ub - inter
        return inter / den if den > 0 else 0.0

    def confirmed(bx, cf, fold=0.6):
        geo = (bx or {}).get('geometry') or []
        ans = (cf or {}).get('answers') or []
        kept, idx = [], []
        for i in range(min(len(geo), len(ans))):
            if not yes(ans[i]):
                continue
            if fold is not None and any(iou(geo[i], k) > fold for k in kept):
                continue
            kept.append(geo[i])
            idx.append(i)
        return kept, idx

    kept, _ = confirmed(bx, cf)
    asked = len((cf or {}).get('answers') or [])
    return {'n': len(kept), 'asked': asked, 'boxes': kept,
            'verdict': '%d of the %d framed candidates were confirmed to hold exactly one whole '
                       'unit, so the counted number is %d' % (len(kept), asked, len(kept))}

# end of count_units_code

# code: chk_code
def count_matches_reference(answer, want):
    """Score 1 if the number in the answer equals the expected count."""
    import re
    if answer is None or isinstance(answer, dict):
        return 0.0
    t = str(answer).strip().lower()
    words = {'zero':0,'one':1,'two':2,'three':3,'four':4,'five':5,'six':6,'seven':7,'eight':8,'nine':9,'ten':10,'eleven':11,'twelve':12}
    m = re.search(r'-?\d+', t)
    n = int(m.group(0)) if m else None
    if n is None:
        for w,v in words.items():
            if w in t: n = v; break
    return 1.0 if (n is not None and n == int(want)) else 0.0

# end of chk_code
