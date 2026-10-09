# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# code: bead_sum_code
def count_beads_all_trays(tray_a, tray_b, tray_c):
    """Add up the beads confirmed in each of the three trays."""
    def n_yes(node): return sum(1 for x in ((node or {}).get('answers') or []) if str(x).strip().lower().startswith('y'))
    def asked(node): return len((node or {}).get('answers') or [])
    na, nb, nc = n_yes(tray_a), n_yes(tray_b), n_yes(tray_c)
    return {'n': na + nb + nc, 'asked': asked(tray_a) + asked(tray_b) + asked(tray_c), 'per_tray': [na, nb, nc], 'verdict': 'beads confirmed tray by tray: %d + %d + %d = %d' % (na, nb, nc, na + nb + nc)}
# end of bead_sum_code
