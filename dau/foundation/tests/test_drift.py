"""Unit tests for Layer 2 Drift Detection + Layer 3 Drift Healing."""

from __future__ import annotations

import pytest

from dau.foundation.drift import (
    DRIFT_BIAS_ABSENT,
    HEAL_RATE,
    HEAL_THRESHOLD,
    DriftState,
    get_drift_bias,
    heal_drift,
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
    """Repeated traumas accumulate with diminishing returns; flag stays set."""

    import math

    from dau.foundation.drift import TRAUMA_DECAY_BASE

    state = DriftState()
    state = update_drift(state, _delta(0.7, domain="social"))
    state = update_drift(state, _delta(0.85, domain="social"))
    first = 0.7
    expected = first + 0.85 * math.exp(-first / TRAUMA_DECAY_BASE)
    assert state.flags["social"] is True
    assert state.magnitudes["social"] == pytest.approx(expected)


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


def test_weak_positive_does_not_heal() -> None:
    """Below HEAL_THRESHOLD, even a non-trauma delta leaves drift untouched."""

    drifted = update_drift(DriftState(), _delta(0.9, domain="resource"))
    after = heal_drift(drifted, _delta(HEAL_THRESHOLD - 0.01, domain="resource"))
    assert after is drifted
    assert after.magnitudes["resource"] == pytest.approx(0.9)
    assert after.flags["resource"] is True


def test_strong_positive_unflagged_domain_no_effect() -> None:
    """Healing a domain with no drift flag is a no-op."""

    drifted = update_drift(DriftState(), _delta(0.9, domain="resource"))
    after = heal_drift(drifted, _delta(0.65, domain="social"))
    assert after is drifted
    assert "social" not in after.flags
    assert after.magnitudes["resource"] == pytest.approx(0.9)


def test_strong_positive_flagged_domain_partial_reduction() -> None:
    """One strong non-trauma experience reduces magnitude by magnitude * HEAL_RATE."""

    # 0.69 is DEEP (heal-eligible); 0.7 is TRAUMA and cannot heal.
    drifted = update_drift(DriftState(), _delta(0.9, domain="resource"))
    heal = _delta(0.69, domain="resource")
    after = heal_drift(drifted, heal)
    expected = 0.9 - 0.69 * HEAL_RATE
    assert after.flags["resource"] is True
    assert after.magnitudes["resource"] == pytest.approx(expected)
    assert get_drift_bias(after, "resource") == pytest.approx(expected)


def test_three_strong_positives_full_clear() -> None:
    """Three strong heals can fully clear a scar sized to 3 * heal * HEAL_RATE."""

    # 0.69 is the strongest non-trauma delta (TRAUMA starts at 0.7).
    # 3 × 0.69 × 0.3 = 0.621 — scar of that size clears on the third heal.
    heal_magnitude = 0.69
    scar_magnitude = 3 * heal_magnitude * HEAL_RATE
    drifted = DriftState(
        flags={"resource": True},
        magnitudes={"resource": scar_magnitude},
    )
    heal = _delta(heal_magnitude, domain="resource")
    after = heal_drift(drifted, heal)
    after = heal_drift(after, heal)
    after = heal_drift(after, heal)
    assert after.magnitudes["resource"] == pytest.approx(0.0)
    assert after.flags["resource"] is False
    assert get_drift_bias(after, "resource") == DRIFT_BIAS_ABSENT


def test_trauma_cannot_heal_trauma() -> None:
    """A trauma-class delta never reduces existing drift."""

    drifted = update_drift(DriftState(), _delta(0.8, domain="resource"))
    after = heal_drift(drifted, _delta(0.9, domain="resource"))
    assert after is drifted
    assert after.magnitudes["resource"] == pytest.approx(0.8)
    assert after.flags["resource"] is True


def test_trauma_accumulation_diminishing_returns():
    import math
    from dau.foundation.drift import TRAUMA_DECAY_BASE
    magnitude = 0.8
    accumulated = 0.0
    increments = []
    for _ in range(5):
        inc = magnitude * math.exp(-accumulated / TRAUMA_DECAY_BASE)
        accumulated += inc
        increments.append(inc)
    for i in range(1, 5):
        assert increments[i] < increments[i - 1]
    assert accumulated < 5 * magnitude
    assert increments[4] < increments[0] * 0.8
