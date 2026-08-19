"""Single-event graph (E2 step 1): one agent, one event, commons untouched."""

from __future__ import annotations

from typing import Any

import pytest

import dau.foundation.graph as graph_mod
from dau.foundation.constraints import build_default_constraints
from dau.foundation.graph import (
    NODE_AGENT,
    NODE_EVALUATOR,
    NODE_META_OBSERVER,
    NODE_POOL_STEP,
    NODE_SOCIAL_PRE,
    build_event_graph,
    run_population,
    run_round,
    step_agent_once,
)
from dau.foundation.drift import DriftState
from dau.foundation.lod import (
    CognitiveMode,
    LODState,
    NPC_ACTION_COOPERATE,
    NPC_ACTION_EXTRACT_MODERATE,
)
from dau.foundation.state import DAUAgentState, InternalState
from dau.society.environment import EnvironmentState

AGENT_ID: str = "event-graph-0"
POOL_START: float = 80.0
ENERGY_START: float = 0.6
STUB_DECISION: str = NPC_ACTION_EXTRACT_MODERATE
# Different agents must announce DIFFERENT amounts, otherwise an order test is
# vacuous: with identical requests a per-agent tick produces the same numbers in
# either order, and the mutation the test exists to catch slips through.
STUB_DECISION_BY_AGENT: dict[str, str] = {}
# Stock too thin to serve both announcements, so the proportional split engages.
POOL_THIN: float = 1.0


def _decision_row(state: DAUAgentState):
    """One agent_decision event in the shape the real node writes."""

    return graph_mod.build_event(
        graph_mod.EventClock(counter=len(state.event_log)),
        "agent_decision",
        {
            "decision": STUB_DECISION_BY_AGENT.get(state.agent_id, STUB_DECISION),
            "energy": float(state.internal_state.energy),
            "expected_outcome": {},
        },
    )


def _stub_agent(state: DAUAgentState) -> dict[str, Any]:
    """Append one decision event without calling any LLM.

    Carries `energy` because the meta observer refuses a decision row without
    it — F_agent averages the energy trace and a hole would silently bias it
    (D-086, self_model.py). The stub has to honour that invariant like the real
    node does, otherwise the test would pass against a weaker contract.
    """

    return {"event_log": list(state.event_log) + [_decision_row(state)]}


def _birth_state() -> DAUAgentState:
    """A minimal living agent with society physics attached."""

    return DAUAgentState(
        agent_id=AGENT_ID,
        environment=build_default_constraints(),
        internal_state=InternalState(energy=ENERGY_START),
        drift_state=DriftState(),
        lod_state=LODState(mode=CognitiveMode.SYSTEM_1),
        env_state=EnvironmentState(pool=POOL_START),
    )


def test_event_graph_has_no_commons_node() -> None:
    """The pasture must tick once per ROUND, so its node is not in this graph."""

    nodes = set(build_event_graph().get_graph().nodes)
    assert {NODE_SOCIAL_PRE, NODE_AGENT, NODE_EVALUATOR, NODE_META_OBSERVER} <= nodes
    assert NODE_POOL_STEP not in nodes


def test_step_agent_once_adds_exactly_one_event(monkeypatch) -> None:
    """One call, one event — the outer loop owns the iteration, not the graph."""

    monkeypatch.setattr(graph_mod, "agent_node", _stub_agent)
    app = build_event_graph()
    state = _birth_state()
    assert len(state.event_log) == 0

    stepped = step_agent_once(state, app)

    assert len(stepped.event_log) == 1
    assert stepped.event_log[-1].payload["decision"] == STUB_DECISION


def test_step_agent_once_leaves_the_commons_alone(monkeypatch) -> None:
    """No harvest, no ledger row, no pool tick — advance_commons does that."""

    monkeypatch.setattr(graph_mod, "agent_node", _stub_agent)
    graph_mod.reset_pool_event_log()
    graph_mod.reset_body_event_log()
    app = build_event_graph()

    stepped = step_agent_once(_birth_state(), app)

    assert stepped.env_state.pool == pytest.approx(POOL_START)
    assert stepped.env_state.event_counter == 0
    assert graph_mod.get_pool_event_log() == []
    assert graph_mod.get_body_event_log() == []


def test_step_agent_once_rejects_an_unexpected_result_type() -> None:
    """A graph that returns something else is a wiring bug, not a no-op (§2.9)."""

    class _Odd:
        def invoke(self, _state: Any) -> Any:
            return "not a state"

    with pytest.raises(TypeError, match="event-graph result"):
        step_agent_once(_birth_state(), _Odd())


# ---------------------------------------------------------------------------
# run_round — N agents act, then the pasture ticks ONCE (E2 step 2)
# ---------------------------------------------------------------------------

SECOND_ID: str = "event-graph-1"
# Below TERMINATION_ENERGY and past the grace window, so the agent must be
# dropped from `alive` rather than quietly kept in the population.



def _birth_state_named(agent_id: str, energy: float = ENERGY_START) -> DAUAgentState:
    """A living agent with a given id and starting energy."""

    return _birth_state().model_copy(
        update={"agent_id": agent_id, "internal_state": InternalState(energy=energy)}
    )


def test_run_round_ticks_the_pasture_once_for_two_agents(monkeypatch) -> None:
    """The load-bearing property: one round, one pool step, N harvest rows."""

    monkeypatch.setattr(graph_mod, "agent_node", _stub_agent)
    graph_mod.reset_pool_event_log()
    graph_mod.reset_body_event_log()
    app = build_event_graph()
    env = EnvironmentState(pool=POOL_START)

    result = run_round(
        env,
        [_birth_state_named(AGENT_ID), _birth_state_named(SECOND_ID)],
        app,
    )

    assert result.env_state.event_counter == 1, "pasture ticked more than once"
    assert len(result.env_state.extraction_history) == 2
    assert set(result.granted) == {AGENT_ID, SECOND_ID}


def test_run_round_advances_every_agent_by_one_event(monkeypatch) -> None:
    """Nobody is skipped and nobody gets two events in one round."""

    monkeypatch.setattr(graph_mod, "agent_node", _stub_agent)
    app = build_event_graph()
    result = run_round(
        EnvironmentState(pool=POOL_START),
        [_birth_state_named(AGENT_ID), _birth_state_named(SECOND_ID)],
        app,
    )

    for agent_id in (AGENT_ID, SECOND_ID):
        assert len(result.states[agent_id].event_log) == 1
        assert result.states[agent_id].env_state is result.env_state


def test_run_round_result_does_not_depend_on_act_order(monkeypatch) -> None:
    """Requests are collected BEFORE the pool moves, so order cannot leak in.

    This is what "shared commons" means mechanically: with a per-agent tick the
    second agent would draw from an already-reduced pool and the two orders
    would disagree.
    """

    monkeypatch.setattr(graph_mod, "agent_node", _stub_agent)
    monkeypatch.setitem(STUB_DECISION_BY_AGENT, SECOND_ID, NPC_ACTION_COOPERATE)
    app = build_event_graph()
    forward = run_round(
        EnvironmentState(pool=POOL_THIN),
        [_birth_state_named(AGENT_ID), _birth_state_named(SECOND_ID)],
        app,
    )
    backward = run_round(
        EnvironmentState(pool=POOL_THIN),
        [_birth_state_named(SECOND_ID), _birth_state_named(AGENT_ID)],
        app,
    )

    assert forward.granted[AGENT_ID] > forward.granted[SECOND_ID], (
        "the thin pasture must actually be short, or the split never engages"
    )

    assert forward.env_state.pool == pytest.approx(backward.env_state.pool)
    assert forward.granted == pytest.approx(backward.granted)


def test_run_round_drops_an_agent_that_cannot_continue(monkeypatch) -> None:
    """`alive` is the population of the NEXT round, not a copy of this one.

    The event budget is used as the stop reason rather than starvation: on a
    stocked pasture the harvest is credited before should_continue judges
    (D-066), so a spent body revives inside the round and energy cannot be made
    to differ cleanly. The budget route exercises the same real
    should_continue.
    """

    monkeypatch.setattr(graph_mod, "agent_node", _stub_agent)
    monkeypatch.setattr(graph_mod, "MAX_EVENTS", 2)
    app = build_event_graph()

    young = _birth_state_named(AGENT_ID)
    old = _birth_state_named(SECOND_ID)
    old = old.model_copy(update={"event_log": [_decision_row(old)]})

    result = run_round(EnvironmentState(pool=POOL_START), [young, old], app)

    assert len(result.states[AGENT_ID].event_log) == 1
    assert len(result.states[SECOND_ID].event_log) == 2
    assert AGENT_ID in result.alive
    assert SECOND_ID not in result.alive, "an agent out of budget must not live on"
    assert SECOND_ID in result.states, "a dropped agent still leaves its last state"


def test_run_round_rejects_an_empty_population() -> None:
    """A round with nobody in it is a caller bug, not a no-op."""

    with pytest.raises(ValueError, match="at least one"):
        run_round(EnvironmentState(pool=POOL_START), [], build_event_graph())


def test_run_round_rejects_duplicate_agent_ids(monkeypatch) -> None:
    """Two states with one id would make the ledger and `granted` ambiguous."""

    monkeypatch.setattr(graph_mod, "agent_node", _stub_agent)
    app = build_event_graph()
    with pytest.raises(ValueError, match="duplicate"):
        run_round(
            EnvironmentState(pool=POOL_START),
            [_birth_state_named(AGENT_ID), _birth_state_named(AGENT_ID)],
            app,
        )


# ---------------------------------------------------------------------------
# run_population — the loop build_graph's conditional edge used to own (E2-3)
# ---------------------------------------------------------------------------

LIFE_EVENTS: int = 4
ROUND_GUARD: int = 20
# Deliberately below the event budget so the guard bites while agents live on.
TIGHT_GUARD: int = 2


def _life_trace(agent_id: str) -> tuple[list[str], list[float]]:
    """Decisions and PE values of one life, read off the global ledgers."""

    decisions = [
        str(row.payload.get("decision", ""))
        for row in _TRACE_STATES[agent_id].event_log
    ]
    pe_values = [
        float(row["prediction_error"])
        for row in graph_mod.get_pe_event_log()
        if row["agent_id"] == agent_id
    ]
    return decisions, pe_values


_TRACE_STATES: dict[str, DAUAgentState] = {}


def test_run_population_reproduces_the_production_graph_digest(monkeypatch) -> None:
    """⭐ The load-bearing check: one life through both paths, same arm_digest.

    The production graph closes its own loop; run_population closes it from
    outside. If the two disagree on decisions or PE — the two sequences
    arm_digest hashes (D-012) — then every run measured before this refactor
    stops being a comparison baseline.
    """

    from dau.diagnostics.preflight import arm_digest

    monkeypatch.setattr(graph_mod, "agent_node", _stub_agent)
    monkeypatch.setattr(graph_mod, "MAX_EVENTS", LIFE_EVENTS)

    graph_mod.reset_pe_event_log()
    graph_mod.reset_pool_event_log()
    graph_mod.reset_body_event_log()
    inside: Any = _birth_state()
    for values in graph_mod.build_graph().stream(
        _birth_state(),
        config={"recursion_limit": ROUND_GUARD * 10},
        stream_mode="values",
    ):
        inside = values
    inside_state = DAUAgentState.model_validate(inside)
    _TRACE_STATES[AGENT_ID] = inside_state
    inside_digest = arm_digest(*_life_trace(AGENT_ID))
    inside_pool = inside_state.env_state.pool
    inside_energy = float(inside_state.internal_state.energy)

    graph_mod.reset_pe_event_log()
    graph_mod.reset_pool_event_log()
    graph_mod.reset_body_event_log()
    outcome = run_population(
        EnvironmentState(pool=POOL_START),
        [_birth_state()],
        build_event_graph(),
        max_rounds=ROUND_GUARD,
    )
    _TRACE_STATES[AGENT_ID] = outcome.states[AGENT_ID]
    outside_digest = arm_digest(*_life_trace(AGENT_ID))

    assert outside_digest == inside_digest
    assert outcome.env_state.pool == pytest.approx(inside_pool)
    assert outcome.states[AGENT_ID].internal_state.energy == pytest.approx(
        inside_energy
    )
    assert outcome.n_rounds == LIFE_EVENTS
    assert outcome.hit_round_cap is False


def test_run_population_runs_two_agents_on_one_pasture(monkeypatch) -> None:
    """N agents, one tick per round — the pool advances once per round, not per agent."""

    monkeypatch.setattr(graph_mod, "agent_node", _stub_agent)
    monkeypatch.setattr(graph_mod, "MAX_EVENTS", LIFE_EVENTS)
    outcome = run_population(
        EnvironmentState(pool=POOL_START),
        [_birth_state_named(AGENT_ID), _birth_state_named(SECOND_ID)],
        build_event_graph(),
        max_rounds=ROUND_GUARD,
    )

    assert outcome.env_state.event_counter == outcome.n_rounds
    assert len(outcome.granted_by_round) == outcome.n_rounds
    assert set(outcome.states) == {AGENT_ID, SECOND_ID}


def test_run_population_says_out_loud_when_the_guard_truncates(monkeypatch) -> None:
    """A truncated run must not look like a completed one (§2.9)."""

    monkeypatch.setattr(graph_mod, "agent_node", _stub_agent)
    monkeypatch.setattr(graph_mod, "MAX_EVENTS", LIFE_EVENTS)
    outcome = run_population(
        EnvironmentState(pool=POOL_START),
        [_birth_state()],
        build_event_graph(),
        max_rounds=TIGHT_GUARD,
    )

    assert outcome.n_rounds == TIGHT_GUARD
    assert outcome.hit_round_cap is True


def test_run_population_rejects_a_nonsense_guard(monkeypatch) -> None:
    """Zero rounds is a caller bug, not an empty result."""

    monkeypatch.setattr(graph_mod, "agent_node", _stub_agent)
    with pytest.raises(ValueError, match="max_rounds"):
        run_population(
            EnvironmentState(pool=POOL_START),
            [_birth_state()],
            build_event_graph(),
            max_rounds=0,
        )


def test_run_population_passes_the_sequential_flag_down(monkeypatch) -> None:
    """The flag has to reach the pasture, not just sit on run_population.

    Measured gap — deleting the pass-through left every test green, because
    nothing above advance_commons looked at who got served first.
    """

    monkeypatch.setattr(graph_mod, "agent_node", _stub_agent)
    monkeypatch.setitem(STUB_DECISION_BY_AGENT, SECOND_ID, NPC_ACTION_COOPERATE)
    monkeypatch.setattr(graph_mod, "MAX_EVENTS", 1)
    app = build_event_graph()

    ordered = run_population(
        EnvironmentState(pool=POOL_THIN),
        [_birth_state_named(AGENT_ID), _birth_state_named(SECOND_ID)],
        app,
        max_rounds=1,
        sequential=True,
    )
    shared = run_population(
        EnvironmentState(pool=POOL_THIN),
        [_birth_state_named(AGENT_ID), _birth_state_named(SECOND_ID)],
        app,
        max_rounds=1,
        sequential=False,
    )

    first_ordered = ordered.granted_by_round[0]
    first_shared = shared.granted_by_round[0]
    assert first_ordered[AGENT_ID] > first_ordered[SECOND_ID]
    assert first_ordered != first_shared, "sequential and proportional agreed"


def test_rotation_moves_the_front_of_the_queue(monkeypatch) -> None:
    """P0-①: no position may be permanently first (D-083 / Suleiman 1996).

    The queue ORDER is asserted rather than the harvest it produces: scarcity
    empties the pasture in the round it bites, so by the next round everyone is
    served zero and the outcomes stop distinguishing the orders. Order is also
    the thing rotation is actually about.
    """

    real_run_round = graph_mod.run_round
    seen: list[list[str]] = []

    def _spy(env_state, states, app, sequential=False):
        seen.append([state.agent_id for state in states])
        return real_run_round(env_state, states, app, sequential=sequential)

    monkeypatch.setattr(graph_mod, "agent_node", _stub_agent)
    monkeypatch.setattr(graph_mod, "MAX_EVENTS", 3)
    monkeypatch.setattr(graph_mod, "run_round", _spy)
    app = build_event_graph()

    run_population(
        EnvironmentState(pool=POOL_START),
        [_birth_state_named(AGENT_ID), _birth_state_named(SECOND_ID)],
        app,
        max_rounds=3,
        sequential=True,
        rotate=True,
    )
    rotated = list(seen)
    seen.clear()
    run_population(
        EnvironmentState(pool=POOL_START),
        [_birth_state_named(AGENT_ID), _birth_state_named(SECOND_ID)],
        app,
        max_rounds=3,
        sequential=True,
        rotate=False,
    )
    fixed = list(seen)

    assert len(rotated) == len(fixed) == 3
    assert len({tuple(order) for order in fixed}) == 1, "a fixed queue must not move"
    assert len({tuple(order) for order in rotated}) > 1, "rotation did not move the queue"
    assert rotated[0][0] != rotated[1][0], "the front of the queue never changed"


# ---------------------------------------------------------------------------
# D-136 — the endpoint's dimension, recorded beside the tag that hides it
# ---------------------------------------------------------------------------


def test_axis_deltas_reports_all_four_axes_not_only_the_winner() -> None:
    """⭐ The debt: `z` looks four-dimensional and has one usable dimension.

    `_primary_affected_domain` computes four swings and keeps one — the argmax.
    In C2 that argmax was `energy` or `resource` in 216 of 216 lives, so
    `social` and `uncertainty` appear nowhere in the results, and nothing in
    the file can say whether those axes never moved or moved and lost.

    Measured (§2.4-b/K5): with `_axis_deltas` returning only the winning axis,
    every other test in this file still passed.
    """

    before = InternalState(
        energy=0.5, resource_load=0.1, social_load=0.2, uncertainty_load=0.3
    )
    after = InternalState(
        energy=0.9, resource_load=0.4, social_load=0.25, uncertainty_load=0.31
    )

    deltas = graph_mod._axis_deltas(before, after)

    assert set(deltas) == {"energy", "resource", "social", "uncertainty"}
    # The losers are present AND non-zero — a report that kept the keys and
    # zeroed the values would be the same blindness with more fields.
    assert deltas["social"] == pytest.approx(0.05)
    assert deltas["uncertainty"] == pytest.approx(0.01, abs=1e-9)
    assert graph_mod._primary_affected_domain(before, after) == "energy"


def test_the_tag_is_the_argmax_of_exactly_the_recorded_swings() -> None:
    """One authority for the tag, and the row shows what it decided from.

    The split exists so a reporter never re-derives the argmax (§2.8). That is
    only safe while the dict the tag comes from IS the dict written to the row,
    so this pins them to each other on an input where three axes are live.
    """

    before = InternalState(
        energy=0.5, resource_load=0.1, social_load=0.2, uncertainty_load=0.3
    )
    after = InternalState(
        energy=0.52, resource_load=0.1, social_load=0.9, uncertainty_load=0.4
    )

    deltas = graph_mod._axis_deltas(before, after)
    tag = graph_mod._primary_affected_domain(before, after)

    assert tag == "social", "the argmax moved off the dict it is supposed to read"
    assert max(deltas, key=deltas.get) == tag


def test_a_lived_pe_row_carries_the_tag_and_the_four_swings(monkeypatch) -> None:
    """K3 — through the node that actually runs, not the helper in isolation.

    `_axis_deltas` can be correct and unreachable: the four numbers matter only
    if `prediction_error_node` puts them on the row the runners drain. This
    project has shipped "fixed in the codebase, absent from the run path" four
    times in one session (§2.4-b/K3).
    """

    monkeypatch.setattr(graph_mod, "agent_node", _stub_agent)
    monkeypatch.setattr(graph_mod, "MAX_EVENTS", LIFE_EVENTS)
    graph_mod.reset_pe_event_log()
    graph_mod.reset_pool_event_log()
    graph_mod.reset_body_event_log()

    run_population(
        EnvironmentState(pool=POOL_START),
        [_birth_state()],
        build_event_graph(),
        max_rounds=ROUND_GUARD,
    )
    rows = graph_mod.get_pe_event_log()

    assert rows, "the life produced no PE row at all"
    for row in rows:
        assert set(row["axis_deltas"]) == {
            "energy",
            "resource",
            "social",
            "uncertainty",
        }
        # The tag on the row must be one the run could actually have chosen,
        # and it must be the largest swing the same row reports.
        assert row["affected_domain"] in row["axis_deltas"]
        assert row["affected_domain"] == max(
            row["axis_deltas"], key=row["axis_deltas"].get
        )


def test_a_lived_pe_row_carries_the_axis_the_shock_was_aimed_at(monkeypatch) -> None:
    """K3 — D-137's reopening trigger has to be visible from a real run.

    The whole GAP-10 decision rests on `k` being constant, and `k` was measured
    on a STUB run because no run recorded it anywhere. A record whose central
    claim cannot be rechecked by the next run is a claim that cannot fail.

    The row's `target_domain` must be an axis the update can actually aim at —
    `energy` is a state axis but never a DAERM target, and a report that
    allowed it would be describing a universe that does not exist.
    """

    monkeypatch.setattr(graph_mod, "agent_node", _stub_agent)
    monkeypatch.setattr(graph_mod, "MAX_EVENTS", LIFE_EVENTS)
    graph_mod.reset_pe_event_log()
    graph_mod.reset_pool_event_log()
    graph_mod.reset_body_event_log()

    run_population(
        EnvironmentState(pool=POOL_START),
        [_birth_state()],
        build_event_graph(),
        max_rounds=ROUND_GUARD,
    )
    rows = graph_mod.get_pe_event_log()

    assert rows, "the life produced no PE row at all"
    for row in rows:
        assert row["target_domain"] in graph_mod.DAERM_LOAD_DOMAINS
    # ⭐ And it is NOT the same field as the tag: `k` is where the shock was
    # aimed, `affected_domain` is where the state moved most. A row that made
    # them equal by construction would hide exactly the difference D-137 turns
    # on. Measured here: the tag is `energy`, which `k` can never be.
    assert {row["target_domain"] for row in rows} != {
        row["affected_domain"] for row in rows
    }
