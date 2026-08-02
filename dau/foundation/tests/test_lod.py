"""Unit tests for Cognitive Level-of-Detail (System 1 / System 2 switching)."""

from __future__ import annotations

import pytest

from dau.foundation.delta import DELTA_THRESHOLD_DEEP
from dau.foundation.lod import (
    DOMAIN_RESOURCE_LOAD,
    DOMAIN_SOCIAL_LOAD,
    DOMAIN_UNCERTAINTY_LOAD,
    NPC_ACTION_CONSERVE,
    NPC_ACTION_COOPERATE,
    NPC_ACTION_EXTRACT_MODERATE,
    NPC_ACTION_MAINTAIN,
    NPC_ACTION_OBSERVE,
    NPC_POOL_RATIO_CONSERVE,
    T_COGNITIVE_DEESCALATE,
    T_COGNITIVE_ESCALATE,
    T_COOLDOWN_STEPS,
    W_DELTA,
    W_DRIFT,
    W_SCARCITY,
    W_SOCIAL,
    CognitiveMode,
    LODState,
    compute_t_cognitive,
    npc_decision,
    should_run_llm,
    update_lod,
)


def test_compute_t_cognitive_formula() -> None:
    """T matches weighted formula and clamps to [0, 1]."""

    delta_magnitude = 0.7
    max_drift_bias = 0.4
    coordination_friction = 0.5
    pool_ratio = 0.8

    expected = (
        W_DELTA * (delta_magnitude / DELTA_THRESHOLD_DEEP)
        + W_DRIFT * max_drift_bias
        + W_SOCIAL * coordination_friction
        + W_SCARCITY * (1.0 - pool_ratio)
    )
    assert compute_t_cognitive(
        delta_magnitude,
        max_drift_bias,
        coordination_friction,
        pool_ratio,
    ) == pytest.approx(expected)

    # Saturating inputs → clamp to 1.0
    assert compute_t_cognitive(10.0, 1.0, 1.0, 0.0) == pytest.approx(1.0)
    # Zero load → 0.0 (scarcity term is zero when pool is full)
    assert compute_t_cognitive(0.0, 0.0, 0.0, 1.0) == pytest.approx(0.0)


def test_escalate_system_1_to_system_2_at_threshold() -> None:
    """SYSTEM_1 escalates immediately when t_cognitive >= escalate threshold."""

    lod = LODState()
    assert lod.mode == CognitiveMode.SYSTEM_1

    below = update_lod(lod, T_COGNITIVE_ESCALATE - 0.01, now_counter=3)
    assert below.mode == CognitiveMode.SYSTEM_1
    assert below.t_cognitive == pytest.approx(T_COGNITIVE_ESCALATE - 0.01)
    assert below.last_escalation_event == 0

    escalated = update_lod(lod, T_COGNITIVE_ESCALATE, now_counter=7)
    assert escalated.mode == CognitiveMode.SYSTEM_2
    assert escalated.consecutive_low_steps == 0
    assert escalated.last_escalation_event == 7
    assert escalated.t_cognitive == pytest.approx(T_COGNITIVE_ESCALATE)
    # Input left untouched (immutable)
    assert lod.mode == CognitiveMode.SYSTEM_1


def test_system_2_does_not_deescalate_immediately() -> None:
    """A single low step only increments the cooldown counter."""

    lod = LODState(
        mode=CognitiveMode.SYSTEM_2,
        t_cognitive=0.9,
        consecutive_low_steps=0,
        last_escalation_event=1,
    )
    updated = update_lod(lod, T_COGNITIVE_DEESCALATE, now_counter=10)
    assert updated.mode == CognitiveMode.SYSTEM_2
    assert updated.consecutive_low_steps == 1

    # Even after T_COOLDOWN_STEPS - 1 lows, still System 2
    for step in range(1, T_COOLDOWN_STEPS):
        lod = update_lod(
            LODState(
                mode=CognitiveMode.SYSTEM_2,
                consecutive_low_steps=step - 1,
                last_escalation_event=1,
            ),
            T_COGNITIVE_DEESCALATE,
            now_counter=10 + step,
        )
        assert lod.mode == CognitiveMode.SYSTEM_2
        assert lod.consecutive_low_steps == step


def test_deescalate_after_consecutive_low_steps() -> None:
    """SYSTEM_2 → SYSTEM_1 only after T_COOLDOWN_STEPS consecutive lows."""

    lod = LODState(
        mode=CognitiveMode.SYSTEM_2,
        consecutive_low_steps=T_COOLDOWN_STEPS - 1,
        last_escalation_event=2,
    )
    deescalated = update_lod(lod, T_COGNITIVE_DEESCALATE, now_counter=20)
    assert deescalated.mode == CognitiveMode.SYSTEM_1
    assert deescalated.consecutive_low_steps == 0
    assert deescalated.last_escalation_event == 2  # preserved


def test_cooldown_counter_resets_when_t_rises() -> None:
    """During SYSTEM_2, t_cognitive above deescalate threshold clears the counter."""

    lod = LODState(
        mode=CognitiveMode.SYSTEM_2,
        consecutive_low_steps=3,
        last_escalation_event=5,
    )
    reset = update_lod(
        lod,
        T_COGNITIVE_DEESCALATE + 0.01,
        now_counter=15,
    )
    assert reset.mode == CognitiveMode.SYSTEM_2
    assert reset.consecutive_low_steps == 0


def test_npc_decision_heuristics() -> None:
    """System 1 NPC actions follow pool scarcity then dominant domain."""

    assert (
        npc_decision("a1", DOMAIN_RESOURCE_LOAD, NPC_POOL_RATIO_CONSERVE - 0.01)
        == NPC_ACTION_CONSERVE
    )
    assert (
        npc_decision("a1", DOMAIN_RESOURCE_LOAD, 0.9)
        == NPC_ACTION_EXTRACT_MODERATE
    )
    assert (
        npc_decision("a1", DOMAIN_SOCIAL_LOAD, 0.9) == NPC_ACTION_COOPERATE
    )
    assert (
        npc_decision("a1", DOMAIN_UNCERTAINTY_LOAD, 0.9) == NPC_ACTION_OBSERVE
    )
    assert npc_decision("a1", "energy", 0.9) == NPC_ACTION_MAINTAIN
    # Scarcity overrides domain
    assert (
        npc_decision("a1", DOMAIN_SOCIAL_LOAD, NPC_POOL_RATIO_CONSERVE - 0.01)
        == NPC_ACTION_CONSERVE
    )


def test_should_run_llm_per_mode() -> None:
    """LLM runs only in SYSTEM_2."""

    assert should_run_llm(LODState(mode=CognitiveMode.SYSTEM_1)) is False
    assert should_run_llm(LODState(mode=CognitiveMode.SYSTEM_2)) is True
