# code: law_code


def _one(x):
    if isinstance(x, dict):
        a = x.get("answers") or [None]
        return a[0]
    return x


def overtake_side_score(pair_answer, arrow_answer, car_answer, reference):
    """Score 1 when the broken line and the overtaking car are on the side the arrow allows."""
    def pair(x):
        s = str(x).strip().lower()
        for k in ("neither", "both", "left", "right"):
            if k in s:
                return k
        return ""

    def side(x):
        s = str(x).strip().lower()
        if "left" in s:
            return "left"
        if "right" in s:
            return "right"
        return ""

    def vert(x):
        s = str(x).strip().lower()
        if "top" in s or s.startswith("up"):
            return "top"
        if "bottom" in s or s.startswith("down"):
            return "bottom"
        return ""

    B, A, C = pair(_one(pair_answer)), vert(_one(arrow_answer)), side(_one(car_answer))
    if not B or not A or not C:
        return {"frac": None, "no_read": True,
                "verdict": "unreadable: pair=%r arrow=%r car=%r" % (pair_answer, arrow_answer, car_answer)}

    may_pass = str(reference.get("overtaking_travel")).strip().lower()
    over_side = "left" if A == may_pass else "right"
    symmetric = B in ("both", "neither")
    ok_lines = (B == over_side)
    ok_car = (C == over_side)
    hits = [ok_lines, ok_car]
    return {"frac": 1.0 if all(hits) else 0.0,
            "symmetric_default": symmetric,
            "crash": "symmetric line pair (the default)" if symmetric else "",
            "verdict": ("the %s lane's arrow points to the %s, so that lane may overtake and the "
                        "broken line must be the %s one of the pair; the pair reads %r and the "
                        "overtaking car is mostly on the %s -> %s%s"
                        % (over_side, A, over_side, B, C,
                           "PASS" if all(hits) else "FAIL",
                           " [both lines the same = the symmetric-double-line default]"
                           if symmetric else ""))}

# end of law_code
