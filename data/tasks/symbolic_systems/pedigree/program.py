# shared code: code_66bb2c70eff4


ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII"]


def obligate_carriers(sexes, parents, affected, mode):
    sex = dict(sexes)
    kids = {k: list(v) for k, v in dict(parents).items()}
    out = set()
    aff = set(affected)
    for child, par in kids.items():
        if child not in aff:
            continue
        if mode == "AR":
            out.update(par)
        else:
            if sex.get(child) == "M":
                for p in par:
                    if sex.get(p) == "F":
                        out.add(p)
    if mode == "XLR":
        for child, par in kids.items():
            if sex.get(child) == "F" and any(p in aff and sex.get(p) == "M" for p in par):
                out.add(child)
    out -= aff
    return sorted(out, key=lambda i: (ROMAN.index(i.split("-")[0]), int(i.split("-")[1])))


def n_people(layout):
    """Number of people in the reference family layout."""
    return {"n": len(list(layout))}


def _yes(a):
    if a is None:
        return None
    t = str(a).strip().lower()
    if t.startswith("y") or t == "true":
        return True
    if t.startswith("n") or t == "false":
        return False
    return None


def _shape(a):
    if a is None:
        return None
    t = str(a).strip().lower()
    if "circle" in t or "round" in t or "oval" in t:
        return "circle"
    if "square" in t or "box" in t or "rect" in t:
        return "square"
    return None


def symbols(sy, dots, shapes, fills):
    g = (sy.get("geometry") if isinstance(sy, dict) else None) or []
    da = (dots.get("answers") if isinstance(dots, dict) else None) or []
    sa = (shapes.get("answers") if isinstance(shapes, dict) else None) or []
    fa = (fills.get("answers") if isinstance(fills, dict) else None) or []
    syms = []
    for k, b in enumerate(g):
        if not isinstance(b, (list, tuple)) or len(b) < 4:
            continue
        ymin, xmin, ymax, xmax = [float(v) for v in list(b)[:4]]
        y0, y1 = min(ymin, ymax), max(ymin, ymax)
        x0, x1 = min(xmin, xmax), max(xmin, xmax)
        syms.append({"x": (x0 + x1) / 2.0, "y": (y0 + y1) / 2.0, "h": (y1 - y0),
                     "centre_dot": bool(_yes(da[k]) if k < len(da) else False),
                     "shape": (_shape(sa[k]) if k < len(sa) else None),
                     "filled": bool(_yes(fa[k]) if k < len(fa) else False)})
    if not syms:
        return {"symbols": [], "gen_sizes": [], "no_read": True, "n_symbols": 0, "n_dots": 0}
    syms.sort(key=lambda t: t["y"])
    hs = sorted(t["h"] for t in syms)
    med = float(hs[len(hs) // 2]) or 1.0
    bands, cur = [], [syms[0]]
    for t in syms[1:]:
        if t["y"] - cur[-1]["y"] > 1.2 * med:
            bands.append(cur)
            cur = [t]
        else:
            cur.append(t)
    bands.append(cur)
    out = []
    for gi, band in enumerate(bands):
        for k, t in enumerate(sorted(band, key=lambda s: s["x"])):
            u = dict(t)
            u["id"] = "%s-%d" % (ROMAN[gi] if gi < len(ROMAN) else "G%d" % (gi + 1), k + 1)
            u["gen"] = gi + 1
            out.append(u)
    return {"symbols": out, "gen_sizes": [len(b) for b in bands], "no_read": False,
            "n_symbols": len(out), "n_dots": sum(1 for t in out if t["centre_dot"])}


def measure_pedigree(sy, dots, shapes, fills, carriers, layout, x_linked):
    """Compare dotted carriers, shapes, fills and generation sizes with the reference."""
    reading = symbols(sy, dots, shapes, fills)
    want = sorted(carriers)
    out = {"no_read": bool(reading["no_read"]), "gt_carriers": want, "n_symbols": reading["n_symbols"]}
    if out["no_read"]:
        for k in ("set_frac", "overlap_frac", "count_frac", "legal_frac",
                  "convention_frac", "dot_present_frac"):
            out[k] = 0.0
        out["read_carriers"] = []
        return out
    syms = reading["symbols"]
    got = sorted(t["id"] for t in syms if t["centre_dot"])
    out["read_carriers"] = got
    out["gen_sizes"] = reading["gen_sizes"]
    out["n_dots"] = reading["n_dots"]
    out["set_frac"] = 1.0 if got == want else 0.0
    A, B = set(got), set(want)
    out["overlap_frac"] = round(2.0 * len(A & B) / float(len(A) + len(B)), 4) if (A or B) else 0.0
    out["count_frac"] = 1.0 if len(got) == len(want) else 0.0
    males_dotted = [t["id"] for t in syms if t["centre_dot"] and t["shape"] == "square"]
    out["males_dotted"] = males_dotted
    out["legal_frac"] = 0.0 if (x_linked and males_dotted) else 1.0
    layout_parts = [str(s).split(":") for s in layout]
    want_sizes = []
    for gid, _sh, _fl in layout_parts:
        gi = ROMAN.index(gid.split("-")[0])
        while len(want_sizes) <= gi:
            want_sizes.append(0)
        want_sizes[gi] += 1
    by_id = {t["id"]: t for t in syms}
    hits = 0
    for gid, sh, fl in layout_parts:
        t = by_id.get(gid)
        if t and t["shape"] == sh and bool(t["filled"]) == (fl == "1"):
            hits += 1
    parts = [hits / float(len(layout_parts)), 1.0 if reading["gen_sizes"] == want_sizes else 0.0]
    out["convention_frac"] = round(sum(parts) / float(len(parts)), 4)
    out["dot_present_frac"] = 1.0 if got else 0.0
    return out


def symbols_readable(sy, dots, shapes, fills, carriers, layout, x_linked):
    """1 if the family symbols could be read at all, else 0."""
    m = measure_pedigree(sy, dots, shapes, fills, carriers, layout, x_linked)
    return {"frac": 0.0 if m["no_read"] else 1.0, "n_symbols": m["n_symbols"]}


def as_score(v):
    return float(v or 0.0)

# end of code_66bb2c70eff4

# code: chart_readable_frac_code
def chart_readable_frac(readable_result, people):
    """1 if the chart draws one readable symbol per person, else 0."""
    n = int((readable_result or {}).get("n_symbols") or 0)
    want = int((people or {}).get("n") or 0)
    if not want:
        return {"frac": 0.0, "n_symbols": n, "n_people": want, "verdict": "the family list is empty"}
    if n != want:
        return {"frac": 0.0, "n_symbols": n, "n_people": want, "verdict": "the chart draws %d symbols where the family has %d people" % (n, want)}
    return {"frac": float((readable_result or {}).get("frac") or 0.0), "n_symbols": n, "n_people": want, "verdict": "the chart draws %d symbols, one per person" % n}

# end of chart_readable_frac_code
