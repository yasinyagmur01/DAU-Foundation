"""Unit tests for Layer 4 shared resource pool physics."""

from __future__ import annotations

import pytest

from dau.foundation.drift import DriftState
from dau.foundation.state import InternalState
from dau.generation.fitness import compute_fitness
from dau.society.environment import (
    COLLAPSE_EPSILON,
    EXTRACTION_KEY_AMOUNT,
    EXTRACTION_KEY_AGENT_ID,
    EXTRACTION_KEY_EVENT,
    POOL_INIT,
    POOL_MAX,
    POOL_MIN,
    POOL_REGEN_RATE,
    EnvironmentState,
    agent_delta_pool,
    apply_crisis_trauma,
    get_pool_ratio,
    realized_extraction_at,
    step_pool,
)
from dau.society.extraction import EXTRACTION_COOPERATE, EXTRACTION_DEFECT


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
    # regen(80)=82.4 → asked 90, pasture holds 82.4 → pool 0 ≤ 5.0 → collapsed
    next_env = step_pool(env, {"a": 90.0})

    assert next_env.pool == POOL_MIN
    assert next_env.collapsed is True
    assert next_env.event_counter == 1
    assert len(next_env.extraction_history) == 1
    assert next_env.extraction_history[0][EXTRACTION_KEY_AGENT_ID] == "a"
    # D-066: the ledger keeps what was DELIVERED, not what was announced. This
    # assertion said 90.0 until the metabolic loop was closed; recording an
    # un-harvested 7.6 would have fed the agent out of an empty pasture.
    assert next_env.extraction_history[0][EXTRACTION_KEY_AMOUNT] == pytest.approx(82.4)
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
    """pool_ratio=0.30 → DriftState unchanged."""

    initial = DriftState()
    result = apply_crisis_trauma(initial, pool_ratio=0.30)
    assert result is initial
    assert result.flags == {}
    assert result.magnitudes == {}


def test_pool_above_crisis_threshold_applies_no_crisis_trauma() -> None:
    """pool_ratio=0.50 → no trauma."""

    initial = DriftState()
    result = apply_crisis_trauma(initial, pool_ratio=0.50)
    assert result is initial
    assert result.flags == {}
    assert result.magnitudes == {}


def test_pool_below_crisis_threshold_applies_multiplied_trauma() -> None:
    """pool_ratio=0.20 → drift_state.flags['resource'] is True."""

    result = apply_crisis_trauma(DriftState(), pool_ratio=0.20)
    assert result.flags["resource"] is True


def test_crisis_trauma_sets_drift_state_flags() -> None:
    """pool_ratio=0.10 → flags['resource'] True and magnitudes['resource'] > 0."""

    result = apply_crisis_trauma(DriftState(), pool_ratio=0.10)
    assert result.flags["resource"] is True
    assert result.magnitudes["resource"] > 0.0


def test_crisis_trauma_flows_to_fitness_path() -> None:
    """Crisis drift lowers endogenous energy recovery → lower F_agent."""

    baseline_drift = DriftState()
    crisis_drift = apply_crisis_trauma(DriftState(), pool_ratio=0.10)
    state = InternalState(energy=1.0)

    f_baseline = compute_fitness(
        state.compute_endogenous_recovery_rate(baseline_drift),
        0.0,
        10,
        10,
    )
    f_crisis = compute_fitness(
        state.compute_endogenous_recovery_rate(crisis_drift),
        0.0,
        10,
        10,
    )
    assert f_crisis < f_baseline


# ---------------------------------------------------------------------------
# D-066 — an empty pasture feeds nobody
# ---------------------------------------------------------------------------

POOL_NEARLY_EMPTY: float = 1.0
HUGE_REQUEST: float = 50.0


def test_realized_extraction_is_capped_by_what_the_pool_holds() -> None:
    """Announced 50 from a nearly empty pool → only the stock is delivered."""

    env = EnvironmentState(pool=POOL_NEARLY_EMPTY)
    regenerated = POOL_NEARLY_EMPTY + POOL_REGEN_RATE * POOL_NEARLY_EMPTY * (
        1.0 - POOL_NEARLY_EMPTY / POOL_MAX
    )
    next_env = step_pool(env, {"a": HUGE_REQUEST})

    granted = next_env.extraction_history[0][EXTRACTION_KEY_AMOUNT]
    assert granted == pytest.approx(regenerated)
    assert granted < HUGE_REQUEST
    assert next_env.pool == pytest.approx(POOL_MIN)


def test_realized_extraction_shares_a_short_pool_in_proportion() -> None:
    """Two agents over-asking split what exists, in proportion to the ask."""

    env = EnvironmentState(pool=POOL_NEARLY_EMPTY)
    next_env = step_pool(env, {"a": 30.0, "b": 10.0})

    by_agent = {
        row[EXTRACTION_KEY_AGENT_ID]: row[EXTRACTION_KEY_AMOUNT]
        for row in next_env.extraction_history
    }
    assert by_agent["a"] == pytest.approx(3.0 * by_agent["b"])
    # Nothing is conjured: the pasture is emptied, not overdrawn.
    assert next_env.pool == pytest.approx(POOL_MIN)


def test_delta_pool_now_counts_harvests_not_announcements() -> None:
    """F_agent's pool term reads deliveries — the reason it was inert (D-060).

    Announcing 8.0 into a dead pool used to add 8.0 to agent_delta_pool for
    every event of the life, which is why the term spread only 0.7% across
    120 arms: it was measuring the decision class, not the commons.
    """

    env = EnvironmentState(pool=POOL_MIN)
    for _ in range(3):
        env = step_pool(env, {"a": EXTRACTION_DEFECT})

    assert agent_delta_pool(env, "a") == pytest.approx(0.0)


def test_realized_extraction_at_reads_one_event(
) -> None:
    """The metabolic loop needs this event's harvest, not the running total."""

    env = EnvironmentState()
    env = step_pool(env, {"a": EXTRACTION_COOPERATE})
    first = realized_extraction_at(env, "a", 1)
    env = step_pool(env, {"a": EXTRACTION_DEFECT})
    second = realized_extraction_at(env, "a", 2)

    assert first == pytest.approx(EXTRACTION_COOPERATE)
    assert second == pytest.approx(EXTRACTION_DEFECT)
    assert agent_delta_pool(env, "a") == pytest.approx(first + second)


# ---------------------------------------------------------------------------
# Carrying capacity scales with N (D-081, fixed after D-102)
# ---------------------------------------------------------------------------

CAPACITY_POPULATION: int = 4
PER_CAPITA_REQUEST: float = EXTRACTION_DEFECT
CAPACITY_STEPS: int = 12


def test_capacity_defaults_to_the_module_constant() -> None:
    """Every existing single-agent run must be untouched by the new field."""

    assert EnvironmentState().capacity == POOL_MAX
    assert get_pool_ratio(EnvironmentState(pool=POOL_MAX / 2)) == pytest.approx(0.5)


def test_per_capita_trajectory_is_identical_under_scaling() -> None:
    """⭐ D-081's whole point: N agents on an N-times pasture live the N=1 life.

    Same per-capita request, same per-capita stock, same capacity per head — so
    the ratio the crisis threshold and F_agent's pool term read must match step
    for step. Before the capacity field this diverged immediately: the
    population grazed a single-agent pasture and simply starved (D-102).
    """

    solo = EnvironmentState(pool=POOL_INIT)
    crowd = EnvironmentState(
        pool=POOL_INIT * CAPACITY_POPULATION,
        capacity=POOL_MAX * CAPACITY_POPULATION,
    )
    crowd_ids = [f"grazer-{index}" for index in range(CAPACITY_POPULATION)]

    for _ in range(CAPACITY_STEPS):
        solo = step_pool(solo, {"grazer-0": PER_CAPITA_REQUEST})
        crowd = step_pool(
            crowd, {agent_id: PER_CAPITA_REQUEST for agent_id in crowd_ids}
        )
        assert get_pool_ratio(crowd) == pytest.approx(get_pool_ratio(solo))
        assert crowd.collapsed is solo.collapsed


def test_capacity_survives_a_step() -> None:
    """step_pool returns a new state; losing capacity would silently shrink it."""

    scaled = EnvironmentState(
        pool=POOL_INIT * CAPACITY_POPULATION,
        capacity=POOL_MAX * CAPACITY_POPULATION,
    )
    stepped = step_pool(scaled, {"grazer-0": PER_CAPITA_REQUEST})

    assert stepped.capacity == POOL_MAX * CAPACITY_POPULATION
