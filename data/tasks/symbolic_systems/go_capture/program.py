# code: helpers
from genolympiad.task_helpers import map_answer_to_token
# end of helpers

# shared code: code_4239f1ef5893


GO_LETTERS = "ABCDEFGHJKLMNOPQRST"


def go_cols(n):
    return GO_LETTERS[:int(n)]


def parse_point(s, n):
    s = str(s).strip().upper()
    return (go_cols(n).index(s[0]), int(s[1:]))


def _name(p, n):
    return "%s%d" % (go_cols(n)[p[0]], p[1])


def neighbours(p, n):
    c, r = p
    out = []
    for dc, dr in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        j, s = c + dc, r + dr
        if 0 <= j < n and 1 <= s <= n:
            out.append((j, s))
    return out


def go_replay(moves, n):
    n = int(n)
    board, nocap = {}, {}
    captured = []
    for mv in moves:
        colour, where = str(mv).split()
        p = parse_point(where, n)
        board[p] = colour.upper()[0]
        nocap[p] = colour.upper()[0]
        enemy = "W" if board[p] == "B" else "B"
        for q in neighbours(p, n):
            if board.get(q) != enemy:
                continue
            grp, seen, libs, stack = [], set(), 0, [q]
            while stack:
                x = stack.pop()
                if x in seen:
                    continue
                seen.add(x)
                grp.append(x)
                for y in neighbours(x, n):
                    if y not in board:
                        libs += 1
                    elif board[y] == enemy and y not in seen:
                        stack.append(y)
            if libs == 0:
                for x in grp:
                    board.pop(x, None)
                    captured.append(x)
    final = {_name(k, n): v for k, v in sorted(board.items())}
    played = {_name(k, n): v for k, v in sorted(nocap.items())}
    return {"final": final,
            "captured": sorted(_name(x, n) for x in set(captured)),
            "must_be_empty": sorted(set(played) - set(final)),
            "n_black": sum(1 for v in final.values() if v == "B"),
            "n_white": sum(1 for v in final.values() if v == "W"),
            "nocap": {_name(k, n): v for k, v in sorted(nocap.items())},
            "nocap_black": sum(1 for v in nocap.values() if v == "B"),
            "nocap_white": sum(1 for v in nocap.values() if v == "W")}


def crossing_boxes(lattice, ruled_lines, n, keep=0.75):
    """One small box around every lattice crossing, or no read if the sheet has no ruled grid."""
    n = int(n)
    ruled_answer = str(ruled_lines or "").strip().lower()
    if ruled_answer.startswith("n"):
        return {"boxes": [], "no_read": True, "reason": "no_ruled_lattice_on_the_board",
                "premise_answer": str(ruled_lines)}
    geometry = (lattice.get("geometry") if isinstance(lattice, dict) else None) or []
    if not geometry or not isinstance(geometry[0], (list, tuple)) or len(geometry[0]) < 4:
        return {"boxes": [], "no_read": True, "reason": "no_lattice_box"}
    y0, x0, y1, x1 = [float(v) for v in list(geometry[0])[:4]]
    y0, y1 = min(y0, y1), max(y0, y1)
    x0, x1 = min(x0, x1), max(x0, x1)
    if (y1 - y0) < 40.0 or (x1 - x0) < 40.0:
        return {"boxes": [], "no_read": True, "reason": "degenerate_lattice"}
    pitch_y = (y1 - y0) / float(n - 1)
    pitch_x = (x1 - x0) / float(n - 1)
    h, w = 0.5 * float(keep) * pitch_y, 0.5 * float(keep) * pitch_x
    out = []
    for i in range(n):
        for j in range(n):
            cy, cx = y0 + pitch_y * i, x0 + pitch_x * j
            out.append([round(cy - h, 1), round(cx - w, 1), round(cy + h, 1), round(cx + w, 1)])
    return {"boxes": out, "no_read": False, "n": len(out),
            "pitch": [round(pitch_y, 2), round(pitch_x, 2)]}


def _stone(a):
    if a is None:
        return ""
    t = str(a).strip().lower()
    if "black" in t:
        return "B"
    if "white" in t:
        return "W"
    if t in ("b",):
        return "B"
    if t in ("w",):
        return "W"
    return ""


def board_of(cx, n):
    n = int(n)
    ans = (cx.get("answers") if isinstance(cx, dict) else None) or []
    if len(ans) < n * n:
        return None
    board = {}
    for k in range(n * n):
        v = _stone(ans[k])
        if v:
            i, j = divmod(k, n)
            board[_name((j, n - i), n)] = v
    return board


def go_measure(crossing_reads, moves, n):
    """Compare the read stones with the replayed final position, scoring captures and counts."""
    n = int(n)
    reference = go_replay(list(moves), n)
    read_board = board_of(crossing_reads, n)
    out = {"no_read": read_board is None, "gt_final": reference["final"], "gt_captured": reference["must_be_empty"],
           "read_board": read_board or {}, "gt_black": reference["n_black"], "gt_white": reference["n_white"]}
    if read_board is None:
        for k in ("capture_frac", "exact_frac", "overlap_frac", "count_frac", "transcribe_frac"):
            out[k] = 0.0
        return out
    n_black = sum(1 for v in read_board.values() if v == "B")
    n_white = sum(1 for v in read_board.values() if v == "W")
    out["n_black"], out["n_white"] = n_black, n_white
    want, captured = reference["final"], reference["must_be_empty"]

    def _bare_ok(p):
        if p in read_board:
            return 0.0
        for q in neighbours(parse_point(p, n), n):
            key = _name(q, n)
            if want.get(key) is not None and read_board.get(key) != want[key]:
                return 0.0
        return 1.0
    out["capture_frac"] = round(sum(_bare_ok(p) for p in captured) / float(len(captured)), 4) if captured else 0.0
    out["captured_but_still_shown"] = sorted(p for p in captured if p in read_board)
    out["exact_frac"] = 1.0 if read_board == want else 0.0
    union = set(read_board) | set(want)
    out["overlap_frac"] = round(sum(1.0 for p in union if read_board.get(p) == want.get(p))
                                / float(len(union)), 4) if union else 0.0
    out["count_frac"] = round(0.5 * ((n_black == reference["n_black"]) + (n_white == reference["n_white"])), 4)
    played = reference["nocap"]
    out["transcribe_frac"] = round(sum(1.0 for p in played if read_board.get(p) == played[p])
                                   / float(len(played)), 4) if played else 0.0
    return out


def readable(crossing_reads, moves, n):
    """1 if the crossings could be read as a full board, else 0."""
    measure = go_measure(crossing_reads, moves, n)
    return {"frac": 0.0 if measure["no_read"] else 1.0, "n_read": len(measure["read_board"])}


def convention_form(crossing_reads, letters_answer, moves, n):
    """Share of form checks passed: some stones were read and the file letters are shown."""
    measure = go_measure(crossing_reads, moves, n)
    parts = [1.0 if len(measure["read_board"]) > 0 else 0.0]
    if letters_answer is not None:
        t = str(letters_answer).strip().lower()
        if t.startswith("y") or t.startswith("n"):
            parts.append(1.0 if t.startswith("y") else 0.0)
    return {"frac": round(sum(parts) / float(len(parts)), 4), "parts": parts,
            "letters_answer": None if letters_answer is None else str(letters_answer)}


def as_score(v):
    return float(v or 0.0)

# end of code_4239f1ef5893
