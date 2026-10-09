# shared code: code_3291d64f4d81



def _frac(b):
    return 1.0 if b else 0.0


def n_squares(n_rows, n_cols):
    """Total number of grid squares in the map."""
    return {"n": int(n_rows) * int(n_cols)}


def _shrink(y0, x0, y1, x1, keep):
    m = (1.0 - float(keep)) / 2.0
    h, w = (y1 - y0), (x1 - x0)
    return [round(y0 + m * h, 1), round(x0 + m * w, 1),
            round(y1 - m * h, 1), round(x1 - m * w, 1)]


def _lat_box(lb):
    lg = (lb.get("geometry") if isinstance(lb, dict) else None) or []
    if not lg or not isinstance(lg[0], (list, tuple)) or len(lg[0]) < 4:
        return None
    ymin, xmin, ymax, xmax = [float(v) for v in list(lg[0])[:4]]
    y0, y1 = min(ymin, ymax), max(ymin, ymax)
    x0, x1 = min(xmin, xmax), max(xmin, xmax)
    if (y1 - y0) < 40.0 or (x1 - x0) < 40.0:
        return None
    return (y0, x0, y1, x1)


def _covers(items, lb, cover):
    r = _lat_box(lb)
    if r is None:
        return True
    ly0, lx0, ly1, lx1 = r
    uy0 = min(t["box"][0] for t in items)
    ux0 = min(t["box"][1] for t in items)
    uy1 = max(t["box"][2] for t in items)
    ux1 = max(t["box"][3] for t in items)
    oh = max(0.0, min(uy1, ly1) - max(uy0, ly0))
    ow = max(0.0, min(ux1, lx1) - max(ux0, lx0))
    return (oh / max(1e-9, ly1 - ly0) >= cover) and (ow / max(1e-9, lx1 - lx0) >= cover)


def grid_square_boxes(gb, lb, n_rows, n_cols, keep=0.70, cover=0.92):
    """Boxes for each grid square, row by row, shrunk toward their centres."""
    n_rows, n_cols = int(n_rows), int(n_cols)
    need = n_rows * n_cols
    geometry = (gb.get("geometry") if isinstance(gb, dict) else None) or []
    why = None
    if len(geometry) != need:
        why = "cell_count_%d_vs_%d" % (len(geometry), need)
    else:
        items = []
        for b in geometry:
            if not isinstance(b, (list, tuple)) or len(b) < 4:
                items = None
                why = "bad_box"
                break
            ymin, xmin, ymax, xmax = [float(v) for v in list(b)[:4]]
            y0, y1 = min(ymin, ymax), max(ymin, ymax)
            x0, x1 = min(xmin, xmax), max(xmin, xmax)
            items.append({"y": (y0 + y1) / 2.0, "x": (x0 + x1) / 2.0,
                          "box": (y0, x0, y1, x1)})
        if items:
            items.sort(key=lambda t: t["y"])
            bands = [items[i * n_cols:(i + 1) * n_cols] for i in range(n_rows)]
            ok = True
            for k in range(n_rows - 1):
                if max(t["y"] for t in bands[k]) >= min(t["y"] for t in bands[k + 1]):
                    ok, why = False, "bands_interleave"
                    break
            if ok:
                out = []
                for band in bands:
                    band.sort(key=lambda t: t["x"])
                    for k in range(len(band) - 1):
                        if band[k + 1]["x"] <= band[k]["x"]:
                            ok, why = False, "band_not_monotone"
                            break
                    if not ok:
                        break
                    for t in band:
                        y0, x0, y1, x1 = t["box"]
                        out.append(_shrink(y0, x0, y1, x1, keep))
                if ok:
                    if not _covers(items, lb, cover):
                        why = "cell_union_misses_array_box"
                    else:
                        return {"boxes": out, "no_read": False, "n": len(out),
                                "source": "cell_ring"}
    r = _lat_box(lb)
    if r is None:
        return {"boxes": [], "no_read": True, "reason": (why or "no_cells") + "|no_lattice_box"}
    y0, x0, y1, x1 = r
    ch, cw = (y1 - y0) / float(n_rows), (x1 - x0) / float(n_cols)
    out = []
    for i in range(n_rows):
        for j in range(n_cols):
            a, b = y0 + ch * i, x0 + cw * j
            out.append(_shrink(a, b, a + ch, b + cw, keep))
    return {"boxes": out, "no_read": False, "n": len(out), "source": "lattice_split",
            "cell_ring_rejected": why}


def _tok(a):
    if a is None:
        return -1
    t = str(a).strip().lower()
    if not t:
        return -1
    for bad in ("none", "empty", "blank", "nothing", "no character"):
        if bad in t:
            return -1
    for ch in t:
        if ch == "1":
            return 1
        if ch == "0":
            return 0
    if "one" in t:
        return 1
    if "zero" in t:
        return 0
    return -1


def matrix(cr, n_rows, n_cols):
    n_rows, n_cols = int(n_rows), int(n_cols)
    ans = cr.get("answers") if isinstance(cr, dict) else None
    if not ans or len(ans) < n_rows * n_cols:
        return None
    vals = [_tok(a) for a in ans[:n_rows * n_cols]]
    return [vals[i * n_cols:(i + 1) * n_cols] for i in range(n_rows)]


def _ones_set(cells):
    return set((r, c) for r, row in enumerate(cells) for c, v in enumerate(row) if int(v) == 1)


def lattice_ok(cb):
    """1 if boxes for the grid squares were found, else 0."""
    return {"frac": 0.0 if cb.get("no_read") else 1.0, "n_cells": cb.get("n", 0)}


def score_ones_count(cr, n_rows, n_cols, n_minterms):
    """1 if the number of squares read as 1 equals the minterm count."""
    m = matrix(cr, n_rows, n_cols)
    if m is None:
        return {"frac": 0.0, "reason": "cells_unread"}
    got = sum(1 for row in m for v in row if v == 1)
    return {"frac": _frac(int(got) == int(n_minterms)), "measured": got,
            "expected": int(n_minterms), "cells": m}


def score_minterm_placement(cr, n_rows, n_cols, reference_squares):
    """Share of minterm squares read as 1, less wrong 1s, floored at zero."""
    m = matrix(cr, n_rows, n_cols)
    if m is None:
        return {"frac": 0.0, "reason": "cells_unread"}
    want = _ones_set([[int(v) for v in r] for r in reference_squares])
    got = _ones_set(m)
    hit = len(want & got)
    fp = len(got - want)
    as_score = max(0.0, (hit - fp) / float(max(1, len(want))))
    return {"frac": round(min(1.0, as_score), 4), "hit": hit, "false_positive": fp,
            "n_minterms": len(want), "cells": m}


def score_map_exact(cr, n_rows, n_cols, reference_squares):
    """1 if every square reads exactly as in the reference map, else 0."""
    m = matrix(cr, n_rows, n_cols)
    if m is None:
        return {"frac": 0.0, "reason": "cells_unread"}
    want = [[int(v) for v in r] for r in reference_squares]
    return {"frac": _frac(m == want), "measured": m, "expected": want}


def _hdr(ans, n):
    import re
    if ans is None:
        return []
    t = str(ans).strip().lower()
    toks = re.findall(r"[01]{2,4}", t)
    return toks[:int(n)]


def appearance_form(column_answer, row_answer, col_headers, row_headers):
    """Share of row and column headers read in the reference order."""
    columns_read = _hdr(column_answer, len(col_headers))
    rows_read = _hdr(row_answer, len(row_headers))
    okc = [str(a) == str(b) for a, b in zip(columns_read, col_headers)]
    okr = [str(a) == str(b) for a, b in zip(rows_read, row_headers)]
    tot = len(col_headers) + len(row_headers)
    return {"frac": round((sum(okc) + sum(okr)) / float(max(1, tot)), 4),
            "col_read": columns_read, "row_read": rows_read,
            "col_expected": list(col_headers), "row_expected": list(row_headers)}


def as_score(v):
    return float(v or 0.0)

# end of code_3291d64f4d81
