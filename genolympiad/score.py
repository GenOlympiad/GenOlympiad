"""Evaluate one task on one generated image and return its score."""
from __future__ import annotations

import hashlib
import logging

from . import tasks

log = logging.getLogger(__name__)
_READY = {"done": False}


def prepare():
    """Load the evaluation pipeline once per process: operators and thread locks."""
    if _READY["done"]:
        return
    from . import operator_locks, ops
    assert ops.OPS
    operator_locks.install_nonsafe_locks()
    _READY["done"] = True


def _sha256_file(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def _held_reasons(tree, held):
    """{check id: reason text} for the checks the evaluation program could not measure."""
    out = {}

    def walk(node):
        if not isinstance(node, dict):
            return
        o = node.get("output") or {}
        if node.get("id") in held and isinstance(o, dict):
            why = o.get("held_reason") or node.get("detail")
            if why:
                out[node["id"]] = str(why)
        for c in node.get("children") or []:
            walk(c)

    walk(tree or {})
    return out


_NO_ANSWER = ("no answer", "did not answer", "unanswered", "returned nothing", "lint",
              "would not answer", "hung")


def _withheld_reason(reasons):
    if reasons and all(any(w in r.lower() for w in _NO_ANSWER) for r in reasons.values()):
        return "vlm_refusal"
    return "grounding_failure"


def judge(entry, image_path):
    """The score of one task: relaxed and strict scores, or withheld with a reason."""
    from . import evaluation_tree, shared_anchors, read_limits, temp_files
    from . import evaluation_plans as templates
    prepare()
    prompt = tasks.prompt_of(entry)
    score = {"task_id": entry["task_id"], "axis": entry["axis"], "relaxed": None, "strict": None,
             "status": "withheld", "withheld_reason": None, "questions": [],
             "image_sha256": _sha256_file(image_path),
             "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(), "vlm_reads": 0}
    counter = read_limits.begin_task_count()
    shared_anchors.task_reset()
    try:
        task, reference = tasks.evaluation_task(entry)
        plan = templates.plan_for_task(task, diagnostics=True)
        res = evaluation_tree.agentic_score(task, image_path, plan, reference_override=reference)
        score["questions"] = [
            {"id": q["id"], "type": "easy" if q.get("gate") else "hard",
             "weight": q.get("weight"), "passed": q.get("score") is not None and q["score"] >= 1.0}
            for q in evaluation_tree.flatten_questions(res["tree"])]
        held = list(res.get("evaluator_held") or [])
        if res.get("conflicts"):
            held += [c.get("bearing") for c in res["conflicts"] if c.get("bearing")]
        if res["graded"] is not None and not held and not shared_anchors.disagreements():
            score.update(relaxed=res["graded"], strict=res["strict"], status="scored")
        elif held:
            reasons = _held_reasons(res.get("tree"), set(held))
            score["withheld_reason"] = _withheld_reason(reasons)
        elif shared_anchors.disagreements():
            score["withheld_reason"] = "grounding_failure"
        else:
            score["withheld_reason"] = "evaluator_failure"
    except Exception as e:
        log.warning("evaluation failed for %s: %s: %s", entry["task_id"], type(e).__name__, e)
        score.update(status="withheld", withheld_reason="evaluator_failure", relaxed=None,
                     strict=None)
    finally:
        read_limits.end_task_count()
        temp_files.retire_task()
    score["vlm_reads"] = counter[0]
    return score
