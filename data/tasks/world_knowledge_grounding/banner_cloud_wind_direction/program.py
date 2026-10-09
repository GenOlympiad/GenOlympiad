# code: bearing_code

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


_DIRS = ('up', 'down', 'left', 'right',
         'up-left', 'up-right', 'down-left', 'down-right')
_BASE = {'up': 'N', 'up-right': 'NE', 'right': 'E', 'down-right': 'SE',
         'down': 'S', 'down-left': 'SW', 'left': 'W', 'up-left': 'NW'}
_ORDER = ('N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW')


def _dir_word(s):
    t = str(s or '').strip().lower().replace('_', '-').replace(' to the ', ' ')
    t = t.replace('upper', 'up').replace('lower', 'down').replace('top', 'up')
    t = t.replace('bottom', 'down')
    up, down = ('up' in t), ('down' in t)
    left, right = ('left' in t), ('right' in t)
    if up and down or left and right:
        return None
    v = 'up' if up else ('down' if down else '')
    h = 'left' if left else ('right' if right else '')
    if v and h:
        return v + '-' + h
    return v or h or None


def plume_compass_bearing(plume_read, rose_read, target):
    """Turn the plume's direction in the picture into a compass point using the drawn N arrow."""
    plume_dir = _dir_word(_ans(plume_read))
    north_dir = _dir_word(_ans(rose_read))
    if plume_dir is None:
        return {'frac': 0.0, 'token': None,
                'verdict': 'the cut-out did not settle which way the plume streams'}
    if north_dir is None:
        return {'frac': 0.0, 'token': None,
                'verdict': 'the cut-out did not settle which way the compass N arrow points'}
    plume_point = _BASE[plume_dir]
    north_point = _BASE[north_dir]
    k = (_ORDER.index(plume_point) - _ORDER.index(north_point)) % 8
    bearing_point = _ORDER[k]
    wanted = str(target).strip().upper()
    return {'frac': 1.0 if bearing_point == wanted else 0.0, 'token': bearing_point, 'plume': plume_dir, 'rose_n': north_dir,
            'verdict': 'the plume streams %s across the picture and the N arrow points %s, so '
                       'the plume points %s (want %s)' % (plume_dir, north_dir, bearing_point, wanted)}

# end of bearing_code
