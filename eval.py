"""Run one text-to-image model on GenOlympiad and report its strict and relaxed scores.

    python eval.py --model gpt-image-1.5

One command makes one image per task, judges every image against its task's evaluation program,
and writes the report to results/<run name>/.
"""
import argparse
import io
import os
import re
import sys
import time

from genolympiad import images, judge_vlm, pipeline, report, tasks

IMAGE_KEY_VARS = {"openai": "OPENAI_API_KEY", "gemini": "GEMINI_API_KEY", "ark": "ARK_API_KEY",
                  "bfl": "BFL_API_KEY", "openrouter": "OPENROUTER_API_KEY",
                  "leonardo": "LEONARDO_API_KEY"}
JUDGE_KEY_VARS = {"gemini": "GEMINI_API_KEY", "openrouter": "OPENROUTER_API_KEY"}

EXAMPLES = """examples:
  python eval.py --model gpt-image-1.5
  python eval.py --model gpt-image-1.5 --limit 5
  python eval.py --export-prompts prompts.jsonl
  python eval.py --model my-model --images my_images/
  python eval.py --model my-model --backend-config backends/openai_compatible.json

API keys come from .env in this folder, from environment variables (OPENAI_API_KEY,
GEMINI_API_KEY, ARK_API_KEY, BFL_API_KEY, OPENROUTER_API_KEY, LEONARDO_API_KEY) or from files
given with --key-file and --judge-key-file.
"""


class RunLog:
    """Prints a line and appends it to the run's log file once the run folder is known."""

    def __init__(self):
        self.path = None

    def __call__(self, message: str) -> None:
        print(message, flush=True)
        if self.path:
            with io.open(self.path, "a", encoding="utf-8") as fh:
                fh.write(message + "\n")


def build_parser() -> argparse.ArgumentParser:
    """The command line of eval.py."""
    ap = argparse.ArgumentParser(
        prog="eval.py",
        description="Run one text-to-image model on GenOlympiad and report its strict and "
                    "relaxed scores.",
        epilog=EXAMPLES, formatter_class=argparse.RawDescriptionHelpFormatter)

    model = ap.add_argument_group("model")
    model.add_argument("--model", metavar="NAME",
                       help="the model id the image API knows, for example gpt-image-1.5 "
                            "(required unless --export-prompts)")
    model.add_argument("--backend", choices=images.backend_names(),
                       help="which image API to call (default: guessed from --model)")
    model.add_argument("--route", metavar="NAME",
                       help="the model name to send to the image API, if it differs from "
                            "--model; --model still names the run")
    model.add_argument("--key-file", metavar="FILE",
                       help="a file with the image API key (default: the environment variable "
                            "of the backend)")

    own = ap.add_argument_group("your own model")
    own.add_argument("--images", metavar="DIR",
                     help="judge your own generated images, named <task_id>.png, "
                          "instead of generating")
    own.add_argument("--export-prompts", metavar="FILE",
                     help="write every prompt as one JSON line, with its capability axis and "
                          "length, and stop")
    own.add_argument("--backend-config", metavar="FILE",
                     help="a JSON file that describes your own HTTP image API (see backends/)")

    length = ap.add_argument_group(
        "long prompts", "A prompt is never cut. A task whose prompt your model cannot take whole "
                        "is not generated. It gets no score, and the report counts it.")
    length.add_argument("--context-length", type=int, metavar="N",
                        help="the most prompt tokens your model's text encoder takes "
                             "(needs --tokenizer)")
    length.add_argument("--tokenizer", metavar="NAME",
                        help="the Hugging Face tokenizer that counts the tokens, "
                             "for example google/t5-v1_1-xxl")
    length.add_argument("--not-generated", metavar="FILE",
                        help="a text or JSON list of task ids your model cannot take whole")

    run = ap.add_argument_group("tasks and run folder")
    run.add_argument("--run-name", metavar="NAME",
                     help="the name of the run folder (default: the model id)")
    run.add_argument("--results-dir", metavar="DIR", default="results",
                     help="the parent of run folders (default: results)")
    run.add_argument("--limit", type=int, metavar="N", help="run only the first N tasks")
    run.add_argument("--tasks", metavar="IDS", help="run only these task ids, comma separated")

    judge = ap.add_argument_group("judge VLM")
    judge.add_argument("--judge", default="gemini", choices=judge_vlm.judge_names(),
                       help="the judge VLM that answers the evaluation questions "
                            "(default: gemini)")
    judge.add_argument("--judge-model", metavar="NAME",
                       help="the judge VLM's model id (default: Gemini 2.5 Flash for both "
                            "gemini and openrouter)")
    judge.add_argument("--judge-key-file", metavar="FILE",
                       help="a file with the judge VLM key (default: the environment variable "
                            "of the judge)")

    speed = ap.add_argument_group("speed and cost")
    speed.add_argument("--workers", metavar="N", type=int, default=16,
                       help="parallel requests to the judge VLM (default: 16)")
    speed.add_argument("--gen-workers", metavar="N", type=int, default=8,
                       help="parallel requests to the image API (default: 8)")
    speed.add_argument("--usd-per-vlm-read", metavar="USD", type=float, default=0.0,
                       help="price of one paid judge VLM read, for the cost line of the report")
    speed.add_argument("--usd-per-image", metavar="USD", type=float, default=0.0,
                       help="price of one image, for the cost line of the report")
    return ap


def default_run_name(model: str) -> str:
    """The model id made safe for a folder name."""
    return re.sub(r"[^A-Za-z0-9._-]+", "-", model).strip("-").lower()


def require_key(var: str, key_file: str | None, what: str, flag: str) -> str:
    """The key from the environment or the key file, or exit with a plain message."""
    if key_file and not os.path.isfile(key_file):
        sys.exit("There is no key file at %s." % key_file)
    key = images.read_key(var, key_file)
    if not key:
        sys.exit("No API key for %s. Set %s in .env or in your environment, or pass %s with "
                 "a file that holds the key." % (what, var, flag))
    return key


def select_tasks(args) -> list[dict]:
    """The tasks this run covers, after checking the task files."""
    ok, problems, _tree = tasks.verify()
    if not ok:
        for line in problems[:10]:
            print("  " + line)
        sys.exit("The task files do not match data/tasks.json. Restore them with "
                 "`git checkout data` and run again.")
    try:
        return tasks.select(tasks.load_index(), limit=args.limit, task_ids=args.tasks)
    except KeyError as err:
        sys.exit("Unknown task id: %s. The ids are in data/tasks.json." % err.args[0])


def make_limits(args) -> images.Limits:
    """The prompt length rules from the command line."""
    if args.context_length and not args.tokenizer:
        sys.exit("--context-length needs --tokenizer, so the prompt tokens can be counted.")
    listed = frozenset()
    if args.not_generated:
        if not os.path.isfile(args.not_generated):
            sys.exit("There is no file at %s." % args.not_generated)
        listed = frozenset(images.load_id_list(args.not_generated))
    return images.Limits(context_length=args.context_length, tokenizer=args.tokenizer,
                         not_generated_ids=listed)


def judge_key(args) -> str | None:
    """The judge VLM key, checked before anything is paid for; None when it needs none."""
    var = JUDGE_KEY_VARS.get(args.judge)
    if var is None:
        return None
    return require_key(var, args.judge_key_file, "the judge VLM (%s)" % args.judge,
                       "--judge-key-file")


def rejected_key(args, err) -> str:
    """The plain message for a judge VLM key the service refused."""
    where = args.judge_key_file or JUDGE_KEY_VARS.get(args.judge, "the judge key")
    return "The judge VLM rejected the key in %s: %s" % (where, err)


def check_judge(args, key) -> None:
    """Stop before any image is paid for when the judge VLM refuses its key."""
    try:
        judge_vlm.check_key(args.judge, model=args.judge_model, key=key)
    except judge_vlm.KeyRejected as err:
        sys.exit(rejected_key(args, err))


def image_source(args) -> dict:
    """Where the images come from: a folder, or a backend with its key and HTTP settings."""
    if args.images:
        if not os.path.isdir(args.images):
            sys.exit("There is no folder at %s." % args.images)
        return {"folder": args.images}
    http_config = images.load_http_config(args.backend_config)
    backend = args.backend or ("http" if http_config else images.backend_for(args.model))
    if backend is None:
        sys.exit("Cannot tell which image API serves %r. Name it with --backend, describe your "
                 "own API with --backend-config, or bring images with --images." % args.model)
    if backend == "http" and not http_config:
        sys.exit("The http backend needs --backend-config.")
    key = None
    if backend in IMAGE_KEY_VARS:
        key = require_key(IMAGE_KEY_VARS[backend], args.key_file,
                          "the image backend (%s)" % backend, "--key-file")
    return {"backend": backend, "key": key, "http_config": http_config}


def get_images(args, source, entries, run_dir, limits, log) -> dict:
    """Generate or import the images and return the generation ledger."""
    if "folder" in source:
        ledger = images.import_folder(source["folder"], entries, run_dir, limits=limits, log=log)
        unmatched = ledger.get("unmatched_files") or []
        if unmatched:
            log("%d file(s) in %s match no task id and were left out, for example %s"
                % (len(unmatched), source["folder"], ", ".join(unmatched[:5])))
        return ledger
    log("generating images with %s (%s)" % (source["backend"], args.route or args.model))
    return images.generate(entries, run_dir, backend=source["backend"],
                           model=args.route or args.model, limits=limits,
                           workers=args.gen_workers, key=source["key"],
                           http_config=source["http_config"])


def main() -> None:
    """Parse the command line and run the benchmark."""
    args = build_parser().parse_args()
    images.load_env()
    if not args.model and not args.export_prompts:
        sys.exit("--model is required. Use --export-prompts to write the prompts out first.")

    entries = select_tasks(args)
    if args.export_prompts:
        n = images.export_prompts(entries, args.export_prompts, tokenizer=args.tokenizer)
        print("wrote %d prompt(s) to %s" % (n, args.export_prompts))
        print("Make one image per line, name it <task_id>.png, put the images in one folder, "
              "and judge them with: python eval.py --model %s --images <folder>"
              % (args.model or "my-model"))
        return

    limits = make_limits(args)
    cache_dir = os.path.join(args.results_dir, ".cache")
    key = judge_key(args)
    check_judge(args, key)
    source = image_source(args)
    name = args.run_name or default_run_name(args.model)
    run_dir = os.path.join(args.results_dir, name)
    os.makedirs(run_dir, exist_ok=True)
    log = RunLog()
    log.path = os.path.join(run_dir, "run.log")
    started = time.time()
    log("run %s: %d task(s), results in %s" % (name, len(entries), run_dir))

    ledger = get_images(args, source, entries, run_dir, limits, log)
    counts = {}
    for rec in ledger.get("tasks", {}).values():
        counts[rec["status"]] = counts.get(rec["status"], 0) + 1
    log("images: " + ", ".join("%d %s" % (n, status.replace("_", " "))
                               for status, n in sorted(counts.items())))
    with_image = len(ledger.get("tasks", {})) - counts.get("not_generated", 0)
    if not with_image:
        sys.exit("There are no images to judge. See %s for the reasons."
                 % os.path.join(run_dir, "generation.json"))

    log("judging %d image(s)" % with_image)
    try:
        judged = pipeline.judge_all(entries, run_dir, judge=args.judge,
                                    judge_model=args.judge_model, cache_dir=cache_dir, key=key,
                                    workers=args.workers, log=log)
    except judge_vlm.KeyRejected as err:
        sys.exit(rejected_key(args, err))
    merged = pipeline.merge(entries, run_dir)
    summary = report.aggregate(entries, merged, axis_names=tasks.axis_names())
    made = ledger.pop("made_in_this_run", 0)
    paid = judged["paid_vlm_reads"]
    spend = {"images_made": made, "paid_vlm_reads": paid,
             "vlm_reads": sum(s.get("vlm_reads", 0) for s in judged["scores"].values()),
             "usd": round(paid * args.usd_per_vlm_read + made * args.usd_per_image, 2),
             "minutes": round((time.time() - started) / 60.0, 1)}
    report.write(run_dir, summary, generation=ledger, spend=spend)
    report.print_block(summary, run_dir, log=log)


if __name__ == "__main__":
    main()
