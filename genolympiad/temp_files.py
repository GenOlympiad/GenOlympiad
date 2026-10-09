"""Scratch files the judge makes while it evaluates one task, removed when the task is done."""
import os
import shutil
import threading

_LOCK = threading.Lock()
_OWNED = {}


def own(path):
    """Record a scratch file or folder as belonging to the current thread's task."""
    with _LOCK:
        _OWNED[os.path.abspath(str(path))] = threading.get_ident()
    return path


def retire_task():
    """Remove every scratch path the current thread recorded; returns how many were removed."""
    me = threading.get_ident()
    with _LOCK:
        mine = [p for p, t in _OWNED.items() if t == me]
        for p in mine:
            del _OWNED[p]
    removed = 0
    for p in mine:
        if os.path.isdir(p):
            shutil.rmtree(p)
            removed += 1
        elif os.path.exists(p):
            os.remove(p)
            removed += 1
    return removed
