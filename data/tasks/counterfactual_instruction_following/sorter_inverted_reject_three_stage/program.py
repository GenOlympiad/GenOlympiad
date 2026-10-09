# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# shared code: code_route_map
def read_route_deck(codes, dirs):
    """Pair each stage code with its arrow direction; refuse unless exactly six distinct coded arrows are read."""
    import re
    routes = {}
    for c, direction in zip(((codes or {}).get('answers') or []), ((dirs or {}).get('answers') or [])):
        m = re.findall(r's\s*(\d)\D*(pass|fail)', str(c).lower())
        direction_text = str(direction).lower()
        route = 'reject' if 'reject' in direction_text else ('onward' if 'onward' in direction_text else '')
        if not m or not route or ('s' + m[0][0] + m[0][1]) in routes:
            return {'unreadable': True, 'canon': '', 'map': {}, 'verdict': 'an arrow gave back no stage code, no direction, or a code already seen -> honest refusal'}
        routes['s' + m[0][0] + m[0][1]] = route
    canon = ' '.join('%s:%s' % (k, routes[k]) for k in sorted(routes))
    if len(routes) != 6:
        return {'unreadable': True, 'canon': canon, 'map': {}, 'verdict': 'the deck gave back %d coded arrows, not six -> honest refusal' % len(routes)}
    return {'unreadable': False, 'canon': canon, 'map': routes, 'verdict': 'the deck reads %s' % canon}

# end of code_route_map

# shared code: code_board_map
def read_count_boards(names, nums):
    """Pair each board name with its figure; refuse unless exactly four distinct boards are read."""
    import re
    boards = {}
    for n, figure in zip(((names or {}).get('answers') or []), ((nums or {}).get('answers') or [])):
        board = ''.join(ch for ch in str(n).lower() if ch.isalnum())
        digits = re.findall(r'\d+', str(figure))
        if not board or not digits or board in boards:
            return {'unreadable': True, 'canon': '', 'map': {}, 'verdict': 'a board gave back no name, no figure, or a name already seen -> honest refusal'}
        boards[board] = int(digits[0])
    canon = ' '.join('%s:%d' % (board, boards[board]) for board in sorted(boards))
    if len(boards) != 4:
        return {'unreadable': True, 'canon': canon, 'map': {}, 'verdict': 'the line gave back %d headed boards, not four -> honest refusal' % len(boards)}
    return {'unreadable': False, 'canon': canon, 'map': boards, 'verdict': 'the boards read %s' % canon}

# end of code_board_map

# shared code: code_agree
def boards_match_routing(route_read, board_read, weights, limits, want):
    """Route the parcel weights through the painted deck and check the boards show the same counts as the wanted result."""
    routes = (route_read or {}).get('map') or {}
    boards = (board_read or {}).get('map') or {}
    def nums(s):
        out = []
        for x in str(s).replace(',', ' ').split():
            try:
                out.append(float(x))
            except ValueError:
                pass
        return out
    parcel_weights, stage_limits = nums(weights), nums(limits)
    got = {'chute1': 0, 'chute2': 0, 'chute3': 0, 'despatch': 0}
    for w in parcel_weights:
        for i, limit in enumerate(stage_limits):
            if routes.get('s%d%s' % (i + 1, 'pass' if w > limit else 'fail')) == 'reject':
                got['chute%d' % (i + 1)] += 1
                break
        else:
            got['despatch'] += 1
    sent = ' '.join('%s:%d' % (k, got[k]) for k in sorted(got))
    shown = ' '.join('%s:%s' % (k, boards.get(k)) for k in sorted(got))
    ok = bool(routes) and bool(boards) and sent == ' '.join('%s:%s' % (k, boards.get(k)) for k in sorted(got)) and sent == str(want)
    return {'unreadable': False, 'ok': 'yes' if ok else 'no', 'verdict': 'the deck as painted sends %s and the boards show %s' % (sent, shown)}

# end of code_agree
