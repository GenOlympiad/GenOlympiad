"""Registered operators that wrap the shared computation library used by evaluation programs."""
from __future__ import annotations

from . import compute_library as C
from ._base import register, resolve
import logging

log = logging.getLogger(__name__)


def _arg(ctx, step, name, default=None):
    return resolve(ctx, step[name]) if name in step else default


def _arg_list(ctx, step, name, default=None):
    if name not in step:
        return default
    val = step[name]
    if isinstance(val, list):
        return [resolve(ctx, v) for v in val]
    return resolve(ctx, val)


@register("compare.band_multi")
def op_compare_band_multi(ctx, step):
    """Tolerance ramp over one value or many -> a fraction in [0, 1]."""
    return C.band_multi(_arg_list(ctx, step, "value"), _arg_list(ctx, step, "target"),
                        core=_arg(ctx, step, "core", 0.0),
                        margin=_arg(ctx, step, "margin", 0.0),
                        aggregate=_arg(ctx, step, "aggregate", "mean"),
                        space=_arg(ctx, step, "space", "linear"),
                        fold=_arg(ctx, step, "fold"),
                        clamp_floor=_arg(ctx, step, "clamp_floor", 0.0),
                        require_all=bool(_arg(ctx, step, "require_all", True)))


@register("compare.token_in")
def op_compare_token_in(ctx, step):
    """Canonicalise both sides, then match -> 1.0 or 0.0."""
    return C.token_in(_arg(ctx, step, "value"), _arg(ctx, step, "target"),
                      vocabulary=_arg_list(ctx, step, "vocabulary"),
                      keep=_arg(ctx, step, "keep", "alnum"),
                      mode=_arg(ctx, step, "mode", "substring"))


@register("read.count_yes")
def op_read_count_yes(ctx, step):
    return C.count_yes(_arg(ctx, step, "value"), prefix=_arg(ctx, step, "prefix", "y"))


@register("geom.grid_cells")
def op_geom_grid_cells(ctx, step):
    """Confirmed board box -> per-cell rectangles, row-major."""
    return C.grid_cells(_arg(ctx, step, "value"), _arg(ctx, step, "rows"),
                        _arg(ctx, step, "cols"), inset=float(_arg(ctx, step, "inset", 0.0)),
                        round_to=_arg(ctx, step, "round_to", 2),
                        min_side=float(_arg(ctx, step, "min_side", 0.0)),
                        square_tol=_arg(ctx, step, "square_tol"))


@register("combine.product")
def op_combine_product(ctx, step):
    vals = _arg(ctx, step, "value")
    if vals is None and "values" in step:
        vals = [resolve(ctx, v) for v in step["values"]]
    return C.product(vals)


