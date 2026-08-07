"""Decision → CPR harvest amount — shared by production graph and society pilots.

Biology analogy: the organism's announced act is translated into a physical
withdrawal from the commons. Mapping is deterministic Python (no LLM judge).
"""

from __future__ import annotations

import re

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


def decision_to_outcome(decision: str) -> str:
    """Map free-text / NPC decision to OUTCOME_* (deterministic, no LLM judge)."""

    token = decision.strip().lower()
    if token in DECISION_TO_OUTCOME:
        return DECISION_TO_OUTCOME[token]
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
