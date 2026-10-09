"""Decide what happens when two checks of a task read the same thing differently."""
from __future__ import annotations
import logging

log = logging.getLogger(__name__)

RULE_DECIDE = "rule_decide"
RULE_RAW = "rule_raw"


def _int(v):
    if isinstance(v, bool) or v is None:
        return None
    try:
        return int(v)
    except (TypeError, ValueError):
        log.debug("error ignored in _int", exc_info=True)
        return None


def decide(count_check, confirmed, allow=None, target=None, reverse=False):
    cc, cf = _int(count_check), _int(confirmed)
    if cc is None or cf is None:
        return (False, None)
    raw = (cc != cf)
    a, t = _int(allow), _int(target)
    if reverse and a is not None:
        dec = (cc > a) != (cf > a)
    elif t is not None:
        dec = (cc == t) != (cf == t)
    else:
        dec = raw
    return (raw, dec)


def _sweep_info(d):
    if not isinstance(d, dict):
        return None
    s = d.get("sweep")
    if isinstance(s, dict) and s.get("count_check") is not None:
        return s
    return None


def witnesses(ctx, seen=None):
    if not isinstance(ctx, dict):
        return None
    read, info = None, None
    for v in ctx.values():
        s = _sweep_info(v)
        if s is not None:
            read, info = v, s
            break
    if info is None:
        return None
    cc = _int(info.get("count_check_final"))
    if cc is None:
        cc = _int(info.get("count_check"))
    if cc is None:
        return None
    reverse = bool(read.get("absent_ok")) or bool(info.get("reverse_sweep"))
    allow = _int(read.get("allow"))
    confirmed, src = None, None
    if reverse:
        confirmed, src = _int(read.get("n_confirmed")), "n_confirmed"
    if confirmed is None:
        for v in ctx.values():
            if isinstance(v, dict) and "n" in v and "asked" in v:
                confirmed, src = _int(v.get("n")), "cnt_read.n"
                break
    if confirmed is None and read.get("n_confirmed") is not None:
        confirmed, src = _int(read.get("n_confirmed")), "n_confirmed"
    if confirmed is None:
        return None
    target = None
    if isinstance(seen, dict):
        target = _int(seen.get("target"))
    return {"count_check": cc, "confirmed": confirmed, "confirmed_src": src,
            "allow": allow, "target": target, "reverse": reverse}


def verdict(ctx, seen=None):
    w = witnesses(ctx, seen)
    if w is None:
        return None
    raw, dec = decide(w["count_check"], w["confirmed"], w["allow"], w["target"], w["reverse"])
    if dec:
        rule = RULE_DECIDE
        why = ("the check's own two witnesses reach OPPOSITE CONCLUSIONS about this picture: the independent count read says %s and the per-crop confirmation (%s) says %s, against %s. A check that cannot get its own two readings to agree may not shut the whole cell."
               % (w["count_check"], w["confirmed_src"], w["confirmed"],
                  ("allow %s" % w["allow"]) if w["reverse"] else ("target %s" % w["target"])))
    elif raw:
        rule = RULE_RAW
        why = ("the check's two witnesses agree on the VERDICT but not on the NUMBER (count read %s vs %s %s) -- verdict unchanged." % (w["count_check"], w["confirmed_src"], w["confirmed"]))
    else:
        return None
    return dict(w, rule=rule, detail=why)
