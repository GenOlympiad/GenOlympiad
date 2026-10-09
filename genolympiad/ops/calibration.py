"""Map a flood status word to its rank: none, action, minor, moderate, major."""
from __future__ import annotations
from ._base import register, resolve

_FLOOD_RANK = {"no-flooding": 0, "no flooding": 0, "none": 0, "normal": 0, "no": 0,
               "action": 1, "minor": 2, "minor flood": 2, "moderate": 3,
               "moderate flood": 3, "major": 4, "major flood": 4}


@register("calib.apply")
def op_calib_apply(ctx, step):
    """Map a value through a named calibration curve."""
    curve = step["curve"]
    val = resolve(ctx, step["value"])
    if curve == "flood_status_rank":
        if val is None:
            return None
        key = str(val).strip().lower().replace("_", "-")
        return _FLOOD_RANK.get(key, _FLOOD_RANK.get(key.split()[0] if key.split() else key))
    raise KeyError(f"calib.apply: unknown curve '{curve}'")
