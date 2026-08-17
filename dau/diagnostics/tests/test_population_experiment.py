"""Population experiment wrapper (E2-4b): plumbing, pedigree, and Price timing."""

from __future__ import annotations

from typing import Any

import pytest

import dau.foundation.graph as graph_mod
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
    (tmp_path / "heir-z").mkdir()

    with pytest.raises(ValueError, match="already exists"):
        inherit_adapter("parent-z", "heir-z")


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
