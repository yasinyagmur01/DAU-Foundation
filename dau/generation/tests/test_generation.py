"""Unit tests for generation transfer candidate cautionary traces."""

from __future__ import annotations

from dau.foundation.state import DeltaRecord


def test_failed_agent_traumas_become_cautionary_traces():
    from dau.foundation.generation import TransferCandidate
    # construct with minimal valid fields — read generation.py for exact signature
    snap = {
        "energy": 1.0,
        "resource_load": 0.0,
        "uncertainty_load": 0.0,
        "social_load": 0.0,
    }
    candidate = TransferCandidate(
        record=DeltaRecord(
            timestamp=1,
            magnitude=0.7,
            affected_domain="resource",
            snapshot_before=snap,
            snapshot_after=dict(snap),
        ),
        record_id="caution-0",
        memory_score=0.7,
        recall_count=2,
    )
    assert candidate.inherited_warning is False  # default
    assert candidate.somatic_scale == 0.0        # default
    candidate.inherited_warning = True
    candidate.somatic_scale = -0.3
    assert candidate.inherited_warning is True
    assert candidate.somatic_scale == -0.3
    pool = [candidate]
    assert len(pool) == 1
