"""Generation consolidation — inheritance of earned traces across lifecycles.

Biology analogy: when one life ends, only what was used and strong enough
passes to the next generation. Trauma scars transfer only if they reshaped
the organism enough to matter. Packaging inheritance is not birth — the
new agent is created elsewhere and then receives this package.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from dau.memory.decay import compute_strength_init
from dau.memory.retrieval import compute_memory_score

from .delta import is_trauma
from .drift import DriftState
from .state import DAUAgentState, DeltaRecord

# ---------------------------------------------------------------------------
# Generation transfer thresholds (no magic numbers in logic)
# ---------------------------------------------------------------------------

GENERATION_TRANSFER_THRESHOLD: float = 0.6
GENERATION_MIN_RECALL: int = 1
DRIFT_TRANSFER_MIN: float = 1.5

RETRIEVAL_CONTEXT_ATTR: str = "retrieval_context"
GENERATION_INHERITED_KEY: str = "generation_inherited"
RECORD_ID_KEY: str = "record_id"


@dataclass
class TransferCandidate:
    """A scored durable memory considered for generational transfer.

    Biology analogy: an engram card pulled from the vault with its rehearsal
    count and current salience attached — selection needs more than the raw
    physiological delta alone.
    """

    record: DeltaRecord
    record_id: str
    memory_score: float
    recall_count: int


@dataclass
class GenerationRecord:
    """Immutable inheritance package from one lifecycle to the next.

    Biology analogy: the will of a finished life — which engrams earned
    survival, which domain scars remain, and when the transfer was sealed.
    Does not create the heir; it only packages what may be inherited.
    """

    agent_id: str
    generation: int = 0
    inherited_memories: list[str] = field(default_factory=list)
    inherited_drift: DriftState = field(default_factory=DriftState)
    transfer_timestamp: int = 0


def select_for_transfer(
    memories: list[TransferCandidate],
    drift_state: DriftState,
) -> list[TransferCandidate]:
    """Keep only memories that earned survival into the next generation.

    Biology analogy: natural selection over engrams — high salience, at least
    one rehearsal, and trauma only if it scarred the decision surface enough.
    """

    selected: list[TransferCandidate] = []
    for candidate in memories:
        if candidate.memory_score < GENERATION_TRANSFER_THRESHOLD:
            continue
        if candidate.recall_count < GENERATION_MIN_RECALL:
            continue
        if is_trauma(candidate.record):
            domain = str(candidate.record.affected_domain)
            drift_magnitude = float(
                drift_state.magnitudes.get(domain, 0.0)
            )
            if drift_magnitude < DRIFT_TRANSFER_MIN:
                continue
        selected.append(candidate)
    return selected


def _now_counter_from_state(agent_state: DAUAgentState) -> int:
    """Derive the current event ordinal from lived logs."""

    stamps: list[int] = []
    for event in agent_state.event_log:
        stamps.append(int(event.timestamp))
    for delta in agent_state.delta_log:
        stamps.append(int(delta.timestamp))
    if not stamps:
        return 0
    return max(stamps)


def _candidates_from_store(
    agent_id: str,
    now_counter: int,
    memory_store: Any,
) -> list[TransferCandidate]:
    """Score every durable node for this agent into transfer candidates."""

    if memory_store is None:
        return []

    candidates: list[TransferCandidate] = []
    for node in memory_store.list_nodes(agent_id):
        record = memory_store.get_record_payload(node.id)
        if record is None:
            # Reconstruct a minimal DeltaRecord from the SQLite index card.
            snap = {
                "energy": 1.0,
                "resource_load": 0.0,
                "uncertainty_load": 0.0,
                "social_load": 0.0,
            }
            record = DeltaRecord(
                timestamp=int(node.timestamp),
                magnitude=float(node.magnitude),
                affected_domain=node.domain,  # type: ignore[arg-type]
                snapshot_before=snap,
                snapshot_after=dict(snap),
            )

        strength_init = compute_strength_init(record)
        recall_count = max(0, int(node.strength) - int(strength_init))
        score = compute_memory_score(
            node.id,
            node.domain,
            now_counter,
            memory_store,
        )
        candidates.append(
            TransferCandidate(
                record=record,
                record_id=str(node.id),
                memory_score=float(score),
                recall_count=int(recall_count),
            )
        )
    return candidates


def consolidate_generation(
    agent_state: DAUAgentState,
    memory_store: Any,
) -> GenerationRecord:
    """Package earned memories and current drift for the next generation.

    Biology analogy: end-of-life consolidation — inventory the vault, keep
    what survived selection pressure, seal the scar map. Does not birth the
    heir; only prepares the inheritance.
    """

    now_counter = _now_counter_from_state(agent_state)
    candidates = _candidates_from_store(
        agent_state.agent_id,
        now_counter,
        memory_store,
    )
    drift = agent_state.drift_state
    if not isinstance(drift, DriftState):
        drift = DriftState()

    selected = select_for_transfer(candidates, drift)
    return GenerationRecord(
        agent_id=agent_state.agent_id,
        generation=int(agent_state.generation),
        inherited_memories=[c.record_id for c in selected],
        inherited_drift=DriftState(
            flags=dict(drift.flags),
            magnitudes=dict(drift.magnitudes),
        ),
        transfer_timestamp=now_counter,
    )


def apply_generation(
    new_agent_state: DAUAgentState,
    record: GenerationRecord,
    memory_store: Any,
) -> DAUAgentState:
    """Apply an inheritance package onto a newly created agent state.

    Biology analogy: the heir receives scarred niches and the engrams that
    earned transfer — lineage age advances by one. memory_store is reserved
    for future vault re-binding; selection IDs already live on the record.
    """

    _ = memory_store  # vault re-binding reserved for later wiring

    inherited_drift = DriftState(
        flags=dict(record.inherited_drift.flags),
        magnitudes=dict(record.inherited_drift.magnitudes),
    )
    retrieval_context: list[dict[str, Any]] = [
        {
            RECORD_ID_KEY: memory_id,
            GENERATION_INHERITED_KEY: True,
        }
        for memory_id in record.inherited_memories
    ]
    return new_agent_state.model_copy(
        update={
            "generation": int(record.generation) + 1,
            "drift_state": inherited_drift,
            "retrieval_context": retrieval_context,
            "generation_record": record,
        }
    )


if __name__ == "__main__":
    from .constraints import build_default_constraints

    empty_state = DAUAgentState(
        agent_id="gen-demo-0",
        environment=build_default_constraints(),
    )
    package = consolidate_generation(empty_state, memory_store=None)
    print(
        f"empty_transfer memories={package.inherited_memories} "
        f"generation={package.generation}"
    )
    heir = DAUAgentState(
        agent_id="gen-demo-1",
        environment=build_default_constraints(),
    )
    applied = apply_generation(heir, package, memory_store=None)
    print(f"heir_generation={applied.generation}")
    print("OK — generation demo complete")
