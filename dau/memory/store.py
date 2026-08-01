"""Long-term memory store — ChromaDB embedding vault + SQLite domain graph.

Biology analogy: the hippocampus writes durable traces to cortex-like storage
and keeps a sparse association graph of what co-occurred under pressure.
This module is pure CRUD — no scoring, no forgetting policy.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from uuid import uuid4

import chromadb
from chromadb.api.types import Documents, EmbeddingFunction, Embeddings
from chromadb.config import Settings

from dau.foundation.delta import (
    DeltaClassification,
    classify_delta,
    is_trauma,
    should_persist,
)
from dau.foundation.state import AffectedDomain, DeltaRecord

from .decay import compute_strength_init

# ---------------------------------------------------------------------------
# Storage paths and co-occurrence window
# ---------------------------------------------------------------------------

CHROMA_COLLECTION_NAME: str = "dau_memory"
CHROMA_DB_PATH: str = "dau_memory_chroma"
SQLITE_MEMORY_PATH: str = "dau_memory.db"
DOMAIN_EDGE_WINDOW: int = 10  # DEEP/TRAUMA within this event-counter span link
EMBEDDING_DIM: int = 32  # Chroma vault only; W_SEM=0 so vectors are not scored


class DeterministicHashEmbedding(EmbeddingFunction[Documents]):
    """Hash-based embedding — no model download, not used for scoring.

    Biology analogy: a filing barcode, not semantic meaning. Chroma needs a
    vector slot; retrieval in DAU scores by magnitude/domain/recency instead.
    """

    def __init__(self) -> None:
        pass

    @staticmethod
    def name() -> str:
        return "dau_deterministic_hash"

    def __call__(self, input: Documents) -> Embeddings:
        vectors: Embeddings = []
        for text in input:
            digest = hashlib.sha256(text.encode("utf-8")).digest()
            # Expand digest into EMBEDDING_DIM floats in [-1, 1].
            raw = (digest * ((EMBEDDING_DIM // len(digest)) + 1))[:EMBEDDING_DIM]
            vectors.append([(b / 127.5) - 1.0 for b in raw])
        return vectors


@dataclass
class MemoryNode:
    """SQLite row mirror for one persisted memory engram.

    Biology analogy: the cortical index card for a consolidated episode —
    identity, domain tag, activation counters, and strength.
    """

    id: str
    agent_id: str
    domain: str
    event_type: str
    timestamp: int
    last_activated_counter: int
    strength: int
    magnitude: float
    classification: str
    drift_flag: int
    chroma_id: str


def persist_decision(record: DeltaRecord) -> dict[str, Any]:
    """Return write/consolidation metadata without mutating storage.

    Biology analogy: the gatekeeper that decides whether a physiological
    swing deserves long-term writing, how strong the first synapse should be,
    and whether sleep should prioritize trauma repair.
    """

    classification = classify_delta(record)
    persist = should_persist(record)
    drift = is_trauma(record)
    strength_init = compute_strength_init(record)

    if classification == DeltaClassification.TRAUMA:
        sleep_priority = 2
    elif classification == DeltaClassification.DEEP:
        sleep_priority = 1
    else:
        sleep_priority = 0

    return {
        "persist": persist,
        "classification": classification.value,
        "strength_init": strength_init,
        "drift_flag": drift,
        "chroma_write": persist,
        "sleep_priority": sleep_priority,
    }


class MemoryStore:
    """Disk-backed episodic store: Chroma for payloads, SQLite for graph.

    Biology analogy: dual-store consolidation — content in one vault,
    association edges in another — without yet applying retrieval or sleep.
    """

    def __init__(
        self,
        chroma_path: str = CHROMA_DB_PATH,
        sqlite_path: str = SQLITE_MEMORY_PATH,
        collection_name: str = CHROMA_COLLECTION_NAME,
    ) -> None:
        Path(chroma_path).mkdir(parents=True, exist_ok=True)
        self._chroma = chromadb.PersistentClient(
            path=chroma_path,
            settings=Settings(anonymized_telemetry=False),
        )
        self._collection = self._chroma.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
            embedding_function=DeterministicHashEmbedding(),
        )
        self._sqlite_path = sqlite_path
        self._conn = sqlite3.connect(sqlite_path)
        self._conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        """Create memory_nodes / memory_edges if missing.

        Biology analogy: laying down the anatomical scaffolding before
        any engram can be filed.
        """

        cur = self._conn.cursor()
        cur.execute(
            """
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
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS memory_edges (
                src_id TEXT NOT NULL,
                dst_id TEXT NOT NULL,
                weight REAL NOT NULL,
                edge_type TEXT NOT NULL,
                PRIMARY KEY (src_id, dst_id)
            )
            """
        )
        self._conn.commit()

    def close(self) -> None:
        """Release SQLite connection.

        Biology analogy: closing the filing cabinet after the day's work.
        """

        self._conn.close()

    def write_record(self, record: DeltaRecord, agent_id: str) -> str:
        """Persist a DeltaRecord when persist_decision allows it.

        Biology analogy: only deep or traumatic swings are written from
        working memory onto durable cortical storage.
        """

        decision = persist_decision(record)
        if not decision["persist"]:
            return ""

        record_id = str(uuid4())
        domain = str(record.affected_domain)
        classification = str(decision["classification"])
        drift_flag = 1 if decision["drift_flag"] else 0
        strength = int(decision["strength_init"])
        document = json.dumps(record.model_dump())

        self._collection.add(
            ids=[record_id],
            documents=[document],
            metadatas=[
                {
                    "agent_id": agent_id,
                    "domain": domain,
                    "magnitude": float(record.magnitude),
                    "timestamp": int(record.timestamp),
                    "classification": classification,
                    "drift_flag": drift_flag,
                }
            ],
        )

        cur = self._conn.cursor()
        cur.execute(
            """
            INSERT INTO memory_nodes (
                id, agent_id, domain, event_type, timestamp,
                last_activated_counter, strength, magnitude,
                classification, drift_flag, chroma_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record_id,
                agent_id,
                domain,
                classification,
                int(record.timestamp),
                int(record.timestamp),
                strength,
                float(record.magnitude),
                classification,
                drift_flag,
                record_id,
            ),
        )
        self._conn.commit()
        return record_id

    def read_records(
        self,
        agent_id: str,
        query_domain: AffectedDomain | str | None = None,
        limit: int = 20,
    ) -> list[DeltaRecord]:
        """Fetch stored DeltaRecords from Chroma (no scoring).

        Biology analogy: open the filing drawer and pull raw episode cards;
        ranking which matter now is someone else's job (retrieval).
        """

        where: dict[str, Any]
        if query_domain is None:
            where = {"agent_id": agent_id}
        else:
            where = {
                "$and": [
                    {"agent_id": agent_id},
                    {"domain": str(query_domain)},
                ]
            }

        result = self._collection.get(
            where=where,
            limit=limit,
            include=["documents", "metadatas"],
        )
        records: list[DeltaRecord] = []
        documents = result.get("documents") or []
        for doc in documents:
            if doc is None:
                continue
            payload = json.loads(doc)
            records.append(DeltaRecord.model_validate(payload))
        return records

    def list_nodes(self, agent_id: str) -> list[MemoryNode]:
        """Return all SQLite memory nodes for an agent.

        Biology analogy: inventory every consolidated engram the organism holds.
        """

        cur = self._conn.cursor()
        cur.execute(
            "SELECT * FROM memory_nodes WHERE agent_id = ? ORDER BY timestamp ASC",
            (agent_id,),
        )
        return [self._row_to_node(row) for row in cur.fetchall()]

    def get_node(self, record_id: str) -> MemoryNode | None:
        """Load one memory node by id.

        Biology analogy: retrieve a single cortical index card by its address.
        """

        cur = self._conn.cursor()
        cur.execute("SELECT * FROM memory_nodes WHERE id = ?", (record_id,))
        row = cur.fetchone()
        if row is None:
            return None
        return self._row_to_node(row)

    def get_edge(self, domain_a: str, domain_b: str) -> bool:
        """Return True if any stored edge links the two domains.

        Biology analogy: soft association — if two homeostatic domains have
        co-occurred under pressure, a faint bridge exists between them.
        """

        if domain_a == domain_b:
            return True
        cur = self._conn.cursor()
        cur.execute(
            """
            SELECT 1
            FROM memory_edges e
            JOIN memory_nodes s ON s.id = e.src_id
            JOIN memory_nodes d ON d.id = e.dst_id
            WHERE (s.domain = ? AND d.domain = ?)
               OR (s.domain = ? AND d.domain = ?)
            LIMIT 1
            """,
            (domain_a, domain_b, domain_b, domain_a),
        )
        return cur.fetchone() is not None

    def update_activation(self, record_id: str, now_counter: int) -> None:
        """Bump last_activated_counter and increment strength on recall.

        Biology analogy: remembering a trace rehearses it — synapses strengthen
        and the last-use stamp moves forward on the event counter.
        """

        cur = self._conn.cursor()
        cur.execute(
            """
            UPDATE memory_nodes
            SET last_activated_counter = ?,
                strength = strength + 1
            WHERE id = ?
            """,
            (int(now_counter), record_id),
        )
        self._conn.commit()

    def boost_strength(self, record_id: str, amount: int) -> None:
        """Add consolidation boost to a node's strength.

        Biology analogy: sleep replaying important episodes adds synaptic weight
        without requiring an external cue.
        """

        cur = self._conn.cursor()
        cur.execute(
            """
            UPDATE memory_nodes
            SET strength = strength + ?
            WHERE id = ?
            """,
            (int(amount), record_id),
        )
        self._conn.commit()

    def write_edge(
        self,
        src_id: str,
        dst_id: str,
        weight: float,
        edge_type: str = "co_occur",
    ) -> None:
        """Upsert a directed association edge between two record ids.

        Biology analogy: Hebbian co-occurrence — cells that fire together
        wire together inside the association graph.
        """

        if src_id == dst_id:
            return
        # Canonicalize undirected pair for PRIMARY KEY stability.
        a, b = (src_id, dst_id) if src_id < dst_id else (dst_id, src_id)
        cur = self._conn.cursor()
        cur.execute(
            """
            INSERT INTO memory_edges (src_id, dst_id, weight, edge_type)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(src_id, dst_id) DO UPDATE SET
                weight = MAX(memory_edges.weight, excluded.weight),
                edge_type = excluded.edge_type
            """,
            (a, b, float(weight), edge_type),
        )
        self._conn.commit()

    def delete_record(self, record_id: str) -> None:
        """Remove a record from Chroma and SQLite (nodes + incident edges).

        Biology analogy: pruning a faded engram from both content store and
        its association fibers.
        """

        try:
            self._collection.delete(ids=[record_id])
        except Exception:
            pass
        cur = self._conn.cursor()
        cur.execute(
            "DELETE FROM memory_edges WHERE src_id = ? OR dst_id = ?",
            (record_id, record_id),
        )
        cur.execute("DELETE FROM memory_nodes WHERE id = ?", (record_id,))
        self._conn.commit()

    def get_record_payload(self, record_id: str) -> DeltaRecord | None:
        """Rehydrate a DeltaRecord from Chroma by id.

        Biology analogy: unfold the full episode content from the vault card.
        """

        result = self._collection.get(
            ids=[record_id],
            include=["documents"],
        )
        documents = result.get("documents") or []
        if not documents or documents[0] is None:
            return None
        return DeltaRecord.model_validate(json.loads(documents[0]))

    @staticmethod
    def _row_to_node(row: sqlite3.Row) -> MemoryNode:
        """Map a SQLite row onto MemoryNode.

        Biology analogy: translate filing-cabinet ink into a usable index card.
        """

        return MemoryNode(
            id=str(row["id"]),
            agent_id=str(row["agent_id"]),
            domain=str(row["domain"]),
            event_type=str(row["event_type"]),
            timestamp=int(row["timestamp"]),
            last_activated_counter=int(row["last_activated_counter"]),
            strength=int(row["strength"]),
            magnitude=float(row["magnitude"]),
            classification=str(row["classification"]),
            drift_flag=int(row["drift_flag"]),
            chroma_id=str(row["chroma_id"]),
        )


if __name__ == "__main__":
    import tempfile

    from dau.foundation.state import DeltaRecord

    with tempfile.TemporaryDirectory() as tmp:
        store = MemoryStore(
            chroma_path=f"{tmp}/chroma",
            sqlite_path=f"{tmp}/memory.db",
        )
        snap = {
            "energy": 1.0,
            "resource_load": 0.0,
            "uncertainty_load": 0.0,
            "social_load": 0.0,
        }
        record = DeltaRecord(
            timestamp=3,
            magnitude=0.85,
            affected_domain="resource",
            snapshot_before=snap,
            snapshot_after=dict(snap),
        )
        decision = persist_decision(record)
        rid = store.write_record(record, agent_id="agent_demo")
        nodes = store.list_nodes("agent_demo")
        print(f"decision={decision}")
        print(f"wrote_id={rid!r} nodes={len(nodes)}")
        store.close()
    print("OK — store demo complete")
