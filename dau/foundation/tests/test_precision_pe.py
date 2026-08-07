"""Unit tests for ADIM 5 precision-weighted prediction error (rolling history)."""

from __future__ import annotations

import statistics
from unittest.mock import patch

import pytest

from dau.foundation.constraints import (
    PRECISION_EPSILON,
    PRECISION_HISTORY_WINDOW,
    PRECISION_MAX_WEIGHT,
    PRECISION_MIN_HISTORY,
    PRECISION_MIN_WEIGHT,
    PRECISION_VAR_REF,
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


def _pi_from_variance(variance: float) -> float:
    """Reference clamp for VAR_REF-scaled precision mapping."""

    pi_raw = 1.0 / (variance / PRECISION_VAR_REF + PRECISION_EPSILON)
    return max(PRECISION_MIN_WEIGHT, min(PRECISION_MAX_WEIGHT, pi_raw))


def test_precision_cold_start_neutral_until_min_history() -> None:
    """Fewer than PRECISION_MIN_HISTORY samples → neutral π=1.0."""

    assert compute_precision_weight([]) == 1.0
    assert compute_precision_weight([0.4] * (PRECISION_MIN_HISTORY - 1)) == 1.0


def test_precision_uses_rolling_history_not_pe_vector() -> None:
    """API accepts a raw-PE history list; pe_vector-style dicts are rejected."""

    history = [0.2, 0.25, 0.22, 0.28, 0.21]
    weight = compute_precision_weight(history)
    assert isinstance(weight, float)
    assert PRECISION_MIN_WEIGHT <= weight <= PRECISION_MAX_WEIGHT
    # Old pe_vector dict iterates as string keys → float() fails (not silent accept).
    with pytest.raises(ValueError):
        compute_precision_weight({"energy": 0.1, "social": 0.2})  # type: ignore[arg-type]


def test_precision_high_history_variance_lowers_weight() -> None:
    """High rolling variance → lower precision (crisis dampens)."""

    stable = [0.40, 0.41, 0.39, 0.40, 0.42, 0.38, 0.40, 0.41, 0.39, 0.40]
    crisis = [0.0, 1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 1.0]
    assert statistics.variance(crisis) > statistics.variance(stable)
    assert compute_precision_weight(crisis) < compute_precision_weight(stable)


def test_precision_low_history_variance_raises_weight() -> None:
    """Low rolling variance → higher precision (stable amplifies)."""

    stable = [0.50, 0.50, 0.50, 0.50, 0.50]
    # Spread enough that VAR_REF-scaled π falls below MAX but above MIN.
    mild = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
    assert compute_precision_weight(stable) == PRECISION_MAX_WEIGHT
    assert compute_precision_weight(mild) < PRECISION_MAX_WEIGHT
    assert compute_precision_weight(stable) > compute_precision_weight(mild)


def test_precision_weight_clamped_at_max_and_min() -> None:
    """Near-zero variance hits MAX; extreme bimodal history hits MIN."""

    near_zero_var = [0.5, 0.5, 0.5, 0.5000001, 0.5]
    assert compute_precision_weight(near_zero_var) == PRECISION_MAX_WEIGHT

    bimodal = [0.0, 1.0] * 5
    assert compute_precision_weight(bimodal) == PRECISION_MIN_WEIGHT


def test_apply_precision_measured_peak_saturation_budget() -> None:
    """Measured raw peak × MAX_WEIGHT must not force universal 1.0 saturation.

    With π=MAX, PE_w = min(0.81·1.2, 1.0) = 0.972 < 1.0 — headroom remains.
    """

    history = [0.5] * PRECISION_MIN_HISTORY
    # Force max gain path via stable history.
    assert compute_precision_weight(history) == PRECISION_MAX_WEIGHT
    weighted = apply_precision_weighting(MEASURED_RAW_PE_PEAK, history)
    assert weighted == pytest.approx(MEASURED_RAW_PE_PEAK * PRECISION_MAX_WEIGHT)
    assert weighted < 1.0


def test_evaluator_appends_raw_pe_to_pe_history(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Evaluator appends unweighted raw_pe after computing π from prior history."""

    prior = [0.2, 0.3]
    raw = 0.55
    state = DAUAgentState(
        agent_id="agent_pe_hist",
        environment=build_default_constraints(),
        internal_state=InternalState(),
        pe_history=list(prior),
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
    monkeypatch.setattr(
        "dau.foundation.graph._prediction_error",
        lambda expected, actual: raw,
    )
    result = evaluator_node(state)
    # History stores unweighted raw_pe, not precision-weighted PE_w.
    assert result["pe_history"] == prior + [raw]
    expected_weighted = apply_precision_weighting(raw, prior)
    assert expected_weighted == pytest.approx(raw * compute_precision_weight(prior))
    assert expected_weighted != pytest.approx(raw)


def test_pe_history_truncated_to_window(monkeypatch: pytest.MonkeyPatch) -> None:
    """Evaluator keeps at most PRECISION_HISTORY_WINDOW raw PE samples."""

    prior = [float(i) * 0.01 for i in range(PRECISION_HISTORY_WINDOW)]
    raw = 0.77
    state = DAUAgentState(
        agent_id="agent_pe_trunc",
        environment=build_default_constraints(),
        pe_history=list(prior),
        event_log=[
            Event(
                event_type="agent_decision",
                payload={
                    "decision": "act",
                    "expected_outcome": "expect",
                },
                timestamp=2,
            )
        ],
    )
    monkeypatch.setattr(
        "dau.foundation.graph._prediction_error",
        lambda expected, actual: raw,
    )
    result = evaluator_node(state)
    assert len(result["pe_history"]) == PRECISION_HISTORY_WINDOW
    assert result["pe_history"] == (prior + [raw])[-PRECISION_HISTORY_WINDOW:]


def test_apply_precision_weighting_clamps_at_one() -> None:
    """High raw PE × high precision cannot exceed 1.0."""

    history = [0.5, 0.5, 0.5]
    result = apply_precision_weighting(0.95, history)
    assert result <= 1.0


def test_precision_epsilon_is_small() -> None:
    """Sanity: epsilon prevents division by zero without dominating variance."""

    assert PRECISION_EPSILON < 1e-3


def test_evaluator_node_does_not_crash_when_precision_fails(
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

    def _always_fail(raw_pe: float, pe_history: list[float]) -> float:
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
    assert result["pe_history"] == [0.4]


def test_var_ref_mapping_matches_reference() -> None:
    """π matches 1/(var/VAR_REF+ε) clamped to [MIN, MAX]."""

    history = [0.1, 0.5, 0.9, 0.2, 0.8]
    expected = _pi_from_variance(statistics.variance(history))
    assert compute_precision_weight(history) == pytest.approx(expected)
