# code: helpers
from genolympiad.task_helpers import count_as_read, count_confirmed_cutouts, count_listed_items
# end of helpers

# shared code: code_7e435d127558

import re

_WORDS = {"zero": "0", "none": "0", "no": "0", "one": "1", "two": "2", "three": "3", "four": "4",
          "five": "5", "six": "6", "seven": "7", "eight": "8", "nine": "9", "ten": "10"}


def _clean(tok):
    t = str(tok).strip().strip('*"\'` ').strip().strip('.').strip().casefold()
    m = re.search(r"\d+", t)
    if m:
        return m.group(0).lstrip("0") or "0"
    w = re.sub(r"[^a-z]", "", t)
    return _WORDS.get(w, t)


def check_panel_counts(read, target):
    """Score 1 when every panel's read bucket count equals the reference sequence."""
    answers = read.get("answers") if isinstance(read, dict) else read
    target = [str(x).strip().casefold().lstrip("0") or "0" for x in (target or [])]
    cells = None
    if (isinstance(answers, (list, tuple)) and len(answers) == len(target)
            and not any(a is None for a in answers)):
        c = [_clean(a) for a in answers]
        if all(x != "" for x in c):
            cells = c
    if not target or cells is None:
        return {"law": 0.0, "share": 0.0, "unreadable": True, "bad": None,
                "verdict": "a panel-cell read never came back -> unreadable"}
    ok, bad = 0, []
    for i, (g, t) in enumerate(zip(cells, target)):
        if g == t:
            ok += 1
        else:
            bad.append([i + 1, g, t])
    tot = len(target)
    return {"law": 1.0 if ok == tot else 0.0, "share": round(ok * 1.0 / tot, 4),
            "unreadable": False, "bad": bad, "read": cells,
            "verdict": "%d/%d panel-cells obey the law -> law %.1f, panel-share %.4f"
                       % (ok, tot, 1.0 if ok == tot else 0.0, ok * 1.0 / tot)}

# end of code_7e435d127558

# shared code: code_69ba913609b0

import re


def panel_grid_boxes(n, layout_read):
    """Split the frame into equal panel boxes from the read row count of the storyboard."""
    n = int(n)
    answer = layout_read
    if isinstance(answer, dict):
        a = answer.get("answers") or []
        answer = a[0] if a else None
    d = re.findall(r"\d+", "" if answer is None else str(answer))
    rows = int(d[0]) if d else 0
    if rows <= 0 or rows > n or n % rows:
        return {"boxes": None, "rows": rows or None, "cols": None, "unreadable": True,
                "verdict": "the panel grid's row count did not come back as a divisor of the %d "
                           "panels (read %r) -> unreadable" % (n, answer)}
    cols = n // rows
    boxes = [[r * 1000.0 / rows, c * 1000.0 / cols,
              (r + 1) * 1000.0 / rows, (c + 1) * 1000.0 / cols]
             for r in range(rows) for c in range(cols)]
    return {"boxes": boxes, "rows": rows, "cols": cols, "unreadable": False,
            "verdict": "panel grid read as %d row(s) x %d column(s); the frame is cut into %d "
                       "equal cells and each cell is counted on its own" % (rows, cols, n)}

# end of code_69ba913609b0
