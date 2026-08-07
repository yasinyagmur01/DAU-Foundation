"""Unit tests for Layer 3 Generation Consolidation."""

from __future__ import annotations

import pytest

from dau.foundation.constraints import build_default_constraints
from dau.foundation.drift import DriftState, update_drift
from dau.foundation.emotional_weight import (
    MARKER_LOSS,
    MARKER_THREAT,
    EmotionalWeight,
    apply_inherited_somatic_scale,
)
from dau.foundation.generation import (
    DRIFT_TRANSFER_MIN,
    GENERATION_INHERITED_KEY,
    GENERATION_MIN_RECALL,
    GENERATION_TRANSFER_THRESHOLD,
    INHERITED_WARNING_KEY,
    RECORD_ID_KEY,
    SOMATIC_SCALE_KEY,
    GenerationRecord,
    TransferCandidate,
    apply_generation,
    consolidate_generation,
    select_for_transfer,
)
from dau.generation.fitness import FITNESS_LOW_THRESHOLD, WARNING_SOMATIC_SCALE
from dau.foundation.state import DAUAgentState, DeltaRecord
from dau.memory.decay import compute_strength_init
from dau.memory.store import MemoryStore


def _delta(magnitude: float, domain: str = "resource", timestamp: int = 1) -> DeltaRecord:
    """Build a DeltaRecord with an explicit magnitude for deterministic tests."""

    snap = {
        "energy": 1.0,
        "resource_load": 0.0,
        "uncertainty_load": 0.0,
        "social_load": 0.0,
    }
    return DeltaRecord(
        timestamp=timestamp,
        magnitude=magnitude,
        affected_domain=domain,  # type: ignore[arg-type]
        snapshot_before=snap,
        snapshot_after=dict(snap),
    )


def _candidate(
    magnitude: float,
    *,
    memory_score: float,
    recall_count: int,
    domain: str = "resource",
    record_id: str = "mem-0",
) -> TransferCandidate:
    """Build a scored transfer candidate for selection tests."""

    return TransferCandidate(
        record=_delta(magnitude, domain=domain),
        record_id=record_id,
        memory_score=memory_score,
        recall_count=recall_count,
    )


def _agent(agent_id: str = "agent-0", generation: int = 0) -> DAUAgentState:
    return DAUAgentState(
        agent_id=agent_id,
        generation=generation,
        environment=build_default_constraints(),
    )


@pytest.fixture
def store(tmp_path):
    ms = MemoryStore(
        chroma_path=str(tmp_path / "chroma"),
        sqlite_path=str(tmp_path / "memory.db"),
    )
    yield ms
    ms.close()


def test_empty_memory_yields_empty_transfer() -> None:
    """No durable traces → empty inheritance package."""

    selected = select_for_transfer([], DriftState())
    assert selected == []

    package = consolidate_generation(_agent(), memory_store=None)
    assert package.inherited_memories == []
    assert package.generation == 0


def test_high_score_recalled_transfers() -> None:
    """High memory_score with at least one recall earns transfer."""

    candidate = _candidate(
        0.55,
        memory_score=GENERATION_TRANSFER_THRESHOLD,
        recall_count=GENERATION_MIN_RECALL,
        record_id="keep-me",
    )
    selected = select_for_transfer([candidate], DriftState())
    assert len(selected) == 1
    assert selected[0].record_id == "keep-me"


def test_low_score_excluded() -> None:
    """Below-threshold salience is excluded even if recalled."""

    candidate = _candidate(
        0.55,
        memory_score=GENERATION_TRANSFER_THRESHOLD - 0.01,
        recall_count=GENERATION_MIN_RECALL,
    )
    assert select_for_transfer([candidate], DriftState()) == []


def test_unrecalled_excluded() -> None:
    """Never-rehearsed traces do not transfer regardless of score."""

    candidate = _candidate(
        0.55,
        memory_score=0.95,
        recall_count=GENERATION_MIN_RECALL - 1,
    )
    assert select_for_transfer([candidate], DriftState()) == []


def test_trauma_with_low_drift_excluded() -> None:
    """Trauma transfers only when domain drift magnitude is high enough."""

    trauma = _candidate(
        0.9,
        memory_score=0.95,
        recall_count=2,
        domain="resource",
        record_id="trauma-low",
    )
    low_drift = DriftState(
        flags={"resource": True},
        magnitudes={"resource": DRIFT_TRANSFER_MIN - 0.1},
    )
    assert select_for_transfer([trauma], low_drift) == []


def test_trauma_with_high_drift_transfers() -> None:
    """Trauma that reshaped the domain enough is eligible for inheritance."""

    trauma = _candidate(
        0.9,
        memory_score=0.95,
        recall_count=2,
        domain="resource",
        record_id="trauma-high",
    )
    high_drift = DriftState(
        flags={"resource": True},
        magnitudes={"resource": DRIFT_TRANSFER_MIN},
    )
    selected = select_for_transfer([trauma], high_drift)
    assert len(selected) == 1
    assert selected[0].record_id == "trauma-high"


def test_apply_generation_sets_generation_counter() -> None:
    """Heir generation is parent generation + 1; drift and context copy over."""

    parent_drift = update_drift(DriftState(), _delta(0.8, domain="social"))
    record = GenerationRecord(
        agent_id="parent-0",
        generation=3,
        inherited_memories=["id-a", "id-b"],
        inherited_drift=parent_drift,
        transfer_timestamp=12,
    )
    heir = apply_generation(_agent("heir-0", generation=0), record, memory_store=None)

    assert heir.generation == 4
    assert heir.drift_state.flags == parent_drift.flags
    assert heir.drift_state.magnitudes == parent_drift.magnitudes
    assert heir.generation_record is record
    assert heir.retrieval_context == [
        {RECORD_ID_KEY: "id-a", GENERATION_INHERITED_KEY: True},
        {RECORD_ID_KEY: "id-b", GENERATION_INHERITED_KEY: True},
    ]


def test_consolidate_generation_selects_recalled_high_score(store) -> None:
    """End-to-end: store write + recall → consolidate keeps the earned id."""

    agent = _agent("life-0", generation=1)
    deep = _delta(0.55, domain="resource", timestamp=5)
    record_id = store.write_record(deep, agent.agent_id)
    assert record_id

    # One recall bumps strength above strength_init → recall_count >= 1.
    store.update_activation(record_id, now_counter=6)
    node = store.get_node(record_id)
    assert node is not None
    assert node.strength - compute_strength_init(deep) >= GENERATION_MIN_RECALL

    # Attach a delta so now_counter is recent (high recency → high score).
    agent.delta_log.append(_delta(0.55, timestamp=6))

    package = consolidate_generation(agent, store)
    assert package.agent_id == "life-0"
    assert package.generation == 1
    assert package.transfer_timestamp == 6
    assert record_id in package.inherited_memories


def test_apply_generation_seeds_memory_store(store) -> None:
    """With a store, apply_generation seeds heir vault under a new record id."""

    parent_id = "parent-seed-0"
    heir_id = "heir-seed-0"
    source_id = store.write_record(
        _delta(0.85, domain="resource", timestamp=3),
        parent_id,
    )
    assert source_id

    record = GenerationRecord(
        agent_id=parent_id,
        generation=0,
        inherited_memories=[source_id],
        inherited_drift=DriftState(),
        transfer_timestamp=3,
    )
    heir = apply_generation(_agent(heir_id), record, memory_store=store)

    heir_nodes = store.list_nodes(heir_id)
    assert len(heir_nodes) == 1
    seeded_id = heir_nodes[0].id
    assert seeded_id != source_id
    assert heir.retrieval_context == [
        {RECORD_ID_KEY: seeded_id, GENERATION_INHERITED_KEY: True},
    ]
    # Parent engram remains under the parent agent_id.
    assert store.get_node(source_id) is not None
    assert len(store.list_nodes(parent_id)) == 1


def test_apply_generation_remaps_warning_ids_in_retrieval_context(store) -> None:
    """Warning markers follow the seeded heir id, not the parent id."""

    parent_id = "parent-warn-0"
    heir_id = "heir-warn-0"
    source_id = store.write_record(
        _delta(0.9, domain="social", timestamp=2),
        parent_id,
    )
    assert source_id

    record = GenerationRecord(
        agent_id=parent_id,
        generation=1,
        inherited_memories=[source_id],
        inherited_warning_ids=[source_id],
        inherited_somatic_scales={source_id: -WARNING_SOMATIC_SCALE},
        transfer_timestamp=2,
    )
    heir = apply_generation(_agent(heir_id), record, memory_store=store)

    assert len(heir.retrieval_context) == 1
    entry = heir.retrieval_context[0]
    assert entry[RECORD_ID_KEY] != source_id
    assert entry[INHERITED_WARNING_KEY] is True
    assert entry[SOMATIC_SCALE_KEY] == -WARNING_SOMATIC_SCALE
    assert entry[GENERATION_INHERITED_KEY] is True
    assert store.get_node(entry[RECORD_ID_KEY]) is not None


def test_apply_generation_store_none_keeps_legacy_context_only() -> None:
    """memory_store=None keeps parent ids in retrieval_context (no vault write)."""

    record = GenerationRecord(
        agent_id="parent-0",
        generation=3,
        inherited_memories=["id-a", "id-b"],
        inherited_drift=DriftState(),
        transfer_timestamp=12,
    )
    heir = apply_generation(_agent("heir-0"), record, memory_store=None)

    assert heir.retrieval_context == [
        {RECORD_ID_KEY: "id-a", GENERATION_INHERITED_KEY: True},
        {RECORD_ID_KEY: "id-b", GENERATION_INHERITED_KEY: True},
    ]


def test_gen2_agent_receives_inherited_warning() -> None:
    """Low-F cautionary transfer → heir context + EW threat/loss dampening."""

    trauma = _candidate(
        0.9,
        memory_score=0.95,
        recall_count=GENERATION_MIN_RECALL,
        record_id="trauma-low-f",
    )
    selected = select_for_transfer(
        [trauma],
        DriftState(flags={"resource": True}, magnitudes={"resource": 2.0}),
        f_agent=FITNESS_LOW_THRESHOLD - 0.01,
    )
    assert len(selected) == 1
    assert selected[0].inherited_warning is True

    record = GenerationRecord(
        agent_id="parent-low-f",
        generation=0,
        inherited_memories=[selected[0].record_id],
        inherited_warning_ids=[selected[0].record_id],
        inherited_somatic_scales={
            selected[0].record_id: selected[0].somatic_scale,
        },
        transfer_timestamp=1,
    )
    heir = apply_generation(_agent("heir-low-f"), record, memory_store=None)
    assert heir.retrieval_context[0][INHERITED_WARNING_KEY] is True
    assert heir.retrieval_context[0][SOMATIC_SCALE_KEY] == -WARNING_SOMATIC_SCALE

    ew = EmotionalWeight(
        somatic_markers={
            MARKER_THREAT: 1.0,
            MARKER_LOSS: 1.0,
        }
    )
    scaled = apply_inherited_somatic_scale(ew, heir.retrieval_context)
    factor = 1.0 - WARNING_SOMATIC_SCALE
    assert scaled.somatic_markers[MARKER_THREAT] == pytest.approx(factor)
    assert scaled.somatic_markers[MARKER_LOSS] == pytest.approx(factor)


def test_generation_record_roundtrip_preserves_warning_fields() -> None:
    """DAUAgentState validator keeps inherited_warning_ids / somatic_scales."""

    record = GenerationRecord(
        agent_id="parent-rt",
        generation=2,
        inherited_memories=["m1"],
        inherited_warning_ids=["m1"],
        inherited_somatic_scales={"m1": -WARNING_SOMATIC_SCALE},
        transfer_timestamp=9,
    )
    heir = apply_generation(_agent("heir-rt"), record, memory_store=None)
    dumped = heir.model_dump()
    restored = DAUAgentState.model_validate(dumped)
    restored_record = restored.generation_record
    assert restored_record is not None
    assert restored_record.inherited_warning_ids == ["m1"]
    assert restored_record.inherited_somatic_scales == {
        "m1": -WARNING_SOMATIC_SCALE,
    }
    assert restored.retrieval_context[0][INHERITED_WARNING_KEY] is True
