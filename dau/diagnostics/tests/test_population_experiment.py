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
from dau.foundation.lod import NPC_ACTION_EXTRACT_MODERATE
from dau.foundation.state import DAUAgentState

SEED: int = 9301
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
