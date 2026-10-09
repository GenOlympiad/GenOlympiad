# code: mono_ok_code

def room_numbers_increase(walk_seq, reference):
    """1 if the right number of room numbers is read along the walk and each one rises."""
    try:
        vals = [int(round(float(x))) for x in walk_seq]
    except Exception:
        return {"fmono": 0.0, "read_n": 0}
    n_expect = int(reference["n_doors"])
    if len(vals) != n_expect:
        return {"fmono": 0.0, "read_n": len(vals)}
    increasing = all(vals[i + 1] > vals[i] for i in range(len(vals) - 1))
    return {"fmono": 1.0 if increasing else 0.0, "read_n": len(vals)}

# end of mono_ok_code
