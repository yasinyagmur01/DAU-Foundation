"""Production graph crisis / pool_step wiring — ADIM 1 integration tests."""

from __future__ import annotations

import pytest

import dau.foundation.graph as graph_mod
from dau.foundation.constraints import build_default_constraints
from dau.foundation.drift import DriftState
from dau.foundation.constraints import LANDMARK_EVENT, METABOLIC_GRACE_EVENTS
from dau.foundation.graph import (
    END,
    CommonsRequest,
    advance_commons,
    NODE_AGENT,
    NODE_META_OBSERVER,
    NODE_POOL_STEP,
    build_graph,
    pool_step_node,
    should_continue,
)
from dau.foundation.lod import CognitiveMode, LODState, NPC_ACTION_EXTRACT_MODERATE
from dau.foundation.state import DAUAgentState, Event, InternalState
from dau.society.environment import (
    POOL_CRISIS_THRESHOLD,
    POOL_MAX,
    POOL_REGEN_RATE,
    EnvironmentState,
    get_pool_ratio,
    harvest_ceiling,
    step_pool,
    crisis_trauma_magnitude,
)
from dau.society.extraction import (
    EXTRACTION_COOPERATE,
    EXTRACTION_DEFECT,
    decision_to_extraction,
    metabolic_gain,
)

AGENT_ID: str = "crisis-wire-0"
POOL_ABOVE_CRISIS: float = 80.0
POOL_NEAR_CRISIS: float = 25.0
MAX_EVENTS_ONE_CYCLE: int = 1
PE_STUB: float = 0.1
# Arbitrary non-zero ordinal: the row must copy the event it describes, not
# re-derive a counter of its own.
SEVENTH_EVENT: int = 7
# Stock too thin to satisfy a DEFECT-sized request even after regeneration.
POOL_MIN_STOCK: float = 1.0
# Written into the drift map AFTER a row is recorded, to prove the row copied.
LATER_SCAR_MAGNITUDE: float = 0.99


def _decision_event(decision: str) -> Event:
    """One agent_decision event carrying a decision string."""

    return Event(
        event_type="agent_decision",
        payload={"decision": decision},
        timestamp=0,
    )


def _state_with_env(
    *,
    pool: float,
    decision: str = NPC_ACTION_EXTRACT_MODERATE,
    env_state: EnvironmentState | None | object = ...,
) -> DAUAgentState:
    """Build a minimal agent state; pass env_state=None to omit society physics."""

    resolved_env: EnvironmentState | None
    if env_state is ...:
        resolved_env = EnvironmentState(pool=pool, event_counter=0)
    else:
        resolved_env = env_state  # type: ignore[assignment]

    return DAUAgentState(
        agent_id=AGENT_ID,
        environment=build_default_constraints(),
        internal_state=InternalState(),
        env_state=resolved_env,
        drift_state=DriftState(),
        lod_state=LODState(mode=CognitiveMode.SYSTEM_1),
        event_log=[_decision_event(decision)],
    )


def test_graph_pool_step_noop_when_env_state_none() -> None:
    """Society physics absent → pool_step returns empty patch."""

    state = _state_with_env(pool=POOL_ABOVE_CRISIS, env_state=None)
    assert pool_step_node(state) == {}


def test_graph_no_crisis_above_threshold() -> None:
    """After step, pool_ratio ≥ crisis threshold → drift flags stay empty."""

    state = _state_with_env(pool=POOL_ABOVE_CRISIS)
    patch = pool_step_node(state)
    new_env = patch["env_state"]
    new_drift = patch["drift_state"]
    assert get_pool_ratio(new_env) >= POOL_CRISIS_THRESHOLD
    assert new_drift.flags.get("resource") is not True
    assert new_env.event_counter == 1


def test_graph_crisis_wiring_triggers_trauma_below_threshold() -> None:
    """After step, pool_ratio < crisis threshold → resource trauma flag."""

    state = _state_with_env(pool=POOL_NEAR_CRISIS)
    patch = pool_step_node(state)
    new_env = patch["env_state"]
    new_drift = patch["drift_state"]
    assert get_pool_ratio(new_env) < POOL_CRISIS_THRESHOLD
    assert new_drift.flags["resource"] is True
    assert new_drift.magnitudes["resource"] > 0.0


def test_graph_pool_step_advances_env_and_writes_env_state() -> None:
    """pool_step returns updated EnvironmentState matching a single step_pool."""

    state = _state_with_env(pool=POOL_ABOVE_CRISIS)
    amount = decision_to_extraction(NPC_ACTION_EXTRACT_MODERATE)
    expected = step_pool(state.env_state, {AGENT_ID: amount})
    patch = pool_step_node(state)
    assert patch["env_state"].pool == pytest.approx(expected.pool)
    assert patch["env_state"].event_counter == expected.event_counter == 1
    assert len(patch["env_state"].extraction_history) == 1


def test_graph_pool_step_uses_decision_to_extraction_amount() -> None:
    """Harvest amount follows shared decision_to_extraction mapping."""

    state = _state_with_env(
        pool=POOL_ABOVE_CRISIS,
        decision=NPC_ACTION_EXTRACT_MODERATE,
    )
    patch = pool_step_node(state)
    history = patch["env_state"].extraction_history
    assert history[0]["amount"] == pytest.approx(EXTRACTION_DEFECT)
    assert history[0]["agent_id"] == AGENT_ID


def test_graph_pool_step_single_advance_per_invocation() -> None:
    """One pool_step_node call → one regen+extract (no double-step physics)."""

    state = _state_with_env(pool=POOL_ABOVE_CRISIS)
    amount = decision_to_extraction(NPC_ACTION_EXTRACT_MODERATE)
    expected_once = step_pool(state.env_state, {AGENT_ID: amount})
    expected_twice = step_pool(expected_once, {AGENT_ID: amount})

    patch = pool_step_node(state)
    got = patch["env_state"]

    assert got.event_counter == 1
    assert got.pool == pytest.approx(expected_once.pool)
    assert got.pool != pytest.approx(expected_twice.pool)


def test_graph_wiring_pool_step_between_meta_and_continue() -> None:
    """Compiled graph: meta_observer → pool_step; continue edges from pool_step."""

    app = build_graph(checkpointer=None)
    graph = app.get_graph()
    edge_pairs = {(edge.source, edge.target) for edge in graph.edges}
    assert (NODE_META_OBSERVER, NODE_POOL_STEP) in edge_pairs
    pool_out = {edge.target for edge in graph.edges if edge.source == NODE_POOL_STEP}
    assert pool_out  # routes to social_pre and/or END


def test_graph_one_cycle_advances_pool_event_counter_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Full sense-act cycle advances env.event_counter by exactly one."""

    monkeypatch.setattr(graph_mod, "MAX_EVENTS", MAX_EVENTS_ONE_CYCLE)
    monkeypatch.setattr(graph_mod, "MEMORY_ENABLED", False)
    monkeypatch.setattr(
        graph_mod,
        "_prediction_error",
        lambda expected, actual: PE_STUB,
    )

    initial = DAUAgentState(
        agent_id=AGENT_ID,
        environment=build_default_constraints(),
        internal_state=InternalState(),
        env_state=EnvironmentState(pool=POOL_ABOVE_CRISIS, event_counter=0),
        drift_state=DriftState(),
        lod_state=LODState(mode=CognitiveMode.SYSTEM_1),
    )
    app = build_graph(checkpointer=None)
    final: DAUAgentState | None = None
    for values in app.stream(initial, stream_mode="values"):
        final = (
            values
            if isinstance(values, DAUAgentState)
            else DAUAgentState.model_validate(values)
        )

    assert final is not None
    assert isinstance(final.env_state, EnvironmentState)
    assert final.env_state.event_counter == 1
    assert len(final.event_log) == 1


# ---------------------------------------------------------------------------
# S5 commons trace (L20: B2 could not run S5 because none of this was recorded)
# ---------------------------------------------------------------------------


def test_pool_event_log_records_extraction_and_no_crisis() -> None:
    """Above the crisis floor: one row, real harvest amount, crisis False."""

    graph_mod.reset_pool_event_log()
    state = _state_with_env(pool=POOL_ABOVE_CRISIS)
    pool_step_node(state)

    rows = graph_mod.get_pool_event_log()
    assert len(rows) == 1
    assert rows[0]["extraction"] == pytest.approx(EXTRACTION_DEFECT)
    assert rows[0]["crisis"] is False
    assert rows[0]["pool_ratio"] >= POOL_CRISIS_THRESHOLD


def test_pool_event_log_crisis_flag_matches_the_gate_that_scars() -> None:
    """Below the floor: crisis=True, and it agrees with the drift patch.

    The flag is only useful if it marks the events that actually scarred the
    agent — a flag computed from a different ratio than apply_crisis_trauma
    reads would silently disagree with the drift map.
    """

    graph_mod.reset_pool_event_log()
    state = _state_with_env(pool=POOL_NEAR_CRISIS)
    patch = pool_step_node(state)

    rows = graph_mod.get_pool_event_log()
    assert len(rows) == 1
    assert rows[0]["crisis"] is True
    assert rows[0]["pool_ratio"] < POOL_CRISIS_THRESHOLD
    assert rows[0]["pool_ratio"] == pytest.approx(get_pool_ratio(patch["env_state"]))
    assert patch["drift_state"].flags["resource"] is True


def test_pool_event_log_row_counter_follows_the_event_it_describes() -> None:
    """event_counter comes from the decision event, so PE rows can be joined."""

    graph_mod.reset_pool_event_log()
    state = _state_with_env(pool=POOL_ABOVE_CRISIS)
    state.event_log[-1] = Event(
        event_type="agent_decision",
        payload={"decision": NPC_ACTION_EXTRACT_MODERATE},
        timestamp=SEVENTH_EVENT,
    )
    pool_step_node(state)

    assert graph_mod.get_pool_event_log()[0]["event_counter"] == SEVENTH_EVENT


def test_pool_event_log_stays_empty_without_society_physics() -> None:
    """No env_state → no commons row (the node returns before the physics)."""

    graph_mod.reset_pool_event_log()
    state = _state_with_env(pool=POOL_ABOVE_CRISIS, env_state=None)
    pool_step_node(state)

    assert graph_mod.get_pool_event_log() == []


# ---------------------------------------------------------------------------
# A4 / D-066 — the metabolic loop: harvest becomes energy, energy runs out
# ---------------------------------------------------------------------------

ENERGY_HALF: float = 0.5
BEYOND_GRACE_EVENTS: int = METABOLIC_GRACE_EVENTS + 1


def test_pool_step_credits_energy_from_the_harvest() -> None:
    """A harvest raises energy — before D-066 energy could only ever fall."""

    graph_mod.reset_pool_event_log()
    state = _state_with_env(pool=POOL_ABOVE_CRISIS)
    state = state.model_copy(update={"internal_state": InternalState(energy=ENERGY_HALF)})

    patch = pool_step_node(state)

    expected = ENERGY_HALF + metabolic_gain(EXTRACTION_DEFECT)
    assert patch["internal_state"].energy == pytest.approx(expected)
    assert patch["internal_state"].energy > ENERGY_HALF


def test_energy_credit_follows_the_delivered_harvest_not_the_announcement() -> None:
    """An exhausted pasture must not feed the agent (the cost of defecting)."""

    graph_mod.reset_pool_event_log()
    state = _state_with_env(pool=POOL_MIN_STOCK)
    state = state.model_copy(update={"internal_state": InternalState(energy=ENERGY_HALF)})

    patch = pool_step_node(state)
    row = graph_mod.get_pool_event_log()[0]

    assert row["requested"] == pytest.approx(EXTRACTION_DEFECT)
    assert row["extraction"] < row["requested"]
    assert patch["internal_state"].energy == pytest.approx(
        ENERGY_HALF + metabolic_gain(row["extraction"])
    )


def test_metabolic_gain_is_concave_not_proportional() -> None:
    """4x the harvest must not buy 4x the energy (DR #4 / J9).

    A proportional link would leave over-extraction strictly dominant, which
    is the flat landscape this change exists to break.
    """

    small = metabolic_gain(EXTRACTION_COOPERATE)
    large = metabolic_gain(EXTRACTION_DEFECT)
    harvest_ratio = EXTRACTION_DEFECT / EXTRACTION_COOPERATE

    assert large > small
    assert large / small < harvest_ratio
    assert metabolic_gain(0.0) == 0.0


def test_agent_survives_zero_energy_during_the_birth_transient() -> None:
    """Inside the grace window the floor still holds the run open."""

    state = _state_with_env(pool=POOL_ABOVE_CRISIS)
    state = state.model_copy(update={"internal_state": InternalState(energy=0.0)})

    assert should_continue(state) == NODE_AGENT


def test_agent_dies_of_exhaustion_once_the_grace_window_passes() -> None:
    """After the transient, running out of energy ends the life (D-066).

    Survival read 1.0 on 120 of 120 arms because AB_ENERGY_FLOOR sat above
    TERMINATION_ENERGY for the whole run — death was structurally impossible.
    """

    state = _state_with_env(pool=POOL_ABOVE_CRISIS)
    state = state.model_copy(
        update={
            "internal_state": InternalState(energy=0.0),
            "event_log": [_decision_event(NPC_ACTION_EXTRACT_MODERATE)]
            * BEYOND_GRACE_EVENTS,
        }
    )

    assert should_continue(state) == END


def test_a_fed_agent_past_the_grace_window_keeps_living() -> None:
    """Death is exhaustion, not age: energy above the floor still routes on."""

    state = _state_with_env(pool=POOL_ABOVE_CRISIS)
    state = state.model_copy(
        update={
            "internal_state": InternalState(energy=ENERGY_HALF),
            "event_log": [_decision_event(NPC_ACTION_EXTRACT_MODERATE)]
            * BEYOND_GRACE_EVENTS,
        }
    )

    assert should_continue(state) == NODE_AGENT


# ---------------------------------------------------------------------------
# K1/K2/K5 (D-070) — the per-event body trace the landmark is read from
# ---------------------------------------------------------------------------


def test_body_event_log_records_energy_after_the_metabolic_credit() -> None:
    """The row is the state the NEXT event starts from, not a mid-cycle one.

    Recording before the credit would report the energy the evaluator left,
    which is a different quantity from the one should_continue is about to
    judge — and the landmark reading would then describe a moment that never
    existed.
    """

    graph_mod.reset_body_event_log()
    state = _state_with_env(pool=POOL_ABOVE_CRISIS)
    state = state.model_copy(
        update={"internal_state": InternalState(energy=ENERGY_HALF)}
    )

    patch = pool_step_node(state)
    rows = graph_mod.get_body_event_log()

    assert len(rows) == 1
    assert rows[0]["energy"] == pytest.approx(patch["internal_state"].energy)
    assert rows[0]["energy"] > ENERGY_HALF


def test_body_event_log_records_drift_after_crisis_scarring() -> None:
    """Drift is read post-crisis, so the landmark sees the scar of that event."""

    graph_mod.reset_body_event_log()
    state = _state_with_env(pool=POOL_NEAR_CRISIS)

    patch = pool_step_node(state)
    row = graph_mod.get_body_event_log()[0]

    assert row["drift_flags"]["resource"] is True
    assert row["drift_flags"] == patch["drift_state"].flags
    assert row["drift_magnitudes"] == pytest.approx(patch["drift_state"].magnitudes)


def test_body_event_row_snapshots_drift_instead_of_aliasing_it() -> None:
    """A live reference would let later scarring rewrite the landmark.

    DriftState is mutable and the agent goes on being scarred after the row
    is written, so a row holding the same dict would report the drift of the
    END of the life under the ordinal of event N.
    """

    graph_mod.reset_body_event_log()
    state = _state_with_env(pool=POOL_NEAR_CRISIS)

    patch = pool_step_node(state)
    row = graph_mod.get_body_event_log()[0]
    recorded = dict(row["drift_magnitudes"])

    patch["drift_state"].magnitudes["resource"] = LATER_SCAR_MAGNITUDE
    patch["drift_state"].flags["social"] = True

    assert graph_mod.get_body_event_log()[0]["drift_magnitudes"] == recorded
    assert "social" not in graph_mod.get_body_event_log()[0]["drift_flags"]


def test_body_event_row_counter_follows_the_event_it_describes() -> None:
    """The landmark is an ordinal, so the row must carry the event's own."""

    graph_mod.reset_body_event_log()
    state = _state_with_env(pool=POOL_ABOVE_CRISIS)
    state.event_log[-1] = Event(
        event_type="agent_decision",
        payload={"decision": NPC_ACTION_EXTRACT_MODERATE},
        timestamp=SEVENTH_EVENT,
    )
    pool_step_node(state)

    assert graph_mod.get_body_event_log()[0]["event_counter"] == SEVENTH_EVENT


def test_no_lineage_can_die_before_reaching_the_landmark() -> None:
    """LANDMARK_EVENT and METABOLIC_GRACE_EVENTS are the same moment (D-070).

    Not a coincidence to be maintained by hand. should_continue is asked
    whether to run event N while len(event_log) is N-1, so an exhausted agent
    is carried through every ordinal up to and including LANDMARK_EVENT — the
    landmark row is always written before death becomes possible.

    The boundary is exact, and asserted in both directions: the very next
    decision is the first one death can win. That is what makes the "died
    before the landmark" rule unreachable today, and why it is still written
    (§2.9) — if grace ever shrinks below the landmark, this test fails rather
    than the rule going quietly dead.
    """

    assert LANDMARK_EVENT <= METABOLIC_GRACE_EVENTS

    def _exhausted_after(events: int) -> DAUAgentState:
        state = _state_with_env(pool=POOL_ABOVE_CRISIS)
        return state.model_copy(
            update={
                "internal_state": InternalState(energy=0.0),
                "event_log": [_decision_event(NPC_ACTION_EXTRACT_MODERATE)]
                * events,
            }
        )

    # About to run the landmark event itself: still alive, out of energy.
    assert should_continue(_exhausted_after(LANDMARK_EVENT - 1)) == NODE_AGENT
    # Landmark event closed and recorded — now exhaustion may end the life.
    assert should_continue(_exhausted_after(LANDMARK_EVENT)) == END


# ---------------------------------------------------------------------------
# advance_commons — N agents share one pasture (E1/E5, D-097)
# ---------------------------------------------------------------------------

SECOND_AGENT_ID: str = "crisis-wire-1"
# Two agents on one thin pasture: the requests differ so a proportional split
# is distinguishable from an equal one.
BIG_REQUEST: float = EXTRACTION_DEFECT
SMALL_REQUEST: float = EXTRACTION_COOPERATE
# Distinct per-agent clocks: the pool ticks once per round, each life counts
# its own events, so a row must not borrow the environment's counter.
FIRST_AGENT_EVENT: int = 3
SECOND_AGENT_EVENT: int = 11


def _request(agent_id: str, requested: float, event_counter: int, energy: float):
    """One CommonsRequest with a fresh body and an unscarred drift map."""

    return CommonsRequest(
        agent_id=agent_id,
        requested=requested,
        event_counter=event_counter,
        drift_state=DriftState(),
        internal_state=InternalState(energy=energy),
    )


def test_advance_commons_matches_the_single_agent_node() -> None:
    """N=1 through advance_commons is the node's own physics, unchanged."""

    graph_mod.reset_pool_event_log()
    graph_mod.reset_body_event_log()
    state = _state_with_env(pool=POOL_ABOVE_CRISIS)
    state = state.model_copy(
        update={"internal_state": InternalState(energy=ENERGY_HALF)}
    )
    node_patch = pool_step_node(state)

    graph_mod.reset_pool_event_log()
    graph_mod.reset_body_event_log()
    direct_env, direct = advance_commons(
        _state_with_env(pool=POOL_ABOVE_CRISIS).env_state,
        [
            _request(
                AGENT_ID,
                decision_to_extraction(NPC_ACTION_EXTRACT_MODERATE),
                0,
                ENERGY_HALF,
            )
        ],
    )

    assert direct_env.pool == pytest.approx(node_patch["env_state"].pool)
    assert direct[AGENT_ID].internal_state.energy == pytest.approx(
        node_patch["internal_state"].energy
    )
    assert direct[AGENT_ID].drift_state.flags == node_patch["drift_state"].flags


def test_advance_commons_serves_a_thin_pasture_through_the_ceiling() -> None:
    """⚠ D-163 rewrote this test's claim, and the old claim is worth keeping
    visible: an exhausted pasture used to serve both grazers PRO RATA, so a
    3:1 ask came back 3:1 even when nothing was left.

    With a stock-proportional ceiling that regime is gone. On a thin pasture
    every ask above the ceiling is levelled to it, so the ratio of the asks
    stops showing up in the ratio of the harvests. What survives — and what
    this test now protects — is that nobody is served more than the commons
    allows and that the ask still decides whenever it sits UNDER the ceiling.
    """

    graph_mod.reset_pool_event_log()
    graph_mod.reset_body_event_log()
    env = EnvironmentState(pool=POOL_MIN_STOCK)
    _, outcomes = advance_commons(
        env,
        [
            _request(AGENT_ID, BIG_REQUEST, FIRST_AGENT_EVENT, ENERGY_HALF),
            _request(SECOND_AGENT_ID, SMALL_REQUEST, SECOND_AGENT_EVENT, ENERGY_HALF),
        ],
    )

    big = outcomes[AGENT_ID].granted
    small = outcomes[SECOND_AGENT_ID].granted
    regenerated = POOL_MIN_STOCK + POOL_REGEN_RATE * POOL_MIN_STOCK * (
        1.0 - POOL_MIN_STOCK / POOL_MAX
    )
    ceiling = harvest_ceiling(regenerated, 2)
    assert big < BIG_REQUEST and small < SMALL_REQUEST, "pasture was not short"
    # This call takes the DEFAULT (proportional) path, where the ceiling is
    # read once for the round: two asks above it come back identical, and the
    # 3:1 ratio the old test asserted is simply not there any more.
    assert big == pytest.approx(ceiling)
    assert small == pytest.approx(ceiling)
    assert big / small == pytest.approx(1.0), "pro-rata behaviour is back"
    # ⚠ The order advantage lives in the SEQUENTIAL path, not this one — see
    # test_sequential_service_favours_the_earlier_position. Asserting it here
    # would claim the population's physics for a function that does not run it.


def test_advance_commons_writes_one_row_per_agent_on_its_own_clock() -> None:
    """Each row carries the AGENT's event counter, never the pool's."""

    graph_mod.reset_pool_event_log()
    graph_mod.reset_body_event_log()
    advance_commons(
        EnvironmentState(pool=POOL_ABOVE_CRISIS),
        [
            _request(AGENT_ID, BIG_REQUEST, FIRST_AGENT_EVENT, ENERGY_HALF),
            _request(SECOND_AGENT_ID, SMALL_REQUEST, SECOND_AGENT_EVENT, ENERGY_HALF),
        ],
    )

    pool_rows = graph_mod.get_pool_event_log()
    body_rows = graph_mod.get_body_event_log()
    assert len(pool_rows) == len(body_rows) == 2
    by_agent = {row["agent_id"]: row["event_counter"] for row in pool_rows}
    assert by_agent == {
        AGENT_ID: FIRST_AGENT_EVENT,
        SECOND_AGENT_ID: SECOND_AGENT_EVENT,
    }


def test_advance_commons_feeds_each_agent_from_its_own_harvest() -> None:
    """The grazer that took more is the one that gained more energy."""

    graph_mod.reset_pool_event_log()
    graph_mod.reset_body_event_log()
    _, outcomes = advance_commons(
        EnvironmentState(pool=POOL_ABOVE_CRISIS),
        [
            _request(AGENT_ID, BIG_REQUEST, FIRST_AGENT_EVENT, ENERGY_HALF),
            _request(SECOND_AGENT_ID, SMALL_REQUEST, SECOND_AGENT_EVENT, ENERGY_HALF),
        ],
    )

    # D-163: read the HARVEST, not the request. The two were the same number
    # while a full pasture served every ask in full; now the ceiling can cut
    # the big one, and asserting against the announcement would be testing the
    # fixture rather than the metabolic loop (§2.8).
    assert outcomes[AGENT_ID].internal_state.energy == pytest.approx(
        ENERGY_HALF + metabolic_gain(outcomes[AGENT_ID].granted)
    )
    assert outcomes[SECOND_AGENT_ID].internal_state.energy == pytest.approx(
        ENERGY_HALF + metabolic_gain(outcomes[SECOND_AGENT_ID].granted)
    )
    assert outcomes[AGENT_ID].granted > outcomes[SECOND_AGENT_ID].granted
    assert (
        outcomes[AGENT_ID].internal_state.energy
        > outcomes[SECOND_AGENT_ID].internal_state.energy
    )


def test_advance_commons_rejects_a_duplicate_agent() -> None:
    """Two requests with one id would make the ledger ambiguous (§2.9)."""

    with pytest.raises(ValueError, match="duplicate"):
        advance_commons(
            EnvironmentState(pool=POOL_ABOVE_CRISIS),
            [
                _request(AGENT_ID, BIG_REQUEST, FIRST_AGENT_EVENT, ENERGY_HALF),
                _request(AGENT_ID, SMALL_REQUEST, SECOND_AGENT_EVENT, ENERGY_HALF),
            ],
        )


def test_advance_commons_rejects_an_empty_round() -> None:
    """A round with no grazers is a caller bug, not a no-op."""

    with pytest.raises(ValueError, match="at least one"):
        advance_commons(EnvironmentState(pool=POOL_ABOVE_CRISIS), [])


def test_advance_commons_logs_the_scar_the_famine_actually_wrote() -> None:
    """⭐ D-117: the crisis path must leave its magnitude on the commons row.

    ``update_drift`` has two callers and this is the one that was silent: a
    famine scars EVERY agent at once, and with only a boolean on the row the
    run could not say whether an agent's drift came from its own surprise or
    from the pasture collapsing on everybody. D-115 had to reconstruct that
    from outside the results file.

    Mutation check (§2.4): passing ``crisis_magnitude=None`` at the call site
    broke NO test until this one — the unit test calls the recorder directly,
    so it never saw the wiring.
    """

    graph_mod.reset_pool_event_log()
    graph_mod.reset_body_event_log()
    env = EnvironmentState(pool=POOL_MIN_STOCK)
    advance_commons(
        env,
        [_request(AGENT_ID, BIG_REQUEST, FIRST_AGENT_EVENT, ENERGY_HALF)],
    )
    row = graph_mod.get_pool_event_log()[-1]
    graph_mod.reset_pool_event_log()

    assert row["crisis"] is True, "the pasture was not in crisis — test is blind"
    # Read from the universe's own function, not restated: a literal here would
    # be the reporting drift §2.8 keeps catching.
    assert row["crisis_magnitude"] == pytest.approx(
        crisis_trauma_magnitude(row["pool_ratio"])
    )


def test_a_healthy_pasture_writes_no_scar_on_the_row() -> None:
    """No crisis, no magnitude: None says 'nobody was scarred here'."""

    graph_mod.reset_pool_event_log()
    graph_mod.reset_body_event_log()
    advance_commons(
        _state_with_env(pool=POOL_ABOVE_CRISIS).env_state,
        [_request(AGENT_ID, SMALL_REQUEST, FIRST_AGENT_EVENT, ENERGY_HALF)],
    )
    row = graph_mod.get_pool_event_log()[-1]
    graph_mod.reset_pool_event_log()

    assert row["crisis"] is False
    assert row["crisis_magnitude"] is None
