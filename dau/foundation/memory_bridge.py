"""Hippocampal bridge between the life loop and durable memory.

Biology analogy: the passage between momentary experience and long-term
storage — write only what mattered, recall what is relevant now, then sleep.
graph.py never imports MemoryStore directly; all traffic crosses this bridge.
"""

from __future__ import annotations

from typing import Any

from dau.foundation.state import DeltaRecord
from dau.memory import (
    ConsolidationReport,
    MemoryStore,
    persist_decision,
    retrieve_top_k,
    run_consolidation,
)

# ---------------------------------------------------------------------------
# Bridge limits and default durable-store paths
# ---------------------------------------------------------------------------

MAX_RETRIEVED_MEMORIES: int = 3
MEMORY_STORE_PATH: str = "dau_memory.db"
CHROMA_PATH: str = "dau_memory_chroma"


def initialize_memory(agent_id: str) -> MemoryStore:
    """Open the durable memory vault for one life run.

    Biology analogy: open the hippocampal filing cabinets before the organism
    begins acting — one store per run start.
    """

    _ = agent_id  # reserved for future per-agent vault routing
    return MemoryStore(
        chroma_path=CHROMA_PATH,
        sqlite_path=MEMORY_STORE_PATH,
    )


def record_delta(
    record: DeltaRecord,
    agent_id: str,
    store: MemoryStore,
) -> dict[str, Any] | None:
    """Decide whether a delta deserves durable writing, then write if so.

    Biology analogy: was this swing important enough to leave a lasting
    engram, or did it fade as noise?
    """

    if store is None:
        return None
    decision = persist_decision(record)
    if decision["persist"]:
        store.write_record(record, agent_id)
    return decision


def retrieve_relevant(
    query_domain: str,
    agent_id: str,
    now_counter: int,
    store: MemoryStore,
    k: int = MAX_RETRIEVED_MEMORIES,
) -> list[dict[str, Any]]:
    """Recall top-k past episodes relevant to the current domain pressure.

    Biology analogy: before deciding, cue the engram library for similar
    homeostatic situations — never traits, only lived magnitude and domain.
    """

    if store is None:
        return []
    top = retrieve_top_k(
        agent_id,
        query_domain,
        now_counter,
        store,
        k=k,
    )
    results: list[dict[str, Any]] = []
    for record_id, score in top:
        node = store.get_node(record_id)
        if node is None:
            continue
        results.append(
            {
                "domain": node.domain,
                "magnitude": float(node.magnitude),
                "classification": node.classification,
                "score": float(score),
                "drift_flag": bool(node.drift_flag),
            }
        )
    return results


def consolidate_run(
    agent_id: str,
    now_counter: int,
    store: MemoryStore,
) -> ConsolidationReport:
    """Run end-of-life sleep consolidation and return the lab report.

    Biology analogy: overnight hippocampal replay — prune faded traces,
    strengthen deep ones, wire co-occurring pressures.
    """

    return run_consolidation(agent_id, now_counter, store)
