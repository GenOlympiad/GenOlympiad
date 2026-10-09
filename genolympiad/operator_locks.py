"""Serialise the operators whose local models keep global state, so threads cannot corrupt them."""
import threading

_LOCK = threading.RLock()

NONSAFE = {"ocr.read"}


def _locked(fn, name):
    def call(*args, **kwargs):
        with _LOCK:
            return fn(*args, **kwargs)
    call.nonsafe_locked = True
    call.__name__ = name
    call.__doc__ = getattr(fn, "__doc__", None)
    return call


def install_nonsafe_locks():
    """Wrap every non-thread-safe operator in one process lock."""
    from genolympiad import ops
    wrapped = []
    for name in sorted(ops.OPS):
        fn = ops.OPS[name]
        if name in NONSAFE and not getattr(fn, "nonsafe_locked", False):
            ops.OPS[name] = _locked(fn, getattr(fn, "__name__", "op"))
            wrapped.append(name)
    return wrapped
