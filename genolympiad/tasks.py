"""The 801 tasks: the task list, the hash check, and prompt and variant lookup."""
from __future__ import annotations

import hashlib
import io
import json
import os
import re

from . import paths


def _load_json(path):
    with io.open(path, encoding="utf-8") as fh:
        return json.load(fh)


def load_index(data_dir=paths.DATA_DIR):
    """The task list from data/tasks.json, in file order."""
    return list(_load_json(os.path.join(data_dir, "tasks.json"))["tasks"])


def _sha256(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def _abs(entry, data_dir):
    return os.path.join(os.path.dirname(os.path.abspath(data_dir)), entry["path"])


def verify(data_dir=paths.DATA_DIR):
    """(ok, problems, tree_sha256): every task file matches its sha256 and the tree hash."""
    index = _load_json(os.path.join(data_dir, "tasks.json"))
    problems = []
    lines = []
    for e in index["tasks"]:
        for name, digest in sorted(e["sha256"].items()):
            p = os.path.join(_abs(e, data_dir), name)
            lines.append("%s/%s %s\n" % (e["path"], name, digest))
            if not os.path.exists(p):
                problems.append("missing: %s/%s" % (e["path"], name))
            elif _sha256(p) != digest:
                problems.append("changed: %s/%s" % (e["path"], name))
    tree = hashlib.sha256("".join(lines).encode("utf-8")).hexdigest()
    if tree != index.get("tree_sha256"):
        problems.append("tree hash differs from data/tasks.json")
    if len(index["tasks"]) != index.get("n"):
        problems.append("task count differs from data/tasks.json")
    return not problems, problems, tree


def select(entries, limit=None, task_ids=None):
    """The entries named by task_ids (in task-list order), cut to the first `limit`."""
    out = list(entries)
    if task_ids:
        want = task_ids if not isinstance(task_ids, str) else re.split(r"[,\s]+", task_ids)
        want = {w for w in want if w}
        known = {e["task_id"] for e in out}
        unknown = sorted(want - known)
        if unknown:
            raise KeyError("unknown task id(s): %s" % ", ".join(unknown))
        out = [e for e in out if e["task_id"] in want]
    return out[:limit] if limit else out


def load_task(entry, data_dir=paths.DATA_DIR):
    """The task.json of one entry."""
    return _load_json(os.path.join(_abs(entry, data_dir), "task.json"))


def prompt_of(entry, data_dir=paths.DATA_DIR):
    """The exact prompt of the task."""
    return load_task(entry, data_dir)["prompt"]


def aspect_ratio_of(entry, data_dir=paths.DATA_DIR):
    """The aspect ratio the task asks for, or None."""
    return load_task(entry, data_dir).get("aspect_ratio")


def axis_names(data_dir=paths.DATA_DIR):
    """{short key: long name} for the nine capability axes, in data/axes.json order."""
    axes = _load_json(os.path.join(data_dir, "axes.json"))
    return {short_key(a["short"]): a["name"] for a in axes.values()}


def axis_short(data_dir=paths.DATA_DIR):
    """{axis key: short key}, for example counterfactual_instruction_following -> cfact."""
    axes = _load_json(os.path.join(data_dir, "axes.json"))
    return {k: short_key(a["short"]) for k, a in axes.items()}


def short_key(short):
    """Report key for an axis short name: lower case, no hyphen or period."""
    return re.sub(r"[^a-z0-9]", "", short.lower())


def evaluation_task(entry, data_dir=paths.DATA_DIR):
    """(task, reference answers) for the judge, read from the task folder."""
    from . import engine, task_format
    task = task_format.load_task_folder(_abs(entry, data_dir))
    return next(engine.variant_tasks(task))
