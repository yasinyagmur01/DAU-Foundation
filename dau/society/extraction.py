"""Decision → CPR harvest amount — shared by production graph and society pilots.

Biology analogy: the organism's announced act is translated into a physical
withdrawal from the commons. Mapping is deterministic Python (no LLM judge).
"""

from __future__ import annotations

import re

from dau.foundation.constraints import (
    METABOLIC_GAIN_HALF_SATURATION,
    METABOLIC_GAIN_MAX,
)
from dau.foundation.lod import (
    NPC_ACTION_CONSERVE,
    NPC_ACTION_COOPERATE,
    NPC_ACTION_EXTRACT_MODERATE,
    NPC_ACTION_MAINTAIN,
    NPC_ACTION_OBSERVE,
)
from dau.foundation.social import (
    OUTCOME_COORDINATE,
    OUTCOME_COOPERATE,
    OUTCOME_DEADLOCK,
    OUTCOME_DEFECT,
)

# ---------------------------------------------------------------------------
# CPR harvest amounts — cooperate restrains, defect over-extracts
# ---------------------------------------------------------------------------

EXTRACTION_COOPERATE: float = 2.0
EXTRACTION_DEFECT: float = 8.0
EXTRACTION_COORDINATE: float = 1.0
EXTRACTION_DEADLOCK: float = 0.0
EXTRACTION_DEFAULT: float = 1.0

# Decision token → social outcome (NPC actions + keyword stubs)
DECISION_TO_OUTCOME: dict[str, str] = {
    NPC_ACTION_COOPERATE: OUTCOME_COOPERATE,
    NPC_ACTION_EXTRACT_MODERATE: OUTCOME_DEFECT,
    NPC_ACTION_CONSERVE: OUTCOME_COORDINATE,
    NPC_ACTION_OBSERVE: OUTCOME_COORDINATE,
    NPC_ACTION_MAINTAIN: OUTCOME_COORDINATE,
}

OUTCOME_TO_EXTRACTION: dict[str, float] = {
    OUTCOME_COOPERATE: EXTRACTION_COOPERATE,
    OUTCOME_DEFECT: EXTRACTION_DEFECT,
    OUTCOME_COORDINATE: EXTRACTION_COORDINATE,
    OUTCOME_DEADLOCK: EXTRACTION_DEADLOCK,
}

DEFECT_KEYWORDS: tuple[str, ...] = (
    "extract",
    "take",
    "defect",
    "refuse",
    "harvest",
    "gather",
    "collect",
)
COOPERATE_KEYWORDS: tuple[str, ...] = ("cooperate", "share", "talk", "social")
CONSERVE_KEYWORDS: tuple[str, ...] = (
    "conserve",
    "rest",
    "wait",
    "observe",
    "restrain",
    "spare",
)

# ---------------------------------------------------------------------------
# Non-harvest usages of DEFECT keywords — stripped before matching (D-092)
# ---------------------------------------------------------------------------
# D-091 measured the defect: DEFECT keywords fired on announcements that
# withdrew nothing at all (14 of 35 `defect` calls carried no harvest
# expression whatsoever). Two usages carried nearly all of it, and both are
# about what the verb is applied to, not about what the organism decided:
#
#   "I will take a moment to assess"      -> English idiom, no object
#   "extract as much information as I can" -> object is not the commons
#
# Both are removed before keyword matching, so the DEFECT branch fires only on
# a surviving harvest expression. The branch ORDER below is deliberately
# unchanged: an announced withdrawal is physical, and cooperation language
# standing next to it does not put the units back. Two alternatives were
# measured on the same 36 real completions and rejected (D-092): "most
# keywords wins" rewards verbosity, "first act announced wins" rewards the
# opening sentence — both tie the harvest to rhetoric rather than to the act.
#
# Only the VERB is removed, never its surroundings (lookahead, not a span
# match): "take a short rest" must lose `take` and keep `rest`, otherwise the
# fix would silently delete CONSERVE evidence while repairing DEFECT.
NON_HARVEST_VERB_FORMS: str = r"tak(?:e|es|en|ing)"
NON_HARVEST_IDIOM_OBJECTS: tuple[str, ...] = (
    "moment",
    "minute",
    "second",
    "breath",
    "step back",
    "stock",
    "note",
    "care",
    "time",
    "account",
    "rest",
    "break",
    "look",
    "chance",
    "turn",
)
NON_COMMONS_VERB_FORMS: str = r"(?:extract|gather|collect|harvest|take)\w*"
NON_COMMONS_OBJECTS: tuple[str, ...] = (
    "information",
    "data",
    "insight",
    "knowledge",
    "detail",
    "context",
    "feedback",
    "input",
)
NON_HARVEST_DETERMINERS: str = r"(?:a |an |some |the |few |several |my |its )*"
NON_HARVEST_ADJECTIVE: str = r"(?:\w+ )?"
NON_HARVEST_QUANTIFIERS: str = (
    r"(?:as much |as many |some |more |additional |any |all |the |further )*"
)

NON_HARVEST_IDIOM_RE: re.Pattern[str] = re.compile(
    rf"\b{NON_HARVEST_VERB_FORMS}\b(?=\s+{NON_HARVEST_DETERMINERS}"
    rf"{NON_HARVEST_ADJECTIVE}(?:{'|'.join(NON_HARVEST_IDIOM_OBJECTS)})s?\b)",
    re.IGNORECASE,
)
NON_COMMONS_OBJECT_RE: re.Pattern[str] = re.compile(
    rf"\b{NON_COMMONS_VERB_FORMS}(?=\s+{NON_HARVEST_QUANTIFIERS}"
    rf"(?:{'|'.join(NON_COMMONS_OBJECTS)})s?\b)",
    re.IGNORECASE,
)
NON_HARVEST_PATTERNS: tuple[re.Pattern[str], ...] = (
    NON_HARVEST_IDIOM_RE,
    NON_COMMONS_OBJECT_RE,
)
NON_HARVEST_REPLACEMENT: str = " "

# Parse explicit harvest quantities from free-text LLM announcements
HARVEST_UNITS_RE: re.Pattern[str] = re.compile(
    r"(\d+(?:\.\d+)?)\s*(?:units?|of the resource)",
    re.IGNORECASE,
)
HARVEST_PERCENT_RE: re.Pattern[str] = re.compile(
    r"(\d+(?:\.\d+)?)\s*%",
    re.IGNORECASE,
)
EXTRACTION_PARSE_MAX: float = 25.0
PERCENT_TO_POOL_SCALE: float = 100.0  # pct/100 * scale → absolute units


def _contains_any(text: str, keywords: tuple[str, ...]) -> bool:
    """True if any keyword appears in lowercased text."""

    lowered = text.lower()
    return any(keyword in lowered for keyword in keywords)


def strip_non_harvest_usages(text: str) -> str:
    """Remove DEFECT-keyword usages that announce no withdrawal (D-092).

    Idiomatic ("take a moment") and non-commons ("extract information") uses of
    a harvest verb are not physical acts on the pool, so they must not reach the
    keyword match. Deterministic regex only — no LLM judge (2nd prohibition).
    """

    stripped = text
    for pattern in NON_HARVEST_PATTERNS:
        stripped = pattern.sub(NON_HARVEST_REPLACEMENT, stripped)
    return stripped


def decision_to_outcome(decision: str) -> str:
    """Map free-text / NPC decision to OUTCOME_* (deterministic, no LLM judge)."""

    token = decision.strip().lower()
    if token in DECISION_TO_OUTCOME:
        return DECISION_TO_OUTCOME[token]
    token = strip_non_harvest_usages(token)
    if _contains_any(token, DEFECT_KEYWORDS):
        return OUTCOME_DEFECT
    if _contains_any(token, COOPERATE_KEYWORDS):
        return OUTCOME_COOPERATE
    if _contains_any(token, CONSERVE_KEYWORDS):
        return OUTCOME_COORDINATE
    return OUTCOME_DEADLOCK


def decision_to_extraction(decision: str) -> float:
    """Map decision → harvest amount; prefer parsed quantity, else outcome table."""

    units_match = HARVEST_UNITS_RE.search(decision)
    if units_match is not None:
        return min(float(units_match.group(1)), EXTRACTION_PARSE_MAX)
    percent_match = HARVEST_PERCENT_RE.search(decision)
    if percent_match is not None:
        fraction = float(percent_match.group(1)) / 100.0
        return min(fraction * PERCENT_TO_POOL_SCALE, EXTRACTION_PARSE_MAX)
    outcome = decision_to_outcome(decision)
    return OUTCOME_TO_EXTRACTION.get(outcome, EXTRACTION_DEFAULT)


def metabolic_gain(realized_extraction: float) -> float:
    """Energy returned by a harvest — concave, saturating (A4 / D-066).

    Biology analogy: the first mouthful is worth far more than the tenth. Flux
    is a concave-hyperbolic function of activity and selection goes neutral at
    saturation (DR #4 / J9 — Dykhuizen, Dean & Hartl 1987, Genetics 115:25-31),
    so a proportional "harvest = energy" link would keep over-extraction
    strictly dominant and rebuild the flat fitness landscape it is meant to
    break.

    Takes the REALIZED harvest, never the announced one: an empty pasture must
    not feed anyone (see environment.realized_extractions).
    """

    harvest = float(realized_extraction)
    if harvest <= 0.0:
        return 0.0
    return METABOLIC_GAIN_MAX * harvest / (METABOLIC_GAIN_HALF_SATURATION + harvest)
