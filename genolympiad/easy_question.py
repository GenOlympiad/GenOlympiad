"""Re-check an easy question that answered no, so it can only fail a task for the reason it states."""
from __future__ import annotations

import re
import logging

log = logging.getLogger(__name__)

_NO_BRANCH = re.compile(
    r"answer\s+no\s+(?:only\s+)?if\s+(?P<c>[^.?!]+)", re.I)
_NON_CLAUSE = re.compile(r"^\s*(?:you\s+cannot|it\s+is\s+unclear|unsure|in\s+doubt)\b", re.I)


def no_branch_clause(question):
    if not isinstance(question, str) or not question.strip():
        return ""
    m = _NO_BRANCH.search(question)
    if not m:
        return ""
    c = re.sub(r"\s+", " ", m.group("c")).strip().strip(",;: ")
    if not c or _NON_CLAUSE.match(c) or len(c.split()) < 3:
        return ""
    return c


def confirm_question(clause):
    c = clause[0].lower() + clause[1:] if clause[:1].isupper() else clause
    c = re.sub(r"^the\s+image\s+instead\s+shows\s+", "", c, flags=re.I)
    c = re.sub(r"^the\s+image\s+shows\s+", "", c, flags=re.I)
    c = re.sub(r"^it\s+shows\s+", "", c, flags=re.I)
    return ("Look at this whole picture. Does it show %s? "
            "Answer with the single word yes or no only." % c)


def _majority_yes(answers):
    y = n = 0
    for a in answers:
        s = str(a or "").strip().lower()
        if s.startswith("y"):
            y += 1
        elif s.startswith("n"):
            n += 1
    if y == n:
        return None
    return y > n


def clause_holds(image, clause, votes=3):
    from genolympiad import read_policy
    from genolympiad.ops import evidence_grounding as _vf
    q = confirm_question(clause)
    raw = []
    for k in range(int(votes)):
        try:
            raw.append(_vf._ask(image, read_policy.paraphrase(q, k)))
        except Exception:
            log.debug("error ignored in clause_holds", exc_info=True)
            raw.append(None)
    return _majority_yes(raw), {"question": q, "answers": [None if a is None else str(a)[:80]
                                                          for a in raw]}


def scene_ask_step(pt):
    for s in (pt.get("flow") or []):
        if isinstance(s, dict) and s.get("op") == "vlm.ask" and s.get("question") is not None:
            return s
    return None


def fired_no(ctx, step):
    out = step.get("out")
    if not out:
        return False
    a = ctx.get(out)
    if isinstance(a, dict):
        return False
    return str(a or "").strip().lower().startswith("n")


def verdict(ctx, pt, image, votes=3):
    step = scene_ask_step(pt)
    if step is None or not fired_no(ctx, step):
        return None
    try:
        from genolympiad.ops.recognize import _q as _resolve_q, _denumber_scene_q, _SCENE_Q_SIG
        q = _resolve_q(ctx, step)
        if _SCENE_Q_SIG in q:
            q = _denumber_scene_q(q)
    except Exception:
        log.debug("error ignored in verdict", exc_info=True)
        return None
    clause = no_branch_clause(q)
    if not clause:
        return None
    holds, rec = clause_holds(image, clause, votes=votes)
    if holds is not False:
        return None
    return {"rule": "A_no_branch_clause", "clause": clause, "confirm": rec,
            "detail": ("the easy question answered 'no', but its own question licenses that answer ONLY IF %r -- and the picture was asked and said that is not what it shows. A gate that breaks the rule printed in its own question may not shut the whole cell ( §5.2(b))."% clause)}
