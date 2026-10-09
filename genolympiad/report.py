"""Aggregate per-task scores the way the paper does, and write the report."""
from __future__ import annotations

import io
import json
import os

from . import images, paths, tasks


def _r1(x):
    return None if x is None else round(float(x) + 0.0, 1)


def _block(rows):
    scored = [r for r in rows if r["status"] == "scored"]
    n = len(rows)
    out = {"n": n, "n_scored": len(scored),
           "relaxed": _r1(sum(r["relaxed"] for r in scored) / len(scored)) if scored else None,
           "strict": _r1(100.0 * sum(1 for r in scored if r["strict"] >= 100) / len(scored))
           if scored else None}
    return out


def aggregate(entries, merged, *, axis_names=None, data_dir=paths.DATA_DIR):
    """Overall and per-axis strict and relaxed scores with the paper's denominators."""
    short = tasks.axis_short(data_dir)
    names = axis_names or tasks.axis_names(data_dir)
    rows = [dict(merged[e["task_id"]], axis=e["axis"]) for e in entries]
    total = _block(rows)
    n_withheld = sum(1 for r in rows if r["status"] == "withheld")
    n_not = sum(1 for r in rows if r["status"] == "not_generated")
    out = {"n": total["n"], "n_scored": total["n_scored"], "n_withheld": n_withheld,
           "n_not_generated": n_not,
           "withheld_rate": _r1(100.0 * n_withheld / (total["n_scored"] + n_withheld))
           if (total["n_scored"] + n_withheld) else None,
           "strict": total["strict"], "relaxed": total["relaxed"], "axis_names": names}
    for axis, key in short.items():
        b = _block([r for r in rows if r["axis"] == axis])
        out["%s_n" % key] = b["n"]
        out["%s_n_scored" % key] = b["n_scored"]
        out["%s_strict" % key] = b["strict"]
        out["%s_relaxed" % key] = b["relaxed"]
    out["not_generated_ids"] = sorted(e["task_id"] for e in entries
                                      if merged[e["task_id"]]["status"] == "not_generated")
    out["tasks"] = {e["task_id"]: merged[e["task_id"]] for e in entries}
    return out


def _fmt(x):
    return "n/a" if x is None else "%.1f" % x


def write(run_dir, summary, *, generation, spend):
    """Write results.json and results.md; returns their paths."""
    doc = dict(summary)
    doc.setdefault("run", os.path.basename(os.path.normpath(run_dir)))
    counts = {}
    for t in (generation or {}).get("tasks", {}).values():
        counts[t["status"]] = counts.get(t["status"], 0) + 1
    doc["generation"] = {k: counts.get(k, 0) for k in ("made", "imported", "not_generated")}
    doc["spend"] = spend
    pj = os.path.join(run_dir, "results.json")
    with io.open(pj, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(doc, fh, ensure_ascii=False, indent=1, sort_keys=True)
        fh.write("\n")
    names = doc["axis_names"]
    lines = ["# %s" % (doc.get("run") or os.path.basename(os.path.abspath(run_dir))), "",
             "| | strict | relaxed | scored tasks |", "|---|--:|--:|--:|",
             "| Overall | %s | %s | %d |" % (_fmt(doc["strict"]), _fmt(doc["relaxed"]),
                                             doc["n_scored"])]
    for key, name in names.items():
        lines.append("| %s | %s | %s | %d |" % (name, _fmt(doc["%s_strict" % key]),
                                                _fmt(doc["%s_relaxed" % key]),
                                                doc["%s_n_scored" % key]))
    lines += ["", "| tasks | scored | withheld | not generated | Withheld (%) |",
              "|--:|--:|--:|--:|--:|",
              "| %d | %d | %d | %d | %s |" % (doc["n"], doc["n_scored"], doc["n_withheld"],
                                              doc["n_not_generated"], _fmt(doc["withheld_rate"])),
              "",
              "Overall is the mean over all scored tasks. Withheld tasks are excluded from the "
              "scores. The withheld rate is the share of judged tasks that were withheld. Tasks "
              "that were not generated are counted separately.",
              "",
              "Images made in this run: %d. Judge VLM reads behind the scores: %d. Paid judge "
              "VLM reads in this run: %d (a read answered from the cache is not paid).%s" % (
                  spend.get("images_made", 0), spend.get("vlm_reads", 0),
                  spend.get("paid_vlm_reads", 0),
                  " Estimated cost: $%.2f." % spend["usd"] if spend.get("usd") else ""), ""]
    if doc["not_generated_ids"]:
        lines += ["Not generated: %s" % ", ".join(doc["not_generated_ids"]), ""]
    pm = os.path.join(run_dir, "results.md")
    with io.open(pm, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines))
    return pj, pm


def summarize_run(run_dir, data_dir=paths.DATA_DIR, entries=None):
    """Rebuild the summary of a finished run from its files and rewrite results.json and .md."""
    if entries is None:
        ledger = images.load_ledger(run_dir)
        known = set(ledger.get("tasks", {}))
        entries = [e for e in tasks.load_index(data_dir) if e["task_id"] in known]
    from . import pipeline
    merged = pipeline.merge(entries, run_dir)
    summary = aggregate(entries, merged, data_dir=data_dir)
    old = {}
    pj = os.path.join(run_dir, "results.json")
    if os.path.exists(pj):
        with io.open(pj, encoding="utf-8") as fh:
            old = json.load(fh)
    for k in ("run", "model", "judge_model"):
        if k in old:
            summary[k] = old[k]
    write(run_dir, summary, generation=images.load_ledger(run_dir),
          spend=old.get("spend") or {"images_made": 0, "paid_vlm_reads": 0, "vlm_reads": 0,
                                     "usd": 0.0, "minutes": 0.0})
    return summary


def print_block(summary, run_dir, log=print):
    """Print the overall and per-axis scores and the task counts."""
    log("")
    log("%-38s %8s %8s" % ("", "strict", "relaxed"))
    log("%-38s %8s %8s" % ("Overall", _fmt(summary["strict"]), _fmt(summary["relaxed"])))
    for key, name in summary["axis_names"].items():
        log("%-38s %8s %8s" % (name, _fmt(summary["%s_strict" % key]),
                               _fmt(summary["%s_relaxed" % key])))
    log("")
    log("tasks %d, scored %d, withheld %d, not generated %d, Withheld (%%) %s"
        % (summary["n"], summary["n_scored"], summary["n_withheld"],
           summary["n_not_generated"], _fmt(summary["withheld_rate"])))
    log("report: %s" % os.path.normpath(os.path.join(run_dir, "results.md")))
