# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# code: norm_winding_code
def winding_score(answer, reference):
    """Score 1 when the read turning direction matches the reference direction."""
    s=str(answer).lower().replace('-','').replace(' ','')
    if 'counter' in s or 'anti' in s or 'ccw' in s:
        winding='counterclockwise'
    elif 'clockwise' in s or s=='cw':
        winding='clockwise'
    else:
        winding='?'
    return {'frac': 1.0 if winding==reference['winding_target'] else 0.0}

# end of norm_winding_code

# code: monotonic_code
def steps_in_order_score(numbers_read, reference):
    """Score 1 when the step numbers read around the stair run in order one way."""
    import re
    n=int(reference['n'])
    nums=[int(x) for x in re.findall(r'\d+', str(numbers_read))]
    seen=[]; seen_set=set()
    for x in nums:
        if 1<=x<=n and x not in seen_set:
            seen.append(x); seen_set.add(x)
    if len(seen)<max(3,n-1):
        return {'frac':0.0,'no_read':True}
    if 1 in seen:
        i=seen.index(1); seen=seen[i:]+seen[:i]
    diffs=[(b-a)%n for a,b in zip(seen, seen[1:])]
    in_order=all(d==1 for d in diffs) or all(d==(n-1) for d in diffs)
    return {'frac': 1.0 if in_order else 0.0, 'no_read': False}

# end of monotonic_code
