"""Unit tests for HippoRAG 2 Personalized PageRank memory retrieval."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from dau.foundation.constraints import PPR_TOP_K_DOMAINS
from dau.foundation.state import DeltaRecord
from dau.memory.ppr_retrieval import compute_ppr_scores, ppr_score_for_domain
from dau.memory.retrieval import compute_memory_score
from dau.memory.store import MemoryStore

# ---------------------------------------------------------------------------
# Schema mirrors store.py memory_nodes / memory_edges (record-id edges)
# ---------------------------------------------------------------------------

_CREATE_NODES: str = """
CREATE TABLE IF NOT EXISTS memory_nodes (
    id TEXT PRIMARY KEY,
    agent_id TEXT NOT NULL,
    domain TEXT NOT NULL,
    event_type TEXT NOT NULL,
    timestamp INTEGER NOT NULL,
    last_activated_counter INTEGER NOT NULL,
    strength INTEGER NOT NULL DEFAULT 1,
    magnitude REAL NOT NULL,
    classification TEXT NOT NULL,
    drift_flag INTEGER NOT NULL DEFAULT 0,
    chroma_id TEXT NOT NULL
)
"""

_CREATE_EDGES: str = """
CREATE TABLE IF NOT EXISTS memory_edges (
    src_id TEXT NOT NULL,
    dst_id TEXT NOT NULL,
    weight REAL NOT NULL,
    edge_type TEXT NOT NULL,
    PRIMARY KEY (src_id, dst_id)
)
"""


def _init_empty_schema(db_path: str) -> None:
    conn = sqlite3.connect(db_path)
    conn.execute(_CREATE_NODES)
    conn.execute(_CREATE_EDGES)
    conn.commit()
    conn.close()


def _insert_node(
    conn: sqlite3.Connection,
    node_id: str,
    domain: str,
    *,
    agent_id: str = "a1",
    timestamp: int = 1,
) -> None:
    conn.execute(
        """
        INSERT INTO memory_nodes (
            id, agent_id, domain, event_type, timestamp,
            last_activated_counter, strength, magnitude,
            classification, drift_flag, chroma_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            node_id,
            agent_id,
            domain,
            "DEEP",
            timestamp,
            timestamp,
            1,
            0.55,
            "DEEP",
            0,
            node_id,
        ),
    )


def _insert_edge(
    conn: sqlite3.Connection,
    src_id: str,
    dst_id: str,
    weight: float = 1.0,
) -> None:
    a, b = (src_id, dst_id) if src_id < dst_id else (dst_id, src_id)
    conn.execute(
        """
        INSERT INTO memory_edges (src_id, dst_id, weight, edge_type)
        VALUES (?, ?, ?, ?)
        """,
        (a, b, weight, "co_occur"),
    )


def _cycle_graph_db(db_path: str) -> None:
    """resource ↔ social ↔ energy ↔ resource via three record-id edges."""

    _init_empty_schema(db_path)
    conn = sqlite3.connect(db_path)
    _insert_node(conn, "n_resource", "resource", timestamp=1)
    _insert_node(conn, "n_social", "social", timestamp=2)
    _insert_node(conn, "n_energy", "energy", timestamp=3)
    _insert_edge(conn, "n_resource", "n_social")
    _insert_edge(conn, "n_social", "n_energy")
    _insert_edge(conn, "n_energy", "n_resource")
    conn.commit()
    conn.close()


def _record(
    magnitude: float,
    domain: str,
    timestamp: int,
) -> DeltaRecord:
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


def test_ppr_scores_empty_graph_returns_seed(tmp_path: Path) -> None:
    db_path = str(tmp_path / "empty.db")
    _init_empty_schema(db_path)
    assert compute_ppr_scores(db_path, "resource") == {"resource": 1.0}


def test_ppr_scores_connected_graph(tmp_path: Path) -> None:
    db_path = str(tmp_path / "cycle.db")
    _cycle_graph_db(db_path)
    scores = compute_ppr_scores(db_path, "resource")
    assert "resource" in scores
    assert "social" in scores
    assert len(scores) <= PPR_TOP_K_DOMAINS


def test_ppr_score_for_domain_reachable(tmp_path: Path) -> None:
    db_path = str(tmp_path / "cycle.db")
    _cycle_graph_db(db_path)
    score = ppr_score_for_domain(db_path, "resource", "social")
    assert score > 0.0


def test_ppr_score_for_domain_unreachable(tmp_path: Path) -> None:
    db_path = str(tmp_path / "cycle.db")
    _cycle_graph_db(db_path)
    score = ppr_score_for_domain(db_path, "resource", "nonexistent")
    assert score == 0.0


def test_ppr_fallback_on_bad_db() -> None:
    result = compute_ppr_scores("/nonexistent/path.db", "resource")
    assert result == {"resource": 1.0}


def test_memory_score_includes_ppr_weight(tmp_path: Path) -> None:
    """Multi-hop edge path raises social score under resource query via PPR.

    Direct resource↔social edge is omitted so DOMAIN_SOFT_MATCH stays 0;
    only associative PPR can lift the related-domain candidate.
    """

    chroma_with = tmp_path / "chroma_with"
    chroma_without = tmp_path / "chroma_without"
    db_with = tmp_path / "with_edges.db"
    db_without = tmp_path / "without_edges.db"

    store_with = MemoryStore(
        chroma_path=str(chroma_with),
        sqlite_path=str(db_with),
    )
    store_without = MemoryStore(
        chroma_path=str(chroma_without),
        sqlite_path=str(db_without),
    )
    try:
        id_resource_w = store_with.write_record(
            _record(0.55, "resource", 1), "a1"
        )
        id_energy_w = store_with.write_record(_record(0.55, "energy", 2), "a1")
        id_social_w = store_with.write_record(_record(0.55, "social", 3), "a1")
        assert id_resource_w and id_energy_w and id_social_w
        # Multi-hop only: resource — energy — social (no direct resource-social)
        store_with.write_edge(id_resource_w, id_energy_w, weight=1.0)
        store_with.write_edge(id_energy_w, id_social_w, weight=1.0)

        id_social_wo = store_without.write_record(
            _record(0.55, "social", 3), "a1"
        )
        assert id_social_wo
        assert store_with.get_edge("resource", "social") is False

        score_with = compute_memory_score(
            id_social_w, "resource", now_counter=3, store=store_with
        )
        score_without = compute_memory_score(
            id_social_wo, "resource", now_counter=3, store=store_without
        )
        assert score_with > score_without
    finally:
        store_with.close()
        store_without.close()
