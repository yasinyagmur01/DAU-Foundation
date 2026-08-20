"""Generation consolidation — inheritance of earned traces across lifecycles.

Biology analogy: when one life ends, only what was used and strong enough
passes to the next generation. Trauma scars transfer only if they reshaped
the organism enough to matter. Packaging inheritance is not birth — the
new agent is created elsewhere and then receives this package.

Layer 4 adds F_agent: low-fitness lives keep trauma as cautionary inherited
warnings; high-fitness lives convert trauma into inherited warnings with scaled
somatic weight. Fitness shapes WHICH traces carry forward, not whether any do
(D-088) — whether is the salience bar's job, and how many heirs a life gets is
w's, which is where selection is priced.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any

from dau.generation.fitness import (
    FITNESS_LABEL_HIGH,
    FITNESS_LABEL_LOW,
    WARNING_SOMATIC_SCALE,
    classify_fitness,
    classify_fitness_relative,
    compute_w_transfer,
)
from dau.memory.decay import compute_strength_init
from dau.memory.retrieval import compute_memory_score

from .delta import is_trauma
from .drift import DriftState
from .state import DAUAgentState, DeltaRecord

# ---------------------------------------------------------------------------
# Generation transfer thresholds (no magic numbers in logic)
# ---------------------------------------------------------------------------

# The salience bar a durable memory clears to be worth carrying forward. It
# gates memory_score — the quantity it was calibrated for in Layer-3 — on BOTH
# selection paths since D-088; before that the F_agent path compared it against
# memory_score·F_agent·valence and so never opened.
GENERATION_TRANSFER_THRESHOLD: float = 0.6
GENERATION_MIN_RECALL: int = 1
DRIFT_TRANSFER_MIN: float = 1.5
# w_transfer on a candidate that was never scored against F_agent (the legacy
# path supplies no fitness). Not zero: zero is a real fitness-weighted salience
# and a reader must be able to tell "unfit" from "never asked".
W_TRANSFER_UNSCORED: float = -1.0

RETRIEVAL_CONTEXT_ATTR: str = "retrieval_context"
GENERATION_INHERITED_KEY: str = "generation_inherited"
RECORD_ID_KEY: str = "record_id"
INHERITED_WARNING_KEY: str = "inherited_warning"
SOMATIC_SCALE_KEY: str = "somatic_scale"

TRANSFER_KIND_STANDARD: str = "standard"
TRANSFER_KIND_INHERITED_WARNING: str = "inherited_warning"

# ---------------------------------------------------------------------------
# Transfer gate census (D-155/D-157 · queue 2.5) — reporting only
# ---------------------------------------------------------------------------
# D-155 measured that 0 of 32 heirs carried a somatic scale while three links
# of the chain demonstrably worked (relative bands populate low/high, the
# trauma threshold is crossed in 48 of 48 lives, and low-band parents do
# reproduce). Which of the REMAINING gates swallows the candidate was an
# inference, not a measurement — the results file carried no recall count and
# no per-gate tally, so "known" and "unknown" were indistinguishable (K6).
#
# ⛔ These counters are written by the gate itself, never re-derived beside it:
# a second function that re-implements the branch conditions would be §2.8's
# error and could agree with a gate that no longer exists.
GATE_KEY_CANDIDATES: str = "candidates"
GATE_KEY_DROPPED_RECALL: str = "dropped_recall"
GATE_KEY_TRAUMA: str = "trauma"
GATE_KEY_WARNING_LOW: str = "warning_low"
GATE_KEY_DROPPED_SALIENCE: str = "dropped_salience"
GATE_KEY_WARNING_HIGH: str = "warning_high"
GATE_KEY_DROPPED_DRIFT: str = "dropped_drift"
GATE_KEY_STANDARD: str = "standard"

TRANSFER_GATE_KEYS: tuple[str, ...] = (
    GATE_KEY_CANDIDATES,
    GATE_KEY_DROPPED_RECALL,
    GATE_KEY_TRAUMA,
    GATE_KEY_WARNING_LOW,
    GATE_KEY_DROPPED_SALIENCE,
    GATE_KEY_WARNING_HIGH,
    GATE_KEY_DROPPED_DRIFT,
    GATE_KEY_STANDARD,
)


def new_transfer_gate_report() -> dict[str, int]:
    """A zeroed census. Every key present, so absent ≠ zero in the results."""

    return {key: 0 for key in TRANSFER_GATE_KEYS}

DEFAULT_REWARD_MARKER: float = 0.0
DEFAULT_THREAT_MARKER: float = 0.0
# Heir vault stamp at lineage handoff (matches MemoryStore.SEED_BIRTH_COUNTER_DEFAULT).
APPLY_BIRTH_COUNTER: int = 0


@dataclass
class TransferCandidate:
    """A scored durable memory considered for generational transfer.

    Biology analogy: an engram card pulled from the vault with its rehearsal
    count and current salience attached — selection needs more than the raw
    physiological delta alone. transfer_kind marks inherited warnings.
    """

    record: DeltaRecord
    record_id: str
    memory_score: float
    recall_count: int
    transfer_kind: str = TRANSFER_KIND_STANDARD
    inherited_warning: bool = False
    somatic_scale: float = 0.0
    # Fitness-weighted salience, filled in by select_for_transfer when F_agent
    # is supplied. It stopped gating transfer in D-088 (it was compared against
    # a threshold calibrated for memory_score alone), but it is still the only
    # place F_agent and salience are combined, so it travels with the candidate
    # rather than being recomputed by a reader (CLAUDE.md 2.8).
    w_transfer: float = W_TRANSFER_UNSCORED


@dataclass
class GenerationRecord:
    """Immutable inheritance package from one lifecycle to the next.

    Biology analogy: the will of a finished life — which engrams earned
    survival, which domain scars remain, and when the transfer was sealed.
    Does not create the heir; it only packages what may be inherited.
    """

    agent_id: str
    generation: int = 0
    inherited_memories: list[str] = field(default_factory=list)
    inherited_drift: DriftState = field(default_factory=DriftState)
    transfer_timestamp: int = 0
    inherited_warning_ids: list[str] = field(default_factory=list)
    inherited_somatic_scales: dict[str, float] = field(default_factory=dict)
    # D-158 / queue 2.5. Where this life's candidates were lost. Reporting
    # only — nothing downstream reads it, and the gate's behaviour does not
    # depend on whether anyone asked for the census.
    transfer_gate_report: dict[str, int] = field(default_factory=dict)


def _legacy_select_for_transfer(
    memories: list[TransferCandidate],
    drift_state: DriftState,
) -> list[TransferCandidate]:
    """Layer-3 path: memory_score, recall_count, trauma gated by drift."""

    selected: list[TransferCandidate] = []
    for candidate in memories:
        if candidate.memory_score < GENERATION_TRANSFER_THRESHOLD:
            continue
        if candidate.recall_count < GENERATION_MIN_RECALL:
            continue
        if is_trauma(candidate.record):
            domain = str(candidate.record.affected_domain)
            drift_magnitude = float(
                drift_state.magnitudes.get(domain, 0.0)
            )
            if drift_magnitude < DRIFT_TRANSFER_MIN:
                continue
        selected.append(candidate)
    return selected


def select_for_transfer(
    memories: list[TransferCandidate],
    drift_state: DriftState,
    f_agent: float | None = None,
    reward_marker: float = DEFAULT_REWARD_MARKER,
    threat_marker: float = DEFAULT_THREAT_MARKER,
    f_agent_reference: list[float] | None = None,
    gate_report: dict[str, int] | None = None,
) -> list[TransferCandidate]:
    """Keep only memories that earned survival into the next generation.

    Biology analogy: natural selection over engrams. When F_agent is omitted,
    Layer-3 salience / rehearsal / drift rules apply. When F_agent is given,
    the same salience bar applies and fitness bands reshape trauma handling.

    D-088: this used to say "W_transfer gates transfer", and it did — against a
    threshold calibrated for memory_score alone, which no lineage could reach.
    W_transfer is still computed and attached to the candidate, but it no
    longer decides. See the comment on the gate below for why fitness belongs
    on which-memories rather than whether-any.
    """

    # D-158 / queue 2.5. A local sink when nobody asked, so every branch below
    # writes unconditionally: a branch that only counts "when reporting is on"
    # is a second code path, and the one that runs in the real experiment
    # would be the untested one (K3).
    census = new_transfer_gate_report() if gate_report is None else gate_report
    for key in TRANSFER_GATE_KEYS:
        census.setdefault(key, 0)
    census[GATE_KEY_CANDIDATES] += len(memories)

    if f_agent is None:
        return _legacy_select_for_transfer(memories, drift_state)

    f_value = float(f_agent)
    # D-152. Which BAND gates this life's transfer policy. With a reference
    # population the band is relative — where this agent sits inside its own
    # cell — because C2 measured 216 of 216 agents in `normal`, leaving two of
    # the three band rules unreachable and the inherited-warning branch dead
    # (0 of 144 heirs carried a somatic scale). Without a reference the
    # absolute bands stand, which is what the single-lineage runner needs:
    # one agent has no cell to be relative to.
    #
    # ⛔ The reference is the cell's F_agent values, NOT w. Deriving the band
    # from heir count would make z a function of w by construction and hollow
    # out Cov(w, z) — the tautology D-075 pinned and P4 keeps three layers
    # apart to avoid.
    band = (
        classify_fitness_relative(f_value, f_agent_reference)
        if f_agent_reference
        else classify_fitness(f_value)
    )
    selected: list[TransferCandidate] = []
    for candidate in memories:
        if candidate.recall_count < GENERATION_MIN_RECALL:
            census[GATE_KEY_DROPPED_RECALL] += 1
            continue

        trauma = is_trauma(candidate.record)
        if trauma:
            census[GATE_KEY_TRAUMA] += 1
        if band == FITNESS_LABEL_LOW and trauma:
            census[GATE_KEY_WARNING_LOW] += 1
            candidate.inherited_warning = True
            candidate.somatic_scale = -WARNING_SOMATIC_SCALE
            selected.append(candidate)
            continue

        # D-088: the salience bar is tested on the quantity it was calibrated
        # for. GENERATION_TRANSFER_THRESHOLD was born in Layer-3 (cf400eb,
        # 2026-08-01) gating memory_score alone, and Layer-4 (da6880b, two days
        # later) reused the same constant against the PRODUCT
        # memory_score·F_agent·valence. Since memory_score ≤ 1 that product can
        # never exceed F_agent·valence, so the gate silently became an
        # undeclared "F_agent ≥ 0.6" requirement: it passed zero memories in
        # all twelve D-085 lineages, and at the F_agent those lives could reach
        # (0.139) no valence in range could have opened it. It also made the
        # low/normal band policies below unreachable — dead code the design
        # clearly meant to run, since it writes a distinct transfer rule for
        # each band.
        #
        # Fitness has NOT been dropped; it moved off the on/off switch. Gating
        # transmission on absolute fitness double-counts selection, because
        # F_agent is also what will set w, the heir count (D-076 / Price). That
        # is the same error K4-b (D-070) removed from the pool term, where
        # longevity was priced twice. F_agent now shapes WHICH memories
        # transfer — the three band rules below — not WHETHER any do.
        #
        # w_transfer stays computed and rides along on the candidate so the
        # fitness-weighted salience is still visible in the results file; a
        # later decision can re-gate on it with a threshold derived for a
        # product rather than transplanted from a score.
        w_transfer = compute_w_transfer(
            candidate.memory_score,
            f_value,
            reward_marker,
            threat_marker,
        )
        candidate = replace(candidate, w_transfer=w_transfer)
        if candidate.memory_score < GENERATION_TRANSFER_THRESHOLD:
            census[GATE_KEY_DROPPED_SALIENCE] += 1
            continue

        if trauma and band == FITNESS_LABEL_HIGH:
            census[GATE_KEY_WARNING_HIGH] += 1
            selected.append(
                replace(
                    candidate,
                    transfer_kind=TRANSFER_KIND_INHERITED_WARNING,
                )
            )
            continue

        if trauma:
            domain = str(candidate.record.affected_domain)
            drift_magnitude = float(
                drift_state.magnitudes.get(domain, 0.0)
            )
            if drift_magnitude < DRIFT_TRANSFER_MIN:
                census[GATE_KEY_DROPPED_DRIFT] += 1
                continue

        census[GATE_KEY_STANDARD] += 1
        selected.append(
            replace(candidate, transfer_kind=TRANSFER_KIND_STANDARD)
        )
    return selected


def _now_counter_from_state(agent_state: DAUAgentState) -> int:
    """Derive the current event ordinal from lived logs."""

    stamps: list[int] = []
    for event in agent_state.event_log:
        stamps.append(int(event.timestamp))
    for delta in agent_state.delta_log:
        stamps.append(int(delta.timestamp))
    if not stamps:
        return 0
    return max(stamps)


def _candidates_from_store(
    agent_id: str,
    now_counter: int,
    memory_store: Any,
) -> list[TransferCandidate]:
    """Score every durable node for this agent into transfer candidates."""

    if memory_store is None:
        return []

    candidates: list[TransferCandidate] = []
    for node in memory_store.list_nodes(agent_id):
        record = memory_store.get_record_payload(node.id)
        if record is None:
            # Reconstruct a minimal DeltaRecord from the SQLite index card.
            snap = {
                "energy": 1.0,
                "resource_load": 0.0,
                "uncertainty_load": 0.0,
                "social_load": 0.0,
            }
            record = DeltaRecord(
                timestamp=int(node.timestamp),
                magnitude=float(node.magnitude),
                affected_domain=node.domain,  # type: ignore[arg-type]
                snapshot_before=snap,
                snapshot_after=dict(snap),
            )

        strength_init = compute_strength_init(record)
        recall_count = max(0, int(node.strength) - int(strength_init))
        score = compute_memory_score(
            node.id,
            node.domain,
            now_counter,
            memory_store,
        )
        candidates.append(
            TransferCandidate(
                record=record,
                record_id=str(node.id),
                memory_score=float(score),
                recall_count=int(recall_count),
            )
        )
    return candidates


def consolidate_generation(
    agent_state: DAUAgentState,
    memory_store: Any,
    f_agent: float | None = None,
    reward_marker: float = DEFAULT_REWARD_MARKER,
    threat_marker: float = DEFAULT_THREAT_MARKER,
    f_agent_reference: list[float] | None = None,
) -> GenerationRecord:
    """Package earned memories and current drift for the next generation.

    Biology analogy: end-of-life consolidation — inventory the vault, keep
    what survived selection pressure, seal the scar map. Does not birth the
    heir; only prepares the inheritance. Optional F_agent enables Layer-4
    fitness-based trauma purge / inherited-warning marking.
    """

    now_counter = _now_counter_from_state(agent_state)
    candidates = _candidates_from_store(
        agent_state.agent_id,
        now_counter,
        memory_store,
    )
    drift = agent_state.drift_state
    if not isinstance(drift, DriftState):
        drift = DriftState()

    gate_report = new_transfer_gate_report()
    selected = select_for_transfer(
        candidates,
        drift,
        f_agent=f_agent,
        reward_marker=reward_marker,
        threat_marker=threat_marker,
        f_agent_reference=f_agent_reference,
        gate_report=gate_report,
    )
    warning_candidates = [
        c
        for c in selected
        if c.transfer_kind == TRANSFER_KIND_INHERITED_WARNING or c.inherited_warning
    ]
    return GenerationRecord(
        agent_id=agent_state.agent_id,
        generation=int(agent_state.generation),
        inherited_memories=[c.record_id for c in selected],
        inherited_drift=DriftState(
            flags=dict(drift.flags),
            magnitudes=dict(drift.magnitudes),
        ),
        transfer_timestamp=now_counter,
        inherited_warning_ids=[c.record_id for c in warning_candidates],
        inherited_somatic_scales={
            c.record_id: (
                c.somatic_scale if c.inherited_warning else WARNING_SOMATIC_SCALE
            )
            for c in warning_candidates
        },
        transfer_gate_report=gate_report,
    )


def _seed_inherited_id_map(
    memory_store: Any,
    parent_ids: list[str],
    dest_agent_id: str,
) -> dict[str, str]:
    """Copy parent engrams into the heir vault; return parent_id → heir_id."""

    id_map: dict[str, str] = {}
    if memory_store is None:
        return id_map
    seed_fn = getattr(memory_store, "seed_inherited_record", None)
    if seed_fn is None:
        return id_map
    for parent_id in parent_ids:
        new_id = seed_fn(
            parent_id,
            dest_agent_id,
            birth_counter=APPLY_BIRTH_COUNTER,
        )
        if new_id:
            id_map[str(parent_id)] = str(new_id)
    return id_map


def apply_generation(
    new_agent_state: DAUAgentState,
    record: GenerationRecord,
    memory_store: Any,
) -> DAUAgentState:
    """Apply an inheritance package onto a newly created agent state.

    Biology analogy: the heir receives scarred niches and the engrams that
    earned transfer — lineage age advances by one. Inherited warnings carry
    a reduced somatic scale so ancestral trauma informs without dominating.

    When memory_store is provided, selected parent engrams are seeded under
    the heir's agent_id (new record ids). When None, only retrieval_context
    markers are written (legacy / unit-test path).
    """

    inherited_drift = DriftState(
        flags=dict(record.inherited_drift.flags),
        magnitudes=dict(record.inherited_drift.magnitudes),
    )
    warning_ids = set(record.inherited_warning_ids)
    warning_scales = dict(record.inherited_somatic_scales)

    id_map = _seed_inherited_id_map(
        memory_store,
        list(record.inherited_memories),
        new_agent_state.agent_id,
    )

    retrieval_context: list[dict[str, Any]] = []
    for parent_id in record.inherited_memories:
        # Prefer seeded heir id; fall back to parent id when store is absent
        # or the source engram was missing from the vault.
        context_id = id_map.get(str(parent_id), str(parent_id))
        entry: dict[str, Any] = {
            RECORD_ID_KEY: context_id,
            GENERATION_INHERITED_KEY: True,
        }
        if parent_id in warning_ids:
            entry[INHERITED_WARNING_KEY] = True
            entry[SOMATIC_SCALE_KEY] = warning_scales.get(
                parent_id, WARNING_SOMATIC_SCALE
            )
        retrieval_context.append(entry)
    return new_agent_state.model_copy(
        update={
            "generation": int(record.generation) + 1,
            "drift_state": inherited_drift,
            "retrieval_context": retrieval_context,
            "generation_record": record,
        }
    )


if __name__ == "__main__":
    from .constraints import build_default_constraints

    empty_state = DAUAgentState(
        agent_id="gen-demo-0",
        environment=build_default_constraints(),
    )
    package = consolidate_generation(empty_state, memory_store=None)
    print(
        f"empty_transfer memories={package.inherited_memories} "
        f"generation={package.generation}"
    )
    heir = DAUAgentState(
        agent_id="gen-demo-1",
        environment=build_default_constraints(),
    )
    applied = apply_generation(heir, package, memory_store=None)
    print(f"heir_generation={applied.generation}")
    print("OK — generation demo complete")
