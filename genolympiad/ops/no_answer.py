"""Check that the image does not simply print the answer the task asks the model to show."""
from __future__ import annotations

import logging

log = logging.getLogger(__name__)

from ._base import register, resolve
from . import no_answer_rules as R


class NoAnsVerdict(str):
    """A human sentence that also answers `.answer` / `.unreadable` / `.hits` / `.transcript`."""

    def __new__(cls, sentence, **fields):
        self = super().__new__(cls, sentence)
        for k, v in fields.items():
            setattr(self, k, v)
        return self

    def as_dict(self):
        return {"sentence": str(self), "answer": self.answer, "leak": self.leak,
                "rule": self.rule, "hits": self.hits, "detail": self.detail,
                "unreadable": self.unreadable, "transcript": self.transcript,
                "mode": self.mode, "level": self.level, "gt_source": self.gt_source,
                "reader_calls": self.reader_calls, "collapse_suspect": self.collapse_suspect,
                "question": self.question}


_HIT_SHOWN = 3
_HIT_CHARS = 40


def _sentence(res, hits):
    if not res["leak"]:
        return ("clean: no printed text at all [no_text]" if res["rule"] == "no_text"
                else "clean: printed text carries no answer [%s]" % res["rule"])
    shown = ", ".join('"%s"' % str(h)[:_HIT_CHARS] for h in hits[:_HIT_SHOWN])
    more = "" if len(hits) <= _HIT_SHOWN else " (+%d more)" % (len(hits) - _HIT_SHOWN)
    return "LEAK: printed answer text %s%s [%s]" % (shown, more, res["rule"])


def _transcribe(im, retries):
    try:
        from .recognize import _reader
    except ImportError:
        log.debug("error ignored in _transcribe", exc_info=True)
        from genolympiad.ops.recognize import _reader
    calls = 0
    for _ in range(max(1, int(retries))):
        calls += 1
        try:
            a = _reader()(im, R.TRANSCRIBE_Q)
        except NotImplementedError:
            raise
        except Exception:
            log.debug("error ignored in _transcribe", exc_info=True)
            a = None
        if a is not None and str(a).strip():
            return str(a), calls
    return None, calls


_COLLAPSE_TOKENS = {"yes", "no", "true", "false"}


def _op_noans_check(ctx, step):
    q = step.get("question")
    if q is not None and str(q) != R.TRANSCRIBE_Q:
        raise ValueError(
            "vlm.noans_check: the transcription question is FIXED (no_answer_rules.TRANSCRIBE_Q). A "
            "reworded question would no longer be the tested question, so it is refused rather than "
            "silently obeyed.")

    task = ctx.get("task") or {}
    mode = R.mode_of(task)
    level = R.level_of(task)
    gt, gt_source = R.variant_gt(task, level, ctx.get("gt"))

    im = resolve(ctx, step.get("image", "image"))
    text, calls = _transcribe(im, step.get("retries", 3))

    common = {"mode": mode, "level": level, "gt_source": gt_source, "reader_calls": calls,
              "question": R.TRANSCRIBE_Q, "transcript": text}

    if text is None:
        v = NoAnsVerdict(
            "UNREAD: the reader returned no transcript after %d attempt(s) "
            "(evaluator fault, not a model crash)" % calls,
            answer=None, leak=None, rule="reader_outage", hits=[], detail=None,
            unreadable=True, empty=True, no_read=True, collapse_suspect=False, **common)
        return v

    res = R.classify(text, mode, level, task if gt_source != "merged_ctx"
                     else {**task, "_variant_gt": gt})
    hits = list(res.get("hits") or [])
    v = NoAnsVerdict(
        _sentence(res, hits),
        answer=("yes" if res["leak"] else "no"),
        leak=bool(res["leak"]), rule=res.get("rule"), hits=hits,
        detail=res.get("detail"), unreadable=False, empty=False, no_read=False,
        collapse_suspect=(str(text).strip().lower() in _COLLAPSE_TOKENS), **common)
    return v


register("vlm.noans_check")(_op_noans_check)


