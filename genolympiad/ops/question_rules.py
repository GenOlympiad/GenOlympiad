"""Wording rules for the questions the evaluation pipeline asks."""
import re
import logging

log = logging.getLogger(__name__)


_PRONOUN = r"(?!\s+(?:it|its|them|their|him|her|each\s+other|one\s+another)\b)"
_ANCHOR = re.compile(
    r"\s+(?:"
    r"(?:printed\s+|drawn\s+|sitting\s+|shown\s+|set\s+|placed\s+)?"
    r"(?:below|above|beneath|underneath|beside|alongside|next\s+to"
    r"|to\s+the\s+(?:left|right)\s+of)" + _PRONOUN +
    r"|at\s+the\s+(?:foot|top|bottom|head|centre|center|end)\s+of"
    r"|(?:on|along|down)\s+the\s+(?:right|left|top|bottom|upper|lower)\s+(?:edge|side|margin)\s+of"
    r"|(?:on|in|inside)\s+the\s+[a-z][\w-]*(?:\s+[a-z][\w-]*){0,3}?\s+"
    r"(?:card|sheet|page|form|panel|chart|rack|board|slip|table|screen|label|strip|frame)\b"
    r")\b.*$", re.I)
_WITH_CLAUSE = re.compile(r"\bwith\b", re.I)

_MIN_WORDS = 2


def crop_phrase(target):
    s = str(target)
    m = _ANCHOR.search(s)
    if not m:
        return s, False, "no page-level positional clause -- returned unchanged"
    w = _WITH_CLAUSE.search(s)
    if w and w.start() < m.start() and "," not in s[w.start():m.start()]:
        return s, False, ("the clause sits inside a `with ...` description of the target's own "
                          "appearance, not a page-level anchor -- returned unchanged")
    head = s[:m.start()].strip().rstrip(",;:")
    if len(head.split()) < _MIN_WORDS or not re.search(r"[A-Za-z]", head):
        return s, False, ("stripping %r would leave too little to identify the target (%r), so "
                          "the ask is left exactly as authored" % (m.group(0).strip()[:40], head))
    return head, True, ("dropped the page-level clause %r: a crop cannot show it, so the question "
                        "could not be true of the picture it was asked about"
                        % m.group(0).strip()[:60])


def crop_target(target):
    phrase, changed, _why = crop_phrase(target)
    if not changed:
        return target
    art = getattr(target, "article", None)
    if art is None:
        return phrase
    for build in (lambda: type(target)(phrase, art), lambda: type(target)(phrase)):
        try:
            out = build()
        except Exception:
            log.debug("error ignored in crop_target", exc_info=True)
            continue
        if getattr(out, "article", None) != art:
            try:
                out.article = art
            except Exception:
                log.debug("error ignored in crop_target", exc_info=True)
                continue
        return out
    return phrase


LEADING_DETERMINERS = (
    "a", "an", "the", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine",
    "ten", "each", "every", "any", "this", "that", "these", "those", "1", "2",
    "3", "4", "5", "6", "7", "8", "9", "10",
)


def leads_with_determiner(target):
    w = re.split(r"\s+", str(target).strip(), 1)
    return bool(w) and w[0].strip().lower().strip(".,;:") in LEADING_DETERMINERS


def article_prefix(target, shipped):
    if leads_with_determiner(target):
        return ""
    return shipped


def one_prefix(target):
    return article_prefix(target, "one ")


_A_NOT_AN = (
    "usage", "use", "used", "useful", "user", "using", "usual", "usurp", "unit", "unity",
    "union", "unique", "unified", "uniform", "unilateral", "universal", "university",
    "urine", "urinal", "utility", "utilities", "utensil", "ubiquit", "ukulele", "eucalypt",
    "euro", "europ", "eulog", "eureka", "ewe", "once", "one-", "ouija",
)
_AN_NOT_A = ("hour", "honest", "honour", "honor", "heir")


def indefinite(target):
    try:
        w = re.split(r"\s+", str(target).strip(), 1)[0]
    except Exception:
        log.debug("error ignored in indefinite", exc_info=True)
        return "a "
    core = w.strip("\"'([{").lower()
    if not core:
        return "a "
    if any(core.startswith(p) for p in _AN_NOT_A):
        return "an "
    if any(core.startswith(p) for p in _A_NOT_AN):
        return "a "
    return "an " if core[0] in "aeiou" else "a "


def the_prefix(target):
    if leads_with_determiner(target):
        return ""
    return "the "


def a_prefix(target):
    return article_prefix(target, indefinite(target))


DASH_CLAUSE = "If this cannot be told from this picture, answer -"


def with_dash(q, op=None, authored_none_fn=None):
    return q


DASH_TOKENS = frozenset(("-", "--", "---", "–", "—", "−", '"-"', "'-'", "[-]"))


def declined(ans, q):
    if ans is None or DASH_CLAUSE not in str(q or ""):
        return False
    s = str(ans).strip().strip(".;,:!").strip()
    return s in DASH_TOKENS
