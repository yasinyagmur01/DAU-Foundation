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
import re
import shutil
import statistics
import tempfile
from dataclasses import dataclass, field
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
    check_ppr_active,
    check_pythonhashseed,
    check_replay_identical,
    check_seed_derivation,
    check_somatic_scale_applied,
    check_training_moved_weights,
    rng_state_digest,
)
from dau.diagnostics.run_cprime_multigen import (
    MOCK_LLM_ENV,
    _count_edges,
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
    _precision_audit_from_pe_rows,
    _train_adapter,
)
from dau.diagnostics.tool_identity import (
    LORA_CHOICE_ON,
    build_tool_identity,
    resolve_lora_choice,
)
from dau.foundation.local_llm import apply_cuda_allocator_config
from dau.foundation.delta import DELTA_THRESHOLD_DEEP, DOMAIN_ATTR
from dau.foundation.drift import DriftState
from dau.foundation.constraints import LANDMARK_EVENT, TRAIN_SKIP_NO_PAIRS
from dau.foundation.emotional_weight import MARKER_REWARD, MARKER_THREAT
from dau.generation.fitness import classify_fitness_relative
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
    PRICE_KEY_ESTIMABLE,
    PRICE_KEY_Z_VARIANCE,
    TOURNAMENT_K,
    Candidate,
    positive_control_partition,
)
from dau.memory.store import MemoryStore
from dau.society.environment import POOL_MAX, EnvironmentState, get_pool_ratio

# ---------------------------------------------------------------------------
# Identifiers and output keys (no magic strings in logic)
# ---------------------------------------------------------------------------

FOUNDER_ID_TEMPLATE: str = "pop-{arm}-s{seed}-a{index}"
# The inverse of FOUNDER_ID_TEMPLATE, and the reason I0.4 can finally be wired
# here (D-105 left it as a debt). The seed sits MID-STRING in a population id
# and every heir suffix is appended after it, so a pattern anchored at the end
# — which is what Protocol C′ uses — matches nothing here. Anchored on the
# founder segment instead, so it reads the same seed off a founder and off a
# third-generation heir.
POPULATION_ID_SEED_PATTERN: re.Pattern[str] = re.compile(
    r"-s(?P<seed>\d+)-a\d+"
)
FIRST_FOUNDER_INDEX: int = 0
# D-127. This said "exploratory, not pre-registered" unconditionally, and on
# the C2 run that sentence was FALSE — the run was bound by
# docs/PREREGISTRATION_2.md. The runner cannot know whether a pre-registration
# binds it (that fact lives in a document and a commit, not in argv), so it now
# states what it actually knows instead of asserting a status it cannot check.
RESULTS_NOTE: str = (
    "pre-registration status is NOT determined by this runner — check "
    "docs/PREREGISTRATION*.md and the commit this run was launched from"
)
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
# D-121. The positive control declared before the run: time-integrated energy
# over the life. Named here so the choice is visible in one place and cannot be
# quietly swapped for whichever quantity happens to move (§2.7).
CONTROL_TRAIT_KEY: str = "energy_mean_over_life"
# D-136. The two keys the PE row carries the endpoint's dimension under. Named
# here because reading the wrong one is silent in exactly the way
# LANDMARK_DRIFT_KEY is: the block comes back empty and the axis report says
# "nothing moved" about a universe where three axes moved and lost.
PE_ROW_AFFECTED_DOMAIN_KEY: str = "affected_domain"
PE_ROW_AXIS_DELTAS_KEY: str = "axis_deltas"
# D-137's reopening trigger lives on this key: the spillover decision rests on
# `k` being constant, and until now `k` was measurable only on a stub run.
PE_ROW_TARGET_DOMAIN_KEY: str = "target_domain"
# The four axes, taken from the universe's own domain table rather than
# retyped: a literal list here would keep reporting four axes after a fifth was
# added to InternalState, and the endpoint would lose a dimension in silence —
# which is the exact failure D-136 is about.
AXIS_ORDER: tuple[str, ...] = tuple(DOMAIN_ATTR)
# The axes a shock can be AIMED at. A different tuple from AXIS_ORDER on
# purpose: `energy` is an axis the state can move on but never one the update
# targets, and flattening the two would report an impossible zero as if it
# were an observation. Taken from graph rather than retyped (§2.8).
TARGET_AXIS_ORDER: tuple[str, ...] = tuple(graph_mod.DAERM_LOAD_DOMAINS)
# P0-① as decided (2026-08-17): sequential service in a rotating order. The
# D-103 pilot measured what the simultaneous, proportional version does — eight
# founders came out bit-identical, z had zero variance, and Cov(w, z) was zero
# BY CONSTRUCTION in every arm. These are module constants rather than CLI flags
# because ① is the declared physics of this experiment, not a knob.
SEQUENTIAL_ACCESS: bool = True
ROTATE_ACT_ORDER: bool = True
# D-111 checkpointing. The suffix hangs off the RESULTS name rather than
# replacing its extension, so the partial file sorts next to the thing it
# belongs to and can never collide with a real result name.
CHECKPOINT_SUFFIX: str = ".partial.json"
CHECKPOINT_TMP_SUFFIX: str = ".tmp"
RESULTS_COMPLETE_KEY: str = "complete"
CHECKPOINT_NOTE: str = (
    "INCOMPLETE — written while the run was still going. The preflight gates "
    "have NOT run, so this file carries no run_quality and is NOT a result. "
    "It exists so that a crashed or refused run leaves its measurements "
    "behind for diagnosis (D-111)."
)
# The keys check_training_moved_weights (I1.1) reads out of a "section". The
# predicate takes plain dicts, so a misspelt key here is not a type error: for a
# train arm it reads as "weights never read" and fails loudly, but for the null
# arm it reads as "nothing was recorded" and PASSES — the contamination half of
# I1.1 would be silently switched off. Named so the test can hold the wrapper
# and the predicate to the same string (§2.8).
SECTION_ARM_KEY: str = "arm"
SECTION_SEED_KEY: str = "seed"
SECTION_DELTA_KEY: str = "lora_b_abs_sum_delta"
# `gated` is the predicate's own word for "deliberately not trained, so do not
# hold it against the run". The multigen path sets it from the diversity gate;
# the population path had no equivalent, which is what took the first B1
# attempt down (D-108).
SECTION_GATED_KEY: str = "gated"
SECTION_REASON_KEY: str = "reason"
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
    skip_cells: frozenset[tuple[str, int]] = frozenset(),
) -> list[str]:
    """Every agent id that exists before the first tournament — I0.7's input.

    Only founders: heir ids are decided by the tournament and cannot be known
    before the run. The heirs are covered at birth instead, by
    ``inherit_adapter`` refusing a directory that is already there.

    The replay arm's founders are in here too, and they are not an afterthought:
    a leftover ``pop-replay-…`` adapter would make the second pass start adapted
    where the first started bare, and I4.1 would report DIVERGED for a reason
    that has nothing to do with determinism.

    ⚠ ``skip_cells`` is the ONE exemption, and it exists for resume (D-176/B2):
    an (arm, seed) that a previous invocation finished has adapters on disk on
    purpose, and I0.7 would read its own work as contamination. Nothing else is
    exempt — in particular the replay arm never is, because a run interrupted
    DURING the replay leaves ``pop-replay-…`` adapters that would make the
    second pass start adapted. That case must abort loudly and be cleaned by
    hand rather than be deleted by a runner that decided it knew better.
    """

    return [
        founder_id(arm, seed, index)
        for seed in seeds
        for arm in tuple(arms) + (REPLAY_ARM_LABEL,)
        if (arm, int(seed)) not in skip_cells
        for index in range(FIRST_FOUNDER_INDEX, FIRST_FOUNDER_INDEX + n_agents)
    ]


def seed_from_population_id(agent_id: str) -> int:
    """Read the seed out of a population agent id — founder or heir.

    No fallback (§2.9): an id this cannot read is an id whose seed-derived
    draws are undefined, and returning a default would hide that behind a run
    that looks healthy. Heir suffixes are appended, never inserted, so the
    same segment answers for every generation.
    """

    match = POPULATION_ID_SEED_PATTERN.search(str(agent_id))
    if match is None:
        raise ValueError(
            f"agent_id {agent_id!r} carries no seed segment — expected "
            f"{FOUNDER_ID_TEMPLATE} or an heir of one"
        )
    return int(match.group("seed"))


def _control_trait(landmark: dict[str, Any]) -> float | None:
    """The pre-declared positive-control value for one agent, or None.

    None rather than 0.0 when the landmark was never reached: an agent with no
    reading must not enter the control as a value it never had (§2.9), and
    ``positive_control_partition`` drops the whole cell rather than average
    around it.
    """

    value = landmark.get(CONTROL_TRAIT_KEY)
    return None if value is None else float(value)


def run_population_phase0(
    gate: Preflight, *, agent_ids: list[str], seeds: list[int]
) -> Preflight:
    """I0.3 · I0.4 · I0.6 · I0.7 before any GPU work — this runner's phase 0.

    A SUBSET of ``preflight.run_phase0``, and the predicates themselves are
    imported rather than re-implemented, so this runner and the multigen one
    cannot drift apart on what a gate means (§2.8).

    ⚠ I0.1/I0.2 are deliberately NOT here — they are a decision, not an
    oversight, and it is written down in D-105.

    ✅ I0.4 is here now (D-118). D-105 could not wire it because the shared
    check hard-coded Protocol C′'s end-anchored seed pattern, which matches
    nothing in ``pop-{arm}-s{seed}-a{index}``; the check now takes the parser
    the caller's ids are built for. What it guards is not cosmetic: the
    shuffle arm draws its permutation from the seed parsed out of the id, so
    an id the parser cannot read costs the run its replay guarantee — GAP-11
    was exactly that failure, and here it would seed a whole lineage.
    """

    gate.check("I0.3", check_pythonhashseed, mode=MODE_ABORT)
    gate.check(
        "I0.4",
        lambda: check_seed_derivation(agent_ids, seeds, seed_from_population_id),
        mode=MODE_ABORT,
    )
    gate.check("I0.6", check_determinism_settings, mode=MODE_ABORT)
    gate.check("I0.7", lambda: check_no_stale_adapters(agent_ids), mode=MODE_ABORT)
    return gate


SHORTFALL_KEY_ROWS: str = "n_rows"
SHORTFALL_KEY_SHORT: str = "n_short"
SHORTFALL_KEY_FIRST_EVENT: str = "first_event"
SHORTFALL_KEY_MAX: str = "max_shortfall"
SHORTFALL_EPSILON: float = 1e-9


def harvest_shortfall_summary(pool_rows: list[dict[str, Any]]) -> dict[str, Any]:
    """How often the commons gave less than was asked, this generation (D-163).

    Reads the ledger the physics already writes — both `requested` and
    `extraction` are on every pool row — rather than recomputing the ceiling
    beside it, so the summary cannot end up describing a rule the run no longer
    uses (§2.8).

    `first_event` is None when nothing was ever short: that is a real state
    (the ceiling never bit) and must not be reported as event 0.
    """

    n_short = 0
    first_event: int | None = None
    largest = 0.0
    for row in pool_rows:
        gap = float(row.get("requested", 0.0)) - float(row.get("extraction", 0.0))
        if gap <= SHORTFALL_EPSILON:
            continue
        n_short += 1
        largest = max(largest, gap)
        event = int(row.get("event_counter", 0))
        if first_event is None or event < first_event:
            first_event = event
    return {
        SHORTFALL_KEY_ROWS: len(pool_rows),
        SHORTFALL_KEY_SHORT: n_short,
        SHORTFALL_KEY_FIRST_EVENT: first_event,
        SHORTFALL_KEY_MAX: largest,
    }


DEMAND_KEY_ROWS: str = "n_rows"
DEMAND_KEY_MEAN: str = "requested_mean"
DEMAND_KEY_MEDIAN: str = "requested_median"
DEMAND_KEY_P90: str = "requested_p90"
DEMAND_KEY_MAX: str = "requested_max"
DEMAND_KEY_OUTCOMES: str = "outcomes"
DEMAND_P90_QUANTILE: float = 0.90
# D-170. Missing rather than zero: an arm whose vault could not be read is not
# an arm with an empty graph, and I5.1 exists precisely to tell those apart.
UNREADABLE_EDGES: int = -1
# ⛔ D-178/B4 — a DECLARED BOUNDARY of this universe, not an oversight.
#
# `run_consolidation` (sleep consolidation: the association graph, Ebbinghaus
# pruning, strengthening) has no caller on the population path — measured in
# D-172, chain read to the end. It is left that way deliberately:
#
#   * Channel 1 is NOT dead. `consolidate_generation` IS called here, and the
#     pilot measured I5.4 "applied 463x" — the symbolic record reaches the
#     heir. What is missing is a WITHIN-LIFE memory dynamic.
#   * That dynamic is absent SYMMETRICALLY in every arm, so it cannot move the
#     lived/shuffle/null contrast, which is the endpoint this run exists for.
#   * Wiring it would change the physics a fourth time and cost a re-measured
#     baseline, for something the comparison does not read.
#
# ⚠ Kept as a constant rather than a comment so the boundary is READ by the
# gate (§2.8) instead of restated next to it, and so wiring consolidation
# forces this line to be revisited. `test_the_declared_boundary_matches_the
# _code` fails if the module ever reaches run_consolidation while this is False.
SLEEP_CONSOLIDATION_WIRED: bool = False
# What I5.1 says instead of "PPR is inert" while the boundary stands. The
# distinction is D-121's and B3 just re-earned it: None means NOT EVALUATED.
# Reporting False would be a statement about the wiring dressed as a statement
# about the system — the exact confusion D-170 wired this gate to end.
SLEEP_CONSOLIDATION_BOUNDARY: str = (
    "not evaluated: sleep consolidation is not wired on the population path "
    "(D-178/B4, declared boundary) — the association graph is empty BY "
    "CONSTRUCTION, so this gate would describe the wiring, not the system"
)


def demand_summary(
    pool_rows: list[dict[str, Any]], max_event: int | None = None
) -> dict[str, Any]:
    """What the agents ASKED for this generation, and which decision asked it.

    D-166, and it exists because D-165 could not be decided without it. The
    harvest ceiling is proportional to per-capita stock while demand is not, so
    whether the ceiling can ever bind before the landmark is a question about
    the DEMAND level — and the run could only bound it as an interval
    ([4.438, 6.578] against a threshold of 6.078 that sits inside it), because
    the ledger kept only realized harvest.

    Reads `requested` and `outcome` off the rows the physics already wrote
    rather than re-deriving either from the decision text (§2.8): a second
    mapping here is exactly how the reporting/measuring pairs drifted apart.

    The mean is the number the ceiling arithmetic needs; the median and p90 are
    kept because `decision_to_extraction` parses quantities out of free text up
    to EXTRACTION_PARSE_MAX, so the distribution is wide and a mean alone
    cannot say whether a shortfall came from a thinning pasture or from one
    agent announcing twenty units.

    ``max_event`` narrows the rows to an agent-clock window. The whole-life
    mean is not the number the ceiling question needs: whether the ceiling can
    bind BEFORE the landmark depends on the demand during those events, and a
    life whose demand drifts as its energy falls would be read wrong by a
    30-event average. Same reason `delta_profile` keeps a `to_landmark` window
    beside the full one (D-124).
    """

    if max_event is not None:
        pool_rows = [
            row for row in pool_rows if int(row.get("event_counter", 0)) <= max_event
        ]
    requested = [float(row.get("requested", 0.0)) for row in pool_rows]
    outcomes: dict[str, int] = {}
    for row in pool_rows:
        label = str(row.get("outcome", ""))
        outcomes[label] = outcomes.get(label, 0) + 1
    if not requested:
        return {
            DEMAND_KEY_ROWS: 0,
            DEMAND_KEY_MEAN: None,
            DEMAND_KEY_MEDIAN: None,
            DEMAND_KEY_P90: None,
            DEMAND_KEY_MAX: None,
            DEMAND_KEY_OUTCOMES: outcomes,
        }
    ordered = sorted(requested)
    return {
        DEMAND_KEY_ROWS: len(requested),
        DEMAND_KEY_MEAN: statistics.fmean(requested),
        DEMAND_KEY_MEDIAN: statistics.median(requested),
        DEMAND_KEY_P90: ordered[
            min(len(ordered) - 1, int(DEMAND_P90_QUANTILE * len(ordered)))
        ],
        DEMAND_KEY_MAX: max(requested),
        DEMAND_KEY_OUTCOMES: outcomes,
    }


def check_harvest_ceiling_binds(arms: list[dict[str, Any]]) -> tuple[bool, str]:
    """I5.6 — the ceiling produced a short-fall in every generation (D-163).

    Layer 1 exists for exactly one thing: a gradient for sequential access to
    differentiate on. If no agent was ever served less than it asked, the
    ceiling never bit and the layer did nothing — and without this gate the run
    would look identical to one where it worked, because `pool_ratio_end` reads
    the same whether the pasture is full from restraint or from abundance.

    That failure mode is not hypothetical here: the layer it replaces produced
    EXACTLY ZERO short-fall through event 16 while every summary in the results
    file looked healthy (D-162 §1). A measured defect with no gate is what K6
    was written for.
    """

    silent: list[str] = []
    late: list[str] = []
    seen = 0
    for arm in arms:
        for row in arm.get("generations", []) or []:
            summary = row.get("harvest_shortfall")
            if not summary:
                continue
            seen += 1
            label = f"s{arm.get('seed')} {arm.get('arm')} gen{row.get('generation')}"
            if int(summary.get(SHORTFALL_KEY_SHORT, 0)) <= 0:
                silent.append(label)
                continue
            first = summary.get(SHORTFALL_KEY_FIRST_EVENT)
            if first is not None and int(first) >= LANDMARK_EVENT:
                late.append(f"{label} first={first}")
    if not seen:
        return False, "no generation reported a harvest short-fall summary"
    if silent:
        return False, "ceiling never bound in: " + "; ".join(silent)
    if late:
        # Not the same failure: the ceiling worked, but it opened after the
        # window the primary endpoint is read in, so the gradient cannot be in
        # the landmark measurement. Reported separately so the two are never
        # confused in a post-mortem.
        return False, (
            f"short-fall opened at or after LANDMARK_EVENT={LANDMARK_EVENT} in: "
            + "; ".join(late)
        )
    return True, f"{seen} generations, all short before event {LANDMARK_EVENT}"


def check_selection_estimable_where_claimed(
    arms: list[dict[str, Any]],
) -> tuple[bool, str]:
    """I5.5 — the transitions the design counts on carry a measurable term.

    D-155/D-157 measured the hole this closes: across 4 seeds and 3 arms, 11 of
    11 FOUNDER transitions had ``Var(z) = 0`` — the selection term is zero by
    construction there, because founders are born identical and the only source
    of differentiation is the adapter, which does not exist until generation 1
    has ended. C2 reported such a run as ``clean``. A number that is zero by
    construction and a number that is zero because selection did nothing look
    identical in the results file, and nothing said which was which (K6).

    The check is deliberately two-sided, because the design's scope rule
    (YENİ-4 / D-156) can fail in both directions:

    * a transition with a gen ≥ 2 parent that has NO estimable domain — the
      part of the run the pre-registration actually reads is dead;
    * a FOUNDER transition that IS estimable — then the founder generation was
      not degenerate after all, YENİ-4 is discarding usable data, and D-157's
      re-open trigger has fired.

    ⛔ ``F_agent`` spread is reported beside the verdict, never as part of it.
    Measured in C2: two of three seeds had a non-zero founder spread (0.0079,
    0.0101) while every founder ``Var(z)`` was still exactly 0. ANDing the two
    would have missed 6 of those 9 cells — the gate would have been green on
    precisely the runs that motivated it.

    ⚠ Reads ``selection_estimable`` as the Price partition wrote it. Deriving
    estimability again here would let the gate agree with a rule the
    experiment no longer uses (§2.8).
    """

    dead: list[str] = []
    unexpected: list[str] = []
    founder: list[str] = []
    seen = 0
    for arm in arms:
        rows = arm.get("generations", []) or []
        spread_by_generation = {
            int(row.get("generation", 0)): (row.get("reproduction_report") or {}).get(
                "f_agent_spread"
            )
            for row in rows
        }
        for row in rows:
            price = row.get("price_for_previous_transition")
            if price is None:
                continue
            child = int(row.get("generation", 0))
            parent = child - 1
            if parent < FIRST_GENERATION:
                continue
            seen += 1
            estimable = [
                domain
                for domain, terms in price.items()
                if bool(terms.get(PRICE_KEY_ESTIMABLE))
            ]
            spread = spread_by_generation.get(parent)
            label = (
                f"s{arm.get('seed')} {arm.get('arm')} gen{parent}->gen{child}"
                f" (f_agent_spread={spread})"
            )
            if parent == FIRST_GENERATION:
                founder.append(label + (f" estimable={estimable}" if estimable else ""))
                if estimable:
                    unexpected.append(label)
                continue
            if not estimable:
                widest = max(
                    (float(t.get(PRICE_KEY_Z_VARIANCE, 0.0)) for t in price.values()),
                    default=0.0,
                )
                dead.append(f"{label} max_z_variance={widest:g}")

    if not seen:
        return False, "no Price transitions were recorded"
    if unexpected:
        return False, (
            "FOUNDER transition is estimable — YENİ-4 discards usable data: "
            + "; ".join(unexpected)
        )
    if dead:
        return False, "no estimable domain in: " + "; ".join(dead)
    return True, (
        f"{seen} transitions; {len(founder)} founder (out of scope by YENİ-4), "
        f"{seen - len(founder)} scored and estimable"
    )


def check_generation_rng_uniform(arms: list[dict[str, Any]]) -> tuple[bool, str]:
    """I4.2 on the population path — one RNG state per (seed, generation).

    ``preflight.check_gen2_rng_uniform`` asks the same question of the multigen
    runner, whose unit is a lineage's gen2 section. Here the unit is a
    generation of an arm, so the shape differs and the predicate is written
    against this shape rather than the other one bent to fit — a wrapper that
    reshaped the data would be the reporting/measuring drift §2.8 keeps
    catching. The QUESTION is identical: within one seed, did every arm enter
    the same generation from the same global RNG state (GAP-12)?

    Generation 1 is excluded on purpose: every arm is re-locked immediately
    before it, so agreement there is guaranteed by construction and would
    dilute the check. What matters is 2 and later, because that is where
    training has happened for `lived`/`shuffle` and not for `null`.
    """

    by_cell: dict[tuple[Any, int], dict[str, str]] = {}
    for arm in arms:
        for row in arm.get("generation_rng_digests", []):
            generation = int(row.get("generation", 0))
            if generation <= FIRST_GENERATION:
                continue
            digest = str(row.get("rng_digest", ""))
            if not digest:
                return False, f"{row.get('arm')} gen{generation} has no rng_digest"
            by_cell.setdefault((row.get("seed"), generation), {})[
                str(row.get("arm"))
            ] = digest
    if not by_cell:
        return False, "no generation-2+ RNG digests were recorded"
    split = [
        f"s{seed} gen{generation}: {len(set(digests.values()))} states"
        for (seed, generation), digests in sorted(by_cell.items())
        if len(set(digests.values())) > 1
    ]
    if split:
        return False, "arms entered a generation from different RNG states: " + "; ".join(split)
    return True, f"{len(by_cell)} (seed, generation) cells, one RNG state each"


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
                reason = "" if outcome is None else str(outcome.get(SECTION_REASON_KEY, ""))
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
                        # ⚠ D-108. Exempt on the REASON, never on the count.
                        # Four of _train_adapter's five early exits also report
                        # zero pairs — an import failure, a pair builder that
                        # raised, a train step that raised — and exempting by
                        # count would wave all of them through. Only the
                        # trainer's own "the pair set was empty" is a fact
                        # about the LIFE rather than about the instrument, and
                        # a life can legitimately be too quiet to yield a pair.
                        # Aborting on that would put a selection effect on
                        # which runs are allowed to report at all: runs where
                        # every agent lived richly pass, runs with a quiet
                        # agent are never written.
                        SECTION_GATED_KEY: reason == TRAIN_SKIP_NO_PAIRS,
                        SECTION_REASON_KEY: reason,
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


@dataclass
class Checkpoint:
    """Partial results on disk, rewritten as each generation finishes (D-111).

    Written because this runner produces NOTHING until the very end, and that
    cost two runs in one night: one was going to be refused by I1.1 after 75
    minutes of GPU (D-108) and one died to a power cut at minute six. The main
    run is planned at twenty hours; losing it to either would be unrecoverable.

    ⚠ A checkpoint is NOT a result, and the file says so in three ways at once:
    its ``note`` states it is incomplete, ``complete`` is false, and it carries
    NO ``run_quality`` and no invariants block — because the gates have not run
    yet and a stamp copied from nowhere is exactly the silent fake result the
    whole preflight system exists to prevent. The analyzer refuses it.

    ⭐ Side effect worth naming: an ABORTED run now leaves its data behind. The
    gates still refuse to write a *result*, which is D-105's contract, but the
    measurements survive for diagnosis instead of evaporating.
    """

    path: Path
    header: dict[str, Any]
    completed: list[dict[str, Any]] = field(default_factory=list)

    def write(self, in_progress: dict[str, Any] | None = None) -> None:
        """Rewrite the file: everything finished, plus the arm mid-flight.

        Written to a temporary file and renamed, because ``rename`` is atomic
        on POSIX: a crash during the write leaves the PREVIOUS checkpoint
        intact rather than a half-written file that parses as truncated data.
        """

        payload = {
            **self.header,
            "note": CHECKPOINT_NOTE,
            RESULTS_COMPLETE_KEY: False,
            "arms": list(self.completed)
            + ([in_progress] if in_progress is not None else []),
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_name(self.path.name + CHECKPOINT_TMP_SUFFIX)
        tmp.write_text(json.dumps(payload, indent=1), encoding="utf-8")
        tmp.replace(self.path)

    def arm_finished(self, arm_result: dict[str, Any]) -> None:
        self.completed.append(arm_result)
        self.write()

    def discard(self) -> None:
        """Remove the checkpoint once a real result has been written.

        A stale partial file sitting next to a complete one is a trap: the two
        differ only by a flag, and the partial is the older, gate-less half.
        """

        with contextlib.suppress(FileNotFoundError):
            self.path.unlink()


def checkpoint_path_for(results: Path) -> Path:
    """Where the partial file for a given results path lives."""

    return results.with_name(results.name + CHECKPOINT_SUFFIX)


def _resume_fingerprint(header: dict[str, Any]) -> dict[str, Any]:
    """The part of a header that decides whether two runs are the same run.

    Two fields are removed, and NOT because they are inconvenient:

    * ``tool_identity.lora.adapter`` is a census of the adapter directory, and
      the run itself writes into that directory — so it differs from its own
      checkpoint by construction. Comparing it would refuse every resume.
    * ``tool_identity.argv`` differs by exactly the ``--resume`` token that
      asked for the resume.

    Everything else is compared verbatim: model, quantization, DPO settings,
    metabolism, fitness, endpoints, sampling, reproduction rule, versions,
    seeds, generations, events. A checkpoint may only be resumed by a run that
    would have produced it.
    """

    fingerprint = json.loads(json.dumps(header))
    identity = fingerprint.get("tool_identity")
    if isinstance(identity, dict):
        identity.pop("argv", None)
        lora = identity.get("lora")
        if isinstance(lora, dict):
            lora.pop("adapter", None)
    return fingerprint


def completed_arms_from_checkpoint(
    path: Path | None,
    header: dict[str, Any],
    n_generations: int,
) -> list[dict[str, Any]]:
    """Arms a previous invocation FINISHED, ready to be skipped (D-176/B2).

    D-111 gave this runner a checkpoint and it has been write-only ever since:
    every generation was saved and nothing could ever read one back, so an
    interrupted run started over. At the planned 70 hours that is the
    difference between losing a night and losing the budget.

    ⛔ Nothing here is best-effort. A checkpoint that does not match the run
    asking for it raises instead of being ignored (§2.9): silently starting
    from zero would turn "resume" into a word that sometimes means nothing,
    and the operator would find out after the second night, not the first.

    ⚠ Only FINISHED arms come back. The file also holds the arm that was
    mid-flight when the crash happened, and that one is re-run from its first
    generation — it is identified structurally, by not having the generation
    count and the RNG ledger a finished arm has, rather than by its position
    in the list.
    """

    if path is None or not path.exists():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get(RESULTS_COMPLETE_KEY) is not False:
        raise ValueError(
            f"{path} is not a checkpoint: {RESULTS_COMPLETE_KEY} is "
            f"{payload.get(RESULTS_COMPLETE_KEY)!r}, not False. A finished "
            "result must not be resumed into — rename it or point --results "
            "somewhere else."
        )
    theirs = _resume_fingerprint(
        {key: payload.get(key) for key in header}
    )
    ours = _resume_fingerprint(header)
    if theirs != ours:
        differing = sorted(k for k in ours if theirs.get(k) != ours.get(k))
        raise ValueError(
            f"{path} was written by a different run and cannot be resumed: "
            f"{differing} differ. Nothing was deleted — move the checkpoint "
            "aside if the old measurements are wanted."
        )
    finished = [
        arm
        for arm in payload.get("arms", [])
        if len(arm.get("generations", [])) == n_generations
        and arm.get("generation_rng_digests")
    ]
    return finished


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
    # D-112. What the endpoint's own trigger condition saw during this life.
    delta_profile: dict[str, Any] = field(default_factory=dict)
    # D-138 / L13. Kept beside delta_profile rather than inside it: π weights
    # the PE that FEEDS the magnitude, so folding it into a magnitude profile
    # would read as if it were another channel of the same quantity.
    precision: dict[str, Any] = field(default_factory=dict)


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


def _magnitude_summary(magnitudes: list[float]) -> dict[str, Any]:
    """max / mean / crossings / headroom for one channel's magnitudes."""

    if not magnitudes:
        return {
            "n_events": 0,
            "max": None,
            "mean": None,
            "n_at_or_above_trauma": 0,
            "headroom_to_trauma": None,
        }
    peak = max(magnitudes)
    return {
        "n_events": len(magnitudes),
        "max": peak,
        "mean": sum(magnitudes) / len(magnitudes),
        "n_at_or_above_trauma": sum(
            1 for m in magnitudes if m >= DELTA_THRESHOLD_DEEP
        ),
        # How far the closest call fell short. Negative means it crossed.
        # Reported rather than inferred from `max` so the reader never has to
        # remember what the threshold is.
        "headroom_to_trauma": DELTA_THRESHOLD_DEEP - peak,
    }


def _primary_axis_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    """How often each axis was the one the shock was AIMED at — D-137's `k`.

    ⚠ Not the same question as ``wins``. ``wins`` counts where the state ended
    up moving most; this counts where the update was pointed. They come apart
    because `k` gets the full PE and every other axis gets a fixed fraction of
    it, so `k` decides the SHAPE of the perturbation while the argmax only
    reports its outcome — and the entire GAP-10 decision (D-137) rests on `k`
    being constant.

    Every known target axis is present even at zero, so "this axis was never
    aimed at" is visible as a number rather than as a missing key. An
    unexpected value is counted under its own name instead of dropped: if the
    universe ever starts aiming somewhere new, that must show up here, not
    disappear into a filter (§2.9).

    Rows without the key are skipped — they predate the field, and "not
    recorded" is not "never targeted".
    """

    counts: dict[str, int] = {axis: 0 for axis in TARGET_AXIS_ORDER}
    for row in rows:
        target = row.get(PE_ROW_TARGET_DOMAIN_KEY)
        if target is None:
            continue
        key = str(target)
        counts[key] = counts.get(key, 0) + 1
    return counts


def _precision_profile(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """π's spread over one life — L13's "Precision-PE is idle", made falsifiable.

    ⚠ The claim has been carried since L13 and could be neither confirmed nor
    refuted from any result file: `precision_weight` is computed per event and
    written to the PE row, but the population run's agent row had no precision
    field at all (D-130 §10), so the quantity left no trace in the artefact.
    A claim that cannot fail is not a finding.

    The saturation/distinct counts come from ``_precision_audit_from_pe_rows``
    — the same helper the protocol-C runner audits with — rather than from a
    second implementation here. Two functions answering "is π moving" in two
    places is how the reporting/measuring pairs in §2.8 drifted apart four
    times. Only min/max/mean are derived here, off the π list that helper
    returns.

    ⛔ Reporting only, and read as estimability, never as effect (L9): whether
    π varies at all is a different question from whether it varies BY ARM.
    """

    saturation_rate, n_distinct, pi_values, n_events, n_saturated = (
        _precision_audit_from_pe_rows(rows)
    )
    if not rows:
        return {
            "n_events": 0,
            "n_distinct": 0,
            "min": None,
            "max": None,
            "mean": None,
            "pe_w_saturation_rate": None,
            "n_pe_w_saturated": 0,
        }
    return {
        "n_events": int(n_events),
        "n_distinct": int(n_distinct),
        "min": min(pi_values),
        "max": max(pi_values),
        "mean": sum(pi_values) / len(pi_values),
        # PE_w saturation rides along because it is the other half of L13: π
        # can look alive while every weighted PE still pins at the ceiling.
        "pe_w_saturation_rate": float(saturation_rate),
        "n_pe_w_saturated": int(n_saturated),
    }


def _axis_profile(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Per-axis swing sizes beside the axis that won the tag — D-136.

    ⚠ Why this is not ``_magnitude_summary``: these two quantities are graded
    against different gates and mixing them would report a threshold that does
    not apply. ``delta_magnitude`` decides WHETHER a scar is written
    (``is_trauma``, >= DELTA_THRESHOLD_DEEP); an axis delta decides only WHICH
    domain the scar is filed under, and no constant in the universe compares
    against it. A ``headroom_to_trauma`` on an axis would be a number the
    physics never computes — §2.8's error, reported instead of measured.

    ``wins`` is read off the row's own ``affected_domain``, never re-derived
    from ``deltas`` here. The two agree by construction today; a reporter that
    recomputed the argmax would keep agreeing after the universe stopped, and
    that silence is the failure this project has paid for four times.

    Rows without the block are skipped, not counted as zero: they come from a
    run made before the field existed, and "not recorded" is not "did not
    move" (§2.9, the same distinction D-121 drew for `z`).

    ⛔ Reporting only. Nothing here feeds any computation; it exists so the
    third pre-registration can ask whether `z` has more than one usable
    dimension with data instead of an argument (PROVENANCE_AUDIT §9: in C2,
    `social` and `uncertainty` appeared zero times in 216 lives).
    """

    instrumented = [row for row in rows if row.get(PE_ROW_AXIS_DELTAS_KEY)]
    per_axis: dict[str, list[float]] = {axis: [] for axis in AXIS_ORDER}
    wins: dict[str, int] = {axis: 0 for axis in AXIS_ORDER}
    for row in instrumented:
        deltas = row[PE_ROW_AXIS_DELTAS_KEY]
        for axis in AXIS_ORDER:
            if axis in deltas:
                per_axis[axis].append(float(deltas[axis]))
        winner = str(row.get(PE_ROW_AFFECTED_DOMAIN_KEY, ""))
        if winner in wins:
            wins[winner] += 1
    return {
        "n_events": len(instrumented),
        "wins": wins,
        "primary_axis": _primary_axis_counts(rows),
        "deltas": {
            axis: {
                "n_events": len(values),
                "max": max(values) if values else None,
                "mean": (sum(values) / len(values)) if values else None,
            }
            for axis, values in per_axis.items()
        },
    }


def _window_profile(
    agent_id: str,
    pe_rows: list[dict[str, Any]],
    pool_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    """The same two channels, but only up to the ordinal `z` is read at (D-124).

    ⚠ Why this exists, measured: the endpoint is a THRESHOLDED quantity —
    drift is written only when a magnitude reaches DELTA_THRESHOLD_DEEP — and
    in the C2 run that threshold was crossed by the individual channel in 24 of
    216 lives, leaving Var(z) = 0 in 14 of 18 transitions. The magnitudes that
    fell short are not noise: their peaks sat at 0.42–0.62 against a 0.70 gate.
    Whether a PRE-threshold endpoint would be estimable is therefore a question
    about the distribution below the gate, and nothing recorded so far could
    answer it: D-112 summarises the WHOLE life, while `z` is read at a fixed
    age, so the two are not about the same slice of the life.

    The window is `event_counter <= LANDMARK_EVENT`, inclusive, because the
    landmark reader takes the row AT that ordinal — the window ends where the
    endpoint is read, not one event earlier. The ordinal comes from constraints,
    not from a literal here, so moving the landmark moves this with it (§2.8).

    ⛔ Reporting only. Nothing here feeds any computation, and choosing an
    endpoint from it is a decision for the NEXT pre-registration — read as
    estimability (does the quantity vary at all), never as effect (L9).
    """

    def _in_window(row: dict[str, Any]) -> bool:
        return (
            row["agent_id"] == agent_id
            and int(row.get("event_counter", 0)) <= LANDMARK_EVENT
        )

    individual = [
        float(row["delta_magnitude"]) for row in pe_rows if _in_window(row)
    ]
    crisis = [
        float(row["crisis_magnitude"])
        for row in pool_rows
        if _in_window(row) and row.get("crisis_magnitude") is not None
    ]
    # Did this life actually reach the ordinal the endpoint is read at? A life
    # that stopped earlier has a TRUNCATED window, and averaging it beside a
    # complete one would compare different slices while looking identical
    # (§2.9 — the run says so rather than papering over it).
    reached = any(
        row["agent_id"] == agent_id
        and int(row.get("event_counter", 0)) >= LANDMARK_EVENT
        for row in pe_rows
    )
    window = _magnitude_summary(individual)
    window["channel"] = "individual"
    window["crisis"] = _magnitude_summary(crisis)
    window["crisis"]["n_crisis_events"] = len(crisis)
    window["window_last_event"] = LANDMARK_EVENT
    window["window_complete"] = reached
    # D-136, restricted to the same slice as everything else in this window —
    # `z` is read AT the landmark, so the axes that could have written it are
    # the ones that moved up to there, not the ones that moved afterwards.
    window["axes"] = _axis_profile([row for row in pe_rows if _in_window(row)])
    return window


def delta_profile(
    agent_id: str,
    pe_rows: list[dict[str, Any]],
    pool_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    """How close this life came to the trauma threshold — D-112, pure reporting.

    ⚠ The endpoint `z` is written by ONE function, ``update_drift``, on ONE
    condition, ``is_trauma`` (``magnitude >= DELTA_THRESHOLD_DEEP``) — but that
    function has TWO callers, and D-112 could only see one of them:

    * **individual** — the agent's own DeltaRecord (graph, PE path). Every one
      of these is on a PE row.
    * **commons crisis** — ``apply_crisis_trauma``, fired for EVERY agent at
      once when ``pool_ratio`` falls below the crisis floor (environment). It
      called ``update_drift`` directly and wrote nothing anywhere.

    D-115 is what the gap cost: seed 9904 had 0 of 72 lives cross the
    individual threshold and 72 of 72 agents carrying drift, and the profile
    said "nothing came close". It also explains the endpoint's real problem —
    a crisis hits the whole arm simultaneously, so eight agents receive the
    same scar, ``z`` has no within-cell variance and ``Cov(w, z)`` is zero not
    because nothing happened but because the same thing happened to everyone.
    Keeping the channels apart is the whole point: pooled, they are again
    indistinguishable.

    Nothing is computed here: the individual magnitudes are already on the PE
    rows and the crisis magnitude is written by ``_record_pool_event`` from the
    universe's own ``crisis_trauma_magnitude``. This only aggregates what the
    run recorded, so it changes no number the experiment produces (§2.10).
    """

    individual = [
        float(row["delta_magnitude"])
        for row in pe_rows
        if row["agent_id"] == agent_id
    ]
    crisis = [
        float(row["crisis_magnitude"])
        for row in pool_rows
        if row["agent_id"] == agent_id and row.get("crisis_magnitude") is not None
    ]
    profile = _magnitude_summary(individual)
    # The individual channel keeps the top-level keys D-112 defined, so a
    # reader (and analyze_population_run) sees the same field meaning the same
    # thing. The second channel is added beside it, never summed into it.
    profile["channel"] = "individual"
    profile["crisis"] = _magnitude_summary(crisis)
    profile["crisis"]["n_crisis_events"] = len(crisis)
    profile["n_at_or_above_trauma_either_channel"] = (
        profile["n_at_or_above_trauma"] + profile["crisis"]["n_at_or_above_trauma"]
    )
    # D-136: which axis carried each delta, and how big the losing axes were.
    # Beside the magnitude summary, never inside it — a swing on an axis and
    # the magnitude that decides trauma are different quantities (_axis_profile).
    profile["axes"] = _axis_profile(
        [row for row in pe_rows if row["agent_id"] == agent_id]
    )
    # D-124: the same channels restricted to the slice `z` is read from.
    profile["to_landmark"] = _window_profile(agent_id, pe_rows, pool_rows)
    return profile


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
    pe_rows = graph_mod.get_pe_event_log()
    pool_rows = graph_mod.get_pool_event_log()
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
                delta_profile=delta_profile(agent_id, pe_rows, pool_rows),
                precision=_precision_profile(
                    graph_mod.rows_for_agent(pe_rows, agent_id)
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
            # D-121's positive control, read from the landmark block the run
            # already writes. Time-integrated energy was chosen because it is
            # continuous and does NOT pass through the trauma threshold, which
            # is the thing that flattens z; measured range 0.59–0.86 (D-085).
            # ⚠ Diagnostic only — no inheritance claim rests on it.
            control=_control_trait(row.landmark),
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

    # D-152. The cell's own F_agent values, so the transfer band is relative.
    # Built once and shared by every parent of the cell — a per-parent rebuild
    # would let two agents of one generation disagree about what "low" means.
    cell_reference = [float(row.f_agent) for row in rows]
    return {
        row.agent_id: consolidate_generation(
            states[row.agent_id],
            store,
            f_agent=row.f_agent,
            reward_marker=row.reward_marker,
            threat_marker=row.threat_marker,
            f_agent_reference=cell_reference,
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
            # D-108. Empty on a healthy step; on a declined one it says which
            # of the five refusals happened, and I1.1 branches on exactly one
            # of them.
            SECTION_REASON_KEY: str(outcome.reason),
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
    checkpoint: "Checkpoint | None" = None,
) -> dict[str, Any]:
    """One arm: G generations of N agents on that arm's own pasture (P1).

    ``checkpoint`` is written after every generation, so an interrupted run
    keeps everything it had already measured (D-111).
    """

    _lock_seeds(seed)
    rng = random.Random(seed)
    app = graph_mod.build_event_graph()
    states = build_arm_population(arm, seed, n_agents)
    env = shared_pasture(states)

    generations: list[dict[str, Any]] = []
    generation_rng_digests: list[dict[str, Any]] = []
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
                vault=vault, generations=generations,
                generation_rng_digests=generation_rng_digests,
                previous_plan=previous_plan,
                previous_parents=previous_parents, n_agents=n_agents,
                n_generations=n_generations, events_budget=events_budget,
                pasture_carryover=pasture_carryover, founders=states,
                checkpoint=checkpoint,
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
    generation_rng_digests: list[dict[str, Any]],
    previous_plan: GenerationPlan | None,
    previous_parents: dict[str, DAUAgentState],
    n_agents: int,
    n_generations: int,
    events_budget: int,
    pasture_carryover: bool,
    founders: list[DAUAgentState],
    checkpoint: "Checkpoint | None" = None,
) -> dict[str, Any]:
    """The generation loop of one arm; run_arm owns the global it borrows."""

    for generation in range(FIRST_GENERATION, FIRST_GENERATION + n_generations):
        # D-176/B1 / D-149 / I4.2 / GAP-12. Re-lock before EVERY generation,
        # matching run_cprime_multigen's four call sites — same seed, same
        # function, so the two runners answer GAP-12 the same way instead of
        # two ways.
        #
        # ⚠ This line replaces a measurement. D-149 shipped the digest WITHOUT
        # the lock on purpose: whether training consumes the global stream
        # could not be settled from a stub run (the stub turns training off,
        # which is K1(b)'s trap), so the first run recorded the state and the
        # gate read it. The number came back in D-173 — arms entered gen3 and
        # gen4 from different states in 6 of 6 cells — and the mode escalates
        # here, as that comment said it would.
        #
        # ⛔ NOT instrumentation: the RNG stream moves, so digests move. Done
        # BEFORE the PREREGISTRATION_3 lock for exactly that reason (§2.10).
        _lock_seeds(seed)
        generation_rng_digests.append(
            {
                "seed": int(seed),
                "arm": str(arm),
                "generation": int(generation),
                "rng_digest": rng_state_digest(),
            }
        )
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
        control: dict[str, float | bool] | None = None
        if previous_plan is not None:
            control = positive_control_partition(
                list(previous_plan.parents), previous_plan.w_by_parent
            )
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
                # D-163 / I5.6. Whether the harvest ceiling actually bit this
                # generation. `pool_ratio_end` alone cannot say: a pasture can
                # end the run half full because nobody was hungry OR because
                # the ceiling was holding everyone back, and those are opposite
                # states. The whole layer is the short-fall, so the run has to
                # report it rather than let the reader infer it.
                "harvest_shortfall": harvest_shortfall_summary(
                    graph_mod.get_pool_event_log()
                ),
                # D-166 / D-165. The other half of the same ledger: the
                # short-fall says what the pasture withheld, this says what was
                # asked and by which decision. Without it the ceiling
                # arithmetic has no demand term and the constant cannot be
                # chosen — which is where D-165 stopped.
                "demand": demand_summary(graph_mod.get_pool_event_log()),
                # The window the ceiling question actually lives in: the
                # endpoint is read at LANDMARK_EVENT, so demand after it cannot
                # affect whether the founders had separated by then.
                "demand_to_landmark": demand_summary(
                    graph_mod.get_pool_event_log(), max_event=LANDMARK_EVENT
                ),
                "agents": [
                    {
                        "agent_id": row.agent_id,
                        "f_agent": row.f_agent,
                        # D-150. The BAND, not just the number: the inherited
                        # warning that feeds the somatic channel fires only in
                        # the low or high band, and C2 reported f_agent for 216
                        # agents while never saying that 0 of them were low and
                        # 12 were high. Derived through `classify_fitness` so
                        # the report cannot disagree with the rule that
                        # actually gates transfer (§2.8).
                        # D-152: the RELATIVE band, because that is the one
                        # that actually gates transfer. Reporting the absolute
                        # band beside a run governed by the relative one is
                        # §2.8's error in its plainest form.
                        "fitness_class": classify_fitness_relative(
                            row.f_agent, [float(r.f_agent) for r in rows]
                        ),
                        "f_agent_inputs": row.f_agent_inputs,
                        "events_lived": row.events_lived,
                        "landmark": row.landmark,
                        "delta_profile": row.delta_profile,
                        "precision": row.precision,
                        # Whether this agent's events could reach the vault at
                        # all. An unbound heir writes no engrams, so its own
                        # children inherit nothing and the transmission term
                        # goes quietly to zero — invisible without this flag
                        # (measured: the binding could be deleted and every
                        # test still passed).
                        "vault_bound": row.agent_id in vault.bound,
                        # D-158 / queue 2.5. Where this parent's candidate
                        # memories were lost on the way to the heir. D-155
                        # could see that 0 of 32 heirs carried a somatic scale
                        # but not WHICH gate swallowed them, so the diagnosis
                        # stayed an inference. Written by the gate itself
                        # (`select_for_transfer`), never re-derived here.
                        "transfer_gates": dict(
                            records[row.agent_id].transfer_gate_report
                        )
                        if row.agent_id in records
                        else {},
                    }
                    for row in rows
                ],
                "trained": trained,
                "n_inherited_by_parent": {
                    agent_id: len(record.inherited_memories)
                    for agent_id, record in sorted(records.items())
                },
                "price_for_previous_transition": price,
                "positive_control_for_previous_transition": control,
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
        # D-111: written HERE, after the generation is appended and before the
        # next one starts. Per generation rather than per arm because at the
        # main run's scale one arm is hours, and the point of the file is how
        # much a crash costs.
        if checkpoint is not None:
            checkpoint.write({"arm": arm, "seed": seed, "generations": generations})
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

    return {
        "arm": arm,
        "seed": seed,
        "generations": generations,
        # D-170 / I5.1. Read HERE because `arm_vault` closes the store on the
        # way out: after that the count is gone and the gate would have to
        # guess. One number per ARM, not per life — the vault is per arm by
        # design (P1), so this is the finest grain that exists.
        "memory_edges": _count_edges(vault.store),
        # D-149 / I4.2 (GAP-12). The global RNG state each generation STARTED
        # from. Kept at arm level rather than inside `generations` because the
        # gate compares ACROSS arms of one seed, and a per-generation nesting
        # would make the reader re-join what the gate needs whole.
        "generation_rng_digests": generation_rng_digests,
    }


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
    checkpoint_path: Path | None = None,
    resume: bool = False,
) -> dict[str, Any]:
    """Every arm × every seed. Each arm keeps its own population and pasture.

    ``preflight`` collects the invariant verdicts; phase 0 runs here and aborts
    before any GPU work, and the block it renders is written into the results.

    ⚠ ``resume`` defaults to False on purpose (D-176/B2). A stale checkpoint
    sitting beside a new run is a trap the Checkpoint docstring already names,
    and picking it up automatically would mean a typo in ``--results`` silently
    inherits somebody else's arms. Resuming is something an operator asks for.
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
    # ⚠ D-176/B2 moved this ABOVE phase 0, and the reason is the resume: I0.7's
    # exemption list is derived from the checkpoint, and the checkpoint cannot
    # be read until there is a header to check it against. Safe to move because
    # phase 0 creates nothing this reads — it checks env, determinism and the
    # adapter directory, and `_adapter_state()` sees the same census either
    # side of it. It stays BELOW `_lock_seeds`, which is load-bearing:
    # `_sampling()` reports the seed that lock just pinned.
    #
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
    header = {
        "protocol": PROTOCOL_NAME,
        "n_agents": n_agents,
        "n_generations": n_generations,
        "events_budget": events_budget,
        "seeds": list(seeds),
        "tool_identity": identity,
    }
    # D-176/B2. Read before phase 0 so I0.7 can be told which adapters are this
    # run's own earlier work rather than contamination. Refuses loudly on a
    # mismatch; returns [] when resume was not asked for.
    completed = (
        completed_arms_from_checkpoint(checkpoint_path, header, n_generations)
        if resume
        else []
    )
    done: dict[tuple[str, int], dict[str, Any]] = {
        (str(arm_result["arm"]), int(arm_result["seed"])): arm_result
        for arm_result in completed
    }
    if done:
        print(
            f"[POPULATION] resuming {checkpoint_path}: "
            f"{sorted(done)} already finished, re-running the rest.",
            flush=True,
        )
    run_population_phase0(
        gate,
        agent_ids=planned_founder_ids(
            list(seeds), n_agents, tuple(arms), skip_cells=frozenset(done)
        ),
        seeds=list(seeds),
    )
    gate.enforce()

    checkpoint = (
        None
        if checkpoint_path is None
        else Checkpoint(path=checkpoint_path, header=header, completed=list(completed))
    )
    arm_results: list[dict[str, Any]] = []
    for seed in seeds:
        for arm in arms:
            # Rebuilt in the canonical loop order, never in checkpoint order:
            # a resumed run and an uninterrupted one must produce the same
            # file, and `arms` is read positionally downstream.
            cached = done.get((arm, int(seed)))
            if cached is not None:
                arm_results.append(cached)
                continue
            result = run_arm(
                arm, seed, n_agents, n_generations, events_budget,
                pasture_carryover=pasture_carryover,
                checkpoint=checkpoint,
            )
            arm_results.append(result)
            if checkpoint is not None:
                checkpoint.arm_finished(result)
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
    # D-149 / GAP-12. Wired here for the first time on this path (D-147/AV-3
    # measured 6 of 26 invariants live, and this was one of the 20).
    #
    # ⭐ D-176/B1: the number D-149 was waiting for arrived. D-173 measured the
    # arms entering gen3 and gen4 from DIFFERENT states in 6 of 6 cells, so
    # `_run_arm_generations` now re-locks before every generation and the two
    # runners answer GAP-12 the same way.
    #
    # ⚠ STILL FLAG, not ABORT — and the reason changed, so it is rewritten
    # rather than left standing. It is no longer "the premise is unmeasured";
    # it is the cost shape. This gate runs in phase 2, AFTER every life, and
    # `main()` writes NO results file on a PreflightAbort. Escalating would
    # mean a 70-hour run that diverges at the last cell produces nothing to
    # read — while the divergence it caught is a TOOL regression, not a dirty
    # measurement: the lives already ran, and the flag names the split cells.
    # So the failure is reported at full volume and the data survives.
    # Declared in PREREGISTRATION_3 §5.1 so the choice is visible before the
    # run, not explained after it.
    gate.check(
        "I4.2",
        lambda: check_generation_rng_uniform(arm_results),
        mode=MODE_FLAG,
    )
    # I5.4 (GAP-3) — the symbolic channel actually reaching the heir. The claim
    # of this experiment is about inheritance, so a run that never applied an
    # inherited somatic scale should say so on its own face.
    # ⚠ Skipped under a canned LLM for the same reason I4.1 is: a mock life
    # accumulates no emotional weight, so "no inherited somatic scale was
    # applied" would be a statement about the stub, not about the system. It
    # records None — not evaluated — rather than a green it did not earn.
    gate.check(
        "I5.4",
        (lambda: (None, "not evaluated under a canned LLM"))
        if use_mock
        else check_somatic_scale_applied,
        mode=MODE_FLAG,
    )
    # I5.1 (GAP-14 / D-169) — is the association graph anything but empty?
    # Bound here because it was DEFINED in preflight and bound only on the
    # single-lineage path: the population runs reported ten gates and this was
    # not one of them, so "PPR contributed a constant" and "PPR contributed a
    # score" were indistinguishable across every population run to date. That
    # is D-149's failure verbatim (a gate defined but not wired) and K6 exists
    # because of it.
    #
    # ⚠ FLAG, and it stays FLAG: whether PPR SHOULD be wired into the run path
    # or documented as inert is the GAP-14 decision, not the gate's call. The
    # gate reports; it does not decide.
    #
    # ⚠ Skipped under a canned LLM, and the first version of this line got the
    # reason wrong in the same way I5.6's first version did. It said edges are
    # "a property of the memory pipeline, not of the model" — measured, and
    # false: `write_edge` has exactly one caller (consolidation.py), which
    # pairs only DEEP/TRAUMA nodes inside DOMAIN_EDGE_WINDOW. A stub life
    # accumulates no emotional weight, so it produces none of those, and the
    # gate would report "PPR is inert" about the stub rather than about the
    # system. Records None — not evaluated — like I4.1, I5.4 and I5.6.
    #
    # ⭐ D-178/B4. The GAP-14 decision named above was taken: sleep
    # consolidation stays unwired and the boundary is declared, so this gate
    # now records None rather than a False that describes the wiring. The
    # condition reads the constant, so wiring consolidation brings the gate
    # back on its own.
    gate.check(
        "I5.1",
        (lambda: (None, "not evaluated under a canned LLM"))
        if use_mock
        else (lambda: (None, SLEEP_CONSOLIDATION_BOUNDARY))
        if not SLEEP_CONSOLIDATION_WIRED
        else (
            lambda: check_ppr_active(
                [
                    {
                        "agent_id": f"{arm['arm']}-s{arm['seed']}",
                        "memory_edges": int(
                            arm.get("memory_edges", UNREADABLE_EDGES)
                        ),
                    }
                    for arm in arm_results
                ],
                unit="arm vaults",
            )
        ),
        mode=MODE_FLAG,
    )
    # I5.5 (D-159 / queue 2.6) — is the selection term measurable where the
    # design says it reads it? FLAG, not ABORT, and for the same reason I4.2
    # is: a non-estimable transition is a legitimate finding about the universe
    # (D-123's "universe null"), not a broken tool. Aborting on it would refuse
    # to record the very result this experiment is willing to report. What was
    # NOT acceptable was reporting it as `clean`, which is what C2 did.
    # ⚠ Evaluated under a canned LLM too, unlike I4.1/I5.4: the estimability of
    # Var(z) is a property of the recorded numbers, not of the language model,
    # so a stub run's answer is about the pipeline and worth having.
    gate.check(
        "I5.5",
        lambda: check_selection_estimable_where_claimed(arm_results),
        mode=MODE_FLAG,
    )
    # I5.6 (D-163 / Layer 1) — did the harvest ceiling actually bite? FLAG
    # rather than ABORT for the same reason as I4.2 and I5.5: a commons that
    # was never short is a statement about the universe, and refusing to record
    # it would throw away the measurement. What it must not do is pass silently.
    #
    # ⚠ Skipped under a canned LLM, and the first version of this line got the
    # reason wrong. The short-fall looks like pure arithmetic on the ledger, so
    # it seemed model-independent — but only the SUPPLY side is. The DEMAND
    # side is the decision, and a stub decides for its own reasons: a canned
    # agent that always cooperates asks for 2.0, never reaches a ceiling that
    # opens at 8.0, and would report "the ceiling never bound" about the stub
    # rather than about the commons. Records None, like I4.1 and I5.4.
    gate.check(
        "I5.6",
        (lambda: (None, "not evaluated under a canned LLM"))
        if use_mock
        else (lambda: check_harvest_ceiling_binds(arm_results)),
        mode=MODE_FLAG,
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
        # D-111. True only here, on the path that ran every gate. The
        # checkpoint file writes False, and the reader refuses that file —
        # otherwise a partial run would be indistinguishable from a result
        # that simply had fewer arms.
        RESULTS_COMPLETE_KEY: True,
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
    # D-176/B2. Opt-in, never automatic: see run_population_experiment's
    # docstring for why a checkpoint is not picked up on its own.
    parser.add_argument(
        "--resume",
        action="store_true",
        help=(
            "continue the checkpoint beside --results: arms that already "
            "finished are kept, everything else re-runs. Refuses if the "
            "checkpoint was written by a different run."
        ),
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_arg_parser().parse_args(argv)
    # D-114: chronic allocator pressure killed two lives of the headroom run.
    # Applied here, before argv can lead anywhere near a CUDA allocation, and
    # loud rather than best-effort — a memory setting that silently failed to
    # apply is worse than none, because the results file would still name it.
    allocator = apply_cuda_allocator_config()
    print(f"{allocator['env']}={allocator['value']} ({allocator['source']})")
    if args.mock_llm:
        os.environ[MOCK_LLM_ENV] = "1"
        install_mock_llm()
    partial = checkpoint_path_for(args.results)
    try:
        results = run_population_experiment(
            seeds=list(args.seeds),
            n_agents=int(args.n_agents),
            n_generations=int(args.n_generations),
            events_budget=int(args.events),
            lora=bool(args.lora),
            pasture_carryover=bool(args.carryover),
            arms=tuple(args.arms),
            checkpoint_path=partial,
            resume=bool(args.resume),
        )
    except PreflightAbort as abort:
        # An expected refusal, not a crash: print the named invariants rather
        # than a traceback, and write NO results file (preflight.py's contract —
        # a silent fake result has to be impossible, not merely labelled).
        # D-111: the checkpoint is deliberately LEFT on disk here. A refused
        # run still measured things, and losing them was the cost D-108 paid.
        raise SystemExit(
            f"{abort}\n\nPartial measurements kept at {partial} — "
            f"NOT a result: no gate passed on it."
        ) from None
    args.results.parent.mkdir(parents=True, exist_ok=True)
    args.results.write_text(json.dumps(results, indent=1), encoding="utf-8")
    Checkpoint(path=partial, header={}).discard()
    print(f"wrote {args.results}")
    print(f"run_quality={results['run_quality']}", flush=True)


if __name__ == "__main__":
    main()
