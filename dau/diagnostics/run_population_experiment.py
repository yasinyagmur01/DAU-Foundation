"""Population experiment wrapper — N agents, G generations, one pasture per arm.

E2-4b. A NEW wrapper rather than a change to ``run_cprime_multigen``, decided by
Yasin on 2026-08-17: that runner is built around gen1 → transfer → gen2 with
three arms sharing one skeleton, and the population scheme does not fit inside
it — P1 gives every arm its OWN population and its OWN pasture, and P6 drops the
second phase entirely. Editing it would mix the path B2 actually ran with a
different experiment and leave no working reference outside the
``prereg/b2-code`` tag.

What this wrapper does, per arm, per generation:

    N initial states → run_population (E2-3) → F_agent per agent (D-071/D-086)
    → z per agent = landmark drift (K5) → plan_next_generation (E4/P2/P3)
    → next generation's states … and one generation later, close_transition
      gives the Price partition for that step (D-101).

⚠ SCOPE — read this before reading the numbers. This step wires the PLUMBING and
the selection term. Two things are deliberately NOT here yet:

  * memory-vault inheritance into heirs (``transfer_to_heir``), and
  * per-arm adapter training.

Without them the three arms are the same experiment run three times and the
transmission term is noise, so **no arm contrast may be read off this runner
yet**. They are E2-4b-2, kept separate because that is where D-033 (adapters
surviving across runs → I0.7) and D-067 (the vault clock) both live, and mixing
them in would make a failure impossible to attribute.

✅ D-081 honoured (fixed after D-102 measured the contradiction): the pasture
scales with N. ``EnvironmentState.capacity`` carries the carrying capacity, so N
agents graze a pasture N times larger and their per-capita trajectory is the N=1
universe's, unchanged. The starting stock comes from the founders' own niche —
they share it under P0-① — multiplied by N, so seed-to-seed variation survives
the scaling instead of being replaced by a flat default.

⚠ Exploratory. Nothing here is pre-registered; the second pre-registration is
still a draft and P7-a (the budget) is still open.
"""

from __future__ import annotations

import argparse
import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import dau.foundation.graph as graph_mod
from dau.diagnostics.run_cprime_multigen import _landmark_reading, mock_llm_enabled
from dau.diagnostics.run_protocol_c_prime import (
    ARM_ORDER,
    _initial_state,
    _lock_seeds,
)
from dau.diagnostics.tool_identity import build_tool_identity, resolve_lora_choice
from dau.foundation.self_model import build_self_model, f_agent_inputs
from dau.foundation.state import DAUAgentState
from dau.generation.population import (
    FIRST_GENERATION,
    GenerationPlan,
    close_transition,
    plan_next_generation,
)
from dau.generation.reproduction import (
    HEIRS_PER_TOURNAMENT_WIN,
    TOURNAMENT_K,
    Candidate,
)
from dau.society.environment import POOL_MAX, EnvironmentState, get_pool_ratio

# ---------------------------------------------------------------------------
# Identifiers and output keys (no magic strings in logic)
# ---------------------------------------------------------------------------

FOUNDER_ID_TEMPLATE: str = "pop-{arm}-s{seed}-a{index}"
FIRST_FOUNDER_INDEX: int = 0
RESULTS_NOTE: str = "exploratory, not pre-registered"
PROTOCOL_NAME: str = "population-experiment"
# The round guard is the event budget itself: should_continue is the authority
# on when a life ends, and this only stops a runaway loop (D-100).
ROUND_GUARD_SLACK: int = 1
# What build_arm_population actually implements, said out loud in the results so
# a reader never has to infer P0 from the code (§2.8).
P0_NICHE_LABEL: str = "shared-per-seed (P0 option 1)"


@dataclass(frozen=True)
class AgentGenerationRow:
    """One agent's one generation: what it was scored on and what it left."""

    agent_id: str
    f_agent: float
    f_agent_inputs: dict[str, float]
    events_lived: int
    landmark: dict[str, Any]


def founder_id(arm: str, seed: int, index: int) -> str:
    """Deterministic id for founder `index` of an arm's population."""

    return FOUNDER_ID_TEMPLATE.format(arm=arm, seed=int(seed), index=int(index))


def build_arm_population(
    arm: str,
    seed: int,
    n_agents: int,
) -> list[DAUAgentState]:
    """The founding generation of one arm — ⚠ THIS FUNCTION ENCODES P0.

    Every founder is born into the SAME niche, drawn from the arm's seed. That
    is P0 option ① (sequential access to a depleting commons): the agents start
    identical and whatever separates them has to come from competition over the
    shared pasture, not from the world handing them different starting points.
    It costs zero new constants, which is why it was the recommendation.

    ⚠ P0 is formally Yasin's decision and is still open (Kuşak 1, item E). It is
    localised here on purpose: choosing ② (a niche per agent), ③ (asymmetric
    birth) or ⑤ (spatial embedding) changes THIS FUNCTION and nothing else.
    Nothing has been measured through it yet, so no result depends on the
    current choice.
    """

    if n_agents < 1:
        raise ValueError(f"n_agents must be >= 1, got {n_agents}")
    return [
        _initial_state(founder_id(arm, seed, index), seed)
        for index in range(FIRST_FOUNDER_INDEX, FIRST_FOUNDER_INDEX + n_agents)
    ]


def shared_pasture(founders: list[DAUAgentState]) -> EnvironmentState:
    """One pasture for the whole arm, scaled to the population (D-081).

    Per-capita stock and capacity stay at the single-agent numbers, so the
    per-capita trajectory of a population of N is the N=1 universe's. The stock
    is taken from the founders' niche rather than from POOL_INIT: under P0-①
    every founder shares one niche, and that niche's pool is seed-dependent —
    replacing it with the module default would quietly delete the seed-to-seed
    variation the run is replicated over.
    """

    if not founders:
        raise ValueError("shared_pasture needs at least one founder")
    per_capita_stock = float(founders[0].env_state.pool)
    n_agents = len(founders)
    return EnvironmentState(
        pool=per_capita_stock * n_agents,
        capacity=POOL_MAX * n_agents,
    )


def score_generation(
    states: dict[str, DAUAgentState],
    events_budget: int,
) -> list[AgentGenerationRow]:
    """F_agent and the landmark reading for every agent of one generation.

    Both go through the existing helpers rather than being recomputed here:
    ``build_self_model`` owns F_agent and ``_landmark_reading`` owns the
    fixed-age read, and a wrapper that rebuilt either would be the reporting
    drift §2.8 has caught four times.
    """

    body_rows = graph_mod.get_body_event_log()
    rows: list[AgentGenerationRow] = []
    for agent_id in sorted(states):
        state = states[agent_id]
        self_model = build_self_model(state, events_budget)
        rows.append(
            AgentGenerationRow(
                agent_id=agent_id,
                f_agent=float(self_model.f_agent),
                f_agent_inputs=f_agent_inputs(state, events_budget),
                events_lived=len(state.event_log),
                landmark=_landmark_reading(body_rows, len(state.event_log), agent_id),
            )
        )
    return rows


def candidates_from_rows(rows: list[AgentGenerationRow]) -> list[Candidate]:
    """Turn scored agents into tournament candidates: F_agent in, z along.

    P4's three layers stay separate here — F_agent is the selection INPUT and
    the landmark drift vector is the OUTCOME that rides along for Price. They
    are carried in one object only because the tournament and the covariance
    read the same population at the same instant.
    """

    return [
        Candidate(
            agent_id=row.agent_id,
            f_agent=row.f_agent,
            z=dict(row.landmark.get("drift_magnitudes", {}) or {}),
        )
        for row in rows
    ]


def _heir_states(
    plan: GenerationPlan,
    parents: dict[str, DAUAgentState],
    seed: int,
) -> list[DAUAgentState]:
    """Birth the planned heirs.

    ⚠ E2-4b-2: these heirs are born from the niche, NOT from their parents'
    vaults. ``transfer_to_heir`` is not called yet, so Channel 1 is silent and
    the transmission term of the Price partition carries no inheritance. The
    pedigree is real; the inheritance is not, and this is the single biggest
    reason the runner's numbers are plumbing evidence and not science yet.
    """

    born: list[DAUAgentState] = []
    for assignment in plan.heirs:
        parent = parents[assignment.parent_id]
        heir = _initial_state(assignment.heir_id, seed)
        born.append(
            heir.model_copy(update={"opponent_id": parent.opponent_id})
        )
    return born


def run_arm(
    arm: str,
    seed: int,
    n_agents: int,
    n_generations: int,
    events_budget: int,
) -> dict[str, Any]:
    """One arm: G generations of N agents on that arm's own pasture (P1)."""

    _lock_seeds(seed)
    rng = random.Random(seed)
    app = graph_mod.build_event_graph()
    states = build_arm_population(arm, seed, n_agents)
    env = shared_pasture(states)

    generations: list[dict[str, Any]] = []
    previous_plan: GenerationPlan | None = None
    previous_parents: dict[str, DAUAgentState] = {}
    # MAX_EVENTS is a module global that should_continue reads. Restoring it is
    # not tidiness: _collect_pe_events restores it too, and a leaked budget was
    # exactly how D-071's survival denominator ended up reading the module
    # default instead of the budget the life actually ran against.
    original_max_events = graph_mod.MAX_EVENTS
    try:
        return _run_arm_generations(
            arm=arm, seed=seed, rng=rng, app=app, env=env, states=states,
            generations=generations, previous_plan=previous_plan,
            previous_parents=previous_parents, n_agents=n_agents,
            n_generations=n_generations, events_budget=events_budget,
        )
    finally:
        graph_mod.MAX_EVENTS = original_max_events


def _run_arm_generations(
    *,
    arm: str,
    seed: int,
    rng: random.Random,
    app: Any,
    env: EnvironmentState,
    states: list[DAUAgentState],
    generations: list[dict[str, Any]],
    previous_plan: GenerationPlan | None,
    previous_parents: dict[str, DAUAgentState],
    n_agents: int,
    n_generations: int,
    events_budget: int,
) -> dict[str, Any]:
    """The generation loop of one arm; run_arm owns the global it borrows."""

    for generation in range(FIRST_GENERATION, FIRST_GENERATION + n_generations):
        graph_mod.reset_pe_event_log()
        graph_mod.reset_pool_event_log()
        graph_mod.reset_body_event_log()
        graph_mod.MAX_EVENTS = int(events_budget)

        outcome = graph_mod.run_population(
            env,
            states,
            app,
            max_rounds=int(events_budget) + ROUND_GUARD_SLACK,
        )
        env = outcome.env_state
        rows = score_generation(outcome.states, events_budget)
        candidates = candidates_from_rows(rows)

        # D-101: the partition for the PREVIOUS transition can only be closed
        # now, because it needs these agents' z. The generation that has just
        # finished gets its own Price row one generation from now, and the last
        # generation never gets one at all.
        price: dict[str, dict[str, float]] | None = None
        if previous_plan is not None:
            price = close_transition(
                previous_plan,
                {row.agent_id: dict(row.landmark.get("drift_magnitudes", {}) or {})
                 for row in rows},
            )

        is_last = generation == FIRST_GENERATION + n_generations - 1
        plan = (
            None
            if is_last
            else plan_next_generation(
                generation + 1, candidates, rng, n_slots=n_agents
            )
        )
        generations.append(
            {
                "generation": generation,
                "n_agents": len(rows),
                "pool_ratio_end": get_pool_ratio(env),
                "hit_round_cap": outcome.hit_round_cap,
                "agents": [
                    {
                        "agent_id": row.agent_id,
                        "f_agent": row.f_agent,
                        "f_agent_inputs": row.f_agent_inputs,
                        "events_lived": row.events_lived,
                        "landmark": row.landmark,
                    }
                    for row in rows
                ],
                "price_for_previous_transition": price,
                "reproduction_report": None if plan is None else plan.report,
                "w_by_parent": None if plan is None else plan.w_by_parent,
                "pedigree": None
                if plan is None
                else [
                    {"heir_id": h.heir_id, "parent_id": h.parent_id}
                    for h in plan.heirs
                ],
            }
        )
        if plan is None:
            break
        previous_parents = dict(outcome.states)
        previous_plan = plan
        states = _heir_states(plan, previous_parents, seed)

    return {"arm": arm, "seed": seed, "generations": generations}


def run_population_experiment(
    seeds: list[int],
    n_agents: int,
    n_generations: int,
    events_budget: int,
) -> dict[str, Any]:
    """Every arm × every seed. Each arm keeps its own population and pasture."""

    if n_generations < 2:
        raise ValueError(
            "n_generations must be >= 2: with one generation there is no "
            "transition and Price is undefined (D-101)"
        )
    # D-094's debt paid here: a run that SELECTS must say which selection rule
    # ran, read from the constants rather than restated (§2.8). `lora_choice` is
    # explicitly OFF because this step trains no adapters at all (E2-4b-2) —
    # letting resolve_lora_choice exit on an unset flag would be right for the
    # pre-registered runner and wrong here, where there is no choice to make yet.
    identity = build_tool_identity(
        lora_choice=resolve_lora_choice(False, mock=mock_llm_enabled()),
        seeds=list(seeds),
        extra={
            "reproduction": {
                "tournament_k": TOURNAMENT_K,
                "heirs_per_tournament_win": HEIRS_PER_TOURNAMENT_WIN,
                "p0_niche": P0_NICHE_LABEL,
                "inheritance_wired": False,
                "adapter_training_wired": False,
                # D-081: per-capita capacity held constant as N grows.
                "pool_capacity_scaled": True,
            }
        },
    )
    return {
        "note": RESULTS_NOTE,
        "protocol": PROTOCOL_NAME,
        "n_agents": n_agents,
        "n_generations": n_generations,
        "events_budget": events_budget,
        "seeds": list(seeds),
        "tool_identity": identity,
        "arms": [
            run_arm(arm, seed, n_agents, n_generations, events_budget)
            for seed in seeds
            for arm in ARM_ORDER
        ],
    }


def build_arg_parser() -> argparse.ArgumentParser:
    """CLI. No defaults for N / G / events: P7-a is undecided (§2.9)."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, nargs="+", required=True)
    parser.add_argument("--n-agents", type=int, required=True)
    parser.add_argument("--n-generations", type=int, required=True)
    parser.add_argument("--events", type=int, required=True)
    parser.add_argument("--results", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_arg_parser().parse_args(argv)
    results = run_population_experiment(
        seeds=list(args.seeds),
        n_agents=int(args.n_agents),
        n_generations=int(args.n_generations),
        events_budget=int(args.events),
    )
    args.results.parent.mkdir(parents=True, exist_ok=True)
    args.results.write_text(json.dumps(results, indent=1), encoding="utf-8")
    print(f"wrote {args.results}")


if __name__ == "__main__":
    main()
