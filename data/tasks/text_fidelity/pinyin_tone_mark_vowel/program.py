# shared code: code_bind_by_gloss
def bind_by_gloss(key_node, val_node, want):
    """Count lines whose read value matches what their own gloss calls for."""
    glosses = [''.join(ch for ch in str(x).lower() if ch.isalpha()) for x in ((key_node or {}).get('answers') or [])]
    values = [''.join(ch for ch in str(x).lower() if ch.isalpha()) for x in ((val_node or {}).get('answers') or [])]
    want = {str(k).lower(): str(v).lower() for k, v in dict(want or {}).items()}
    ok = sum(1 for i, k in enumerate(glosses) if k in want and i < len(values) and values[i] == want[k])
    return {'ok': ok, 'asked': len(glosses),
            'verdict': '%d of the %d lines agree with what their own entry calls for' % (ok, len(glosses))}

# end of code_bind_by_gloss
