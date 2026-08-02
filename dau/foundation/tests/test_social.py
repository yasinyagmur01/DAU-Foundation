"""Unit tests for Layer 4 social_load (cooperation vs coordination)."""

from __future__ import annotations

import math

import pytest

from dau.foundation.social import (
    ENTROPY_WINDOW,
    MARKOV_WINDOW,
    OUTCOME_COORDINATE,
    OUTCOME_COOPERATE,
    OUTCOME_DEADLOCK,
    OUTCOME_DEFECT,
    SOCIAL_W1,
    SOCIAL_W2,
    TRUST_DECAY,
    TRUST_INIT,
    TRUST_RECOVERY,
    InteractionRecord,
    SocialState,
    compute_coordination_friction,
    compute_cooperation_stress,
    compute_markov_expectation,
    compute_social_load,
    record_interaction,
    shannon_entropy,
)


def _record(
    agent_id: str,
    opponent_id: str,
    outcome: str,
    event_counter: int,
) -> InteractionRecord:
    """Build a directed InteractionRecord for deterministic tests."""

    return InteractionRecord(
        agent_id=agent_id,
        opponent_id=opponent_id,
        outcome=outcome,
        event_counter=event_counter,
    )


def test_cooperation_stress_zero_with_no_defections() -> None:
    """No defections and full trust → cooperation_stress is 0."""

    social = SocialState()
    social = record_interaction(
        social, _record("a", "b", OUTCOME_COOPERATE, 1)
    )
    social = record_interaction(
        social, _record("a", "b", OUTCOME_COORDINATE, 2)
    )
    assert compute_cooperation_stress(social, "a", "b") == pytest.approx(0.0)


def test_cooperation_stress_increases_with_defections_and_trust_decay() -> None:
    """Defects raise defect rate and decay trust → stress rises."""

    social = SocialState()
    social = record_interaction(social, _record("a", "b", OUTCOME_DEFECT, 1))
    stress_one = compute_cooperation_stress(social, "a", "b")
    # defect_rate=1, trust=1-0.1=0.9 → stress = 1 * 0.1 = 0.1
    assert stress_one == pytest.approx(1.0 * (1.0 - (TRUST_INIT - TRUST_DECAY)))

    social = record_interaction(social, _record("a", "b", OUTCOME_DEFECT, 2))
    stress_two = compute_cooperation_stress(social, "a", "b")
    trust_after_two = TRUST_INIT - 2 * TRUST_DECAY
    assert stress_two == pytest.approx(1.0 * (1.0 - trust_after_two))
    assert stress_two > stress_one


def test_coordination_friction_zero_without_deadlock() -> None:
    """Entropy alone is not enough — friction stays 0 unless last is deadlock."""

    social = SocialState()
    social = record_interaction(
        social, _record("a", "b", OUTCOME_COOPERATE, 1)
    )
    social = record_interaction(
        social, _record("a", "b", OUTCOME_COORDINATE, 2)
    )
    social = record_interaction(social, _record("a", "b", OUTCOME_DEFECT, 3))
    assert compute_coordination_friction(social, "a", "b") == pytest.approx(0.0)


def test_coordination_friction_nonzero_with_deadlock_and_entropy() -> None:
    """Mixed outcomes ending in deadlock → friction = clamp(H, 0, 1)."""

    social = SocialState()
    social = record_interaction(
        social, _record("a", "b", OUTCOME_COOPERATE, 1)
    )
    social = record_interaction(
        social, _record("a", "b", OUTCOME_DEADLOCK, 2)
    )
    outcomes = [OUTCOME_COOPERATE, OUTCOME_DEADLOCK]
    raw_entropy = shannon_entropy(outcomes)
    assert raw_entropy > 0.0
    # Two equiprobable outcomes → H = 1.0; clamp is a no-op at the bound.
    assert compute_coordination_friction(social, "a", "b") == pytest.approx(
        min(1.0, raw_entropy)
    )


def test_social_load_composite_correct() -> None:
    """social_load = W1 * cooperation_stress + W2 * coordination_friction."""

    social = SocialState()
    social = record_interaction(social, _record("a", "b", OUTCOME_DEFECT, 1))
    social = record_interaction(
        social, _record("a", "b", OUTCOME_COOPERATE, 2)
    )
    social = record_interaction(
        social, _record("a", "b", OUTCOME_DEADLOCK, 3)
    )

    coop = compute_cooperation_stress(social, "a", "b")
    coord = compute_coordination_friction(social, "a", "b")
    expected = SOCIAL_W1 * coop + SOCIAL_W2 * coord
    assert compute_social_load(social, "a", "b") == pytest.approx(expected)
    assert 0.0 <= compute_social_load(social, "a", "b") <= 1.0


def test_markov_expectation_correct_probability() -> None:
    """P(cooperate) counts cooperate+coordinate over opponent's recent acts."""

    social = SocialState()
    # Opponent "b" acts toward "a"
    social = record_interaction(
        social, _record("b", "a", OUTCOME_COOPERATE, 1)
    )
    social = record_interaction(
        social, _record("b", "a", OUTCOME_COORDINATE, 2)
    )
    social = record_interaction(social, _record("b", "a", OUTCOME_DEFECT, 3))
    social = record_interaction(
        social, _record("b", "a", OUTCOME_DEADLOCK, 4)
    )
    # Noise from the reverse direction must not count
    social = record_interaction(
        social, _record("a", "b", OUTCOME_COOPERATE, 5)
    )

    assert compute_markov_expectation(social, "a", "b") == pytest.approx(
        2.0 / 4.0
    )


def test_record_interaction_trust_updates_bidirectional() -> None:
    """Defect/cooperate adjust trust on both directed keys of the dyad."""

    social = SocialState()
    social = record_interaction(social, _record("a", "b", OUTCOME_DEFECT, 1))
    assert social.bilateral_trust["a:b"] == pytest.approx(
        TRUST_INIT - TRUST_DECAY
    )
    assert social.bilateral_trust["b:a"] == pytest.approx(
        TRUST_INIT - TRUST_DECAY
    )

    social = record_interaction(
        social, _record("a", "b", OUTCOME_COOPERATE, 2)
    )
    assert social.bilateral_trust["a:b"] == pytest.approx(
        TRUST_INIT - TRUST_DECAY + TRUST_RECOVERY
    )
    assert social.bilateral_trust["b:a"] == pytest.approx(
        TRUST_INIT - TRUST_DECAY + TRUST_RECOVERY
    )


def test_shannon_entropy_uniform_and_empty() -> None:
    """Empty → 0; two equally likely outcomes → 1 bit."""

    assert shannon_entropy([]) == pytest.approx(0.0)
    assert shannon_entropy([OUTCOME_COOPERATE, OUTCOME_DEFECT]) == pytest.approx(
        1.0
    )
    assert shannon_entropy(
        [OUTCOME_COOPERATE, OUTCOME_COOPERATE]
    ) == pytest.approx(0.0)
    # Sanity: formula matches -sum p log2 p
    outcomes = [OUTCOME_COOPERATE, OUTCOME_DEFECT, OUTCOME_DEADLOCK]
    p = 1.0 / 3.0
    expected = -3.0 * (p * math.log2(p))
    assert shannon_entropy(outcomes) == pytest.approx(expected)


def test_markov_window_truncates_to_last_n() -> None:
    """Only the last MARKOV_WINDOW opponent actions enter the probability."""

    social = SocialState()
    # Fill with defections, then MARKOV_WINDOW cooperates
    for i in range(MARKOV_WINDOW):
        social = record_interaction(
            social, _record("b", "a", OUTCOME_DEFECT, i + 1)
        )
    for i in range(MARKOV_WINDOW):
        social = record_interaction(
            social,
            _record("b", "a", OUTCOME_COOPERATE, MARKOV_WINDOW + i + 1),
        )
    assert compute_markov_expectation(social, "a", "b") == pytest.approx(1.0)


def test_entropy_window_uses_last_n_only() -> None:
    """Coordination friction entropy is limited to ENTROPY_WINDOW."""

    social = SocialState()
    # Old uniform mix, then ENTROPY_WINDOW identical deadlocks
    for i in range(ENTROPY_WINDOW):
        outcome = OUTCOME_COOPERATE if i % 2 == 0 else OUTCOME_DEFECT
        social = record_interaction(
            social, _record("a", "b", outcome, i + 1)
        )
    for i in range(ENTROPY_WINDOW):
        social = record_interaction(
            social,
            _record("a", "b", OUTCOME_DEADLOCK, ENTROPY_WINDOW + i + 1),
        )
    # Last window is all deadlock → H = 0 → friction = 0
    assert compute_coordination_friction(social, "a", "b") == pytest.approx(0.0)
