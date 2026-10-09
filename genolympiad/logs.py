"""Logging for the evaluation pipeline."""
import logging

_log = logging.getLogger("genolympiad")


def say(*args, **kwargs):
    """Send a message to the log at info level instead of printing it."""
    _log.info(" ".join(str(a) for a in args))
