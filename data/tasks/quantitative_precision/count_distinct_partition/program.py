# shared code: code_a51815bc1876

def _band(err, core, margin):
    f = 1.0 - max(0.0, float(err) - float(core)) / max(float(margin), 1e-9)
    return round(min(1.0, max(0.0, f)), 4)


def ring_counts(colours, rings):
    cols = list(colours or [])
    counts, bad = [], False
    for c in cols:
        pair = rings.get(c)
        if not pair:
            bad = True
            counts.append(0)
            continue
        ring, crop = pair
        ans = (crop or {}).get("answers")
        if (ring or {}).get("unreadable") or (ring or {}).get("refused") or ans is None \
                or any(a is None for a in ans):
            bad = True
            counts.append(0)
            continue
        counts.append(sum(1 for a in ans if str(a).strip().lower().startswith("y")))
    return counts, bad


def score_colour_counts(colours, total, floor, ratio_cap, colour_reads):
    """Check the colour counts hit the total, all differ, meet the floor and obey the ratio cap."""
    colour_list = list(colours or [])
    k = len(colour_list)
    counts, bad = ring_counts(colour_list, colour_reads)
    total_read = sum(counts)
    times_seen = {}
    for v in counts:
        times_seen[v] = times_seen.get(v, 0) + 1
    n_unique = sum(1 for v in counts if times_seen[v] == 1)
    n_at_floor = sum(1 for v in counts if v >= int(floor))
    lo, hi = (min(counts), max(counts)) if counts else (0, 0)
    if ratio_cap is None:
        ratio_frac, ratio_ok, ratio = None, True, None
    else:
        ratio = (hi / float(lo)) if lo > 0 else 999.0
        ratio_ok = ratio <= float(ratio_cap) + 1e-9
        ratio_frac = round(max(0.0, min(1.0, 1.0 - max(0.0, ratio - float(ratio_cap)))), 4)
    lawful = 1.0 if (k > 0 and total_read == int(total) and n_unique == k and n_at_floor == k
                    and ratio_ok) else 0.0
    return {"counts": counts, "colours": colour_list, "k": k, "sum": total_read,
            "unreadable": bool(bad or k == 0),
            "verdict": "counts %s  sum %s (demanded %s)  all different %s  all >= %s %s  legal %s"
                       % (dict(zip(colour_list, counts)), total_read, total, n_unique == k, floor,
                          n_at_floor == k, lawful == 1.0),
            "total_frac": _band(abs(total_read - int(total)), 0, 3),
            "distinct_frac": round(n_unique / float(k), 4) if k else 0.0,
            "floor_frac": round(n_at_floor / float(k), 4) if k else 0.0,
            "ratio": ratio, "ratio_frac": ratio_frac, "legal": lawful}


def matches_equal_split(colours, decoy, colour_reads):
    """Score 1 if the colour counts read match the decoy equal split within one."""
    colour_list = list(colours or [])
    counts, bad = ring_counts(colour_list, colour_reads)
    if bad:
        return 0.0
    counts_sorted = sorted(counts)
    want = sorted(int(x) for x in (decoy or []))
    if not want or len(counts_sorted) != len(want):
        return 0.0
    return 1.0 if all(abs(a - b) <= 1 for a, b in zip(counts_sorted, want)) else 0.0

# end of code_a51815bc1876
