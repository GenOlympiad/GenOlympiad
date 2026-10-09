"""Per-question read settings for the judge VLM, such as votes and thinking budget."""
from __future__ import annotations
import io, json, os, re
import logging

log = logging.getLogger(__name__)

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_WHITELIST_PATH = os.path.join(_ROOT, 'data', "read_policy_whitelist.json")

_WL = None
_POLICY = None
_LEVEL_TAIL = re.compile(r"__[A-Za-z0-9]+$")


def _load():
    global _WL, _POLICY
    if _WL is not None:
        return
    _WL, _POLICY = {}, {}
    try:
        d = json.load(io.open(_WHITELIST_PATH, encoding="utf-8"))
    except Exception:
        log.debug("error ignored in _load", exc_info=True)
        return
    _POLICY = d.get("policy") or {}
    for e in d.get("entries", []):
        _WL[(e.get("mode"), e.get("point"))] = e


def base_task_id(task):
    """Base id of a (possibly variant-flattened) task."""
    if not isinstance(task, dict):
        return None
    tid = task.get("id")
    if not isinstance(tid, str):
        return None
    lv = task.get("_variant_level")
    if lv and tid.endswith("__" + str(lv)):
        return tid[: -len("__" + str(lv))]
    return _LEVEL_TAIL.sub("", tid)


STRUCTURED_OPS = {"vlm.read_seq", "vlm.read_grid", "vlm.read_stone_grid"}


def policy_for(task, point_id, qref=None, op=None):
    if not point_id:
        return None
    if op in STRUCTURED_OPS:
        return None
    _load()
    e = _WL.get((base_task_id(task), point_id))
    if not e:
        return None
    lv = task.get("_variant_level") if isinstance(task, dict) else None
    levels = e.get("levels") or []
    if lv is not None and levels and lv not in levels:
        return None
    qrefs = e.get("qrefs") or []
    if qrefs and qref is not None and qref not in qrefs:
        return None
    p = dict(_POLICY)
    p["classes"] = e.get("classes", [])
    p["levels"] = levels
    return p


PARAPHRASES = (
    lambda q: q + "\n\nGive only the answer itself, in exactly the format requested above. "
                  "Do not show your working.",
    lambda q: "Question:\n" + q + "\n\nRespond with the answer only, exactly in the format the "
                                  "question asks for.",
    lambda q: "Answer the following question about the image.\n\n" + q +
              "\n\nOutput the answer alone, in the requested format, with nothing else.",
)


def paraphrase(q, i):
    return PARAPHRASES[i % len(PARAPHRASES)](q)


_RETRY_WRAP = (lambda q: "Look at the image carefully and answer this question.\n\n" + q +
                         "\n\nReply with the answer only, exactly in the format the question "
                         "asks for, and nothing else.")


def retry_wrap(q):
    return _RETRY_WRAP(q)
