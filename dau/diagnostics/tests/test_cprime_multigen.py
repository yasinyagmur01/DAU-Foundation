"""Tests for Protocol C′ multigen orchestration — mock LLM, no API/GPU."""

from __future__ import annotations

import hashlib
import json
import math
import os
import random
import statistics
from dataclasses import asdict
from types import SimpleNamespace
from typing import Any
from unittest.mock import patch

import numpy as np
import pytest

import dau.diagnostics.run_cprime_multigen as multigen_mod
import dau.foundation.graph as graph_mod
import dau.foundation.constraints as C
import dau.diagnostics.tool_identity as tool_identity_mod
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
    MODE_REPORT,
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
    check_replay_identical,
    check_gradient_clipping,
    check_gradient_step_taken,
    check_pair_count_sufficient,
    check_pairs_survived_filter,
    check_training_moved_weights,
    check_import_time_env,
    check_memory_written,
    check_ppr_active,
    check_somatic_scale_applied,
    check_lora_choice,
    check_early_termination_fraction,
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
    build_tool_identity,
)
from dau.foundation.drift import DriftState
from dau.foundation.generation import (
    GENERATION_INHERITED_KEY,
    consolidate_generation,
    GENERATION_MIN_RECALL,
    INHERITED_WARNING_KEY,
    RECORD_ID_KEY,
    SOMATIC_SCALE_KEY,
)
from dau.foundation.state import DAUAgentState, DeltaRecord, Event, InternalState
from dau.generation.fitness import (
    FITNESS_W_ENERGY,
    FITNESS_W_POOL,
    FITNESS_W_SURVIVAL,
    WARNING_SOMATIC_SCALE,
)
from dau.memory.decay import compute_strength_init
from dau.memory.store import MemoryStore
from dau.diagnostics.run_protocol_c_prime import _initial_state
from dau.society.environment import EnvironmentState


SEED_UNIT: int = 9101
ARM_UNIT: str = "lived"
# Cumulative extraction far past what a life of this length could sustainably
# take — the regime where the F_agent pool term runs negative and clamps the
# score (D-034).
POOL_EXTRACTED: float = 250.0
# F_agent's survival denominator: the generation's event budget (K4-b, D-070).
# Deliberately larger than the unit fixtures' event logs, so a survival term
# that silently went back to t_survived/t_survived would read 1.0 instead.
EVENTS_GEN1_UNIT: int = 50
EVENT_TYPE_LANDMARK: str = "landmark-probe"
# E3: two agents whose event rows land in the same buffer. Every reader has to
# say whose rows it wants, so the fixtures carry an owner.
AGENT_A: str = "cprime-unit-agentA"
AGENT_B: str = "cprime-unit-agentB"
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
            events_gen1=EVENTS_GEN1_UNIT,
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
        events_gen1=EVENTS_GEN1_UNIT,
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
    expected = f_agent_inputs(parent, EVENTS_GEN1_UNIT)
    assert expected["delta_pool"] == POOL_EXTRACTED, "fixture must extract"

    _heir, _record, birth = transfer_to_heir(
        parent_state=parent,
        memory_store=store,
        seed=SEED_UNIT,
        gen1_arm=ARM_UNIT,
        events_gen1=EVENTS_GEN1_UNIT,
    )

    assert birth.f_agent_energy_lived == expected["energy_lived"]
    assert birth.f_agent_delta_pool == expected["delta_pool"]
    # K4-b: the pool term is a rate now, so the record has to carry both
    # halves of it. Reporting delta_pool alone would leave the same number
    # meaning two different things depending on how long the life ran.
    assert birth.f_agent_t_survived == expected["t_survived"]
    assert birth.f_agent_t_generation == expected["t_generation"]
    assert birth.f_agent_t_generation == float(EVENTS_GEN1_UNIT)
    # The budget must be the generation's, not the agent's own lifespan —
    # that identity is what pinned the survival term at 1.0 (D-070).
    assert birth.f_agent_t_survived < birth.f_agent_t_generation
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
    # t_generation deliberately unequal to t_survived: if _resolve_f_agent
    # ignored the helper and rebuilt the reads, it would land back on the
    # agent's own lifespan for both and the survival term would be 1.0.
    sentinel = {
        "energy_lived": 0.5,
        "delta_pool": 12.5,
        "t_survived": 7.0,
        "t_generation": 20.0,
    }
    original = self_model.f_agent_inputs
    try:
        self_model.f_agent_inputs = lambda _state, _t_generation: sentinel
        from dau.generation.fitness import compute_fitness

        assert self_model._resolve_f_agent(
            parent, EVENTS_GEN1_UNIT
        ) == compute_fitness(
            energy_lived=0.5, delta_pool=12.5, t_survived=7, t_generation=20
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


def test_i0_6_rejects_warn_only_determinism(monkeypatch: pytest.MonkeyPatch) -> None:
    """D-037. warn_only is a failure now, not a footnote.

    Measured on four controlled runs of seed 2001: under warn_only the two
    trained arms produced different adapter weights and flipped 21/50 and
    23/50 phase-2 decisions between runs, while NULL stayed bit-exact. Under
    strict the same comparison gave 0/50. The flag is checked through torch's
    own state rather than the constant, so a runner that forgets to lock is
    caught too.
    """

    torch = pytest.importorskip("torch")

    _lock_seeds(SEED_UNIT)
    assert check_determinism_settings()[0] is True

    torch.use_deterministic_algorithms(True, warn_only=True)
    try:
        passed, detail = check_determinism_settings()
        assert passed is False
        assert "warn_only" in detail
    finally:
        _lock_seeds(SEED_UNIT)


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
    """A row per event LIVED, not per event budgeted (D-073)."""

    full = [
        {"n_pe_events_audited": 10, "events_lived": 10},
        {"n_pe_events_audited": 10, "events_lived": 10},
    ]
    assert check_pe_event_sufficiency(full, min_fraction=0.5)[0] is True

    starved = [
        {"n_pe_events_audited": 2, "events_lived": 10},
        {"n_pe_events_audited": 2, "events_lived": 10},
    ]
    passed, detail = check_pe_event_sufficiency(starved, min_fraction=0.5)
    assert passed is False
    assert "4/20" in detail


def test_i3_1_does_not_call_a_short_life_a_starved_instrument() -> None:
    """The whole point of the D-073 denominator change.

    Since D-066 lineages die early by design, and against the event BUDGET
    this check reported the universe working as intended as an instrument
    fault. Same rows, same budget, different denominators: an agent that lived
    12 events and logged 12 of them has a healthy sensor.
    """

    short_lives = [
        {"n_pe_events_audited": 12, "events_lived": 12},
        {"n_pe_events_audited": 11, "events_lived": 11},
    ]
    passed, detail = check_pe_event_sufficiency(short_lives, min_fraction=0.5)
    assert passed is True
    assert "23/23" in detail

    # And the fault it does exist to catch is still caught: same short rows,
    # but the lives ran to the full budget.
    broken = [
        {"n_pe_events_audited": 12, "events_lived": 50},
        {"n_pe_events_audited": 11, "events_lived": 50},
    ]
    assert check_pe_event_sufficiency(broken, min_fraction=0.5)[0] is False


def test_i3_1_sums_both_gen1_phases() -> None:
    """A gen1 section holds two lives and its PE audit merges both."""

    two_phases = [
        {
            "n_pe_events_audited": 24,
            "events_lived_phase1": 12,
            "events_lived_phase2": 12,
        }
    ]
    passed, detail = check_pe_event_sufficiency(two_phases, min_fraction=0.5)
    assert passed is True
    assert "24/24" in detail


def test_i3_1_cannot_be_assessed_without_a_lived_count() -> None:
    """No denominator is not a pass (§2.9) — a pre-D-073 section has none."""

    passed, detail = check_pe_event_sufficiency(
        [{"n_pe_events_audited": 10}], min_fraction=0.5
    )
    assert passed is False
    assert "cannot be assessed" in detail


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


def test_i3_4_reports_events_the_cohort_never_reached() -> None:
    """Same arithmetic, renamed to what it measures (D-073).

    LOCF is gone, so nothing is padded any more; the number is now how much of
    the budget the cohort did not live to see.
    """

    whole_budget = [{"n_pe_events_audited": 10}]
    assert check_early_termination_fraction(
        whole_budget, expected_per_section=10, max_fraction=0.0
    )[0] is True

    died_early = [{"n_pe_events_audited": 7}]
    passed, detail = check_early_termination_fraction(
        died_early, expected_per_section=10, max_fraction=0.0
    )
    assert passed is False
    assert "3/10 events not reached" in detail


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


def test_i1_3_catches_what_a_weight_reading_cannot() -> None:
    """I1.3 only earns its place if it fails where I1.1 passes.

    Each shape below has a healthy lora_b_abs_sum_delta, so I1.1 calls it a
    real train. If I1.3 accepted them too it would be a duplicate gate.
    """

    def arm(**over: object) -> dict[str, object]:
        base = {
            "seed": 1,
            "arm": "lived",
            "lora_b_abs_sum_delta": 7.8,  # I1.1 is happy in every case here
            "dpo_loss": 0.69,
            "dpo_optimizer_steps": 12,
            "dpo_grad_norm_min": 0.4,
            "dpo_clipped_steps": 0,
        }
        base.update(over)
        return base

    healthy = [arm()]
    assert check_training_moved_weights(healthy)[0] is True
    assert check_gradient_step_taken(healthy)[0] is True

    # Accumulated but never stepped: the group flush never fired.
    passed, detail = check_gradient_step_taken([arm(dpo_optimizer_steps=0)])
    assert check_training_moved_weights([arm(dpo_optimizer_steps=0)])[0] is True
    assert passed is False
    assert "never stepped" in detail

    # Non-finite loss. The weights still move — into NaN.
    for bad in (float("nan"), float("inf")):
        passed, detail = check_gradient_step_taken([arm(dpo_loss=bad)])
        assert passed is False
        assert "dpo_loss" in detail

    # Optimizer stepped on an exactly-zero gradient.
    passed, detail = check_gradient_step_taken([arm(dpo_grad_norm_min=0.0)])
    assert passed is False
    assert "zero gradient" in detail

    # Field never written: unread, which is not a healthy reading (I1.1 rule).
    passed, detail = check_gradient_step_taken([arm(dpo_grad_norm_min=None)])
    assert passed is False
    assert "never read" in detail

    # null and gated arms are exempt, exactly as in I1.1.
    assert check_gradient_step_taken([arm(), {"seed": 1, "arm": "null"}])[0] is True
    assert check_gradient_step_taken([arm(), arm(seed=2, gated=True)])[0] is True

    # --no-lora is not-applicable, never True: a False-y run must not read as
    # proof that training happened.
    assert check_gradient_step_taken(healthy, lora_enabled=False)[0] is None


def test_i1_3b_reports_clipping_without_failing_the_run() -> None:
    """Clipping is a labelling matter, not an abort — but it must be visible."""

    clean = [
        {"seed": 1, "arm": "lived", "dpo_optimizer_steps": 10, "dpo_clipped_steps": 0}
    ]
    assert check_gradient_clipping(clean)[0] is True

    clipped = [
        {"seed": 1, "arm": "lived", "dpo_optimizer_steps": 10, "dpo_clipped_steps": 10}
    ]
    passed, detail = check_gradient_clipping(clipped)
    assert passed is False
    assert "100.0%" in detail
    # The point of the message: the locked learning rate is not what set the
    # step size. If that reasoning is gone, the flag is just a number.
    assert "DPO_LEARNING_RATE" in detail

    # A single clipped step still counts — PAD_FRACTION_MAX's strictness.
    one = [
        {"seed": 1, "arm": "lived", "dpo_optimizer_steps": 10, "dpo_clipped_steps": 1}
    ]
    assert check_gradient_clipping(one)[0] is False

    assert check_gradient_clipping([{"seed": 1, "arm": "null"}])[0] is None
    assert check_gradient_clipping(clipped, lora_enabled=False)[0] is None


def test_i1_4_asks_the_question_that_survived_d030() -> None:
    """The specified ratio is 1.0 by construction, so I1.4 asks a live one.

    D-030 moved the margin test into pair construction. A gate on "share of
    surviving pairs above the floor" could never fail; this one fails on the
    degenerate case that the floor can actually produce — nothing survived.
    """

    healthy = {
        "available": True,
        "snr_candidates": 7983,
        "snr_rejected_below_margin": 3714,
        "pairs_passed": 299,
    }
    passed, detail = check_pairs_survived_filter(healthy)
    assert passed is True
    assert "46.5%" in detail

    starved = dict(healthy, snr_rejected_below_margin=7983, pairs_passed=0)
    passed, detail = check_pairs_survived_filter(starved)
    assert passed is False
    assert "nothing to learn from" in detail

    empty = dict(healthy, snr_candidates=0, snr_rejected_below_margin=0, pairs_passed=0)
    assert check_pairs_survived_filter(empty)[0] is False

    # A filter that did not report is not a pass.
    assert check_pairs_survived_filter(None)[0] is None
    assert check_pairs_survived_filter({"available": False})[0] is None


def test_i1_5_floor_follows_the_config_it_claims_to_describe() -> None:
    """MIN_PAIRS must be derived, or it keeps claiming 'one full group'."""

    from dau.foundation.constraints import (
        DPO_BATCH_SIZE,
        DPO_GRADIENT_ACCUMULATION_STEPS,
        MIN_PAIRS,
        MIN_PAIRS_CALIBRATED,
    )

    assert MIN_PAIRS == DPO_BATCH_SIZE * DPO_GRADIENT_ACCUMULATION_STEPS
    # It came from config, not from a pilot. Reported so it cannot read as
    # settled (2.8) — the same guard SNR_MARGIN_FLOOR_CALIBRATED carries.
    assert MIN_PAIRS_CALIBRATED is False

    enough = [{"seed": 1, "arm": "lived", "n_pairs_trained": MIN_PAIRS}]
    assert check_pair_count_sufficient(enough)[0] is True

    short = [{"seed": 1, "arm": "lived", "n_pairs_trained": MIN_PAIRS - 1}]
    passed, detail = check_pair_count_sufficient(short)
    assert passed is False
    assert f"MIN_PAIRS={MIN_PAIRS}" in detail

    # null and gated arms never train, so they cannot be short.
    assert check_pair_count_sufficient([{"seed": 1, "arm": "null"}])[0] is None
    assert (
        check_pair_count_sufficient(
            [{"seed": 1, "arm": "lived", "gated": True, "n_pairs_trained": 0}]
        )[0]
        is None
    )


def test_i1_1_catches_the_bug_every_other_signal_missed() -> None:
    """The fake-train shape: pairs built, adapter saved, weights untouched.

    That arm is indistinguishable from a real one on n_pairs_trained and
    adapter_present, which is exactly why I1.1 reads lora_B instead.
    """

    def arm(name: str, delta: float, **extra: object) -> dict[str, object]:
        return {
            "seed": 2001,
            "arm": name,
            "n_pairs_trained": 47 if name != "null" else 0,
            "adapter_present": name != "null",
            "lora_b_abs_sum_delta": delta,
            **extra,
        }

    unread = float("nan")
    healthy = [arm("lived", 0.42), arm("null", unread), arm("shuffle", 0.37)]
    assert check_training_moved_weights(healthy)[0] is True

    # The bug: DPO ran, nothing moved.
    passed, detail = check_training_moved_weights(
        [arm("lived", 0.0), arm("null", unread), arm("shuffle", 0.37)]
    )
    assert passed is False
    assert "did not move" in detail

    # A train arm the tool could not measure is not a passing arm.
    passed, detail = check_training_moved_weights(
        [arm("lived", unread), arm("null", unread), arm("shuffle", 0.37)]
    )
    assert passed is False
    assert "never had lora_B read" in detail

    # A null that reports a train-step read means something trained on it.
    passed, detail = check_training_moved_weights(
        [arm("lived", 0.42), arm("null", 0.0), arm("shuffle", 0.37)]
    )
    assert passed is False
    assert "null arm" in detail

    # Deliberately skipped training is exempt — but only when it says so.
    gated = [
        arm("lived", unread, gated=True),
        arm("null", unread),
        arm("shuffle", 0.37),
    ]
    assert check_training_moved_weights(gated)[0] is True

    assert check_training_moved_weights([])[0] is False

    # --no-lora is a run mode, not a fault: not-applicable, never True.
    assert (
        check_training_moved_weights(healthy, lora_enabled=False)[0] is None
    )


def test_i4_1_fails_when_the_same_seed_lands_somewhere_else() -> None:
    """D-037's failure: identical seed and code, two runs, two adapters.

    Every other gate stayed green through it, so this one must not be
    satisfiable by anything short of an equal digest.
    """

    same = {
        "seed": 2001,
        "arm": "lived",
        "recorded_digest": "a" * 64,
        "replay_digest": "a" * 64,
    }
    assert check_replay_identical(same)[0] is True

    diverged = dict(same, replay_digest="b" * 64)
    passed, detail = check_replay_identical(diverged)
    assert passed is False
    assert "diverged" in detail

    # A missing digest is not a pass — the replay proved nothing.
    passed, detail = check_replay_identical(dict(same, recorded_digest=""))
    assert passed is False
    assert "digest is missing" in detail

    # Not run is "not applicable", which record() keeps distinct from True.
    assert check_replay_identical(None)[0] is None


def test_replay_agent_id_is_a_fresh_slot_that_still_derives_its_seed() -> None:
    """It must not collide with the arm it replays, or I0.4 would reject it."""

    from dau.diagnostics.run_cprime_multigen import (
        REPLAY_OF_ARM,
        parent_agent_id,
        replay_agent_id,
    )
    from dau.diagnostics.run_protocol_c_prime import _seed_from_agent_id

    replay = replay_agent_id(2001)
    assert replay != parent_agent_id(REPLAY_OF_ARM, 2001)
    assert _seed_from_agent_id(replay) == 2001


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
        # monkeypatch cannot undo this one: delenv on an ABSENT variable records
        # nothing to restore, and install_mock_llm's setdefault then creates it.
        # The value outlived the test and every later test in the process ran on
        # the groq backend — which silently turns I0.7 into "not applicable",
        # because switch_adapter's disk path is local-only. Caught by the
        # population runner's stale-adapter test once A1 wired that gate in.
        os.environ.pop(LLM_BACKEND_ENV, None)


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
        assert "f_agent_energy_lived" in lin.transfer

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
    # D-036: the pairs dict is hand-built, so a field on the dataclass does not
    # reach the file by itself. Asserting on the object alone let this ship
    # computed-but-unwritten.
    assert doc["pairs"][0]["phase2_decision_divergence"] == divergence
    # D-051: the same omission, one field over. LineageResult.consolidation
    # says in its own comment that an unreported consolidation would move gen2
    # numbers with nothing to attribute them to, and it was being computed,
    # printed and dropped. Asserted on the FILE, because the object carried it
    # the whole time — checking the object is what let this ship.
    for lineage, source in zip(doc["pairs"][0]["lineages"], results[0].lineages):
        assert "consolidation" in lineage, "consolidation dropped from the file"
        assert lineage["consolidation"] == source.consolidation
        if source.consolidation:
            # deleted_count is the number GAP-19 is a question about.
            assert "deleted_count" in lineage["consolidation"]
            assert "now_counter" in lineage["consolidation"]
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


# ---------------------------------------------------------------------------
# S5 — gen2 behavioural trace reaches the results file (L20)
# ---------------------------------------------------------------------------

CRISIS_AT_THIRD_EVENT: int = 3
TRAUMA_AT_SECOND_EVENT: int = 2
STALE_POOL_ROW_COUNTER: int = 99
# Shorter than EVENTS_SMOKE so 'lived' and 'budgeted' cannot be confused.
SHORT_LIFE_EVENTS: int = 3


def _pool_rows(
    crisis_flags: list[bool], agent_id: str = AGENT_A
) -> list[dict[str, Any]]:
    """Commons rows shaped like graph._record_pool_event writes them."""

    return [
        {
            graph_mod.EVENT_ROW_AGENT_ID: agent_id,
            "event_counter": index + 1,
            "extraction": float(index),
            "pool_ratio": 0.1 if crisis else 0.9,
            "crisis": crisis,
        }
        for index, crisis in enumerate(crisis_flags)
    ]


def _delta_class_rows(
    trauma_positions: set[int], agent_id: str = AGENT_A
) -> list[dict[str, Any]]:
    """PE audit rows carrying delta_class, the second reading of 'trauma'."""

    return [
        {
            graph_mod.EVENT_ROW_AGENT_ID: agent_id,
            "event_counter": index + 1,
            "prediction_error": 0.5,
            "raw_pe": 0.5,
            "precision_weight": 1.0,
            "delta_class": "TRAUMA" if (index + 1) in trauma_positions else "SHALLOW",
        }
        for index in range(4)
    ]


def test_s5_behaviour_keeps_both_readings_of_first_trauma() -> None:
    """Commons crisis and TRAUMA-class imprint are different events (2.11).

    The pre-registration line for S5 says "events until the first trauma"
    without saying which one, so the recorder must not collapse them.
    """

    behaviour = multigen_mod._s5_behaviour(
        _pool_rows([False, False, True, False]),
        _delta_class_rows({TRAUMA_AT_SECOND_EVENT}),
        AGENT_A,
    )

    assert behaviour["events_to_first_crisis"] == CRISIS_AT_THIRD_EVENT
    assert behaviour["events_to_first_delta_trauma"] == TRAUMA_AT_SECOND_EVENT
    assert behaviour["n_crisis_events"] == 1
    assert behaviour["crisis_by_event"] == [False, False, True, False]
    assert behaviour["extraction_by_event"] == [0.0, 1.0, 2.0, 3.0]


def test_s5_behaviour_reports_absence_as_never_not_as_event_zero() -> None:
    """A life with no crisis must not read as 'crisis on the zeroth event'."""

    behaviour = multigen_mod._s5_behaviour(
        _pool_rows([False, False]), _delta_class_rows(set()), AGENT_A
    )

    assert behaviour["events_to_first_crisis"] == multigen_mod.EVENT_NEVER_OCCURRED
    assert behaviour["events_to_first_delta_trauma"] == multigen_mod.EVENT_NEVER_OCCURRED
    assert behaviour["n_crisis_events"] == 0


def test_gen2_result_carries_the_commons_trace(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """B2 could not run S5 because none of this reached the JSON (L20)."""

    monkeypatch.setenv("DAU_LLM_SEED", "0")
    monkeypatch.setenv("DAU_LLM_TEMPERATURE", "0.2")

    def _fake_life(*, agent_id, seed, n_events, store, initial):
        graph_mod.reset_pool_event_log()
        # Rows are written under the heir's own id: run_gen2_measure filters
        # the shared buffer to the agent it is reporting on (E3), so rows
        # owned by anyone else are correctly invisible to it.
        for row in _pool_rows([False, False, True], agent_id):
            graph_mod._pool_event_log.append(row)
        return (
            [0.25] * n_events,
            [],
            _delta_class_rows({TRAUMA_AT_SECOND_EVENT}, agent_id),
            initial,
        )

    monkeypatch.setattr(multigen_mod, "run_life_keep_vault", _fake_life)

    heir_id = heir_agent_id(ARM_UNIT, SEED_UNIT)
    result = run_gen2_measure(
        heir=_initial_state(heir_id, SEED_UNIT),
        store=None,
        seed=SEED_UNIT,
        gen1_arm=ARM_UNIT,
        events_gen2=EVENTS_SMOKE,
        k_gen2=1,
        pe_window=EVENTS_SMOKE,
    )

    assert result.crisis_by_event == [False, False, True]
    assert result.n_crisis_events == 1
    assert result.events_to_first_crisis == CRISIS_AT_THIRD_EVENT
    assert result.events_to_first_delta_trauma == TRAUMA_AT_SECOND_EVENT
    assert result.pool_ratio_by_event[-1] == pytest.approx(0.1)
    # asdict() feeds the results file; a field the writer drops is invisible.
    assert "extraction_by_event" in asdict(result)


def test_run_life_clears_the_commons_buffer_before_streaming(
    monkeypatch: pytest.MonkeyPatch,
    store: MemoryStore,
) -> None:
    """A life must not inherit the previous life's commons rows.

    The buffer is module-global and drained after the stream; without the
    reset, gen2's S5 trace would silently contain gen1 phase-2 events.
    """

    graph_mod.reset_pool_event_log()
    graph_mod._pool_event_log.append(
        {
            "event_counter": STALE_POOL_ROW_COUNTER,
            "extraction": 1.0,
            "pool_ratio": 0.5,
            "crisis": False,
        }
    )

    agent_id = heir_agent_id(ARM_UNIT, SEED_UNIT)
    start = _initial_state(agent_id, SEED_UNIT)
    monkeypatch.setattr(
        multigen_mod,
        "build_graph",
        lambda checkpointer=None: SimpleNamespace(stream=lambda *a, **k: iter([start])),
    )

    multigen_mod.run_life_keep_vault(
        agent_id=agent_id,
        seed=SEED_UNIT,
        n_events=EVENTS_SMOKE,
        store=store,
        initial=start,
    )

    counters = [row["event_counter"] for row in graph_mod.get_pool_event_log()]
    assert STALE_POOL_ROW_COUNTER not in counters


# ---------------------------------------------------------------------------
# S6 — f_agent=None shadow record (L20; the arm B2 could not produce)
# ---------------------------------------------------------------------------


def test_transfer_records_what_f_agent_none_would_have_inherited(
    store: MemoryStore,
) -> None:
    """The fitness gate's effect must be readable without a fourth arm.

    The parent here is low-fitness with a transferable trauma, which is the
    branch where the two paths disagree: with F_agent the trauma transfers as
    an inherited warning, without it the legacy salience rules decide.
    """

    parent = _parent_with_transferable_trauma(store, SEED_UNIT)
    _heir, record, birth = transfer_to_heir(
        parent_state=parent,
        memory_store=store,
        seed=SEED_UNIT,
        gen1_arm=ARM_UNIT,
        events_gen1=EVENTS_GEN1_UNIT,
    )

    assert birth.f_agent_none_n_transfer_candidates == len(
        birth.f_agent_none_inherited_memory_ids
    )
    assert birth.n_inherited_warnings == len(record.inherited_warning_ids)
    # The gate is not decorative on this parent: it marks a warning the
    # legacy path does not.
    assert birth.f_agent_none_n_inherited_warnings != birth.n_inherited_warnings
    assert birth.f_agent_none_inheritance_identical is False


def test_f_agent_none_shadow_does_not_disturb_the_real_transfer(
    store: MemoryStore,
) -> None:
    """The shadow reads the vault; it must not change what actually transfers.

    A second consolidate_generation that wrote to the store would corrupt the
    heir's inheritance — the exact failure the shadow exists to avoid paying
    for with a fourth arm.
    """

    parent = _parent_with_transferable_trauma(store, SEED_UNIT)
    nodes_before = {node.id for node in store.list_nodes(parent.agent_id)}

    _heir, record, birth = transfer_to_heir(
        parent_state=parent,
        memory_store=store,
        seed=SEED_UNIT,
        gen1_arm=ARM_UNIT,
        events_gen1=EVENTS_GEN1_UNIT,
    )

    assert {node.id for node in store.list_nodes(parent.agent_id)} == nodes_before
    assert birth.inherited_memory_ids == list(record.inherited_memories)
    assert birth.n_transfer_candidates == len(record.inherited_memories)


def test_birth_drift_cannot_see_f_agent_at_all(store: MemoryStore) -> None:
    """Why S6 is not a fourth arm: the primary endpoint is blind to F_agent.

    birth_drift_magnitudes comes from GenerationRecord.inherited_drift, which
    consolidate_generation copies from the parent's drift; select_for_transfer
    only reads drift. So "f_agent=None, same test as the primary" is identical
    by construction, and running it as an arm would buy a known answer.
    """

    parent = _parent_with_transferable_trauma(store, SEED_UNIT)
    with_gate = consolidate_generation(parent, store, f_agent=0.0)
    without_gate = consolidate_generation(parent, store, f_agent=None)

    assert with_gate.inherited_drift.magnitudes == without_gate.inherited_drift.magnitudes
    assert with_gate.inherited_drift.flags == without_gate.inherited_drift.flags
    # Same drift, different inheritance — that is the channel S6 can measure.
    # On this parent the id set survives both paths and the disagreement is in
    # the marking: the gate transfers the trauma as an inherited warning with a
    # negative somatic scale, the legacy path transfers it unmarked.
    assert with_gate.inherited_warning_ids != without_gate.inherited_warning_ids
    assert with_gate.inherited_somatic_scales != without_gate.inherited_somatic_scales


METABOLIC_GAIN_PROBE: float = 0.123


def test_tool_identity_reports_the_metabolic_loop_and_its_calibration(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A universe-shaping constant that the results file cannot see is invisible.

    D-066 changed the physics: harvest feeds energy and exhaustion kills. All
    three constants are declared, not measured, so the block must say so —
    the U5/D-030 pattern that keeps an uncalibrated threshold from reading as
    a settled one.

    The gain is probed through a moved constant rather than compared to its own
    value: a block that hard-codes 0.5 agrees with the real constant on every
    run and only disagrees once the constant moves. That is exactly the
    "report repeats the instrument instead of following it" failure (2.8), and
    an equality check against the constant cannot see it.
    """

    identity = build_tool_identity(lora_choice=LORA_CHOICE_OFF, seeds=[SEED_UNIT])
    metabolism = identity["metabolism"]

    assert metabolism["gain_half_saturation"] == C.METABOLIC_GAIN_HALF_SATURATION
    assert metabolism["grace_events"] == C.METABOLIC_GRACE_EVENTS
    assert metabolism["calibrated"] is False
    assert metabolism["death_on_exhaustion"] is True

    monkeypatch.setattr(
        tool_identity_mod, "METABOLIC_GAIN_MAX", METABOLIC_GAIN_PROBE
    )
    moved = build_tool_identity(lora_choice=LORA_CHOICE_OFF, seeds=[SEED_UNIT])
    assert moved["metabolism"]["gain_max"] == METABOLIC_GAIN_PROBE


EXTRACTION_MAX_PROBE: float = 3.75


def test_tool_identity_reports_the_fitness_formulas_scale(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The per-event pool scale is invisible in the results file otherwise.

    K4-b (D-070) changed what f_agent means without changing its name or its
    range, so two runs can report the same score from different physics. Same
    probe discipline as the metabolic block: the scale is moved rather than
    compared to itself, because a hard-coded 8.0 agrees with the constant on
    every run and only disagrees once the constant moves (2.8).
    """

    identity = build_tool_identity(lora_choice=LORA_CHOICE_OFF, seeds=[SEED_UNIT])
    fitness = identity["fitness"]

    assert fitness["w_energy"] == FITNESS_W_ENERGY
    assert fitness["w_pool"] == FITNESS_W_POOL
    assert fitness["w_survival"] == FITNESS_W_SURVIVAL

    monkeypatch.setattr(
        tool_identity_mod, "EXTRACTION_DEFECT", EXTRACTION_MAX_PROBE
    )
    moved = build_tool_identity(lora_choice=LORA_CHOICE_OFF, seeds=[SEED_UNIT])
    assert moved["fitness"]["pool_term_per_event_max"] == EXTRACTION_MAX_PROBE


LANDMARK_EVENT_PROBE: int = 7


def test_tool_identity_reports_the_landmark_ordinal(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Two runs can mean different things by "the endpoint" (K1/K2/K5, D-070).

    Nothing else in the results file carries the ordinal: the landmark fields
    on ArmResult are named for the concept, not for the event they were read
    at, so a run that moved LANDMARK_EVENT would be silently incomparable.
    """

    identity = build_tool_identity(lora_choice=LORA_CHOICE_OFF, seeds=[SEED_UNIT])
    assert identity["endpoints"]["landmark_event"] == C.LANDMARK_EVENT

    monkeypatch.setattr(tool_identity_mod, "LANDMARK_EVENT", LANDMARK_EVENT_PROBE)
    moved = build_tool_identity(lora_choice=LORA_CHOICE_OFF, seeds=[SEED_UNIT])
    assert moved["endpoints"]["landmark_event"] == LANDMARK_EVENT_PROBE


def test_life_seals_the_vault_clock_with_events_actually_lived(
    monkeypatch: pytest.MonkeyPatch,
    store: MemoryStore,
) -> None:
    """Phase-2 must not reuse phase-1's ordinals (GAP-19 / D-067).

    Sealed with the lived length, not the budget: since D-066 a life can end
    early, and sealing with n_events would age the vault by time the agent
    never had.
    """

    agent_id = heir_agent_id(ARM_UNIT, SEED_UNIT)
    start = _initial_state(agent_id, SEED_UNIT)
    lived = [
        Event(event_type="agent_decision", payload={"decision": "x"}, timestamp=i + 1)
        for i in range(SHORT_LIFE_EVENTS)
    ]
    ended = start.model_copy(update={"event_log": lived})
    monkeypatch.setattr(
        multigen_mod,
        "build_graph",
        lambda checkpointer=None: SimpleNamespace(stream=lambda *a, **k: iter([ended])),
    )

    assert store.counter_base == 0
    multigen_mod.run_life_keep_vault(
        agent_id=agent_id,
        seed=SEED_UNIT,
        n_events=EVENTS_SMOKE,
        store=store,
        initial=start,
    )

    assert store.counter_base == SHORT_LIFE_EVENTS
    assert store.counter_base != EVENTS_SMOKE


# ---------------------------------------------------------------------------
# K1/K2/K5 (D-070) — landmark reading: same age, not same ending
# ---------------------------------------------------------------------------

LANDMARK_ENERGY: float = 0.62
LANDMARK_SCAR: float = 0.41
LATE_ENERGY: float = 0.10
LATE_SCAR: float = 0.88
SHORT_LIFE_BEFORE_LANDMARK: int = C.LANDMARK_EVENT - 3


def _body_rows(
    n_events: int,
    *,
    agent_id: str = AGENT_A,
    landmark_energy: float = LANDMARK_ENERGY,
    late_energy: float = LATE_ENERGY,
) -> list[dict[str, object]]:
    """Body rows for a life of n_events, distinguishable at the landmark."""

    rows: list[dict[str, object]] = []
    for counter in range(1, n_events + 1):
        at_landmark = counter == C.LANDMARK_EVENT
        rows.append(
            {
                graph_mod.EVENT_ROW_AGENT_ID: agent_id,
                "event_counter": counter,
                "energy": landmark_energy if at_landmark else late_energy,
                "drift_flags": {"resource": True} if at_landmark else {"energy": True},
                "drift_magnitudes": (
                    {"resource": LANDMARK_SCAR}
                    if at_landmark
                    else {"energy": LATE_SCAR}
                ),
            }
        )
    return rows


def test_landmark_reading_reads_the_fixed_ordinal_not_the_last_event() -> None:
    """The whole point: the same AGE, whatever age the life ended at.

    A life that runs past the landmark keeps scarring, and the end-of-life
    drift is what the transferred record already carries. Reading the last row
    here would reproduce that endpoint under a new name.
    """

    rows = _body_rows(C.LANDMARK_EVENT * 2)
    reading = multigen_mod._landmark_reading(rows, len(rows), AGENT_A)

    assert reading["landmark_reached"] is True
    assert reading["landmark_energy"] == pytest.approx(LANDMARK_ENERGY)
    assert reading["landmark_drift_flags"] == {"resource": True}
    assert reading["landmark_drift_magnitudes"] == pytest.approx(
        {"resource": LANDMARK_SCAR}
    )


def test_energy_mean_covers_the_whole_life_not_just_the_landmark() -> None:
    """K2's second reading: E_final is decided by the death rule, not by living.

    Unit-spaced ordinals make the mean the time integral over the lifespan, so
    two lives of different length are still comparable on it.
    """

    rows = _body_rows(C.LANDMARK_EVENT * 2)
    reading = multigen_mod._landmark_reading(rows, len(rows), AGENT_A)

    expected = statistics.fmean(float(row["energy"]) for row in rows)
    assert reading["energy_mean_over_life"] == pytest.approx(expected)
    # Not secretly the landmark value, and not the final one either.
    assert reading["energy_mean_over_life"] != pytest.approx(LANDMARK_ENERGY)
    assert reading["energy_mean_over_life"] != pytest.approx(LATE_ENERGY)


def test_landmark_not_reached_is_reported_never_imputed() -> None:
    """A life that ended early has no landmark — and gets no substitute (§2.9).

    Unreachable while grace covers the landmark, which is exactly why the rule
    is written: if METABOLIC_GRACE_EVENTS ever moves below it, the reading must
    say "not measured" rather than quietly reporting some other ordinal.
    """

    rows = _body_rows(SHORT_LIFE_BEFORE_LANDMARK)
    reading = multigen_mod._landmark_reading(rows, len(rows), AGENT_A)

    assert reading["landmark_reached"] is False
    assert math.isnan(float(reading["landmark_energy"]))
    assert reading["landmark_drift_flags"] == {}
    assert reading["landmark_drift_magnitudes"] == {}
    # The life still happened, so its integrated energy is still measured.
    assert not math.isnan(float(reading["energy_mean_over_life"]))


def test_missing_landmark_row_on_a_long_life_aborts() -> None:
    """Instrumentation that stopped writing must not read as a short life.

    The two are indistinguishable from the rows alone, and they mean opposite
    things: one is a finding about the agent, the other is a broken instrument.
    """

    rows = [
        row
        for row in _body_rows(C.LANDMARK_EVENT * 2)
        if row["event_counter"] != C.LANDMARK_EVENT
    ]

    with pytest.raises(SystemExit, match=str(C.LANDMARK_EVENT)):
        multigen_mod._landmark_reading(rows, C.LANDMARK_EVENT * 2, AGENT_A)


def test_arm_result_carries_the_landmark_of_phase_two(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Phase 2, because that is the life the transferred drift comes from.

    Phase 1 runs before any adapter exists, so all three arms are identical
    there; a landmark read off phase 1 could not differ by arm at all.
    """

    lives: list[int] = []

    def _fake_life(*, agent_id, seed, n_events, store, initial):
        lives.append(len(lives))
        graph_mod.reset_body_event_log()
        for row in _body_rows(n_events):
            graph_mod._record_body_event(
                agent_id=agent_id,
                event_counter=int(row["event_counter"]),
                energy=float(row["energy"]),
                drift_flags=dict(row["drift_flags"]),
                drift_magnitudes=dict(row["drift_magnitudes"]),
            )
        state = _initial_state(agent_id, seed)
        state = state.model_copy(
            update={
                "event_log": [
                    Event(event_type=EVENT_TYPE_LANDMARK, timestamp=counter)
                    for counter in range(1, n_events + 1)
                ]
            }
        )
        return [0.3] * n_events, [], [], state

    monkeypatch.setattr(multigen_mod, "run_life_keep_vault", _fake_life)
    monkeypatch.setattr(
        multigen_mod,
        "_open_lineage_store",
        lambda: (None, _FakeTmp()),
    )

    arm_result, _state, _store, _tmp = run_gen1_arm_lineage(
        seed=SEED_UNIT,
        arm=ARM_NULL,
        events_gen1=EVENTS_GEN1_UNIT,
    )

    assert len(lives) == 2, "both phases must run, or 'phase 2' means nothing"
    assert arm_result.events_lived_phase1 == EVENTS_GEN1_UNIT
    assert arm_result.events_lived_phase2 == EVENTS_GEN1_UNIT
    assert arm_result.landmark_reached is True
    assert arm_result.landmark_energy == pytest.approx(LANDMARK_ENERGY)
    assert arm_result.landmark_drift_magnitudes == pytest.approx(
        {"resource": LANDMARK_SCAR}
    )
    assert not math.isnan(arm_result.energy_mean_over_life)


LANDMARK_E2E_EVENTS: int = C.LANDMARK_EVENT + 1


def test_landmark_survives_a_real_graph_stream(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The junction no unit test reaches: real stream writes, reader finds.

    The graph tests prove pool_step_node appends a row and the reader tests
    prove _landmark_reading picks the right one, but between them sit the two
    things that actually break — the ordinals the graph writes agreeing with
    the ordinal the reader looks up, and the buffer surviving from the end of
    phase 2 to the drain without another life clearing it. Both were silent
    failure modes in the S5 wiring they are copied from (D-063 / L20).

    One arm and one event past the landmark: enough to prove the junction,
    cheap enough to keep in the suite.
    """

    monkeypatch.setenv(LORA_ENABLED_ENV, "0")
    monkeypatch.setattr(
        "dau.foundation.graph._prediction_error",
        lambda expected, actual: 0.25 + (len(str(actual)) % 7) * 0.05,
    )
    # install_mock_llm setdefaults the backend to groq and nothing takes it back
    # out; in a real run the process ends, in a test it leaks into every test
    # that follows. See test_install_mock_llm_pins_groq_when_backend_unset.
    from dau.foundation.graph import LLM_BACKEND_ENV

    previous_backend = os.environ.get(LLM_BACKEND_ENV)
    previous = multigen_mod.install_mock_llm()
    try:
        arm_result, _state, _store, tmp = run_gen1_arm_lineage(
            seed=SEED_UNIT,
            arm=ARM_NULL,
            events_gen1=LANDMARK_E2E_EVENTS,
        )
    finally:
        multigen_mod.restore_llm_builder(previous)
        if previous_backend is None:
            os.environ.pop(LLM_BACKEND_ENV, None)
        else:
            os.environ[LLM_BACKEND_ENV] = previous_backend

    try:
        assert arm_result.events_lived_phase1 == LANDMARK_E2E_EVENTS
        assert arm_result.events_lived_phase2 == LANDMARK_E2E_EVENTS
        assert arm_result.landmark_reached is True
        # A real body, so the values are whatever the life produced — what is
        # under test is that they were READ, not what they are.
        assert not math.isnan(arm_result.landmark_energy)
        assert not math.isnan(arm_result.energy_mean_over_life)
        # One row per event of the second phase, numbered from one: if the
        # buffer had carried phase 1 as well this would be twice as long, and
        # the landmark would have been read off the untrained life.
        rows = graph_mod.get_body_event_log()
        assert [row["event_counter"] for row in rows] == list(
            range(1, LANDMARK_E2E_EVENTS + 1)
        )
    finally:
        if tmp is not None:
            tmp.cleanup()


# ---------------------------------------------------------------------------
# K1 / D-073 — LOCF is gone; the comparable endpoint is read at a fixed age
# ---------------------------------------------------------------------------

PE_LIVED_VALUE: float = 0.20
PE_TAIL_VALUE: float = 0.90
SHORT_PE_LIFE: int = C.LANDMARK_EVENT - 4
PE_BUDGET: int = C.LANDMARK_EVENT * 3


def _pe_trace(n_events: int) -> list[float]:
    """A trace whose landmark window and whose tail disagree on purpose."""

    return [
        PE_LIVED_VALUE if i < C.LANDMARK_EVENT else PE_TAIL_VALUE
        for i in range(n_events)
    ]


def test_short_pe_trace_is_not_padded_to_the_budget() -> None:
    """LOCF is gone (D-073). A short life returns a short trace.

    Lachin (Clinical Trials 2015) on carrying the last observation forward:
    not conservative, biased either way, and it understates variance. In the
    D-066 pilot 71% of gen1's slots were padding, so most of the endpoint was
    LOCF output rather than measurement.
    """

    trace = multigen_mod._clip_pe_trace(_pe_trace(SHORT_PE_LIFE), PE_BUDGET)

    assert len(trace) == SHORT_PE_LIFE
    assert trace == _pe_trace(SHORT_PE_LIFE)


def test_whole_phase_mean_is_now_a_per_event_rate() -> None:
    """The mean divides by what was lived, so it cannot inherit lifespan.

    Under padding these two lives returned different means from identical
    per-event behaviour, because the shorter one had its last value repeated
    into every empty slot.

    The pattern alternates deliberately: a constant trace has its own mean as
    its last value, so LOCF moves nothing and this test would pass under the
    very padding it exists to forbid. The first version did exactly that and
    the mutation check caught it (§2.4).
    """

    cycle = [PE_LIVED_VALUE, PE_TAIL_VALUE]
    repeats = PE_BUDGET // len(cycle)
    short_life = multigen_mod._clip_pe_trace(cycle * (repeats // 3), PE_BUDGET)
    long_life = multigen_mod._clip_pe_trace(cycle * repeats, PE_BUDGET)

    assert len(short_life) * 3 == len(long_life), "lifespans must differ"
    assert multigen_mod._window_mean(short_life) == pytest.approx(
        multigen_mod._window_mean(long_life)
    )


def test_landmark_window_takes_exactly_the_first_landmark_events() -> None:
    """Every arm contributes the same events, so lifespan cannot enter."""

    short_budget_life = _pe_trace(C.LANDMARK_EVENT)
    long_life = _pe_trace(PE_BUDGET)

    assert multigen_mod._landmark_window_mean(long_life) == pytest.approx(
        PE_LIVED_VALUE
    )
    # The tail is louder and much longer, and the fixed window ignores it.
    assert multigen_mod._landmark_window_mean(long_life) == pytest.approx(
        multigen_mod._landmark_window_mean(short_budget_life)
    )
    assert multigen_mod._window_mean(long_life) > multigen_mod._landmark_window_mean(
        long_life
    )


def test_landmark_window_refuses_a_partial_window() -> None:
    """A window over "however many it managed" is the confound being removed.

    Structurally unreachable while grace covers the landmark; written because
    §2.9 forbids the silent fallback, not because it is expected to fire.
    """

    assert math.isnan(multigen_mod._landmark_window_mean(_pe_trace(SHORT_PE_LIFE)))
    assert math.isnan(multigen_mod._pe_at_landmark(_pe_trace(SHORT_PE_LIFE)))


def test_pe_at_landmark_is_the_point_read_not_the_window() -> None:
    """Recorded alongside, so the point read costs no extra run (D-073)."""

    trace = _pe_trace(PE_BUDGET)
    trace[C.LANDMARK_EVENT - 1] = PE_TAIL_VALUE

    assert multigen_mod._pe_at_landmark(trace) == pytest.approx(PE_TAIL_VALUE)
    # One event out of the window moved; the window mean barely notices, which
    # is exactly why the window is the primary and the point read is not.
    assert multigen_mod._landmark_window_mean(trace) < PE_TAIL_VALUE


def test_pe_window_report_says_padding_is_off() -> None:
    """Same field names before and after D-073 — this is what disambiguates."""

    described = multigen_mod.describe_pe_window()

    assert described["pe_locf_padding"] is False
    assert described["pe_landmark_event"] == C.LANDMARK_EVENT


def test_report_mode_records_without_touching_run_quality() -> None:
    """I3.4 became a finding, not a fault (D-073 / K7).

    PAD_FRACTION_MAX is 0.0 and since D-066 lineages die early by design, so a
    flag here would fire on every run from now on and run_quality would stop
    separating anything. The number still has to reach the results file.
    """

    gate = Preflight()
    gate.check("I3.4", lambda: (False, "9/30 events not reached"), mode=MODE_REPORT)

    assert gate.run_quality() == RUN_QUALITY_CLEAN
    assert gate.invariants()["I3.4"] is False
    assert "not reached" in gate.details()["I3.4"]["detail"]
    gate.enforce()  # must not raise

    # And the modes that do label a run still do.
    gate.check("I3.1", lambda: (False, "starved"), mode=MODE_FLAG)
    assert gate.run_quality() == RUN_QUALITY_FLAGGED


# ---------------------------------------------------------------------------
# E3 — event rows carry their owner, and every reader says whose it wants
# ---------------------------------------------------------------------------

OTHER_LANDMARK_ENERGY: float = 0.13
OTHER_LANDMARK_SCAR: float = 0.77


def _interleaved_body_rows() -> list[dict[str, object]]:
    """Two agents' rows in one buffer, alternating — the population case.

    Interleaved rather than concatenated on purpose: a reader that takes the
    first matching event_counter looks correct on concatenated rows for the
    agent that happens to come first.
    """

    a_rows = _body_rows(C.LANDMARK_EVENT * 2, agent_id=AGENT_A)
    b_rows = _body_rows(
        C.LANDMARK_EVENT * 2,
        agent_id=AGENT_B,
        landmark_energy=OTHER_LANDMARK_ENERGY,
    )
    mixed: list[dict[str, object]] = []
    for a_row, b_row in zip(a_rows, b_rows):
        mixed.append(b_row)
        mixed.append(a_row)
    return mixed


def test_landmark_reading_reads_the_agent_it_was_asked_for() -> None:
    """The silent failure E3 exists to prevent (POPULATION_DESIGN_PROPOSAL).

    With N agents alive the buffer holds N rows per ordinal. An unfiltered
    lookup returns one of them — a real number, from the wrong agent, with no
    error and no warning. Every other population blocker stops the code from
    running; this one lets it run and lie.
    """

    mixed = _interleaved_body_rows()

    reading_a = multigen_mod._landmark_reading(mixed, C.LANDMARK_EVENT * 2, AGENT_A)
    reading_b = multigen_mod._landmark_reading(mixed, C.LANDMARK_EVENT * 2, AGENT_B)

    assert reading_a["landmark_energy"] == pytest.approx(LANDMARK_ENERGY)
    assert reading_b["landmark_energy"] == pytest.approx(OTHER_LANDMARK_ENERGY)
    assert reading_a["landmark_energy"] != reading_b["landmark_energy"]
    # B's rows come first in the buffer, so an unfiltered reader would hand
    # B's landmark to A — the exact swap this test forbids.
    assert reading_a["landmark_energy"] != pytest.approx(OTHER_LANDMARK_ENERGY)


def test_energy_mean_is_over_one_agents_life_not_the_population() -> None:
    """Averaging the buffer would report the cohort under one agent's name."""

    mixed = _interleaved_body_rows()
    own_only = _body_rows(C.LANDMARK_EVENT * 2, agent_id=AGENT_A)

    mixed_reading = multigen_mod._landmark_reading(mixed, C.LANDMARK_EVENT * 2, AGENT_A)
    alone_reading = multigen_mod._landmark_reading(
        own_only, C.LANDMARK_EVENT * 2, AGENT_A
    )

    assert mixed_reading["energy_mean_over_life"] == pytest.approx(
        alone_reading["energy_mean_over_life"]
    )


def test_s5_behaviour_describes_one_heir_not_the_commons() -> None:
    """The commons buffer is shared by construction — the trace is not."""

    mixed_pool = _pool_rows([False, True, True], AGENT_B) + _pool_rows(
        [False, False, True], AGENT_A
    )
    mixed_pe = _delta_class_rows({TRAUMA_AT_SECOND_EVENT}, AGENT_A) + _delta_class_rows(
        set(), AGENT_B
    )

    behaviour = multigen_mod._s5_behaviour(mixed_pool, mixed_pe, AGENT_A)

    assert behaviour["crisis_by_event"] == [False, False, True]
    assert behaviour["n_crisis_events"] == 1
    assert behaviour["events_to_first_crisis"] == CRISIS_AT_THIRD_EVENT


def test_graph_writes_the_owner_onto_every_event_row() -> None:
    """Filtering is only as good as the column it filters on."""

    graph_mod.reset_body_event_log()
    graph_mod.reset_pool_event_log()
    graph_mod.reset_pe_event_log()

    graph_mod._record_body_event(
        agent_id=AGENT_A,
        event_counter=1,
        energy=LANDMARK_ENERGY,
        drift_flags={},
        drift_magnitudes={},
    )
    graph_mod._record_pool_event(
        agent_id=AGENT_A,
        event_counter=1,
        extraction=1.0,
        requested=1.0,
        pool_ratio=0.5,
        crisis=False,
        crisis_magnitude=None,
    )
    graph_mod._record_pe_event(
        agent_id=AGENT_A,
        event_counter=1,
        prediction_error=0.5,
        raw_pe=0.5,
        precision_weight=1.0,
        delta_magnitude=0.1,
        delta_class="SHALLOW",
        affected_domain="energy",
        axis_deltas={"energy": 0.1, "resource": 0.0, "social": 0.0, "uncertainty": 0.0},
    )

    for rows in (
        graph_mod.get_body_event_log(),
        graph_mod.get_pool_event_log(),
        graph_mod.get_pe_event_log(),
    ):
        assert rows[0][graph_mod.EVENT_ROW_AGENT_ID] == AGENT_A
        assert graph_mod.rows_for_agent(rows, AGENT_B) == []
        assert graph_mod.rows_for_agent(rows, AGENT_A) == rows
