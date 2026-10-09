# shared code: code_a54610831234



def jets(nodes, colours):
    boxes = []
    for i, c in enumerate(colours or []):
        node = nodes[i] if i < len(nodes) else None
        g = (node or {}).get("geometry") or []
        b = None
        for cand in g:
            try:
                y0, x0, y1, x1 = [float(v) for v in cand[:4]]
            except Exception:
                continue
            if x1 - x0 <= 0 or y1 - y0 <= 0:
                continue
            if b is None or (x1 - x0) > (b[3] - b[1]):
                b = [y0, x0, y1, x1]
        boxes.append(b)
    out = {"n_boxes": sum(1 for b in boxes if b), "reach": [], "n_found": 0, "spread": None,
           "argmax": None, "x_face": None,
           "boxes": [None if not b else [round(v, 1) for v in b] for b in boxes]}
    lefts = sorted(b[1] for b in boxes if b)
    if not lefts:
        out["reach"] = [None for _ in (colours or [])]
        return out
    n = len(lefts)
    x_face = lefts[n // 2] if n % 2 else (lefts[n // 2 - 1] + lefts[n // 2]) / 2.0
    out["x_face"] = round(x_face, 2)
    reach = []
    for b in boxes:
        if not b:
            reach.append(None)
            continue
        r = b[3] - x_face
        reach.append(round(r, 2) if r > 0 else None)
    out["reach"] = reach
    good = [(c, r) for c, r in zip(colours, reach) if r]
    out["n_found"] = len(good)
    if len(good) >= 2:
        vals = [r for _, r in good]
        out["spread"] = round(max(vals) / min(vals), 4)
        out["argmax"] = str(max(good, key=lambda t: t[1])[0]).lower()
    return out


def read_reach_spread(nodes, colours):
    """Measure each stream's reach; spread and furthest stay undefined if one is missing."""
    measured = jets(nodes, colours)
    n_colours = len(colours or [])
    if measured["n_found"] < n_colours:
        measured["spread"] = None
        measured["argmax"] = None
        measured["verdict"] = ("streams measured %d of %d -- with a stream missing the spread and the "
                        "furthest-stream identity are undefined, not smaller" % (measured["n_found"], n_colours))
    else:
        measured["verdict"] = ("reaches (per-mille, from the vessel face) %s, spread %s, furthest %s"
                        % (measured["reach"], measured["spread"], measured["argmax"]))
    return measured

# end of code_a54610831234

# shared code: code_d80888d99caa
def pad(colours):
    cs = [str(c) for c in (colours or [])] or ["coloured"]
    out = {}
    for i in range(6):
        out["c%d" % i] = cs[i] if i < len(cs) else cs[-1]
    return out

# end of code_d80888d99caa

# code: jet_nodes_for_readable_code
_SYN = {"purple": ("purple", "violet", "magenta", "mauve", "lilac", "indigo"), "blue": ("blue", "cyan", "teal", "turquoise", "azure"), "green": ("green",), "red": ("red", "crimson", "scarlet"), "yellow": ("yellow", "gold", "amber"), "orange": ("orange",), "pink": ("pink", "rose"), "brown": ("brown", "tan"), "black": ("black",), "white": ("white",), "grey": ("grey", "gray", "silver")}
def _says(answer, colour): a = str(answer if answer is not None else "").strip().lower(); c = str(colour or "").strip().lower(); return bool(a) and any(w and w in a for w in _SYN.get(c, (c,)))
def jet_nodes_for_readable(vessel_read, landing_read, colour_reads, colours):
    """For each colour, keep the furthest landing mark past the vessel face and its reach."""
    vessel_boxes = [b for b in ((vessel_read or {}).get("geometry") or []) if b and len(b) >= 4]; marks = [b for b in ((landing_read or {}).get("geometry") or []) if b and len(b) >= 4]; answers = list((colour_reads or {}).get("answers") or []); colour_list = list(colours or [])
    out = {"nodes": [{"geometry": []} for _ in colour_list], "x_face": None, "n_marks": len(marks), "reach": [None for _ in colour_list], "said": [], "no_colour_read": False, "refused": False}
    if marks and (not answers or all(a is None for a in answers)): out.update({"no_colour_read": True, "refused": True, "reason": "no landing mark could be given a colour"}); return out
    if not vessel_boxes: return out
    face = max(max(float(b[1]), float(b[3])) for b in vessel_boxes); out["x_face"] = round(face, 2)
    seen = [{"x": (min(float(b[1]), float(b[3])) + max(float(b[1]), float(b[3]))) / 2.0, "y0": min(float(b[0]), float(b[2])), "y1": max(float(b[0]), float(b[2])), "said": answers[i] if i < len(answers) else None} for i, b in enumerate(marks)]; out["said"] = [m["said"] for m in seen]
    picks = [max([m for m in seen if m["x"] > face and _says(m["said"], c)] or [None], key=lambda z: z["x"] if z else -1.0) for c in colour_list]
    out["nodes"] = [{"geometry": [[m["y0"], face, max(m["y0"] + 1.0, m["y1"]), m["x"]]]} if m else {"geometry": []} for m in picks]; out["reach"] = [round(m["x"] - face, 2) if m else None for m in picks]
    return out
# end of jet_nodes_for_readable_code

# code: f_code



def jets(nodes, colours):
    boxes = []
    for i, c in enumerate(colours or []):
        node = nodes[i] if i < len(nodes) else None
        g = (node or {}).get("geometry") or []
        b = None
        for cand in g:
            try:
                y0, x0, y1, x1 = [float(v) for v in cand[:4]]
            except Exception:
                continue
            if x1 - x0 <= 0 or y1 - y0 <= 0:
                continue
            if b is None or (x1 - x0) > (b[3] - b[1]):
                b = [y0, x0, y1, x1]
        boxes.append(b)
    out = {"n_boxes": sum(1 for b in boxes if b), "reach": [], "n_found": 0, "spread": None,
           "argmax": None, "x_face": None,
           "boxes": [None if not b else [round(v, 1) for v in b] for b in boxes]}
    lefts = sorted(b[1] for b in boxes if b)
    if not lefts:
        out["reach"] = [None for _ in (colours or [])]
        return out
    n = len(lefts)
    x_face = lefts[n // 2] if n % 2 else (lefts[n // 2 - 1] + lefts[n // 2]) / 2.0
    out["x_face"] = round(x_face, 2)
    reach = []
    for b in boxes:
        if not b:
            reach.append(None)
            continue
        r = b[3] - x_face
        reach.append(round(r, 2) if r > 0 else None)
    out["reach"] = reach
    good = [(c, r) for c, r in zip(colours, reach) if r]
    out["n_found"] = len(good)
    if len(good) >= 2:
        vals = [r for _, r in good]
        out["spread"] = round(max(vals) / min(vals), 4)
        out["argmax"] = str(max(good, key=lambda t: t[1])[0]).lower()
    return out


def streams_found_score(nodes, colours, n_required):
    """Score 1 when every required colour has its own confirmed stream."""
    measured = jets(nodes, colours)
    ok = 1.0 if int(measured["n_found"]) >= int(n_required) else 0.0
    return {"frac": ok, "boxes": measured["boxes"],
            "verdict": "streams confirmed under their own colour %d vs required %d -> frac %s"
            % (measured["n_found"], int(n_required), ok)}

# end of f_code

# code: jet_nodes_for_ratio_code
_SYN = {"purple": ("purple", "violet", "magenta", "mauve", "lilac", "indigo"), "blue": ("blue", "cyan", "teal", "turquoise", "azure"), "green": ("green",), "red": ("red", "crimson", "scarlet"), "yellow": ("yellow", "gold", "amber"), "orange": ("orange",), "pink": ("pink", "rose"), "brown": ("brown", "tan"), "black": ("black",), "white": ("white",), "grey": ("grey", "gray", "silver")}
def _says(answer, colour): a = str(answer if answer is not None else "").strip().lower(); c = str(colour or "").strip().lower(); return bool(a) and any(w and w in a for w in _SYN.get(c, (c,)))
def jet_nodes_for_ratio(vessel_read, landing_read, colour_reads, colours):
    """For each colour, keep the furthest landing mark past the vessel face and its reach."""
    vessel_boxes = [b for b in ((vessel_read or {}).get("geometry") or []) if b and len(b) >= 4]; marks = [b for b in ((landing_read or {}).get("geometry") or []) if b and len(b) >= 4]; answers = list((colour_reads or {}).get("answers") or []); colour_list = list(colours or [])
    out = {"nodes": [{"geometry": []} for _ in colour_list], "x_face": None, "n_marks": len(marks), "reach": [None for _ in colour_list], "said": [], "no_colour_read": False, "refused": False}
    if marks and (not answers or all(a is None for a in answers)): out.update({"no_colour_read": True, "refused": True, "reason": "no landing mark could be given a colour"}); return out
    if not vessel_boxes: return out
    face = max(max(float(b[1]), float(b[3])) for b in vessel_boxes); out["x_face"] = round(face, 2)
    seen = [{"x": (min(float(b[1]), float(b[3])) + max(float(b[1]), float(b[3]))) / 2.0, "y0": min(float(b[0]), float(b[2])), "y1": max(float(b[0]), float(b[2])), "said": answers[i] if i < len(answers) else None} for i, b in enumerate(marks)]; out["said"] = [m["said"] for m in seen]
    picks = [max([m for m in seen if m["x"] > face and _says(m["said"], c)] or [None], key=lambda z: z["x"] if z else -1.0) for c in colour_list]
    out["nodes"] = [{"geometry": [[m["y0"], face, max(m["y0"] + 1.0, m["y1"]), m["x"]]]} if m else {"geometry": []} for m in picks]; out["reach"] = [round(m["x"] - face, 2) if m else None for m in picks]
    return out
# end of jet_nodes_for_ratio_code

# code: f_code_2



def jets(nodes, colours):
    boxes = []
    for i, c in enumerate(colours or []):
        node = nodes[i] if i < len(nodes) else None
        g = (node or {}).get("geometry") or []
        b = None
        for cand in g:
            try:
                y0, x0, y1, x1 = [float(v) for v in cand[:4]]
            except Exception:
                continue
            if x1 - x0 <= 0 or y1 - y0 <= 0:
                continue
            if b is None or (x1 - x0) > (b[3] - b[1]):
                b = [y0, x0, y1, x1]
        boxes.append(b)
    out = {"n_boxes": sum(1 for b in boxes if b), "reach": [], "n_found": 0, "spread": None,
           "argmax": None, "x_face": None,
           "boxes": [None if not b else [round(v, 1) for v in b] for b in boxes]}
    lefts = sorted(b[1] for b in boxes if b)
    if not lefts:
        out["reach"] = [None for _ in (colours or [])]
        return out
    n = len(lefts)
    x_face = lefts[n // 2] if n % 2 else (lefts[n // 2 - 1] + lefts[n // 2]) / 2.0
    out["x_face"] = round(x_face, 2)
    reach = []
    for b in boxes:
        if not b:
            reach.append(None)
            continue
        r = b[3] - x_face
        reach.append(round(r, 2) if r > 0 else None)
    out["reach"] = reach
    good = [(c, r) for c, r in zip(colours, reach) if r]
    out["n_found"] = len(good)
    if len(good) >= 2:
        vals = [r for _, r in good]
        out["spread"] = round(max(vals) / min(vals), 4)
        out["argmax"] = str(max(good, key=lambda t: t[1])[0]).lower()
    return out


def reach_ratio_score(nodes, colours, units, ref_index, core, margin):
    """Average how closely each jet's reach ratio to the reference jet matches the key."""
    measured = jets(nodes, colours)
    reach = measured["reach"]
    ref_index = int(ref_index)
    try:
        ref_reach = float(reach[ref_index])
        ref_units = float(units[ref_index])
    except Exception:
        return {"frac": 0.0, "reach": reach,
                "verdict": "the reference jet could not be read -> frac 0.0"}
    if ref_reach <= 0 or ref_units <= 0:
        return {"frac": 0.0, "reach": reach,
                "verdict": "the reference jet measured zero -> frac 0.0"}
    n = 0
    total = 0.0
    per_jet = []
    for i in range(len(units)):
        if i == ref_index:
            continue
        want_ratio = float(units[i]) / ref_units
        if abs(want_ratio - 1.0) < 1e-6:
            continue
        n += 1
        try:
            got_ratio = float(reach[i]) / ref_reach
        except Exception:
            per_jet.append(0.0)
            continue
        error = abs(got_ratio - want_ratio)
        core_band = float(core) * want_ratio
        margin_band = max(float(margin) * want_ratio, 1e-9)
        closeness = max(0.0, min(1.0, 1.0 - max(0.0, error - core_band) / margin_band))
        per_jet.append(round(closeness, 4))
        total += closeness
    frac = round(total / n, 4) if n else 0.0
    return {"frac": frac, "reach": reach, "x_face": measured["x_face"], "per_jet": per_jet,
            "verdict": "reaches (per-mille, from the vessel face) %s, ratios against jet %d vs "
            "key %s -> frac %s" % (reach, ref_index, list(units), frac)}

# end of f_code_2

# code: jet_nodes_for_spread_code
_SYN = {"purple": ("purple", "violet", "magenta", "mauve", "lilac", "indigo"), "blue": ("blue", "cyan", "teal", "turquoise", "azure"), "green": ("green",), "red": ("red", "crimson", "scarlet"), "yellow": ("yellow", "gold", "amber"), "orange": ("orange",), "pink": ("pink", "rose"), "brown": ("brown", "tan"), "black": ("black",), "white": ("white",), "grey": ("grey", "gray", "silver")}
def _says(answer, colour): a = str(answer if answer is not None else "").strip().lower(); c = str(colour or "").strip().lower(); return bool(a) and any(w and w in a for w in _SYN.get(c, (c,)))
def jet_nodes_for_spread(vessel_read, landing_read, colour_reads, colours):
    """For each colour, keep the furthest landing mark past the vessel face and its reach."""
    vessel_boxes = [b for b in ((vessel_read or {}).get("geometry") or []) if b and len(b) >= 4]; marks = [b for b in ((landing_read or {}).get("geometry") or []) if b and len(b) >= 4]; answers = list((colour_reads or {}).get("answers") or []); colour_list = list(colours or [])
    out = {"nodes": [{"geometry": []} for _ in colour_list], "x_face": None, "n_marks": len(marks), "reach": [None for _ in colour_list], "said": [], "no_colour_read": False, "refused": False}
    if marks and (not answers or all(a is None for a in answers)): out.update({"no_colour_read": True, "refused": True, "reason": "no landing mark could be given a colour"}); return out
    if not vessel_boxes: return out
    face = max(max(float(b[1]), float(b[3])) for b in vessel_boxes); out["x_face"] = round(face, 2)
    seen = [{"x": (min(float(b[1]), float(b[3])) + max(float(b[1]), float(b[3]))) / 2.0, "y0": min(float(b[0]), float(b[2])), "y1": max(float(b[0]), float(b[2])), "said": answers[i] if i < len(answers) else None} for i, b in enumerate(marks)]; out["said"] = [m["said"] for m in seen]
    picks = [max([m for m in seen if m["x"] > face and _says(m["said"], c)] or [None], key=lambda z: z["x"] if z else -1.0) for c in colour_list]
    out["nodes"] = [{"geometry": [[m["y0"], face, max(m["y0"] + 1.0, m["y1"]), m["x"]]]} if m else {"geometry": []} for m in picks]; out["reach"] = [round(m["x"] - face, 2) if m else None for m in picks]
    return out
# end of jet_nodes_for_spread_code

# code: jet_nodes_for_ties_code
_SYN = {"purple": ("purple", "violet", "magenta", "mauve", "lilac", "indigo"), "blue": ("blue", "cyan", "teal", "turquoise", "azure"), "green": ("green",), "red": ("red", "crimson", "scarlet"), "yellow": ("yellow", "gold", "amber"), "orange": ("orange",), "pink": ("pink", "rose"), "brown": ("brown", "tan"), "black": ("black",), "white": ("white",), "grey": ("grey", "gray", "silver")}
def _says(answer, colour): a = str(answer if answer is not None else "").strip().lower(); c = str(colour or "").strip().lower(); return bool(a) and any(w and w in a for w in _SYN.get(c, (c,)))
def jet_nodes_for_ties(vessel_read, landing_read, colour_reads, colours):
    """For each colour, keep the furthest landing mark past the vessel face and its reach."""
    vessel_boxes = [b for b in ((vessel_read or {}).get("geometry") or []) if b and len(b) >= 4]; marks = [b for b in ((landing_read or {}).get("geometry") or []) if b and len(b) >= 4]; answers = list((colour_reads or {}).get("answers") or []); colour_list = list(colours or [])
    out = {"nodes": [{"geometry": []} for _ in colour_list], "x_face": None, "n_marks": len(marks), "reach": [None for _ in colour_list], "said": [], "no_colour_read": False, "refused": False}
    if marks and (not answers or all(a is None for a in answers)): out.update({"no_colour_read": True, "refused": True, "reason": "no landing mark could be given a colour"}); return out
    if not vessel_boxes: return out
    face = max(max(float(b[1]), float(b[3])) for b in vessel_boxes); out["x_face"] = round(face, 2)
    seen = [{"x": (min(float(b[1]), float(b[3])) + max(float(b[1]), float(b[3]))) / 2.0, "y0": min(float(b[0]), float(b[2])), "y1": max(float(b[0]), float(b[2])), "said": answers[i] if i < len(answers) else None} for i, b in enumerate(marks)]; out["said"] = [m["said"] for m in seen]
    picks = [max([m for m in seen if m["x"] > face and _says(m["said"], c)] or [None], key=lambda z: z["x"] if z else -1.0) for c in colour_list]
    out["nodes"] = [{"geometry": [[m["y0"], face, max(m["y0"] + 1.0, m["y1"]), m["x"]]]} if m else {"geometry": []} for m in picks]; out["reach"] = [round(m["x"] - face, 2) if m else None for m in picks]
    return out
# end of jet_nodes_for_ties_code

# code: f_code_3



def jets(nodes, colours):
    boxes = []
    for i, c in enumerate(colours or []):
        node = nodes[i] if i < len(nodes) else None
        g = (node or {}).get("geometry") or []
        b = None
        for cand in g:
            try:
                y0, x0, y1, x1 = [float(v) for v in cand[:4]]
            except Exception:
                continue
            if x1 - x0 <= 0 or y1 - y0 <= 0:
                continue
            if b is None or (x1 - x0) > (b[3] - b[1]):
                b = [y0, x0, y1, x1]
        boxes.append(b)
    out = {"n_boxes": sum(1 for b in boxes if b), "reach": [], "n_found": 0, "spread": None,
           "argmax": None, "x_face": None,
           "boxes": [None if not b else [round(v, 1) for v in b] for b in boxes]}
    lefts = sorted(b[1] for b in boxes if b)
    if not lefts:
        out["reach"] = [None for _ in (colours or [])]
        return out
    n = len(lefts)
    x_face = lefts[n // 2] if n % 2 else (lefts[n // 2 - 1] + lefts[n // 2]) / 2.0
    out["x_face"] = round(x_face, 2)
    reach = []
    for b in boxes:
        if not b:
            reach.append(None)
            continue
        r = b[3] - x_face
        reach.append(round(r, 2) if r > 0 else None)
    out["reach"] = reach
    good = [(c, r) for c, r in zip(colours, reach) if r]
    out["n_found"] = len(good)
    if len(good) >= 2:
        vals = [r for _, r in good]
        out["spread"] = round(max(vals) / min(vals), 4)
        out["argmax"] = str(max(good, key=lambda t: t[1])[0]).lower()
    return out


def tie_separation_score(nodes, colours, ties, aparts, units):
    """Score tied jet pairs on equal reach and apart pairs on a big enough gap, multiplied."""
    measured = jets(nodes, colours)
    reach = measured["reach"]

    def reach_of(i):
        try:
            v = float(reach[int(i)])
            return v if v > 0 else None
        except Exception:
            return None

    tie_scores = []
    for p in ties:
        a, b = reach_of(p[0]), reach_of(p[1])
        if a is None or b is None:
            tie_scores.append(0.0)
            continue
        x = max(a, b) / max(min(a, b), 1e-9) - 1.0
        tie_scores.append(max(0.0, min(1.0, 1.0 - max(0.0, x - 0.08) / 0.12)))
    apart_scores = []
    for p in aparts:
        i, j = int(p[0]), int(p[1])
        vi, vj = reach_of(i), reach_of(j)
        if vi is None or vj is None:
            apart_scores.append(0.0)
            continue
        need = 0.60 * (float(units[i]) / float(units[j]) - 1.0)
        got = vi / max(vj, 1e-9) - 1.0
        apart_scores.append(max(0.0, min(1.0, got / max(need, 1e-9))))
    tie_mean = sum(tie_scores) / len(tie_scores) if tie_scores else 1.0
    apart_mean = sum(apart_scores) / len(apart_scores) if apart_scores else 1.0
    frac = round(tie_mean * apart_mean, 4)
    return {"frac": frac, "reach": reach, "ties": tie_scores, "separations": apart_scores,
            "verdict": "tied pairs %s x separated pairs %s -> frac %s" % (tie_scores, apart_scores, frac)}

# end of f_code_3

# code: jet_nodes_for_furthest_code
_SYN = {"purple": ("purple", "violet", "magenta", "mauve", "lilac", "indigo"), "blue": ("blue", "cyan", "teal", "turquoise", "azure"), "green": ("green",), "red": ("red", "crimson", "scarlet"), "yellow": ("yellow", "gold", "amber"), "orange": ("orange",), "pink": ("pink", "rose"), "brown": ("brown", "tan"), "black": ("black",), "white": ("white",), "grey": ("grey", "gray", "silver")}
def _says(answer, colour): a = str(answer if answer is not None else "").strip().lower(); c = str(colour or "").strip().lower(); return bool(a) and any(w and w in a for w in _SYN.get(c, (c,)))
def jet_nodes_for_furthest(vessel_read, landing_read, colour_reads, colours):
    """For each colour, keep the furthest landing mark past the vessel face and its reach."""
    vessel_boxes = [b for b in ((vessel_read or {}).get("geometry") or []) if b and len(b) >= 4]; marks = [b for b in ((landing_read or {}).get("geometry") or []) if b and len(b) >= 4]; answers = list((colour_reads or {}).get("answers") or []); colour_list = list(colours or [])
    out = {"nodes": [{"geometry": []} for _ in colour_list], "x_face": None, "n_marks": len(marks), "reach": [None for _ in colour_list], "said": [], "no_colour_read": False, "refused": False}
    if marks and (not answers or all(a is None for a in answers)): out.update({"no_colour_read": True, "refused": True, "reason": "no landing mark could be given a colour"}); return out
    if not vessel_boxes: return out
    face = max(max(float(b[1]), float(b[3])) for b in vessel_boxes); out["x_face"] = round(face, 2)
    seen = [{"x": (min(float(b[1]), float(b[3])) + max(float(b[1]), float(b[3]))) / 2.0, "y0": min(float(b[0]), float(b[2])), "y1": max(float(b[0]), float(b[2])), "said": answers[i] if i < len(answers) else None} for i, b in enumerate(marks)]; out["said"] = [m["said"] for m in seen]
    picks = [max([m for m in seen if m["x"] > face and _says(m["said"], c)] or [None], key=lambda z: z["x"] if z else -1.0) for c in colour_list]
    out["nodes"] = [{"geometry": [[m["y0"], face, max(m["y0"] + 1.0, m["y1"]), m["x"]]]} if m else {"geometry": []} for m in picks]; out["reach"] = [round(m["x"] - face, 2) if m else None for m in picks]
    return out
# end of jet_nodes_for_furthest_code

# code: jet_nodes_for_overlay_code
_SYN = {"purple": ("purple", "violet", "magenta", "mauve", "lilac", "indigo"), "blue": ("blue", "cyan", "teal", "turquoise", "azure"), "green": ("green",), "red": ("red", "crimson", "scarlet"), "yellow": ("yellow", "gold", "amber"), "orange": ("orange",), "pink": ("pink", "rose"), "brown": ("brown", "tan"), "black": ("black",), "white": ("white",), "grey": ("grey", "gray", "silver")}
def _says(answer, colour): a = str(answer if answer is not None else "").strip().lower(); c = str(colour or "").strip().lower(); return bool(a) and any(w and w in a for w in _SYN.get(c, (c,)))
def jet_nodes_for_overlay(vessel_read, landing_read, colour_reads, colours):
    """For each colour, keep the furthest landing mark past the vessel face and its reach."""
    vessel_boxes = [b for b in ((vessel_read or {}).get("geometry") or []) if b and len(b) >= 4]; marks = [b for b in ((landing_read or {}).get("geometry") or []) if b and len(b) >= 4]; answers = list((colour_reads or {}).get("answers") or []); colour_list = list(colours or [])
    out = {"nodes": [{"geometry": []} for _ in colour_list], "x_face": None, "n_marks": len(marks), "reach": [None for _ in colour_list], "said": [], "no_colour_read": False, "refused": False}
    if marks and (not answers or all(a is None for a in answers)): out.update({"no_colour_read": True, "refused": True, "reason": "no landing mark could be given a colour"}); return out
    if not vessel_boxes: return out
    face = max(max(float(b[1]), float(b[3])) for b in vessel_boxes); out["x_face"] = round(face, 2)
    seen = [{"x": (min(float(b[1]), float(b[3])) + max(float(b[1]), float(b[3]))) / 2.0, "y0": min(float(b[0]), float(b[2])), "y1": max(float(b[0]), float(b[2])), "said": answers[i] if i < len(answers) else None} for i, b in enumerate(marks)]; out["said"] = [m["said"] for m in seen]
    picks = [max([m for m in seen if m["x"] > face and _says(m["said"], c)] or [None], key=lambda z: z["x"] if z else -1.0) for c in colour_list]
    out["nodes"] = [{"geometry": [[m["y0"], face, max(m["y0"] + 1.0, m["y1"]), m["x"]]]} if m else {"geometry": []} for m in picks]; out["reach"] = [round(m["x"] - face, 2) if m else None for m in picks]
    return out
# end of jet_nodes_for_overlay_code

# code: f_code_4



def jets(nodes, colours):
    boxes = []
    for i, c in enumerate(colours or []):
        node = nodes[i] if i < len(nodes) else None
        g = (node or {}).get("geometry") or []
        b = None
        for cand in g:
            try:
                y0, x0, y1, x1 = [float(v) for v in cand[:4]]
            except Exception:
                continue
            if x1 - x0 <= 0 or y1 - y0 <= 0:
                continue
            if b is None or (x1 - x0) > (b[3] - b[1]):
                b = [y0, x0, y1, x1]
        boxes.append(b)
    out = {"n_boxes": sum(1 for b in boxes if b), "reach": [], "n_found": 0, "spread": None,
           "argmax": None, "x_face": None,
           "boxes": [None if not b else [round(v, 1) for v in b] for b in boxes]}
    lefts = sorted(b[1] for b in boxes if b)
    if not lefts:
        out["reach"] = [None for _ in (colours or [])]
        return out
    n = len(lefts)
    x_face = lefts[n // 2] if n % 2 else (lefts[n // 2 - 1] + lefts[n // 2]) / 2.0
    out["x_face"] = round(x_face, 2)
    reach = []
    for b in boxes:
        if not b:
            reach.append(None)
            continue
        r = b[3] - x_face
        reach.append(round(r, 2) if r > 0 else None)
    out["reach"] = reach
    good = [(c, r) for c, r in zip(colours, reach) if r]
    out["n_found"] = len(good)
    if len(good) >= 2:
        vals = [r for _, r in good]
        out["spread"] = round(max(vals) / min(vals), 4)
        out["argmax"] = str(max(good, key=lambda t: t[1])[0]).lower()
    return out


def reach_ratio_overlay(nodes, colours, units, ref, core, margin):
    """Score reach ratios against the reference jet and report the boxes for drawing."""
    measured = jets(nodes, colours)
    reach = measured["reach"]
    frac = 0.0
    try:
        ref_reach, ref_units = float(reach[int(ref)]), float(units[int(ref)])
        n = 0
        total = 0.0
        for i in range(len(units)):
            if i == int(ref):
                continue
            want_ratio = float(units[i]) / ref_units
            if abs(want_ratio - 1.0) < 1e-6:
                continue
            n += 1
            got_ratio = float(reach[i]) / ref_reach
            core_band = float(core) * want_ratio
            margin_band = max(float(margin) * want_ratio, 1e-9)
            total += max(0.0, min(1.0, 1.0 - max(0.0, abs(got_ratio - want_ratio) - core_band) / margin_band))
        frac = round(total / n, 4) if n else 0.0
    except Exception:
        frac = 0.0
    return {"frac": frac, "reach": reach, "boxes": measured["boxes"], "x_face": measured["x_face"],
            "spread": measured["spread"], "argmax": measured["argmax"],
            "verdict": "per-colour boxes %s -> reaches %s (vessel face at x=%s), furthest %s"
            % (measured["boxes"], reach, measured["x_face"], measured["argmax"])}

# end of f_code_4
