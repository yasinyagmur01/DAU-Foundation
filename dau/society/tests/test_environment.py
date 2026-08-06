"""Unit tests for Layer 4 shared resource pool physics."""

from __future__ import annotations

import pytest

from dau.foundation.drift import DriftState, get_drift_bias
from dau.generation.fitness import FITNESS_LOW_THRESHOLD, classify_fitness, compute_fitness
from dau.society.environment import (
    COLLAPSE_EPSILON,
    CRISIS_AFFECTED_DOMAIN,
    CRISIS_BASE_MAGNITUDE,
    CRISIS_TRAUMA_MULTIPLIER,
    EXTRACTION_KEY_AMOUNT,
    EXTRACTION_KEY_AGENT_ID,
    EXTRACTION_KEY_EVENT,
    POOL_CRISIS_THRESHOLD,
    POOL_INIT,
    POOL_MAX,
    POOL_MIN,
    POOL_REGEN_RATE,
    EnvironmentState,
    agent_delta_pool,
    apply_crisis_trauma,
    crisis_trauma_magnitude,
    get_pool_ratio,
    step_pool,
    step_pool_with_crisis,
)


def _regen(pool: float) -> float:
    """Closed-form logistic regeneration term for expected-value checks."""

    return POOL_REGEN_RATE * pool * (1.0 - pool / POOL_MAX)


def test_step_pool_normal_regeneration() -> None:
    """Zero extraction: pool grows by logistic regen only; history empty add."""

    env = EnvironmentState()
    next_env = step_pool(env, {})

    expected = POOL_INIT + _regen(POOL_INIT)
    assert next_env.pool == pytest.approx(expected)
    assert next_env.event_counter == 1
    assert next_env.collapsed is False
    assert next_env.extraction_history == []
    # Immutable: original unchanged
    assert env.pool == POOL_INIT
    assert env.event_counter == 0


def test_step_pool_over_extraction_causes_collapse() -> None:
    """Heavy harvest drives pool to floor and sets collapsed."""

    env = EnvironmentState()
    # regen(80)=2.4 → extract 90 → clamp(-7.6)=0 ≤ 5.0 → collapsed
    next_env = step_pool(env, {"a": 90.0})

    assert next_env.pool == POOL_MIN
    assert next_env.collapsed is True
    assert next_env.event_counter == 1
    assert len(next_env.extraction_history) == 1
    assert next_env.extraction_history[0][EXTRACTION_KEY_AGENT_ID] == "a"
    assert next_env.extraction_history[0][EXTRACTION_KEY_AMOUNT] == 90.0
    assert next_env.extraction_history[0][EXTRACTION_KEY_EVENT] == 1


def test_step_pool_clamps_at_pool_max_and_pool_min() -> None:
    """Pool never leaves [POOL_MIN, POOL_MAX]."""

    above = step_pool(EnvironmentState(pool=POOL_MAX + 25.0), {})
    assert above.pool == POOL_MAX

    below = step_pool(EnvironmentState(pool=POOL_INIT), {"drain": 10_000.0})
    assert below.pool == POOL_MIN


def test_get_pool_ratio_returns_correct_fraction() -> None:
    """Ratio is pool / POOL_MAX."""

    env = EnvironmentState(pool=40.0)
    assert get_pool_ratio(env) == pytest.approx(40.0 / POOL_MAX)
    assert get_pool_ratio(EnvironmentState(pool=POOL_MAX)) == pytest.approx(1.0)
    assert get_pool_ratio(EnvironmentState(pool=POOL_MIN)) == pytest.approx(0.0)


def test_agent_delta_pool_sums_across_multiple_steps() -> None:
    """Cumulative extraction for one agent ignores others."""

    env = EnvironmentState()
    env = step_pool(env, {"alice": 3.0, "bob": 5.0})
    env = step_pool(env, {"alice": 2.0})
    env = step_pool(env, {"bob": 1.0, "alice": 4.0})

    assert agent_delta_pool(env, "alice") == pytest.approx(9.0)
    assert agent_delta_pool(env, "bob") == pytest.approx(6.0)
    assert agent_delta_pool(env, "carol") == pytest.approx(0.0)
    assert env.event_counter == 3
    assert len(env.extraction_history) == 5


def test_collapsed_flag_at_collapse_epsilon_threshold() -> None:
    """collapsed iff P_next <= POOL_MAX * COLLAPSE_EPSILON (inclusive)."""

    threshold = POOL_MAX * COLLAPSE_EPSILON  # 5.0
    base = EnvironmentState(pool=POOL_INIT)
    regen = _regen(POOL_INIT)

    # Exact threshold → collapsed
    extract_at = POOL_INIT + regen - threshold
    at_edge = step_pool(base, {"x": extract_at})
    assert at_edge.pool == pytest.approx(threshold)
    assert at_edge.collapsed is True

    # Just above threshold → not collapsed
    extract_above = POOL_INIT + regen - (threshold + 0.01)
    above = step_pool(base, {"x": extract_above})
    assert above.pool == pytest.approx(threshold + 0.01)
    assert above.collapsed is False


def test_pool_at_crisis_threshold_applies_no_crisis_trauma() -> None:
    """pool_ratio >= POOL_CRISIS_THRESHOLD: DriftState unchanged."""

    pool = POOL_MAX * POOL_CRISIS_THRESHOLD  # exactly 0.30
    env = EnvironmentState(pool=pool, event_counter=3)
    assert get_pool_ratio(env) == pytest.approx(POOL_CRISIS_THRESHOLD)

    initial = DriftState()
    result = apply_crisis_trauma(env, initial)
    assert result is initial
    assert result.flags == {}
    assert result.magnitudes == {}
    assert get_drift_bias(result, CRISIS_AFFECTED_DOMAIN) == 0.0


def test_pool_above_crisis_threshold_applies_no_crisis_trauma() -> None:
    """Abundant pool: apply_crisis_trauma is a no-op."""

    env = EnvironmentState(pool=POOL_INIT)  # ratio 0.80
    assert get_pool_ratio(env) > POOL_CRISIS_THRESHOLD
    initial = DriftState()
    assert apply_crisis_trauma(env, initial) is initial


def test_pool_below_crisis_threshold_applies_multiplied_trauma() -> None:
    """pool_ratio < 0.30: trauma magnitude = base × CRISIS_TRAUMA_MULTIPLIER."""

    pool = POOL_MAX * POOL_CRISIS_THRESHOLD - 1.0  # ratio < 0.30
    env = EnvironmentState(pool=pool, event_counter=7)
    assert get_pool_ratio(env) < POOL_CRISIS_THRESHOLD

    expected_magnitude = crisis_trauma_magnitude(CRISIS_BASE_MAGNITUDE)
    assert expected_magnitude == pytest.approx(
        CRISIS_BASE_MAGNITUDE * CRISIS_TRAUMA_MULTIPLIER
    )

    result = apply_crisis_trauma(EnvironmentState(pool=pool, event_counter=7), DriftState())
    assert result.flags.get(CRISIS_AFFECTED_DOMAIN) is True
    assert result.magnitudes[CRISIS_AFFECTED_DOMAIN] == pytest.approx(expected_magnitude)
    assert get_drift_bias(result, CRISIS_AFFECTED_DOMAIN) == pytest.approx(
        expected_magnitude
    )


def test_crisis_trauma_sets_drift_state_flags() -> None:
    """Crisis path flags the resource domain via update_drift."""

    env = EnvironmentState(pool=POOL_MIN, event_counter=1)
    drifted = apply_crisis_trauma(env, DriftState())
    assert drifted.flags == {CRISIS_AFFECTED_DOMAIN: True}
    assert CRISIS_AFFECTED_DOMAIN in drifted.magnitudes
    assert drifted.magnitudes[CRISIS_AFFECTED_DOMAIN] > 0.0


def test_crisis_trauma_flows_to_fitness_path() -> None:
    """Crisis scar + heavy extraction: low F_agent band for cautionary transfer.

    Pool crisis sets drift flags; cumulative extraction (Δpool) punishes
    F_agent so classify_fitness lands in the low band used by generation.
    """

    env = EnvironmentState(pool=POOL_INIT)
    env, drifts = step_pool_with_crisis(
        env,
        {"alice": 70.0},
        {"alice": DriftState()},
    )
    assert get_pool_ratio(env) < POOL_CRISIS_THRESHOLD
    alice_drift = drifts["alice"]
    assert alice_drift.flags.get(CRISIS_AFFECTED_DOMAIN) is True

    delta_pool = agent_delta_pool(env, "alice")
    f_agent = compute_fitness(
        energy_final=0.2,
        delta_pool=delta_pool,
        t_survived=5,
        t_generation=10,
    )
    assert classify_fitness(f_agent) == "low"
    assert f_agent < FITNESS_LOW_THRESHOLD
    assert get_drift_bias(alice_drift, CRISIS_AFFECTED_DOMAIN) > 0.0
