# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# shared code: code_shape_bind
def drop_shapes_match(coated_read, bare_read):
    """Yes if the coated half shows a beaded drop and the bare half a spread film."""
    coated_shape = str((((coated_read or {}).get('answers') or [''])[0]) or '').strip().lower()
    bare_shape = str((((bare_read or {}).get('answers') or [''])[0]) or '').strip().lower()
    ok = 'yes' if (coated_shape.startswith('bead') and bare_shape.startswith('film')) else 'no'
    return {'coated': coated_shape, 'bare': bare_shape, 'ok': ok,
            'verdict': 'drop on the COATED half reads %s, drop on the BARE half reads %s '
                       '-> label-to-shape binding %s' % (coated_shape, bare_shape, ok)}

# end of code_shape_bind
