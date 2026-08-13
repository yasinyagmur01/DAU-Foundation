"""Production graph crisis / pool_step wiring — ADIM 1 integration tests."""

from __future__ import annotations

import pytest

import dau.foundation.graph as graph_mod
from dau.foundation.constraints import build_default_constraints
from dau.foundation.drift import DriftState
from dau.foundation.graph import (
    NODE_META_OBSERVER,
    NODE_POOL_STEP,
    build_graph,
    pool_step_node,
)
from dau.foundation.lod import CognitiveMode, LODState, NPC_ACTION_EXTRACT_MODERATE
from dau.foundation.state import DAUAgentState, Event, InternalState
from dau.society.environment import (
    POOL_CRISIS_THRESHOLD,
    EnvironmentState,
    get_pool_ratio,
    step_pool,
)
from dau.society.extraction import EXTRACTION_DEFECT, decision_to_extraction

AGENT_ID: str = "crisis-wire-0"
POOL_ABOVE_CRISIS: float = 80.0
POOL_NEAR_CRISIS: float = 25.0
MAX_EVENTS_ONE_CYCLE: int = 1
PE_STUB: float = 0.1
# Arbitrary non-zero ordinal: the row must copy the event it describes, not
# re-derive a counter of its own.
SEVENTH_EVENT: int = 7


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
