"""Population experiment wrapper (E2-4b): plumbing, pedigree, and Price timing."""

from __future__ import annotations

from typing import Any

import pytest

import dau.foundation.graph as graph_mod
from dau.diagnostics.preflight import RUN_QUALITY_CLEAN, PreflightAbort
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
GATED_INVARIANTS: tuple[str, ...] = ("I0.3", "I0.6", "I0.7", "I1.1", "I4.1")


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


def test_mock_llm_flag_installs_the_canned_llm(monkeypatch, tmp_path) -> None:
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
    assert results["run_quality"] == RUN_QUALITY_CLEAN
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
    assert results["run_quality"] == RUN_QUALITY_CLEAN


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
    assert results["run_quality"] == RUN_QUALITY_CLEAN


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
    profile = delta_profile("a", rows)

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
        "a", [{"agent_id": "a", "delta_magnitude": 0.9}]
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

    profile = delta_profile("ghost", [{"agent_id": "a", "delta_magnitude": 0.9}])

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
    profile = delta_profile("a", [{"agent_id": "a", "delta_magnitude": exact}])

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
