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

⛔ G >= 3 IS STRUCTURAL (A3, D-107). Under P0-① the founders are bit-identical,
so generation 1 enters its transition with no variance in z and Cov(w, z) is
zero however the tournament goes. A G=2 run has exactly one transition and it
is that one: it can only report zero. The runner still ACCEPTS G=2 — that is a
legitimate smoke configuration and Price is well defined there — but it says so
on the console and stamps ``generations_informative`` into the results, because
a run that can only report zero must not be read as one that measured zero.

✅ The preflight gates are wired (A1, D-105). Until then this wrapper had ZERO
of them while the multigen runner had nine, and the missing one that mattered
most was I0.7: with the adapter now COPIED from parent to heir, a leftover
directory on disk does not merely contaminate one life, it seeds a lineage.
Phase 0 (I0.3 · I0.6 · I0.7) aborts before any GPU work, I1.1 is read after the
run, and the results carry the invariants block and a `run_quality` stamp.

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
from dau.diagnostics.preflight import (
    MODE_ABORT,
    MODE_FLAG,
    Preflight,
    PreflightAbort,
    arm_digest,
    check_determinism_settings,
    check_no_stale_adapters,
    check_pythonhashseed,
    check_replay_identical,
    check_training_moved_weights,
)
from dau.diagnostics.run_cprime_multigen import (
    MOCK_LLM_ENV,
    _decisions,
    _landmark_reading,
    install_mock_llm,
    mock_llm_enabled,
)
from dau.diagnostics.run_protocol_c_prime import (
    ARM_LIVED,
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
from dau.diagnostics.tool_identity import (
    LORA_CHOICE_ON,
    build_tool_identity,
    resolve_lora_choice,
)
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
# The key _landmark_reading writes z under. Named rather than inlined because
# reading the wrong one is silent: `z` comes back empty, price_partition finds
# no domains and returns {}, and every generation reports a Price row that says
# nothing. That is exactly what happened on the first full-chain run.
LANDMARK_DRIFT_KEY: str = "landmark_drift_magnitudes"
# P0-① as decided (2026-08-17): sequential service in a rotating order. The
# D-103 pilot measured what the simultaneous, proportional version does — eight
# founders came out bit-identical, z had zero variance, and Cov(w, z) was zero
# BY CONSTRUCTION in every arm. These are module constants rather than CLI flags
# because ① is the declared physics of this experiment, not a knob.
SEQUENTIAL_ACCESS: bool = True
ROTATE_ACT_ORDER: bool = True
# The keys check_training_moved_weights (I1.1) reads out of a "section". The
# predicate takes plain dicts, so a misspelt key here is not a type error: for a
# train arm it reads as "weights never read" and fails loudly, but for the null
# arm it reads as "nothing was recorded" and PASSES — the contamination half of
# I1.1 would be silently switched off. Named so the test can hold the wrapper
# and the predicate to the same string (§2.8).
SECTION_ARM_KEY: str = "arm"
SECTION_SEED_KEY: str = "seed"
SECTION_DELTA_KEY: str = "lora_b_abs_sum_delta"
# I4.1 (A2). The replay is an arm in its own right, run under its own label so
# its founders get their own ids: re-using the original ids would make the
# second pass load the adapters the first one just wrote, and phase 1 would run
# adapted where the original ran bare — a divergence that is not
# non-determinism. Same reasoning as the multigen runner's replay_agent_id.
REPLAY_ARM_LABEL: str = "replay"
REPLAY_OF_ARM: str = ARM_LIVED
# ⚠ Depth, and it is DERIVED, not chosen. Founders are born with no adapter, so
# generation 1's decisions come from the base policy: replaying it alone could
# not see the failure I4.1 exists to catch (D-037 — the same seed and code
# producing different ADAPTERS between runs). The first generation whose
# decisions depend on trained weights is generation 2, because that is when the
# heir inherits its parent's adapter. So 2 is the smallest depth that can see
# it, and a deeper replay would only buy more of the same at ~1 arm-generation
# of GPU time each.
REPLAY_GENERATIONS: int = 2
# ⚠ A3 (D-107) — two different floors, and conflating them is the mistake.
#
# DEFINED: with a single generation there is no transition at all, so Price is
# undefined. This one is an error.
#
# INFORMATIVE: under P0-① every founder is born into the same niche, identical
# down to the bit. Generation 1 therefore enters its transition with NO variance
# in z, and Cov(w, z) over a constant z is zero however the tournament goes —
# not "small", not "we failed to detect it", zero BY CONSTRUCTION. Measured in
# D-104: gen1 gave 1 distinct z out of 8 agents while gen2 and gen3 gave 4.
# ⇒ A G=2 run has exactly one transition, and it is the one that can only
# report zero. G >= 3 is therefore a STRUCTURAL requirement of the design, not
# a power or budget preference — and P7-a may not trade it away.
MINIMUM_GENERATIONS_DEFINED: int = 2
MINIMUM_GENERATIONS_INFORMATIVE: int = 3


def planned_founder_ids(
    seeds: list[int],
    n_agents: int,
    arms: tuple[str, ...],
) -> list[str]:
    """Every agent id that exists before the first tournament — I0.7's input.

    Only founders: heir ids are decided by the tournament and cannot be known
    before the run. The heirs are covered at birth instead, by
    ``inherit_adapter`` refusing a directory that is already there.

    The replay arm's founders are in here too, and they are not an afterthought:
    a leftover ``pop-replay-…`` adapter would make the second pass start adapted
    where the first started bare, and I4.1 would report DIVERGED for a reason
    that has nothing to do with determinism.
    """

    return [
        founder_id(arm, seed, index)
        for seed in seeds
        for arm in tuple(arms) + (REPLAY_ARM_LABEL,)
        for index in range(FIRST_FOUNDER_INDEX, FIRST_FOUNDER_INDEX + n_agents)
    ]


def run_population_phase0(gate: Preflight, *, agent_ids: list[str]) -> Preflight:
    """I0.3 · I0.6 · I0.7 before any GPU work — the population runner's phase 0.

    A SUBSET of ``preflight.run_phase0``, and calling the whole thing instead
    would abort every run here: I0.4 derives the seed from the agent id with
    ``AGENT_ID_SEED_PATTERN``, which matches ``cprime-{arm}-{seed}`` and not the
    population's ``pop-{arm}-s{seed}-a{index}`` (nor a heir's ``…-g{n}-h{k}``).
    The predicates themselves are imported rather than re-implemented, so this
    runner and the multigen one cannot drift apart on what a gate means (§2.8).

    ⚠ I0.1/I0.2 are deliberately NOT here — they are a decision, not an
    oversight, and it is written down in D-105.
    """

    gate.check("I0.3", check_pythonhashseed, mode=MODE_ABORT)
    gate.check("I0.6", check_determinism_settings, mode=MODE_ABORT)
    gate.check("I0.7", lambda: check_no_stale_adapters(agent_ids), mode=MODE_ABORT)
    return gate


def training_sections(arms: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """One I1.1 section per agent per generation, across every arm.

    Per AGENT, not per arm: in a population an arm trains N adapters per
    generation and a single silent failure among them is exactly the thing that
    must not average out. The null arm gets rows too, carrying no delta at all —
    that is what lets I1.1's other half fire, the one that catches a train step
    landing on the control's weights.
    """

    sections: list[dict[str, Any]] = []
    for arm_result in arms:
        for generation in arm_result["generations"]:
            trained = generation.get("trained") or {}
            for agent in generation["agents"]:
                outcome = trained.get(agent["agent_id"])
                sections.append(
                    {
                        SECTION_ARM_KEY: arm_result["arm"],
                        SECTION_SEED_KEY: (
                            f"{arm_result['seed']}/g{generation['generation']}/"
                            f"{agent['agent_id']}"
                        ),
                        SECTION_DELTA_KEY: (
                            None
                            if outcome is None
                            else outcome.get(SECTION_DELTA_KEY)
                        ),
                    }
                )
    return sections


def run_population_phase2(
    gate: Preflight,
    *,
    sections: list[dict[str, Any]],
    lora_enabled: bool,
) -> Preflight:
    """I1.1 — read after the run, because only then have the weights moved.

    ABORT, like the multigen runner, and for the same reason: every other
    signal a trained agent emits is produced upstream of the gradient step, so
    a run that reports pair counts and adapter files while Σ|lora_B| never
    moved is the failure this project already shipped once (e4c026b).

    ⚠ There is no diversity gate in this path, so ``gated`` is never set: an
    agent whose life yields no usable preference pair reports an unread delta
    and takes the whole run down with it. That is the strict reading and it is
    deliberate — the alternative, exempting agents by their pair count, is
    exactly the hole the predicate's docstring warns about, because a gated
    agent and a silently failed one report the same zero.
    """

    gate.check(
        "I1.1",
        lambda: check_training_moved_weights(sections, lora_enabled=lora_enabled),
        # A canned LLM has no LoRA layers to read, so the delta is unread by
        # construction; aborting there would only punish smoke runs (D-012).
        mode=MODE_FLAG if gate.mock else MODE_ABORT,
    )
    return gate


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


def generation_digest(states: dict[str, DAUAgentState]) -> str:
    """sha256(decisions ++ PE) for one generation of one arm — I4.1's unit.

    Built through ``preflight.arm_digest`` so the population runner and the
    multigen one hash the same way; what changes is only that a generation has
    N agents instead of one. Agents are concatenated in id order, and that is
    stable across the replay even though the replay runs under a different arm
    label: every id inside one arm shares the prefix ``pop-{arm}-s{seed}``, so
    the ordering is decided by the suffix, which the label does not touch.

    Per GENERATION rather than per arm, because that is what makes a divergence
    readable: a replay that matches generation 1 and differs at generation 2
    says the drift is in the inherited adapter, not in the life.
    """

    pe_rows = graph_mod.get_pe_event_log()
    decisions: list[str] = []
    pe_values: list[float] = []
    for agent_id in sorted(states):
        decisions.extend(_decisions(states[agent_id]))
        pe_values.extend(
            float(row["prediction_error"])
            for row in pe_rows
            if row["agent_id"] == agent_id
        )
    return arm_digest(decisions, pe_values)


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
            z=dict(row.landmark.get(LANDMARK_DRIFT_KEY, {}) or {}),
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

    ⚠ The refusal is checked BEFORE the parent is, and that order is the whole
    point: heir ids cannot be known before the tournament, so I0.7 can only
    clear the founders and this call is the heirs' half of the same gate. If it
    only fired when the parent had an adapter, the null arm — which never
    trains, so its parents never have one — would be the one arm able to inherit
    a previous run's weights off disk, and it is the control.
    """

    try:
        from dau.foundation.local_llm import adapter_dir, adapter_exists
    except ImportError:  # torch/peft absent — the arm simply stays untrained
        return False
    target = adapter_dir(heir_id)
    if adapter_exists(heir_id):
        raise ValueError(
            f"{heir_id}: adapter directory already exists — refusing to graft "
            "onto it (D-033 / I0.7: a leftover adapter is how a fresh arm "
            "silently inherits a previous run)"
        )
    if not adapter_exists(parent_id):
        return False
    # adapter_exists asks for the config file, so the refusal above lets an
    # EMPTY leftover directory through — and there are many: 79 of the 114 under
    # dau_runs/adapters were created by a query that used to mkdir what it was
    # asked about. An empty directory carries no weights and switch_adapter
    # never loads from it, so it is not contamination; it would only make
    # copytree raise FileExistsError three hours into a run.
    shutil.copytree(adapter_dir(parent_id), target, dirs_exist_ok=True)
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
    pasture_carryover: bool,
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
                pasture_carryover=pasture_carryover, founders=states,
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
    pasture_carryover: bool,
    founders: list[DAUAgentState],
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
            sequential=SEQUENTIAL_ACCESS,
            rotate=ROTATE_ACT_ORDER,
        )
        env = outcome.env_state
        rows = score_generation(outcome.states, events_budget)
        # Read before training and birth, so the digest describes the life this
        # generation lived rather than what was done with it afterwards.
        # ⚠ Hygiene, not a guard: measured — moving this read below the training
        # and birth calls changes no digest today, because neither writes to the
        # PE log or to a parent's event log. It is placed here so that stays
        # true by construction rather than by accident.
        digest = generation_digest(outcome.states)
        candidates = candidates_from_rows(rows)

        # D-101: the partition for the PREVIOUS transition can only be closed
        # now, because it needs these agents' z. The generation that has just
        # finished gets its own Price row one generation from now, and the last
        # generation never gets one at all.
        price: dict[str, dict[str, float]] | None = None
        if previous_plan is not None:
            price = close_transition(
                previous_plan,
                {
                    row.agent_id: dict(row.landmark.get(LANDMARK_DRIFT_KEY, {}) or {})
                    for row in rows
                },
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
                "arm_digest": digest,
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
        # Whether the next generation inherits the pasture its parents left, or
        # is born into a fresh one. 1A chose fresh for the single-lineage design
        # so that the arm contrast could not be contaminated by the environment
        # each arm had made; the population case is an open decision and is
        # carried explicitly rather than settled by whichever the loop happened
        # to do (D-103 found it was carrying over, undeclared).
        if not pasture_carryover:
            env = shared_pasture(founders)

    return {"arm": arm, "seed": seed, "generations": generations}


def chain_digest(digests: list[str]) -> str:
    """One string for a sequence of generation digests, order included.

    check_replay_identical compares two strings, so the sequence has to become
    one. Chained through the same primitive rather than joined by hand: a
    reordering must change the result, and ``arm_digest`` already guarantees
    that (it separates its inputs with a null byte).
    """

    return arm_digest(digests, [])


def run_replay_arm(
    *,
    seed: int,
    n_agents: int,
    events_budget: int,
    pasture_carryover: bool,
    recorded: list[str],
    skip: bool,
) -> dict[str, Any] | None:
    """I4.1 (A2) — run the lived arm a second time and compare the digests.

    Runs LAST, after every arm of the experiment has finished, so nothing
    downstream can consume the adapters this pass writes.

    Costs one arm of ``REPLAY_GENERATIONS`` generations. That is the whole
    price of being able to SAY the run is deterministic: within a single pass
    each agent is trained exactly once, so there is nothing to compare it
    against, and every other gate stayed green through D-037 while the same
    seed and code were producing different adapters between runs.

    ⚠ Only the first ``REPLAY_GENERATIONS`` generations of the recorded arm are
    compared, because that is all the replay runs. It is a prefix, not a
    sample: the generations run in sequence, so generation 3 cannot change what
    generation 2 did.
    """

    if skip or not recorded:
        return None
    print(
        f"[POPULATION][I4.1] replaying seed={seed} arm={REPLAY_OF_ARM} "
        f"as {REPLAY_ARM_LABEL} for {REPLAY_GENERATIONS} generation(s) …",
        flush=True,
    )
    replayed = run_arm(
        REPLAY_ARM_LABEL,
        seed,
        n_agents,
        REPLAY_GENERATIONS,
        events_budget,
        pasture_carryover=pasture_carryover,
    )
    replay_digests = [row["arm_digest"] for row in replayed["generations"]]
    recorded_digests = recorded[: len(replay_digests)]
    replay = {
        "seed": seed,
        "arm": REPLAY_OF_ARM,
        "arm_label": REPLAY_ARM_LABEL,
        "n_generations": REPLAY_GENERATIONS,
        "recorded_digest": chain_digest(recorded_digests),
        "replay_digest": chain_digest(replay_digests),
        # Kept alongside the chain so a divergence names the generation it
        # started in — the chain alone only says "somewhere".
        "recorded_per_generation": recorded_digests,
        "replay_per_generation": replay_digests,
        # The whole second pass, kept rather than summarised: it is a trained
        # arm, so I1.1 has to see it, and a reader comparing two digests will
        # want the run behind the second one.
        "arm_result": replayed,
    }
    verdict = (
        "identical"
        if replay["recorded_digest"] == replay["replay_digest"]
        else "DIVERGED"
    )
    print(f"[POPULATION][I4.1] {verdict}", flush=True)
    return replay


def recorded_digests_for(
    arm_results: list[dict[str, Any]],
    *,
    seed: int,
    arm: str,
) -> list[str]:
    """The per-generation digests of one arm of one seed, in order."""

    for result in arm_results:
        if result["arm"] == arm and int(result["seed"]) == int(seed):
            return [row["arm_digest"] for row in result["generations"]]
    return []


def run_population_experiment(
    seeds: list[int],
    n_agents: int,
    n_generations: int,
    events_budget: int,
    lora: bool = False,
    pasture_carryover: bool = False,
    arms: tuple[str, ...] = ARM_ORDER,
    preflight: Preflight | None = None,
) -> dict[str, Any]:
    """Every arm × every seed. Each arm keeps its own population and pasture.

    ``preflight`` collects the invariant verdicts; phase 0 runs here and aborts
    before any GPU work, and the block it renders is written into the results.
    """

    if n_generations < MINIMUM_GENERATIONS_DEFINED:
        raise ValueError(
            f"n_generations must be >= {MINIMUM_GENERATIONS_DEFINED}: with one "
            "generation there is no transition and Price is undefined (D-101)"
        )
    if n_generations < MINIMUM_GENERATIONS_INFORMATIVE:
        # Not an error: G=2 is well defined and is what a smoke run wants. It
        # is announced because a run that can only report zero must not be read
        # as a run that measured zero (§2.9 — the state that cannot be
        # determined makes noise instead of passing quietly).
        print(
            f"[POPULATION][WARN] n_generations={n_generations} < "
            f"{MINIMUM_GENERATIONS_INFORMATIVE}: under P0-① the founders are "
            "identical, so the first transition has no variance in z and its "
            "selection term is zero BY CONSTRUCTION (D-104). This run can "
            "produce no non-zero selection term at all — smoke only, never a "
            "result (A3/D-107).",
            flush=True,
        )
    use_mock = mock_llm_enabled()
    # Resolved before anything runs: it is what sets DAU_LORA_ENABLED, and the
    # three gate layers downstream read that env var at call time.
    lora_choice = resolve_lora_choice(bool(lora), mock=use_mock)
    gate = preflight if preflight is not None else Preflight(mock=use_mock)
    gate.mock = use_mock
    # Lock before checking I0.6: the check reports the determinism state the run
    # will have, it does not create it. run_arm locks again per arm; this first
    # lock exists so phase 0 is not judging the state some earlier import left.
    _lock_seeds(seeds[0])
    run_population_phase0(
        gate,
        agent_ids=planned_founder_ids(list(seeds), n_agents, tuple(arms)),
    )
    gate.enforce()

    # D-094's debt paid here: a run that SELECTS must say which selection rule
    # ran, read from the constants rather than restated (§2.8).
    identity = build_tool_identity(
        lora_choice=lora_choice,
        seeds=list(seeds),
        extra={
            "reproduction": {
                "tournament_k": TOURNAMENT_K,
                "heirs_per_tournament_win": HEIRS_PER_TOURNAMENT_WIN,
                "p0_niche": P0_NICHE_LABEL,
                "sequential_access": SEQUENTIAL_ACCESS,
                "rotate_act_order": ROTATE_ACT_ORDER,
                "pasture_carryover": pasture_carryover,
                "inheritance_wired": True,
                "adapter_training_wired": True,
                # D-081: per-capita capacity held constant as N grows.
                "pool_capacity_scaled": True,
            }
        },
    )
    arm_results = [
        run_arm(
            arm, seed, n_agents, n_generations, events_budget,
            pasture_carryover=pasture_carryover,
        )
        for seed in seeds
        for arm in arms
    ]
    replay = run_replay_arm(
        seed=seeds[0],
        n_agents=n_agents,
        events_budget=events_budget,
        pasture_carryover=pasture_carryover,
        recorded=recorded_digests_for(arm_results, seed=seeds[0], arm=REPLAY_OF_ARM),
        # A canned LLM replays trivially — the check would assert nothing and
        # the arm would still cost its GPU time.
        skip=use_mock,
    )
    # Phase 2 can only be judged now — the weights move during the run. It is
    # still ABORT, so a run whose training silently did nothing writes no JSON.
    # The replay arm's agents are included: it is a real trained arm, and a
    # train step that silently did nothing there would make the digests match
    # for the wrong reason.
    run_population_phase2(
        gate,
        sections=training_sections(
            arm_results + ([replay["arm_result"]] if replay else [])
        ),
        lora_enabled=(lora_choice == LORA_CHOICE_ON),
    )
    gate.check(
        "I4.1",
        lambda: check_replay_identical(replay),
        mode=MODE_FLAG if use_mock else MODE_ABORT,
    )
    gate.enforce()
    return {
        "note": RESULTS_NOTE,
        "protocol": PROTOCOL_NAME,
        "n_agents": n_agents,
        "n_generations": n_generations,
        # A3/D-107. In the file, not only on the console: a reader who opens
        # this JSON a month from now has no terminal scrollback, and "the first
        # transition's selection term is zero by construction" is exactly the
        # kind of thing that gets read as a finding.
        "generations_informative": n_generations >= MINIMUM_GENERATIONS_INFORMATIVE,
        "events_budget": events_budget,
        "seeds": list(seeds),
        "tool_identity": identity,
        **gate.block(),
        "replay": replay,
        "arms": arm_results,
    }


def build_arg_parser() -> argparse.ArgumentParser:
    """CLI. No defaults for N / G / events: P7-a is undecided (§2.9)."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, nargs="+", required=True)
    parser.add_argument("--n-agents", type=int, required=True)
    parser.add_argument("--n-generations", type=int, required=True)
    parser.add_argument("--events", type=int, required=True)
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--arms", nargs="+", default=list(ARM_ORDER))
    pasture = parser.add_mutually_exclusive_group(required=True)
    pasture.add_argument(
        "--pasture-carryover", dest="carryover", action="store_true", default=None
    )
    pasture.add_argument(
        "--fresh-pasture", dest="carryover", action="store_false", default=None
    )
    parser.add_argument(
        "--mock-llm",
        action="store_true",
        help="Deterministic canned LLM (no GPU). Must be INSTALLED, not just "
        "flagged: reading the env var alone left the real model loading, which "
        "is how the first full-chain smoke run silently became a real run.",
    )
    # Mirrors the multigen runner: no default, so a forgotten flag can never be
    # mistaken for a deliberately untrained run (D-004 pattern).
    lora = parser.add_mutually_exclusive_group(required=True)
    lora.add_argument("--lora", dest="lora", action="store_true", default=None)
    lora.add_argument("--no-lora", dest="lora", action="store_false", default=None)
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_arg_parser().parse_args(argv)
    if args.mock_llm:
        os.environ[MOCK_LLM_ENV] = "1"
        install_mock_llm()
    try:
        results = run_population_experiment(
            seeds=list(args.seeds),
            n_agents=int(args.n_agents),
            n_generations=int(args.n_generations),
            events_budget=int(args.events),
            lora=bool(args.lora),
            pasture_carryover=bool(args.carryover),
            arms=tuple(args.arms),
        )
    except PreflightAbort as abort:
        # An expected refusal, not a crash: print the named invariants rather
        # than a traceback, and write NO results file (preflight.py's contract —
        # a silent fake result has to be impossible, not merely labelled).
        raise SystemExit(str(abort)) from None
    args.results.parent.mkdir(parents=True, exist_ok=True)
    args.results.write_text(json.dumps(results, indent=1), encoding="utf-8")
    print(f"wrote {args.results}")
    print(f"run_quality={results['run_quality']}", flush=True)


if __name__ == "__main__":
    main()
