"""Rebuild and print the report of a finished run.

    python summarize.py results/<model>
    python summarize.py results/<model> --tex row.tex --label "My model"
"""
import argparse
import io
import os
import sys

from genolympiad import paths, report

# The column order of the paper's results table.
AXES = ("text", "cfact", "symbol", "world", "phys", "quant", "spatial", "latent", "long")


def fmt(value) -> str:
    """A score with one decimal, or a dash when there is none."""
    return "-" if value is None else "%.1f" % value


def table_lines(summary: dict) -> list[str]:
    """The per-axis and overall scores and the task counts as plain text lines."""
    names = summary["axis_names"]
    missing = [short for short in AXES if short not in names]
    if missing:
        sys.exit("The report has no %s axis." % ", ".join(missing))
    row = "%-40s %6s %7s %7s %8s"
    lines = [row % ("capability axis", "tasks", "scored", "strict", "relaxed")]
    for short in AXES:
        lines.append(row % (names[short], summary[short + "_n"], summary[short + "_n_scored"],
                            fmt(summary[short + "_strict"]), fmt(summary[short + "_relaxed"])))
    lines.append(row % ("overall", summary["n"], summary["n_scored"], fmt(summary["strict"]),
                        fmt(summary["relaxed"])))
    lines += ["",
              "tasks in run      %d" % summary["n"],
              "scored            %d" % summary["n_scored"],
              "withheld          %d" % summary["n_withheld"],
              "not generated     %d" % summary["n_not_generated"],
              "withheld rate     %s%% of judged tasks" % fmt(summary["withheld_rate"])]
    return lines


def tex_row(summary: dict, label: str) -> str:
    """One LaTeX table row: strict and relaxed per axis in the paper's order, then overall."""
    values = []
    for short in AXES:
        values += [fmt(summary[short + "_strict"]), fmt(summary[short + "_relaxed"])]
    values += [fmt(summary["strict"]), fmt(summary["relaxed"])]
    return "%s & %s \\\\" % (label, " & ".join(values))


def main() -> None:
    """Parse the command line, rebuild the report and print it."""
    ap = argparse.ArgumentParser(
        prog="summarize.py",
        description="Rebuild results.json and results.md of a finished run and print the "
                    "strict and relaxed scores per capability axis.")
    ap.add_argument("run_dir", help="the run folder, for example results/gpt-image-1.5")
    ap.add_argument("--data-dir", metavar="DIR", default=paths.DATA_DIR,
                    help="the task data folder (default: data in this repository)")
    ap.add_argument("--tex", metavar="FILE", help="also write one LaTeX table row to FILE")
    ap.add_argument("--label",
                    help="the model name in the LaTeX row (default: the run folder name)")
    args = ap.parse_args()

    if not os.path.isdir(args.run_dir):
        sys.exit("There is no run folder at %s." % args.run_dir)
    summary = report.summarize_run(args.run_dir, data_dir=args.data_dir)
    name = summary.get("run") or os.path.basename(os.path.normpath(args.run_dir))
    print("run %s" % name)
    print("")
    for line in table_lines(summary):
        print(line)
    print("")
    for filename in ("results.json", "results.md"):
        path = os.path.join(args.run_dir, filename)
        if not os.path.isfile(path):
            sys.exit("The report was not written: %s is missing." % path)
        print("wrote %s" % path)
    if args.tex:
        with io.open(args.tex, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(tex_row(summary, args.label or name) + "\n")
        print("wrote %s" % args.tex)


if __name__ == "__main__":
    main()
