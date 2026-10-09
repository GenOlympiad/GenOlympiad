"""Settings for the check that every instance of an object has a bounding box."""


def deficit_probe_note(n_count, n_boxed):
    return ("recall v2: the reader says every one is boxed, but the check's OWN independent count "
            "read says about %d and only %d are boxed. A deficit of %d is inside the shipped "
            "slack, which would certify here -- this probe spends ONE directed ask on the "
            "difference first. Anything it finds still faces its own cut-out confirmation and the "
            "unchanged whole-set gate." % (n_count, n_boxed, n_count - n_boxed))


def deficit_result_note(n_count, n_boxed_before, added):
    if added:
        return ("recall deficit probe: %d further %s confirmed (%d -> %d boxes) -- the sweep "
                "continues on the grown set and must reach its terminal 'no' again."
                % (added, "box" if added == 1 else "boxes", n_boxed_before, n_boxed_before + added))
    return ("recall deficit probe: the directed ask found nothing the cut-out confirmation "
            "would accept, so the count read (~%d) does not overturn the reader's 'all boxed' at "
            "%d -- certified."
            % (n_count, n_boxed_before))


