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
    POOL_CRISIS_THRESHOLD,
    POOL_MIN,
    POOL_REGEN_RATE,
    EXTRACTION_LIMIT_RATIO,
    EnvironmentState,
    harvest_ceiling,
    realized_extractions,
    realized_extractions_sequential,
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


def test_one_heavy_harvest_can_no_longer_empty_the_pasture() -> None:
    """⭐ D-163 turned this test around, and the reversal is the point.

    It used to read "heavy harvest drives pool to floor and sets collapsed":
    one agent announced 90.0 and walked off with the entire regenerated stock,
    leaving zero. That single-step wipe-out is exactly the binary regime the
    ceiling exists to remove — with it, no announcement can take more than
    EXTRACTION_LIMIT_RATIO of the per-capita stock, so the pasture thins
    instead of dying and a short-fall exists to be shared.

    ⚠ Collapse is NOT gone; it is reached over many events instead of one, and
    the equilibrium is COLLAPSE_EPSILON by construction (see the constant).
    """

    env = EnvironmentState()
    regenerated = POOL_INIT + _regen(POOL_INIT)
    next_env = step_pool(env, {"a": 90.0})

    assert next_env.collapsed is False, "one harvest still wiped out the commons"
    assert next_env.pool > POOL_MIN
    assert next_env.event_counter == 1
    assert len(next_env.extraction_history) == 1
    assert next_env.extraction_history[0][EXTRACTION_KEY_AGENT_ID] == "a"
    # D-066: the ledger keeps what was DELIVERED. D-163: what is deliverable is
    # now the ceiling, read from the same helper the physics uses (§2.8).
    assert next_env.extraction_history[0][EXTRACTION_KEY_AMOUNT] == pytest.approx(
        harvest_ceiling(regenerated, 1)
    )
    assert next_env.extraction_history[0][EXTRACTION_KEY_EVENT] == 1


def test_step_pool_clamps_at_pool_max_and_pool_min() -> None:
    """Pool never leaves [POOL_MIN, POOL_MAX]."""

    above = step_pool(EnvironmentState(pool=POOL_MAX + 25.0), {})
    assert above.pool == POOL_MAX

    # D-163: the lower clamp can no longer be reached by asking for more — the
    # ceiling caps the draw — so it is exercised where it still bites: an empty
    # pasture regenerates nothing and must stay at the floor rather than drift
    # negative through the extraction arithmetic.
    below = step_pool(EnvironmentState(pool=POOL_MIN), {"drain": 10_000.0})
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

    # D-163: the flag can no longer be driven across the line by a single huge
    # request, because the ceiling caps the draw. The inclusive `<=` is what
    # this test protects, so the landing has to stay EXACT — it is reached by
    # harvesting away precisely this round's regrowth from a pasture already at
    # the floor. The draw is small enough to clear the ceiling, which is
    # asserted rather than assumed.
    regrowth = _regen(threshold)
    assert regrowth < harvest_ceiling(threshold + regrowth, 1), (
        "the fixture's draw is itself capped, so it can no longer land exactly"
    )

    at_edge = step_pool(EnvironmentState(pool=threshold), {"x": regrowth})
    assert at_edge.pool == pytest.approx(threshold)
    assert at_edge.collapsed is True

    above = step_pool(EnvironmentState(pool=threshold), {"x": regrowth - 0.01})
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


def test_realized_extraction_is_capped_by_the_stock_proportional_ceiling() -> None:
    """Announced 50 from a nearly empty pool → the ceiling decides, not the ask.

    ⚠ D-163 moved the binding constraint. It used to be "the pasture holds only
    so much"; now the ceiling bites first and always, which is what makes the
    squeeze graduated rather than a single cliff.
    """

    env = EnvironmentState(pool=POOL_NEARLY_EMPTY)
    regenerated = POOL_NEARLY_EMPTY + _regen(POOL_NEARLY_EMPTY)
    next_env = step_pool(env, {"a": HUGE_REQUEST})

    granted = next_env.extraction_history[0][EXTRACTION_KEY_AMOUNT]
    assert granted == pytest.approx(harvest_ceiling(regenerated, 1))
    assert granted < HUGE_REQUEST
    assert granted < regenerated, "the ceiling must bind before the stock does"
    assert next_env.pool > POOL_MIN


def test_the_ceiling_makes_the_pro_rata_shortfall_unreachable() -> None:
    """⛔ D-163 — an unreachable branch, declared rather than left silent.

    The pro-rata split used to be the whole shortfall story: two agents
    over-asking shared what existed 3:1. With the ceiling it can never run, and
    the reason is arithmetic rather than empirical: every agent is capped at
    EXTRACTION_LIMIT_RATIO of the per-capita stock, so the capped total is at
    most EXTRACTION_LIMIT_RATIO of what is available — and that ratio is well
    below 1. The `total_requested > available` branch in realized_extractions
    is therefore dead code TODAY.

    It is kept, not deleted, because it is the guard that stops an overdraw if
    the ceiling is ever raised or removed. What is not acceptable is leaving
    that unreachability undiscovered — a gate everyone believes is running
    while it never opens is the exact failure D-088 dug out of the transfer
    path. This test pins the fact so a future change has to face it.
    """

    env = EnvironmentState(pool=POOL_NEARLY_EMPTY)
    next_env = step_pool(env, {"a": 30.0, "b": 10.0})

    by_agent = {
        row[EXTRACTION_KEY_AGENT_ID]: row[EXTRACTION_KEY_AMOUNT]
        for row in next_env.extraction_history
    }
    regenerated = POOL_NEARLY_EMPTY + _regen(POOL_NEARLY_EMPTY)
    ceiling = harvest_ceiling(regenerated, 2)
    # Both asked far above the ceiling, so both leave with exactly the ceiling:
    # the 3:1 ask is invisible once neither can be served in full.
    assert by_agent["a"] == pytest.approx(ceiling)
    assert by_agent["b"] == pytest.approx(ceiling)
    assert sum(by_agent.values()) < regenerated, (
        "capped demand must stay under what is available, or the pro-rata "
        "branch is reachable after all and this test is the wrong shape"
    )


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


# ---------------------------------------------------------------------------
# Sequential service — P0-① as decided (D-103 measured why it is needed)
# ---------------------------------------------------------------------------

SEQUENTIAL_STOCK: float = 10.0
SEQUENTIAL_REQUEST: float = 8.0
# D-163: a stock large enough that the ceiling clears the biggest ask in these
# fixtures, so "there is enough" describes the ceiling and not only the stock.
SEQUENTIAL_ABUNDANT_STOCK: float = 60.0


def test_sequential_service_favours_the_earlier_position() -> None:
    """⭐ The half of P0-① that breaks symmetry: order decides who goes short.

    Under the proportional split identical requests get identical shares, so
    identical agents stay identical forever — the D-103 pilot measured exactly
    that, with eight bit-identical founders and Cov(w, z) zero by construction.
    """

    requests = {"first": SEQUENTIAL_REQUEST, "second": SEQUENTIAL_REQUEST}
    granted = realized_extractions_sequential(SEQUENTIAL_STOCK, requests)

    # ⭐ D-163 made this claim STRONGER, not weaker. It used to hold only when
    # the stock ran out mid-round (first got 8.0, second got the 2.0 left).
    # Now the ceiling is recomputed from what is still there, so the earlier
    # position is favoured on EVERY round — which is the whole reason the
    # layer exists: identical agents need a gradient before the collapse, not
    # only at it.
    first_ceiling = harvest_ceiling(SEQUENTIAL_STOCK, len(requests))
    assert granted["first"] == pytest.approx(first_ceiling)
    assert granted["second"] == pytest.approx(
        harvest_ceiling(SEQUENTIAL_STOCK - granted["first"], len(requests))
    )
    assert granted["first"] > granted["second"]
    assert sum(granted.values()) < SEQUENTIAL_STOCK, "the pasture was emptied"


def test_sequential_service_never_overdraws_the_stock() -> None:
    """The pasture cannot give what it does not have, in any order."""

    requests = {f"a{i}": SEQUENTIAL_REQUEST for i in range(4)}
    granted = realized_extractions_sequential(SEQUENTIAL_STOCK, requests)

    # D-163: the invariant is "never more than the stock", and it used to be
    # tested at equality because the herd drained the pasture exactly. The
    # ceiling now leaves something standing, which is the point — but the
    # no-overdraw guarantee is what this test protects and it still holds.
    assert sum(granted.values()) <= SEQUENTIAL_STOCK + 1e-9
    assert sum(granted.values()) < SEQUENTIAL_STOCK
    assert all(value >= 0.0 for value in granted.values())
    # Strictly decreasing: each grazer faces a thinner stock than the last.
    order = list(granted.values())
    assert all(a > b for a, b in zip(order, order[1:]))


def test_sequential_and_proportional_agree_when_there_is_enough() -> None:
    """Order only matters under scarcity; a full pasture serves everyone alike."""

    # D-163: "enough" now means enough for the CEILING, not just for the stock.
    # SEQUENTIAL_STOCK would cap both asks and the two paths would disagree by
    # design, so the stock is raised until neither ask is capped — which is
    # exactly the regime this test was written to describe.
    requests = {"first": 2.0, "second": 3.0}
    stock = SEQUENTIAL_ABUNDANT_STOCK
    assert harvest_ceiling(stock, len(requests)) > max(requests.values()), (
        "fixture no longer describes an unconstrained round"
    )
    assert realized_extractions_sequential(stock, requests) == realized_extractions(
        stock, requests
    )


def test_step_pool_sequential_flag_changes_who_gets_served() -> None:
    """The flag has to reach step_pool, not just exist on the helper."""

    env = EnvironmentState(pool=SEQUENTIAL_STOCK, capacity=POOL_MAX)
    requests = {"first": SEQUENTIAL_REQUEST, "second": SEQUENTIAL_REQUEST}
    ordered = step_pool(env, requests, sequential=True)
    shared = step_pool(env, requests, sequential=False)

    got_ordered = {row["agent_id"]: row["amount"] for row in ordered.extraction_history}
    got_shared = {row["agent_id"]: row["amount"] for row in shared.extraction_history}
    assert got_ordered["first"] > got_ordered["second"]
    assert got_shared["first"] == pytest.approx(got_shared["second"])


# ---------------------------------------------------------------------------
# Layer 1 — the stock-proportional ceiling (D-162 / D-163)
# ---------------------------------------------------------------------------

CEILING_STOCK_HIGH: float = 640.0
CEILING_STOCK_LOW: float = 200.0
CEILING_HERD: int = 8


def test_the_ratio_is_the_expression_not_a_number() -> None:
    """⛔ D-163. The value is a derivation, and it has to stay one.

    A hard-coded 0.1425 would read as a tuned constant the moment anyone looked
    at it, and §2.7 does not allow a fitted number here. Written as
    POOL_REGEN_RATE × (1 − COLLAPSE_EPSILON), it says what it means: the
    ceiling whose equilibrium sits exactly on the floor the code already calls
    collapse.
    """

    assert EXTRACTION_LIMIT_RATIO == pytest.approx(
        POOL_REGEN_RATE * (1.0 - COLLAPSE_EPSILON)
    )
    # ⚠ K5 caught the first version of this test empty: 0.1425 satisfies the
    # equality above just as well as the expression does, so the assertion
    # said nothing about the thing it was named after. The property that
    # actually matters is that the SOURCE derives it — a literal would not
    # follow POOL_REGEN_RATE or COLLAPSE_EPSILON if either were ever revised,
    # and the derivation would quietly become a fitted number.
    import inspect
    import re

    import dau.society.environment as environment_module

    assignment = re.search(
        r"^EXTRACTION_LIMIT_RATIO\s*:\s*float\s*=\s*(.+)$",
        inspect.getsource(environment_module),
        re.MULTILINE,
    )
    assert assignment is not None, "the constant is no longer a module-level literal"
    written = assignment.group(1)
    assert "POOL_REGEN_RATE" in written and "COLLAPSE_EPSILON" in written, (
        f"the ratio is written as a bare value, not a derivation: {written!r}"
    )


def test_the_equilibrium_lands_on_the_collapse_floor() -> None:
    """⭐ D-163 — the closed form the ratio was chosen from.

    A ceiling makes the stock settle where the herd's draw equals the regrowth:
    r·p = REGEN·p·(1 − p/capacity), so p/capacity = 1 − r/REGEN. Choosing the
    ratio IS choosing where the commons comes to rest, and D-162 missed that —
    its ratio parked the equilibrium at 0.333, above the crisis floor, which
    would have deleted a channel that fires in 127 of 192 real lives.
    """

    equilibrium = 1.0 - EXTRACTION_LIMIT_RATIO / POOL_REGEN_RATE
    assert equilibrium == pytest.approx(COLLAPSE_EPSILON)
    # The regimes the universe defines must all stay reachable — this is the
    # test that would have caught D-162's ratio before a six-hour run did.
    assert equilibrium < POOL_CRISIS_THRESHOLD, "the crisis channel is unreachable"


def test_the_ceiling_falls_with_the_stock() -> None:
    """⚠ K2 — the whole mechanism is a function of the stock, so one stock
    level cannot test it. A ceiling that ignored its argument would satisfy any
    single-value fixture and produce a flat, undifferentiating commons.
    """

    high = harvest_ceiling(CEILING_STOCK_HIGH, CEILING_HERD)
    low = harvest_ceiling(CEILING_STOCK_LOW, CEILING_HERD)

    assert high > low
    assert high / low == pytest.approx(CEILING_STOCK_HIGH / CEILING_STOCK_LOW)
    # Per-capita, so N agents on an N-times pasture face the same ceiling each
    # — the invariant D-081 locked when the commons was scaled with N.
    assert harvest_ceiling(CEILING_STOCK_HIGH, CEILING_HERD) == pytest.approx(
        harvest_ceiling(CEILING_STOCK_HIGH / CEILING_HERD, 1)
    )


def test_the_shortfall_opens_before_the_landmark() -> None:
    """⭐⭐ D-163's reason for existing, as a number.

    Under the constant quota the short-fall was EXACTLY ZERO through event 16
    while the primary endpoint is read at event 10 — so at the moment of
    measurement the commons had contributed nothing to telling two agents
    apart, and eight founders came out bit-identical in three of four seeds.
    The ceiling has to open that gap before the landmark or the layer buys
    nothing for the endpoint it was built for.

    ⚠ K2: eight agents, and the round is walked, so both dimensions the rule
    depends on (who is served when, and how the stock falls) actually vary.
    """

    from dau.foundation.constraints import LANDMARK_EVENT

    env = EnvironmentState(pool=POOL_INIT * CEILING_HERD, capacity=POOL_MAX * CEILING_HERD)
    first_short: int | None = None
    spread_at_landmark = 0.0
    for event in range(1, LANDMARK_EVENT + 1):
        env = step_pool(
            env,
            {f"a{i}": EXTRACTION_DEFECT for i in range(CEILING_HERD)},
            sequential=True,
        )
        counter = max(row[EXTRACTION_KEY_EVENT] for row in env.extraction_history)
        served = [
            row[EXTRACTION_KEY_AMOUNT]
            for row in env.extraction_history
            if row[EXTRACTION_KEY_EVENT] == counter
        ]
        if first_short is None and served[0] < EXTRACTION_DEFECT - 1e-9:
            first_short = event
        spread_at_landmark = served[0] - served[-1]

    assert first_short is not None, "the ceiling never bound"
    assert first_short < LANDMARK_EVENT, (
        f"short-fall opened at event {first_short}, at or after the landmark"
    )
    assert spread_at_landmark > 0.0, (
        "no spread inside the landmark window — the endpoint still cannot see "
        "the commons, which is the state this layer was built to end"
    )
