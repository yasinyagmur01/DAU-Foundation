"""LLM-free end-to-end demo for DAU-Memory Layer 1."""

from __future__ import annotations

import tempfile
from pathlib import Path

from dau.foundation.state import DeltaRecord
from dau.memory.consolidation import run_consolidation
from dau.memory.retrieval import retrieve_top_k
from dau.memory.store import MemoryStore


def _record(magnitude: float, domain: str, timestamp: int) -> DeltaRecord:
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


def main() -> None:
    """Write ten mixed deltas, retrieve, consolidate, print the sleep report.

    Biology analogy: a short waking day of strong and weak imprints, then
    overnight pruning and wiring — no language model required.
    """

    samples = [
        _record(0.05, "resource", 1),  # NO_TRACE — skipped
        _record(0.25, "resource", 2),  # NORMAL — skipped
        _record(0.45, "resource", 3),  # DEEP
        _record(0.55, "resource", 4),  # DEEP
        _record(0.85, "resource", 5),  # TRAUMA
        _record(0.50, "social", 6),  # DEEP
        _record(0.60, "energy", 7),  # DEEP
        _record(0.90, "uncertainty", 8),  # TRAUMA
        _record(0.48, "social", 9),  # DEEP
        _record(0.70, "resource", 10),  # TRAUMA
    ]

    with tempfile.TemporaryDirectory(prefix="dau_memory_demo_") as tmp:
        root = Path(tmp)
        store = MemoryStore(
            chroma_path=str(root / "chroma"),
            sqlite_path=str(root / "memory.db"),
        )
        agent_id = "demo_agent"
        written: list[str] = []
        for record in samples:
            rid = store.write_record(record, agent_id)
            if rid:
                written.append(rid)

        print(f"wrote_persistable={len(written)} / {len(samples)}")
        top = retrieve_top_k(
            agent_id,
            query_domain="resource",
            now_counter=10,
            store=store,
            k=5,
        )
        print("retrieve_top_k(resource):")
        for rid, score in top:
            node = store.get_node(rid)
            domain = node.domain if node else "?"
            print(f"  {rid[:8]}… domain={domain} score={score:.4f}")

        report = run_consolidation(agent_id, now_counter=10, store=store)
        print("consolidation_report:")
        print(f"  deleted={report.deleted_count}")
        print(f"  strengthened={report.strengthened_count}")
        print(f"  edges_created={report.edges_created}")
        print(f"  drift_flags={report.drift_flag_count}")
        store.close()
    print("OK — memory demo complete")


if __name__ == "__main__":
    main()
