"""Operators: every module here registers its operators into OPS when imported."""
from ._base import OPS, Fail, majority, resolve, register, as_float
from . import logic
from . import run_code
from . import fetch
from . import calibration
from . import recognize
from . import flow_control
from . import read_text
from . import deterministic_checks
from . import logic_domain
from . import overlay
from .recognize import set_vlm_reader
from .flow_control import set_flow_runner
from . import no_answer
from . import evidence_grounding
from . import compute_ops
