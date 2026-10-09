"""Run a code step of an evaluation program."""
from __future__ import annotations
import sys
from ._base import register, resolve, align_by_printed_key
import logging

log = logging.getLogger(__name__)

_SHARED = {"align_by_printed_key": align_by_printed_key}


class _AttrDict(dict):
    def __getattr__(self, k):
        try:
            v = self[k]
        except KeyError:
            raise AttributeError(k)
        return _AttrDict(v) if isinstance(v, dict) else v


def _attr_ctx(ctx):
    return {k: (_AttrDict(v) if isinstance(v, dict) else v) for k, v in ctx.items()}


@register("run.code")
def op_run_code(ctx, step):
    """Execute the code of an evaluation program step and call the named function."""
    code = resolve(ctx, step["code"])
    call = resolve(ctx, step["call"])
    ns: dict = dict(_SHARED)
    ret = step.get("return")

    if ret == "coverage":
        funcname = call.split("(", 1)[0].strip()
        fname = f"<gt_{funcname}>"
        exec(compile(code, fname, "exec"), ns)
        executed = set()

        def tracer(frame, event, arg):
            if frame.f_code.co_filename == fname:
                executed.add(frame.f_lineno)
            return tracer
        old = sys.gettrace()
        sys.settrace(tracer)
        try:
            eval(compile(call, fname, "eval"), ns)
        finally:
            sys.settrace(old)
        return sorted(executed)

    exec(compile(code, "<gt_run>", "exec"), ns)
    if "value" in step:
        arg = resolve(ctx, step["value"])
        try:
            arg = float(arg)
        except (TypeError, ValueError):
            log.debug("error ignored in op_run_code", exc_info=True)
            pass
        return ns[call.strip()](arg)

    env = {**ns, **_attr_ctx(ctx)}
    return eval(call, env)
