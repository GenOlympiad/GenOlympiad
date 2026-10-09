# shared code: code_lamp_law


def _first_answer(x):
    if isinstance(x, dict):
        a = x.get("answers")
        a = list(a) if isinstance(a, (list, tuple)) else [None]
        return a[0] if a else None
    return x

def lamp_visibility_score(green_read, red_read, white_read, reference):
    """Score 1 when the green, red and white lamp reads match the arcs at this bearing."""
    def yn(x):
        s = str(x).strip().lower()
        if s.startswith("y") or s == "true":
            return True
        if s.startswith("n") or s == "false":
            return False
        return None

    green_read, red_read, white_read = _first_answer(green_read), _first_answer(red_read), _first_answer(white_read)
    bearing = float(reference.get("bearing_deg"))
    mast_half = float(reference.get("masthead_arc")) / 2.0
    side_half = float(reference.get("sidelight_arc"))
    stern_half = float(reference.get("sternlight_arc")) / 2.0
    on_stbd = str(reference.get("observer_side")).strip().lower() == "starboard"

    want_green = on_stbd and bearing <= side_half
    want_red = (not on_stbd) and bearing <= side_half
    want_white = (1 if bearing <= mast_half else 0) + (1 if bearing >= 180.0 - stern_half else 0)

    g, r = yn(green_read), yn(red_read)
    try:
        w = int(round(float(white_read)))
    except (TypeError, ValueError):
        w = None
    if g is None or r is None or w is None:
        return {"frac": None, "no_read": True,
                "verdict": "unreadable: green=%r red=%r white=%r" % (green_read, red_read, white_read)}
    hits = [g == want_green, r == want_red, w == want_white]
    return {"frac": 1.0 if all(hits) else 0.0,
            "n_ok": sum(1 for h in hits if h),
            "verdict": ("at %g deg on the %s side the arcs admit green=%s red=%s white lamps=%d; "
                        "the picture shows green=%s red=%s white lamps=%d -> %s"
                        % (bearing, reference.get("observer_side"), want_green, want_red, want_white,
                           g, r, w, "PASS" if all(hits) else "FAIL"))}

# end of code_lamp_law
