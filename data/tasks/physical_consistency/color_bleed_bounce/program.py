# code: halves_code

def _ans(node, i=0):
    if isinstance(node, dict):
        a = node.get('answers') or []
        return a[i] if i < len(a) else None
    return node


def _boxes(node):
    if isinstance(node, dict):
        g = node.get('geometry')
        return list(g) if g else []
    return list(node or [])


def _cx(b):
    return (float(b[1]) + float(b[3])) / 2.0


def _cy(b):
    return (float(b[0]) + float(b[2])) / 2.0


def split_ball_halves(ball_node, wall_node):
    """Split the ball box into the half nearer the wall and the half farther away."""
    ball_boxes = _boxes(ball_node)
    wall_boxes = _boxes(wall_node)
    if not ball_boxes or not wall_boxes:
        return {'near': [], 'far': [], 'no_read': True}
    y0, x0, y1, x1 = [float(v) for v in ball_boxes[0][:4]]
    x_mid = (x0 + x1) / 2.0
    wall_left = _cx(wall_boxes[0]) < x_mid
    left = [y0, x0, y1, x_mid]
    right = [y0, x_mid, y1, x1]
    near, far = (left, right) if wall_left else (right, left)
    return {'near': [near], 'far': [far], 'wall_side': 'left' if wall_left else 'right'}

# end of halves_code

# code: tint_code
def tint_matches(node, want):
    """Whether the tint read, reddish or white, matches the wanted one."""
    answer = ((node or {}).get("answers") or [None])[0]
    s = str(answer or "").strip().lower()
    red = ("red" in s) or ("pink" in s)
    white = ("white" in s) or ("neutral" in s)
    if red == white:
        return "unclear"
    read_tint = "reddish" if red else "white"
    return "yes" if read_tint == str(want) else "no"

# end of tint_code
