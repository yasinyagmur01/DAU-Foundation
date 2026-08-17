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
