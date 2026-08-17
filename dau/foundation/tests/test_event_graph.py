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
    step_agent_once,
)
from dau.foundation.drift import DriftState
from dau.foundation.lod import (
    CognitiveMode,
    LODState,
    NPC_ACTION_EXTRACT_MODERATE,
)
from dau.foundation.state import DAUAgentState, InternalState
from dau.society.environment import EnvironmentState

AGENT_ID: str = "event-graph-0"
POOL_START: float = 80.0
ENERGY_START: float = 0.6
STUB_DECISION: str = NPC_ACTION_EXTRACT_MODERATE


def _stub_agent(state: DAUAgentState) -> dict[str, Any]:
    """Append one decision event without calling any LLM.

    Carries `energy` because the meta observer refuses a decision row without
    it — F_agent averages the energy trace and a hole would silently bias it
    (D-086, self_model.py). The stub has to honour that invariant like the real
    node does, otherwise the test would pass against a weaker contract.
    """

    event = graph_mod.build_event(
        graph_mod.EventClock(counter=len(state.event_log)),
        "agent_decision",
        {
            "decision": STUB_DECISION,
            "energy": float(state.internal_state.energy),
            "expected_outcome": {},
        },
    )
    return {"event_log": list(state.event_log) + [event]}


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
