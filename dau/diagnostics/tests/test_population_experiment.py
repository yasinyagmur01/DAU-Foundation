"""Population experiment wrapper (E2-4b): plumbing, pedigree, and Price timing."""

from __future__ import annotations

from typing import Any

import pytest

import dau.foundation.graph as graph_mod
from dau.diagnostics.preflight import RUN_QUALITY_CLEAN, PreflightAbort

# ⭐ D-149. A stub run legitimately raises I5.4: no life accumulates an
# emotional weight worth scaling, so no inherited somatic scale is ever
# applied. Asserting a blanket `clean` would force the choice between a
# false-green suite and an unwired gate — so the tests assert the flagged SET
# instead, which is a stronger statement than `clean` ever was: it says which
# gates fired AND that no other did.
STUB_EXPECTED_FLAGS: frozenset[str] = frozenset({"I5.4"})


def _flagged(results: dict[str, Any]) -> frozenset[str]:
    """Invariant names that did not pass, from the results' own block."""

    # ⚠ `is False`, not `is not True`: a gate that did not run records None,
    # and counting that as a failure would make "not evaluated" and "failed"
    # the same thing — the distinction D-121 spent a decision on.
    return frozenset(
        name for name, ok in results["invariants"].items() if ok is False
    )


def assert_only_expected_flags(results: dict[str, Any]) -> None:
    """Everything green except the stub's known-empty channel."""

    unexpected = _flagged(results) - STUB_EXPECTED_FLAGS
    assert not unexpected, f"a gate fired that this test did not expect: {unexpected}"
    if not _flagged(results):
        assert_only_expected_flags(results)
from dau.diagnostics.run_population_experiment import (
    build_arm_population,
    founder_id,
    run_population_experiment,
)
from dau.diagnostics.run_protocol_c_prime import ARM_ORDER
from dau.foundation.local_llm import ADAPTER_CONFIG_FILE
from dau.foundation.lod import NPC_ACTION_EXTRACT_MODERATE
from dau.foundation.state import DAUAgentState

SEED: int = 9301
CUDA_ALLOC_UNSET: str = ""
# A pasture that never fell below the crisis floor: the commons channel of
# delta_profile has nothing to report (D-117).
NO_CRISIS: list[dict[str, Any]] = []
SHUFFLE_MARKER: str = "-shuffle-"
NULL_MARKER: str = "-null-"
N_AGENTS: int = 3
N_GENERATIONS: int = 3
EVENTS: int = 3
# Deliberately not EVENTS: the restore has to be distinguishable from a leak.
MAX_EVENTS_SENTINEL: int = 137
# What A1 wired in. Named so the test asserts the SET, not just that some
# invariants block exists: a gate quietly dropped from run_population_phase0
# would otherwise leave a healthy-looking block behind.
GATED_INVARIANTS: tuple[str, ...] = (
    "I0.3", "I0.4", "I0.6", "I0.7", "I1.1", "I4.1",
)


@pytest.fixture(autouse=True)
def _preflight_env(monkeypatch) -> None:
    """Give every test the environment a real run is required to have (A1).

    PYTHONHASHSEED can only be honoured by the interpreter, so the runner
    refuses rather than setting it — which means the whole module would abort
    on I0.3 without this. Set here rather than in the runner on purpose: a test
    that wants to see the gate fire deletes it again, and
    ``test_run_aborts_without_pythonhashseed`` is that test.
    """

    monkeypatch.setenv("PYTHONHASHSEED", "0")


@pytest.fixture
def fresh_cuda_process(monkeypatch):
    """The one condition a real run starts under: allocator not yet up (D-116).

    Measured: after importing the runner, ``torch.cuda.is_initialized()`` is
    False — main() genuinely runs before the allocator. Inside a pytest session
    it is True by then, because an earlier test already encoded on the GPU, so
    without this the allocator tests would pass or fail on test ORDER. Setting
    the variable to "" rather than deleting it makes monkeypatch responsible
    for the teardown, so a test cannot leak the setting into the next one.
    """

    from dau.foundation.local_llm import CUDA_ALLOC_CONF_ENV

    monkeypatch.setenv(CUDA_ALLOC_CONF_ENV, CUDA_ALLOC_UNSET)
    try:
        import torch
    except ImportError:
        return
    monkeypatch.setattr(torch.cuda, "is_initialized", lambda: False)


def _stub_agent(state: DAUAgentState) -> dict[str, Any]:
    """Append one decision event without an LLM, honouring the energy invariant.

    `energy` is required on every decision row or the meta observer refuses it
    (D-086, self_model.py) — the stub has to meet the same contract the real
    node does, or the test would pass against a weaker one.
    """

    event = graph_mod.build_event(
        graph_mod.EventClock(counter=len(state.event_log)),
        "agent_decision",
        {
            "decision": NPC_ACTION_EXTRACT_MODERATE,
            "energy": float(state.internal_state.energy),
            "expected_outcome": {},
        },
    )
    return {"event_log": list(state.event_log) + [event]}


def test_founding_population_shares_one_niche_with_distinct_ids() -> None:
    """P0-①: identical starting worlds, so separation must come from the commons."""

    population = build_arm_population(ARM_ORDER[0], SEED, N_AGENTS)

    assert len(population) == N_AGENTS
    assert len({state.agent_id for state in population}) == N_AGENTS
    first = population[0].environment
    for state in population[1:]:
        assert state.environment == first, "founders must share the niche under ①"


def test_founder_id_is_deterministic_and_arm_scoped() -> None:
    """Ids carry arm and seed so two arms cannot collide in the ledgers."""

    assert founder_id("lived", SEED, 0) != founder_id("null", SEED, 0)
    assert founder_id("lived", SEED, 0) == founder_id("lived", SEED, 0)


def test_experiment_runs_every_arm_and_generation(monkeypatch) -> None:
    """End-to-end plumbing: three arms, G generations, own pasture each."""

    monkeypatch.setattr(graph_mod, "agent_node", _stub_agent)
    results = run_population_experiment(
        seeds=[SEED],
        n_agents=N_AGENTS,
        n_generations=N_GENERATIONS,
        events_budget=EVENTS,
    )

    assert len(results["arms"]) == len(ARM_ORDER)
    assert {arm["arm"] for arm in results["arms"]} == set(ARM_ORDER)
    for arm in results["arms"]:
        assert len(arm["generations"]) == N_GENERATIONS


def test_price_is_reported_one_generation_late(monkeypatch) -> None:
    """⭐ D-101: G generations give G−1 Price rows, and the first has none."""

    monkeypatch.setattr(graph_mod, "agent_node", _stub_agent)
    results = run_population_experiment(
        seeds=[SEED],
        n_agents=N_AGENTS,
        n_generations=N_GENERATIONS,
        events_budget=EVENTS,
    )

    for arm in results["arms"]:
        rows = arm["generations"]
        assert rows[0]["price_for_previous_transition"] is None
        closed = [
            row for row in rows if row["price_for_previous_transition"] is not None
        ]
        assert len(closed) == N_GENERATIONS - 1


def test_last_generation_plans_no_children(monkeypatch) -> None:
    """The final generation supplies z and nothing else — it has no heirs."""

    monkeypatch.setattr(graph_mod, "agent_node", _stub_agent)
    results = run_population_experiment(
        seeds=[SEED],
        n_agents=N_AGENTS,
        n_generations=N_GENERATIONS,
        events_budget=EVENTS,
    )

    for arm in results["arms"]:
        last = arm["generations"][-1]
        assert last["pedigree"] is None
        assert last["w_by_parent"] is None
        for row in arm["generations"][:-1]:
            assert sum(row["w_by_parent"].values()) == N_AGENTS
            assert len(row["pedigree"]) == N_AGENTS


def test_experiment_refuses_a_single_generation() -> None:
    """One generation has no transition, so Price is undefined (D-101)."""

    with pytest.raises(ValueError, match="n_generations must be"):
        run_population_experiment(
            seeds=[SEED], n_agents=N_AGENTS, n_generations=1, events_budget=EVENTS
        )


def test_tool_identity_reports_the_reproduction_rule(monkeypatch) -> None:
    """D-094's debt: a run that selects must say what selection rule ran (§2.8)."""

    monkeypatch.setattr(graph_mod, "agent_node", _stub_agent)
    results = run_population_experiment(
        seeds=[SEED],
        n_agents=N_AGENTS,
        n_generations=2,
        events_budget=EVENTS,
    )
    reproduction = results["tool_identity"]["reproduction"]

    from dau.generation.reproduction import TOURNAMENT_K

    assert reproduction["tournament_k"] == TOURNAMENT_K
    assert "p0_niche" in reproduction


def test_max_events_global_is_restored(monkeypatch) -> None:
    """The wrapper borrows a module global; a leak silently rescales F_agent.

    The sentinel must differ from `events_budget`, and reading whatever the
    global happens to hold is not enough: an earlier test in this module leaks
    the budget, so `before == events_budget` and the assertion passes even with
    the restore deleted. Measured — the mutation slipped through the first
    version of this test (§2.4: check WHICH test breaks, not whether one does).
    """

    monkeypatch.setattr(graph_mod, "agent_node", _stub_agent)
    monkeypatch.setattr(graph_mod, "MAX_EVENTS", MAX_EVENTS_SENTINEL)
    run_population_experiment(
        seeds=[SEED], n_agents=2, n_generations=2, events_budget=EVENTS
    )
    assert graph_mod.MAX_EVENTS == MAX_EVENTS_SENTINEL


def test_shared_pasture_scales_stock_and_capacity_with_n() -> None:
    """D-081: per-capita numbers held constant, so the trajectory is the N=1 one."""

    from dau.society.environment import POOL_MAX

    from dau.diagnostics.run_population_experiment import shared_pasture

    founders = build_arm_population(ARM_ORDER[0], SEED, N_AGENTS)
    pasture = shared_pasture(founders)

    assert pasture.capacity == pytest.approx(POOL_MAX * N_AGENTS)
    assert pasture.pool == pytest.approx(founders[0].env_state.pool * N_AGENTS)


def test_shared_pasture_keeps_the_seed_dependent_niche_stock() -> None:
    """Two seeds must not collapse onto one default starting stock."""

    from dau.diagnostics.run_population_experiment import shared_pasture

    one = shared_pasture(build_arm_population(ARM_ORDER[0], SEED, N_AGENTS))
    other = shared_pasture(build_arm_population(ARM_ORDER[0], SEED + 1, N_AGENTS))

    assert one.pool != pytest.approx(other.pool)


def test_heirs_inherit_from_their_parents_vault(monkeypatch) -> None:
    """⭐ Channel 1: a newborn must carry ancestry before its first event.

    Checked through the generation record rather than a marker count, because
    the count can legitimately be zero for an unfit parent — what must never
    happen is heirs being born from a blank niche while the pedigree claims
    descent (the state this runner was in at D-102).
    """

    monkeypatch.setattr(graph_mod, "agent_node", _stub_agent)
    results = run_population_experiment(
        seeds=[SEED],
        n_agents=N_AGENTS,
        n_generations=N_GENERATIONS,
        events_budget=EVENTS,
    )

    for arm in results["arms"]:
        for row in arm["generations"][:-1]:
            assert set(row["n_inherited_by_parent"]) == {
                a["agent_id"] for a in row["agents"]
            }
            assert len(row["birth"]) == N_AGENTS
            for agent in row["agents"]:
                assert agent["vault_bound"] is True, (
                    "an unbound agent writes no engrams, so its children "
                    "inherit nothing"
                )
            for birth in row["birth"]:
                # apply_generation advances lineage age; a heir born from a
                # blank niche stays at generation 0 forever.
                assert birth["generation"] >= 1, "heir was not born through apply_generation"
        assert arm["generations"][-1]["birth"] == []
    assert results["tool_identity"]["reproduction"]["inheritance_wired"] is True


def test_arm_vault_unbinds_every_agent_it_bound(monkeypatch) -> None:
    """A leaked binding would let the next arm read this arm's engrams (P1)."""

    monkeypatch.setattr(graph_mod, "agent_node", _stub_agent)
    run_population_experiment(
        seeds=[SEED], n_agents=2, n_generations=2, events_budget=EVENTS
    )

    assert graph_mod._memory_stores == {}
    assert graph_mod._memory_written == {}


# ---------------------------------------------------------------------------
# Channel 2 — per-arm training and adapter inheritance (step 3/4)
# ---------------------------------------------------------------------------


def _fake_adapter(base, agent_id: str):
    """A directory adapter_exists() recognises: it looks for the config file."""

    path = base / agent_id
    path.mkdir()
    (path / ADAPTER_CONFIG_FILE).write_text("{}", encoding="utf-8")
    (path / "adapter_model.safetensors").write_bytes(b"weights")
    return path


def test_null_arm_never_trains(monkeypatch) -> None:
    """P5: the arm IS the training rule, and null's whole job is to stay blank."""

    from dau.diagnostics.run_population_experiment import train_generation
    from dau.diagnostics.run_protocol_c_prime import ARM_LIVED, ARM_NULL

    monkeypatch.setattr(graph_mod, "agent_node", _stub_agent)
    results = run_population_experiment(
        seeds=[SEED], n_agents=2, n_generations=2, events_budget=EVENTS
    )
    by_arm = {arm["arm"]: arm for arm in results["arms"]}

    for row in by_arm[ARM_NULL]["generations"]:
        assert row["trained"] == {}
    assert train_generation(ARM_NULL, [], {}) == {}
    # The trained arms get a row per agent even when the LoRA gate is closed:
    # "trained nothing" and "was never asked to train" must not read alike.
    for row in by_arm[ARM_LIVED]["generations"][:-1]:
        assert set(row["trained"]) == {a["agent_id"] for a in row["agents"]}


def test_inherit_adapter_copies_the_parent_directory(monkeypatch, tmp_path) -> None:
    """⭐ Channel 2 crosses generations: the heir starts from ancestor weights."""

    from dau.foundation import local_llm

    from dau.diagnostics.run_population_experiment import inherit_adapter

    monkeypatch.setattr(local_llm, "ADAPTER_BASE_DIR", str(tmp_path))
    _fake_adapter(tmp_path, "parent-x")

    assert inherit_adapter("parent-x", "heir-x") is True
    assert (tmp_path / "heir-x" / ADAPTER_CONFIG_FILE).exists()
    assert (
        tmp_path / "heir-x" / "adapter_model.safetensors"
    ).read_bytes() == b"weights"


def test_inherit_adapter_is_a_noop_without_a_parent_adapter(
    monkeypatch, tmp_path
) -> None:
    """A founder has no ancestor; an untrained arm never wrote one."""

    from dau.foundation import local_llm

    from dau.diagnostics.run_population_experiment import inherit_adapter

    monkeypatch.setattr(local_llm, "ADAPTER_BASE_DIR", str(tmp_path))
    assert inherit_adapter("nobody", "heir-y") is False
    assert not (tmp_path / "heir-y").exists()


def test_inherit_adapter_refuses_an_existing_heir_directory(
    monkeypatch, tmp_path
) -> None:
    """D-033 / I0.7: a leftover adapter is how a fresh arm inherits an old run."""

    from dau.foundation import local_llm

    from dau.diagnostics.run_population_experiment import inherit_adapter

    monkeypatch.setattr(local_llm, "ADAPTER_BASE_DIR", str(tmp_path))
    _fake_adapter(tmp_path, "parent-z")
    _fake_adapter(tmp_path, "heir-z")

    with pytest.raises(ValueError, match="already exists"):
        inherit_adapter("parent-z", "heir-z")


def test_inherit_adapter_refuses_a_stale_heir_even_with_no_parent_adapter(
    monkeypatch, tmp_path
) -> None:
    """⭐ A1: the heirs' half of I0.7, and the null arm is who it protects.

    Heir ids are decided by the tournament, so phase 0 can only clear the
    founders. If the refusal came after the parent check, the ONE arm that never
    trains — and therefore never has a parent adapter — would be the one able to
    start a life on a previous run's weights. That arm is the control.
    """

    from dau.foundation import local_llm

    from dau.diagnostics.run_population_experiment import inherit_adapter

    monkeypatch.setattr(local_llm, "ADAPTER_BASE_DIR", str(tmp_path))
    _fake_adapter(tmp_path, "stale-heir")

    with pytest.raises(ValueError, match="already exists"):
        inherit_adapter("parent-with-nothing", "stale-heir")


def test_inherit_adapter_tolerates_an_empty_leftover_directory(
    monkeypatch, tmp_path
) -> None:
    """An empty directory carries no weights — refusing it would be a false alarm.

    79 of the 114 directories under dau_runs/adapters on 2026-08-10 were empty,
    left by a query that used to create what it was asked about. switch_adapter
    never loads from one, so the graft must go through.
    """

    from dau.foundation import local_llm

    from dau.diagnostics.run_population_experiment import inherit_adapter

    monkeypatch.setattr(local_llm, "ADAPTER_BASE_DIR", str(tmp_path))
    _fake_adapter(tmp_path, "parent-w")
    (tmp_path / "heir-w").mkdir()

    assert inherit_adapter("parent-w", "heir-w") is True
    assert (tmp_path / "heir-w" / ADAPTER_CONFIG_FILE).exists()


def test_cli_requires_an_explicit_lora_choice() -> None:
    """A forgotten flag must not read as a deliberately untrained run (D-004)."""

    from dau.diagnostics.run_population_experiment import build_arg_parser

    with pytest.raises(SystemExit):
        build_arg_parser().parse_args(
            ["--seeds", "1", "--n-agents", "2", "--n-generations", "2",
             "--events", "3", "--results", "/tmp/x.json"]
        )


def test_heirs_actually_receive_the_grafted_adapter(monkeypatch, tmp_path) -> None:
    """The call site, not just the helper: skipping the graft must be visible.

    Measured gap — with the LoRA gate closed no adapter exists, so deleting the
    inherit_adapter call changed nothing observable and every test still passed.
    Founders are given a fake adapter here so the graft has something to carry.
    """

    from dau.foundation import local_llm

    import dau.diagnostics.run_population_experiment as pop_mod

    monkeypatch.setattr(graph_mod, "agent_node", _stub_agent)
    monkeypatch.setattr(local_llm, "ADAPTER_BASE_DIR", str(tmp_path))
    # The fixture this test needs — a saved adapter on every founder — is
    # EXACTLY what I0.7 refuses, and rightly so. Stub the predicate rather than
    # weaken the gate; I0.7 has its own test, and it asserts the abort.
    monkeypatch.setattr(
        pop_mod, "check_no_stale_adapters", lambda agent_ids: (True, "stubbed")
    )
    for index in range(2):
        for arm in ARM_ORDER:
            _fake_adapter(tmp_path, pop_mod.founder_id(arm, SEED, index))

    results = run_population_experiment(
        seeds=[SEED], n_agents=2, n_generations=2, events_budget=EVENTS
    )

    grafted = [
        birth["adapter_inherited"]
        for arm in results["arms"]
        for row in arm["generations"]
        for birth in row["birth"]
    ]
    assert grafted, "no heirs were born at all"
    assert all(grafted), "a heir was born without its ancestor's weights"


def test_shuffle_arm_trains_with_the_preference_direction_shuffled(
    monkeypatch,
) -> None:
    """`shuffled` is what makes shuffle a control rather than a second lived arm.

    Measured gap — with the LoRA gate closed _train_adapter returns before it
    ever looks at the flag, so passing shuffled=False everywhere was invisible.
    A spy is used rather than a real train step: what is under test is which
    rule each arm is asked for, not whether the gradient landed (I1.1 owns that).
    """

    from dau.diagnostics.run_protocol_c_prime import TrainOutcome

    import dau.diagnostics.run_population_experiment as pop_mod

    seen: list[tuple[str, bool]] = []
    untrained = TrainOutcome(0, 0, -1.0)

    def _spy(agent_id: str, examples, shuffled: bool = False) -> TrainOutcome:
        seen.append((agent_id, bool(shuffled)))
        return untrained

    monkeypatch.setattr(graph_mod, "agent_node", _stub_agent)
    monkeypatch.setattr(pop_mod, "_train_adapter", _spy)
    run_population_experiment(
        seeds=[SEED], n_agents=2, n_generations=2, events_budget=EVENTS
    )

    counts = {True: 0, False: 0}
    for agent_id, shuffled in seen:
        counts[shuffled] += 1
        assert (SHUFFLE_MARKER in agent_id) is shuffled, (
            f"{agent_id} trained with shuffled={shuffled}"
        )
    assert counts[True] > 0, "the shuffle arm never trained"
    assert counts[False] > 0, "the lived arm never trained"
    assert not any(NULL_MARKER in agent_id for agent_id, _ in seen)


def test_mock_llm_flag_installs_the_canned_llm(
    monkeypatch, tmp_path, fresh_cuda_process
) -> None:
    """Flagging a mock without installing it silently runs the real model.

    Measured: the first full-chain smoke run set the env var, reported
    `mock=True` in tool_identity, and spent three minutes loading Llama before
    it was killed. The flag has to reach graph._build_llm, not just the report.
    """

    import dau.diagnostics.run_population_experiment as pop_mod
    from dau.diagnostics.run_cprime_multigen import MOCK_LLM_ENV

    # main() writes this variable into the process and nothing restored it, so
    # every test that ran afterwards was silently a MOCK run. Invisible until
    # A1 wired run_quality in — the stamp then came back "mock" and I1.1
    # dropped from ABORT to FLAG, which is the gate switching itself off.
    # Setting it through monkeypatch makes the teardown responsible for it.
    monkeypatch.setenv(MOCK_LLM_ENV, "0")
    monkeypatch.setattr(graph_mod, "agent_node", _stub_agent)
    installed: list[bool] = []
    monkeypatch.setattr(
        pop_mod, "install_mock_llm", lambda: installed.append(True) or (lambda: None)
    )
    monkeypatch.setattr(
        pop_mod,
        "run_population_experiment",
        lambda **_: {"arms": [], "run_quality": "mock"},
    )

    pop_mod.main(
        [
            "--seeds", str(SEED), "--n-agents", "2", "--n-generations", "2",
            "--events", "3", "--no-lora", "--mock-llm", "--fresh-pasture",
            "--results", str(tmp_path / "out.json"),
        ]
    )

    assert installed == [True]


def test_price_partition_actually_carries_drift_domains(monkeypatch) -> None:
    """⭐ z must not be empty when the landmark was reached.

    Reading the wrong landmark key is SILENT: z comes back empty, the partition
    finds no domains and returns {}, and every generation reports a Price row
    that says nothing at all. Measured — the first full-chain run reported
    `price={}` for every transition and looked healthy otherwise.
    """

    from dau.foundation.constraints import LANDMARK_EVENT

    monkeypatch.setattr(graph_mod, "agent_node", _stub_agent)
    results = run_population_experiment(
        seeds=[SEED],
        n_agents=2,
        n_generations=2,
        events_budget=LANDMARK_EVENT + 2,
    )

    closed = [
        row["price_for_previous_transition"]
        for arm in results["arms"]
        for row in arm["generations"]
        if row["price_for_previous_transition"] is not None
    ]
    assert closed, "no transition was closed at all"
    assert any(part for part in closed), "every Price partition came back empty"
    for arm in results["arms"]:
        for row in arm["generations"]:
            for agent in row["agents"]:
                if agent["landmark"]["landmark_reached"]:
                    assert agent["landmark"]["landmark_drift_magnitudes"] is not None


# ---------------------------------------------------------------------------
# A1 — the preflight gates (D-105). Until this step the wrapper had none.
# ---------------------------------------------------------------------------


def test_results_carry_the_invariant_block_and_a_quality_stamp(monkeypatch) -> None:
    """A run that reports must say what it proved about itself first."""

    monkeypatch.setattr(graph_mod, "agent_node", _stub_agent)
    results = run_population_experiment(
        seeds=[SEED], n_agents=2, n_generations=2, events_budget=EVENTS
    )

    assert set(GATED_INVARIANTS) <= set(results["invariants"])
    assert_only_expected_flags(results)
    for invariant in ("I0.3", "I0.6"):
        assert results["invariants"][invariant] is True
    # I1.1 under --no-lora: not applicable, and deliberately NOT True — a check
    # that could not run must never read as one that succeeded.
    assert results["invariants"]["I1.1"] is None


def test_run_aborts_without_pythonhashseed(monkeypatch) -> None:
    """I0.3 is ABORT: no JSON is written, so a non-replayable run cannot report.

    The autouse fixture sets the variable for every other test; deleting it
    here is what makes this test about the gate rather than about the fixture.
    """

    monkeypatch.setattr(graph_mod, "agent_node", _stub_agent)
    monkeypatch.delenv("PYTHONHASHSEED", raising=False)

    with pytest.raises(PreflightAbort, match="I0.3"):
        run_population_experiment(
            seeds=[SEED], n_agents=2, n_generations=2, events_budget=EVENTS
        )


def test_a_stale_founder_adapter_aborts_before_any_life_runs(
    monkeypatch, tmp_path
) -> None:
    """⭐ I0.7, the gate A1 existed for — and it must fire BEFORE the run.

    D-033's leak favoured the hypothesis: `lived` accumulates training across
    runs and `null` never does. With the adapter now copied parent → heir, the
    leak no longer contaminates one life, it founds a lineage. The abort has to
    land before any agent takes an event, which is why the stub counts calls.
    """

    from dau.foundation import local_llm

    import dau.diagnostics.run_population_experiment as pop_mod

    lives: list[str] = []

    def _counting_agent(state: DAUAgentState) -> dict[str, Any]:
        lives.append(state.agent_id)
        return _stub_agent(state)

    monkeypatch.setattr(graph_mod, "agent_node", _counting_agent)
    monkeypatch.setattr(local_llm, "ADAPTER_BASE_DIR", str(tmp_path))
    _fake_adapter(tmp_path, pop_mod.founder_id(ARM_ORDER[0], SEED, 0))

    with pytest.raises(PreflightAbort, match="I0.7"):
        run_population_experiment(
            seeds=[SEED], n_agents=2, n_generations=2, events_budget=EVENTS
        )
    assert lives == [], "the run started before the stale adapter was caught"


def test_i0_7_covers_every_arm_and_seed_not_just_the_first(monkeypatch) -> None:
    """The gate's input is the whole planned founding population.

    A leak in ONE arm is the worst case, not a milder one: it breaks the
    contrast the experiment is made of. Checking only the first arm's ids would
    still pass the run that D-033 caught.
    """

    import dau.diagnostics.run_population_experiment as pop_mod

    planned = pop_mod.planned_founder_ids([SEED, SEED + 1], 2, tuple(ARM_ORDER))

    # +1 arm: the replay's founders count too. A leftover pop-replay adapter
    # would make the second pass start adapted and I4.1 would read DIVERGED for
    # a reason that is not non-determinism.
    assert len(planned) == (len(ARM_ORDER) + 1) * 2 * 2
    assert len(set(planned)) == len(planned)
    for arm in ARM_ORDER:
        assert pop_mod.founder_id(arm, SEED + 1, 1) in planned
    assert pop_mod.founder_id(pop_mod.REPLAY_ARM_LABEL, SEED, 0) in planned


def test_i1_1_aborts_when_a_trained_agent_never_moved_its_weights(
    monkeypatch,
) -> None:
    """⭐ The failure this project already shipped: counts without a gradient.

    The spy returns the pair counts a healthy arm reports and the UNREAD weight
    sentinel, which is exactly what `_train_adapter` returns on every one of its
    five early exits. Nothing else in the results distinguishes that from a real
    train step.
    """

    from dau.diagnostics.run_protocol_c_prime import (
        LORA_B_ABS_SUM_UNREAD,
        TrainOutcome,
    )

    import dau.diagnostics.run_population_experiment as pop_mod

    monkeypatch.setattr(graph_mod, "agent_node", _stub_agent)
    monkeypatch.setattr(
        pop_mod,
        "_train_adapter",
        lambda agent_id, examples, shuffled=False: TrainOutcome(
            7, 0, LORA_B_ABS_SUM_UNREAD
        ),
    )

    with pytest.raises(PreflightAbort, match="I1.1"):
        run_population_experiment(
            seeds=[SEED], n_agents=2, n_generations=2, events_budget=EVENTS, lora=True
        )


def test_i1_1_passes_when_every_trained_agent_moved(monkeypatch) -> None:
    """The other side of the same gate — otherwise it could just always abort."""

    from dau.diagnostics.run_protocol_c_prime import TrainOutcome

    import dau.diagnostics.run_population_experiment as pop_mod

    monkeypatch.setattr(graph_mod, "agent_node", _stub_agent)
    monkeypatch.setattr(
        pop_mod,
        "_train_adapter",
        lambda agent_id, examples, shuffled=False: TrainOutcome(7, 0, 0.5),
    )
    results = run_population_experiment(
        seeds=[SEED], n_agents=2, n_generations=2, events_budget=EVENTS, lora=True
    )

    assert results["invariants"]["I1.1"] is True
    assert_only_expected_flags(results)


def test_training_sections_speak_the_key_i1_1_reads(monkeypatch) -> None:
    """§2.8: the section keys are shared with the predicate, not re-invented.

    A misspelt delta key is not a type error. For a train arm it reads as
    "weights never read" and fails loudly — but for the null arm it reads as
    "nothing recorded", which is the PASSING case, so I1.1's contamination half
    would be switched off in silence. This holds the two ends together by
    feeding a null section a real number and requiring the abort.
    """

    from dau.diagnostics.preflight import check_training_moved_weights
    from dau.diagnostics.run_protocol_c_prime import ARM_NULL, TrainOutcome

    import dau.diagnostics.run_population_experiment as pop_mod

    monkeypatch.setattr(graph_mod, "agent_node", _stub_agent)
    monkeypatch.setattr(
        pop_mod,
        "_train_adapter",
        lambda agent_id, examples, shuffled=False: TrainOutcome(7, 0, 0.5),
    )
    results = run_population_experiment(
        seeds=[SEED], n_agents=2, n_generations=2, events_budget=EVENTS, lora=True
    )
    sections = pop_mod.training_sections(results["arms"])

    assert sections, "no sections were built at all"
    by_arm = {section[pop_mod.SECTION_ARM_KEY] for section in sections}
    assert by_arm == set(ARM_ORDER), "the null arm has no rows, so it is unchecked"
    for section in sections:
        if section[pop_mod.SECTION_ARM_KEY] == ARM_NULL:
            section[pop_mod.SECTION_DELTA_KEY] = 1.0
    passed, detail = check_training_moved_weights(sections, lora_enabled=True)
    assert passed is False and "null" in detail


# ---------------------------------------------------------------------------
# A2 — I4.1 replay for the population runner (D-106)
# ---------------------------------------------------------------------------


def test_replay_runs_and_lands_on_the_same_digest(monkeypatch) -> None:
    """⭐ I4.1: the only way this runner can CLAIM determinism.

    Inside a single pass each agent is trained once, so there is nothing to
    compare it against — every other gate stayed green through D-037 while the
    same seed and code produced different adapters between runs.
    """

    import dau.diagnostics.run_population_experiment as pop_mod

    monkeypatch.setattr(graph_mod, "agent_node", _stub_agent)
    results = run_population_experiment(
        seeds=[SEED], n_agents=2, n_generations=N_GENERATIONS, events_budget=EVENTS
    )
    replay = results["replay"]

    assert replay is not None, "the replay never ran"
    assert results["invariants"]["I4.1"] is True
    assert replay["recorded_digest"] == replay["replay_digest"]
    # A prefix of the recorded arm, not a sample of it: generations run in
    # sequence, so a later one cannot change what an earlier one did.
    assert len(replay["replay_per_generation"]) == pop_mod.REPLAY_GENERATIONS
    assert (
        replay["recorded_per_generation"] == replay["replay_per_generation"]
    )


def test_a_diverging_replay_aborts_the_run(monkeypatch) -> None:
    """The gate has to bite, or it is decoration.

    The divergence is injected into the SECOND pass's digests rather than into
    the check, so what is under test is the wiring: a run whose two passes
    disagree must not be written.
    """

    import dau.diagnostics.run_population_experiment as pop_mod

    real_run_arm = pop_mod.run_arm

    def _diverging(arm, *args, **kwargs):
        result = real_run_arm(arm, *args, **kwargs)
        if arm == pop_mod.REPLAY_ARM_LABEL:
            for row in result["generations"]:
                row["arm_digest"] = "diverged-" + row["arm_digest"]
        return result

    monkeypatch.setattr(graph_mod, "agent_node", _stub_agent)
    monkeypatch.setattr(pop_mod, "run_arm", _diverging)

    with pytest.raises(PreflightAbort, match="I4.1"):
        run_population_experiment(
            seeds=[SEED], n_agents=2, n_generations=N_GENERATIONS,
            events_budget=EVENTS,
        )


def test_replay_runs_last_and_under_its_own_arm_label(monkeypatch) -> None:
    """Two properties, and both are load-bearing.

    Its own label, because re-using the original ids would make the second pass
    load the adapters the first one just wrote — phase 1 adapted where the
    original ran bare. Last, because otherwise a later arm could consume the
    adapters the replay leaves behind.
    """

    import dau.diagnostics.run_population_experiment as pop_mod

    real_run_arm = pop_mod.run_arm
    order: list[str] = []

    def _recording(arm, *args, **kwargs):
        order.append(arm)
        return real_run_arm(arm, *args, **kwargs)

    monkeypatch.setattr(graph_mod, "agent_node", _stub_agent)
    monkeypatch.setattr(pop_mod, "run_arm", _recording)
    results = run_population_experiment(
        seeds=[SEED], n_agents=2, n_generations=N_GENERATIONS, events_budget=EVENTS
    )

    assert order[-1] == pop_mod.REPLAY_ARM_LABEL
    assert order.count(pop_mod.REPLAY_ARM_LABEL) == 1
    assert set(order[:-1]) == set(ARM_ORDER)
    replayed_ids = {
        agent["agent_id"]
        for row in results["replay"]["arm_result"]["generations"]
        for agent in row["agents"]
    }
    lived_ids = {
        agent["agent_id"]
        for arm in results["arms"]
        for row in arm["generations"]
        for agent in row["agents"]
    }
    assert replayed_ids and not (replayed_ids & lived_ids)


def test_the_replay_arm_is_checked_by_i1_1_too(monkeypatch) -> None:
    """It is a trained arm: a silent no-op there makes the digests match.

    Two passes that both trained nothing agree perfectly, so I4.1 would report
    "identical" about a run in which Channel 2 never fired.
    """

    import dau.diagnostics.run_population_experiment as pop_mod

    monkeypatch.setattr(graph_mod, "agent_node", _stub_agent)
    results = run_population_experiment(
        seeds=[SEED], n_agents=2, n_generations=N_GENERATIONS, events_budget=EVENTS
    )
    sections = pop_mod.training_sections(
        results["arms"] + [results["replay"]["arm_result"]]
    )

    assert pop_mod.REPLAY_ARM_LABEL in {
        section[pop_mod.SECTION_ARM_KEY] for section in sections
    }


def test_replay_is_skipped_under_a_canned_llm(monkeypatch) -> None:
    """A mock replays trivially — the check would assert nothing and still cost.

    None, not True: a gate that could not run must never read as one that
    passed.
    """

    import dau.diagnostics.run_population_experiment as pop_mod

    monkeypatch.setattr(graph_mod, "agent_node", _stub_agent)
    monkeypatch.setattr(pop_mod, "mock_llm_enabled", lambda: True)
    results = run_population_experiment(
        seeds=[SEED], n_agents=2, n_generations=2, events_budget=EVENTS
    )

    assert results["replay"] is None
    assert results["invariants"]["I4.1"] is None
    assert results["run_quality"] == "mock"


def test_chain_digest_notices_the_order_of_the_generations(monkeypatch) -> None:
    """Two generations that swapped places are a divergence, not a match."""

    import dau.diagnostics.run_population_experiment as pop_mod

    forward = pop_mod.chain_digest(["a", "b"])

    assert forward != pop_mod.chain_digest(["b", "a"])
    assert forward != pop_mod.chain_digest(["ab"])
    assert forward == pop_mod.chain_digest(["a", "b"])


# ---------------------------------------------------------------------------
# A3 — G >= 3 as a structural requirement (D-107)
# ---------------------------------------------------------------------------


def test_two_generations_are_stamped_uninformative(monkeypatch, capsys) -> None:
    """⛔ A3: a run that can only report zero must not read as one that measured it.

    Under P0-① the founders are identical, so the ONLY transition a G=2 run has
    is the one whose z has no variance — Cov(w, z) is zero however the
    tournament goes. G=2 is still accepted (Price is defined, and it is what a
    smoke run wants), so the guard is a stamp, not a refusal.
    """

    monkeypatch.setattr(graph_mod, "agent_node", _stub_agent)
    results = run_population_experiment(
        seeds=[SEED], n_agents=2, n_generations=2, events_budget=EVENTS
    )

    assert results["generations_informative"] is False
    assert "zero BY CONSTRUCTION" in capsys.readouterr().out


def test_three_generations_are_not_stamped(monkeypatch) -> None:
    """The other side: the stamp has to distinguish, not always fire."""

    monkeypatch.setattr(graph_mod, "agent_node", _stub_agent)
    results = run_population_experiment(
        seeds=[SEED], n_agents=2, n_generations=3, events_budget=EVENTS
    )

    assert results["generations_informative"] is True


def test_one_generation_is_still_refused() -> None:
    """The two floors are different things: undefined is an error, uninformative is a stamp."""

    import dau.diagnostics.run_population_experiment as pop_mod

    assert (
        pop_mod.MINIMUM_GENERATIONS_DEFINED < pop_mod.MINIMUM_GENERATIONS_INFORMATIVE
    )
    with pytest.raises(ValueError, match="n_generations must be"):
        run_population_experiment(
            seeds=[SEED], n_agents=2, n_generations=1, events_budget=EVENTS
        )


# ---------------------------------------------------------------------------
# D-108 — a life too quiet to yield a preference pair is data, not a failure
# ---------------------------------------------------------------------------


def _outcome(reason: str):
    """A declined train step: zero counts and an unread weight, plus a reason.

    This is byte-for-byte what all five of _train_adapter's early exits return,
    which is the whole problem — only `reason` tells them apart.
    """

    from dau.diagnostics.run_protocol_c_prime import (
        LORA_B_ABS_SUM_UNREAD,
        TrainOutcome,
    )

    return TrainOutcome(0, 0, LORA_B_ABS_SUM_UNREAD, reason=reason)


def test_an_agent_with_no_pairs_does_not_take_the_run_down(monkeypatch) -> None:
    """⭐ D-108, measured on the first real pilot: two of 48 agents had no pairs.

    A life can be too quiet to yield a usable preference pair, and that is a
    property of the LIFE. Aborting on it puts a selection effect on which runs
    may report at all: runs where every agent lived richly pass, runs with one
    quiet agent are never written — and the JSON is never produced, so the
    other 46 agents are lost with it.
    """

    from dau.diagnostics.run_protocol_c_prime import TrainOutcome
    from dau.foundation.constraints import TRAIN_SKIP_NO_PAIRS

    import dau.diagnostics.run_population_experiment as pop_mod

    quiet = "pop-lived-"

    def _mostly_fine(agent_id: str, examples, shuffled: bool = False):
        if agent_id.startswith(quiet) and agent_id.endswith("a1"):
            return _outcome(TRAIN_SKIP_NO_PAIRS)
        return TrainOutcome(7, 0, 0.5)

    monkeypatch.setattr(graph_mod, "agent_node", _stub_agent)
    monkeypatch.setattr(pop_mod, "_train_adapter", _mostly_fine)
    results = run_population_experiment(
        seeds=[SEED], n_agents=2, n_generations=2, events_budget=EVENTS, lora=True
    )

    assert results["invariants"]["I1.1"] is True
    assert_only_expected_flags(results)


@pytest.mark.parametrize(
    "reason",
    [
        "lora_update import failed",
        "pair builder raised",
        "train raised",
        "declined without a stated reason",
        "",
    ],
)
def test_every_other_refusal_still_aborts(monkeypatch, reason: str) -> None:
    """⛔ The exemption is on the REASON, and on exactly one of them.

    Four of the five early exits ALSO report zero pairs, so exempting by count
    would wave an import failure, a pair builder that raised and a train step
    that raised straight through — and e4c026b (weights that never moved while
    the run reported healthy counts) is the failure this gate exists for.
    """

    from dau.diagnostics.run_protocol_c_prime import TrainOutcome

    import dau.diagnostics.run_population_experiment as pop_mod

    # ⚠ MIXED on purpose, and this is the whole discriminating power of the
    # test. With every agent declining, the gate aborts anyway via "no ungated
    # train arm to check" — so the test would pass even if the exemption were
    # wired to the pair COUNT, which would wave these four refusals through.
    # Measured: two mutations (exempt-by-count, exempt-on-any-reason) both
    # survived the all-declining version of this test (§2.4).
    def _one_bad_agent(agent_id: str, examples, shuffled: bool = False):
        if agent_id.endswith("a1"):
            return _outcome(reason)
        return TrainOutcome(7, 0, 0.5)

    monkeypatch.setattr(graph_mod, "agent_node", _stub_agent)
    monkeypatch.setattr(pop_mod, "_train_adapter", _one_bad_agent)

    with pytest.raises(PreflightAbort, match="I1.1"):
        run_population_experiment(
            seeds=[SEED], n_agents=2, n_generations=2, events_budget=EVENTS,
            lora=True,
        )


def test_the_exempting_reason_is_the_trainers_own_string() -> None:
    """Both ends of the branch read ONE constant — never two literals.

    The gate branches on this text. If the trainer's wording and the reader's
    wording were separate literals, the day one was reworded the exemption
    would stop firing and the only symptom would be a run that aborts for a
    reason nobody can find.
    """

    from dau.foundation import constraints, local_llm

    import dau.diagnostics.run_population_experiment as pop_mod

    assert (
        pop_mod.TRAIN_SKIP_NO_PAIRS
        is local_llm.TRAIN_SKIP_NO_PAIRS
        is constraints.TRAIN_SKIP_NO_PAIRS
    )


def test_the_reason_reaches_the_results_file(monkeypatch) -> None:
    """A reader must be able to see WHICH agent was exempted, and why.

    Without this the results say "48 agents, 46 trained" and nothing about the
    other two — the exemption would be invisible in the artefact and visible
    only in a console log nobody keeps.
    """

    from dau.foundation.constraints import TRAIN_SKIP_NO_PAIRS

    import dau.diagnostics.run_population_experiment as pop_mod

    from dau.diagnostics.run_protocol_c_prime import TrainOutcome

    def _one_quiet(agent_id: str, examples, shuffled: bool = False):
        if agent_id.endswith("a1"):
            return _outcome(TRAIN_SKIP_NO_PAIRS)
        return TrainOutcome(7, 0, 0.5)

    monkeypatch.setattr(graph_mod, "agent_node", _stub_agent)
    monkeypatch.setattr(pop_mod, "_train_adapter", _one_quiet)
    results = run_population_experiment(
        seeds=[SEED], n_agents=2, n_generations=2, events_budget=EVENTS, lora=True
    )

    trained = results["arms"][0]["generations"][0]["trained"]
    assert trained, "no training block at all"
    quiet = [
        record
        for agent_id, record in trained.items()
        if agent_id.endswith("a1")
    ]
    assert quiet and all(
        record[pop_mod.SECTION_REASON_KEY] == TRAIN_SKIP_NO_PAIRS
        for record in quiet
    )
    sections = pop_mod.training_sections(results["arms"])
    exempted = [s for s in sections if s[pop_mod.SECTION_GATED_KEY]]
    assert exempted, "the exemption never reached the gate's input"


def test_a_run_where_EVERY_agent_was_exempted_still_aborts(monkeypatch) -> None:
    """⭐ The exemption must not become a blanket off-switch.

    One quiet life among many is data. A run in which NOTHING trained
    demonstrates nothing about Channel 2, and `lived` / `shuffle` / `null` then
    differ only in name — so the gate still refuses, via "no ungated train arm
    to check". Found by writing the test above with every agent exempted and
    watching it abort, which was the correct answer.
    """

    from dau.foundation.constraints import TRAIN_SKIP_NO_PAIRS

    import dau.diagnostics.run_population_experiment as pop_mod

    monkeypatch.setattr(graph_mod, "agent_node", _stub_agent)
    monkeypatch.setattr(
        pop_mod,
        "_train_adapter",
        lambda agent_id, examples, shuffled=False: _outcome(TRAIN_SKIP_NO_PAIRS),
    )

    with pytest.raises(PreflightAbort, match="I1.1"):
        run_population_experiment(
            seeds=[SEED], n_agents=2, n_generations=2, events_budget=EVENTS,
            lora=True,
        )


# ---------------------------------------------------------------------------
# D-111 — partial results survive a crash or a refusal
# ---------------------------------------------------------------------------


def test_checkpoint_is_written_after_every_generation(monkeypatch, tmp_path) -> None:
    """⭐ The point is the GRANULARITY, not that a file eventually appears.

    Per arm would already be an improvement, but at the main run's scale one
    arm is hours. This asserts the file grows while a single arm is still in
    flight, which is the only version that bounds what a crash costs.
    """

    import json as _json

    import dau.diagnostics.run_population_experiment as pop_mod

    partial = tmp_path / "run.json.partial.json"
    seen: list[int] = []
    real_write = pop_mod.Checkpoint.write

    def _counting_write(self, in_progress=None):
        real_write(self, in_progress)
        payload = _json.loads(partial.read_text(encoding="utf-8"))
        seen.append(
            sum(len(a["generations"]) for a in payload["arms"])
        )

    monkeypatch.setattr(graph_mod, "agent_node", _stub_agent)
    monkeypatch.setattr(pop_mod.Checkpoint, "write", _counting_write)
    run_population_experiment(
        seeds=[SEED], n_agents=2, n_generations=N_GENERATIONS, events_budget=EVENTS,
        checkpoint_path=partial,
    )

    # Strictly increasing generation counts, and more writes than there are
    # arms: a per-arm checkpoint would produce exactly len(ARM_ORDER) of them.
    assert len(seen) > len(ARM_ORDER)
    assert seen == sorted(seen)


def test_the_checkpoint_never_carries_a_quality_stamp(monkeypatch, tmp_path) -> None:
    """⛔ A gate-less file must not look gated.

    The checkpoint is written before any gate has run. If it carried
    `run_quality` or an invariants block, a reader — or the analyzer — would
    treat a mid-flight snapshot as a judged result, which is the silent fake
    result the whole preflight system exists to prevent.
    """

    import json as _json

    import dau.diagnostics.run_population_experiment as pop_mod

    partial = tmp_path / "run.json.partial.json"
    captured: list[dict] = []
    real_write = pop_mod.Checkpoint.write

    def _capturing_write(self, in_progress=None):
        real_write(self, in_progress)
        captured.append(_json.loads(partial.read_text(encoding="utf-8")))

    monkeypatch.setattr(graph_mod, "agent_node", _stub_agent)
    monkeypatch.setattr(pop_mod.Checkpoint, "write", _capturing_write)
    run_population_experiment(
        seeds=[SEED], n_agents=2, n_generations=2, events_budget=EVENTS,
        checkpoint_path=partial,
    )

    assert captured, "nothing was ever written"
    for payload in captured:
        assert payload[pop_mod.RESULTS_COMPLETE_KEY] is False
        assert "run_quality" not in payload
        assert "invariants" not in payload
        assert "INCOMPLETE" in payload["note"]


def test_a_crash_mid_run_leaves_the_measurements_behind(
    monkeypatch, tmp_path
) -> None:
    """⭐ D-111's whole reason: two runs were lost in one night.

    The crash is injected in the middle of the third arm, so the file must
    still hold the two finished arms — that is the data that used to evaporate.
    """

    import json as _json

    import dau.diagnostics.run_population_experiment as pop_mod

    partial = tmp_path / "run.json.partial.json"
    real_run_arm = pop_mod.run_arm

    def _crashing(arm, *args, **kwargs):
        if arm == ARM_ORDER[-1]:
            raise RuntimeError("power cut")
        return real_run_arm(arm, *args, **kwargs)

    monkeypatch.setattr(graph_mod, "agent_node", _stub_agent)
    monkeypatch.setattr(pop_mod, "run_arm", _crashing)

    with pytest.raises(RuntimeError, match="power cut"):
        run_population_experiment(
            seeds=[SEED], n_agents=2, n_generations=2, events_budget=EVENTS,
            checkpoint_path=partial,
        )

    payload = _json.loads(partial.read_text(encoding="utf-8"))
    assert len(payload["arms"]) == len(ARM_ORDER) - 1
    assert payload[pop_mod.RESULTS_COMPLETE_KEY] is False


def test_the_finished_result_is_marked_complete(monkeypatch, tmp_path) -> None:
    """And the real result says so, which is what the reader checks."""

    monkeypatch.setattr(graph_mod, "agent_node", _stub_agent)
    results = run_population_experiment(
        seeds=[SEED], n_agents=2, n_generations=2, events_budget=EVENTS,
        checkpoint_path=tmp_path / "run.json.partial.json",
    )

    import dau.diagnostics.run_population_experiment as pop_mod

    assert results[pop_mod.RESULTS_COMPLETE_KEY] is True


def test_checkpoint_path_hangs_off_the_results_name() -> None:
    """So the partial file sorts next to what it belongs to, and cannot collide."""

    import dau.diagnostics.run_population_experiment as pop_mod

    from pathlib import Path as _Path

    assert pop_mod.checkpoint_path_for(_Path("dau_runs/x.json")) == _Path(
        "dau_runs/x.json.partial.json"
    )


# ---------------------------------------------------------------------------
# D-112 — how close the universe came to the endpoint's trigger
# ---------------------------------------------------------------------------


def test_delta_profile_reports_the_headroom_to_the_trauma_threshold() -> None:
    """⭐ The number B1 could not produce, and the decision it blocks.

    z is written by exactly one condition: delta magnitude >= 0.7. B1 found z
    empty in 23 of 24 cells, and the results file could not say whether the
    universe missed by 0.02 or by 0.5 — two situations that call for opposite
    decisions about the endpoint.
    """

    from dau.foundation.delta import DELTA_THRESHOLD_DEEP

    from dau.diagnostics.run_population_experiment import delta_profile

    rows = [
        {"agent_id": "a", "delta_magnitude": 0.10},
        {"agent_id": "a", "delta_magnitude": 0.68},
        {"agent_id": "b", "delta_magnitude": 0.90},
    ]
    profile = delta_profile("a", rows, NO_CRISIS)

    assert profile["n_events"] == 2, "another agent's events leaked in"
    assert profile["max"] == pytest.approx(0.68)
    assert profile["n_at_or_above_trauma"] == 0
    assert profile["headroom_to_trauma"] == pytest.approx(
        DELTA_THRESHOLD_DEEP - 0.68
    )


def test_delta_profile_counts_a_crossing_and_reports_negative_headroom() -> None:
    """The other side: a life that DID cross must be visibly different."""

    from dau.diagnostics.run_population_experiment import delta_profile

    profile = delta_profile(
        "a", [{"agent_id": "a", "delta_magnitude": 0.9}], NO_CRISIS
    )

    assert profile["n_at_or_above_trauma"] == 1
    assert profile["headroom_to_trauma"] < 0


def test_delta_profile_of_a_life_with_no_events_is_not_zero() -> None:
    """None, not 0.0: 'never measured' and 'measured zero' are opposites here.

    A headroom of 0.0 would read as "this life sat exactly on the threshold",
    which is the most interesting possible value — and it would be a lie about
    a life that produced no event at all.
    """

    from dau.diagnostics.run_population_experiment import delta_profile

    profile = delta_profile(
        "ghost", [{"agent_id": "a", "delta_magnitude": 0.9}], NO_CRISIS
    )

    assert profile["n_events"] == 0
    assert profile["max"] is None
    assert profile["headroom_to_trauma"] is None


def test_the_delta_profile_reaches_the_results_file(monkeypatch) -> None:
    """Aggregating it is useless if it never lands in the artefact."""

    monkeypatch.setattr(graph_mod, "agent_node", _stub_agent)
    results = run_population_experiment(
        seeds=[SEED], n_agents=2, n_generations=2, events_budget=EVENTS
    )

    agents = results["arms"][0]["generations"][0]["agents"]
    assert agents, "no agents at all"
    for agent in agents:
        assert "delta_profile" in agent
        assert "headroom_to_trauma" in agent["delta_profile"]


def test_delta_profile_counts_the_boundary_the_same_way_the_universe_does() -> None:
    """⭐ Exactly 0.7 IS trauma, and the reporter must agree with update_drift.

    classify_delta returns TRAUMA at magnitude >= 0.7, and test_drift.py pins
    that boundary from the other side (0.69 writes no drift, 0.70 does). A
    reporter using `>` would say "no crossing" about a life the universe
    treated as traumatic — the instrument and the thing it reports on would
    disagree in silence, at the one value where it matters most.

    Measured: with `>` instead of `>=`, every other test in this group still
    passed (§2.4 — check WHICH test breaks).
    """

    from dau.foundation.delta import (
        DELTA_THRESHOLD_DEEP,
        DeltaRecord,
        is_trauma,
    )

    from dau.diagnostics.run_population_experiment import delta_profile

    exact = DELTA_THRESHOLD_DEEP
    profile = delta_profile(
        "a", [{"agent_id": "a", "delta_magnitude": exact}], NO_CRISIS
    )

    assert profile["n_at_or_above_trauma"] == 1
    assert profile["headroom_to_trauma"] == pytest.approx(0.0)
    # And the universe agrees, read from its own function rather than restated:
    # if these two ever disagree the reporter is describing a different world.
    snapshot = {
        "energy": 1.0,
        "resource_load": 0.0,
        "uncertainty_load": 0.0,
        "social_load": 0.0,
    }
    assert is_trauma(
        DeltaRecord(
            timestamp=1,
            magnitude=exact,
            affected_domain="resource",
            snapshot_before=snapshot,
            snapshot_after=snapshot,
        )
    )


# ---------------------------------------------------------------------------
# D-116 — the CUDA allocator setting (D-114's OOM fix)
# ---------------------------------------------------------------------------


def test_allocator_config_is_applied_before_the_gpu(fresh_cuda_process) -> None:
    """The runner installs expandable_segments, and names the constant it used.

    Mutation check (§2.4): dropping the ``os.environ[...] = ...`` line leaves
    every other test in this module passing — the setting is invisible to the
    rest of the harness by design, which is exactly why it needs its own test.
    """

    from dau.foundation.local_llm import (
        ALLOC_CONF_SET_BY_RUNNER,
        CUDA_ALLOC_CONF_ENV,
        CUDA_ALLOC_CONF_EXPANDABLE,
        apply_cuda_allocator_config,
    )

    report = apply_cuda_allocator_config()

    import os

    assert os.environ[CUDA_ALLOC_CONF_ENV] == CUDA_ALLOC_CONF_EXPANDABLE
    assert report["source"] == ALLOC_CONF_SET_BY_RUNNER
    assert report["value"] == CUDA_ALLOC_CONF_EXPANDABLE


def test_allocator_config_refuses_to_overwrite_a_different_value(monkeypatch) -> None:
    """A conflicting operator setting stops the run instead of being replaced.

    §2.11: two sources disagree about a memory setting, so the process asks
    rather than picking one. The value already in the environment survives.
    """

    from dau.foundation.local_llm import (
        CUDA_ALLOC_CONF_ENV,
        apply_cuda_allocator_config,
    )

    monkeypatch.setenv(CUDA_ALLOC_CONF_ENV, "max_split_size_mb:128")
    with pytest.raises(ValueError, match="max_split_size_mb:128"):
        apply_cuda_allocator_config()

    import os

    assert os.environ[CUDA_ALLOC_CONF_ENV] == "max_split_size_mb:128"


def test_allocator_config_accepts_an_operator_who_set_the_same_value(
    monkeypatch,
) -> None:
    """Exporting it by hand is the documented way, so it must not be an error."""

    from dau.foundation.local_llm import (
        ALLOC_CONF_FROM_OPERATOR,
        CUDA_ALLOC_CONF_ENV,
        CUDA_ALLOC_CONF_EXPANDABLE,
        apply_cuda_allocator_config,
    )

    monkeypatch.setenv(CUDA_ALLOC_CONF_ENV, CUDA_ALLOC_CONF_EXPANDABLE)
    assert apply_cuda_allocator_config()["source"] == ALLOC_CONF_FROM_OPERATOR


def test_tool_identity_reports_the_allocator_from_the_environment(
    monkeypatch,
) -> None:
    """The block follows the process, it does not repeat the constant (§2.8).

    A run whose allocator setting never took effect must report ``applied:
    False``; restating CUDA_ALLOC_CONF_EXPANDABLE would have it claim the fix
    in a file produced without it — the U3a failure mode, on memory instead of
    the model id.
    """

    from dau.diagnostics.tool_identity import LORA_CHOICE_OFF, build_tool_identity
    from dau.foundation.local_llm import CUDA_ALLOC_CONF_ENV, CUDA_ALLOC_CONF_EXPANDABLE

    monkeypatch.setenv(CUDA_ALLOC_CONF_ENV, CUDA_ALLOC_UNSET)
    block = build_tool_identity(lora_choice=LORA_CHOICE_OFF, seeds=[SEED])[
        "cuda_allocator"
    ]
    assert block["applied"] is False
    assert block["expected"] == CUDA_ALLOC_CONF_EXPANDABLE

    monkeypatch.setenv(CUDA_ALLOC_CONF_ENV, CUDA_ALLOC_CONF_EXPANDABLE)
    applied = build_tool_identity(lora_choice=LORA_CHOICE_OFF, seeds=[SEED])[
        "cuda_allocator"
    ]
    assert applied["applied"] is True
    assert applied["value"] == CUDA_ALLOC_CONF_EXPANDABLE


def test_allocator_config_refuses_once_cuda_is_up(monkeypatch) -> None:
    """Setting it after the allocator started is a LIE, not a fallback (§2.9).

    PyTorch reads PYTORCH_CUDA_ALLOC_CONF once. Assigning it afterwards
    succeeds in os.environ and changes nothing in the allocator — and
    tool_identity, which reads os.environ, would then report a fix the run
    never had. That is GAP-15's failure mode on memory instead of temperature,
    so the process stops instead.
    """

    from dau.foundation.local_llm import (
        CUDA_ALLOC_CONF_ENV,
        apply_cuda_allocator_config,
    )

    torch = pytest.importorskip("torch")
    monkeypatch.setenv(CUDA_ALLOC_CONF_ENV, CUDA_ALLOC_UNSET)
    monkeypatch.setattr(torch.cuda, "is_initialized", lambda: True)

    with pytest.raises(ValueError, match="already initialised"):
        apply_cuda_allocator_config()

    import os

    assert os.environ[CUDA_ALLOC_CONF_ENV] == CUDA_ALLOC_UNSET


def test_main_applies_the_allocator_setting(
    monkeypatch, tmp_path, fresh_cuda_process
) -> None:
    """The wiring itself, not just the function (§2.4).

    Measured: deleting the ``apply_cuda_allocator_config()`` call from main()
    broke NOTHING — the three unit tests above call the function directly and
    the mock-llm test stubs the experiment away. A fix present in the codebase
    and absent from the run path is the failure this test exists for.
    """

    import os

    import dau.diagnostics.run_population_experiment as pop_mod
    from dau.diagnostics.run_cprime_multigen import MOCK_LLM_ENV
    from dau.foundation.local_llm import CUDA_ALLOC_CONF_ENV, CUDA_ALLOC_CONF_EXPANDABLE

    monkeypatch.setenv(MOCK_LLM_ENV, "0")
    monkeypatch.setattr(pop_mod, "install_mock_llm", lambda: (lambda: None))
    monkeypatch.setattr(
        pop_mod,
        "run_population_experiment",
        lambda **_: {"arms": [], "run_quality": "mock"},
    )

    pop_mod.main(
        [
            "--seeds", str(SEED), "--n-agents", "2", "--n-generations", "2",
            "--events", "3", "--no-lora", "--mock-llm", "--fresh-pasture",
            "--results", str(tmp_path / "out.json"),
        ]
    )

    assert os.environ[CUDA_ALLOC_CONF_ENV] == CUDA_ALLOC_CONF_EXPANDABLE


# ---------------------------------------------------------------------------
# D-117 — the second writer of z: the commons crisis
# ---------------------------------------------------------------------------


def test_delta_profile_sees_the_crisis_channel_when_the_individual_one_is_empty(
) -> None:
    """⭐ Seed 9904's exact shape: 0 individual crossings, every agent scarred.

    This is the case D-115 could not read from the results file. The commons
    crisis calls update_drift for every agent at once, so `z` is full while the
    individual channel reports nothing came close. Before D-117 this profile
    said "headroom 0.6, no crossing" about a life whose drift map had been
    rewritten.
    """

    from dau.diagnostics.run_population_experiment import delta_profile

    quiet_pe = [{"agent_id": "a", "delta_magnitude": 0.10}]
    famine = [
        {"agent_id": "a", "crisis": True, "crisis_magnitude": 1.0},
        {"agent_id": "b", "crisis": True, "crisis_magnitude": 1.0},
    ]
    profile = delta_profile("a", quiet_pe, famine)

    # The individual channel is unchanged — and still says "nothing close".
    assert profile["n_at_or_above_trauma"] == 0
    assert profile["channel"] == "individual"
    # The commons channel is where this life's drift actually came from.
    assert profile["crisis"]["n_crisis_events"] == 1, "another agent's famine leaked"
    assert profile["crisis"]["n_at_or_above_trauma"] == 1
    assert profile["crisis"]["headroom_to_trauma"] < 0
    assert profile["n_at_or_above_trauma_either_channel"] == 1


def test_delta_profile_keeps_the_two_channels_apart() -> None:
    """Pooling them would rebuild exactly the blindness D-115 diagnosed.

    A crisis scars the whole arm simultaneously, so its magnitude carries no
    between-agent information; the individual channel is the only one that can.
    Summed into one number, a seed whose z came from famine and one whose z
    came from surprise look identical again.
    """

    from dau.diagnostics.run_population_experiment import delta_profile

    profile = delta_profile(
        "a",
        [{"agent_id": "a", "delta_magnitude": 0.20}],
        [{"agent_id": "a", "crisis": True, "crisis_magnitude": 1.0}],
    )

    assert profile["max"] == pytest.approx(0.20), "crisis magnitude leaked into it"
    assert profile["n_events"] == 1, "crisis events counted as individual ones"
    assert profile["crisis"]["max"] == pytest.approx(1.0)


def test_quiet_pasture_rows_are_not_read_as_crises() -> None:
    """A row with crisis_magnitude None is an event that scarred nobody."""

    from dau.diagnostics.run_population_experiment import delta_profile

    profile = delta_profile(
        "a",
        [{"agent_id": "a", "delta_magnitude": 0.20}],
        [{"agent_id": "a", "crisis": False, "crisis_magnitude": None}],
    )

    assert profile["crisis"]["n_crisis_events"] == 0
    assert profile["crisis"]["max"] is None
    assert profile["n_at_or_above_trauma_either_channel"] == 0


def test_recorded_crisis_magnitude_is_the_one_the_universe_scarred_with() -> None:
    """⭐ §2.8: the reporter must not recompute the scar, it must read it.

    The recorder takes the number from ``crisis_trauma_magnitude``, the same
    function ``apply_crisis_trauma`` scars with — so the log cannot describe a
    different universe than the one that ran. Checked against update_drift's
    own threshold rather than a literal: the point is whether the scar the
    commons writes is a trauma, and both sides must say so together.
    """

    from dau.foundation.delta import DELTA_THRESHOLD_DEEP
    from dau.foundation.drift import DriftState
    from dau.society.environment import (
        POOL_CRISIS_THRESHOLD,
        apply_crisis_trauma,
        crisis_trauma_magnitude,
    )

    below = POOL_CRISIS_THRESHOLD / 2.0
    magnitude = crisis_trauma_magnitude(below)

    assert magnitude is not None
    assert magnitude >= DELTA_THRESHOLD_DEEP, "the commons scar must be a trauma"
    assert crisis_trauma_magnitude(POOL_CRISIS_THRESHOLD) is None, "boundary is safe"

    # And the universe agrees: at this ratio drift actually moves.
    scarred = apply_crisis_trauma(DriftState(), below)
    assert scarred != DriftState()
    assert apply_crisis_trauma(DriftState(), POOL_CRISIS_THRESHOLD) == DriftState()


def test_pool_event_rows_carry_the_crisis_magnitude(monkeypatch) -> None:
    """The wiring: the graph's commons recorder writes it, not just the flag."""

    import dau.foundation.graph as g
    from dau.society.environment import POOL_CRISIS_THRESHOLD, crisis_trauma_magnitude

    g.reset_pool_event_log()
    ratio = POOL_CRISIS_THRESHOLD / 2.0
    g._record_pool_event(
        agent_id="a",
        event_counter=1,
        extraction=0.0,
        requested=8.0,
        pool_ratio=ratio,
        crisis=True,
        crisis_magnitude=crisis_trauma_magnitude(ratio),
    )
    row = g.get_pool_event_log()[-1]
    g.reset_pool_event_log()

    assert row["crisis_magnitude"] == pytest.approx(crisis_trauma_magnitude(ratio))


# ---------------------------------------------------------------------------
# D-118 — I0.4, the gate D-105 had to leave out
# ---------------------------------------------------------------------------


def test_the_seed_survives_every_generation_of_ids() -> None:
    """⭐ A third-generation heir must still name the seed it descends from.

    The shuffle arm draws its permutation from the seed parsed out of the id,
    so an id the parser cannot read costs the run its replay guarantee — that
    is GAP-11, and in a population it would seed an entire lineage rather than
    one life. Heir suffixes are APPENDED, so the founder segment has to keep
    answering at any depth; this test is what pins that property.
    """

    from dau.diagnostics.run_population_experiment import (
        founder_id,
        seed_from_population_id,
    )
    from dau.generation.population import heir_id

    founder = founder_id(ARM_ORDER[0], SEED, 3)
    gen2 = heir_id(founder, 2, 0)
    gen3 = heir_id(gen2, 3, 1)

    assert seed_from_population_id(founder) == SEED
    assert seed_from_population_id(gen2) == SEED
    assert seed_from_population_id(gen3) == SEED


def test_an_unreadable_id_raises_instead_of_defaulting() -> None:
    """§2.9: no silent fallback. A default seed would be a different universe."""

    from dau.diagnostics.run_population_experiment import seed_from_population_id

    with pytest.raises(ValueError, match="no seed segment"):
        seed_from_population_id("cprime-lived-9901")


def test_i04_rejects_an_id_that_names_an_unplanned_seed() -> None:
    """The gate compares the id's seed against the seeds the run planned.

    Checked through the shared predicate with THIS runner's parser, not a
    re-implementation: the point of D-118 is that both runners keep meaning
    the same thing by I0.4 while reading different id formats (§2.8).
    """

    from dau.diagnostics.preflight import check_seed_derivation
    from dau.diagnostics.run_population_experiment import (
        founder_id,
        seed_from_population_id,
    )

    ok, note = check_seed_derivation(
        [founder_id(ARM_ORDER[0], SEED, 0)], [SEED], seed_from_population_id
    )
    assert ok, note

    stranger = founder_id(ARM_ORDER[0], SEED + 1, 0)
    bad, why = check_seed_derivation([stranger], [SEED], seed_from_population_id)
    assert not bad
    assert str(SEED + 1) in why


def test_i04_aborts_the_run_when_an_id_carries_the_wrong_seed(monkeypatch) -> None:
    """The wiring, not just the predicate (§2.4).

    Measured: deleting the gate from run_population_phase0 broke nothing —
    every other test builds well-formed ids, which is exactly the condition
    under which a missing gate is invisible.
    """

    import dau.diagnostics.run_population_experiment as pop_mod

    monkeypatch.setattr(graph_mod, "agent_node", _stub_agent)
    monkeypatch.setattr(
        pop_mod,
        "planned_founder_ids",
        lambda seeds, n_agents, arms: [pop_mod.founder_id(arms[0], 1234, 0)],
    )

    with pytest.raises(PreflightAbort, match="I0.4"):
        run_population_experiment(
            seeds=[SEED],
            n_agents=N_AGENTS,
            n_generations=N_GENERATIONS,
            events_budget=EVENTS,
        )


def test_the_positive_control_reaches_the_results_file(monkeypatch) -> None:
    """⭐ D-121's wiring, not just its function (§2.4).

    This is the third time in this session that a fix existed in the codebase
    and not on the run path (D-116's main() call, D-117's recorder, D-118's
    gate). The unit tests in test_reproduction.py call the partition directly
    and would all pass with the runner never calling it.
    """

    monkeypatch.setattr(graph_mod, "agent_node", _stub_agent)
    results = run_population_experiment(
        seeds=[SEED],
        n_agents=N_AGENTS,
        n_generations=N_GENERATIONS,
        events_budget=EVENTS,
    )

    from dau.generation.reproduction import CONTROL_KEY_COVARIANCE

    closed = [
        row
        for arm in results["arms"]
        for row in arm["generations"]
        if row["price_for_previous_transition"] is not None
    ]
    assert closed, "no transition closed — test is blind"
    for row in closed:
        control = row["positive_control_for_previous_transition"]
        assert control is not None, "the control never reached the file"
        assert CONTROL_KEY_COVARIANCE in control


def test_the_price_rows_carry_estimability(monkeypatch) -> None:
    """A cell whose z could not vary must be readable as such from the file."""

    from dau.foundation.constraints import LANDMARK_EVENT

    # The budget has to reach the landmark or z carries no domains at all and
    # there is no partition to inspect — the same blindness
    # test_price_partition_actually_carries_drift_domains guards against.
    monkeypatch.setattr(graph_mod, "agent_node", _stub_agent)
    results = run_population_experiment(
        seeds=[SEED],
        n_agents=2,
        n_generations=2,
        events_budget=LANDMARK_EVENT + 2,
    )

    from dau.generation.reproduction import PRICE_KEY_ESTIMABLE

    parts = [
        part
        for arm in results["arms"]
        for row in arm["generations"]
        if row["price_for_previous_transition"]
        for part in row["price_for_previous_transition"].values()
    ]
    assert parts, "no partition to check"
    assert all(PRICE_KEY_ESTIMABLE in part for part in parts)


# ---------------------------------------------------------------------------
# D-124 — the slice the endpoint is actually read from
# ---------------------------------------------------------------------------


def test_the_window_stops_where_the_endpoint_is_read() -> None:
    """⭐ Events after the landmark must not enter the window.

    The endpoint is read AT the landmark ordinal, so a summary that swept the
    whole life would describe a different slice than `z` does — which is
    exactly why D-112's whole-life profile could not answer whether a
    pre-threshold endpoint would be estimable.
    """

    from dau.foundation.constraints import LANDMARK_EVENT

    from dau.diagnostics.run_population_experiment import delta_profile

    rows = [
        {"agent_id": "a", "event_counter": LANDMARK_EVENT - 1, "delta_magnitude": 0.20},
        {"agent_id": "a", "event_counter": LANDMARK_EVENT, "delta_magnitude": 0.30},
        # After the landmark: real, recorded, and OUT of the window.
        {"agent_id": "a", "event_counter": LANDMARK_EVENT + 1, "delta_magnitude": 0.99},
    ]
    window = delta_profile("a", rows, NO_CRISIS)["to_landmark"]

    assert window["n_events"] == 2, "an event past the landmark leaked in"
    assert window["max"] == pytest.approx(0.30)
    assert window["window_last_event"] == LANDMARK_EVENT
    # And the whole-life profile still sees all three — the two answer
    # different questions and must not collapse into each other.
    assert delta_profile("a", rows, NO_CRISIS)["n_events"] == 3


def test_the_window_is_inclusive_of_the_landmark_ordinal() -> None:
    """Boundary, pinned from the other side (§2.4).

    `_landmark_reading` takes the row AT LANDMARK_EVENT, so a window that
    stopped one event earlier would silently describe a slice the endpoint
    does not come from. Measured: with `<` instead of `<=`, every other test
    in this group still passed.
    """

    from dau.foundation.constraints import LANDMARK_EVENT

    from dau.diagnostics.run_population_experiment import delta_profile

    only_at_landmark = [
        {"agent_id": "a", "event_counter": LANDMARK_EVENT, "delta_magnitude": 0.44}
    ]
    window = delta_profile("a", only_at_landmark, NO_CRISIS)["to_landmark"]

    assert window["n_events"] == 1
    assert window["max"] == pytest.approx(0.44)


def test_a_life_that_never_reached_the_landmark_says_so() -> None:
    """§2.9: a truncated window must not look like a complete one.

    Averaged beside a full window it would compare different slices of life
    while reporting the same field names.
    """

    from dau.foundation.constraints import LANDMARK_EVENT

    from dau.diagnostics.run_population_experiment import delta_profile

    short = [
        {"agent_id": "a", "event_counter": 1, "delta_magnitude": 0.5},
        {"agent_id": "a", "event_counter": 2, "delta_magnitude": 0.6},
    ]
    full = [
        {"agent_id": "a", "event_counter": LANDMARK_EVENT, "delta_magnitude": 0.6}
    ]

    assert delta_profile("a", short, NO_CRISIS)["to_landmark"]["window_complete"] is False
    assert delta_profile("a", full, NO_CRISIS)["to_landmark"]["window_complete"] is True


def test_the_window_keeps_the_two_channels_apart_too() -> None:
    """D-117's separation applies inside the window as well.

    Pooled here, a famine before the landmark would again be indistinguishable
    from the agent's own surprise — the reading error D-115 diagnosed, just on
    a narrower slice.
    """

    from dau.foundation.constraints import LANDMARK_EVENT

    from dau.diagnostics.run_population_experiment import delta_profile

    pe = [{"agent_id": "a", "event_counter": 3, "delta_magnitude": 0.25}]
    pool = [
        {"agent_id": "a", "event_counter": 4, "crisis": True, "crisis_magnitude": 1.0},
        # Past the window: must not be counted.
        {
            "agent_id": "a",
            "event_counter": LANDMARK_EVENT + 5,
            "crisis": True,
            "crisis_magnitude": 1.0,
        },
    ]
    window = delta_profile("a", pe, pool)["to_landmark"]

    assert window["max"] == pytest.approx(0.25), "crisis leaked into the individual channel"
    assert window["crisis"]["n_crisis_events"] == 1, "a crisis past the window leaked in"


def test_the_window_reaches_the_results_file(monkeypatch) -> None:
    """The wiring, not the function (§2.4).

    Fourth time this session that the gap was 'the fix exists in the codebase
    and not on the run path', so the call-site test is written first now.
    """

    from dau.foundation.constraints import LANDMARK_EVENT

    monkeypatch.setattr(graph_mod, "agent_node", _stub_agent)
    results = run_population_experiment(
        seeds=[SEED],
        n_agents=2,
        n_generations=2,
        events_budget=LANDMARK_EVENT + 2,
    )

    profiles = [
        agent["delta_profile"]
        for arm in results["arms"]
        for row in arm["generations"]
        for agent in row["agents"]
    ]
    assert profiles, "no agents to check"
    for profile in profiles:
        assert "to_landmark" in profile
        assert profile["to_landmark"]["window_last_event"] == LANDMARK_EVENT
        # The window can never see more events than the whole life did.
        assert profile["to_landmark"]["n_events"] <= profile["n_events"]


# ---------------------------------------------------------------------------
# D-136 — the endpoint's dimension, recovered as pure reporting
# ---------------------------------------------------------------------------

# Two agents whose axes moved differently, so an aggregation that forgot to
# filter reports numbers neither agent produced (K2). "a" is energy-dominant
# like the real universe; "b" is the counterfactual the run has never seen.
AXIS_ROWS_TWO_AGENTS: list[dict[str, Any]] = [
    {
        "agent_id": "a",
        "event_counter": 1,
        "delta_magnitude": 0.2,
        "affected_domain": "energy",
        "axis_deltas": {
            "energy": 0.40, "resource": 0.10, "social": 0.00, "uncertainty": 0.02
        },
    },
    {
        "agent_id": "a",
        "event_counter": 2,
        "delta_magnitude": 0.3,
        "affected_domain": "resource",
        "axis_deltas": {
            "energy": 0.20, "resource": 0.60, "social": 0.05, "uncertainty": 0.04
        },
    },
    {
        "agent_id": "b",
        "event_counter": 1,
        "delta_magnitude": 0.9,
        "affected_domain": "social",
        "axis_deltas": {
            "energy": 0.01, "resource": 0.02, "social": 0.99, "uncertainty": 0.03
        },
    },
]


def test_axis_profile_keeps_the_losing_axes_and_counts_who_won() -> None:
    """⭐ The debt itself: `z` is one-dimensional and the file could not say so.

    PROVENANCE_AUDIT §9 measured `social` and `uncertainty` at zero appearances
    across 216 lives — but that is a statement about the TAG, and the tag is an
    argmax. Whether those axes are dead or merely outvoted is a different
    question, and answering it decides whether the third pre-registration can
    use more than one dimension of the endpoint.
    """

    from dau.diagnostics.run_population_experiment import delta_profile

    axes = delta_profile("a", AXIS_ROWS_TWO_AGENTS, NO_CRISIS)["axes"]

    assert axes["n_events"] == 2, "another agent's events leaked into the axes"
    assert axes["wins"] == {
        "energy": 1, "resource": 1, "social": 0, "uncertainty": 0
    }
    # ⭐ The point of the whole item: an axis that won NOTHING still reports how
    # far it moved. Under the old code this number did not exist.
    assert axes["deltas"]["social"]["n_events"] == 2
    assert axes["deltas"]["social"]["max"] == pytest.approx(0.05)
    assert axes["deltas"]["energy"]["mean"] == pytest.approx(0.30)


def test_axis_profile_does_not_pool_two_agents(monkeypatch) -> None:
    """K2 — the aggregation runs over agents, so its test needs two of them.

    Measured: with the agent filter deleted, "a" reports a social peak of 0.99
    that belongs to "b", and every single-agent assertion in this file still
    passes. That is the shape of the two collapse bugs D-127 found.
    """

    from dau.diagnostics.run_population_experiment import delta_profile

    a_axes = delta_profile("a", AXIS_ROWS_TWO_AGENTS, NO_CRISIS)["axes"]
    b_axes = delta_profile("b", AXIS_ROWS_TWO_AGENTS, NO_CRISIS)["axes"]

    assert a_axes["deltas"]["social"]["max"] == pytest.approx(0.05)
    assert b_axes["deltas"]["social"]["max"] == pytest.approx(0.99)
    assert b_axes["wins"]["social"] == 1
    assert a_axes["wins"]["social"] == 0


def test_axis_profile_reads_the_recorded_tag_instead_of_recomputing_it() -> None:
    """⭐ §2.8 — the reporter must follow the universe, not imitate it.

    A reporter that ran its own argmax would agree with `update_drift` today
    and go on agreeing after the universe changed how it tags — the silent
    divergence this project has paid for four times. The only way to pin that
    is a row where the two disagree, which production cannot produce and a
    fixture can.
    """

    from dau.diagnostics.run_population_experiment import delta_profile

    disagreeing = [
        {
            "agent_id": "a",
            "event_counter": 1,
            "delta_magnitude": 0.5,
            # Not the argmax of its own deltas — on purpose.
            "affected_domain": "uncertainty",
            "axis_deltas": {
                "energy": 0.90, "resource": 0.10, "social": 0.0, "uncertainty": 0.05
            },
        }
    ]

    axes = delta_profile("a", disagreeing, NO_CRISIS)["axes"]

    assert axes["wins"]["uncertainty"] == 1, "the reporter re-derived the tag"
    assert axes["wins"]["energy"] == 0


def test_axis_profile_skips_uninstrumented_rows_rather_than_calling_them_zero() -> None:
    """"Not recorded" is not "did not move" — the distinction D-121 drew for `z`.

    Rows written before this field existed carry no axis block. Counting them
    as four zeros would report a universe where nothing ever moved, which is
    the most alarming possible reading and a false one.
    """

    from dau.diagnostics.run_population_experiment import delta_profile

    legacy = [{"agent_id": "a", "event_counter": 1, "delta_magnitude": 0.68}]
    profile = delta_profile("a", legacy, NO_CRISIS)

    # The magnitude channel still reports the event — only the axis block abstains.
    assert profile["n_events"] == 1
    assert profile["axes"]["n_events"] == 0
    assert profile["axes"]["deltas"]["energy"]["max"] is None
    assert profile["axes"]["deltas"]["energy"]["mean"] is None
    assert profile["axes"]["wins"] == {
        "energy": 0, "resource": 0, "social": 0, "uncertainty": 0
    }


def test_axis_profile_in_the_window_stops_where_the_endpoint_is_read() -> None:
    """`z` is read AT the landmark, so the axes that could write it end there.

    A whole-life axis report placed under `to_landmark` would describe swings
    that happened after the endpoint was already frozen — D-124's confound,
    reintroduced through a new field.
    """

    from dau.foundation.constraints import LANDMARK_EVENT

    from dau.diagnostics.run_population_experiment import delta_profile

    rows = [
        {
            "agent_id": "a",
            "event_counter": LANDMARK_EVENT,
            "delta_magnitude": 0.2,
            "affected_domain": "energy",
            "axis_deltas": {
                "energy": 0.3, "resource": 0.1, "social": 0.02, "uncertainty": 0.01
            },
        },
        {
            "agent_id": "a",
            "event_counter": LANDMARK_EVENT + 1,
            "delta_magnitude": 0.9,
            "affected_domain": "social",
            "axis_deltas": {
                "energy": 0.1, "resource": 0.1, "social": 0.95, "uncertainty": 0.01
            },
        },
    ]
    profile = delta_profile("a", rows, NO_CRISIS)

    assert profile["axes"]["n_events"] == 2, "the whole-life block lost an event"
    assert profile["axes"]["wins"]["social"] == 1
    window = profile["to_landmark"]["axes"]
    assert window["n_events"] == 1, "the window ran past the landmark"
    assert window["wins"]["social"] == 0
    assert window["deltas"]["social"]["max"] == pytest.approx(0.02)


def test_the_axis_report_reaches_the_results_file(monkeypatch) -> None:
    """K3 — the field is worthless if the run path never writes it out.

    End to end through the real runner: only `agent_node` is stubbed, so the
    PE path, the profile and the serialisation are the production ones.
    """

    monkeypatch.setattr(graph_mod, "agent_node", _stub_agent)
    results = run_population_experiment(
        seeds=[SEED], n_agents=2, n_generations=2, events_budget=EVENTS
    )

    agents = results["arms"][0]["generations"][0]["agents"]
    assert agents, "no agents at all"
    for agent in agents:
        for block in (agent["delta_profile"]["axes"],
                      agent["delta_profile"]["to_landmark"]["axes"]):
            assert set(block["deltas"]) == {
                "energy", "resource", "social", "uncertainty"
            }
            assert set(block["wins"]) == set(block["deltas"])
        # A live run must have produced instrumented rows, or the block is a
        # well-formed shell reporting nothing (the failure K3 exists for).
        assert agent["delta_profile"]["axes"]["n_events"] > 0


# ---------------------------------------------------------------------------
# D-138 — `k` (queue 0.2b) and π (queue 0.3), both pure reporting
# ---------------------------------------------------------------------------


def test_primary_axis_counts_show_a_never_targeted_axis_as_a_zero() -> None:
    """⭐ D-137's trigger: "`k` becomes variable" must be readable as a number.

    A missing key would read as "no data"; an explicit 0 reads as "measured,
    never happened". Those call for opposite decisions about reopening GAP-10.
    """

    from dau.diagnostics.run_population_experiment import delta_profile

    rows = [
        {
            "agent_id": "a", "event_counter": 1, "delta_magnitude": 0.2,
            "affected_domain": "energy", "target_domain": "resource_load",
            "axis_deltas": {
                "energy": 0.4, "resource": 0.1, "social": 0.02, "uncertainty": 0.01
            },
        },
        {
            "agent_id": "a", "event_counter": 2, "delta_magnitude": 0.3,
            "affected_domain": "energy", "target_domain": "social_load",
            "axis_deltas": {
                "energy": 0.5, "resource": 0.1, "social": 0.30, "uncertainty": 0.01
            },
        },
    ]
    primary = delta_profile("a", rows, NO_CRISIS)["axes"]["primary_axis"]

    assert primary["resource_load"] == 1
    assert primary["social_load"] == 1
    # Never aimed at — present, and zero.
    assert primary["uncertainty_load"] == 0
    # `energy` is not a target axis at all; it must not appear as a phantom 0.
    assert "energy" not in primary


def test_primary_axis_is_not_the_same_field_as_the_argmax_winner() -> None:
    """§2.8 — two questions, two fields; conflating them would hide D-137.

    Every row here was AIMED at resource and every row MOVED energy most. A
    reporter that read one field for both would say `k` varies (it does not)
    or that energy is a target (it cannot be).
    """

    from dau.diagnostics.run_population_experiment import delta_profile

    rows = [
        {
            "agent_id": "a", "event_counter": n, "delta_magnitude": 0.2,
            "affected_domain": "energy", "target_domain": "resource_load",
            "axis_deltas": {
                "energy": 0.9, "resource": 0.1, "social": 0.02, "uncertainty": 0.01
            },
        }
        for n in (1, 2, 3)
    ]
    axes = delta_profile("a", rows, NO_CRISIS)["axes"]

    assert axes["primary_axis"]["resource_load"] == 3
    assert axes["wins"]["energy"] == 3
    assert axes["wins"]["resource"] == 0


def test_primary_axis_skips_rows_that_predate_the_field() -> None:
    """"Not recorded" is not "never targeted" (§2.9)."""

    from dau.diagnostics.run_population_experiment import delta_profile

    legacy = [{"agent_id": "a", "event_counter": 1, "delta_magnitude": 0.5}]
    primary = delta_profile("a", legacy, NO_CRISIS)["axes"]["primary_axis"]

    assert primary == {"resource_load": 0, "social_load": 0, "uncertainty_load": 0}


def test_precision_profile_separates_a_frozen_pi_from_a_moving_one() -> None:
    """⭐ L13 made falsifiable: "Precision-PE is idle" had no number to fail on.

    π is computed every event and written to the PE row, but no result file
    carried it (D-130 §10), so the claim could be neither confirmed nor
    refuted. Two lives that differ in exactly the way L13 is about must now
    look different in the artefact.
    """

    from dau.diagnostics.run_population_experiment import _precision_profile

    frozen = [
        {"agent_id": "a", "prediction_error": 1.0, "precision_weight": 1.0}
        for _ in range(4)
    ]
    moving = [
        {"agent_id": "a", "prediction_error": 0.4, "precision_weight": w}
        for w in (0.5, 0.8, 1.2, 1.6)
    ]

    assert _precision_profile(frozen)["n_distinct"] == 1
    assert _precision_profile(frozen)["min"] == _precision_profile(frozen)["max"]
    assert _precision_profile(moving)["n_distinct"] == 4
    assert _precision_profile(moving)["min"] == pytest.approx(0.5)
    assert _precision_profile(moving)["max"] == pytest.approx(1.6)
    assert _precision_profile(moving)["mean"] == pytest.approx(1.025)


def test_precision_profile_reports_pe_w_saturation_beside_pi() -> None:
    """L13's other half: π can move while every weighted PE still pins at 1.0.

    Reported through the protocol-C audit helper rather than recomputed, so
    the two runners cannot disagree about what "saturated" means (§2.8).
    """

    from dau.diagnostics.run_population_experiment import _precision_profile

    rows = [
        {"agent_id": "a", "prediction_error": 1.0, "precision_weight": 0.5},
        {"agent_id": "a", "prediction_error": 1.0, "precision_weight": 0.9},
        {"agent_id": "a", "prediction_error": 0.3, "precision_weight": 1.4},
        {"agent_id": "a", "prediction_error": 0.2, "precision_weight": 1.8},
    ]
    profile = _precision_profile(rows)

    assert profile["n_distinct"] == 4, "pi looks alive"
    assert profile["n_pe_w_saturated"] == 2
    assert profile["pe_w_saturation_rate"] == pytest.approx(0.5)


def test_precision_profile_of_a_life_with_no_events_is_not_zero() -> None:
    """None, not 0.0 — a mean of 0.0 would be the most alarming possible π."""

    from dau.diagnostics.run_population_experiment import _precision_profile

    empty = _precision_profile([])

    assert empty["n_events"] == 0
    assert empty["min"] is None and empty["max"] is None and empty["mean"] is None
    assert empty["pe_w_saturation_rate"] is None


def test_k_and_precision_reach_the_results_file_per_agent(monkeypatch) -> None:
    """K2 + K3 — two agents, and through the real runner, not the helpers.

    K2 because both blocks aggregate over agents: an unfiltered version reports
    the population while claiming to report one agent, and with one agent in
    the fixture that bug is invisible.
    """

    monkeypatch.setattr(graph_mod, "agent_node", _stub_agent)
    results = run_population_experiment(
        seeds=[SEED], n_agents=2, n_generations=2, events_budget=EVENTS
    )

    agents = results["arms"][0]["generations"][0]["agents"]
    assert len(agents) == 2, "K2 needs two agents in the dimension being summed"
    for agent in agents:
        primary = agent["delta_profile"]["axes"]["primary_axis"]
        assert sum(primary.values()) == agent["delta_profile"]["axes"]["n_events"]
        assert agent["delta_profile"]["axes"]["n_events"] == agent["events_lived"]
        precision = agent["precision"]
        assert precision["n_events"] == agent["events_lived"], "another agent leaked in"
        assert precision["min"] is not None
        assert precision["n_distinct"] >= 1


def test_a_flat_cell_names_nobody_low_and_nobody_high() -> None:
    """⚠ D-152's guard: identical agents have no relative structure.

    Min-max normalisation on a flat cell is 0/0. Inventing a band there would
    manufacture a difference the universe did not make — and flat cells are not
    hypothetical here: D-129 measured a `null` arm whose eight agents were
    identical in every quantity.
    """

    from dau.generation.fitness import classify_fitness_relative, normalize_fitness

    flat = [0.5, 0.5, 0.5, 0.5]

    assert normalize_fitness(0.5, flat) is None, "a flat cell reported a position"
    assert [classify_fitness_relative(v, flat) for v in flat] == ["normal"] * 4


def test_relative_bands_revive_the_two_dead_bands() -> None:
    """⭐⭐ D-152. The change exists for exactly one measured number.

    C2 put 216 of 216 agents in `normal`: the low band got 0 and the high band
    12, so the inherited-warning branch that feeds the somatic channel fired 0
    times in 144 heirs. The SAME spread, read relatively, has to name both
    ends — otherwise the change bought nothing.

    ⚠ K2: this needs a cell with spread, not a single value. With one agent the
    normalisation is degenerate and the test would pass against a stub.
    """

    from dau.generation.fitness import (
        FITNESS_LABEL_HIGH,
        FITNESS_LABEL_LOW,
        classify_fitness,
        classify_fitness_relative,
    )

    # C2's observed span: min 0.3919, max 0.7696 — every one of these is
    # `normal` on the absolute scale.
    cell = [0.3919, 0.45, 0.52, 0.60, 0.6026, 0.68, 0.72, 0.7696]
    absolute = {classify_fitness(v) for v in cell}
    relative = [classify_fitness_relative(v, cell) for v in cell]

    assert absolute == {"normal", "high"}, "the fixture stopped resembling C2"
    assert FITNESS_LABEL_LOW in relative, "the low band is still unreachable"
    assert FITNESS_LABEL_HIGH in relative
    # The extremes are the extremes — min-max puts them at 0.0 and 1.0.
    assert relative[0] == FITNESS_LABEL_LOW
    assert relative[-1] == FITNESS_LABEL_HIGH


def test_the_band_is_not_derived_from_heir_count() -> None:
    """⛔ P4's separation: z must not become a function of w by construction.

    The tempting relative reference is the tournament — an agent that won
    nothing is the population's own definition of unfit. It is forbidden:
    the band gates which memories transfer, so it shapes z, and deriving it
    from w would make Cov(w, z) partly an identity (D-075's tautology).
    So the reference is F_agent, and this pins that the signature offers no
    other one.
    """

    import inspect

    from dau.foundation.generation import select_for_transfer

    params = inspect.signature(select_for_transfer).parameters
    assert "f_agent_reference" in params
    assert not any("w" == name or "heir" in name for name in params), (
        "select_for_transfer gained a heir-count input — that closes the "
        "Price loop on itself"
    )


def test_the_results_name_the_fitness_band_not_only_the_number() -> None:
    """⭐ D-150. The band is what gates the somatic channel, and it was invisible.

    `select_for_transfer` converts a trauma memory into an inherited warning
    only in the LOW band (f < 0.35) or the HIGH one (f >= 0.70). C2 printed
    f_agent for 216 agents and never said that 0 of them were low — the
    threshold sits BELOW the whole observed distribution (min 0.3919), so that
    branch could not fire, and nothing in the results file said so.

    Read through `classify_fitness` rather than compared here, so the report
    cannot drift from the rule that actually decides (§2.8).
    """

    from dau.generation.fitness import (
        FITNESS_HIGH_THRESHOLD,
        FITNESS_LOW_THRESHOLD,
        classify_fitness,
    )

    # K2: three values, one per band — with a single value the mapping could be
    # constant and the test would not see it.
    below = FITNESS_LOW_THRESHOLD / 2
    between = (FITNESS_LOW_THRESHOLD + FITNESS_HIGH_THRESHOLD) / 2
    at_high = FITNESS_HIGH_THRESHOLD

    assert classify_fitness(below) == "low"
    assert classify_fitness(between) == "normal"
    assert classify_fitness(at_high) == "high", "the boundary belongs to high"


def test_the_fitness_band_reaches_the_results_file(monkeypatch) -> None:
    """K3 — the band is worthless if the artefact never carries it."""

    from dau.generation.fitness import classify_fitness

    monkeypatch.setattr(graph_mod, "agent_node", _stub_agent)
    results = run_population_experiment(
        seeds=[SEED], n_agents=2, n_generations=2, events_budget=EVENTS
    )

    agents = results["arms"][0]["generations"][0]["agents"]
    assert agents
    for agent in agents:
        assert "fitness_class" in agent
        assert agent["fitness_class"] == classify_fitness(agent["f_agent"])


def _trauma_candidate(record_id: str):
    """One durable memory whose delta is trauma-class — the branch's other half."""

    from dau.foundation.delta import DELTA_THRESHOLD_DEEP, DeltaRecord
    from dau.foundation.generation import TransferCandidate

    return TransferCandidate(
        record=DeltaRecord(
            timestamp=1,
            # At the boundary, which classify_delta counts as TRAUMA.
            magnitude=DELTA_THRESHOLD_DEEP,
            affected_domain="energy",
            snapshot_before={},
            snapshot_after={},
        ),
        record_id=record_id,
        memory_score=1.0,
        recall_count=1,
    )


def test_transfer_uses_the_relative_band_not_the_absolute_one() -> None:
    """⭐⭐ K3 for D-152 — the classifier is not the change; THIS is.

    Measured: with the classifier correct but `select_for_transfer` still
    reading the absolute band, every test above still passed. The behaviour
    that matters is whether a trauma memory becomes an inherited warning, and
    only this exercises it.

    The agent below is `normal` on the absolute scale (0.3919 sits between
    0.35 and 0.70 — that is C2's actual minimum) and the LOWEST of its cell.
    Absolute: no warning. Relative: warning.
    """

    from dau.foundation.drift import DriftState
    from dau.foundation.generation import select_for_transfer
    from dau.generation.fitness import classify_fitness

    lowest = 0.3919
    cell = [lowest, 0.52, 0.6026, 0.7696]
    assert classify_fitness(lowest) == "normal", "the fixture stopped resembling C2"

    absolute = select_for_transfer(
        [_trauma_candidate("m0")], DriftState(), f_agent=lowest
    )
    relative = select_for_transfer(
        [_trauma_candidate("m0")],
        DriftState(),
        f_agent=lowest,
        f_agent_reference=cell,
    )

    assert not any(c.inherited_warning for c in absolute), (
        "the absolute path started warning — the fixture no longer isolates the change"
    )
    assert any(c.inherited_warning for c in relative), (
        "the relative band did not reach select_for_transfer"
    )


def test_the_highest_of_a_cell_also_earns_a_warning() -> None:
    """Both ends, not one: the high band writes a warning through transfer_kind.

    ⚠ K2 in the band dimension — a change that only revived `low` would pass a
    test that only looked at `low`, and the design writes a rule for each end.
    """

    from dau.foundation.drift import DriftState
    from dau.foundation.generation import (
        TRANSFER_KIND_INHERITED_WARNING,
        select_for_transfer,
    )

    cell = [0.3919, 0.52, 0.6026, 0.7696]
    top = select_for_transfer(
        [_trauma_candidate("m1")],
        DriftState(),
        f_agent=0.7696,
        f_agent_reference=cell,
    )

    assert any(
        c.transfer_kind == TRANSFER_KIND_INHERITED_WARNING or c.inherited_warning
        for c in top
    ), "the high end of the cell earned nothing"
