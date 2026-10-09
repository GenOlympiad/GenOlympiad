# code: helpers
from genolympiad.task_helpers import count_listed_items
# end of helpers

# shared code: code_9fcc9a932431

def panel_boxes(layout):
    """Split the picture into three equal panel boxes along the stated layout."""
    is_row = str(layout).lower().startswith("r")
    out = []
    for i in range(3):
        a, b = int(round(1000.0 * i / 3.0)), int(round(1000.0 * (i + 1) / 3.0))
        out.append([0, a, 1000, b] if is_row else [a, 0, b, 1000])
    return {"geometry": out, "p1": [out[0]], "p2": [out[1]], "p3": [out[2]],
            "p12pair": [out[0], out[1]],
            "p12": [[0, 0, 1000, 667] if is_row else [0, 0, 667, 1000]],
            "all": out}


def edge_crossing_questions(flow):
    """Write the questions for where the river meets the map edges, by flow direction."""
    vertical_flow = str(flow).lower().startswith("v")
    in_question = ("Measured along the BOTTOM edge of this map, starting from its bottom-left corner, how "
           "far across that edge does the river meet it? Answer with a single number between 0 "
           "and 100, where 0 is the left-hand corner and 100 is the right-hand corner.") if vertical_flow else \
          ("Measured down the LEFT edge of this map, starting from its top-left corner, how far "
           "down that edge does the river meet it? Answer with a single number between 0 and 100, "
           "where 0 is the top corner and 100 is the bottom corner.")
    out_question = ("Measured along the TOP edge of this map, starting from its top-left corner, how far "
           "across that edge does the river meet it? Answer with a single number between 0 and "
           "100, where 0 is the left-hand corner and 100 is the right-hand corner.") if vertical_flow else \
          ("Measured down the RIGHT edge of this map, starting from its top-right corner, how far "
           "down that edge does the river meet it? Answer with a single number between 0 and 100, "
           "where 0 is the top corner and 100 is the bottom corner.")
    return {"q_in": in_question, "q_out": out_question}


def _ans(r, i=0):
    if not isinstance(r, dict):
        return None
    a = r.get("answers")
    if not isinstance(a, list) or i >= len(a):
        return None
    return None if a[i] is None else str(a[i]).strip()


def _int(r, i=0):
    import re
    s = _ans(r, i)
    if s is None:
        return None
    m = re.match(r"^\s*(\d+)", s)
    if m:
        return int(m.group(1))
    ns = re.findall(r"\d+", s)
    if ns:
        return int(ns[-1])
    w = {"zero": 0, "none": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6}
    for k, val in w.items():
        if s.lower().startswith(k):
            return val
    return None


def _side(r, i=0):
    s = _ans(r, i)
    if s is None:
        return None
    s = s.lower()
    for k in ("left", "right", "top", "bottom", "upper", "lower", "above", "below"):
        if k in s:
            return {"upper": "top", "above": "top", "lower": "bottom", "below": "bottom"}.get(k, k)
    return None


def _yesno(r, i=0):
    s = _ans(r, i)
    if s is None:
        return None
    s = s.lower()
    if s.startswith("y") or " yes" in s:
        return True
    if s.startswith("n") or " no" in s:
        return False
    return None


def _opposite(a, b):
    pair = {"left": "right", "right": "left", "top": "bottom", "bottom": "top"}
    return bool(a and b and pair.get(a) == b)


def oxbow_read(rn, rbranch, rneck, rloop2, rlake3, ropen3, rin=None, rout=None,
               rloops2=None, rloops3=None, rloop3=None):
    """Collect the panel reads into one record: water counts, branches, neck, sides, crossings."""
    water_counts = [_int(rn, i) for i in range(3)]
    if any(c is None for c in water_counts):
        return {"no_read": True, "reason": "reader_gave_no_water_count"}
    branches = [_yesno(rbranch, 0), _yesno(rbranch, 1)]
    if any(b is None for b in branches):
        return {"no_read": True, "reason": "reader_gave_no_branch_answer"}
    neck = _yesno(rneck)
    loop2 = _side(rloop2)
    lake = _side(rlake3)
    lake_opens = _ans(ropen3)
    lake_opens = None if lake_opens is None else ("towards" if "toward" in lake_opens.lower()
                                  else ("away" if "away" in lake_opens.lower() else None))
    lake_ok = bool(water_counts[2] >= 2)
    record = {"no_read": False, "comps": water_counts, "branch": [1 if branches[0] else 0, 1 if branches[1] else 0],
         "neck_narrows": neck, "loop_side_p2": loop2, "lake_side": lake, "lake_open": lake_opens,
         "lake_ok": lake_ok}
    if rin is not None and rout is not None:
        a1, a3 = _int(rin, 0), _int(rin, 2)
        b1, b3 = _int(rout, 0), _int(rout, 2)
        record["shift_in"] = None if (a1 is None or a3 is None) else abs(a1 - a3) / 100.0
        record["shift_out"] = None if (b1 is None or b3 is None) else abs(b1 - b3) / 100.0
    if rloops2 is not None:
        record["p2_loops"] = _int(rloops2)
        record["p3_loops"] = _int(rloops3)
        record["p3_loop_side"] = _side(rloop3)
    return record


def score_unbranched(reads):
    """Score 1 when neither of the first two panels shows a branching channel."""
    if reads.get("no_read"):
        return 0.0
    branches = reads.get("branch")
    return 1.0 if (branches and int(branches[0]) == 0 and int(branches[1]) == 0) else 0.0


def score_water_counts(reads, want):
    """Score 1 when the water-body count in each panel equals the wanted count."""
    if reads.get("no_read"):
        return 0.0
    counts = reads.get("comps")
    return 1.0 if [int(x) for x in counts] == [int(x) for x in want] else 0.0


def score_neck(reads):
    """Score 1 when the loop neck is read as narrowing."""
    if reads.get("no_read"):
        return 0.0
    return 1.0 if reads.get("neck_narrows") is True else 0.0


def score_lake_side(reads):
    """Score 1 when the oxbow lake sits on the same side as the panel-two loop."""
    if reads.get("no_read") or not reads.get("lake_ok"):
        return 0.0
    a, b = reads.get("loop_side_p2"), reads.get("lake_side")
    if not a or not b:
        return 0.0
    return 1.0 if a == b else 0.0


def score_lake_opening(reads):
    """Score 1 when the oxbow lake's open side faces toward the river."""
    if reads.get("no_read") or not reads.get("lake_ok"):
        return 0.0
    return 1.0 if reads.get("lake_open") == "towards" else 0.0


def _band(x, core, marg):
    if x is None:
        return 0.0
    x = float(x)
    if x <= core:
        return 1.0
    if x >= marg:
        return 0.0
    return (marg - x) / (marg - core)


def score_edge_crossings(reads):
    """Average how well the river's entry and exit points shift between panels one and three."""
    if reads.get("no_read"):
        return 0.0
    return round(0.5 * (_band(reads.get("shift_in"), 0.02, 0.14)
                        + _band(reads.get("shift_out"), 0.02, 0.14)), 4)


def score_one_bend(reads):
    """Half for two loops in panel two, half for one loop in panel three on the far side."""
    if reads.get("no_read"):
        return 0.0
    two_loops = 1.0 if (reads.get("p2_loops") is not None and int(reads.get("p2_loops")) >= 2) else 0.0
    far_loop = 0.0
    if reads.get("p3_loops") is not None and int(reads.get("p3_loops")) == 1:
        far_loop = 1.0 if _opposite(reads.get("p3_loop_side"), reads.get("lake_side")) else 0.0
    return round(0.5 * two_loops + 0.5 * far_loop, 4)


def score_read_present(reads):
    """Score 1 whenever the panel reads came back at all."""
    if reads.get("no_read"):
        return 0.0
    return 1.0

# end of code_9fcc9a932431
