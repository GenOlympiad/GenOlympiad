# shared code: code_f8ecc93f4100
def _order(node):
    g = [[float(v) for v in b] for b in ((node or {}).get('geometry') or [])]
    g.sort(key=lambda b: (b[1] + b[3]) / 2.0)
    return g


def water_read(water_boxes):
    """The water depth in each jar, with the jars ordered left to right."""
    g = _order(water_boxes)
    depths = [round(b[2] - b[0], 2) for b in g]
    return {'n_cols': len(g), 'depths': depths, 'boxes': g}


def rod_read(rod):
    """The rod heights left to right, the gaps between them and their spread."""
    g = _order(rod)
    rod_heights = [round((b[0] + b[2]) / 2.0, 2) for b in g]
    gaps = [round(rod_heights[i] - rod_heights[i + 1], 2) for i in range(len(rod_heights) - 1)]
    spread = round((max(rod_heights) - min(rod_heights)) / 1000.0, 4) if len(rod_heights) >= 2 else 0.0
    return {'n_rods': len(g), 'rod_y': rod_heights, 'gaps': gaps, 'rod_spread_frac': spread,
            'boxes': g}


def gauges_readable_frac(column_confirms, rod_confirms, k):
    """1 if exactly k water columns and k rods are confirmed, else 0."""
    def nyes(node):
        a = [str(x or '').strip().lower() for x in ((node or {}).get('answers') or [])]
        return sum(1 for x in a if x.startswith('y'))
    n_columns, n_rods = nyes(column_confirms), nyes(rod_confirms)
    return {'frac': 1.0 if (n_columns == int(k) and n_rods == int(k)) else 0.0,
            'n_cols': n_columns, 'n_rods': n_rods, 'k': int(k)}


def stepped_frac(rods, min_spread):
    """1 if the rods spread over at least the minimum share of the height, else 0."""
    return {'frac': 1.0 if float(rods.get('rod_spread_frac') or 0.0) >= float(min_spread)
            else 0.0, 'rod_spread_frac': rods.get('rod_spread_frac')}


def _bandfrac(err, core, margin):
    err = abs(float(err))
    if err <= core:
        return 1.0
    if err >= margin:
        return 0.0
    return round(1.0 - (err - core) / (margin - core), 4)


def equal_depth_frac(water, core=0.12, margin=0.40):
    """Score how close the deepest and shallowest water depths are to equal."""
    depths = [v for v in (water.get('depths') or []) if v > 0]
    if len(depths) < 2:
        return {'frac': 0.0, 'ratio': None}
    ratio = max(depths) / float(min(depths))
    return {'frac': _bandfrac(ratio - 1.0, core, margin), 'ratio': round(ratio, 3),
            'depths': depths}


def rod_ladder_frac(rods, ratios, core=0.12, margin=0.30):
    """Score how closely the gaps between the rods follow the wanted ratios."""
    gaps = list(rods.get('gaps') or [])
    wanted = [float(x) for x in ratios]
    if len(gaps) != len(wanted):
        return {'frac': 0.0, 'gaps': gaps, 'want': wanted}
    mean_gap = sum(gaps) / float(len(gaps))
    if mean_gap <= 0:
        return {'frac': 0.0, 'gaps': gaps, 'want': wanted, 'note': 'ladder runs the wrong way'}
    mean_wanted = sum(wanted) / float(len(wanted))
    worst = 0.0
    for gi, ti in zip(gaps, wanted):
        tn = ti / mean_wanted
        worst = max(worst, abs(gi / mean_gap - tn) / max(1e-6, tn))
    return {'frac': _bandfrac(worst, core, margin), 'gaps': gaps, 'want': wanted,
            'worst_rel_err': round(worst, 4)}

# end of code_f8ecc93f4100
