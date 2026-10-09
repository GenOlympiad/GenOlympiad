"""Rules for what counts as a printed answer, with per-task exemptions."""
from __future__ import annotations

import re
import logging

log = logging.getLogger(__name__)


SKIP_KEY_RE = re.compile(
    r'^('
    r'q|qa|qa2|qb|qb2|qc|q_[a-z0-9_]+|[a-z0-9_]*_q|d2_[a-z0-9_]+'
    r'|enforce_[a-z0-9_]+|vlm_leaves|flow|deriv|premise_gate'
    r'|[a-z0-9_]*_lo|[a-z0-9_]*_hi'
    r'|tol|core|margin|core_abs|margin_abs|c_core|c_margin|dy_core|dy_margin'
    r'|min_frac|min_area|min_items|size_min|sep_min|coh_min|nmin|n_cols'
    r'|prof_err_target'
    r'|[a-z0-9_]*_noun|[a-z0-9_]*_form|[a-z0-9_]*_label_q'
    r')$'
)

ANSWER_KEY_RE = re.compile(
    r'^('
    r'target[a-z0-9_]*'
    r'|answer[a-z0-9_]*|result|value|reading|measured'
    r'|total|cents|sum'
    r'|signal'
    r'|order_[a-z0-9_]+|[a-z0-9_]+_order'
    r'|tallest|highest|lowest'
    r'|cur_[a-z0-9_]+'
    r'|[a-z0-9_]+_cm|[a-z0-9_]+_mm|[a-z0-9_]+_m|[a-z0-9_]+_deg'
    r')$'
)

MAX_LIST = 32


def _walk_gt(gt, prefix=""):
    if isinstance(gt, dict):
        for k, v in gt.items():
            if not isinstance(k, str) or SKIP_KEY_RE.match(k):
                continue
            if isinstance(v, (dict, list)):
                if isinstance(v, list) and len(v) > MAX_LIST:
                    continue
                for kk, vv in _walk_gt(v, k):
                    yield kk, vv
            else:
                yield k, v
    elif isinstance(gt, list):
        if len(gt) > MAX_LIST:
            return
        for v in gt:
            if isinstance(v, (dict, list)):
                for kk, vv in _walk_gt(v, prefix):
                    yield kk, vv
            else:
                yield prefix, v


def _num_forms(key, v):
    forms = set()
    try:
        f = float(v)
    except (TypeError, ValueError):
        log.debug("error ignored in _num_forms", exc_info=True)
        return forms
    if f == int(f):
        i = int(f)
        forms.add(str(i))
        forms.add("%d.0" % i)
        if abs(i) >= 1000:
            forms.add("{:,}".format(i))
    else:
        s = ("%f" % f).rstrip("0").rstrip(".")
        forms.add(s)
    if "cent" in key:
        forms.add("$%.2f" % (f / 100.0))
        forms.add("$%d" % int(f))
    return forms


def _lit_regex(s):
    esc = re.escape(s)
    if re.match(r'^[-+$]?[\d.,]+$', s):
        esc = esc.replace(r'\.', r'[.,]')
        return r'(?<![0-9A-Za-z.,])' + esc + r'(?![0-9])'
    return r'(?<![0-9A-Za-z])' + esc + r'(?![0-9A-Za-z])'


def _seq_regex(items):
    parts = [re.escape(str(x)) for x in items]
    return r'(?<![0-9A-Za-z])' + r'[\s,;/|.]*'.join(parts) + r'(?![0-9A-Za-z])'


def _int_line_alt(lo, hi, extra=()):
    hi = int(max(lo, min(hi, lo + 200)))
    alts = [str(i) for i in range(int(lo), hi + 1)] + list(extra)
    return r'(?m)^\s*(' + "|".join(alts) + r')\s*$'


CARRIER_EXEMPT = {
    "graduated_scale_numerals": {
        "regex_from_gt": lambda gt: _int_line_alt(0, int(gt.get("vmax") or 100)),
        "shown": "(?m)^\\s*(0|1|...|gt.vmax)\\s*$",
        "rationale":
            "A ruler / graduated scale is defined by its printed tick numerals; a bare "
            "numeral no larger than the scale maximum given in reference answer is a graduation, not a "
            "caption. Bounded by gt.vmax so a number off the scale still counts as a leak.",
    },
    "dial_numerals": {
        "regex_from_gt": lambda gt: _int_line_alt(0, int(gt.get("numeral_count") or 12)),
        "shown": "(?m)^\\s*(0|1|...|gt.numeral_count or 12)\\s*$",
        "rationale":
            "A clock or gauge dial is defined by its printed hour numerals; the prompt "
            "demands the dial, so numerals within the dial's own numbering range are the "
            "requested content, not an answer caption.",
    },
    "button_panel_digits": {
        "regex": r'(?m)^\s*(\d{1,3}|G|B|LG|Emergency|EMERGENCY|\d+-\d+-\d+)\s*$',
        "rationale":
            "Lift car panels inherently carry floor digits, a ground-floor letter, an "
            "EMERGENCY legend and inspection/plate codes; the floor digits ARE the "
            "demanded content of this task.",
    },
    "keycap_legends": {
        "regex": r'(?m)^\s*([A-Za-z0-9]|Tab|Shift|Caps Lock|Ctrl|Alt|Enter|Return|Space'
                 r'|Backspace|Esc|Fn|AltGr)\s*$',
        "rationale":
            "A keyboard is defined by its key legends; the letters ARE the demanded "
            "content of the layout task, so transcribing them is not an answer caption.",
    },
    "punchcard_bits": {
        "regex": r'(?m)^\s*[012]\s*$',
        "rationale":
            "A punched card carries a printed 0/1 digit above every column; the bit grid "
            "is the demanded data payload, not a stated result.",
    },
    "panel_index_numerals": {
        "regex_from_gt": lambda gt: _int_line_alt(1, int(gt.get("n") or 9)),
        "shown": "(?m)^\\s*(1|...|gt.n panels)\\s*$",
        "rationale":
            "A multi-panel comic strip conventionally numbers its panels; a lone digit "
            "within the panel count is a panel index of the demanded layout. Bounded by "
            "the panel count so a larger printed number is still treated as a leak.",
    },
    "peg_and_disk_labels": {
        "regex_from_gt": lambda gt: _int_line_alt(1, int(gt.get("n_disks") or 9),
                                                  extra=("A", "B", "C")),
        "shown": "(?m)^\\s*(A|B|C|1|...|gt.n_disks)\\s*$",
        "rationale":
            "Tower-of-Hanoi renders are demanded with lettered pegs and numbered disks; "
            "those labels are the notation of the puzzle. Bounded by the disk count so a "
            "printed move/visit tally (which exceeds it) is still caught.",
    },
    "plot_axis_ticks": {
        "regex": r'(?m)^\s*([-+]?\d{1,4}([.,]\d+)?\s*\.?|[xy]|[XY])\s*$',
        "rationale":
            "A plotted graph inherently prints axis tick values and axis letters; these "
            "are carrier furniture of any chart, not the plotted curve's answer.",
    },
    "engineering_dimension_callouts": {
        "regex": r'(?m)^\s*(TOP|FRONT|SIDE|PLAN|SECTION|\d{1,4})\s*$',
        "rationale":
            "Orthographic engineering drawings are demanded WITH view names and dimension "
            "callouts; that annotation convention is the requested drawing style, and the "
            "scored leaves of this task are view arrangement, not any printed number.",
    },
    "coin_mint_inscriptions": {
        "regex": r'(?i)\b(LIBERTY|IN GOD WE TRUST|E PLURIBUS UNUM|UNUM|UNITED STATES OF AMERICA'
                 r'|QUARTER DOLLAR|ONE DIME|ONE CENT|FIVE CENTS|ELIZABETH II|D\s*G\s*REG'
                 r'|REGINA|ROYAL MINT|EURO|CENT)\b|\b(1[89]|20)\d{2}\b',
        "rationale":
            "Real coins are minted with a motto, country, denomination and a date; a "
            "render that reproduces them is depicting a coin, not captioning an answer. "
            "Only the mint legend and a 4-digit mint year are exempt -- a currency amount "
            "such as $2.18 is not.",
    },
    "celestial_object_names": {
        "regex": r'(?i)\b(Polaris|Lyra|Vega|Ursa Major|Ursa Minor|Big Dipper|Plough'
                 r'|Cassiopeia|Orion|Draco|Cygnus|Deneb|Altair|North Star)\b',
        "rationale":
            "A star chart names its stars/constellation; naming the object is the poster "
            "convention and does not state the scored geometry (angles and spacings).",
    },
    "street_scene_signage": {
        "regex": r'(?i)\b(SHOPS?|HIGH STREET|BUS|STOP|BUS STOP|NEWS|DELI|CAFE|CAFÉ'
                 r'|BAKERY|POST|OPEN|CLOSED|SALE|HOTEL|BANK|MARKET|PHARMACY|CALLES?)\b',
        "rationale":
            "Ecological street scenes are expected to contain shop fascias, bus-stop "
            "plates and newspaper mastheads; incidental signage is scene furniture and "
            "carries none of the per-panel state the task scores.",
    },
    "garment_and_prop_slogans": {
        "regex": r'(?i)\b(ADVENTURE|AWAITS|ALWAYS|GAS|MILK|TEAM|CAMP|EXPLORE)\b',
        "rationale":
            "Clothing prints, evaluator nameplates and prop branding are incidental "
            "scene text and state no measurement.",
    },
    "book_page_furniture": {
        "regex": r'(?i)\b(START|END|CHAPTER|PAGE)\b',
        "rationale":
            "The book task explicitly demands a START marker on the first page; printing "
            "the demanded marker is compliance, not leakage.",
    },
    "diagram_part_names": {
        "regex": r'(?i)\b(INTRADOS|EXTRADOS|OXTRADOS|GREADOS|FUNICULAR|MASONRY|VAULT'
                 r'|NORMAL|SURFACE|INTERFACE|AIR|GLASS|TRAY|WICK|LEGEND|LEFT|RIGHT'
                 r'|INCIDENT|REFRACTED|RAY|OUTER CURVE|INNER CURVE)\b',
        "rationale":
            "Naming the parts of a demanded technical diagram (part names, legend "
            "entries, material names, side labels) identifies geometry; it does not state "
            "its measured value. Words that can carry a value (height, width, ratio) are "
            "deliberately NOT exempt.",
    },
}


GENERAL_LEAK_RULES = [
    (
        "governing_law_printed",
        r'(?i)(=|equals)\s*(a\s+)?constant\b|\bis\s+constant\b',
        "Printing the governing relation ('h x w = Constant') hands over the very law "
        "the render was supposed to embody, so the reader never has to measure.",
    ),
    (
        "derivation_formula_printed",
        r'(?i)\b(arcsin|arccos|arctan|asin|acos|atan|sin\^?-1|cos\^?-1|tan\^?-1)\b'
        r'|\b(sin|cos|tan)\s*[\(\[]',
        "A trigonometric derivation written on the image states the computed answer "
        "and its working, converting a measurement task into transcription.",
    ),
    (
        "quantity_equality_printed",
        r'(?i)(length|width|height|ratio|value|resistance|current)\s*(/|÷|:)\s*[A-Za-z ]{0,20}'
        r'(length|width|height|ratio|value|resistance|current)\s*\)?\s*=',
        "An equation equating two measured quantities (A length / B length = C length / "
        "D length) asserts the scored relation in words instead of showing it.",
    ),
    (
        "numeric_equality_printed",
        r'(?m)^[^\n]*?(?<![A-Za-z0-9_])[-+]?\d+([.,]\d+)?\s*=\s*[-+]?\d+([.,]\d+)?',
        "A printed numeric identity ('Balanced: 0.5 = 0.5') announces the verification "
        "result that the image was supposed to make measurable, not stated.",
    ),
    (
        "verdict_caption_printed",
        r'(?i)\b(answer|result|solution|verdict|total|balanced|unbalanced|conclusion)\s*[:=]',
        "A captioned verdict ('Answer: ...', 'Balanced: ...') states the conclusion the "
        "deterministic check is supposed to derive from the depicted geometry. The colon/equals is "
        "required so that an isolated adjective in incidental scene lettering (a shop "
        "fascia, a garment print) is not mistaken for a caption.",
    ),
]


_MEASURE_CALLOUT = (
    "metric_dimension_callout",
    r'(?<![0-9A-Za-z])[-+]?\d+([.,]\d+)?\s*(cm|mm|centimet(re|er)s?|millimet(re|er)s?)\b',
    "The scored quantity of this task IS a physical length/size read off the picture; "
    "printing that length as a dimension callout replaces the measurement with text.",
)

_PCT_CALLOUT = (
    "fraction_percentage_callout",
    r'(?<![0-9A-Za-z])[-+]?\d+([.,]\d+)?\s*%',
    "The scored quantity of this task is a dimensionless fraction; a percentage "
    "printed on the object states that fraction outright.",
)

NOANS_RULES = {
    "ccw_clock_time": {"exempt": ["dial_numerals"]},
    "even_floor_elevator": {"exempt": ["button_panel_digits"]},

    "punchcard_parity": {"exempt": ["punchcard_bits"]},
    "hanoi_disk1_visit_tally": {"exempt": ["peg_and_disk_labels"]},
    "hanoi_illegal_freeze": {"exempt": ["peg_and_disk_labels"]},
    "hanoi_midstate_nonstd": {"exempt": ["peg_and_disk_labels"]},
    "hanoi_midstate_optimal": {"exempt": ["peg_and_disk_labels"]},
    "hanoi_reroot_target": {"exempt": ["peg_and_disk_labels"]},
    "polynomial_plot": {"exempt": ["plot_axis_ticks"]},
    "multiview_depth_coupling": {"exempt": ["engineering_dimension_callouts"]},

    "derive_countdown_ledger": {"exempt": ["panel_index_numerals", "street_scene_signage"]},
    "derive_interval_recurrence": {"exempt": ["panel_index_numerals", "street_scene_signage"]},
    "derive_undo_rollback": {"exempt": ["panel_index_numerals", "street_scene_signage"]},
    "derive_rotation_lineup": {"exempt": ["panel_index_numerals", "street_scene_signage"]},

    "coin_change_exact": {"exempt": ["coin_mint_inscriptions"]},

    "count_tray_conservation": {"exempt": ["diagram_part_names"]},

    "big_dipper_pointer": {"exempt": ["celestial_object_names"]},

    "three_candles_burn_order": {"leak": [_MEASURE_CALLOUT]},
    "popsicle_melt_frames": {"leak": [_MEASURE_CALLOUT]},

    "anaglyph_parallax": {"leak": [_PCT_CALLOUT]},

    "refraction_snell": {"exempt": ["diagram_part_names"]},
    "capillary_rise_inverse": {"exempt": ["diagram_part_names"]},

}

NO_TEXT_RE = re.compile(r'^\s*(none|no text|n/?a|-{0,3})\s*\.?\s*$', re.I)


def _variant_gt(task, level):
    for v in (task or {}).get("variants", []):
        if v.get("level") == level:
            return v.get("gt", {}) or {}
    return {}


def _build_patterns(gt):
    answer_lits, answer_seqs, given_lits = [], [], []
    seen_answer = set()

    def add_answer(key, val):
        if isinstance(val, bool) or val is None:
            return
        if isinstance(val, (int, float)):
            for f in _num_forms(key, val):
                if f not in seen_answer:
                    seen_answer.add(f)
                    answer_lits.append((key, f))
        elif isinstance(val, str):
            s = val.strip()
            if len(s) >= 3 and re.fullmatch(r'[A-Z]{3,12}', s):
                answer_seqs.append((key, list(s)))
            elif len(s) >= 2 and s not in seen_answer:
                seen_answer.add(s)
                answer_lits.append((key, s))

    for k, v in _walk_gt(gt):
        if ANSWER_KEY_RE.match(k):
            add_answer(k, v)
    for k, v in (gt or {}).items():
        if isinstance(k, str) and ANSWER_KEY_RE.match(k) and isinstance(v, list) \
                and 2 < len(v) <= MAX_LIST and all(isinstance(x, (str, int, float)) for x in v):
            answer_seqs.append((k, [str(x) for x in v]))

    for k, v in _walk_gt(gt):
        if ANSWER_KEY_RE.match(k) or isinstance(v, bool) or v is None:
            continue
        if isinstance(v, (int, float)):
            for f in _num_forms(k, v):
                given_lits.append((k, f))
        elif isinstance(v, str):
            s = v.strip()
            if len(s) >= 2:
                given_lits.append((k, s))

    given_vals = {s for _, s in given_lits}
    answer_lits = [(k, s) for k, s in answer_lits if s not in given_vals]
    return answer_lits, answer_seqs, given_lits


def _exempt_regex(name, gt):
    ent = CARRIER_EXEMPT[name]
    if "regex_from_gt" in ent:
        try:
            return ent["regex_from_gt"](gt or {})
        except Exception:
            log.debug("error ignored in _exempt_regex", exc_info=True)
            return ent["regex_from_gt"]({})
    return ent["regex"]


def _mask(text, regex, flags=0):
    def rep(m):
        return re.sub(r'[^\n]', ' ', m.group(0))
    try:
        return re.sub(regex, rep, text, flags=flags)
    except re.error:
        log.debug("error ignored in _mask", exc_info=True)
        return text


def classify(transcript, mode, level, task):
    hits = []
    if transcript is None or NO_TEXT_RE.match(str(transcript)):
        return {"leak": False, "hits": [], "rule": "no_text"}
    text = str(transcript)
    if not text.strip():
        return {"leak": False, "hits": [], "rule": "no_text"}

    gt = _variant_gt(task, level)
    answer_lits, answer_seqs, given_lits = _build_patterns(gt)
    cfg = NOANS_RULES.get(mode, {})

    masked = text
    for name in cfg.get("exempt", []):
        masked = _mask(masked, _exempt_regex(name, gt))
    for _k, lit in given_lits:
        masked = _mask(masked, _lit_regex(lit))

    for key, lit in answer_lits:
        m = re.search(_lit_regex(lit), masked)
        if m:
            hits.append({"rule": "answer_value_printed", "match": m.group(0).strip(),
                         "gt_key": key})
    for key, seq in answer_seqs:
        m = re.search(_seq_regex(seq), masked)
        if m:
            hits.append({"rule": "answer_sequence_printed",
                         "match": " ".join(m.group(0).split()), "gt_key": key})

    for name, rx, _rat in GENERAL_LEAK_RULES:
        m = re.search(rx, masked)
        if m:
            hits.append({"rule": name, "match": " ".join(m.group(0).split())})
    for name, rx, _rat in cfg.get("leak", []):
        m = re.search(rx, masked)
        if m:
            hits.append({"rule": name, "match": " ".join(m.group(0).split())})

    if hits:
        return {"leak": True, "hits": [h["match"] for h in hits],
                "rule": hits[0]["rule"], "detail": hits}
    return {"leak": False, "hits": [], "rule": "no_answer_text_found"}


TRANSCRIBE_Q = (
    "Read out every piece of printed text you can see in this image: every word, letter, number "
    "and caption, each on its own line. Include text printed on objects. If there is no printed "
    "text at all, reply exactly: NONE"
)

_LEVEL_TAIL = re.compile(r"__[A-Za-z0-9]+$")


def mode_of(task):
    if not isinstance(task, dict):
        return None
    tid = task.get("id")
    if not isinstance(tid, str):
        return None
    lv = task.get("_variant_level")
    if lv and tid.endswith("__" + str(lv)):
        return tid[: -len("__" + str(lv))]
    return _LEVEL_TAIL.sub("", tid)


def level_of(task):
    if not isinstance(task, dict):
        return None
    lv = task.get("_variant_level")
    if lv:
        return str(lv)
    tid = task.get("id")
    if isinstance(tid, str) and "__" in tid:
        tail = tid.rsplit("__", 1)[1]
        if tail != "ctrl":
            return tail
    return None


def variant_gt(task, level=None, ctx_gt=None):
    if isinstance(task, dict):
        vg = task.get("_variant_gt")
        if isinstance(vg, dict) and vg:
            return dict(vg), "variant_gt"
        lv = level or level_of(task)
        for v in task.get("variants") or []:
            if v.get("level") == lv:
                return dict(v.get("gt") or {}), "variants_by_level"
    if isinstance(ctx_gt, dict) and ctx_gt:
        return dict(ctx_gt), "merged_ctx"
    return {}, "none"


def _variant_gt(task, level):
    gt, _src = variant_gt(task, level)
    return gt


TOLERANCE_KEY_RE = re.compile(r"(_err_target|_err|_tol|_eps|_margin|_core)$|^(tol|core|margin)$")

_NON_ANSWER_POINT_RE = re.compile(r"^(d\d+_|no_answer_text$|scene_compliance$)")


def answer_keys_from_task(task):
    keys = set()
    for pt in (task or {}).get("scoring", []) or []:
        if _NON_ANSWER_POINT_RE.match(str(pt.get("id", ""))):
            continue
        for s in pt.get("flow", []) or []:
            if not isinstance(s, dict) or not str(s.get("op", "")).startswith("compare."):
                continue
            t = s.get("target")
            if isinstance(t, str) and t.startswith("gt."):
                parts = t.split(".")
                if len(parts) >= 2 and not TOLERANCE_KEY_RE.search(parts[1]):
                    keys.add(parts[1])
    return keys


def build_patterns(gt, answer_keys=()):
    global ANSWER_KEY_RE
    if not answer_keys:
        return _build_patterns(gt)
    pat = ANSWER_KEY_RE.pattern
    if not pat.endswith(")$"):
        return _build_patterns(gt)
    widened = pat[:-2] + "|" + "|".join(re.escape(k) for k in sorted(answer_keys)) + ")$"
    saved = ANSWER_KEY_RE
    ANSWER_KEY_RE = re.compile(widened)
    try:
        return _build_patterns(gt)
    finally:
        ANSWER_KEY_RE = saved


SHORT_ANSWER_MAX = 2

_ANSWER_CONTEXT_WORDS = (r"answers?|totals?|sums?|results?|solutions?|roots?|values?|counts?|"
                         r"equals?|is|are|=")
ANSWER_CONTEXT_LEFT = re.compile(
    r"(?:[=:]|\b(?:" + _ANSWER_CONTEXT_WORDS + r")\b)[ \t]*\n?[ \t]*$", re.I)
ANSWER_CONTEXT_RIGHT = re.compile(r"^[ \t]*\n?[ \t]*(?:[=:])", re.I)


def has_answer_context(text, start, end):
    return bool(ANSWER_CONTEXT_LEFT.search(text[:start])
                or ANSWER_CONTEXT_RIGHT.match(text[end:]))


_TRAILING_ZERO = re.compile(r"^(-?\d+)\.0$")


def answer_length(lit):
    s = str(lit).replace(",", "")
    m = _TRAILING_ZERO.match(s)
    if m:
        s = m.group(1)
    return len(s)


def _find_answer_literal(masked, lit):
    rx = _lit_regex(lit)
    short = answer_length(lit) <= SHORT_ANSWER_MAX
    for m in re.finditer(rx, masked):
        if short and not has_answer_context(masked, m.start(), m.end()):
            continue
        return m
    return None


def classify(transcript, mode, level, task, answer_keys=None):
    hits = []
    if transcript is None or NO_TEXT_RE.match(str(transcript)):
        return {"leak": False, "hits": [], "rule": "no_text", "laws": _LAWS_APPLIED,
                "answer_keys": []}
    text = str(transcript)
    if not text.strip():
        return {"leak": False, "hits": [], "rule": "no_text", "laws": _LAWS_APPLIED,
                "answer_keys": []}

    gt = _variant_gt(task, level)
    keys = answer_keys_from_task(task) if answer_keys is None else set(answer_keys)
    answer_lits, answer_seqs, given_lits = build_patterns(gt, keys)
    cfg = NOANS_RULES.get(mode, {})

    masked = text
    for name in cfg.get("exempt", []):
        masked = _mask(masked, _exempt_regex(name, gt))
    for _k, lit in given_lits:
        masked = _mask(masked, _lit_regex(lit))

    for key, lit in answer_lits:
        m = _find_answer_literal(masked, lit)
        if m:
            hits.append({"rule": "answer_value_printed", "match": m.group(0).strip(),
                         "gt_key": key})
    for key, seq in answer_seqs:
        m = re.search(_seq_regex(seq), masked)
        if m:
            hits.append({"rule": "answer_sequence_printed",
                         "match": " ".join(m.group(0).split()), "gt_key": key})

    for name, rx, _rat in GENERAL_LEAK_RULES:
        m = re.search(rx, masked)
        if m:
            hits.append({"rule": name, "match": " ".join(m.group(0).split())})
    for name, rx, _rat in cfg.get("leak", []):
        m = re.search(rx, masked)
        if m:
            hits.append({"rule": name, "match": " ".join(m.group(0).split())})

    out = {"laws": _LAWS_APPLIED, "answer_keys": sorted(keys)}
    if hits:
        out.update({"leak": True, "hits": [h["match"] for h in hits],
                    "rule": hits[0]["rule"], "detail": hits})
    else:
        out.update({"leak": False, "hits": [], "rule": "no_answer_text_found"})
    return out


_LAWS_APPLIED = ("spec_is_truth_answer_keys", "exemption_first", "short_answer_context")


