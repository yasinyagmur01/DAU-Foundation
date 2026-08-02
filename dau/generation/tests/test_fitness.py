"""Unit tests for F_agent fitness and fitness-based transfer selection."""

from __future__ import annotations

import math

import pytest

from dau.foundation.delta import DELTA_THRESHOLD_DEEP
from dau.foundation.drift import DriftState
from dau.foundation.generation import (
    DRIFT_TRANSFER_MIN,
    GENERATION_MIN_RECALL,
    GENERATION_TRANSFER_THRESHOLD,
    INHERITED_WARNING_KEY,
    RECORD_ID_KEY,
    SOMATIC_SCALE_KEY,
    TRANSFER_KIND_INHERITED_WARNING,
    TRANSFER_KIND_STANDARD,
    GenerationRecord,
    TransferCandidate,
    apply_generation,
    select_for_transfer,
)
from dau.foundation.constraints import build_default_constraints
from dau.foundation.state import DAUAgentState, DeltaRecord
from dau.generation.fitness import (
    ENERGY_MAX,
    FITNESS_HIGH_THRESHOLD,
    FITNESS_LABEL_HIGH,
    FITNESS_LABEL_LOW,
    FITNESS_LABEL_NORMAL,
    FITNESS_LOW_THRESHOLD,
    FITNESS_W_ENERGY,
    FITNESS_W_POOL,
    FITNESS_W_SURVIVAL,
    WARNING_SOMATIC_SCALE,
    W_TRANSFER_VALENCE_BASE,
    classify_fitness,
    compute_fitness,
    compute_w_transfer,
)
from dau.society.environment import POOL_MAX


def _delta(magnitude: float, domain: str = "resource", timestamp: int = 1) -> DeltaRecord:
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


def _candidate(
    magnitude: float,
    *,
    memory_score: float,
    recall_count: int,
    domain: str = "resource",
    record_id: str = "mem-0",
) -> TransferCandidate:
    return TransferCandidate(
        record=_delta(magnitude, domain=domain),
        record_id=record_id,
        memory_score=memory_score,
        recall_count=recall_count,
    )


def test_compute_fitness_formula() -> None:
    """F matches weighted energy / pool / survival terms and clamps to [0, 1]."""

    energy_final = 0.8
    delta_pool = 20.0
    t_survived = 40
    t_generation = 50

    expected = (
        FITNESS_W_ENERGY * (energy_final / ENERGY_MAX)
        + FITNESS_W_POOL * (1.0 - abs(delta_pool) / POOL_MAX)
        + FITNESS_W_SURVIVAL * (t_survived / t_generation)
    )
    assert compute_fitness(
        energy_final, delta_pool, t_survived, t_generation
    ) == pytest.approx(expected)

    assert compute_fitness(2.0, 0.0, 10, 10) == 1.0
    assert compute_fitness(0.0, POOL_MAX, 0, 0) == 0.0


def test_classify_fitness_thresholds() -> None:
    """Low / high thresholds map onto policy labels; mid-band is normal."""

    assert classify_fitness(FITNESS_LOW_THRESHOLD - 0.01) == FITNESS_LABEL_LOW
    assert classify_fitness(FITNESS_LOW_THRESHOLD) == FITNESS_LABEL_NORMAL
    assert classify_fitness(FITNESS_HIGH_THRESHOLD - 0.01) == FITNESS_LABEL_NORMAL
    assert classify_fitness(FITNESS_HIGH_THRESHOLD) == FITNESS_LABEL_HIGH


def test_compute_w_transfer_formula() -> None:
    """W matches memory_score · F · (1 + tanh(reward − threat)) and clamps."""

    memory_score = 0.8
    f_agent = 0.5
    reward_marker = 0.6
    threat_marker = 0.2
    expected = memory_score * f_agent * (
        W_TRANSFER_VALENCE_BASE + math.tanh(reward_marker - threat_marker)
    )
    assert compute_w_transfer(
        memory_score, f_agent, reward_marker, threat_marker
    ) == pytest.approx(expected)
    assert compute_w_transfer(1.0, 1.0, 10.0, 0.0) == 1.0


def test_low_fitness_excludes_trauma() -> None:
    """Below FITNESS_LOW_THRESHOLD: all trauma purged; non-trauma can pass."""

    f_low = FITNESS_LOW_THRESHOLD - 0.01
    trauma = _candidate(
        DELTA_THRESHOLD_DEEP,
        memory_score=0.95,
        recall_count=GENERATION_MIN_RECALL,
        record_id="trauma-low-f",
    )
    # W = 0.95 * f_low * 1 ≈ 0.32 < 0.60 with neutral markers — boost valence.
    normal = _candidate(
        0.55,
        memory_score=0.95,
        recall_count=GENERATION_MIN_RECALL,
        record_id="keep-normal",
    )
    high_drift = DriftState(
        flags={"resource": True},
        magnitudes={"resource": DRIFT_TRANSFER_MIN},
    )
    selected = select_for_transfer(
        [trauma, normal],
        high_drift,
        f_agent=f_low,
        reward_marker=5.0,
        threat_marker=0.0,
    )
    ids = [c.record_id for c in selected]
    assert "trauma-low-f" not in ids
    assert "keep-normal" in ids
    assert all(c.transfer_kind == TRANSFER_KIND_STANDARD for c in selected)


def test_high_fitness_trauma_becomes_inherited_warning() -> None:
    """High F + trauma → inherited_warning; apply_generation scales somatic."""

    f_high = FITNESS_HIGH_THRESHOLD
    trauma = _candidate(
        DELTA_THRESHOLD_DEEP,
        memory_score=0.95,
        recall_count=GENERATION_MIN_RECALL,
        record_id="warn-me",
    )
    # No drift required for high-fitness inherited warnings.
    selected = select_for_transfer(
        [trauma],
        DriftState(),
        f_agent=f_high,
        reward_marker=5.0,
        threat_marker=0.0,
    )
    assert len(selected) == 1
    assert selected[0].transfer_kind == TRANSFER_KIND_INHERITED_WARNING

    record = GenerationRecord(
        agent_id="parent-0",
        generation=1,
        inherited_memories=["warn-me"],
        inherited_warning_ids=["warn-me"],
        transfer_timestamp=3,
    )
    heir = apply_generation(
        DAUAgentState(
            agent_id="heir-0",
            environment=build_default_constraints(),
        ),
        record,
        memory_store=None,
    )
    assert heir.retrieval_context == [
        {
            RECORD_ID_KEY: "warn-me",
            "generation_inherited": True,
            INHERITED_WARNING_KEY: True,
            SOMATIC_SCALE_KEY: WARNING_SOMATIC_SCALE,
        }
    ]


def test_normal_fitness_uses_w_transfer_and_drift_gate() -> None:
    """Normal F: W_transfer threshold + trauma still needs high drift."""

    f_normal = (FITNESS_LOW_THRESHOLD + FITNESS_HIGH_THRESHOLD) / 2.0
    trauma = _candidate(
        DELTA_THRESHOLD_DEEP,
        memory_score=0.95,
        recall_count=GENERATION_MIN_RECALL,
        record_id="trauma-normal",
    )
    low_drift = DriftState(
        flags={"resource": True},
        magnitudes={"resource": DRIFT_TRANSFER_MIN - 0.1},
    )
    assert (
        select_for_transfer(
            [trauma],
            low_drift,
            f_agent=f_normal,
            reward_marker=5.0,
            threat_marker=0.0,
        )
        == []
    )

    high_drift = DriftState(
        flags={"resource": True},
        magnitudes={"resource": DRIFT_TRANSFER_MIN},
    )
    selected = select_for_transfer(
        [trauma],
        high_drift,
        f_agent=f_normal,
        reward_marker=5.0,
        threat_marker=0.0,
    )
    assert len(selected) == 1
    assert selected[0].transfer_kind == TRANSFER_KIND_STANDARD

    # Below W_transfer threshold even with high drift.
    weak = _candidate(
        0.55,
        memory_score=0.1,
        recall_count=GENERATION_MIN_RECALL,
        record_id="weak",
    )
    assert (
        select_for_transfer(
            [weak],
            DriftState(),
            f_agent=f_normal,
            reward_marker=0.0,
            threat_marker=0.0,
        )
        == []
    )
    assert compute_w_transfer(0.1, f_normal, 0.0, 0.0) < GENERATION_TRANSFER_THRESHOLD
