"""Child process that evaluates one batch of tasks (started by pipeline.judge_all)."""
import io
import json
import logging
import os
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor


def main(job_path):
    """Evaluate the tasks named in the job file and write one score file per task."""
    with io.open(job_path, encoding="utf-8") as fh:
        job = json.load(fh)
    os.makedirs(job["scratch"], exist_ok=True)
    tempfile.tempdir = tempfile.mkdtemp(dir=job["scratch"])
    from . import judge_vlm, score
    score.prepare()
    judge_vlm.configure(job["judge"], model=job.get("judge_model"), cache_dir=job["cache_dir"])
    judge_vlm._set_repeat_tag(job.get("fresh") or "")
    os.makedirs(job["out_dir"], exist_ok=True)

    def one(entry):
        image = os.path.join(job["images_dir"], entry["task_id"] + ".png")
        s = score.judge(entry, image)
        path = os.path.join(job["out_dir"], entry["task_id"] + ".json")
        with io.open(path + ".tmp", "w", encoding="utf-8", newline="\n") as fh:
            json.dump(s, fh, ensure_ascii=False, indent=1, sort_keys=True)
            fh.write("\n")
        os.replace(path + ".tmp", path)
        return s["status"]

    with ThreadPoolExecutor(max_workers=max(1, int(job.get("workers") or 1))) as ex:
        list(ex.map(one, job["entries"]))
    with io.open(job["done_file"], "w", encoding="utf-8") as fh:
        json.dump({"paid_vlm_reads": judge_vlm.paid_vlm_reads(),
                   "key_rejected": judge_vlm.rejected()}, fh)
    import shutil
    shutil.rmtree(tempfile.tempdir)
    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s")
    sys.exit(main(sys.argv[1]))
