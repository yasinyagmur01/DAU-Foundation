"""Unit tests for Layer 2 Drift Detection."""

from __future__ import annotations

import pytest

from dau.foundation.drift import (
    DRIFT_BIAS_ABSENT,
    DriftState,
    get_drift_bias,
    update_drift,
)
from dau.foundation.state import DeltaRecord


def _delta(magnitude: float, domain: str = "resource") -> DeltaRecord:
    """Build a DeltaRecord with an explicit magnitude for deterministic tests."""

    snap = {
        "energy": 1.0,
        "resource_load": 0.0,
        "uncertainty_load": 0.0,
        "social_load": 0.0,
    }
    return DeltaRecord(
        timestamp=1,
        magnitude=magnitude,
        affected_domain=domain,  # type: ignore[arg-type]
        snapshot_before=snap,
        snapshot_after=dict(snap),
    )


def test_no_trauma_leaves_drift_unchanged() -> None:
    """Non-trauma deltas do not set flags or accumulate magnitude."""

    initial = DriftState()
    result = update_drift(initial, _delta(0.69))
    assert result is initial
    assert result.flags == {}
    assert result.magnitudes == {}
    assert get_drift_bias(result, "resource") == DRIFT_BIAS_ABSENT


def test_trauma_sets_flag_and_magnitude() -> None:
    """Trauma-class delta flags the affected domain and records magnitude."""

    result = update_drift(DriftState(), _delta(0.7, domain="resource"))
    assert result.flags["resource"] is True
    assert result.magnitudes["resource"] == pytest.approx(0.7)
    assert get_drift_bias(result, "resource") == pytest.approx(0.7)


def test_magnitude_accumulates_across_multiple_traumas() -> None:
    """Repeated traumas in the same domain add magnitudes; flag stays set."""

    state = DriftState()
    state = update_drift(state, _delta(0.7, domain="social"))
    state = update_drift(state, _delta(0.85, domain="social"))
    assert state.flags["social"] is True
    assert state.magnitudes["social"] == pytest.approx(0.7 + 0.85)


def test_get_drift_bias_flagged_vs_unflagged() -> None:
    """Bias is magnitude when flagged; absent (0.0) for untouched domains."""

    state = update_drift(DriftState(), _delta(0.8, domain="uncertainty"))
    assert get_drift_bias(state, "uncertainty") == pytest.approx(0.8)
    assert get_drift_bias(state, "energy") == DRIFT_BIAS_ABSENT
    assert get_drift_bias(state, "resource") == DRIFT_BIAS_ABSENT


def test_non_trauma_after_drift_preserves_existing() -> None:
    """A later non-trauma event must not clear or alter existing drift."""

    drifted = update_drift(DriftState(), _delta(0.75, domain="energy"))
    after = update_drift(drifted, _delta(0.3, domain="energy"))
    assert after is drifted
    assert after.flags["energy"] is True
    assert after.magnitudes["energy"] == pytest.approx(0.75)
