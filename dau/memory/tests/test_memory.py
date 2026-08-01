"""Tests for DAU-Memory Layer 1."""

from __future__ import annotations

import math

import pytest

from dau.foundation.delta import should_persist
from dau.foundation.state import DeltaRecord
from dau.memory.consolidation import run_consolidation
from dau.memory.decay import (
    R_MIN,
    TRAUMA_S_BASE,
    compute_retention,
    compute_strength_init,
    should_forget,
)
from dau.memory.retrieval import compute_memory_score, retrieve_top_k
from dau.memory.store import MemoryStore, persist_decision


def _record(
    magnitude: float,
    domain: str = "resource",
    timestamp: int = 1,
) -> DeltaRecord:
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


@pytest.fixture
def store(tmp_path):
    ms = MemoryStore(
        chroma_path=str(tmp_path / "chroma"),
        sqlite_path=str(tmp_path / "memory.db"),
    )
    yield ms
    ms.close()


def test_compute_strength_init_from_magnitude():
    deep = _record(0.55)
    assert compute_strength_init(deep) == max(1, round(0.55 / 0.1))
    trauma = _record(0.85)
    assert compute_strength_init(trauma) >= TRAUMA_S_BASE


def test_compute_retention_extremes():
    assert compute_retention(10, 10, strength=5) == pytest.approx(1.0)
    far = compute_retention(10_000, 0, strength=1)
    assert far == pytest.approx(0.0, abs=1e-6)


def test_should_forget_trauma_and_normal():
    trauma = _record(0.9)
    normal_deep = _record(0.5)
    assert should_forget(0.0, trauma) is False
    assert should_forget(R_MIN - 0.01, normal_deep) is True
    assert should_forget(0.9, normal_deep) is False


def test_persist_decision_trauma():
    trauma = _record(0.85)
    decision = persist_decision(trauma)
    assert decision["persist"] is True
    assert decision["drift_flag"] is True
    assert decision["classification"] == "TRAUMA"
    assert decision["chroma_write"] is True
    assert decision["sleep_priority"] == 2


def test_should_persist_deep_and_no_trace():
    assert should_persist(_record(0.5)) is True
    assert should_persist(_record(0.05)) is False


def test_compute_memory_score_domain_match(store):
    same = _record(0.55, domain="resource", timestamp=1)
    other = _record(0.55, domain="social", timestamp=2)
    id_same = store.write_record(same, "a1")
    id_other = store.write_record(other, "a1")
    score_same = compute_memory_score(id_same, "resource", now_counter=2, store=store)
    score_other = compute_memory_score(id_other, "resource", now_counter=2, store=store)
    assert score_same > score_other


def test_retrieve_top_k_order_and_activation(store):
    high = _record(0.65, domain="resource", timestamp=1)
    low = _record(0.45, domain="resource", timestamp=2)
    id_high = store.write_record(high, "a1")
    id_low = store.write_record(low, "a1")
    before = store.get_node(id_high)
    assert before is not None
    strength_before = before.strength
    top = retrieve_top_k("a1", "resource", now_counter=5, store=store, k=2)
    assert len(top) == 2
    assert top[0][0] == id_high
    assert top[0][1] >= top[1][1]
    after = store.get_node(id_high)
    assert after is not None
    assert after.strength == strength_before + 1
    assert after.last_activated_counter == 5
    _ = id_low  # written; ordering asserts high wins


def test_run_consolidation_forget_protect_edge_report(store):
    # Faded ordinary DEEP: low strength, ancient activation → forget.
    faded = _record(0.45, domain="resource", timestamp=1)
    trauma = _record(0.85, domain="resource", timestamp=2)
    deep_near = _record(0.55, domain="social", timestamp=3)
    id_faded = store.write_record(faded, "a1")
    id_trauma = store.write_record(trauma, "a1")
    id_deep = store.write_record(deep_near, "a1")

    # Force faded node into forgettable retention territory.
    cur = store._conn.cursor()
    cur.execute(
        """
        UPDATE memory_nodes
        SET strength = 1, last_activated_counter = 0
        WHERE id = ?
        """,
        (id_faded,),
    )
    store._conn.commit()

    # Modest now: faded (S=1, last=0) drops; recent DEEP/TRAUMA survive for edges.
    now = 20
    faded_node = store.get_node(id_faded)
    assert faded_node is not None
    r = compute_retention(now, faded_node.last_activated_counter, faded_node.strength)
    assert should_forget(r, faded) is True
    assert math.exp(-now / 1) < R_MIN

    report = run_consolidation("a1", now_counter=now, store=store)
    assert store.get_node(id_faded) is None
    assert store.get_node(id_trauma) is not None
    assert report.deleted_count >= 1
    assert report.strengthened_count >= 1
    assert report.drift_flag_count >= 1
    # Trauma + near deep should create an edge (timestamps 2 and 3 within window).
    assert report.edges_created >= 1
    assert store.get_edge("resource", "social") is True
    trauma_node = store.get_node(id_trauma)
    assert trauma_node is not None
    assert trauma_node.strength >= TRAUMA_S_BASE + 2
    _ = id_deep
