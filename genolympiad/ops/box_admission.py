"""Rules that decide whether a proposed bounding box may join the set of boxes."""
from __future__ import annotations

import logging

log = logging.getLogger(__name__)

FRAME_AREA = 1000.0 * 1000.0

FRAME_FRAC = 0.90
AREA_MULT = 4.0


def area01k(b):
    try:
        return max(0.0, float(b[2]) - float(b[0])) * max(0.0, float(b[3]) - float(b[1]))
    except (TypeError, ValueError, IndexError):
        log.debug("error ignored in area01k", exc_info=True)
        return 0.0


def shield_disqualified(k, others):
    a = area01k(k)
    if a >= FRAME_FRAC * FRAME_AREA:
        return True, "the covering box is %.0f%% of the frame" % (100.0 * a / FRAME_AREA)
    areas = [v for v in (area01k(b) for b in (others or [])) if v > 0]
    if areas:
        biggest = max(areas)
        if a > AREA_MULT * biggest:
            return True, ("the covering box is %.1fx the largest other kept box (limit %.1fx)"
                          % (a / biggest, AREA_MULT))
    return False, None


def giant_backstop(box):
    a = area01k(box)
    if a >= FRAME_FRAC * FRAME_AREA:
        return True, "covers %.0f%% of the frame" % (100.0 * a / FRAME_AREA)
    return False, None


def admit(kept, extra, merge, thr, provenance="", transcript=None, info=None):
    return merge(kept, extra, thr)
