"""Unit tests for ADIM 5 precision-weighted prediction error."""

from __future__ import annotations

import statistics
from unittest.mock import patch

import pytest

from dau.foundation.constraints import (
    PRECISION_EPSILON,
    PRECISION_MAX_WEIGHT,
    build_default_constraints,
)
from dau.foundation.graph import evaluator_node
from dau.foundation.semantic_similarity import (
    apply_precision_weighting,
    compute_precision_weight,
)
from dau.foundation.state import DAUAgentState, Event, InternalState

# Peak raw PE observed in a local Protocol C′ probe (10 events, seed 2001).
MEASURED_RAW_PE_PEAK: float = 0.81


def test_compute_precision_weight_stable_agent() -> None:
    """Low variance → precision weight > 1.0."""

    pe_vector = {"energy": 0.1, "social": 0.11, "resource": 0.09}
    assert compute_precision_weight(pe_vector) > 1.0


def test_unclamped_precision_falls_with_variance() -> None:
    """Design intent: higher variance → lower precision, before clamping."""

    stable_variance = statistics.variance([0.0, 0.0, 1.0])
    crisis_variance = statistics.variance([0.0, 1.0])
    assert crisis_variance > stable_variance
    stable_pi = 1.0 / (stable_variance + PRECISION_EPSILON)
    crisis_pi = 1.0 / (crisis_variance + PRECISION_EPSILON)
    assert crisis_pi < stable_pi


def test_clamp_binds_for_every_pe_vector_in_unit_interval() -> None:
    """PE is bounded, so the ceiling — not the variance — sets the gain.

    Sample variance of values in [0, 1] tops out at 0.5, so pi >= 2.0 always
    and PRECISION_MAX_WEIGHT is the value actually applied. The adaptive band
    below the ceiling is unreachable while PE stays bounded.
    """

    vectors = [
        {"energy": 0.0, "social": 1.0},
        {"energy": 0.0, "social": 0.0, "resource": 1.0},
        {"energy": 0.1, "social": 0.11, "resource": 0.09},
        {"energy": 0.5, "social": 0.5},
    ]
    for pe_vector in vectors:
        assert compute_precision_weight(pe_vector) == PRECISION_MAX_WEIGHT


def test_measured_pe_range_does_not_saturate() -> None:
    """Observed raw PE peaks near 0.81 — weighting must keep it below 1.0."""

    pe_vector = {"energy": 0.1, "social": 0.1, "resource": 0.1}
    assert apply_precision_weighting(MEASURED_RAW_PE_PEAK, pe_vector) < 1.0


def test_precision_weight_clamped_at_max() -> None:
    """Nearly identical values → extremely high raw pi → clamped."""

    pe_vector = {"energy": 0.100, "social": 0.101}
    result = compute_precision_weight(pe_vector)
    assert result == PRECISION_MAX_WEIGHT


def test_apply_precision_weighting_amplifies_stable() -> None:
    """Stable pe_vector amplifies raw PE, clamped to [0, 1]."""

    pe_vector = {"energy": 0.1, "social": 0.1, "resource": 0.1}
    raw_pe = 0.3
    result = apply_precision_weighting(raw_pe, pe_vector)
    assert result > raw_pe
    assert result <= 1.0


def test_apply_precision_weighting_clamps_at_one() -> None:
    """High raw PE × high precision cannot exceed 1.0."""

    pe_vector = {"energy": 0.1, "social": 0.1}
    raw_pe = 0.9
    result = apply_precision_weighting(raw_pe, pe_vector)
    assert result <= 1.0


def test_single_domain_returns_neutral_weight() -> None:
    """Single axis → not enough data → neutral weight."""

    pe_vector = {"energy": 0.5}
    result = compute_precision_weight(pe_vector)
    assert result == 1.0


def test_evaluator_node_does_not_crash_with_empty_pe_vector(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Precision weighting failure falls back to raw_pe; evaluator continues."""

    state = DAUAgentState(
        agent_id="agent_pe",
        environment=build_default_constraints(),
        internal_state=InternalState(),
        event_log=[
            Event(
                event_type="agent_decision",
                payload={
                    "decision": "I will extract resources carefully.",
                    "expected_outcome": "I will extract and take resources.",
                },
                timestamp=1,
            )
        ],
    )

    def _always_fail(raw_pe: float, pe_vector: dict[str, float]) -> float:
        raise RuntimeError("precision weighting failed")

    monkeypatch.setattr(
        "dau.foundation.graph.apply_precision_weighting",
        _always_fail,
    )
    with patch("dau.foundation.graph._prediction_error", return_value=0.4):
        result = evaluator_node(state)

    assert "internal_state" in result
    assert "delta_log" in result
    assert len(result["delta_log"]) == 1


def test_precision_epsilon_is_small() -> None:
    """Sanity: epsilon prevents division by zero without dominating variance."""

    assert PRECISION_EPSILON < 1e-3
