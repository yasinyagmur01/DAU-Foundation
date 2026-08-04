"""Tests for Layer 1.5 semantic prediction-error sensor (MiniLM).

Inverts the old Jaccard characterization suite: paraphrase PE must fall
below unrelated PE; exact match ≈ 0. Negation remains a known MiniLM limit.
"""

from __future__ import annotations

import pytest

from dau.foundation.graph import (
    EXPECTED_OUTCOME_ENERGY,
    EXPECTED_OUTCOME_RESOURCE,
    EXPECTED_OUTCOME_SOCIAL,
    SYSTEM_PROMPT,
    _keyword_overlap_ratio,
    _prediction_error,
)
from dau.foundation.semantic_similarity import (
    SENSOR_LABEL,
    get_sensor_label,
    semantic_similarity,
)

# ---------------------------------------------------------------------------
# Thresholds calibrated on all-MiniLM-L6-v2 (deterministic frozen weights)
# ---------------------------------------------------------------------------

EXACT_MATCH_PE_MAX: float = 0.02
# Paraphrase vs natural expected: MiniLM ~0.40 (was Jaccard 1.0)
PARAPHRASE_PE_MAX: float = 0.55
# Unrelated domain (extract vs rest) must surprise more than paraphrase
UNRELATED_PE_MIN: float = 0.60
# Jaccard on paraphrase must stay near-max — proves we left the old proxy
JACCARD_PARAPHRASE_PE_MIN: float = 0.99

PARAPHRASE_ACTUAL: str = (
    "I will gather the necessary supplies from the environmental cache."
)
KEYWORD_PARROT_ACTUAL: str = "social talk cooperate"
NEGATION_ACTUAL: str = "I refuse to cooperate or share with anyone."
UNRELATED_ACTUAL: str = "I rest and recover energy."


def test_sensor_label_is_minilm() -> None:
    """Empiric label documents the active semantic sensor."""

    assert get_sensor_label() == SENSOR_LABEL
    assert "MiniLM" in SENSOR_LABEL


def test_exact_match_near_zero_prediction_error() -> None:
    """Identical expected/actual → PE ≈ 0 under MiniLM."""

    pe = _prediction_error(EXPECTED_OUTCOME_RESOURCE, EXPECTED_OUTCOME_RESOURCE)
    assert pe <= EXACT_MATCH_PE_MAX


def test_paraphrase_pe_below_jaccard_era_and_below_unrelated() -> None:
    """Semantic paraphrase PE << old keyword-bag Jaccard 1.0 and < unrelated PE."""

    paraphrase_pe = _prediction_error(EXPECTED_OUTCOME_RESOURCE, PARAPHRASE_ACTUAL)
    unrelated_pe = _prediction_error(EXPECTED_OUTCOME_RESOURCE, UNRELATED_ACTUAL)
    # Legacy bag (pre-natural-language expectations) still yields Jaccard ≈ 1 PE
    legacy_bag = "resource extract take"
    jaccard_sim = _keyword_overlap_ratio(legacy_bag, PARAPHRASE_ACTUAL)
    jaccard_pe = 1.0 - jaccard_sim

    assert paraphrase_pe <= PARAPHRASE_PE_MAX
    assert unrelated_pe >= UNRELATED_PE_MIN
    assert paraphrase_pe < unrelated_pe
    assert jaccard_pe >= JACCARD_PARAPHRASE_PE_MIN


def test_keyword_bag_still_aligns_better_than_jaccard_zero() -> None:
    """Short keyword parrot vs natural social expected: sim > 0 (Jaccard may be low)."""

    sim = semantic_similarity(EXPECTED_OUTCOME_SOCIAL, KEYWORD_PARROT_ACTUAL)
    pe = _prediction_error(EXPECTED_OUTCOME_SOCIAL, KEYWORD_PARROT_ACTUAL)
    assert sim > 0.0
    assert pe < 1.0


def test_negation_remains_imperfect_under_minilm() -> None:
    """MiniLM negation weakness: refuse-cooperate still somewhat near cooperate.

    Documents remaining sensor limit — not a pass for polarity mastery.
    """

    pe = _prediction_error(EXPECTED_OUTCOME_SOCIAL, NEGATION_ACTUAL)
    # Soft bound: not a perfect 1.0 trauma, not a perfect 0 match
    assert 0.2 <= pe <= 0.9


def test_energy_expectation_distinct_from_resource_act() -> None:
    """Cross-domain mismatch stays high-surprise."""

    pe = _prediction_error(EXPECTED_OUTCOME_ENERGY, PARAPHRASE_ACTUAL)
    assert pe >= UNRELATED_PE_MIN


def test_system_prompt_still_lists_action_words() -> None:
    """Prompt still mentions action lexicon (legacy steer; sensor no longer Jaccard)."""

    prompt_lower = SYSTEM_PROMPT.lower()
    for keyword in ("resource", "extract", "cooperate"):
        assert keyword in prompt_lower
