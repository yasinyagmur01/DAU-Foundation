"""Tests for Protocol C′ multigen orchestration — mock LLM, no API/GPU."""

from __future__ import annotations

import hashlib
import json
import random
from typing import Any
from unittest.mock import patch

import numpy as np
import pytest

import dau.diagnostics.run_cprime_multigen as multigen_mod
from dau.diagnostics.run_cprime_multigen import (
    MOCK_LLM_ENV,
    heir_agent_id,
    parent_agent_id,
    run_cprime_multigen,
    run_gen1_arm_lineage,
    run_gen2_measure,
    transfer_to_heir,
    write_multigen_results_json,
)
from dau.diagnostics.run_protocol_c_prime import (
    ARM_NULL,
    PE_W_SATURATION_VALUE,
    _lock_seeds,
)
from dau.foundation.drift import DriftState
from dau.foundation.generation import (
    GENERATION_INHERITED_KEY,
    GENERATION_MIN_RECALL,
    INHERITED_WARNING_KEY,
    RECORD_ID_KEY,
    SOMATIC_SCALE_KEY,
)
from dau.foundation.state import DAUAgentState, DeltaRecord, InternalState
from dau.generation.fitness import WARNING_SOMATIC_SCALE
from dau.memory.decay import compute_strength_init
from dau.memory.store import MemoryStore
from dau.diagnostics.run_protocol_c_prime import _initial_state
from dau.society.environment import EnvironmentState


SEED_UNIT: int = 9101
ARM_UNIT: str = "lived"
EVENTS_SMOKE: int = 5
N_SMOKE: int = 1


def _trauma_delta(timestamp: int = 3) -> DeltaRecord:
    snap = {
        "energy": 1.0,
        "resource_load": 0.0,
        "uncertainty_load": 0.0,
        "social_load": 0.0,
    }
    return DeltaRecord(
        timestamp=timestamp,
        magnitude=0.9,
        affected_domain="resource",
        snapshot_before=snap,
        snapshot_after={
            "energy": 0.2,
            "resource_load": 0.8,
            "uncertainty_load": 0.0,
            "social_load": 0.0,
        },
    )


@pytest.fixture
def store(tmp_path):
    ms = MemoryStore(
        chroma_path=str(tmp_path / "chroma"),
        sqlite_path=str(tmp_path / "memory.db"),
    )
    yield ms
    ms.close()


def _parent_with_transferable_trauma(store: MemoryStore, seed: int) -> DAUAgentState:
    """Parent state + vault engram that select_for_transfer can keep."""

    parent_id = parent_agent_id(ARM_UNIT, seed)
    parent = _initial_state(parent_id, seed)
    delta = _trauma_delta()
    record_id = store.write_record(delta, parent_id)
    assert record_id
    # Recall bumps strength above strength_init → recall_count >= 1.
    store.update_activation(record_id, now_counter=int(delta.timestamp) + 1)
    node = store.get_node(record_id)
    assert node is not None
    assert node.strength - compute_strength_init(delta) >= GENERATION_MIN_RECALL

    drifted = DriftState(
        flags={"resource": True},
        magnitudes={"resource": 2.0},
    )
    # Low energy → f_agent < FITNESS_LOW_THRESHOLD so trauma → inherited_warning.
    return parent.model_copy(
        update={
            "drift_state": drifted,
            "delta_log": [delta, _trauma_delta(timestamp=6)],
            "event_log": parent.event_log,
            "internal_state": InternalState(energy=0.05),
            "env_state": EnvironmentState(pool=40.0),
            "generation": 0,
        }
    )


def test_gen2_orchestration_applies_inheritance_before_first_invoke(
    store: MemoryStore,
) -> None:
    """apply_generation fills retrieval_context before any graph stream."""

    parent = _parent_with_transferable_trauma(store, SEED_UNIT)
    # Force low F via energy so trauma → inherited_warning when selected.
    # build_self_model computes f_agent; low energy helps stay below threshold.
    assert parent.internal_state.energy < 0.5

    stream_calls: list[Any] = []

    class _BoomApp:
        def stream(self, *_args: Any, **_kwargs: Any):
            stream_calls.append(True)
            raise AssertionError("gen2 graph must not run during transfer")

    with patch(
        "dau.diagnostics.run_cprime_multigen.build_graph",
        return_value=_BoomApp(),
    ):
        heir, record, birth = transfer_to_heir(
            parent_state=parent,
            memory_store=store,
            seed=SEED_UNIT,
            gen1_arm=ARM_UNIT,
        )

    assert stream_calls == []
    assert heir.agent_id == heir_agent_id(ARM_UNIT, SEED_UNIT)
    assert heir.event_log == []
    assert heir.delta_log == []
    assert heir.generation == parent.generation + 1
    assert heir.generation_record is record
    assert birth.n_transfer_candidates == len(record.inherited_memories)
    assert birth.birth_drift_flags.get("resource") is True

    # A13/A40: inherited markers present on heir BEFORE first invoke.
    assert heir.retrieval_context, "heir must carry inherited retrieval_context"
    inherited = [
        e for e in heir.retrieval_context if e.get(GENERATION_INHERITED_KEY) is True
    ]
    assert inherited, "expected generation_inherited entries"
    # When fitness/selection marks warning, somatic markers must appear.
    if record.inherited_warning_ids:
        warn_entries = [e for e in inherited if e.get(INHERITED_WARNING_KEY) is True]
        assert warn_entries
        assert all(SOMATIC_SCALE_KEY in e for e in warn_entries)
        assert all(
            e[SOMATIC_SCALE_KEY] == -WARNING_SOMATIC_SCALE
            or abs(float(e[SOMATIC_SCALE_KEY])) == WARNING_SOMATIC_SCALE
            for e in warn_entries
        )
    assert all(RECORD_ID_KEY in e for e in inherited)


def test_transfer_logs_birth_drift_independent_of_gen2_pe(store: MemoryStore) -> None:
    """Birth-drift log is produced at transfer time (channel diagnosis)."""

    parent = _parent_with_transferable_trauma(store, SEED_UNIT)
    heir, _record, birth = transfer_to_heir(
        parent_state=parent,
        memory_store=store,
        seed=SEED_UNIT,
        gen1_arm=ARM_UNIT,
    )
    assert birth.heir_agent_id == heir.agent_id
    assert birth.gen1_arm == ARM_UNIT
    assert "resource" in birth.birth_drift_magnitudes
    assert birth.n_retrieval_context == len(heir.retrieval_context)


def _rng_digest() -> str:
    """Fingerprint of every RNG _lock_seeds pins (torch optional)."""

    digest = hashlib.sha256()
    digest.update(repr(random.getstate()).encode("utf-8"))
    digest.update(repr(np.random.get_state()).encode("utf-8"))
    try:
        import torch
    except ImportError:
        pass
    else:
        digest.update(torch.random.get_rng_state().numpy().tobytes())
    return digest.hexdigest()


def _burn_rng(n_draws: int) -> None:
    """Stand in for the RNG an arm consumes before gen2 (DPO, shuffle)."""

    for _ in range(n_draws):
        random.random()
    np.random.random(n_draws + 1)
    try:
        import torch
    except ImportError:
        pass
    else:
        torch.rand(n_draws + 1)


def test_gen2_measure_locks_rng_for_every_arm(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """GAP-12: heirs must enter gen2 from one RNG state, not three.

    lived/shuffle run DPO between gen1 and gen2 and consume torch RNG; null
    does not; shuffle additionally permutes pairs from Python RNG. Unlocked,
    the arm contrast would carry an RNG contrast inside it.
    """

    # _lock_seeds writes these; declare them so monkeypatch restores them.
    monkeypatch.setenv("DAU_LLM_SEED", "0")
    monkeypatch.setenv("DAU_LLM_TEMPERATURE", "0.2")

    digests: dict[str, str] = {}

    def _fake_life(*, agent_id, seed, n_events, store, initial):
        digests[str(agent_id)] = _rng_digest()
        return [0.25] * n_events, [], [], initial

    monkeypatch.setattr(multigen_mod, "run_life_keep_vault", _fake_life)

    for arm, n_draws in (("lived", 7), ("null", 0), ("shuffle", 31)):
        _burn_rng(n_draws)
        heir_id = heir_agent_id(arm, SEED_UNIT)
        heir = _initial_state(heir_id, SEED_UNIT)
        run_gen2_measure(
            heir=heir,
            store=None,
            seed=SEED_UNIT,
            gen1_arm=arm,
            events_gen2=EVENTS_SMOKE,
            k_gen2=1,
            pe_window=EVENTS_SMOKE,
        )

    assert len(digests) == 3
    assert len(set(digests.values())) == 1, (
        f"heirs entered gen2 from different RNG states: {digests}"
    )

    # Equality alone could be an accident; pin it to the lock itself.
    _burn_rng(13)
    _lock_seeds(SEED_UNIT)
    assert set(digests.values()) == {_rng_digest()}


def _pe_rows(pe_w_values: list[float], pi_values: list[float]) -> list[dict[str, Any]]:
    """pe_event_log rows shaped as _precision_audit_from_pe_rows reads them."""

    return [
        {"prediction_error": pe_w, "precision_weight": pi}
        for pe_w, pi in zip(pe_w_values, pi_values)
    ]


class _FakeTmp:
    def cleanup(self) -> None:
        return None


def test_gen1_arm_result_carries_precision_audit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """GAP-13: multigen dropped the audit rows and shipped default zeros."""

    sat = PE_W_SATURATION_VALUE
    row_groups = [
        _pe_rows([sat, 0.4, 0.4], [0.5, 0.6, 0.5]),  # phase-1
        _pe_rows([sat, 0.2], [0.7, 0.5]),  # phase-2
    ]

    def _fake_life(*, agent_id, seed, n_events, store, initial):
        rows = row_groups.pop(0)
        return [0.3] * n_events, [], rows, _initial_state(agent_id, seed)

    monkeypatch.setattr(multigen_mod, "run_life_keep_vault", _fake_life)
    monkeypatch.setattr(
        multigen_mod,
        "_open_lineage_store",
        lambda: (None, _FakeTmp()),
    )

    # null arm: no training, so the audit is the only thing under test here.
    arm_result, _state, _store, _tmp = run_gen1_arm_lineage(
        seed=SEED_UNIT,
        arm=ARM_NULL,
        events_gen1=EVENTS_SMOKE,
    )

    # Both phases audited, not just one.
    assert arm_result.n_pe_events_audited == 5
    assert arm_result.n_saturated == 2
    assert arm_result.saturation_rate == pytest.approx(0.4)
    assert arm_result.pi_n_distinct == 3
    assert arm_result.pi_values == [0.5, 0.6, 0.5, 0.7, 0.5]


def test_gen2_result_carries_precision_audit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The heir needs its own instrument health — gen1's does not cover it."""

    sat = PE_W_SATURATION_VALUE
    rows = _pe_rows([sat, 0.3, 0.3, 0.3], [0.9, 0.9, 0.4, 0.2])

    def _fake_life(*, agent_id, seed, n_events, store, initial):
        return [0.3] * n_events, [], rows, initial

    monkeypatch.setattr(multigen_mod, "run_life_keep_vault", _fake_life)

    heir = _initial_state(heir_agent_id(ARM_UNIT, SEED_UNIT), SEED_UNIT)
    gen2 = run_gen2_measure(
        heir=heir,
        store=None,
        seed=SEED_UNIT,
        gen1_arm=ARM_UNIT,
        events_gen2=EVENTS_SMOKE,
        k_gen2=1,
        pe_window=EVENTS_SMOKE,
    )

    assert gen2.n_pe_events_audited == 4
    assert gen2.n_saturated == 1
    assert gen2.saturation_rate == pytest.approx(0.25)
    assert gen2.pi_n_distinct == 3
    assert gen2.pi_values == [0.9, 0.9, 0.4, 0.2]


def test_multigen_smoke_mock_llm_end_to_end(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """N=1, events=5 mock path writes gen1/transfer/gen2 JSON sections."""

    monkeypatch.setenv(MOCK_LLM_ENV, "1")
    monkeypatch.setenv("DAU_LORA_ENABLED", "0")
    monkeypatch.setenv("DAU_LLM_BACKEND", "groq")
    # Keep MiniLM out of the critical path when available stub is cleaner.
    monkeypatch.setattr(
        "dau.foundation.graph._prediction_error",
        lambda expected, actual: 0.25 + (len(str(actual)) % 7) * 0.05,
    )

    results = run_cprime_multigen(
        n_pairs=N_SMOKE,
        seed_start=SEED_UNIT,
        events_gen1=EVENTS_SMOKE,
        events_gen2=EVENTS_SMOKE,
        k_gen2=1,
        pe_window_gen2=EVENTS_SMOKE,
        mock_llm=True,
    )
    assert len(results) == 1
    assert len(results[0].lineages) == 3
    arms = {lin.gen1_arm for lin in results[0].lineages}
    assert arms == {"lived", "null", "shuffle"}

    for lin in results[0].lineages:
        assert "pe_before" in lin.gen1
        assert "n_transfer_candidates" in lin.transfer
        assert "birth_drift_flags" in lin.transfer
        assert lin.gen2["gen1_arm"] == lin.gen1_arm
        assert "mean_pe" in lin.gen2
        assert lin.transfer["heir_agent_id"].endswith("-g2")

    out = tmp_path / "multigen_smoke.json"
    path = write_multigen_results_json(
        results,
        path=out,
        events_gen1=EVENTS_SMOKE,
        events_gen2=EVENTS_SMOKE,
        k_gen2=1,
        n_pairs=N_SMOKE,
        seed_start=SEED_UNIT,
        pe_window_gen2=EVENTS_SMOKE,
    )
    # GAP-13: default zeros read as "no saturation" but mean "never measured".
    # A run whose instrument health is all zeros must not look healthy.
    doc = json.loads(path.read_text(encoding="utf-8"))
    for lineage in doc["pairs"][0]["lineages"]:
        for generation in ("gen1", "gen2"):
            section = lineage[generation]
            assert section["n_pe_events_audited"] > 0, generation
            assert section["pi_values"], generation
            assert section["pi_n_distinct"] > 0, generation
    audit = doc["summary"]["precision_audit"]
    assert audit["gen1"]["n_pe_events_audited"] > 0
    assert audit["gen2"]["n_pe_events_audited"] > 0
    # Descriptive block only — the verdict belongs to the preflight gate (I3.2).
    assert "saturation_pass" not in audit["gen1"]

    payload = path.read_text(encoding="utf-8")
    assert "C_PRIME_MULTIGEN" in payload
    assert "transfer" in payload
    assert "gen2" in payload
    assert "gen1_arm" in payload
