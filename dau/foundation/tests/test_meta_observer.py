"""Unit tests for Layer 5 metacognition — SelfModel + Meta-Observer actuators."""

from __future__ import annotations

from statistics import fmean

import pytest

from dau.foundation.constraints import build_default_constraints
from dau.foundation.delta import DELTA_THRESHOLD_DEEP, DELTA_THRESHOLD_NORMAL
from dau.foundation.drift import HEAL_RATE, HEAL_THRESHOLD, DriftState
from dau.foundation.emotional_weight import MARKER_REWARD, EmotionalWeight
from dau.foundation.generation import (
    GENERATION_INHERITED_KEY,
    INHERITED_WARNING_KEY,
    RECORD_ID_KEY,
    SOMATIC_SCALE_KEY,
)
from dau.foundation.lod import CognitiveMode, LODState
from dau.foundation.meta_observer import (
    META_DRIFT_HEAL_FITNESS_THRESHOLD,
    META_DRIFT_HEAL_REWARD_MIN,
    META_RETRIEVAL_MIN_SCORE,
    META_RETRIEVAL_VARIANCE_THRESHOLD,
    bind_memory_store,
    context_prune,
    lod_override,
    meta_observer_node,
    trigger_drift_healing,
    trigger_retrieval,
    unbind_memory_store,
)
from dau.generation.fitness import WARNING_SOMATIC_SCALE
from dau.foundation.self_model import (
    EPSILON,
    M_RATIO_LOW_THRESHOLD,
    SelfModel,
    build_self_model,
)
from dau.foundation.state import DAUAgentState, DeltaRecord, Event, InternalState


def _snap() -> dict[str, float]:
    return {
        "energy": 1.0,
        "resource_load": 0.0,
        "uncertainty_load": 0.0,
        "social_load": 0.0,
    }


T_GENERATION_UNIT: int = 20  # F_agent's survival denominator (K4-b, D-070)
EVENTS_LIVED_UNIT: int = 4
BUDGET_SHORT: int = 8
BUDGET_LONG: int = 40
EVENT_TYPE_UNIT: str = "meta-budget-probe"


def _delta(magnitude: float, domain: str = "resource") -> DeltaRecord:
    snap = _snap()
    return DeltaRecord(
        timestamp=1,
        magnitude=magnitude,
        affected_domain=domain,  # type: ignore[arg-type]
        snapshot_before=snap,
        snapshot_after=dict(snap),
    )


def _self_model(
    *,
    delta_current: float,
    delta_history: list[float],
    drift_state: DriftState | None = None,
    emotional_weight: EmotionalWeight | None = None,
    t_cognitive: float = 0.0,
    memory_retrieval_scores: list[float] | None = None,
    f_agent: float = 0.9,
    generation_count: int = 0,
) -> SelfModel:
    return SelfModel(
        delta_current=delta_current,
        delta_history=list(delta_history),
        drift_state=drift_state if drift_state is not None else DriftState(),
        emotional_weight=(
            emotional_weight if emotional_weight is not None else EmotionalWeight()
        ),
        t_cognitive=t_cognitive,
        memory_retrieval_scores=(
            list(memory_retrieval_scores)
            if memory_retrieval_scores is not None
            else []
        ),
        f_agent=f_agent,
        generation_count=generation_count,
    )


def test_self_model_builds_from_valid_state() -> None:
    """build_self_model consolidates delta, LOD, scores, and generation."""

    state = DAUAgentState(
        agent_id="meta-build-0",
        environment=build_default_constraints(),
        generation=2,
        internal_state=InternalState(energy=0.8),
        delta_log=[_delta(0.4), _delta(0.55)],
        lod_state=LODState(mode=CognitiveMode.SYSTEM_2, t_cognitive=0.72),
        retrieval_context=[
            {"score": 0.7},
            {"memory_score": 0.5},
        ],
        drift_state=DriftState(
            flags={"resource": True},
            magnitudes={"resource": 0.8},
        ),
    )
    model = build_self_model(state, T_GENERATION_UNIT)

    assert model.delta_current == pytest.approx(0.55)
    assert model.delta_history == pytest.approx([0.4, 0.55])
    assert model.t_cognitive == pytest.approx(0.72)
    assert model.generation_count == 2
    assert model.memory_retrieval_scores == pytest.approx([0.7, 0.5])
    assert model.drift_state.flags["resource"] is True
    assert model.f_agent >= 0.0
    assert isinstance(model.emotional_weight, EmotionalWeight)


def test_m_ratio_computes_correctly() -> None:
    """m_ratio = mean(delta_history) / (delta_current + EPSILON)."""

    history = [0.4, 0.6]
    current = 0.5
    model = _self_model(delta_current=current, delta_history=history)
    expected = fmean(history) / (current + EPSILON)
    assert model.m_ratio == pytest.approx(expected)


def test_m_ratio_epsilon_edge_case_zero_delta_current() -> None:
    """delta_current=0 uses EPSILON so m_ratio stays finite."""

    history = [0.5, 0.5]
    model = _self_model(delta_current=0.0, delta_history=history)
    expected = fmean(history) / EPSILON
    assert model.m_ratio == pytest.approx(expected)
    assert model.m_ratio > 0.0


def test_lod_override_triggers_when_both_conditions_met() -> None:
    """Deep delta + low m_ratio forces SYSTEM_2."""

    model = _self_model(
        delta_current=DELTA_THRESHOLD_DEEP,
        delta_history=[0.2, 0.2],
    )
    assert model.m_ratio < M_RATIO_LOW_THRESHOLD
    lod = LODState(mode=CognitiveMode.SYSTEM_1, t_cognitive=0.1)
    result = lod_override(model, lod)
    assert result.mode == CognitiveMode.SYSTEM_2
    assert lod.mode == CognitiveMode.SYSTEM_1


def test_lod_override_does_not_trigger_when_only_delta_met() -> None:
    """Deep delta alone (m_ratio healthy) leaves mode unchanged."""

    model = _self_model(
        delta_current=DELTA_THRESHOLD_DEEP,
        delta_history=[0.7, 0.7],
    )
    assert model.m_ratio >= M_RATIO_LOW_THRESHOLD
    lod = LODState(mode=CognitiveMode.SYSTEM_1)
    result = lod_override(model, lod)
    assert result.mode == CognitiveMode.SYSTEM_1


def test_lod_override_does_not_trigger_when_only_m_ratio_met() -> None:
    """Low m_ratio alone (delta below DEEP) leaves mode unchanged."""

    model = _self_model(
        delta_current=DELTA_THRESHOLD_NORMAL,
        delta_history=[0.1, 0.1],
    )
    assert model.delta_current < DELTA_THRESHOLD_DEEP
    assert model.m_ratio < M_RATIO_LOW_THRESHOLD
    lod = LODState(mode=CognitiveMode.SYSTEM_1)
    result = lod_override(model, lod)
    assert result.mode == CognitiveMode.SYSTEM_1


def test_context_prune_removes_low_scores_when_variance_high() -> None:
    """High retrieval-score variance drops entries below min score."""

    scores = [0.0, 1.0]
    from statistics import variance

    assert variance(scores) > META_RETRIEVAL_VARIANCE_THRESHOLD

    model = _self_model(
        delta_current=0.0,
        delta_history=[],
        memory_retrieval_scores=scores,
    )
    context = [
        {"score": 0.1},
        {"score": 0.9},
        {"memory_score": 0.2},
        {"id": "keep-no-score"},
    ]
    pruned = context_prune(context, model)
    assert {"score": 0.9} in pruned
    assert {"id": "keep-no-score"} in pruned
    assert {"score": 0.1} not in pruned
    assert {"memory_score": 0.2} not in pruned
    assert all(
        (
            entry.get("score", entry.get("memory_score", META_RETRIEVAL_MIN_SCORE))
            >= META_RETRIEVAL_MIN_SCORE
            or "id" in entry
        )
        for entry in pruned
    )


def test_context_prune_does_not_prune_when_variance_low() -> None:
    """Low variance leaves retrieval_context untouched."""

    scores = [0.50, 0.51]
    from statistics import variance

    assert variance(scores) <= META_RETRIEVAL_VARIANCE_THRESHOLD

    model = _self_model(
        delta_current=0.0,
        delta_history=[],
        memory_retrieval_scores=scores,
    )
    context = [{"score": 0.1}, {"score": 0.9}]
    assert context_prune(context, model) == context


def test_context_prune_keeps_generation_inherited_entries() -> None:
    """Score-less generation_inherited / cautionary refs survive high-variance prune."""

    scores = [0.0, 1.0]
    from statistics import variance

    assert variance(scores) > META_RETRIEVAL_VARIANCE_THRESHOLD

    inherited = {
        RECORD_ID_KEY: "heir-engram",
        GENERATION_INHERITED_KEY: True,
        INHERITED_WARNING_KEY: True,
        SOMATIC_SCALE_KEY: -WARNING_SOMATIC_SCALE,
    }
    model = _self_model(
        delta_current=0.0,
        delta_history=[],
        memory_retrieval_scores=scores,
    )
    context = [
        {"score": 0.1},
        inherited,
        {"score": 0.9},
    ]
    pruned = context_prune(context, model)
    assert inherited in pruned
    assert {"score": 0.1} not in pruned
    assert {"score": 0.9} in pruned


def test_trigger_drift_healing_activates_when_all_conditions_met() -> None:
    """Flagged domain + low fitness + high reward → heal_drift reduces magnitude."""

    initial_mag = 1.0
    drift = DriftState(
        flags={"resource": True},
        magnitudes={"resource": initial_mag},
    )
    model = _self_model(
        delta_current=0.0,
        delta_history=[],
        drift_state=drift,
        f_agent=META_DRIFT_HEAL_FITNESS_THRESHOLD - 0.1,
        emotional_weight=EmotionalWeight(
            somatic_markers={MARKER_REWARD: META_DRIFT_HEAL_REWARD_MIN + 0.1}
        ),
    )
    healed = trigger_drift_healing(drift, model)
    expected = initial_mag - HEAL_THRESHOLD * HEAL_RATE
    assert healed.magnitudes["resource"] == pytest.approx(expected)
    assert healed.flags["resource"] is True


def test_trigger_drift_healing_does_not_activate_when_reward_too_low() -> None:
    """Reward at or below threshold leaves drift magnitudes unchanged."""

    drift = DriftState(
        flags={"resource": True},
        magnitudes={"resource": 1.0},
    )
    model = _self_model(
        delta_current=0.0,
        delta_history=[],
        drift_state=drift,
        f_agent=META_DRIFT_HEAL_FITNESS_THRESHOLD - 0.1,
        emotional_weight=EmotionalWeight(
            somatic_markers={MARKER_REWARD: META_DRIFT_HEAL_REWARD_MIN}
        ),
    )
    healed = trigger_drift_healing(drift, model)
    assert healed.magnitudes["resource"] == pytest.approx(1.0)
    assert healed.flags["resource"] is True


def test_trigger_retrieval_fires_when_m_ratio_low_and_delta_sufficient(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Low m_ratio + delta ≥ NORMAL appends supplementary retrieval results."""

    supplements = [
        {
            "domain": "resource",
            "magnitude": 0.55,
            "classification": "DEEP",
            "score": 0.88,
            "drift_flag": False,
        }
    ]
    monkeypatch.setattr(
        "dau.foundation.meta_observer.retrieve_relevant",
        lambda **_kwargs: list(supplements),
    )
    agent_id = "meta-ret-fire-0"
    bind_memory_store(agent_id, object())
    try:
        model = _self_model(
            delta_current=DELTA_THRESHOLD_NORMAL,
            delta_history=[0.1, 0.1],
        )
        assert model.m_ratio < M_RATIO_LOW_THRESHOLD
        state = DAUAgentState(
            agent_id=agent_id,
            environment=build_default_constraints(),
            retrieval_context=[{"existing": True}],
            delta_log=[_delta(DELTA_THRESHOLD_NORMAL)],
        )
        result = trigger_retrieval(state, model)
        assert result[0] == {"existing": True}
        assert result[1] == supplements[0]
        assert len(result) == 2
    finally:
        unbind_memory_store(agent_id)


def test_trigger_retrieval_noop_when_memory_store_unbound(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Low m_ratio + sufficient delta still no-ops if no store is bound.

    Diagnostic (audit Adım 2): silent no-op must stay deterministic so
    Meta-Observer A/B does not mis-attribute missing retrieval to control.
    """

    def _fail_retrieve(**_kwargs: object) -> list[dict[str, object]]:
        raise AssertionError("retrieve_relevant must not run without bound store")

    monkeypatch.setattr(
        "dau.foundation.meta_observer.retrieve_relevant",
        _fail_retrieve,
    )
    agent_id = "meta-ret-unbound-0"
    unbind_memory_store(agent_id)
    model = _self_model(
        delta_current=DELTA_THRESHOLD_NORMAL,
        delta_history=[0.1, 0.1],
    )
    assert model.m_ratio < M_RATIO_LOW_THRESHOLD
    existing = {"existing": True}
    state = DAUAgentState(
        agent_id=agent_id,
        environment=build_default_constraints(),
        retrieval_context=[existing],
        delta_log=[_delta(DELTA_THRESHOLD_NORMAL)],
    )
    result = trigger_retrieval(state, model)
    assert result == [existing]
    assert len(result) == 1


def test_meta_observer_node_returns_dict_with_expected_keys() -> None:
    """Node returns lod_state, retrieval_context, drift_state, self_model."""

    state = DAUAgentState(
        agent_id="meta-node-0",
        environment=build_default_constraints(),
        delta_log=[_delta(0.45)],
        lod_state=LODState(),
    )
    patch = meta_observer_node(state)
    assert set(patch.keys()) == {
        "lod_state",
        "retrieval_context",
        "drift_state",
        "self_model",
    }
    assert isinstance(patch["lod_state"], LODState)
    assert isinstance(patch["retrieval_context"], list)
    assert isinstance(patch["drift_state"], DriftState)
    assert isinstance(patch["self_model"], SelfModel)
    assert patch["self_model"].delta_current == pytest.approx(0.45)


def test_meta_observer_reads_the_live_event_budget(monkeypatch) -> None:
    """F_agent's survival term follows graph.MAX_EVENTS as the runner sets it.

    The node cannot be handed the budget — LangGraph fixes its signature at
    (state) -> dict — so it reads the graph global that should_continue ends
    the life on. Two failure modes this guards: binding MAX_EVENTS at import
    time (every runner rebinds it around a life, so an import-time read
    freezes the module default in and scores a 50-event life against 20), and
    falling back to the agent's own lifespan, which pins the term at 1.0.
    """

    from dau.foundation import graph as graph_mod

    state = DAUAgentState(
        agent_id="meta-budget-0",
        environment=build_default_constraints(),
        delta_log=[_delta(0.45)],
        lod_state=LODState(),
        event_log=[
            Event(event_type=EVENT_TYPE_UNIT) for _ in range(EVENTS_LIVED_UNIT)
        ],
    )

    monkeypatch.setattr(graph_mod, "MAX_EVENTS", BUDGET_SHORT)
    against_short = meta_observer_node(state)["self_model"].f_agent
    monkeypatch.setattr(graph_mod, "MAX_EVENTS", BUDGET_LONG)
    against_long = meta_observer_node(state)["self_model"].f_agent

    # Same life, same body, same ledger — only the span it is measured
    # against differs, and surviving 4 of 8 beats surviving 4 of 40.
    assert against_short > against_long
