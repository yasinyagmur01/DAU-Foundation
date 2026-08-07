"""
DAU PPR Retrieval
HippoRAG 2 inspired Personalized PageRank over SQLite domain co-occurrence graph.
CPU only. Zero VRAM. NetworkX + SciPy.

STEP 1 — existing memory engine (read before implement):
  memory_score (retrieval.py):
    W_RECENCY=0.3 · recency + W_IMPORTANCE=0.4 · magnitude + W_RELEVANCE=0.3 · domain_match
    fields: recency via compute_retention(last_activated_counter, strength);
            importance = node.magnitude; relevance = 1.0 | DOMAIN_SOFT_MATCH(0.5) | 0.0
  SQLite edge table (store.py):
    memory_edges(src_id TEXT, dst_id TEXT, weight REAL, edge_type TEXT)
    PRIMARY KEY (src_id, dst_id) — edges link record ids, not domains;
    domain co-occurrence = JOIN memory_nodes on src_id/dst_id → s.domain / d.domain
  retrieve API:
    retrieve_top_k(agent_id, query_domain, now_counter, store, k=5) → list[tuple[id, score]]
    retrieve_relevant(query_domain, agent_id, now_counter, store, k=...) in memory_bridge
  networkx: not imported anywhere under dau/ before this module
"""

from __future__ import annotations

import sqlite3
from typing import Any

try:
    import networkx as nx

    _NX_AVAILABLE = True
except ImportError:
    _NX_AVAILABLE = False

from dau.foundation.constraints import PPR_ALPHA, PPR_TOP_K_DOMAINS

# Edge weight key on NetworkX DiGraph (matches memory_edges.weight)
_EDGE_WEIGHT_ATTR: str = "weight"


def _load_graph_from_sqlite(db_path: str) -> Any:
    """Load domain co-occurrence edges from SQLite into a NetworkX DiGraph.

    memory_edges stores record-id pairs; domains come from memory_nodes.
    Co-occurrence is treated as bidirectional for associative recall.
    """

    if not _NX_AVAILABLE:
        raise RuntimeError("networkx is required to load the PPR graph")

    graph = nx.DiGraph()
    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute(
            """
            SELECT s.domain AS src_domain,
                   d.domain AS dst_domain,
                   e.weight AS weight
            FROM memory_edges e
            JOIN memory_nodes s ON s.id = e.src_id
            JOIN memory_nodes d ON d.id = e.dst_id
            """
        ).fetchall()
    finally:
        conn.close()

    for src_domain, dst_domain, weight in rows:
        src = str(src_domain)
        dst = str(dst_domain)
        if src == dst:
            continue
        w = float(weight)
        for u, v in ((src, dst), (dst, src)):
            if graph.has_edge(u, v):
                prev = float(graph[u][v].get(_EDGE_WEIGHT_ATTR, 0.0))
                graph[u][v][_EDGE_WEIGHT_ATTR] = max(prev, w)
            else:
                graph.add_edge(u, v, **{_EDGE_WEIGHT_ATTR: w})
    return graph


def compute_ppr_scores(
    db_path: str,
    seed_domain: str,
    alpha: float = PPR_ALPHA,
    top_k: int = PPR_TOP_K_DOMAINS,
) -> dict[str, float]:
    """
    Run Personalized PageRank seeded on seed_domain.
    Returns dict of {domain: ppr_score} for top_k domains.
    If networkx unavailable or graph empty, returns {seed_domain: 1.0}.
    """
    if not _NX_AVAILABLE:
        return {seed_domain: 1.0}
    try:
        G = _load_graph_from_sqlite(db_path)
        if len(G.nodes) == 0:
            return {seed_domain: 1.0}
        personalization = {seed_domain: 1.0} if seed_domain in G else None
        scores = nx.pagerank(
            G,
            alpha=alpha,
            personalization=personalization,
            weight=_EDGE_WEIGHT_ATTR,
        )
        top = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
        return dict(top)
    except Exception:
        return {seed_domain: 1.0}


def ppr_score_for_domain(
    db_path: str,
    seed_domain: str,
    target_domain: str,
) -> float:
    """
    Returns PPR score of target_domain when seeded from seed_domain.
    Returns 0.0 if target not reachable.
    """
    scores = compute_ppr_scores(db_path, seed_domain)
    return scores.get(target_domain, 0.0)
