"""Vault clock across lives — GAP-19 / D-067."""

from __future__ import annotations

import pytest

from dau.foundation.state import DeltaRecord
from dau.memory.consolidation import run_consolidation
from dau.memory.retrieval import compute_memory_score
from dau.memory.store import MemoryStore

# ---------------------------------------------------------------------------
# GAP-19 / D-067 — two lives, one vault, one clock
# ---------------------------------------------------------------------------

PHASE_EVENTS: int = 50
LATE_PHASE1_EVENT: int = 48


def _deep_record(timestamp: int) -> DeltaRecord:
    """A DEEP-class delta, i.e. one that actually reaches durable storage."""

    snap = {
        "energy": 1.0,
        "resource_load": 0.0,
        "uncertainty_load": 0.0,
        "social_load": 0.0,
    }
    return DeltaRecord(
        timestamp=timestamp,
        magnitude=0.55,
        affected_domain="resource",
        snapshot_before=snap,
        snapshot_after={
            "energy": 0.45,
            "resource_load": 0.55,
            "uncertainty_load": 0.0,
            "social_load": 0.0,
        },
    )


def test_new_vault_starts_at_zero_base(tmp_path) -> None:
    """A vault that has seen one life only is unchanged (demo path)."""

    store = MemoryStore(
        chroma_path=str(tmp_path / "chroma"),
        sqlite_path=str(tmp_path / "m.db"),
    )
    try:
        assert store.vault_counter(LATE_PHASE1_EVENT) == LATE_PHASE1_EVENT
    finally:
        store.close()


def test_second_life_on_the_same_vault_does_not_reuse_phase_one_ordinals(
    tmp_path,
) -> None:
    """The bug: an event-48 memory from each phase looked the same age.

    Phase-2 opens with an empty event log and counts from zero again while
    sharing the vault, so Ebbinghaus read t=2 for a trace that was really 52
    events old (D-051).
    """

    store = MemoryStore(
        chroma_path=str(tmp_path / "chroma"),
        sqlite_path=str(tmp_path / "m.db"),
    )
    try:
        first = store.write_record(_deep_record(LATE_PHASE1_EVENT), "agent")
        store.seal_phase(PHASE_EVENTS)
        second = store.write_record(_deep_record(LATE_PHASE1_EVENT), "agent")

        old = store.get_node(first)
        fresh = store.get_node(second)
        assert old is not None and fresh is not None
        assert old.last_activated_counter == LATE_PHASE1_EVENT
        assert fresh.last_activated_counter == PHASE_EVENTS + LATE_PHASE1_EVENT
        assert fresh.last_activated_counter > old.last_activated_counter
    finally:
        store.close()


def test_recall_in_the_second_life_stamps_the_vault_clock(tmp_path) -> None:
    """A phase-local recall counter must not rewind the vault's clock."""

    store = MemoryStore(
        chroma_path=str(tmp_path / "chroma"),
        sqlite_path=str(tmp_path / "m.db"),
    )
    try:
        record_id = store.write_record(_deep_record(LATE_PHASE1_EVENT), "agent")
        store.seal_phase(PHASE_EVENTS)
        store.update_activation(record_id, now_counter=1)

        node = store.get_node(record_id)
        assert node is not None
        assert node.last_activated_counter == PHASE_EVENTS + 1
    finally:
        store.close()


def test_sleep_judges_a_first_life_memory_by_its_real_age(tmp_path) -> None:
    """The Ebbinghaus half of GAP-19: t was read as 2 where the truth was 52.

    A DEEP trace last touched at event 48 of phase-1, judged at the end of a
    50-event phase-2, is 52 events old and decays past R_MIN. On the broken
    clock it looked 2 events old and survived — which is exactly the decision
    that reaches the heir through what gets consolidated.
    """

    store = MemoryStore(
        chroma_path=str(tmp_path / "chroma"),
        sqlite_path=str(tmp_path / "m.db"),
    )
    try:
        record_id = store.write_record(_deep_record(LATE_PHASE1_EVENT), "agent")
        store.seal_phase(PHASE_EVENTS)

        report = run_consolidation("agent", now_counter=PHASE_EVENTS, store=store)

        assert store.get_node(record_id) is None
        assert report.deleted_count == 1
    finally:
        store.close()


def test_recall_is_invariant_to_which_life_the_agent_is_living(tmp_path) -> None:
    """Retrieval reads the same clock as sleep does.

    The same trace, written 2 events before the end of its own phase and
    recalled at that phase's end, must score identically whether that phase is
    the first or the second. On the un-translated clock the second life's node
    is stamped past the counter it is scored against, retention comes out
    above 1.0, and the recency term rewards a memory for being in the future.
    """

    store = MemoryStore(
        chroma_path=str(tmp_path / "chroma"),
        sqlite_path=str(tmp_path / "m.db"),
    )
    try:
        in_first_life = store.write_record(_deep_record(LATE_PHASE1_EVENT), "agent")
        score_first = compute_memory_score(
            in_first_life, "resource", PHASE_EVENTS, store
        )

        store.seal_phase(PHASE_EVENTS)
        in_second_life = store.write_record(_deep_record(LATE_PHASE1_EVENT), "agent")
        score_second = compute_memory_score(
            in_second_life, "resource", PHASE_EVENTS, store
        )

        assert score_second == pytest.approx(score_first)
    finally:
        store.close()
