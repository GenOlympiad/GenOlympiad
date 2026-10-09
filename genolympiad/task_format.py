"""Read a task folder (task.json and program.py) into the evaluation plan input."""
from __future__ import annotations

import io
import json
import os
import re

STEP_VERBS = {
    "guard.fail": ("fail_if", "when"),
    "run.code": ("run", None),
    "compare.equals": ("compare", "value"),
    "compare.band": ("compare_band", "value"),
    "compare.tol": ("compare_tolerance", "value"),
    "compare.set": ("compare_set", "value"),
    "compare.grid": ("compare_grid", "value"),
    "compare.token_in": ("compare_token", "value"),
    "compare.compass": ("compare_compass", "value"),
    "compare.seq_band": ("compare_sequence", "value"),
    "compare.band_multi": ("compare_bands", "value"),
    "compare.text_f1": ("compare_text", "value"),
    "compare.phase_neighbor": ("compare_phase", "value"),
    "category.adjacent": ("compare_category", "value"),
    "trend.match": ("match_trend", "value"),
    "order.match": ("match_order", "value"),
    "compare.min": ("minimum", "values"),
    "combine.and": ("all", "values"),
    "combine.or": ("any", "values"),
    "combine.product": ("product", "values"),
    "vlm.ask": ("ask", "question"),
    "vlm.crop_read": ("read_crop", "question"),
    "vlm.grounded_read": ("read", "primitive"),
    "vlm.read_number": ("read_number", "question"),
    "vlm.read_seq": ("read_sequence", "question"),
    "vlm.read_grid": ("read_grid", "describe"),
    "vlm.noans_check": ("check_no_answer", None),
    "vlm.compose_ray_target": ("compose_ray", "ray"),
    "fallback.read": ("read_fallback", "primary"),
    "read.count_yes": ("count_yes", "value"),
    "ocr.read": ("read_text", None),
    "overlay.compare": ("overlay", "mode"),
    "regex.extract": ("extract", "pattern"),
    "crop.bbox": ("crop", "bbox"),
    "crop.full": ("crop_full", None),
    "json.get": ("get", "path"),
    "const": ("const", "value"),
    "fetch.url": ("fetch", "url"),
    "len": ("length", "value"),
    "time.to_minutes": ("to_minutes", "value"),
    "compute.mirror_closure": ("mirror_closure", "points"),
    "board.foreach": ("for_each_row", "board"),
    "geom.grid_cells": ("grid_cells", "value"),
    "aqi.consistency": ("check_air_quality", "value"),
    "calib.apply": ("calibrate", "curve"),
}
VERB_OPS = {v[0]: op for op, v in STEP_VERBS.items()}
COMPARE_TARGET = {"compare.equals", "compare.band", "compare.tol", "compare.set", "compare.grid",
                  "compare.token_in", "compare.compass", "compare.seq_band", "compare.band_multi",
                  "compare.text_f1", "compare.phase_neighbor", "category.adjacent", "trend.match",
                  "order.match"}
STEP_DEFAULTS = {
    "image": "image",
    "retries": 3,
    "votes": 3,
}
DEFAULT_STEP_KEYS = {
    "vlm.ask": ("image", "retries"), "vlm.crop_read": ("image", "votes"),
    "vlm.grounded_read": ("image", "retries"), "vlm.read_number": ("image", "retries"),
    "vlm.read_seq": ("image", "retries"), "vlm.read_grid": ("image",),
    "vlm.noans_check": ("image", "retries"), "vlm.compose_ray_target": ("image",),
    "ocr.read": ("image",), "crop.bbox": ("image",), "crop.full": ("image",),
    "overlay.compare": ("image",),
}
NESTED_STEPS = ("else", "each")
CHECK_KEYS = {"premise_gate": "premise", "d2": "not_scored", "only_when": "only_if"}
EASY_CHECK = "scene_compliance"
NO_TEXT_CHECK = "no_answer_text"
_TASK_KEYS = ("id", "axis", "prompt", "difficulty", "easy_question", "reference", "checks",
              "reference_steps", "reference_extra", "aspect_ratio")
_WORD_REFERENCE = re.compile(r"\breference\b")
_BLOCK_RE = re.compile(r"^# (shared code|code): (\S+)\n(.*?)\n# end of \2\n", re.S | re.M)


def to_ref(v):
    """reference.x -> gt.x inside any value of a step."""
    if isinstance(v, str):
        return "gt." + v[len("reference."):] if v.startswith("reference.") else v
    if isinstance(v, list):
        return [to_ref(x) for x in v]
    if isinstance(v, dict):
        return {k: to_ref(x) for k, x in v.items()}
    return v


def read_program(path):
    """{block name: (code, shared)} in file order, from program.py."""
    if not os.path.exists(path):
        return {}
    with io.open(path, encoding="utf-8", newline="") as fh:
        text = fh.read()
    return {m.group(2): (m.group(3), m.group(1) == "shared code") for m in _BLOCK_RE.finditer(text)}


def _defines(code):
    names = set(re.findall(r"^def (\w+)\(", code, re.M))
    head = "from genolympiad.task_helpers import"
    if code.startswith(head):
        names.update(re.findall(r"\w+", code[len(head):]))
    return names


def _code_of(step, blocks):
    name = step.get("code")
    if isinstance(name, dict):
        return blocks[name["inline"]][0]
    if isinstance(name, str):
        return "gt." + name
    fn = step["run"]
    hits = [b for b, (code, _shared) in blocks.items() if fn in _defines(code)]
    b = hits[0]
    code, shared = blocks[b]
    return "gt." + b if shared else code


def step_to_internal(step, blocks):
    """One task.json step -> the operator step the engine runs."""
    verb = next(k for k in step if k in VERB_OPS)
    op = VERB_OPS[verb]
    rest = {k: v for k, v in step.items() if k != verb}
    out = {"op": op}
    if op == "run.code":
        out["code"] = _code_of(step, blocks)
        if "expression" in rest:
            out["call"] = _WORD_REFERENCE.sub("gt", rest.pop("expression"))
        elif "args" in rest:
            out["call"] = "%s(%s)" % (step["run"], _WORD_REFERENCE.sub("gt", ", ".join(rest.pop("args"))))
        else:
            out["call"] = step["run"]
        rest.pop("code", None)
    elif op == "const" and isinstance(step[verb], dict) and "program" in step[verb]:
        out["value"] = blocks[step[verb]["program"]][0]
    else:
        main = STEP_VERBS[op][1]
        if main is not None:
            out[main] = to_ref(step[verb])
    if op in COMPARE_TARGET and "to" in rest:
        rest["target"] = rest.pop("to")
    for k in DEFAULT_STEP_KEYS.get(op, ()):
        if k not in rest:
            rest[k] = STEP_DEFAULTS[k]
        elif rest[k] is None:
            rest.pop(k)
    for k, v in rest.items():
        if k in NESTED_STEPS and isinstance(v, list):
            out[k] = [step_to_internal(s, blocks) for s in v]
        else:
            out[k] = to_ref(v)
    return out


def check_to_internal(check, blocks):
    """One task.json check -> the scoring point the engine runs."""
    pt = {"id": check["name"]}
    if "weight" in check:
        pt["weight"] = check["weight"]
    for k, v in check.items():
        if k in ("name", "weight", "steps"):
            continue
        pt[{v2: k2 for k2, v2 in CHECK_KEYS.items()}.get(k, k)] = to_ref(v)
    if "pass_at" not in check:
        pt["pass_at"] = 0.999
    if "score" not in pt:
        pt["score"] = "frac"
    if check["name"] == EASY_CHECK and "only_if" not in check:
        pt["only_when"] = "gt.enforce_scene"
    if check["name"] == NO_TEXT_CHECK and "only_if" not in check:
        pt["only_when"] = "gt.enforce_notext"
    pt["flow"] = [step_to_internal(s, blocks) for s in check["steps"]]
    return pt


def load_task_folder(folder):
    """The task in the engine's input form: one variant, its reference answers and its checks."""
    with io.open(os.path.join(folder, "task.json"), encoding="utf-8") as fh:
        t = json.load(fh)
    blocks = read_program(os.path.join(folder, "program.py"))
    gt = {"enforce_scene": True, "easy_question": t["easy_question"]}
    for k, v in t.get("reference", {}).items():
        gt[k] = blocks[v["program"]][0] if isinstance(v, dict) and set(v) == {"program"} else v
    task = {"id": t["id"], "axis": t["axis"]}
    for k, v in t.items():
        if k not in _TASK_KEYS:
            task[k] = to_ref(v)
    if "aspect_ratio" in t:
        task["gen_params"] = {"aspect_ratio": t["aspect_ratio"]}
    task["variants"] = [{"level": t["difficulty"], "prompt": t["prompt"], "gt": gt}]
    top = {}
    if "reference_steps" in t:
        top["flow"] = [step_to_internal(s, blocks) for s in t["reference_steps"]]
    else:
        shared = [{"op": "const", "value": code, "out": name}
                  for name, (code, is_shared) in blocks.items() if is_shared]
        if shared:
            top["flow"] = shared
    for k, v in (t.get("reference_extra") or {}).items():
        top[k] = [step_to_internal(s, blocks) for s in v] if k.endswith("flow") else v
    if top:
        task["gt"] = top
    task["scoring"] = [check_to_internal(c, blocks) for c in t["checks"]]
    return task
