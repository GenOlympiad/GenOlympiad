"""Control-flow operators: repeat a flow over a board, or fall back to a second read."""
from __future__ import annotations
from ._base import register, resolve, as_float

_FLOW_RUNNER = None


def _note_read(ctx, entry):
    tr = ctx.get("_read_trace")
    if isinstance(tr, list):
        tr.append(entry)


def set_flow_runner(fn):
    """Inject engine._run_flow(ctx, flow) -> (fail, seen)."""
    global _FLOW_RUNNER
    _FLOW_RUNNER = fn


def _fmt(flow, bindings):
    def sub(x):
        if isinstance(x, str):
            for k, v in bindings.items():
                x = x.replace("{" + str(k) + "}", str(v))
            return x
        if isinstance(x, list):
            return [sub(e) for e in x]
        if isinstance(x, dict):
            return {k: sub(v) for k, v in x.items()}
        return x
    return [sub(dict(step)) for step in flow]


@register("fallback.read")
def op_fallback_read(ctx, step):
    """Two-stage lazy evidence chain that prevents single-reader false zeros."""
    prim_flagged = any(resolve(ctx, f) for f in step.get("primary_flags", []))
    if not prim_flagged:
        v = resolve(ctx, step["primary"])
        pmin = step.get("primary_min")
        if pmin is not None:
            fv = as_float(v)
            if fv is not None and fv < float(pmin):
                prim_flagged = True
    if not prim_flagged:
        v = resolve(ctx, step["primary"])
        if v is not None and not (isinstance(v, dict) and (v.get("unreadable") or v.get("abstain"))):
            _note_read(ctx, {"op": "fallback.read", "out": step.get("out"), "stage": "primary",
                             "primary": step.get("primary")})
            return v
    if _FLOW_RUNNER is None:
        raise RuntimeError("fallback.read: engine flow runner not injected")
    subctx = dict(ctx)
    fail, _ = _FLOW_RUNNER(subctx, step["else"])
    if fail is None and not any(resolve(subctx, f) for f in step.get("else_flags", [])):
        v = resolve(subctx, step["else_value"])
        if v is not None and not (isinstance(v, dict) and (v.get("unreadable") or v.get("abstain"))):
            _note_read(ctx, {"op": "fallback.read", "out": step.get("out"), "stage": "vlm_fallback"})
            return v
    _note_read(ctx, {"op": "fallback.read", "out": step.get("out"), "stage": "exhausted"})
    return {"exhausted": True, "unreadable": True}


@register("board.foreach")
def op_board_foreach(ctx, step):
    """For each row of a variable-length live board, run `each` on that row and combine the fractions."""
    if _FLOW_RUNNER is None:
        raise RuntimeError("board.foreach: engine flow runner not injected")
    board = resolve(ctx, step["board"]) or []
    labels = resolve(ctx, step.get("labels", [])) or []
    only_if = step.get("only_if")
    fracs = []
    for i, row in enumerate(board):
        label = labels[i] if i < len(labels) else ""
        subctx = dict(ctx)
        subctx["board"] = row
        subctx["label"] = label
        if only_if is not None and not resolve(subctx, only_if):
            continue
        bindings = {"label": label}
        if isinstance(row, dict):
            bindings.update(row)
        _FLOW_RUNNER(subctx, _fmt(step["each"], bindings))
        fracs.append(as_float(subctx.get("frac"), 0.0))
    if not fracs:
        return 1.0
    return round(sum(fracs) / len(fracs), 4)
