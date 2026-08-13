"""Sleep consolidation — prune, strengthen, and wire co-occurring deep traces.

Biology analogy: overnight hippocampal replay drops faded ordinary memories,
boosts deep/trauma engrams, and links episodes that shared the same night.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from dau.foundation.delta import DeltaClassification

from .decay import compute_retention, should_forget
from .store import DOMAIN_EDGE_WINDOW, MemoryStore

# ---------------------------------------------------------------------------
# Sleep consolidation parameters
# ---------------------------------------------------------------------------

CONSOLIDATION_BOOST: int = 2  # DEEP/TRAUMA strength gain at run end
EDGE_MIN_WEIGHT: float = 0.3


class ConsolidationReport(BaseModel):
    """Summary of one sleep-consolidation pass.

    Biology analogy: a lab report after overnight replay — what was pruned,
    what was strengthened, which associations formed, how many trauma flags.
    """

    model_config = ConfigDict(frozen=True)

    agent_id: str
    timestamp: int
    deleted_count: int = Field(..., ge=0)
    strengthened_count: int = Field(..., ge=0)
    edges_created: int = Field(..., ge=0)
    drift_flag_count: int = Field(..., ge=0)


def run_consolidation(
    agent_id: str,
    now_counter: int,
    store: MemoryStore,
) -> ConsolidationReport:
    """Run end-of-run sleep consolidation for one agent.

    Biology analogy: while the organism rests, weak traces fade away, deep
    and traumatic imprints are replayed (strengthened), and co-occurring
    high-intensity episodes wire into an association graph.
    """

    # Sleep happens at the end of a life, but the traces being judged may come
    # from an earlier life on the same vault (GAP-19).
    now_counter = store.vault_counter(now_counter)
    nodes = store.list_nodes(agent_id)
    deleted_count = 0
    strengthened_count = 0
    edges_created = 0
    drift_flag_count = sum(1 for n in nodes if n.drift_flag)

    survivors = []
    for node in nodes:
        payload = store.get_record_payload(node.id)
        if payload is None:
            store.delete_record(node.id)
            deleted_count += 1
            continue
        retention = compute_retention(
            now_counter,
            node.last_activated_counter,
            node.strength,
        )
        if should_forget(retention, payload):
            store.delete_record(node.id)
            deleted_count += 1
            continue
        survivors.append(node)

    deep_like = []
    for node in survivors:
        if node.classification in (
            DeltaClassification.DEEP.value,
            DeltaClassification.TRAUMA.value,
        ):
            store.boost_strength(node.id, CONSOLIDATION_BOOST)
            strengthened_count += 1
            # Refresh strength locally for edge weight logic (boost already applied).
            refreshed = store.get_node(node.id)
            if refreshed is not None:
                deep_like.append(refreshed)

    # Pairwise edges for DEEP/TRAUMA within DOMAIN_EDGE_WINDOW on event counter.
    for i, a in enumerate(deep_like):
        for b in deep_like[i + 1 :]:
            if abs(a.timestamp - b.timestamp) > DOMAIN_EDGE_WINDOW:
                continue
            weight = min(a.magnitude, b.magnitude)
            if weight < EDGE_MIN_WEIGHT:
                continue
            edge_type = (
                "trauma_link"
                if a.drift_flag or b.drift_flag
                else "co_occur"
            )
            store.write_edge(a.id, b.id, weight=weight, edge_type=edge_type)
            edges_created += 1

    return ConsolidationReport(
        agent_id=agent_id,
        timestamp=now_counter,
        deleted_count=deleted_count,
        strengthened_count=strengthened_count,
        edges_created=edges_created,
        drift_flag_count=drift_flag_count,
    )


if __name__ == "__main__":
    import tempfile

    from dau.foundation.state import DeltaRecord

    def _rec(mag: float, domain: str, ts: int) -> DeltaRecord:
        snap = {
            "energy": 1.0,
            "resource_load": 0.0,
            "uncertainty_load": 0.0,
            "social_load": 0.0,
        }
        return DeltaRecord(
            timestamp=ts,
            magnitude=mag,
            affected_domain=domain,  # type: ignore[arg-type]
            snapshot_before=snap,
            snapshot_after=dict(snap),
        )

    with tempfile.TemporaryDirectory() as tmp:
        store = MemoryStore(
            chroma_path=f"{tmp}/chroma",
            sqlite_path=f"{tmp}/memory.db",
        )
        store.write_record(_rec(0.85, "resource", 1), "agent_demo")
        store.write_record(_rec(0.55, "resource", 2), "agent_demo")
        report = run_consolidation("agent_demo", now_counter=2, store=store)
        print(report.model_dump())
        store.close()
    print("OK — consolidation demo complete")
