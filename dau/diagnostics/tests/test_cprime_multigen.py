"""Tests for Protocol C′ multigen orchestration — mock LLM, no API/GPU."""

from __future__ import annotations

import hashlib
import json
import os
import random
from types import SimpleNamespace
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
from dau.diagnostics.preflight import (
    MODE_ABORT,
    MODE_FLAG,
    RUN_QUALITY_CLEAN,
    RUN_QUALITY_FLAGGED,
    RUN_QUALITY_MOCK,
    Preflight,
    PreflightAbort,
    check_determinism_settings,
    arm_digest,
    check_arms_differ,
    check_gated_fraction,
    check_gen2_rng_uniform,
    check_null_untrained,
    check_import_time_env,
    check_memory_written,
    check_ppr_active,
    check_somatic_scale_applied,
    check_lora_choice,
    check_pad_fraction,
    check_pe_event_sufficiency,
    check_precision_saturation,
    check_pythonhashseed,
    check_seed_derivation,
    check_tool_identity,
    run_phase2,
)
from dau.diagnostics.tool_identity import (
    ARM_NULL_NAME,
    LORA_CHOICE_OFF,
    LORA_ENABLED_ENV,
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
# Cumulative extraction past POOL_MAX=100 — the 50-event regime where the
# F_agent pool term runs negative and clamps the score (D-034).
POOL_EXTRACTED: float = 250.0
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


def test_transfer_records_what_f_agent_was_computed_from(store: MemoryStore) -> None:
    """A zero F_agent must be explainable from the results file alone.

    The pilot returned f_agent=0.000 for all nine lineages (D-034) and the
    score by itself cannot say whether the cohort was unfit or the pool term
    clamped it. These two numbers must come from the same reader
    _resolve_f_agent uses, not from a second derivation (CLAUDE.md 2.8).
    """

    from dau.foundation.self_model import f_agent_inputs
    from dau.society.environment import (
        EXTRACTION_KEY_AGENT_ID,
        EXTRACTION_KEY_AMOUNT,
        EXTRACTION_KEY_EVENT,
    )

    parent = _parent_with_transferable_trauma(store, SEED_UNIT)
    # A life that extracted. The default fixture never touches the pool, so
    # delta_pool is 0 there and a report that hardcoded zero would pass — the
    # first version of this test did exactly that until the mutation check
    # caught it (CLAUDE.md 2.4). POOL_EXTRACTED also exceeds POOL_MAX, which
    # is the regime D-034 suspects clamps F_agent to zero.
    import dataclasses

    env = dataclasses.replace(
        parent.env_state,
        extraction_history=[
            {
                EXTRACTION_KEY_AGENT_ID: parent.agent_id,
                EXTRACTION_KEY_AMOUNT: POOL_EXTRACTED,
                EXTRACTION_KEY_EVENT: 1,
            }
        ],
    )
    parent = parent.model_copy(update={"env_state": env})
    expected = f_agent_inputs(parent)
    assert expected["delta_pool"] == POOL_EXTRACTED, "fixture must extract"

    _heir, _record, birth = transfer_to_heir(
        parent_state=parent,
        memory_store=store,
        seed=SEED_UNIT,
        gen1_arm=ARM_UNIT,
    )

    assert birth.f_agent_energy_final == expected["energy_final"]
    assert birth.f_agent_delta_pool == expected["delta_pool"]
    # The regime the record exists to expose: score clamped, inputs readable.
    assert birth.f_agent == 0.0
    assert birth.f_agent_delta_pool > 0.0


def test_f_agent_inputs_is_the_only_reader(store: MemoryStore) -> None:
    """_resolve_f_agent must go through the helper, so both cannot drift.

    Mutation guard: if _resolve_f_agent re-reads the state itself, a change
    to one reader would leave the report describing a score it no longer
    explains.
    """

    from dau.foundation import self_model

    parent = _parent_with_transferable_trauma(store, SEED_UNIT)
    sentinel = {
        "energy_final": 0.5,
        "delta_pool": 12.5,
        "t_survived": 7.0,
        "t_generation": 7.0,
    }
    original = self_model.f_agent_inputs
    try:
        self_model.f_agent_inputs = lambda _state: sentinel
        from dau.generation.fitness import compute_fitness

        assert self_model._resolve_f_agent(parent) == compute_fitness(
            energy_final=0.5, delta_pool=12.5, t_survived=7, t_generation=7
        )
    finally:
        self_model.f_agent_inputs = original


def _gen1(arm: str, decisions: list[str]) -> dict[str, Any]:
    """Minimal gen1 section carrying one arm's phase-2 decision fingerprints."""

    import hashlib

    return {
        "arm": arm,
        "phase2_decision_hashes": [
            hashlib.sha256(d.encode("utf-8")).hexdigest()[
                : multigen_mod.DECISION_HASH_CHARS
            ]
            for d in decisions
        ],
    }


def test_phase2_divergence_counts_events_the_adapter_changed() -> None:
    """The digest says two arms differ; this says how many decisions did.

    In the pilot's seed 2001 all three arm digests differed while pe_after
    was bit-identical (D-034 correction), so "something moved" was all the
    results file could support. NULL is the reference: it is the only arm
    without an adapter and phase 1 is identical across arms.
    """

    divergence = multigen_mod._phase2_decision_divergence(
        {
            ARM_NULL: _gen1(ARM_NULL, ["a", "b", "c", "d"]),
            "lived": _gen1("lived", ["a", "X", "c", "Y"]),
            "shuffle": _gen1("shuffle", ["a", "b", "c", "d"]),
        }
    )

    assert divergence["reference_arm"] == ARM_NULL
    assert divergence["n_phase2_events"] == 4
    assert divergence["n_differing_lived"] == 2
    # An adapter that changed nothing must read as zero, not as missing.
    assert divergence["n_differing_shuffle"] == 0


def test_phase2_divergence_refuses_to_compare_ragged_traces() -> None:
    """None, not a number: an arm that ended early cannot be zipped.

    zip() would silently truncate to the shorter trace and report agreement
    over events one arm never lived.
    """

    divergence = multigen_mod._phase2_decision_divergence(
        {
            ARM_NULL: _gen1(ARM_NULL, ["a", "b", "c", "d"]),
            "lived": _gen1("lived", ["a", "b"]),
        }
    )

    assert divergence["n_differing_lived"] is None


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


def _identity(**overrides: Any) -> dict[str, Any]:
    """Minimal tool-identity shape for the phase-0 checks."""

    identity: dict[str, Any] = {
        "backend": "groq",
        "model_id": "llama-3.1-8b-instant",
        "lora": {"choice": LORA_CHOICE_OFF, "enabled_env": "0"},
    }
    identity.update(overrides)
    return identity


def test_i0_1_rejects_undeterminable_field() -> None:
    passed, detail = check_tool_identity(_identity())
    assert passed is True

    passed, detail = check_tool_identity(_identity(quantization={"quant_type": None}))
    assert passed is False
    assert "quant_type" in detail


def test_i0_2_rejects_choice_env_disagreement() -> None:
    assert check_tool_identity(_identity())[0] is True
    assert check_lora_choice(_identity())[0] is True

    # Choice says off while the env says training is on: the three gate layers
    # downstream would disagree with the results file.
    passed, detail = check_lora_choice(
        _identity(lora={"choice": LORA_CHOICE_OFF, "enabled_env": "1"})
    )
    assert passed is False
    assert "expected" in detail

    passed, _ = check_lora_choice(_identity(lora={"choice": None, "enabled_env": "0"}))
    assert passed is False


def test_i0_3_requires_pinned_hashseed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PYTHONHASHSEED", "0")
    assert check_pythonhashseed()[0] is True

    monkeypatch.delenv("PYTHONHASHSEED", raising=False)
    passed, detail = check_pythonhashseed()
    assert passed is False
    assert "PYTHONHASHSEED=0 python" in detail

    monkeypatch.setenv("PYTHONHASHSEED", "random")
    assert check_pythonhashseed()[0] is False


def test_i0_4_rejects_agent_id_outside_planned_seeds() -> None:
    seeds = [SEED_UNIT]
    ids = [parent_agent_id(ARM_UNIT, SEED_UNIT), heir_agent_id(ARM_UNIT, SEED_UNIT)]
    assert check_seed_derivation(ids, seeds)[0] is True

    passed, detail = check_seed_derivation(
        ids + [parent_agent_id(ARM_UNIT, SEED_UNIT + 1)], seeds
    )
    assert passed is False
    assert "not in planned seeds" in detail
    assert check_seed_derivation([], seeds)[0] is False


def test_i0_5_detects_env_changed_after_import(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bindings = [("N_PAIRS", 15, "DAU_MULTIGEN_N_PAIRS", int)]
    monkeypatch.delenv("DAU_MULTIGEN_N_PAIRS", raising=False)
    assert check_import_time_env(bindings)[0] is True

    monkeypatch.setenv("DAU_MULTIGEN_N_PAIRS", "15")
    assert check_import_time_env(bindings)[0] is True

    monkeypatch.setenv("DAU_MULTIGEN_N_PAIRS", "40")
    passed, detail = check_import_time_env(bindings)
    assert passed is False
    assert "N_PAIRS=15" in detail


def test_i0_6_detects_determinism_off(monkeypatch: pytest.MonkeyPatch) -> None:
    _lock_seeds(SEED_UNIT)
    assert check_determinism_settings()[0] is True

    monkeypatch.delenv("CUBLAS_WORKSPACE_CONFIG", raising=False)
    passed, detail = check_determinism_settings()
    assert passed is False
    assert "CUBLAS_WORKSPACE_CONFIG" in detail


def test_i0_7_detects_adapter_left_by_an_earlier_run(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A seed re-used across runs must not start on the old run's weights.

    Measured 2026-08-10: the 08-09 pilot's cprime-lived-2001-g1 adapter was
    still on disk, so that arm's phase 1 began trained while null — which
    never writes one — began from base. The arms' lives diverged (n_unique
    6/7/6).
    """

    from dau.diagnostics.preflight import check_no_stale_adapters
    from dau.foundation import local_llm

    monkeypatch.setenv("DAU_LLM_BACKEND", "local")
    monkeypatch.setattr(local_llm, "ADAPTER_BASE_DIR", str(tmp_path))
    agent_ids = ["cprime-lived-2001-g1", "cprime-null-2001-g1"]

    passed, detail = check_no_stale_adapters(agent_ids)
    assert passed is True, detail

    leftover = tmp_path / "cprime-lived-2001-g1"
    leftover.mkdir()
    (leftover / local_llm.ADAPTER_CONFIG_FILE).write_text("{}")

    passed, detail = check_no_stale_adapters(agent_ids)
    assert passed is False
    assert "cprime-lived-2001-g1" in detail


def test_i0_7_is_not_applicable_off_the_local_backend(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """None, not True: switch_adapter's disk path is local-only.

    A groq or mock run cannot load a stale adapter, but reporting that as a
    pass would claim the gate checked something it never looked at.
    """

    from dau.diagnostics.preflight import check_no_stale_adapters
    from dau.foundation import local_llm

    monkeypatch.setenv("DAU_LLM_BACKEND", "groq")
    monkeypatch.setattr(local_llm, "ADAPTER_BASE_DIR", str(tmp_path))
    leftover = tmp_path / "cprime-lived-2001-g1"
    leftover.mkdir()
    (leftover / local_llm.ADAPTER_CONFIG_FILE).write_text("{}")

    passed, _ = check_no_stale_adapters(["cprime-lived-2001-g1"])
    assert passed is None


def test_i0_7_runs_in_phase0_under_abort() -> None:
    """The check has to be wired, not merely defined."""

    from dau.diagnostics.preflight import run_phase0

    gate = Preflight()
    run_phase0(
        gate,
        tool_identity=_identity(),
        agent_ids=[],
        seeds=[SEED_UNIT],
        import_time_bindings=[],
    )
    recorded = {r.id: r for r in gate.results}

    assert "I0.7" in recorded
    assert recorded["I0.7"].mode == MODE_ABORT


def test_abort_mode_failure_blocks_the_run() -> None:
    gate = Preflight()
    gate.record("I0.3", False, mode=MODE_ABORT, detail="unset")
    with pytest.raises(PreflightAbort) as excinfo:
        gate.enforce()
    assert "I0.3" in str(excinfo.value)
    assert gate.run_quality() == "aborted"


def test_broken_check_counts_as_failure() -> None:
    """A check that raises must not read as a check that passed."""

    gate = Preflight()

    def _boom() -> tuple[bool, str]:
        raise RuntimeError("sensor unplugged")

    gate.check("I0.1", _boom, mode=MODE_ABORT)
    assert gate.invariants()["I0.1"] is False
    assert "sensor unplugged" in gate.details()["I0.1"]["detail"]


def test_i3_1_detects_starved_pe_log() -> None:
    full = [{"n_pe_events_audited": 10}, {"n_pe_events_audited": 10}]
    assert check_pe_event_sufficiency(
        full, expected_per_section=10, min_fraction=0.5
    )[0] is True

    starved = [{"n_pe_events_audited": 2}, {"n_pe_events_audited": 2}]
    passed, detail = check_pe_event_sufficiency(
        starved, expected_per_section=10, min_fraction=0.5
    )
    assert passed is False
    assert "4/20" in detail


def test_i3_2_detects_saturated_sensor() -> None:
    healthy = {
        "n_pe_events_audited": 100,
        "saturation_rate": 0.002,
        "pi_n_distinct": 14,
    }
    assert check_precision_saturation(
        healthy, max_rate=0.05, min_distinct=8
    )[0] is True

    saturated = {
        "n_pe_events_audited": 100,
        "saturation_rate": 0.9,
        "pi_n_distinct": 1,
    }
    passed, detail = check_precision_saturation(
        saturated, max_rate=0.05, min_distinct=8
    )
    assert passed is False
    assert "saturation_rate" in detail and "pi_n_distinct" in detail

    # Zero audited events must not read as zero saturation (GAP-13).
    passed, detail = check_precision_saturation(
        {"n_pe_events_audited": 0, "saturation_rate": 0.0, "pi_n_distinct": 0},
        max_rate=0.05,
        min_distinct=8,
    )
    assert passed is False
    assert "cannot be assessed" in detail


def test_i3_3_detects_too_many_gated_arms() -> None:
    sections = [{"gated": False}] * 4 + [{"gated": True}]
    assert check_gated_fraction(sections, max_fraction=0.20)[0] is True

    sections = [{"gated": True}] * 3 + [{"gated": False}] * 2
    passed, detail = check_gated_fraction(sections, max_fraction=0.20)
    assert passed is False
    assert "3/5" in detail


def test_i3_4_flags_any_padding() -> None:
    unpadded = [{"n_pe_events_audited": 10}]
    assert check_pad_fraction(
        unpadded, expected_per_section=10, max_fraction=0.0
    )[0] is True

    padded = [{"n_pe_events_audited": 7}]
    passed, detail = check_pad_fraction(
        padded, expected_per_section=10, max_fraction=0.0
    )
    assert passed is False
    assert "3/10 padded" in detail


def test_i2_1_detects_identical_arms() -> None:
    """GAP-1's actual consequence: three copies of one experiment."""

    distinct = [
        {"seed": 1, "arm": arm, "arm_digest": digest}
        for arm, digest in (("lived", "a"), ("null", "b"), ("shuffle", "c"))
    ]
    assert check_arms_differ(distinct)[0] is True

    identical = [
        {"seed": 1, "arm": arm, "arm_digest": "same"}
        for arm in ("lived", "null", "shuffle")
    ]
    passed, detail = check_arms_differ(identical)
    assert passed is False
    assert "identical arms" in detail

    passed, _ = check_arms_differ([{"seed": 1, "arm": "lived"}])
    assert passed is False


def test_arm_digest_separates_equal_decisions_with_different_pe() -> None:
    """Decisions alone are not enough — same words, different PE is real."""

    decisions = ["cooperate", "defect"]
    assert arm_digest(decisions, [0.1, 0.2]) != arm_digest(decisions, [0.1, 0.3])
    assert arm_digest(decisions, [0.1, 0.2]) == arm_digest(decisions, [0.1, 0.2])
    assert arm_digest(["defect", "cooperate"], [0.1, 0.2]) != arm_digest(
        decisions, [0.1, 0.2]
    )


def test_i2_2_detects_trained_or_contaminated_null() -> None:
    clean = [{"arm": "null", "n_pairs_trained": 0, "adapter_present": False}]
    assert check_null_untrained(clean)[0] is True

    trained = [{"arm": "null", "n_pairs_trained": 4, "adapter_present": False}]
    passed, detail = check_null_untrained(trained)
    assert passed is False
    assert "trained pairs" in detail

    stale = [{"arm": "null", "n_pairs_trained": 0, "adapter_present": True}]
    passed, detail = check_null_untrained(stale)
    assert passed is False
    assert "adapter on disk" in detail

    assert check_null_untrained([{"arm": "lived"}])[0] is False


def test_arm_null_name_matches_runner() -> None:
    assert ARM_NULL_NAME == ARM_NULL


def test_i2_1_is_flag_under_mock_and_abort_otherwise() -> None:
    """Canned decisions make arms identical by design (D-012 exception)."""

    identical = [
        {"seed": 1, "arm": arm, "arm_digest": "same"}
        for arm in ("lived", "null", "shuffle")
    ]
    real = Preflight(mock=False)
    run_phase2(real, gen1_sections=identical)
    with pytest.raises(PreflightAbort):
        real.enforce()

    mocked = Preflight(mock=True)
    run_phase2(mocked, gen1_sections=identical)
    mocked.enforce()  # must not raise
    assert mocked.invariants()["I2.1"] is False


def test_i4_2_detects_arm_dependent_rng_entry() -> None:
    same = [
        {"seed": 1, "gen1_arm": arm, "rng_digest": "abc"}
        for arm in ("lived", "null", "shuffle")
    ]
    assert check_gen2_rng_uniform(same)[0] is True

    diverged = [
        {"seed": 1, "gen1_arm": "lived", "rng_digest": "abc"},
        {"seed": 1, "gen1_arm": "null", "rng_digest": "def"},
    ]
    passed, detail = check_gen2_rng_uniform(diverged)
    assert passed is False
    assert "RNG states" in detail

    # A missing digest is not agreement.
    passed, _ = check_gen2_rng_uniform([{"seed": 1, "gen1_arm": "lived"}])
    assert passed is False


def test_i5_1_detects_inert_ppr() -> None:
    assert check_ppr_active([{"memory_edges": 4}, {"memory_edges": 0}])[0] is True

    passed, detail = check_ppr_active([{"memory_edges": 0}, {"memory_edges": 0}])
    assert passed is False
    assert "inert" in detail

    # An unreadable store is not an empty graph.
    passed, detail = check_ppr_active([{"memory_edges": -1}])
    assert passed is False
    assert "unreadable" in detail


def test_i5_3_detects_life_that_wrote_nothing() -> None:
    lives = [{"agent_id": "a", "memory_written": 3}]
    assert check_memory_written(lives)[0] is True

    lives = [{"agent_id": "a", "memory_written": 3}, {"agent_id": "b", "memory_written": 0}]
    passed, detail = check_memory_written(lives)
    assert passed is False
    assert "b" in detail


def test_i5_4_detects_somatic_scale_never_applied() -> None:
    from dau.foundation.emotional_weight import (
        EmotionalWeight,
        apply_inherited_somatic_scale,
        reset_somatic_scale_stats,
    )

    reset_somatic_scale_stats()
    ew = EmotionalWeight(somatic_markers={"threat": 0.5})
    apply_inherited_somatic_scale(ew, [])
    passed, detail = check_somatic_scale_applied()
    assert passed is False
    assert "never applied" in detail

    apply_inherited_somatic_scale(
        ew, [{"inherited_warning": True, "somatic_scale": -0.3}]
    )
    assert check_somatic_scale_applied()[0] is True
    reset_somatic_scale_stats()


def test_count_edges_reports_zero_on_empty_graph(store: MemoryStore) -> None:
    """I5.1's data source: an empty graph counts zero, it does not error."""

    assert store.count_edges() == 0


def test_flag_failure_does_not_stop_the_run() -> None:
    """FLAG labels the result; only ABORT withholds it."""

    gate = Preflight()
    gate.record("I3.2", False, mode=MODE_FLAG, detail="saturated")
    gate.enforce()  # must not raise
    assert gate.run_quality() == RUN_QUALITY_FLAGGED


def test_not_applicable_is_not_a_pass() -> None:
    gate = Preflight()
    gate.record("I1.1", None, mode=MODE_ABORT, detail="no training in mock")
    gate.enforce()  # None must not trip the abort
    assert gate.invariants()["I1.1"] is None
    assert gate.run_quality() == RUN_QUALITY_CLEAN


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


def test_install_mock_llm_pins_groq_when_backend_unset(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """D-018 flipped the default to local; the mock still needs the groq branch.

    _build_llm is only called by the groq branch of agent_node, so an unset
    variable would send a mock run down the local branch and load the real
    model. The setdefault states that requirement, and must survive the
    default flip.
    """

    from dau.foundation.graph import LLM_BACKEND_ENV, LLM_BACKEND_GROQ

    monkeypatch.delenv(LLM_BACKEND_ENV, raising=False)
    previous = multigen_mod.install_mock_llm()
    try:
        assert os.environ[LLM_BACKEND_ENV] == LLM_BACKEND_GROQ
    finally:
        multigen_mod.restore_llm_builder(previous)


def test_install_mock_llm_does_not_override_explicit_backend(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """setdefault, not set: an explicit choice by the runner still wins."""

    from dau.foundation.graph import LLM_BACKEND_ENV, LLM_BACKEND_LOCAL

    monkeypatch.setenv(LLM_BACKEND_ENV, LLM_BACKEND_LOCAL)
    previous = multigen_mod.install_mock_llm()
    try:
        assert os.environ[LLM_BACKEND_ENV] == LLM_BACKEND_LOCAL
    finally:
        multigen_mod.restore_llm_builder(previous)


def test_multigen_smoke_mock_llm_end_to_end(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """N=1, events=5 mock path writes gen1/transfer/gen2 JSON sections."""

    monkeypatch.setenv(MOCK_LLM_ENV, "1")
    # LoRA off is now a stated choice, not an env default we lean on (GAP-1).
    monkeypatch.setenv(LORA_ENABLED_ENV, "1")
    monkeypatch.setenv("DAU_LLM_BACKEND", "groq")
    monkeypatch.setenv("PYTHONHASHSEED", "0")
    gate = Preflight(mock=True)
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
        lora=False,
        preflight=gate,
    )
    # The stated choice wins over the environment, so the three gate layers
    # downstream cannot disagree with what the JSON reports.
    assert os.environ[LORA_ENABLED_ENV] == "0"
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
        # D-035 item 3 wiring. The unit test for the comparison passed while
        # the runner never populated these — removing the assignment left the
        # suite green, which is the empty-guard case CLAUDE.md 2.4 warns about.
        assert lin.gen1["phase2_decision_hashes"], "phase-2 fingerprints missing"
        # D-036: the endpoint must be checkable against the trace it averages.
        assert lin.gen1["pe_before_list"], "gen1 phase-1 PE trace missing"
        assert lin.gen1["pe_after_list"], "gen1 phase-2 PE trace missing"
        assert lin.gen1["pe_before"] == pytest.approx(
            sum(lin.gen1["pe_before_list"]) / len(lin.gen1["pe_before_list"])
        ), "pe_before must be the mean of the whole phase, not a prefix"
        # D-035 item 1: a zero F_agent has to be explainable from the file.
        assert "f_agent_delta_pool" in lin.transfer
        assert "f_agent_energy_final" in lin.transfer

    divergence = results[0].phase2_decision_divergence
    assert divergence["reference_arm"] == ARM_NULL
    assert divergence["n_phase2_events"] > 0
    # Mock decisions are canned, so lived cannot differ from null here — but
    # the key must exist and be a number, not absent.
    assert divergence["n_differing_lived"] == 0

    out = tmp_path / "multigen_smoke.json"
    path = write_multigen_results_json(
        results,
        lora_choice=LORA_CHOICE_OFF,
        preflight=gate,
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
    # A mock run must never read as clean: canned decisions make the arms
    # identical by construction.
    assert doc["run_quality"] in {RUN_QUALITY_MOCK, RUN_QUALITY_FLAGGED}
    assert doc["run_quality"] != RUN_QUALITY_CLEAN
    assert set(doc["invariants"]) >= {
        "I0.1", "I0.2", "I0.3", "I0.4", "I0.5", "I0.6",
        "I3.1", "I3.2", "I3.3", "I3.4", "I5.2",
    }
    # Every phase-0 invariant is ABORT, so reaching this line proves they held.
    assert all(
        doc["invariants"][f"I0.{i}"] is True for i in range(1, 7)
    )

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


# ---------------------------------------------------------------------------
# D-031 / GAP-14 — consolidation on the experiment path
# ---------------------------------------------------------------------------


def test_consolidation_runs_after_phase2_not_between_phases(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The NULL arm's delta_pe must stay a measurement of "no training".

    Consolidation deletes memories, so a pass between phase-1 and phase-2
    would move pe_after for every arm — including NULL, which never trains.
    The control would then report a non-zero delta_pe made entirely of
    forgetting. This asserts the call order, which is what protects it.
    """

    order: list[str] = []

    monkeypatch.setattr(
        multigen_mod,
        "run_gen1_arm_lineage",
        lambda **kw: (
            order.append("gen1"),
            (
                SimpleNamespace(seed=kw["seed"], arm=kw["arm"]),
                SimpleNamespace(event_log=[1, 2, 3]),
                object(),
                None,
            ),
        )[1],
    )
    monkeypatch.setattr(
        multigen_mod,
        "_consolidate_gen1",
        lambda **_kw: (order.append("consolidate"), {"ran": True})[1],
    )
    monkeypatch.setattr(
        multigen_mod,
        "transfer_to_heir",
        lambda **_kw: (
            order.append("transfer"),
            (object(), object(), SimpleNamespace()),
        )[1],
    )
    monkeypatch.setattr(
        multigen_mod,
        "run_gen2_measure",
        lambda **_kw: (order.append("gen2"), SimpleNamespace())[1],
    )
    monkeypatch.setattr(multigen_mod, "asdict", lambda obj: {})

    multigen_mod.run_lineage(
        seed=2001,
        arm=ARM_UNIT,
        events_gen1=2,
        events_gen2=2,
        k_gen2=1,
        pe_window_gen2=2,
    )

    assert order == ["gen1", "consolidate", "transfer", "gen2"], order


def test_consolidation_report_reaches_the_lineage_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Deletions change what the heir inherits — the run must record them."""

    from dau.foundation.state import DAUAgentState

    captured = {}

    class _Store:
        pass

    def _fake_consolidate(agent_id, counter, store):
        captured["agent_id"] = agent_id
        captured["counter"] = counter
        return SimpleNamespace(
            deleted_count=3,
            strengthened_count=2,
            edges_created=5,
            drift_flag_count=1,
        )

    monkeypatch.setattr(multigen_mod, "consolidate_run", _fake_consolidate)

    payload = multigen_mod._consolidate_gen1(
        agent_id="cprime-lived-2001-g1",
        state=SimpleNamespace(event_log=[0, 1, 2, 3]),
        store=_Store(),
    )

    assert payload == {
        "ran": True,
        "now_counter": 4,
        "deleted_count": 3,
        "strengthened_count": 2,
        "edges_created": 5,
        "drift_flag_count": 1,
    }
    assert captured["agent_id"] == "cprime-lived-2001-g1"
    assert captured["counter"] == 4


def test_consolidation_failure_is_not_swallowed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A silently skipped sleep would leave the JSON claiming one happened."""

    def _boom(*_a, **_k):
        raise RuntimeError("store exploded")

    monkeypatch.setattr(multigen_mod, "consolidate_run", _boom)

    with pytest.raises(RuntimeError):
        multigen_mod._consolidate_gen1(
            agent_id="a",
            state=SimpleNamespace(event_log=[0]),
            store=object(),
        )
