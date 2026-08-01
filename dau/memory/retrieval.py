"""Memory retrieval — score and rank durable traces for the current query.

Biology analogy: cue-driven recall blends how fresh a memory feels, how
important the original swing was, and whether the queried life domain matches.
"""

from __future__ import annotations

from dau.foundation.state import AffectedDomain

from .decay import compute_retention
from .store import MemoryStore

# ---------------------------------------------------------------------------
# Generative-Agents-style weights (embedding cosine weight held at zero)
# ---------------------------------------------------------------------------

W_RECENCY: float = 0.3
W_IMPORTANCE: float = 0.4
W_RELEVANCE: float = 0.3
DOMAIN_SOFT_MATCH: float = 0.5  # edge-linked different domain


def compute_memory_score(
    record_id: str,
    query_domain: AffectedDomain | str,
    now_counter: int,
    store: MemoryStore,
) -> float:
    """Weighted memory_score = recency + importance + domain relevance.

    Biology analogy: what comes to mind is recent, emotionally charged, and
    relevant to the current homeostatic concern — not a raw embedding match.
    """

    node = store.get_node(record_id)
    if node is None:
        return 0.0

    recency = compute_retention(
        now_counter,
        node.last_activated_counter,
        node.strength,
    )
    importance = float(node.magnitude)
    q = str(query_domain)
    if node.domain == q:
        relevance = 1.0
    elif store.get_edge(node.domain, q):
        relevance = DOMAIN_SOFT_MATCH
    else:
        relevance = 0.0

    return (
        W_RECENCY * recency
        + W_IMPORTANCE * importance
        + W_RELEVANCE * relevance
    )


def retrieve_top_k(
    agent_id: str,
    query_domain: AffectedDomain | str,
    now_counter: int,
    store: MemoryStore,
    k: int = 5,
) -> list[tuple[str, float]]:
    """Score all agent nodes, rehearse them, return top-k (id, score).

    Biology analogy: scanning the engram library under a domain cue, then
    rehearsing whatever is retrieved so the trace strengthens.
    """

    nodes = store.list_nodes(agent_id)
    scored: list[tuple[str, float]] = []
    for node in nodes:
        score = compute_memory_score(
            node.id,
            query_domain,
            now_counter,
            store,
        )
        scored.append((node.id, score))

    scored.sort(key=lambda item: item[1], reverse=True)
    top = scored[:k]
    for record_id, _ in top:
        store.update_activation(record_id, now_counter)
    return top


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
        store.write_record(_rec(0.55, "resource", 1), "agent_demo")
        store.write_record(_rec(0.55, "social", 2), "agent_demo")
        top = retrieve_top_k(
            "agent_demo", "resource", now_counter=2, store=store, k=2
        )
        print(f"top_k={[(i[:8], round(s, 4)) for i, s in top]}")
        store.close()
    print("OK — retrieval demo complete")
