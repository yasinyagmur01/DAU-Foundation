"""Protocol C′ multigen — gen1 (3 arms) → transfer → gen2 (single measure).

Biology analogy: one life consolidates scars and engrams; the heir is born into
a fresh niche carrying only what earned transfer — then a short measurement
life reads whether lineage left a mark on prediction error.

Gen1 reuses Protocol C′ helpers (niche, seed lock, PE window, train, diversity).
Gen2 uses the same seed niche draw as the null arm (1A: fresh pool, not gen1's
continuing commons). Inheritance is memory + drift + retrieval_context only
(3A: no parent LoRA adapter load).

Gen2 metric (2A): single-phase precision-weighted mean PE over the PE window
(not a two-phase train ΔPE). Labeled with gen1_arm for groupby analysis.

Transfer (4A): consolidate_generation on gen1 phase-2 final state + the vault
kept across phase-1 and phase-2. apply_generation completes synchronously
before any gen2 graph stream.

Somatic-scale note: agent_node.apply_inherited_somatic_scale runs only when
state.delta_log is non-empty. Inherited threat/loss scaling is therefore
measurable from gen2 event 2 onward — not on the first event.

Mock mode (DAU_MULTIGEN_MOCK_LLM=1): patches graph._build_llm for
deterministic, API/GPU-free smoke. Real-backend pilots are out of scope here.
"""

from __future__ import annotations

import argparse
import json
import os
import statistics
import tempfile
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable

import dau.foundation.graph as graph_mod
from dau.diagnostics.run_protocol_c_prime import (
    AB_ENERGY_FLOOR,
    ARM_LIVED,
    ARM_NULL,
    ARM_ORDER,
    ARM_SHUFFLE,
    DIVERSITY_MIN_PE_GAP,
    EMPTY_COUNT,
    EMPTY_MEAN,
    LORA_ENABLED_ENV,
    NAN_DELTA,
    NLI_FILTER_ENABLED_ENV,
    PE_WINDOW_EVENTS,
    PI_DISTINCT_DECIMALS,
    STREAM_NODES_PER_EVENT,
    STREAM_RECURSION_HEADROOM,
    ArmResult,
    _build_lived_examples,
    _diversity_gate_reason,
    _initial_state,
    _json_sanitize,
    _lock_seeds,
    _merge_pe_rows,
    _pad_pe_list,
    _phase1_diversity,
    _pair_filter_report,
    _precision_audit_from_pe_rows,
    _train_adapter,
    TrainOutcome,
    _window_mean,
    describe_pe_window,
)
from dau.diagnostics.preflight import (
    Preflight,
    PreflightAbort,
    arm_digest,
    rng_state_digest,
    run_phase0,
    run_phase2,
    run_phase3,
    run_phase4_5,
)
from dau.diagnostics.tool_identity import (
    LORA_CHOICE_OFF,
    LORA_CHOICE_ON,
    build_tool_identity,
    resolve_lora_choice,
)
from dau.foundation.constraints import LANDMARK_EVENT, LORA_B_ABS_SUM_UNREAD
from dau.foundation.drift import DriftState
from dau.foundation.emotional_weight import (
    MARKER_REWARD,
    MARKER_THREAT,
    reset_somatic_scale_stats,
)
from dau.foundation.generation import (
    INHERITED_WARNING_KEY,
    SOMATIC_SCALE_KEY,
    GenerationRecord,
    apply_generation,
    consolidate_generation,
)
from dau.foundation.graph import (
    LLM_BACKEND_GROQ,
    build_graph,
    get_pe_event_log,
    reset_pe_event_log,
)
from dau.foundation.memory_bridge import consolidate_run
from dau.foundation.meta_observer import bind_memory_store, unbind_memory_store
from dau.foundation.polarity_filter import describe_polarity_filter
from dau.foundation.self_model import build_self_model, f_agent_inputs
from dau.foundation.state import DAUAgentState
from dau.generation.fitness import classify_fitness
from dau.memory.store import MemoryStore

# ---------------------------------------------------------------------------
# Multigen parameters (env / CLI; pre-reg not locked — keep parametric)
# ---------------------------------------------------------------------------

N_PAIRS: int = int(os.environ.get("DAU_MULTIGEN_N_PAIRS", "15"))
EVENTS_GEN1: int = int(os.environ.get("DAU_MULTIGEN_EVENTS_GEN1", "50"))
EVENTS_GEN2: int = int(os.environ.get("DAU_MULTIGEN_EVENTS_GEN2", "20"))
K_GEN2: int = int(os.environ.get("DAU_MULTIGEN_K_GEN2", "3"))
SEED_START: int = int(os.environ.get("DAU_MULTIGEN_SEED_START", "2001"))
PE_WINDOW_GEN2: int = int(
    os.environ.get("DAU_MULTIGEN_PE_WINDOW", str(PE_WINDOW_EVENTS))
)
MOCK_LLM_ENV: str = "DAU_MULTIGEN_MOCK_LLM"
MOCK_LLM_DEFAULT: str = "0"
RESULTS_PATH: Path = Path(
    os.environ.get(
        "DAU_MULTIGEN_RESULTS",
        "dau_runs/protocol_c_prime_multigen_results.json",
    )
)

PROTOCOL_ID: str = "C_PRIME_MULTIGEN"
HEIR_SUFFIX: str = "g2"
PARENT_SUFFIX: str = "g1"
# I4.1 replays a TRAINED arm: null was already deterministic under warn_only
# (no adapter matmul), so replaying it would have sailed past D-037's failure.
REPLAY_ARM: str = "replay"
REPLAY_OF_ARM: str = ARM_LIVED
# A gen1 arm lives twice on the same vault (before and after training), so its
# PE log holds two lives' worth of events; the heir lives once.
GEN1_PHASES: int = 2
UNKNOWN_COUNT: int = -1

# Per-life liveness samples for phase 5. Module-level because the values are
# only readable inside run_life_keep_vault's teardown, and threading a
# collector through run_multigen_pair → run_lineage → run_life_keep_vault
# would put plumbing in four signatures to carry two integers. The runner is
# single-threaded and run_cprime_multigen clears this at the start of a run.
LIFE_STATS: list[dict[str, Any]] = []
TMP_PREFIX: str = "dau_cprime_multigen_"

MOCK_DECISION_TEXTS: tuple[str, ...] = (
    "I cooperate and share resources carefully with others.",
    "I extract maximum resources for myself alone.",
    "I wait and observe the pool before acting.",
    "I trust this domain and cooperate with partners.",
    "I defect and take as much as possible right now.",
)

# Diversity gate for gen2 uses K_GEN2; pe_gap floor matches gen1.
GEN2_DIVERSITY_MIN_PE_GAP: float = DIVERSITY_MIN_PE_GAP

# S5 (gen2 behavioural endpoint). The audit row class written for a traumatic
# imprint, and the ordinal reported when the event never happened in a life —
# a life with no crisis must not read as "crisis on event 0".
DELTA_CLASS_TRAUMA: str = "TRAUMA"
EVENT_NEVER_OCCURRED: int = -1


# ---------------------------------------------------------------------------
# Result dataclasses
# ---------------------------------------------------------------------------


@dataclass
class BirthDriftLog:
    """Transfer-time channel diagnostics (pre-gen2, not PE-filtered)."""

    parent_agent_id: str
    heir_agent_id: str
    gen1_arm: str
    seed: int
    f_agent: float
    # Every input F_agent is computed from, recorded because the pilot
    # returned f_agent=0.000 and fitness_class="low" for all nine lineages
    # (D-034) and the score alone cannot say why.
    # F = 0.4*(E/E_max) + 0.3*(1 - (|dpool|/t_survived)/X_max) + 0.3*(t_survived/t_gen),
    # clamped to [0,1]. All four are kept because after K4-b (D-070) no single
    # one of them is redundant: the pool term is now a per-event rate, so it
    # cannot be read without t_survived, and t_generation stopped being a copy
    # of t_survived — which is what had pinned the survival term at exactly
    # 1.0 for every lineage this harness has ever scored.
    f_agent_energy_final: float
    f_agent_delta_pool: float
    f_agent_t_survived: float
    f_agent_t_generation: float
    fitness_class: str
    n_transfer_candidates: int
    inherited_memory_ids: list[str]
    n_inherited_warnings: int
    birth_drift_flags: dict[str, bool]
    birth_drift_magnitudes: dict[str, float]
    n_retrieval_context: int
    has_inherited_warning_marker: bool
    has_somatic_scale_marker: bool
    # S6 shadow (D-003): what would have transferred with the Layer-4 fitness
    # gate switched off. ⚠ Recorded here rather than as a fourth arm because
    # the primary endpoint cannot see F_agent at all: birth_drift_magnitudes
    # comes from GenerationRecord.inherited_drift, which is a straight copy of
    # the parent's drift, and select_for_transfer only ever reads drift. So
    # "f_agent=None, same test as the primary" is guaranteed identical by
    # construction; the channel F_agent does gate is which engrams transfer.
    f_agent_none_n_transfer_candidates: int = EMPTY_COUNT
    f_agent_none_inherited_memory_ids: list[str] = field(default_factory=list)
    f_agent_none_n_inherited_warnings: int = EMPTY_COUNT
    f_agent_none_inheritance_identical: bool = False


@dataclass
class Gen2Result:
    """Single-phase gen2 measurement labeled by gen1 arm."""

    seed: int
    gen1_arm: str
    heir_agent_id: str
    mean_pe: float  # 2A: single-phase window mean (labeled gen2 ΔPE in JSON)
    n_events: int
    n_unique: int
    pe_gap_max: float
    gated: bool
    gate_reason: str
    wall_seconds: float
    pe_list: list[float] = field(default_factory=list)
    # Precision audit over this heir's pe_event_log rows. Gen2 is where the
    # inheritance claim is read, and a saturated sensor reads "no difference"
    # exactly like a real null — so the heir needs its own instrument health,
    # not just gen1's (GAP-13).
    saturation_rate: float = EMPTY_MEAN
    pi_n_distinct: int = EMPTY_COUNT
    n_pe_events_audited: int = EMPTY_COUNT
    n_saturated: int = EMPTY_COUNT
    pi_values: list[float] = field(default_factory=list)
    # RNG fingerprint at the moment this heir's life starts. Recorded rather
    # than asserted so I4.2 can prove the gen2 lock is still in place in a
    # real run, not only under test (GAP-12).
    rng_digest: str = ""
    # S5 behavioural trace. B2 could not run S5 at all because none of this
    # reached the results file (L20): the gen2 block carried only the PE trace.
    # Raw per-event rows plus the two "how long until it happened" ordinals —
    # no summary statistic, because which statistic S5 uses is a
    # pre-registration decision, not this recorder's (2.7).
    extraction_by_event: list[float] = field(default_factory=list)
    pool_ratio_by_event: list[float] = field(default_factory=list)
    crisis_by_event: list[bool] = field(default_factory=list)
    n_crisis_events: int = EMPTY_COUNT
    # ⚠ Two readings of "events until the first trauma" (2.11): the commons
    # crisis that scars via apply_crisis_trauma, and the TRAUMA-class imprint
    # on the PE path. They are different events and the pre-registration line
    # does not say which one it means — so both are recorded and neither is
    # chosen here.
    events_to_first_crisis: int = EVENT_NEVER_OCCURRED
    events_to_first_delta_trauma: int = EVENT_NEVER_OCCURRED


@dataclass
class LineageResult:
    """One gen1 arm → transfer → gen2 heir for a seed."""

    seed: int
    gen1_arm: str
    gen1: dict[str, Any]
    transfer: dict[str, Any]
    gen2: dict[str, Any]
    # D-031: end-of-gen1 sleep. Reported because it changes what the heir
    # inherits — deletions included — and that reaches the primary endpoint
    # (birth-drift, D-002). An unreported consolidation would move gen2
    # numbers with nothing in the results file to attribute them to.
    consolidation: dict[str, Any] = field(default_factory=dict)


@dataclass
class MultigenPairResult:
    """Three lineages (lived/null/shuffle) for one seed."""

    seed: int
    lineages: list[LineageResult]
    # D-035 step 0, item 3. Whether the adapter changed any phase-2 decision,
    # counted against the untrained arm. Lives here rather than on a lineage
    # because it is a comparison BETWEEN the seed's arms.
    phase2_decision_divergence: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Mock LLM (smoke / unit path)
# ---------------------------------------------------------------------------


class _MockMsg:
    def __init__(self, content: str) -> None:
        self.content = content


class MockLLM:
    """Deterministic stand-in for ChatGroq.invoke — cycles decision texts."""

    def __init__(self, texts: tuple[str, ...] = MOCK_DECISION_TEXTS) -> None:
        self._texts = texts
        self.calls = 0

    def invoke(self, _messages: list[dict[str, str]]) -> _MockMsg:
        text = self._texts[self.calls % len(self._texts)]
        self.calls += 1
        return _MockMsg(text)


def mock_llm_enabled() -> bool:
    raw = os.environ.get(MOCK_LLM_ENV, MOCK_LLM_DEFAULT).strip()
    return raw in {"1", "true", "TRUE", "yes", "YES"}


def install_mock_llm() -> Callable[[], Any]:
    """Patch graph._build_llm; return previous builder for restore.

    The backend setdefault is not a default any more (D-018 made that
    local) — it states the mock's own requirement: the canned LLM is
    patched into _build_llm, which only the groq branch of agent_node
    calls. Left unset, the run would take the local branch and load the
    real model instead of the mock.
    """

    previous = graph_mod._build_llm
    mock = MockLLM()
    graph_mod._build_llm = lambda: mock  # type: ignore[assignment]
    os.environ.setdefault("DAU_LLM_BACKEND", LLM_BACKEND_GROQ)
    return previous


def restore_llm_builder(previous: Callable[[], Any]) -> None:
    graph_mod._build_llm = previous  # type: ignore[assignment]


# ---------------------------------------------------------------------------
# Life runner that keeps the vault (unlike _collect_pe_events)
# ---------------------------------------------------------------------------


def _state_from_stream(values: Any) -> DAUAgentState:
    if isinstance(values, DAUAgentState):
        return values
    if isinstance(values, dict):
        return DAUAgentState.model_validate(values)
    raise TypeError(f"Unexpected stream value type: {type(values)!r}")


def _open_lineage_store() -> tuple[MemoryStore, tempfile.TemporaryDirectory[str]]:
    tmp = tempfile.TemporaryDirectory(prefix=TMP_PREFIX)
    store = MemoryStore(
        chroma_path=os.path.join(tmp.name, "chroma"),
        sqlite_path=os.path.join(tmp.name, "memory.db"),
    )
    return store, tmp


def run_life_keep_vault(
    *,
    agent_id: str,
    seed: int,
    n_events: int,
    store: MemoryStore,
    initial: DAUAgentState | None = None,
    energy_floor: float = AB_ENERGY_FLOOR,
) -> tuple[list[float], list[Any], list[dict[str, Any]], DAUAgentState]:
    """Stream one life; keep MemoryStore bound for the caller (no close).

    When ``initial`` is provided (gen2 heir after apply_generation), that state
    is streamed as-is — inheritance must already be applied.
    """

    graph_mod.load_env_file()
    original_max = graph_mod.MAX_EVENTS
    original_floor = graph_mod.AB_ENERGY_FLOOR
    reset_pe_event_log()
    # Same lifetime as the PE buffer: drained by the caller after the stream
    # ends, so it must start empty or it would carry the previous life's rows.
    graph_mod.reset_pool_event_log()
    # Same lifetime and the same reason: the landmark is an ordinal within ONE
    # life, so a buffer carrying the previous life's rows would let event 10 be
    # read off the wrong agent.
    graph_mod.reset_body_event_log()

    try:
        graph_mod.MAX_EVENTS = int(n_events)
        graph_mod.AB_ENERGY_FLOOR = float(energy_floor)
        graph_mod._memory_stores[agent_id] = store
        graph_mod._memory_written[agent_id] = 0
        bind_memory_store(agent_id, store)

        start = initial if initial is not None else _initial_state(agent_id, seed)
        assert start.agent_id == agent_id
        stream_limit = n_events * STREAM_NODES_PER_EVENT + STREAM_RECURSION_HEADROOM
        result: Any = start
        app = build_graph(checkpointer=None)
        for values in app.stream(
            start,
            config={"recursion_limit": stream_limit},
            stream_mode="values",
        ):
            result = values

        state = _state_from_stream(result)
        pe_rows = list(get_pe_event_log())
        pe_list = [float(row["prediction_error"]) for row in pe_rows]
        pe_list = _pad_pe_list(pe_list, n_events)
        lived_examples = _build_lived_examples(state, pe_rows)
        # GAP-19 / D-067: this life is over, so the vault's clock moves past it
        # and the next life on the same vault counts on top. Sealed with the
        # events actually lived rather than the budget — since D-066 a life can
        # end early, and sealing with n_events would age the vault by time the
        # agent never had.
        store.seal_phase(len(state.event_log))
        return pe_list, lived_examples, pe_rows, state
    finally:
        # Liveness sample taken here because the finally below drops
        # _memory_written and the caller closes the vault: after this point
        # neither number can be recovered (I5.1, I5.3).
        LIFE_STATS.append(
            {
                "agent_id": agent_id,
                "memory_written": int(graph_mod._memory_written.get(agent_id, 0)),
                "memory_edges": _count_edges(store),
            }
        )
        unbind_memory_store(agent_id)
        graph_mod._memory_stores.pop(agent_id, None)
        graph_mod._memory_written.pop(agent_id, None)
        graph_mod.MAX_EVENTS = original_max
        graph_mod.AB_ENERGY_FLOOR = original_floor


def _decisions(state: Any) -> list[str]:
    """Decision texts in order, for the I2.1 arm digest."""

    events = getattr(state, "event_log", None) or []
    decisions: list[str] = []
    for event in events:
        payload = getattr(event, "payload", None)
        if not isinstance(payload, dict):
            continue
        decision = payload.get("decision")
        if decision is not None:
            decisions.append(str(decision))
    return decisions


DECISION_HASH_CHARS: int = 12


def _decision_hashes(state: Any) -> list[str]:
    """Per-event fingerprints of one life's decisions (D-035).

    Built from _decisions so the fingerprints cover exactly what the arm
    digest covers — a second reader of the event log could drift from it and
    then the two would disagree about what "the decisions" were.
    """

    import hashlib

    return [
        hashlib.sha256(text.encode("utf-8")).hexdigest()[:DECISION_HASH_CHARS]
        for text in _decisions(state)
    ]


def _phase2_decision_divergence(gen1_by_arm: dict[str, dict]) -> dict[str, Any]:
    """How many phase-2 events each trained arm decided differently from NULL.

    NULL is the reference because it is the one arm with no adapter, and
    phase 1 is identical across arms by construction, so a difference here is
    the adapter's doing. ``None`` when the traces are not comparable — a
    length mismatch means an arm ended early, and zipping them would invent
    agreement that was never observed.
    """

    report: dict[str, Any] = {"reference_arm": ARM_NULL}
    ref = list((gen1_by_arm.get(ARM_NULL) or {}).get("phase2_decision_hashes") or [])
    report["n_phase2_events"] = len(ref)
    for arm_name, gen1 in gen1_by_arm.items():
        if arm_name == ARM_NULL:
            continue
        hashes = list((gen1 or {}).get("phase2_decision_hashes") or [])
        report[f"n_differing_{arm_name}"] = (
            sum(1 for a, b in zip(hashes, ref) if a != b)
            if ref and len(hashes) == len(ref)
            else None
        )
    return report


def _adapter_present(agent_id: str) -> bool:
    """Whether this agent has an adapter on disk (I2.2)."""

    try:
        from dau.foundation.local_llm import adapter_exists
    except ImportError:
        return False
    try:
        return bool(adapter_exists(agent_id))
    except Exception:  # noqa: BLE001 — a probe must not kill the run
        return False


def _count_edges(store: Any) -> int:
    """Edge count for a live store, or -1 when it cannot be read.

    -1 rather than 0: an unreadable store is not an empty graph, and I5.1
    exists precisely to tell "found nothing" from "never ran".
    """

    counter = getattr(store, "count_edges", None)
    if counter is None:
        return UNKNOWN_COUNT
    try:
        return int(counter())
    except Exception:  # noqa: BLE001 — a closed store must not kill the life
        return UNKNOWN_COUNT


def import_time_bindings() -> list[tuple[str, Any, str, Any]]:
    """Module constants captured at import, with the env var each came from.

    I0.5 compares these against the environment as it stands now. Anything
    changed after import is silently ignored by the module that read it, so
    the run would use one setting while a later reader saw another.
    """

    return [
        ("N_PAIRS", N_PAIRS, "DAU_MULTIGEN_N_PAIRS", int),
        ("EVENTS_GEN1", EVENTS_GEN1, "DAU_MULTIGEN_EVENTS_GEN1", int),
        ("EVENTS_GEN2", EVENTS_GEN2, "DAU_MULTIGEN_EVENTS_GEN2", int),
        ("K_GEN2", K_GEN2, "DAU_MULTIGEN_K_GEN2", int),
        ("SEED_START", SEED_START, "DAU_MULTIGEN_SEED_START", int),
        ("PE_WINDOW_GEN2", PE_WINDOW_GEN2, "DAU_MULTIGEN_PE_WINDOW", int),
    ]


def parent_agent_id(arm: str, seed: int) -> str:
    return f"cprime-{arm}-{seed}-{PARENT_SUFFIX}"


def _run_replay_arm(
    results: list[MultigenPairResult],
    *,
    events_gen1: int,
    skip: bool,
) -> dict[str, Any] | None:
    """I4.1: re-run the first seed's lived arm and hand back both digests.

    Runs last, after every seed and heir is finished, so nothing downstream
    can consume the replay's adapter. Costs one arm — ~7 min, which is 12% of
    an N=3 run and 2% of an N=15 one.
    """

    if skip or not results:
        return None
    seed = int(results[0].seed)
    agent_id = replay_agent_id(seed)
    recorded = ""
    for lineage in results[0].lineages:
        if str(lineage.gen1.get("arm")) == REPLAY_OF_ARM:
            recorded = str(lineage.gen1.get("arm_digest", ""))
            break

    print(
        f"[MULTIGEN][I4.1] replaying seed={seed} arm={REPLAY_OF_ARM} "
        f"as {agent_id} …",
        flush=True,
    )
    arm_result, _state, _store, tmp = run_gen1_arm_lineage(
        seed=seed,
        arm=REPLAY_OF_ARM,
        events_gen1=events_gen1,
        agent_id=agent_id,
    )
    tmp.cleanup()
    replay = {
        "seed": seed,
        "arm": REPLAY_OF_ARM,
        "agent_id": agent_id,
        "recorded_digest": recorded,
        "replay_digest": arm_result.arm_digest,
    }
    verdict = "identical" if recorded == arm_result.arm_digest else "DIVERGED"
    print(f"[MULTIGEN][I4.1] {verdict}", flush=True)
    return replay


def replay_agent_id(seed: int) -> str:
    """I4.1's arm. A separate id so the replay starts with no adapter on disk.

    Re-using the original id would make the replay load the adapter the first
    pass just wrote, so phase-1 would run adapted where the original ran bare
    and the digests would differ for a reason that is not non-determinism.
    Still matches AGENT_ID_SEED_PATTERN, so I0.4 can verify it like any other.
    """

    return f"cprime-{REPLAY_ARM}-{seed}-{PARENT_SUFFIX}"


def heir_agent_id(arm: str, seed: int) -> str:
    return f"cprime-{arm}-{seed}-{HEIR_SUFFIX}"


def _gen2_diversity_gate_reason(n_unique: int, pe_gap_max: float, k_gen2: int) -> str:
    if n_unique < k_gen2:
        return f"n_unique={n_unique} < K_GEN2={k_gen2}"
    if pe_gap_max < GEN2_DIVERSITY_MIN_PE_GAP:
        return (
            f"pe_gap_max={pe_gap_max:.6g} < "
            f"GEN2_DIVERSITY_MIN_PE_GAP={GEN2_DIVERSITY_MIN_PE_GAP}"
        )
    return ""


# ---------------------------------------------------------------------------
# Transfer (synchronous; before any gen2 invoke)
# ---------------------------------------------------------------------------


def transfer_to_heir(
    *,
    parent_state: DAUAgentState,
    memory_store: MemoryStore,
    seed: int,
    gen1_arm: str,
    events_gen1: int,
) -> tuple[DAUAgentState, GenerationRecord, BirthDriftLog]:
    """Consolidate parent → birth heir with apply_generation (pre-invoke).

    Ordering guarantee: apply_generation returns before this function returns;
    callers must not stream the heir graph until after this returns.

    ``events_gen1`` is F_agent's survival denominator (K4-b). It is passed in
    rather than read from graph.MAX_EVENTS the way meta_observer_node does,
    because run_life_keep_vault restores that global in its finally block —
    by the time we get here it holds the module default again, not the budget
    the life was actually run against.
    """

    # GAP-12: this runs after gen1 training, so the incoming RNG state is
    # arm-dependent. Birth-drift is the primary endpoint (D-002) and no code on
    # this path draws from RNG today — the lock keeps that true by construction
    # rather than by grep.
    _lock_seeds(seed)

    self_model = build_self_model(parent_state, events_gen1)
    f_agent = float(self_model.f_agent)
    # Read through the same helper _resolve_f_agent uses, so the report cannot
    # drift from the score it explains (CLAUDE.md 2.8).
    f_inputs = f_agent_inputs(parent_state, events_gen1)
    f_agent_energy = float(f_inputs["energy_final"])
    f_agent_dpool = float(f_inputs["delta_pool"])
    f_agent_t_survived = float(f_inputs["t_survived"])
    f_agent_t_generation = float(f_inputs["t_generation"])
    reward = float(self_model.emotional_weight.somatic_markers.get(MARKER_REWARD, 0.0))
    threat = float(self_model.emotional_weight.somatic_markers.get(MARKER_THREAT, 0.0))

    record = consolidate_generation(
        parent_state,
        memory_store,
        f_agent=f_agent,
        reward_marker=reward,
        threat_marker=threat,
    )

    # S6 shadow, taken after the real record so nothing it touches can reach
    # the transfer that counts. Read-only against the vault: the candidate
    # builder only lists nodes and scores them, and select_for_transfer works
    # on freshly built candidate objects — so this costs a pass over the
    # vault, not a fourth arm.
    shadow = consolidate_generation(
        parent_state,
        memory_store,
        f_agent=None,
        reward_marker=reward,
        threat_marker=threat,
    )

    heir_id = heir_agent_id(gen1_arm, seed)
    # 1A: fresh niche via _seed_niche(seed) — not gen1's continuing pool.
    heir_blank = _initial_state(heir_id, seed)
    assert heir_blank.event_log == []
    assert heir_blank.delta_log == []

    # --- synchronous inheritance (must complete before any gen2 stream) ---
    heir = apply_generation(heir_blank, record, memory_store)
    assert heir.generation_record is record
    assert heir.agent_id == heir_id
    # ---------------------------------------------------------------------

    drift = heir.drift_state
    if not isinstance(drift, DriftState):
        drift = DriftState()
    has_warning = any(
        isinstance(e, dict) and e.get(INHERITED_WARNING_KEY) is True
        for e in heir.retrieval_context
    )
    has_scale = any(
        isinstance(e, dict) and SOMATIC_SCALE_KEY in e for e in heir.retrieval_context
    )
    birth = BirthDriftLog(
        parent_agent_id=str(parent_state.agent_id),
        heir_agent_id=heir_id,
        gen1_arm=gen1_arm,
        seed=seed,
        f_agent=f_agent,
        f_agent_energy_final=f_agent_energy,
        f_agent_delta_pool=f_agent_dpool,
        f_agent_t_survived=f_agent_t_survived,
        f_agent_t_generation=f_agent_t_generation,
        fitness_class=classify_fitness(f_agent),
        n_transfer_candidates=len(record.inherited_memories),
        inherited_memory_ids=list(record.inherited_memories),
        n_inherited_warnings=len(record.inherited_warning_ids),
        birth_drift_flags=dict(drift.flags),
        birth_drift_magnitudes=dict(drift.magnitudes),
        n_retrieval_context=len(heir.retrieval_context),
        has_inherited_warning_marker=has_warning,
        has_somatic_scale_marker=has_scale,
        f_agent_none_n_transfer_candidates=len(shadow.inherited_memories),
        f_agent_none_inherited_memory_ids=list(shadow.inherited_memories),
        f_agent_none_n_inherited_warnings=len(shadow.inherited_warning_ids),
        f_agent_none_inheritance_identical=(
            list(shadow.inherited_memories) == list(record.inherited_memories)
            and list(shadow.inherited_warning_ids) == list(record.inherited_warning_ids)
        ),
    )
    print(
        f"[MULTIGEN][TRANSFER] {parent_state.agent_id} → {heir_id} "
        f"arm={gen1_arm} n_transfer={birth.n_transfer_candidates} "
        f"f_agent={f_agent:.3f} (E={f_agent_energy:.3f} "
        f"|dpool|={abs(f_agent_dpool):.1f}) "
        f"warnings={birth.n_inherited_warnings} "
        f"drift_flags={birth.birth_drift_flags}",
        flush=True,
    )
    return heir, record, birth


# ---------------------------------------------------------------------------
# Gen1 arm (phase-1 → train? → phase-2 on same vault) + gen2 measure
# ---------------------------------------------------------------------------


def run_gen1_arm_lineage(
    *,
    seed: int,
    arm: str,
    events_gen1: int,
    agent_id: str | None = None,
) -> tuple[ArmResult, DAUAgentState, MemoryStore, tempfile.TemporaryDirectory[str]]:
    """Full gen1 arm keeping one MemoryStore across phase-1 and phase-2.

    ``agent_id`` is overridable for the I4.1 replay only. It must not reach the
    prompt — it does not; the id is used for the adapter directory and the
    checkpoint path, never for AgentView — so a replay under a different id
    decides identically and its digest is comparable.
    """

    started = time.perf_counter()
    agent_id = agent_id or parent_agent_id(arm, seed)
    _lock_seeds(seed)
    store, tmp = _open_lineage_store()

    pe_before_list, lived_examples, pe_rows_1, state_1 = run_life_keep_vault(
        agent_id=agent_id,
        seed=seed,
        n_events=events_gen1,
        store=store,
        initial=None,
    )
    pe_before = _window_mean(pe_before_list)
    n_unique, pe_gap_max = _phase1_diversity(lived_examples)

    # null never trains, and a diversity-gated arm skips train too — in both
    # cases nothing about the step was ever read, which is not the same as a
    # step that ran and did nothing. TrainOutcome's defaults carry that
    # distinction, so an untrained arm keeps the unread sentinels.
    outcome = TrainOutcome(EMPTY_COUNT, EMPTY_COUNT, LORA_B_ABS_SUM_UNREAD)
    gated = False
    gate_reason = ""

    if arm in {ARM_LIVED, ARM_SHUFFLE}:
        gate_reason = _diversity_gate_reason(n_unique, pe_gap_max)
        if gate_reason:
            gated = True
            print(
                f"[MULTIGEN] {agent_id}: diversity gate — {gate_reason} "
                f"(skip train; phase-2 still runs for transfer)",
                flush=True,
            )
        else:
            outcome = _train_adapter(
                agent_id,
                lived_examples,
                shuffled=(arm == ARM_SHUFFLE),
            )

    # Phase-2: fresh body + same seed niche, SAME vault (4A material).
    _lock_seeds(seed)
    pe_after_list, _, pe_rows_2, state_2 = run_life_keep_vault(
        agent_id=agent_id,
        seed=seed,
        n_events=events_gen1,
        store=store,
        initial=None,
    )
    # Drained here, before anything else can start a life and reset the buffer
    # (same rule as the S5 pool rows, L20). Phase 2 and not phase 1: the arms
    # are identical until the adapter is trained, and this is the life the
    # transferred drift comes from — so the landmark is a cross-section of the
    # same life the primary endpoint has always been read off.
    landmark = _landmark_reading(
        graph_mod.get_body_event_log(),
        len(state_2.event_log),
    )
    pe_after = _window_mean(pe_after_list)
    delta_pe = NAN_DELTA if gated else (pe_after - pe_before)

    # GAP-13: Protocol C′ audits both phases (run_protocol_c_prime.py:874);
    # multigen dropped the rows on the floor and shipped default zeros, which
    # read as "no saturation" when they mean "never measured".
    sat, pi_n, pi_vals, n_aud, n_sat = _precision_audit_from_pe_rows(
        _merge_pe_rows(pe_rows_1, pe_rows_2)
    )

    arm_result = ArmResult(
        seed=seed,
        arm=arm,
        pe_before=pe_before,
        pe_after=pe_after,
        delta_pe=delta_pe,
        n_events=events_gen1,
        n_pairs_trained=outcome.n_pairs_trained,
        n_pairs_rejected=outcome.n_pairs_rejected,
        wall_seconds=float(time.perf_counter() - started),
        gated=gated,
        gate_reason=gate_reason,
        n_unique=n_unique,
        pe_gap_max=pe_gap_max,
        saturation_rate=sat,
        pi_n_distinct=pi_n,
        n_pe_events_audited=n_aud,
        n_saturated=n_sat,
        pi_values=list(pi_vals),
        events_lived=len(state_2.event_log),
        **landmark,
        arm_digest=arm_digest(
            _decisions(state_1) + _decisions(state_2),
            list(pe_before_list) + list(pe_after_list),
        ),
        phase2_decision_hashes=_decision_hashes(state_2),
        pe_before_list=list(pe_before_list),
        pe_after_list=list(pe_after_list),
        adapter_present=_adapter_present(agent_id),
        lora_b_abs_sum_delta=outcome.lora_b_abs_sum_delta,
        dpo_loss=outcome.dpo_loss,
        dpo_optimizer_steps=outcome.dpo_optimizer_steps,
        dpo_grad_norm_min=outcome.dpo_grad_norm_min,
        dpo_clipped_steps=outcome.dpo_clipped_steps,
        dpo_delta_logp_chosen=outcome.dpo_delta_logp_chosen,
        dpo_delta_logp_rejected=outcome.dpo_delta_logp_rejected,
        dpo_chosen_went_down=outcome.dpo_chosen_went_down,
    )
    return arm_result, state_2, store, tmp


def _first_ordinal(flags: list[bool]) -> int:
    """1-based position of the first True, or EVENT_NEVER_OCCURRED.

    Position in the life, not ``event_counter``: the two coincide for a heir
    (its event log starts empty) but only the position stays meaningful if a
    life ever begins mid-counter.
    """

    for index, flag in enumerate(flags):
        if flag:
            return index + 1
    return EVENT_NEVER_OCCURRED


def _landmark_reading(
    body_rows: list[dict[str, Any]],
    events_lived: int,
) -> dict[str, Any]:
    """Read one life at a fixed AGE, plus its energy averaged over that life.

    K1/K2/K5 (D-070). Since D-066 lifespans differ by arm, so an end-of-life
    reading answers two questions at once — how the arm changed the agent, and
    how long the agent lasted — and the second one drowns the first (K4-b found
    the same confound inside F_agent's pool term). Reading every lineage at
    LANDMARK_EVENT makes the arms comparable at the cost of a narrower claim:
    what is compared is a cross-section, not the whole life. That limit gets
    declared in the second pre-registration.

    The mean over events IS the time integral divided by lifespan here: event
    ordinals are unit-spaced by construction (EventClock ticks by one), and
    each row holds the energy that event left standing until the next one.

    Two failure modes, both loud (§2.9):

    * the life reached the landmark but no row exists — impossible unless the
      instrumentation broke, so it aborts rather than reporting a hole;
    * the life ended before the landmark — cannot happen while death is
      suspended through METABOLIC_GRACE_EVENTS, but the rule is written anyway
      so that moving grace cannot retire it in silence. Reports NaN, never a
      substituted value from another ordinal.
    """

    by_counter = {int(row["event_counter"]): row for row in body_rows}
    row = by_counter.get(LANDMARK_EVENT)
    energies = [float(row["energy"]) for row in body_rows]
    energy_mean = float(statistics.fmean(energies)) if energies else NAN_DELTA

    if row is None:
        if events_lived >= LANDMARK_EVENT:
            raise SystemExit(
                f"[LANDMARK] life ran {events_lived} events but no body row "
                f"for event {LANDMARK_EVENT}; recorded ordinals: "
                f"{sorted(by_counter)}"
            )
        print(
            f"[LANDMARK][WARN] life ended at event {events_lived}, before the "
            f"landmark at {LANDMARK_EVENT} — reading unavailable, not imputed",
            flush=True,
        )
        return {
            "landmark_reached": False,
            "landmark_energy": NAN_DELTA,
            "landmark_drift_flags": {},
            "landmark_drift_magnitudes": {},
            "energy_mean_over_life": energy_mean,
        }

    return {
        "landmark_reached": True,
        "landmark_energy": float(row["energy"]),
        "landmark_drift_flags": dict(row["drift_flags"]),
        "landmark_drift_magnitudes": dict(row["drift_magnitudes"]),
        "energy_mean_over_life": energy_mean,
    }


def _s5_behaviour(
    pool_rows: list[dict[str, Any]],
    pe_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    """S5's raw behavioural trace for one life — recording only, no statistic."""

    crisis = [bool(row["crisis"]) for row in pool_rows]
    trauma = [str(row.get("delta_class", "")) == DELTA_CLASS_TRAUMA for row in pe_rows]
    return {
        "extraction_by_event": [float(row["extraction"]) for row in pool_rows],
        "pool_ratio_by_event": [float(row["pool_ratio"]) for row in pool_rows],
        "crisis_by_event": crisis,
        "n_crisis_events": sum(crisis),
        "events_to_first_crisis": _first_ordinal(crisis),
        "events_to_first_delta_trauma": _first_ordinal(trauma),
    }


def run_gen2_measure(
    *,
    heir: DAUAgentState,
    store: MemoryStore,
    seed: int,
    gen1_arm: str,
    events_gen2: int,
    k_gen2: int,
    pe_window: int,
) -> Gen2Result:
    """Single-phase PE measure on the heir (fresh LoRA weights — no adapter)."""

    started = time.perf_counter()
    # GAP-12: lived/shuffle just ran DPO and consumed torch RNG, null did not,
    # and shuffle also drew from Python RNG when permuting pairs. Without this
    # lock the three heirs enter gen2 from three different RNG states, and the
    # arm contrast carries an RNG contrast inside it.
    _lock_seeds(seed)
    rng_digest = rng_state_digest()
    # 3A: do not load parent adapter; heir agent_id has no trained adapter.
    pe_list, lived_examples, pe_rows, _final = run_life_keep_vault(
        agent_id=heir.agent_id,
        seed=seed,
        n_events=events_gen2,
        store=store,
        initial=heir,
    )
    # Drained after the stream, before anything else can start a life and
    # reset the buffer (S5, L20).
    behaviour = _s5_behaviour(graph_mod.get_pool_event_log(), pe_rows)
    mean_pe = _window_mean(pe_list, window=pe_window)
    n_unique, pe_gap_max = _phase1_diversity(lived_examples)
    gate_reason = _gen2_diversity_gate_reason(n_unique, pe_gap_max, k_gen2)
    gated = bool(gate_reason)
    sat, pi_n, pi_vals, n_aud, n_sat = _precision_audit_from_pe_rows(pe_rows)
    return Gen2Result(
        seed=seed,
        gen1_arm=gen1_arm,
        heir_agent_id=str(heir.agent_id),
        mean_pe=mean_pe,
        n_events=events_gen2,
        n_unique=n_unique,
        pe_gap_max=pe_gap_max,
        gated=gated,
        gate_reason=gate_reason,
        wall_seconds=float(time.perf_counter() - started),
        pe_list=list(pe_list),
        saturation_rate=sat,
        pi_n_distinct=pi_n,
        n_pe_events_audited=n_aud,
        n_saturated=n_sat,
        pi_values=list(pi_vals),
        rng_digest=rng_digest,
        **behaviour,
    )


def _consolidate_gen1(
    *,
    agent_id: str,
    state: DAUAgentState,
    store: MemoryStore,
) -> dict[str, Any]:
    """End-of-gen1 sleep consolidation; returns the lab report (D-031).

    The demo path has always done this at end of run (graph.py:1433); the
    experiment path streamed the graph directly and never reached it, so on
    this path forgetting never ran either (GAP-14, D-022). Failure is loud:
    a silently skipped consolidation would leave the heir inheriting an
    unconsolidated vault while the results file said otherwise.
    """

    counter = len(state.event_log)
    report = consolidate_run(agent_id, counter, store)
    payload = {
        "ran": True,
        "now_counter": counter,
        "deleted_count": int(report.deleted_count),
        "strengthened_count": int(report.strengthened_count),
        "edges_created": int(report.edges_created),
        "drift_flag_count": int(report.drift_flag_count),
    }
    print(
        f"[CONSOLIDATE] {agent_id}: deleted={payload['deleted_count']} "
        f"strengthened={payload['strengthened_count']} "
        f"edges={payload['edges_created']} at counter={counter}",
        flush=True,
    )
    return payload


def run_lineage(
    *,
    seed: int,
    arm: str,
    events_gen1: int,
    events_gen2: int,
    k_gen2: int,
    pe_window_gen2: int,
) -> LineageResult:
    """Gen1 arm → sync transfer → gen2 measure; vault closed after."""

    store: MemoryStore | None = None
    tmp: tempfile.TemporaryDirectory[str] | None = None
    try:
        gen1, parent_final, store, tmp = run_gen1_arm_lineage(
            seed=seed,
            arm=arm,
            events_gen1=events_gen1,
        )
        # D-031 / GAP-14: end-of-gen1 sleep, before the heir is built.
        #
        # After phase-2, not between the phases. delta_pe = pe_after -
        # pe_before is designed to isolate the training step, and the NULL
        # arm never trains — so a consolidation sitting between the phases
        # would give the control a non-zero delta_pe made entirely of
        # forgetting. The control would stop being able to measure the zero
        # it exists to measure.
        consolidation = _consolidate_gen1(
            agent_id=parent_agent_id(arm, seed),
            state=parent_final,
            store=store,
        )

        # Transfer BEFORE any gen2 invoke (ordering asserted inside).
        heir, _record, birth = transfer_to_heir(
            parent_state=parent_final,
            memory_store=store,
            seed=seed,
            gen1_arm=arm,
            events_gen1=events_gen1,
        )
        # Birth-drift logged at transfer time — independent of gen2 PE.
        gen2 = run_gen2_measure(
            heir=heir,
            store=store,
            seed=seed,
            gen1_arm=arm,
            events_gen2=events_gen2,
            k_gen2=k_gen2,
            pe_window=pe_window_gen2,
        )
        return LineageResult(
            seed=seed,
            gen1_arm=arm,
            gen1=asdict(gen1),
            transfer=asdict(birth),
            gen2=asdict(gen2),
            consolidation=consolidation,
        )
    finally:
        if store is not None:
            try:
                store.close()
            except Exception:
                pass
        if tmp is not None:
            try:
                tmp.cleanup()
            except Exception:
                pass


def run_multigen_pair(
    seed: int,
    *,
    events_gen1: int = EVENTS_GEN1,
    events_gen2: int = EVENTS_GEN2,
    k_gen2: int = K_GEN2,
    pe_window_gen2: int = PE_WINDOW_GEN2,
) -> MultigenPairResult:
    """Lived / null / shuffle lineages for one seed."""

    lineages: list[LineageResult] = []
    for arm in ARM_ORDER:
        print(
            f"[MULTIGEN] seed={seed} arm={arm} "
            f"events_gen1={events_gen1} events_gen2={events_gen2}",
            flush=True,
        )
        lineages.append(
            run_lineage(
                seed=seed,
                arm=arm,
                events_gen1=events_gen1,
                events_gen2=events_gen2,
                k_gen2=k_gen2,
                pe_window_gen2=pe_window_gen2,
            )
        )
    divergence = _phase2_decision_divergence(
        {ln.gen1_arm: ln.gen1 for ln in lineages}
    )
    print(
        f"[MULTIGEN] seed={seed} phase-2 decisions differing from "
        f"{ARM_NULL}: " + ", ".join(
            f"{name.removeprefix('n_differing_')}={value}"
            for name, value in divergence.items()
            if name.startswith("n_differing_")
        ) + f" (of {divergence['n_phase2_events']} events)",
        flush=True,
    )
    return MultigenPairResult(
        seed=seed,
        lineages=lineages,
        phase2_decision_divergence=divergence,
    )


def run_cprime_multigen(
    *,
    n_pairs: int = N_PAIRS,
    seed_start: int = SEED_START,
    events_gen1: int = EVENTS_GEN1,
    events_gen2: int = EVENTS_GEN2,
    k_gen2: int = K_GEN2,
    pe_window_gen2: int = PE_WINDOW_GEN2,
    mock_llm: bool | None = None,
    lora: bool | None = None,
    preflight: Preflight | None = None,
) -> list[MultigenPairResult]:
    """Run N seeds × 3 arms through gen1 → transfer → gen2.

    ``lora`` must be stated: True trains, False deliberately does not, and
    None exits (GAP-1 — the default was off and nothing said so out loud).

    ``preflight`` collects the invariant verdicts. Pass the same object to
    the results writer; phase 0 runs here and aborts before any GPU work.
    """

    use_mock = mock_llm_enabled() if mock_llm is None else bool(mock_llm)
    lora_choice = resolve_lora_choice(lora, mock=use_mock)
    print(f"[MULTIGEN] lora={lora_choice}", flush=True)
    if lora_choice == LORA_CHOICE_OFF:
        print(
            "[MULTIGEN][WARN] LoRA training is OFF — the three arms differ "
            "only in bookkeeping, not in weights. Any arm contrast from this "
            "run is not evidence about lived experience.",
            flush=True,
        )

    seeds = list(range(seed_start, seed_start + n_pairs))
    gate = preflight if preflight is not None else Preflight(mock=use_mock)
    gate.mock = use_mock
    # Liveness counters are per-run, not per-process: a previous run's counts
    # would let a component that never fired this time still look alive.
    LIFE_STATS.clear()
    reset_somatic_scale_stats()
    # Lock before checking I0.6: the check reports the determinism state the
    # run will have, it does not create it.
    _lock_seeds(seed_start)
    run_phase0(
        gate,
        tool_identity=build_tool_identity(lora_choice=lora_choice, seeds=seeds),
        agent_ids=[
            fn(arm, seed)
            for seed in seeds
            for arm in ARM_ORDER
            for fn in (parent_agent_id, heir_agent_id)
        ]
        # I4.1's arm is a real agent that will exist, so I0.4 verifies its id
        # derives the right seed like every other — an unparseable replay id
        # would only surface hours later, at the replay.
        + [replay_agent_id(seeds[0])],
        seeds=seeds,
        import_time_bindings=import_time_bindings(),
    )
    gate.enforce()

    previous_builder: Callable[[], Any] | None = None
    if use_mock:
        previous_builder = install_mock_llm()
        print("[MULTIGEN] mock LLM installed", flush=True)

    results: list[MultigenPairResult] = []
    try:
        for seed in seeds:
            results.append(
                run_multigen_pair(
                    seed,
                    events_gen1=events_gen1,
                    events_gen2=events_gen2,
                    k_gen2=k_gen2,
                    pe_window_gen2=pe_window_gen2,
                )
            )
        # Inside the try so the replay sees the same LLM the run used; a mock
        # replays trivially, so it is skipped rather than asserted.
        replay = _run_replay_arm(
            results,
            events_gen1=events_gen1,
            skip=use_mock,
        )
    finally:
        if previous_builder is not None:
            restore_llm_builder(previous_builder)

    # Phase 3 reads the finished run, so it cannot abort it — every check is
    # FLAG and lands as a label on the results instead.
    gen1_sections = [lin.gen1 for pair in results for lin in pair.lineages]
    gen2_sections = [lin.gen2 for pair in results for lin in pair.lineages]
    run_phase3(
        gate,
        gen1_sections=gen1_sections,
        gen2_sections=gen2_sections,
        # Gen1 runs two phases on the same arm; gen2 runs one.
        expected_gen1=events_gen1 * GEN1_PHASES,
        expected_gen2=events_gen2,
        gen1_audit=_precision_audit_totals(gen1_sections),
        gen2_audit=_precision_audit_totals(gen2_sections),
    )
    run_phase2(
        gate,
        gen1_sections=gen1_sections,
        lora_enabled=(lora_choice == LORA_CHOICE_ON),
        # Read here rather than passed down from the arms: these are run-wide
        # counters, and every arm plus the replay has finished by now, so this
        # is the same snapshot write_multigen_results_json will record.
        pair_filter=_pair_filter_report(),
    )
    run_phase4_5(
        gate,
        gen2_sections=gen2_sections,
        life_stats=list(LIFE_STATS),
        replay=replay,
    )
    # I4.2 is ABORT and can only be judged once the heirs have run: a lineage
    # whose arms entered gen2 from different RNG states has no separable arm
    # contrast, so it must not be written as a result.
    gate.enforce()
    return results


def _precision_audit_totals(sections: list[dict[str, Any]]) -> dict[str, Any]:
    """Pool the per-section precision audit into one readable block.

    Descriptive only — no pass/fail. The thresholds this will be judged
    against (SATURATION_MAX, PI_N_DISTINCT_MIN) are still uncalibrated, and
    I3.2 assigns the verdict to the preflight gate, not to the writer of the
    numbers. Counting here and judging there keeps an uncalibrated threshold
    from being locked in by accident.
    """

    n_events = sum(int(s.get("n_pe_events_audited", 0)) for s in sections)
    n_saturated = sum(int(s.get("n_saturated", 0)) for s in sections)
    all_pi: list[float] = []
    for section in sections:
        all_pi.extend(float(value) for value in section.get("pi_values", []))
    return {
        "n_pe_events_audited": n_events,
        "n_saturated": n_saturated,
        "saturation_rate": (
            float(n_saturated) / float(n_events) if n_events > 0 else EMPTY_MEAN
        ),
        "pi_n_distinct": len(
            {round(value, PI_DISTINCT_DECIMALS) for value in all_pi}
        ),
    }


def _summary(results: list[MultigenPairResult]) -> dict[str, Any]:
    """Lightweight aggregate: gen2 mean_pe by gen1_arm (no claim tests)."""

    by_arm: dict[str, list[float]] = {arm: [] for arm in ARM_ORDER}
    n_transfer_total = EMPTY_COUNT
    for pair in results:
        for lineage in pair.lineages:
            arm = lineage.gen1_arm
            gen2 = lineage.gen2
            if not gen2.get("gated", False):
                by_arm.setdefault(arm, []).append(float(gen2["mean_pe"]))
            n_transfer_total += int(lineage.transfer.get("n_transfer_candidates", 0))

    def _arm_mean(values: list[float]) -> float:
        return float(statistics.mean(values)) if values else EMPTY_MEAN

    return {
        "n_seeds": len(results),
        "n_lineages": sum(len(p.lineages) for p in results),
        "n_transfer_candidates_total": n_transfer_total,
        "mean_gen2_pe_by_gen1_arm": {
            arm: _arm_mean(by_arm.get(arm, [])) for arm in ARM_ORDER
        },
        "n_usable_gen2_by_gen1_arm": {
            arm: len(by_arm.get(arm, [])) for arm in ARM_ORDER
        },
        "precision_audit": {
            "gen1": _precision_audit_totals(
                [lin.gen1 for pair in results for lin in pair.lineages]
            ),
            "gen2": _precision_audit_totals(
                [lin.gen2 for pair in results for lin in pair.lineages]
            ),
        },
    }


def write_multigen_results_json(
    results: list[MultigenPairResult],
    *,
    lora_choice: str,
    preflight: Preflight,
    path: Path | None = None,
    events_gen1: int = EVENTS_GEN1,
    events_gen2: int = EVENTS_GEN2,
    k_gen2: int = K_GEN2,
    n_pairs: int = N_PAIRS,
    seed_start: int = SEED_START,
    pe_window_gen2: int = PE_WINDOW_GEN2,
) -> Path:
    """Persist gen1 / transfer / gen2 sections in one JSON document.

    ``lora_choice`` has no default on purpose: the writer cannot recover it
    from the environment, and inventing one would be the writer guessing at
    the run's configuration (D-004).
    """

    out = path if path is not None else RESULTS_PATH
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = _json_sanitize(
        {
            "protocol": PROTOCOL_ID,
            "n_pairs": n_pairs,
            "seed_start": seed_start,
            "events_gen1": events_gen1,
            "events_gen2": events_gen2,
            "k_gen2": k_gen2,
            # D-036: both windows reported through the resolver, so a
            # sentinel 0 reads as "all_events" rather than as a broken run.
            "pe_window_gen2": describe_pe_window(pe_window_gen2),
            "pe_window_gen1": describe_pe_window(PE_WINDOW_EVENTS),
            "lora_enabled": os.environ.get(LORA_ENABLED_ENV, "0"),
            # D-032: the polarity gate is cosine now, so DAU_NLI_FILTER_ENABLED
            # only means anything under POLARITY_FILTER=nli. Reporting the env
            # var alone would have every cosine run claim "nli_filter_enabled:
            # 1" — the report repeating a constant instead of following the
            # tool (CLAUDE.md 2.8). The active gate is read from its own
            # resolver; the env var stays, labelled for what it now gates.
            **describe_polarity_filter(),
            "nli_filter_enabled_env": os.environ.get(NLI_FILTER_ENABLED_ENV, "1"),
            # D-032/D-033. Multigen is the experiment path (D-014, D-031), but
            # the pair-filter counts only reached Protocol C′'s results file —
            # so prompt_skipped_no_record, the polarity rejections and
            # pairs_passed were invisible in the run that actually matters.
            "pair_filter": _pair_filter_report(),
            "mock_llm": mock_llm_enabled(),
            "tool_identity": build_tool_identity(
                lora_choice=lora_choice,
                seeds=list(range(seed_start, seed_start + n_pairs)),
            ),
            **preflight.block(),
            "notes": {
                "gen2_env": "fresh _seed_niche(seed) — same draw as null arm",
                "gen2_metric": "single-phase window mean PE (not train ΔPE)",
                "gen2_adapter": "fresh weights — no parent LoRA load",
                "somatic_scale": (
                    "apply_inherited_somatic_scale needs non-empty delta_log; "
                    "measurable from gen2 event 2+"
                ),
            },
            "pairs": [
                {
                    "seed": pair.seed,
                    # D-036. Hand-built dict, so a field added to
                    # MultigenPairResult does not reach the file on its own —
                    # this one was computed, printed and dropped, and the test
                    # that guarded it asserted on the object rather than the
                    # JSON, so the suite stayed green.
                    "phase2_decision_divergence": pair.phase2_decision_divergence,
                    "lineages": [
                        {
                            "gen1_arm": lin.gen1_arm,
                            "gen1": lin.gen1,
                            "transfer": lin.transfer,
                            "gen2": {
                                **lin.gen2,
                                # Explicit analysis key: gen2 PE × gen1 arm.
                                "delta_pe": lin.gen2.get("mean_pe"),
                                "gen1_arm": lin.gen1_arm,
                            },
                            # D-051. The same omission the note above
                            # describes, one field over: LineageResult grew a
                            # consolidation field whose own comment says an
                            # unreported consolidation would move gen2 numbers
                            # with nothing to attribute them to — and it was
                            # computed, printed to stdout, and dropped here.
                            # deleted_count is what GAP-19 is a question about.
                            "consolidation": lin.consolidation,
                        }
                        for lin in pair.lineages
                    ],
                }
                for pair in results
            ],
            "summary": _summary(results),
        }
    )
    out.write_text(json.dumps(payload, indent=2, allow_nan=False), encoding="utf-8")
    print(f"Wrote {out}", flush=True)
    return out


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Protocol C′ multigen: gen1 → transfer → gen2",
    )
    parser.add_argument("--n-pairs", type=int, default=N_PAIRS)
    parser.add_argument("--seed-start", type=int, default=SEED_START)
    parser.add_argument("--events-gen1", type=int, default=EVENTS_GEN1)
    parser.add_argument("--events-gen2", type=int, default=EVENTS_GEN2)
    parser.add_argument("--k-gen2", type=int, default=K_GEN2)
    parser.add_argument("--pe-window-gen2", type=int, default=PE_WINDOW_GEN2)
    parser.add_argument(
        "--mock-llm",
        action="store_true",
        help="Use deterministic MockLLM (no API/GPU).",
    )
    # No default: the run refuses to start until one of these is given, so a
    # forgotten flag can never be mistaken for an untrained run on purpose.
    lora_group = parser.add_mutually_exclusive_group()
    lora_group.add_argument(
        "--lora",
        dest="lora",
        action="store_true",
        default=None,
        help="Train per-agent adapters (requires DAU_LLM_BACKEND=local).",
    )
    lora_group.add_argument(
        "--no-lora",
        dest="lora",
        action="store_false",
        default=None,
        help="Deliberately run without training; recorded in the results JSON.",
    )
    parser.add_argument(
        "--results",
        type=Path,
        default=RESULTS_PATH,
        help="Output JSON path.",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_arg_parser().parse_args(argv)
    # Gate first: a refused run should print the reason, not a run banner.
    lora_choice = resolve_lora_choice(args.lora, mock=bool(args.mock_llm))
    if args.mock_llm:
        os.environ[MOCK_LLM_ENV] = "1"
    gate = Preflight(mock=bool(args.mock_llm))
    print(
        f"Protocol C′ multigen — N={args.n_pairs} "
        f"events_gen1={args.events_gen1} events_gen2={args.events_gen2} "
        f"K_gen2={args.k_gen2} mock={mock_llm_enabled()}",
        flush=True,
    )
    try:
        results = run_cprime_multigen(
            n_pairs=args.n_pairs,
            seed_start=args.seed_start,
            events_gen1=args.events_gen1,
            events_gen2=args.events_gen2,
            k_gen2=args.k_gen2,
            pe_window_gen2=args.pe_window_gen2,
            mock_llm=True if args.mock_llm else None,
            lora=args.lora,
            preflight=gate,
        )
    except PreflightAbort as abort:
        # An expected refusal, not a crash: print the named invariants rather
        # than a traceback, and write nothing.
        raise SystemExit(str(abort)) from None
    path = write_multigen_results_json(
        results,
        lora_choice=lora_choice,
        preflight=gate,
        path=args.results,
        events_gen1=args.events_gen1,
        events_gen2=args.events_gen2,
        k_gen2=args.k_gen2,
        n_pairs=args.n_pairs,
        seed_start=args.seed_start,
        pe_window_gen2=args.pe_window_gen2,
    )
    summary = _summary(results)
    print("\n=== MULTIGEN SUMMARY ===", flush=True)
    print(json.dumps(summary, indent=2), flush=True)
    print(f"run_quality={gate.run_quality()}", flush=True)
    print(f"results={path}", flush=True)


if __name__ == "__main__":
    main()
