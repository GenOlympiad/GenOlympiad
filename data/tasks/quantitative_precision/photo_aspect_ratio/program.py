# shared code: code_d0f588e92a6a
def frame_aspect_ratios(frames, image, n):
    """Width to height ratio of each photo frame, left to right, if exactly n are boxed."""
    g = frames.get('geometry') if isinstance(frames, dict) else frames
    if not g or len(g) != int(n):
        return {'ratios': None, 'no_read': True}
    W, H = image.size
    rows = []
    for b in g:
        ymin, xmin, ymax, xmax = [float(v) for v in b[:4]]
        wpx = abs(xmax - xmin) * float(W) / 1000.0
        hpx = abs(ymax - ymin) * float(H) / 1000.0
        if wpx < 8.0 or hpx < 8.0:
            return {'ratios': None, 'no_read': True}
        rows.append((0.5 * (xmin + xmax), wpx / hpx))
    rows.sort(key=lambda r: r[0])
    return {'ratios': [round(r[1], 4) for r in rows], 'no_read': False}

# end of code_d0f588e92a6a

# code: joincode
def worst_ratio_error(ratios, targets):
    """The largest gap between a measured frame ratio and its target ratio."""
    if ratios is None or len(ratios) != len(targets):
        return 9.99
    return round(max(abs(float(r) - float(t)) for r, t in zip(ratios, targets)), 4)

# end of joincode

# code: diagcode
def share_within_tolerance(ratios, targets, tol):
    """Share of frames whose ratio lies within tolerance of its target."""
    if ratios is None or len(ratios) != len(targets):
        return 0.0
    return round(sum(1 for r, t in zip(ratios, targets) if abs(float(r) - float(t)) <= float(tol)) / float(len(targets)), 4)

# end of diagcode
