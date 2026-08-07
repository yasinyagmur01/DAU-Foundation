"""Unit tests for Layer 2 EmotionalWeight (somatic markers as functions)."""

from __future__ import annotations

import pytest

from dau.foundation.emotional_weight import (
    LOSS_DEFAULT,
    LOSS_ON_TRAUMA,
    MARKER_LOSS,
    MARKER_NOVELTY,
    MARKER_ORDER,
    MARKER_REWARD,
    MARKER_SOCIAL,
    MARKER_THREAT,
    PRIORITY_PROMPT_TEMPLATE,
    EmotionalWeight,
    apply_emotional_weight,
    apply_inherited_somatic_scale,
    compute_emotional_weight,
)
from dau.foundation.generation import (
    GENERATION_INHERITED_KEY,
    INHERITED_WARNING_KEY,
    RECORD_ID_KEY,
    SOMATIC_SCALE_KEY,
)
from dau.foundation.state import DeltaRecord, InternalState
from dau.generation.fitness import WARNING_SOMATIC_SCALE


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


def test_compute_emotional_weight_formulas() -> None:
    """Each marker follows the specified deterministic formula."""

    delta = _delta(0.5)
    state = InternalState(
        energy=0.8,
        resource_load=0.6,
        uncertainty_load=0.4,
        social_load=0.25,
    )
    ew = compute_emotional_weight(delta, state)
    markers = ew.somatic_markers

    assert markers[MARKER_THREAT] == pytest.approx(0.5 * 0.6)
    assert markers[MARKER_REWARD] == pytest.approx((1.0 - 0.5) * 0.8)
    assert markers[MARKER_NOVELTY] == pytest.approx(0.5 * 0.4)
    assert markers[MARKER_SOCIAL] == pytest.approx(0.25)
    assert markers[MARKER_LOSS] == LOSS_DEFAULT


def test_compute_emotional_weight_clamps_to_unit_interval() -> None:
    """Marker products that would exceed 1.0 are clamped."""

    # magnitude * resource_load would be 1.0 * 1.0 = 1.0 (at bound).
    # Use values that stay in-range for InternalState fields.
    delta = _delta(1.0)
    state = InternalState(
        energy=1.0,
        resource_load=1.0,
        uncertainty_load=1.0,
        social_load=1.0,
    )
    ew = compute_emotional_weight(delta, state)
    for marker in MARKER_ORDER:
        assert 0.0 <= ew.somatic_markers[marker] <= 1.0


def test_loss_marker_on_trauma() -> None:
    """Trauma-class deltas set loss to 1.0; non-trauma stays 0.0."""

    trauma = compute_emotional_weight(_delta(0.7), InternalState())
    deep = compute_emotional_weight(_delta(0.69), InternalState())
    assert trauma.somatic_markers[MARKER_LOSS] == LOSS_ON_TRAUMA
    assert deep.somatic_markers[MARKER_LOSS] == LOSS_DEFAULT


def test_compute_returns_all_five_markers() -> None:
    """EmotionalWeight always carries the full marker set."""

    ew = compute_emotional_weight(_delta(0.2), InternalState())
    assert set(ew.somatic_markers.keys()) == set(MARKER_ORDER)


def test_apply_emotional_weight_injects_top_marker_only() -> None:
    """Prompt bias is exactly the priority line for the highest marker."""

    ew = EmotionalWeight(
        somatic_markers={
            MARKER_THREAT: 0.1,
            MARKER_REWARD: 0.9,
            MARKER_NOVELTY: 0.2,
            MARKER_SOCIAL: 0.3,
            MARKER_LOSS: 0.0,
        }
    )
    prompt = "You are a living being."
    result = apply_emotional_weight(prompt, ew)
    bias = PRIORITY_PROMPT_TEMPLATE.format(top_marker=MARKER_REWARD)
    assert result == f"{prompt}\n{bias}"
    assert result.count("You are currently prioritizing:") == 1


def test_apply_emotional_weight_empty_prompt() -> None:
    """With an empty prompt, only the bias line is returned."""

    ew = EmotionalWeight(
        somatic_markers={
            MARKER_THREAT: 0.8,
            MARKER_REWARD: 0.1,
            MARKER_NOVELTY: 0.0,
            MARKER_SOCIAL: 0.0,
            MARKER_LOSS: 0.0,
        }
    )
    assert apply_emotional_weight("", ew) == PRIORITY_PROMPT_TEMPLATE.format(
        top_marker=MARKER_THREAT
    )


def test_apply_emotional_weight_tie_breaks_by_marker_order() -> None:
    """Equal top weights resolve to the earliest key in MARKER_ORDER."""

    ew = EmotionalWeight(
        somatic_markers={
            MARKER_THREAT: 0.5,
            MARKER_REWARD: 0.5,
            MARKER_NOVELTY: 0.5,
            MARKER_SOCIAL: 0.5,
            MARKER_LOSS: 0.5,
        }
    )
    result = apply_emotional_weight("Decide.", ew)
    assert result.endswith(
        PRIORITY_PROMPT_TEMPLATE.format(top_marker=MARKER_ORDER[0])
    )


def test_trauma_loss_dominates_when_others_low() -> None:
    """After trauma with low homeostatic loads, loss becomes the top marker."""

    state = InternalState(
        energy=0.0,
        resource_load=0.0,
        uncertainty_load=0.0,
        social_load=0.0,
    )
    ew = compute_emotional_weight(_delta(0.85), state)
    result = apply_emotional_weight("Act.", ew)
    assert result.endswith(
        PRIORITY_PROMPT_TEMPLATE.format(top_marker=MARKER_LOSS)
    )


def test_apply_inherited_somatic_scale_dampens_threat_on_negative_scale() -> None:
    """Negative ancestral somatic_scale dampens threat and loss markers."""

    ew = EmotionalWeight(
        somatic_markers={
            MARKER_THREAT: 0.8,
            MARKER_REWARD: 0.4,
            MARKER_NOVELTY: 0.3,
            MARKER_SOCIAL: 0.2,
            MARKER_LOSS: 1.0,
        }
    )
    context = [
        {
            RECORD_ID_KEY: "heir-warn",
            GENERATION_INHERITED_KEY: True,
            INHERITED_WARNING_KEY: True,
            SOMATIC_SCALE_KEY: -WARNING_SOMATIC_SCALE,
        }
    ]
    scaled = apply_inherited_somatic_scale(ew, context)
    factor = 1.0 - WARNING_SOMATIC_SCALE
    assert scaled.somatic_markers[MARKER_THREAT] == pytest.approx(0.8 * factor)
    assert scaled.somatic_markers[MARKER_LOSS] == pytest.approx(1.0 * factor)
    # Non-cautionary markers untouched.
    assert scaled.somatic_markers[MARKER_REWARD] == pytest.approx(0.4)


def test_apply_inherited_somatic_scale_noop_without_warnings() -> None:
    """Without inherited_warning entries, EmotionalWeight is unchanged."""

    ew = EmotionalWeight(
        somatic_markers={
            MARKER_THREAT: 0.5,
            MARKER_REWARD: 0.5,
            MARKER_NOVELTY: 0.5,
            MARKER_SOCIAL: 0.5,
            MARKER_LOSS: 0.0,
        }
    )
    context = [
        {RECORD_ID_KEY: "plain", GENERATION_INHERITED_KEY: True},
    ]
    scaled = apply_inherited_somatic_scale(ew, context)
    assert scaled.somatic_markers == ew.somatic_markers
