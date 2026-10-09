# shared code: code_5450bfcc79ad

def _items(read, k):
    if isinstance(read, dict) or not isinstance(read, (list, tuple)) or len(read) < k:
        return None
    out = []
    for v in list(read)[:k]:
        if isinstance(v, (list, tuple)):
            v = v[0] if v else ""
        out.append(str(v).strip().strip(".").casefold())
    return out


def _pick(group, k):
    for i, read in enumerate(group or []):
        got = _items(read, k)
        if got is not None:
            return got, ("primary" if i == 0 else "rescue")
    return None, "unreadable"


def _agree(group, k):
    reads = [_items(r, k) for r in (group or [])]
    reads = [r for r in reads if r is not None]
    if len(reads) < 2:
        return None
    return round(sum(1.0 for a, b in zip(reads[0], reads[1]) if a == b) / max(1, k), 4)


def _judge(groups, tgts):
    pairs, srcs, agrees = [], [], []
    for group, tgt in zip(groups, tgts):
        if tgt is None:
            continue
        tgt = [str(x).strip().casefold() for x in tgt]
        got, src = _pick(group, len(tgt))
        pairs.append((got, tgt))
        srcs.append(src)
        agrees.append(_agree(group, len(tgt)))
    if not pairs or any(p[0] is None for p in pairs):
        return {"law": 0.0, "share": 0.0, "unreadable": True, "bad": None, "read": None,
                "source": srcs, "wording_agreement": agrees,
                "verdict": "an ordered read never came back complete (%s) -> honest refusal; "
                           "no verdict is declared on a partial read" % ",".join(srcs)}
    ok = tot = 0
    bad = []
    for gi, (got, tgt) in enumerate(pairs):
        for i, t in enumerate(tgt):
            tot += 1
            if got[i] == t:
                ok += 1
            else:
                bad.append([gi, i + 1, got[i], t])
    return {"law": 1.0 if ok == tot else 0.0, "share": round(ok / tot, 4),
            "unreadable": False, "bad": bad, "ok": ok, "tot": tot,
            "read": [p[0] for p in pairs], "want": [p[1] for p in pairs],
            "source": srcs, "wording_agreement": agrees}


def law_holds_score(groups, targets):
    """Score 1 when every panel's hat and scarf follow the repeating law."""
    r = _judge(groups, targets)
    if r["unreadable"]:
        return {"frac": 0.0, "unreadable": True, "source": r["source"], "verdict": r["verdict"]}
    r["frac"] = r["law"]
    r["verdict"] = ("%d/%d panel-cells obey the law -> %s -> frac %.1f%s"
                    % (r["ok"], r["tot"], "HOLDS" if r["law"] else "BROKEN", r["law"],
                       "" if r["law"] else "; first offence panel %d of read %d: read '%s', law "
                       "requires '%s'" % (r["bad"][0][1], r["bad"][0][0] + 1,
                                          r["bad"][0][2], r["bad"][0][3])))
    return r


def law_share_score(groups, targets):
    """The share of panel reads that match what the law requires."""
    r = _judge(groups, targets)
    if r["unreadable"]:
        return {"frac": 0.0, "unreadable": True, "source": r["source"], "verdict": r["verdict"]}
    r["frac"] = r["share"]
    r["verdict"] = ("%d of %d panel-cells match the law -> share %.4f (read %s vs required %s)"
                    % (r["ok"], r["tot"], r["share"], r["read"], r["want"]))
    return r

# end of code_5450bfcc79ad

# code: strip_reads_code

def _cx(b):
    return (float(b[1]) + float(b[3])) / 2.0


def _cy(b):
    return (float(b[0]) + float(b[2])) / 2.0


def _yes(a):
    return str(a).strip().lower().startswith('y')


def _reading_order(geo, ok, *cols):
    items = []
    for i in range(min(len(geo), len(ok))):
        if not _yes(ok[i]):
            continue
        items.append((geo[i], [(c[i] if i < len(c) else None) for c in cols]))
    items.sort(key=lambda it: _cy(it[0]))
    rows, cur = [], []
    for it in items:
        if cur and abs(_cy(it[0]) - _cy(cur[-1][0])) >= 0.5 * max(
                abs(float(it[0][2]) - float(it[0][0])),
                abs(float(cur[-1][0][2]) - float(cur[-1][0][0]))):
            rows.append(cur)
            cur = []
        cur.append(it)
    if cur:
        rows.append(cur)
    out = []
    for r in rows:
        out.extend(sorted(r, key=lambda it: _cx(it[0])))
    return out


def strip_reads(panel_boxes, pc, ph, ps, reference):
    """Read the hats and scarves panel by panel in reading order."""
    items = _reading_order((panel_boxes or {}).get('geometry') or [],
                           (pc or {}).get('answers') or [],
                           (ph or {}).get('answers') or [],
                           (ps or {}).get('answers') or [])
    hats = [str(v[0]) if v[0] is not None else '' for _b, v in items]
    scarves = [str(v[1]) if v[1] is not None else '' for _b, v in items]
    return {'hats': hats, 'scarves': scarves, 'n': len(items),
            'verdict': '%d panels confirmed by the ring; in reading order the hats read %s and '
                       'the scarves read %s' % (len(items), hats, scarves)}

# end of strip_reads_code
