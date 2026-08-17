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

✅ Channel 1 (the memory vault) is wired: each arm keeps one temp vault, every
parent is consolidated at the end of its life and each heir is birthed through
``apply_generation``, so inherited engrams, drift and somatic scales reach the
newborn before it takes its first event.

✅ Channel 2 (the LoRA adapter) is wired too, and one locked decision was
REVERSED to make it mean anything. The single-lineage design said "3A: no parent
LoRA adapter load" — the heir started parametrically blank — which was coherent
while a generation had two phases: the agent trained and then lived again with
its own adapter. P6 removed the second phase, and with 3A still in force the
adapter would be trained at the end of a life and consumed by nobody: Channel 2
would compute and then evaporate, and `lived` / `shuffle` / `null` would differ
only in name.

⇒ Yasin chose (2026-08-17): **the heir inherits its parent's adapter.** The
parent's adapter directory is COPIED to the heir's id at birth, so the heir
starts from its ancestor's weights and then trains on top of its own life. The
copy is not waste — it is the heir's own adapter, and writing into the parent's
directory instead would corrupt the ancestor a later replay still needs.

⚠ This narrows nothing quietly: it changes what D-002's birth-drift endpoint
means (inheritance is no longer symbolic-only), and the second pre-registration
must declare it.

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
import contextlib
import json
import os
import random
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import dau.foundation.graph as graph_mod
from dau.diagnostics.run_cprime_multigen import _landmark_reading, mock_llm_enabled
from dau.diagnostics.run_protocol_c_prime import (
    ARM_NULL,
    ARM_ORDER,
    ARM_SHUFFLE,
    _initial_state,
    _lock_seeds,
)
from dau.diagnostics.run_protocol_c_prime import (  # noqa: E402
    _build_lived_examples,
    _train_adapter,
)
from dau.diagnostics.tool_identity import build_tool_identity, resolve_lora_choice
from dau.foundation.drift import DriftState
from dau.foundation.emotional_weight import MARKER_REWARD, MARKER_THREAT
from dau.foundation.generation import (
    INHERITED_WARNING_KEY,
    SOMATIC_SCALE_KEY,
    GenerationRecord,
    apply_generation,
    consolidate_generation,
)
from dau.foundation.meta_observer import bind_memory_store, unbind_memory_store
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
from dau.memory.store import MemoryStore
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
    reward_marker: float
    threat_marker: float


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
                reward_marker=float(
                    self_model.emotional_weight.somatic_markers.get(MARKER_REWARD, 0.0)
                ),
                threat_marker=float(
                    self_model.emotional_weight.somatic_markers.get(MARKER_THREAT, 0.0)
                ),
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


@dataclass
class ArmVault:
    """The arm's vault plus the set of agents currently bound to it."""

    store: MemoryStore
    bound: set[str]

    def bind(self, agent_ids: list[str]) -> None:
        """Register newborns so their events reach the vault."""

        bind_vault(self.store, agent_ids)
        self.bound.update(agent_ids)


@contextlib.contextmanager
def arm_vault(agent_ids: list[str]):
    """One vault for the whole arm, bound to every agent in it.

    Per ARM rather than per agent: the store is already agent_id-keyed
    (`list_nodes(agent_id)`), so agents inside an arm cannot see each other's
    engrams, while a heir CAN be seeded from its parent's nodes — which is
    exactly what apply_generation does and what a per-agent store would make
    impossible. Arms stay isolated from each other, which is what P1 requires.

    The store is a temp directory, so nothing survives the run: D-033 found
    adapters outliving their runs and I0.7 exists because of it, and a vault
    that persisted would reopen the same hole on the memory side.
    """

    tmp = tempfile.TemporaryDirectory(prefix="dau_population_")
    store = MemoryStore(
        chroma_path=os.path.join(tmp.name, "chroma"),
        sqlite_path=os.path.join(tmp.name, "memory.db"),
    )
    vault = ArmVault(store=store, bound=set())
    try:
        vault.bind(list(agent_ids))
        yield vault
    finally:
        for agent_id in sorted(vault.bound):
            unbind_memory_store(agent_id)
            graph_mod._memory_stores.pop(agent_id, None)
            graph_mod._memory_written.pop(agent_id, None)
        with contextlib.suppress(Exception):
            store.close()
        with contextlib.suppress(Exception):
            tmp.cleanup()


def bind_vault(store: MemoryStore, agent_ids: list[str]) -> None:
    """Register a vault for each agent so their events reach it."""

    for agent_id in agent_ids:
        graph_mod._memory_stores[agent_id] = store
        graph_mod._memory_written[agent_id] = 0
        bind_memory_store(agent_id, store)


def consolidate_parents(
    rows: list[AgentGenerationRow],
    states: dict[str, DAUAgentState],
    store: MemoryStore,
) -> dict[str, GenerationRecord]:
    """End-of-life consolidation for every parent — the inheritance package.

    F_agent is passed in, so the Layer-4 fitness gate that D-088 recalibrated
    is the one that runs here too; the wrapper does not get its own copy of the
    rule.
    """

    return {
        row.agent_id: consolidate_generation(
            states[row.agent_id],
            store,
            f_agent=row.f_agent,
            reward_marker=row.reward_marker,
            threat_marker=row.threat_marker,
        )
        for row in rows
    }


def inherit_adapter(parent_id: str, heir_id: str) -> bool:
    """Copy the parent's adapter to the heir's id — Channel 2 across generations.

    A copy rather than a symlink or a shared directory: the heir trains on top
    of what it inherited, so a shared directory would rewrite the ancestor's
    weights and destroy the only parametric record of a life that already ended
    (and that I4.1 may still want to replay). One directory per agent also keeps
    ``adapter_exists``/``switch_adapter`` honest — they answer about an agent,
    not about a lineage.

    Returns whether anything was inherited. False is normal, not a failure: a
    founder has no parent adapter and an untrained arm never writes one.
    """

    try:
        from dau.foundation.local_llm import adapter_dir, adapter_exists
    except ImportError:  # torch/peft absent — the arm simply stays untrained
        return False
    if not adapter_exists(parent_id):
        return False
    target = adapter_dir(heir_id)
    if target.exists():
        raise ValueError(
            f"{heir_id}: adapter directory already exists — refusing to graft "
            "onto it (D-033 / I0.7: a leftover adapter is how a fresh arm "
            "silently inherits a previous run)"
        )
    shutil.copytree(adapter_dir(parent_id), target)
    return True


def train_generation(
    arm: str,
    rows: list[AgentGenerationRow],
    states: dict[str, DAUAgentState],
) -> dict[str, dict[str, Any]]:
    """Channel 2 for one generation of one arm.

    The arm IS the training rule (P5): ``lived`` trains on the agent's own
    PE-ranked pairs, ``shuffle`` trains on the same pairs with the preference
    direction shuffled, and ``null`` never trains. `_train_adapter` is the same
    function the single-lineage path calls — including its own
    ``DAU_LORA_ENABLED`` guard — so the two runners cannot drift apart on what
    "trained" means (§2.8).
    """

    if arm == ARM_NULL:
        return {}
    pe_rows = graph_mod.get_pe_event_log()
    trained: dict[str, dict[str, Any]] = {}
    for row in rows:
        agent_rows = [r for r in pe_rows if r["agent_id"] == row.agent_id]
        examples = _build_lived_examples(states[row.agent_id], agent_rows)
        outcome = _train_adapter(
            row.agent_id, examples, shuffled=(arm == ARM_SHUFFLE)
        )
        trained[row.agent_id] = {
            "n_pairs_trained": int(outcome.n_pairs_trained),
            "n_pairs_rejected": int(outcome.n_pairs_rejected),
            "lora_b_abs_sum_delta": float(outcome.lora_b_abs_sum_delta),
        }
    return trained


def _heir_states(
    plan: GenerationPlan,
    parents: dict[str, DAUAgentState],
    records: dict[str, GenerationRecord],
    store: MemoryStore,
    seed: int,
    adapter_inherited: dict[str, bool] | None = None,
) -> list[DAUAgentState]:
    """Birth the planned heirs WITH their parent's inheritance (Channel 1).

    Each heir starts from a fresh niche — not the parent's continuing pool —
    and then apply_generation seeds the selected parent engrams under the
    heir's own id and writes the inherited drift and somatic scales. That is
    the same call the single-lineage path makes; a second implementation here
    would be the drift §2.8 keeps catching.

    Ordering matters and is enforced by construction: apply_generation returns
    before this function does, so no heir can be streamed before its
    inheritance has landed.
    """

    born: list[DAUAgentState] = []
    for assignment in plan.heirs:
        parent = parents[assignment.parent_id]
        blank = _initial_state(assignment.heir_id, seed)
        heir = apply_generation(blank, records[assignment.parent_id], store)
        grafted = inherit_adapter(assignment.parent_id, assignment.heir_id)
        if adapter_inherited is not None:
            adapter_inherited[assignment.heir_id] = grafted
        born.append(heir.model_copy(update={"opponent_id": parent.opponent_id}))
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
        with arm_vault([state.agent_id for state in states]) as vault:
            return _run_arm_generations(
                arm=arm, seed=seed, rng=rng, app=app, env=env, states=states,
                vault=vault, generations=generations, previous_plan=previous_plan,
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
    vault: "ArmVault",
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

        # Channel 2 first, then Channel 1. Order matters: training reads the
        # life's PE rows, which reset_pe_event_log clears at the top of the next
        # generation, and consolidation walks the vault, which training never
        # touches. Doing it the other way round would still work today, but the
        # PE rows are the fragile half and they are consumed here.
        trained = train_generation(arm, rows, outcome.states)
        # Channel 1: end-of-life consolidation for every parent, before any
        # heir exists. The record is what the heir inherits; building it after
        # birth would let a newborn's own events into its ancestry.
        records = consolidate_parents(rows, outcome.states, vault.store)
        is_last = generation == FIRST_GENERATION + n_generations - 1
        plan = (
            None
            if is_last
            else plan_next_generation(
                generation + 1, candidates, rng, n_slots=n_agents
            )
        )
        adapter_inherited: dict[str, bool] = {}
        heirs = (
            []
            if plan is None
            else _heir_states(
                plan, outcome.states, records, vault.store, seed, adapter_inherited
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
                        # Whether this agent's events could reach the vault at
                        # all. An unbound heir writes no engrams, so its own
                        # children inherit nothing and the transmission term
                        # goes quietly to zero — invisible without this flag
                        # (measured: the binding could be deleted and every
                        # test still passed).
                        "vault_bound": row.agent_id in vault.bound,
                    }
                    for row in rows
                ],
                "trained": trained,
                "n_inherited_by_parent": {
                    agent_id: len(record.inherited_memories)
                    for agent_id, record in sorted(records.items())
                },
                "price_for_previous_transition": price,
                "reproduction_report": None if plan is None else plan.report,
                "w_by_parent": None if plan is None else plan.w_by_parent,
                "pedigree": None
                if plan is None
                else [
                    {"heir_id": h.heir_id, "parent_id": h.parent_id}
                    for h in plan.heirs
                ],
                # Birth telemetry, the population equivalent of BirthDriftLog.
                # Written because a pedigree alone cannot show whether the
                # inheritance actually landed: skipping apply_generation leaves
                # a heir whose `generation` never advances, and without this
                # block that failure is invisible in the results (measured —
                # the first version of the inheritance test passed with
                # apply_generation deleted).
                "birth": [
                    {
                        "heir_id": heir.agent_id,
                        "generation": int(heir.generation),
                        "n_retrieval_context": len(heir.retrieval_context),
                        "has_inherited_warning": any(
                            isinstance(entry, dict)
                            and entry.get(INHERITED_WARNING_KEY) is True
                            for entry in heir.retrieval_context
                        ),
                        "has_somatic_scale": any(
                            isinstance(entry, dict) and SOMATIC_SCALE_KEY in entry
                            for entry in heir.retrieval_context
                        ),
                        "adapter_inherited": adapter_inherited.get(
                            heir.agent_id, False
                        ),
                        "birth_drift_flags": dict(heir.drift_state.flags)
                        if isinstance(heir.drift_state, DriftState)
                        else {},
                    }
                    for heir in heirs
                ],
            }
        )
        if plan is None:
            break
        previous_parents = dict(outcome.states)
        previous_plan = plan
        states = heirs
        vault.bind([state.agent_id for state in states])

    return {"arm": arm, "seed": seed, "generations": generations}


def run_population_experiment(
    seeds: list[int],
    n_agents: int,
    n_generations: int,
    events_budget: int,
    lora: bool = False,
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
        lora_choice=resolve_lora_choice(bool(lora), mock=mock_llm_enabled()),
        seeds=list(seeds),
        extra={
            "reproduction": {
                "tournament_k": TOURNAMENT_K,
                "heirs_per_tournament_win": HEIRS_PER_TOURNAMENT_WIN,
                "p0_niche": P0_NICHE_LABEL,
                "inheritance_wired": True,
                "adapter_training_wired": True,
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
    # Mirrors the multigen runner: no default, so a forgotten flag can never be
    # mistaken for a deliberately untrained run (D-004 pattern).
    lora = parser.add_mutually_exclusive_group(required=True)
    lora.add_argument("--lora", dest="lora", action="store_true", default=None)
    lora.add_argument("--no-lora", dest="lora", action="store_false", default=None)
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_arg_parser().parse_args(argv)
    results = run_population_experiment(
        seeds=list(args.seeds),
        n_agents=int(args.n_agents),
        n_generations=int(args.n_generations),
        events_budget=int(args.events),
        lora=bool(args.lora),
    )
    args.results.parent.mkdir(parents=True, exist_ok=True)
    args.results.write_text(json.dumps(results, indent=1), encoding="utf-8")
    print(f"wrote {args.results}")


if __name__ == "__main__":
    main()
