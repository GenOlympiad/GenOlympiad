"""Run a task's evaluation program step by step and combine the checks into a score."""
from __future__ import annotations
import os
from PIL import ImageFont
from . import ops as _ops
import logging

log = logging.getLogger(__name__)


def _run_flow_public(ctx, flow):
    return _run_flow(ctx, flow)


_ops.set_flow_runner(_run_flow_public)


_FONT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "fonts")


def _font(sz):
    for p in (os.path.join(_FONT_DIR, "DejaVuSansMono.ttf"),
              os.path.join(_FONT_DIR, "DejaVuSans.ttf")):
        if os.path.exists(p):
            return ImageFont.truetype(p, sz)
    for name in ("consola.ttf", "arial.ttf", "DejaVuSansMono.ttf"):
        try:
            return ImageFont.truetype(name, sz)
        except Exception:
            log.debug("error ignored in _font", exc_info=True)
            pass
    return ImageFont.load_default()


def _run_flow(ctx, flow):
    seen = {}
    for i, step in enumerate(flow):
        out = _ops.OPS[step["op"]](ctx, step)
        if isinstance(out, _ops.Fail):
            return out, seen
        if "out" in step:
            ctx[step["out"]] = out
        if step["op"].startswith("compare."):
            seen["value"] = _ops.resolve(ctx, step.get("value"))
            seen["target"] = _ops.resolve(ctx, step.get("target"))
            seen["target_ref"] = (step.get("target")
                                  if isinstance(step.get("target"), str) else None)
            seen.pop("target_band_text", None)
    return None, seen


import re as _re


_DIAG_LEAF_RE = _re.compile(r"^d\d+_")


def _is_diagnostic_leaf(pt_id: str, pt=None) -> bool:
    if isinstance(pt, dict) and pt.get("d2"):
        return True
    return bool(isinstance(pt_id, str) and _DIAG_LEAF_RE.match(pt_id))


_FAMILY_PREFIXES = (
    ("detect.", "box step"), ("headcount.", "box step"),
    ("compute.", "check_net"), ("overlay.", "check_net"), ("measure.", "check_net"),
    ("vlm.", "vlm"),
    ("ocr.", "ocr"), ("table.", "ocr"), ("read.", "ocr"), ("music.", "ocr"),
    ("braille.", "ocr"), ("text.", "ocr"),
    ("cv.", "cv"), ("segment.", "cv"), ("pose.", "cv"), ("color.", "cv"), ("grid.", "cv"),
    ("run.code", "code"), ("logic.", "code"), ("calib.", "code"),
    ("fetch.", "data"),
)


def _op_family(op):
    o = str(op or "")
    for pre, fam in _FAMILY_PREFIXES:
        if o.startswith(pre):
            return fam
    return (o.split(".")[0] or "unknown")


def _all_steps(flow):
    for s in flow or []:
        if not isinstance(s, dict):
            continue
        yield s
        for key in ("else", "each"):
            if isinstance(s.get(key), list):
                for t in _all_steps(s[key]):
                    yield t


def _producer_of(flow, name):
    if not name:
        return None
    got = None
    for s in _all_steps(flow):
        if s.get("out") == name:
            got = s
    return got


def _thru_code(flow, step, depth=4):
    for _ in range(depth):
        if step is None or str(step.get("op", "")) != "run.code":
            break
        refs = []
        for key in ("value", "call"):
            v = step.get(key)
            if isinstance(v, str):
                refs += _re.findall(r"[A-Za-z_]\w*", v)
        nxt = None
        for r in refs:
            p = _producer_of(flow, r)
            if p is not None and p is not step:
                nxt = p
                break
        if nxt is None:
            break
        step = nxt
    return step


def _bearing_ref(pt):
    flow = pt.get("flow") or []
    score_ref = pt.get("score")
    head = str(score_ref).split(".")[0] if isinstance(score_ref, str) else None
    cand = _producer_of(flow, head)
    if not (cand and str(cand.get("op", "")).startswith("compare.")):
        cand = None
        for s in _all_steps(flow):
            if str(s.get("op", "")).startswith("compare."):
                cand = s
    if not cand:
        return None
    v = cand.get("value")
    return str(v).split(".")[0] if isinstance(v, str) else None


def bearing_source(pt, read_trace=None):
    flow = pt.get("flow") or []
    name = _bearing_ref(pt)
    step = _producer_of(flow, name)
    if step is None:
        reads = [s for s in _all_steps(flow) if s.get("out") and s.get("op") != "guard.fail"]
        step = reads[-1] if reads else None
    step = _thru_code(flow, step)
    if step is None:
        return "none"
    op = str(step.get("op", ""))
    if op != "fallback.read":
        return _op_family(op)
    ev = None
    for e in (read_trace or []):
        if isinstance(e, dict) and e.get("op") == "fallback.read" and e.get("out") == step.get("out"):
            ev = e
    stage = (ev or {}).get("stage")
    prim = _thru_code(flow, _producer_of(flow, str(step.get("primary", "")).split(".")[0]))
    prim_fam = _op_family(prim.get("op")) if prim else "unknown"
    if stage == "primary":
        return prim_fam
    if stage == "vlm_fallback":
        return "vlm_fallback"
    if stage in ("exhausted", "fallback_denied"):
        return "none"
    return prim_fam + "?"


_DIAG_ID_RE = _re.compile(r"^d\d+_|_xev$|(^|_)(crossevidence|consistency)(_|$)")


def _ref_head_in_live(ref, live_out_fields):
    if not isinstance(ref, str) or not live_out_fields:
        return False
    parts = ref.split(".")
    if parts[0] == "gt" and len(parts) >= 2:
        return parts[1] in live_out_fields
    return parts[0] in live_out_fields


def _point_live_refs(pt):
    refs = []
    for step in pt.get("flow", []):
        t = step.get("target")
        if isinstance(t, str):
            refs.append(t)
        q = step.get("question")
        if isinstance(q, str):
            refs += _re.findall(r"\{([A-Za-z_][\w.]*)\}", q)
    return refs


def _point_needs_unavailable_live_gt(pt, gt, live_out_fields):
    gctx = {"gt": gt, **gt}
    for ref in _point_live_refs(pt):
        if not _ref_head_in_live(ref, live_out_fields):
            continue
        v = _ops.resolve(gctx, ref)
        if v is None or (isinstance(v, (list, tuple, str)) and len(v) == 0):
            return True
    return False


def skip_on_null(task, pt=None):
    if isinstance(pt, dict) and pt.get("skip_on_null") is not None:
        return bool(pt["skip_on_null"])
    if isinstance(task, dict) and task.get("skip_on_null") is not None:
        return bool(task["skip_on_null"])
    return str((task or {}).get("grounding") or "").strip().lower() == "live"


def live_outage_skip(task, pt, gt, live_out_fields, live_fetch_failed):
    if not (live_fetch_failed or ((skip_on_null(task, pt)))):
        return False
    return _point_needs_unavailable_live_gt(pt, gt, live_out_fields)


EVALUATOR_REFUSED = "evaluator_refused"
EVALUATOR_HELD = "EVALUATOR_HELD"


def _evaluator_row(pt, reason, diagnosis=""):
    row = {"id": pt["id"], "weight": pt.get("weight", 1.0), "gate": pt.get("gate", False),
           "pass_at": pt.get("pass_at", 0.999), "frac": None, "fail": reason,
           "error": None, "skipped": True, "skip_reason": EVALUATOR_REFUSED,
           "evaluator_refused": True, "verdict": EVALUATOR_REFUSED,
           "value": None, "target": None}
    if diagnosis:
        row["diagnosis"] = diagnosis
    return row


def variant_tasks(mode_task: dict):
    """Yield one flattened (task, reference answers) per difficulty variant of a task file."""
    if not mode_task.get("variants"):
        yield mode_task, None
        return
    for v in mode_task["variants"]:
        t = {**mode_task, "id": f"{mode_task['id']}__{v['level']}", "prompt": v.get("prompt", "")}
        t.pop("variants", None)
        t["_variant_level"] = v.get("level")
        t["_variant_gt"] = dict(v.get("gt") or {})
        yield t, v.get("gt")


def score_task(task: dict, image_path: str, reference_override: dict = None) -> dict:
    seed = dict(reference_override or {})
    gtctx = {"image": image_path, "task": task, "gt": seed, **seed}
    gt_flow = task.get("gt", {}).get("flow") or []
    live_out_fields = {s["out"] for s in gt_flow if isinstance(s, dict) and "out" in s}
    if gt_flow:
        try:
            _run_flow(gtctx, gt_flow)
        except Exception as e:
            log.debug("error ignored in score_task", exc_info=True)
            gtctx["_gt_error"] = f"{type(e).__name__}:{e}"
    live_fetch_failed = bool(gtctx.get("_fetch_failed"))
    gt = {k: v for k, v in gtctx.items() if k not in ("image", "task", "gt")}
    gt.update(seed)

    rows = []
    for pt in task["scoring"]:
        ctx = {"image": image_path, "task": task, "gt": gt, "_point": pt.get("id")}
        cond = pt.get("only_when")
        if cond is not None and not _ops.resolve(ctx, cond):
            rows.append({"id": pt["id"], "weight": pt.get("weight", 1.0), "gate": pt.get("gate", False),
                         "pass_at": pt.get("pass_at", 0.999), "frac": None, "fail": None,
                         "error": None, "skipped": True, "value": None, "target": None})
            continue
        if live_outage_skip(task, pt, gt, live_out_fields, live_fetch_failed):
            rows.append({"id": pt["id"], "weight": pt.get("weight", 1.0), "gate": pt.get("gate", False),
                         "pass_at": pt.get("pass_at", 0.999), "frac": None, "fail": None,
                         "error": None, "skipped": True, "skip_reason": "live_gt_unavailable",
                         "value": None, "target": None})
            continue
        err = None
        try:
            fail, seen = _run_flow(ctx, pt["flow"])
            if (isinstance(fail, _ops.Fail) and getattr(fail, "evaluator", False) and not _is_diagnostic_leaf(pt["id"], pt)):
                rows.append(_evaluator_row(pt, fail.reason,
                                            getattr(fail, "diagnosis", "")))
                continue
            if isinstance(fail, _ops.Fail):
                frac, reason = 0.0, fail.reason
            else:
                sc = _ops.resolve(ctx, pt["score"])
                frac, reason = (float(sc) if sc is not None else 0.0), None
        except NotImplementedError as e:
            log.debug("error ignored in score_task", exc_info=True)
            if not _is_diagnostic_leaf(pt["id"], pt):
                rows.append(_evaluator_row(
                    pt, f"unwired:{e}",
                    "this check's flow reached an op that is declared but NOT WIRED in this "
                    "interpreter. Nothing was measured about the picture, so nothing is charged "
                    "to the model, so the task is withheld."))
                continue
            frac, reason, seen, err = 0.0, f"unwired:{e}", {}, "unwired"
        except Exception as e:
            log.debug("error ignored in score_task", exc_info=True)
            if not _is_diagnostic_leaf(pt["id"], pt):
                rows.append(_evaluator_row(
                    pt, f"op_error:{type(e).__name__}:{e}",
                    "the scoring flow itself raised (missing import / op key absent from the registry / the op's own code failed). This is an EVALUATOR fault, never a model failure. It used to be folded to frac=0.0, which produced three-reads-agree, zero-impound, zero-error false zeros that the k=3 fold layer cannot see."))
                continue
            frac, reason, seen, err = 0.0, f"op_error:{type(e).__name__}:{e}", {}, "error"

        is_diag = _is_diagnostic_leaf(pt["id"], pt)
        if pt.get("premise_gate") and pt.get("gate") and not is_diag:
            frac = 1.0 if frac >= 0.5 else 0.0
        row = {"id": pt["id"], "weight": pt.get("weight", 1.0), "gate": pt.get("gate", False),
               "pass_at": pt.get("pass_at", 0.999), "frac": round(frac, 4), "fail": reason,
               "error": err,
               "value": _fmt(seen.get("value")), "target": _fmt(seen.get("target"))}
        if is_diag:
            row["skipped"] = True
            row["skip_reason"] = "diagnostic_evidence_only"
            row["diagnostic"] = True
        rows.append(row)

    conflicts = []

    active = [r for r in rows if not r.get("skipped")]
    gates = [r for r in active if r["gate"]]
    content = [r for r in active if not r["gate"]]
    gate_prod = 1.0
    for r in gates:
        gate_prod *= r["frac"]
    wsum = sum(r["weight"] for r in content)
    graded = 100.0 * (sum(r["weight"] * r["frac"] for r in content) / wsum) * gate_prod if wsum else None
    all_gates_pass = all(r["frac"] >= 0.999 for r in gates)
    all_content_pass = all(r["frac"] >= r["pass_at"] for r in content)
    strict = 100.0 if (content and all_gates_pass and all_content_pass) else 0.0

    errors = [r["id"] for r in rows if r.get("error")]
    out = {"id": task.get("id"), "graded": None if graded is None else round(graded, 1),
           "strict": strict, "gate_prod": round(gate_prod, 3),
           "errors": errors, "complete": not errors, "rows": rows}
    held = [r["id"] for r in rows if r.get("evaluator_refused")]
    if held:
        out["graded"], out["strict"] = None, None
        out["status"], out["evaluator_held"], out["escalate"] = EVALUATOR_HELD, held, True
    if conflicts:
        out["graded"], out["strict"] = None, None
        out["conflicts"], out["escalate"] = conflicts, True
    return out


def _fmt(v):
    if v is None: return None
    if isinstance(v, set):
        try:
            return str(sorted(v))[:40]
        except TypeError:
            log.debug("error ignored in _fmt", exc_info=True)
            return str(list(v))[:40]
    if isinstance(v, list):
        return str(list(v))[:40]
    if isinstance(v, float): return f"{v:.3f}"
    return str(v)[:40]


