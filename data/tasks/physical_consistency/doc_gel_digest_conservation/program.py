# code: helpers
from genolympiad.task_helpers import (
    count_confirmed_cutouts, count_listed_items, paint_cells_by_fraction, plan_grid_from_read_count)
# end of helpers

# shared code: code_gel_sizes
def sizes_of(reads):
    """The band sizes read as whole numbers, with their total and count."""
    import re
    sizes = []
    for a in (reads or {}).get('answers') or []:
        m = re.search(r'\d+', str(a).replace(',', ''))
        if m:
            sizes.append(int(m.group()))
    return {'sizes': sizes, 'total': sum(sizes), 'n': len(sizes)}

# end of code_gel_sizes

# shared code: code_gel_tieout
def sample_bands_fit_ladder(ladder_boxes, ladder_reads, sample_boxes, sample_reads):
    """Share of sample bands whose height on the gel agrees with the ladder's size order."""
    import re
    def rows(g, a):
        out = []
        for i, s in enumerate((a or {}).get('answers') or []):
            m = re.search(r'\d+', str(s).replace(',', ''))
            if m and i < len((g or {}).get('geometry') or []):
                out.append((float(g['geometry'][i][0]), int(m.group())))
        return sorted(out)
    ladder, sample = rows(ladder_boxes, ladder_reads), rows(sample_boxes, sample_reads)
    fits = [1 for y, v in sample if ladder and all((b - y) * (w - v) <= 0 for b, w in ladder)]
    return {'n': len(sample), 'hits': len(fits), 'frac': (len(fits) / len(sample)) if sample else 0.0}

# end of code_gel_tieout
