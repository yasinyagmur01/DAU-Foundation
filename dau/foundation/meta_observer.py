"""Meta-Observer — out-of-band closed-loop control from S_self telemetry.

Biology analogy: a parallel regulatory circuit that reads only bodily and
cognitive instruments (never narrative), then nudges LOD, memory context,
drift healing, and supplementary recall. Runs after evaluator_node so Delta
is already measured; interventions take effect on the next life cycle.

No LLM calls. No randomness. Actuators are pure functions of telemetry + state.
"""

from __future__ import annotations

from dataclasses import replace
from statistics import variance
from typing import Any

from .delta import DELTA_THRESHOLD_DEEP, DELTA_THRESHOLD_NORMAL
from .drift import HEAL_THRESHOLD, DriftState, heal_drift
from .emotional_weight import MARKER_REWARD
from .lod import CognitiveMode, LODState
from .memory_bridge import retrieve_relevant
from .self_model import (
    MEMORY_SCORE_ALT_KEY,
    MEMORY_SCORE_KEY,
    M_RATIO_LOW_THRESHOLD,
    SelfModel,
    build_self_model,
)
from .state import (
    METRIC_MIN,
    AffectedDomain,
    DAUAgentState,
    DeltaRecord,
)

# ---------------------------------------------------------------------------
# Meta-Observer actuator thresholds (no magic numbers in logic)
# ---------------------------------------------------------------------------

META_LOD_OVERRIDE_ENABLED: bool = True

META_RETRIEVAL_VARIANCE_THRESHOLD: float = 0.3
META_RETRIEVAL_MIN_SCORE: float = 0.4

META_DRIFT_HEAL_FITNESS_THRESHOLD: float = 0.5
META_DRIFT_HEAL_REWARD_MIN: float = 0.4

META_HEAL_TIMESTAMP: int = 0
MIN_VARIANCE_SAMPLE_SIZE: int = 2
DEFAULT_RETRIEVAL_DOMAIN: str = "uncertainty"

# Empty vital panel for synthetic heal deltas (heal_drift ignores snapshots).
HEAL_SNAPSHOT_ENERGY: float = METRIC_MIN
HEAL_SNAPSHOT_RESOURCE_LOAD: float = METRIC_MIN
HEAL_SNAPSHOT_UNCERTAINTY_LOAD: float = METRIC_MIN
HEAL_SNAPSHOT_SOCIAL_LOAD: float = METRIC_MIN

# Optional vault handles — graph may bind the same store as agent_node.
# Kept out of DAUAgentState (Pydantic cannot serialize MemoryStore).
_meta_memory_stores: dict[str, Any] = {}

VALID_AFFECTED_DOMAINS: frozenset[str] = frozenset(
    {"energy", "resource", "social", "uncertainty"}
)


def bind_memory_store(agent_id: str, store: Any) -> None:
    """Register a durable memory vault for supplementary retrieval."""

    _meta_memory_stores[str(agent_id)] = store


def unbind_memory_store(agent_id: str) -> None:
    """Drop a previously bound vault handle (tests / run teardown)."""

    _meta_memory_stores.pop(str(agent_id), None)


def _entry_memory_score(entry: dict[str, Any]) -> float | None:
    """Read memory_score or Layer-1 score key; None if absent."""

    if MEMORY_SCORE_KEY in entry:
        return float(entry[MEMORY_SCORE_KEY])
    if MEMORY_SCORE_ALT_KEY in entry:
        return float(entry[MEMORY_SCORE_ALT_KEY])
    return None


def _score_variance(scores: list[float]) -> float:
    """Sample variance; zero when fewer than two scores exist.

    Sample (not population) variance is required: unit-interval scores have
    population variance ≤ 0.25, so META_RETRIEVAL_VARIANCE_THRESHOLD=0.3
    would never fire under pvariance.
    """

    if len(scores) < MIN_VARIANCE_SAMPLE_SIZE:
        return METRIC_MIN
    return float(variance(scores))


def _reward_marker(self_model: SelfModel) -> float:
    """Reward somatic marker — Layer 2 stores it under somatic_markers only."""

    return float(
        self_model.emotional_weight.somatic_markers.get(MARKER_REWARD, METRIC_MIN)
    )


def _ensure_lod(state: DAUAgentState) -> LODState:
    """Birth-default LOD when lod_state is unset."""

    lod = state.lod_state
    if isinstance(lod, LODState):
        return lod
    return LODState()


def _ensure_drift(state: DAUAgentState) -> DriftState:
    """Birth-default drift when drift_state is unset or wrong type."""

    drift = state.drift_state
    if isinstance(drift, DriftState):
        return DriftState(
            flags=dict(drift.flags),
            magnitudes=dict(drift.magnitudes),
        )
    return DriftState()


def _current_delta_domain(state: DAUAgentState) -> str:
    """Query key for supplementary retrieval — latest delta domain."""

    if state.delta_log:
        return str(state.delta_log[-1].affected_domain)
    return DEFAULT_RETRIEVAL_DOMAIN


def _heal_snapshot() -> dict[str, float]:
    """Deterministic empty vital panel for metacognitive heal deltas."""

    return {
        "energy": HEAL_SNAPSHOT_ENERGY,
        "resource_load": HEAL_SNAPSHOT_RESOURCE_LOAD,
        "uncertainty_load": HEAL_SNAPSHOT_UNCERTAINTY_LOAD,
        "social_load": HEAL_SNAPSHOT_SOCIAL_LOAD,
    }


def _healing_delta(domain: AffectedDomain) -> DeltaRecord:
    """Strong non-trauma delta that satisfies heal_drift gates (mag ≥ HEAL_THRESHOLD)."""

    snap = _heal_snapshot()
    return DeltaRecord(
        timestamp=META_HEAL_TIMESTAMP,
        magnitude=HEAL_THRESHOLD,
        affected_domain=domain,
        snapshot_before=dict(snap),
        snapshot_after=dict(snap),
    )


def lod_override(self_model: SelfModel, lod_state: LODState) -> LODState:
    """Force System 2 when deep delta coincides with low metacognitive calibration.

    Condition: delta_current ≥ DELTA_THRESHOLD_DEEP AND m_ratio < M_RATIO_LOW_THRESHOLD.
    Action: mode → CognitiveMode.SYSTEM_2 regardless of T_cognitive formula.
    """

    if not META_LOD_OVERRIDE_ENABLED:
        return lod_state
    if (
        self_model.delta_current >= DELTA_THRESHOLD_DEEP
        and self_model.m_ratio < M_RATIO_LOW_THRESHOLD
    ):
        return replace(lod_state, mode=CognitiveMode.SYSTEM_2)
    return lod_state


def context_prune(
    retrieval_context: list[dict[str, Any]],
    self_model: SelfModel,
) -> list[dict[str, Any]]:
    """Drop low-score retrieval entries when retrieval-score variance is high.

    Condition: variance(memory_retrieval_scores) > META_RETRIEVAL_VARIANCE_THRESHOLD.
    Action: remove entries with memory_score < META_RETRIEVAL_MIN_SCORE.
    Entries without a score key are kept (e.g. inheritance refs).
    """

    context = list(retrieval_context)
    if _score_variance(self_model.memory_retrieval_scores) <= (
        META_RETRIEVAL_VARIANCE_THRESHOLD
    ):
        return context

    pruned: list[dict[str, Any]] = []
    for entry in context:
        if not isinstance(entry, dict):
            continue
        score = _entry_memory_score(entry)
        if score is None or score >= META_RETRIEVAL_MIN_SCORE:
            pruned.append(entry)
    return pruned


def trigger_drift_healing(
    drift_state: DriftState,
    self_model: SelfModel,
) -> DriftState:
    """Call heal_drift on flagged domains when fitness is low but reward is present.

    Condition: any flag True AND f_agent < fitness threshold AND reward > min.
    Action: heal_drift() once per flagged domain with a HEAL_THRESHOLD delta.
    """

    any_flagged = any(bool(flag) for flag in drift_state.flags.values())
    reward = _reward_marker(self_model)
    if not (
        any_flagged
        and self_model.f_agent < META_DRIFT_HEAL_FITNESS_THRESHOLD
        and reward > META_DRIFT_HEAL_REWARD_MIN
    ):
        return DriftState(
            flags=dict(drift_state.flags),
            magnitudes=dict(drift_state.magnitudes),
        )

    healed = DriftState(
        flags=dict(drift_state.flags),
        magnitudes=dict(drift_state.magnitudes),
    )
    for domain, flagged in list(healed.flags.items()):
        if not flagged:
            continue
        if domain not in VALID_AFFECTED_DOMAINS:
            continue
        healed = heal_drift(healed, _healing_delta(domain))  # type: ignore[arg-type]
    return healed


def trigger_retrieval(
    state: DAUAgentState,
    self_model: SelfModel,
) -> list[dict[str, Any]]:
    """Append supplementary domain-cued memories when calibration is low.

    Condition: m_ratio < M_RATIO_LOW_THRESHOLD AND delta_current ≥ NORMAL.
    Action: Chroma/domain retrieval via bound MemoryStore; append to context.
    With no bound store, context is returned unchanged (deterministic no-op).
    """

    context = list(state.retrieval_context)
    if not (
        self_model.m_ratio < M_RATIO_LOW_THRESHOLD
        and self_model.delta_current >= DELTA_THRESHOLD_NORMAL
    ):
        return context

    store = _meta_memory_stores.get(str(state.agent_id))
    if store is None:
        return context

    supplements = retrieve_relevant(
        query_domain=_current_delta_domain(state),
        agent_id=state.agent_id,
        now_counter=len(state.event_log),
        store=store,
    )
    return context + list(supplements)


def meta_observer_node(state: DAUAgentState) -> dict[str, Any]:
    """Build S_self, run four actuators in order, persist SelfModel on state.

    Order: lod_override → context_prune → trigger_drift_healing → trigger_retrieval.
    Returns a LangGraph partial update dict (same pattern as evaluator_node).
    Pure w.r.t. agent state given a fixed bound memory store.
    """

    print(f"[META] meta_observer_node called, event={len(state.event_log)}")

    self_model = build_self_model(state)

    lod = lod_override(self_model, _ensure_lod(state))
    context = context_prune(list(state.retrieval_context), self_model)
    drift = trigger_drift_healing(_ensure_drift(state), self_model)

    interim = state.model_copy(
        update={
            "lod_state": lod,
            "retrieval_context": context,
            "drift_state": drift,
        }
    )
    context = trigger_retrieval(interim, self_model)

    updated = state.model_copy(
        update={
            "lod_state": lod,
            "retrieval_context": context,
            "drift_state": drift,
        }
    )
    final_self = build_self_model(updated)

    return {
        "lod_state": lod,
        "retrieval_context": context,
        "drift_state": drift,
        "self_model": final_self,
    }


if __name__ == "__main__":
    from .constraints import build_default_constraints

    demo = DAUAgentState(
        agent_id="meta-observer-demo-0",
        environment=build_default_constraints(),
    )
    patch = meta_observer_node(demo)
    print(
        f"OK — meta_observer_node; self_model={patch['self_model'] is not None}, "
        f"mode={patch['lod_state'].mode}, "
        f"context_len={len(patch['retrieval_context'])}"
    )
