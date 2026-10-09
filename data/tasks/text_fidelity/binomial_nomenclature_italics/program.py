# shared code: code_face_switch
def face_switch(name_node, auth_node, sur_node, want_name, want_auth):
    """Count lines that print a surname, slant the two name words and keep the surname upright."""
    name_faces = [str(x).strip().lower() for x in ((name_node or {}).get('answers') or [])]
    author_faces = [str(x).strip().lower() for x in ((auth_node or {}).get('answers') or [])]
    surnames = [''.join(c for c in str(x).lower() if c.isalpha()) for x in ((sur_node or {}).get('answers') or [])]
    dead = ('', 'blank', 'none', 'na', 'empty', 'nil', 'notfilled', 'nosurname', 'unknown', 'unclear')
    wn, wa = str(want_name).lower()[:5], str(want_auth).lower()[:5]
    ok = sum(1 for i, n in enumerate(name_faces)
             if i < len(author_faces) and i < len(surnames) and surnames[i] not in dead
             and n.startswith(wn) and author_faces[i].startswith(wa))
    return {'ok': ok, 'asked': len(name_faces),
            'verdict': '%d of the %d lines print a surname, slant the two name words and leave that surname upright' % (ok, len(name_faces))}

# end of code_face_switch

# shared code: code_key_bind
def brackets_by_genus(key_node, flag_node, want):
    """Count lines whose author brackets match what the record for that genus calls for."""
    genera = [''.join(ch for ch in str(x).lower() if ch.isalpha()) for x in ((key_node or {}).get('answers') or [])]
    bracket_flags = [str(x).strip().lower()[:1] for x in ((flag_node or {}).get('answers') or [])]
    want = dict(want or {})
    ok = 0
    for i, k in enumerate(genera):
        if k in want and i < len(bracket_flags) and bracket_flags[i] == str(want[k]).lower()[:1]:
            ok += 1
    return {'ok': ok, 'asked': len(genera),
            'verdict': '%d of the %d lines bracket the authority the way their own record calls for' % (ok, len(genera))}

# end of code_key_bind
