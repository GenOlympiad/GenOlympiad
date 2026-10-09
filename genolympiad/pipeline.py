"""Evaluate every task of a run and merge the per-task outcomes."""
from __future__ import annotations

import io
import json
import os
import re
import subprocess
import sys
import time

from . import images, paths

_BATCH = 45
_BATCH_TIMEOUT_MIN = 180
_MAX_REPEATS = 4
_STOP_BELOW_PCT = 5.0
_KEY_ENV = {"gemini": "GEMINI_API_KEY", "openrouter": "OPENROUTER_API_KEY"}


def _dump(path, doc):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with io.open(path + ".tmp", "w", encoding="utf-8", newline="\n") as fh:
        json.dump(doc, fh, ensure_ascii=False, indent=1, sort_keys=True)
        fh.write("\n")
    os.replace(path + ".tmp", path)


def _load(path):
    with io.open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _scores_in(folder):
    out = {}
    if os.path.isdir(folder):
        for fn in sorted(os.listdir(folder)):
            if fn.endswith(".json"):
                out[fn[:-5]] = _load(os.path.join(folder, fn))
    return out


def _run_batches(entries, run_dir, out_dir, *, judge, judge_model, cache_dir, key, workers,
                 fresh, log, on_batch=None):
    """Evaluate the entries in child processes, one batch at a time; returns paid VLM calls."""
    work = os.path.join(run_dir, ".work")
    paid = 0
    pending = [e for e in entries if not os.path.exists(os.path.join(out_dir, e["task_id"] + ".json"))]
    for i in range(0, len(pending), _BATCH):
        batch = pending[i:i + _BATCH]
        job = os.path.join(work, "job.json")
        done_file = os.path.join(work, "job_done.json")
        if os.path.exists(done_file):
            os.remove(done_file)
        _dump(job, {"entries": batch, "images_dir": os.path.join(run_dir, "images"),
                    "out_dir": out_dir, "judge": judge, "judge_model": judge_model,
                    "cache_dir": os.path.abspath(cache_dir), "workers": workers,
                    "fresh": fresh, "done_file": done_file, "scratch": os.path.join(work, "tmp")})
        env = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
        if key and judge in _KEY_ENV:
            env[_KEY_ENV[judge]] = key
        with io.open(os.path.join(work, "batch.log"), "ab") as fh:
            child = subprocess.Popen([sys.executable, "-X", "utf8", "-m", "genolympiad.batch_worker", job],
                                     cwd=paths.REPO_ROOT, env=env, stdout=fh, stderr=subprocess.STDOUT)
            try:
                rc = child.wait(timeout=_BATCH_TIMEOUT_MIN * 60)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait()
                rc = None
        if rc != 0:
            log("  a batch of %d task(s) stopped early (%s); see %s"
                % (len(batch), "time limit" if rc is None else "exit code %d" % rc,
                   os.path.normpath(os.path.join(work, "batch.log"))))
        if os.path.exists(done_file):
            done = _load(done_file)
            paid += int(done.get("paid_vlm_reads", 0))
            if done.get("key_rejected"):
                for e in batch:
                    stale = os.path.join(out_dir, e["task_id"] + ".json")
                    if os.path.exists(stale):
                        os.remove(stale)
                from .judge_vlm import KeyRejected
                raise KeyRejected(done["key_rejected"])
        if on_batch is not None:
            on_batch(batch, _scores_in(out_dir))
    return paid


def _missing_score(entry):
    return {"task_id": entry["task_id"], "axis": entry["axis"], "relaxed": None, "strict": None,
            "status": "withheld", "withheld_reason": "evaluator_failure", "questions": [],
            "vlm_reads": 0}


def _judge_and_recheck(ready, run_dir, work, first_dir, run_name, bar, *, judge,
                       judge_model, cache_dir, key, workers, log):
    """Judge every task, then judge the withheld ones again; returns (scores, withheld, paid)."""
    ids = {e["task_id"] for e in ready}

    def first(batch, got):
        bar.update(len(batch))
        bar.set_postfix(withheld=sum(1 for tid, sc in got.items()
                                     if tid in ids and sc["status"] != "scored"))
    paid = _run_batches(ready, run_dir, first_dir, judge=judge, judge_model=judge_model,
                        cache_dir=cache_dir, key=key, workers=workers, fresh="", log=log,
                        on_batch=first)
    best = _scores_in(first_dir)
    for e in ready:
        if e["task_id"] not in best:
            best[e["task_id"]] = _missing_score(e)
    left = [e for e in ready if best[e["task_id"]]["status"] != "scored"]
    for k in range(1, _MAX_REPEATS + 1):
        if not left:
            break
        folder = os.path.join(work, "s%d" % k)
        waiting = list(left)

        def again(batch, got, waiting=waiting):
            bar.set_postfix(withheld=sum(1 for e in waiting
                                         if (got.get(e["task_id"]) or {}).get("status") != "scored"))
        paid += _run_batches(left, run_dir, folder, judge=judge, judge_model=judge_model,
                             cache_dir=cache_dir, key=key, workers=workers,
                             fresh="repeat_%s_%d" % (run_name, k), log=log, on_batch=again)
        got = _scores_in(folder)
        still = []
        for e in left:
            s = got.get(e["task_id"])
            if s is not None and s["status"] == "scored":
                best[e["task_id"]] = s
            else:
                if s is not None:
                    best[e["task_id"]] = s
                still.append(e)
        released = len(left) - len(still)
        stop = released < _STOP_BELOW_PCT / 100.0 * max(1, len(left))
        left = still
        if stop:
            break
    return best, left, paid


def judge_all(entries, run_dir, *, judge, judge_model=None, cache_dir, key=None, workers=16,
              log=print):
    """Evaluate every task that has an image; writes scores/ and judging.json."""
    ledger = images.load_ledger(run_dir)
    ready = [e for e in entries
             if (ledger["tasks"].get(e["task_id"]) or {}).get("status") in ("made", "imported")
             and os.path.exists(os.path.join(run_dir, "images", e["task_id"] + ".png"))]
    work = os.path.join(run_dir, ".work")
    run_name = re.sub(r"[^a-z0-9]", "", os.path.basename(os.path.abspath(run_dir)).lower())[-12:]
    first_dir = os.path.join(work, "s0")
    from tqdm import tqdm
    ids = {e["task_id"] for e in ready}
    bar = tqdm(total=len(ready), initial=len(set(_scores_in(first_dir)) & ids), desc="judging",
               unit="task", dynamic_ncols=True)
    try:
        best, left, paid = _judge_and_recheck(ready, run_dir, work, first_dir, run_name, bar,
                                              judge=judge, judge_model=judge_model,
                                              cache_dir=cache_dir, key=key, workers=workers,
                                              log=log)
    finally:
        bar.close()
    log("  %d task(s) evaluated, %d withheld" % (len(ready), len(left)))
    scores_dir = os.path.join(run_dir, "scores")
    for tid, s in best.items():
        _dump(os.path.join(scores_dir, tid + ".json"), s)
    _dump(os.path.join(run_dir, "judging.json"),
          {"tasks": {tid: {"status": s["status"], "vlm_reads": s.get("vlm_reads", 0)}
                     for tid, s in sorted(best.items())}})
    return {"scores": best, "paid_vlm_reads": paid}


def merge(entries, run_dir):
    """{task_id: {strict, relaxed, status, reason}} from scores/ and generation.json."""
    ledger = images.load_ledger(run_dir)
    scores = _scores_in(os.path.join(run_dir, "scores"))
    out = {}
    for e in entries:
        tid = e["task_id"]
        gen = ledger["tasks"].get(tid) or {"status": "not_generated", "reason": "no_image_supplied"}
        if gen.get("status") == "not_generated":
            out[tid] = {"strict": None, "relaxed": None, "status": "not_generated",
                        "reason": gen.get("reason")}
        elif tid in scores:
            s = scores[tid]
            out[tid] = {"strict": s.get("strict"), "relaxed": s.get("relaxed"),
                        "status": s["status"], "reason": s.get("withheld_reason")}
        else:
            out[tid] = {"strict": None, "relaxed": None, "status": "withheld",
                        "reason": "evaluator_failure"}
    return out
