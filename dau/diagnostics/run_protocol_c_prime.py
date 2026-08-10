"""Protocol C′ — LIVED vs NULL vs SHUFFLE LoRA validation (ADIM 6).

Protocol C tested META_ON vs META_OFF (frozen weights) → null result.
Protocol C′ tests three arms per seed with local LLM + per-agent LoRA:

  LIVED:   phase-1 events → train on lived preference pairs (Signal v2,
           NLI filtered) → phase-2 events with updated adapter
  NULL:    same seed / events, no LoRA training between phases
  SHUFFLE: same as LIVED but chosen↔rejected swapped before training

Primary metric: ΔPE = mean(PE_after) − mean(PE_before) per arm.
Hypothesis H1: ΔPE_lived < ΔPE_null (lived training reduces PE).

No trait injection. No LLM-as-judge. Do not re-run frozen Protocol C.
"""

from __future__ import annotations

import argparse
import dataclasses
import datetime
import json
import math
import os
import random
import re
import statistics
import tempfile
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
from scipy import stats

import dau.foundation.graph as graph_mod
from dau.diagnostics.tool_identity import (
    LORA_CHOICE_OFF,
    build_tool_identity,
    resolve_lora_choice,
)
from dau.foundation.constraints import (
    ADAPTER_BASE_DIR,
    NLI_CONTRADICTION_THRESHOLD,
    PER_AGENT_LORA_ALPHA,
    PER_AGENT_LORA_RANK,
    PRECISION_EPSILON,
    PRECISION_HISTORY_WINDOW,
    PRECISION_MAX_WEIGHT,
    PRECISION_MIN_HISTORY,
    PRECISION_MIN_WEIGHT,
    PRECISION_VAR_REF,
    SNR_MARGIN_FLOOR,
    PPR_ALPHA,
    PPR_WEIGHT_IN_SCORE,
    build_default_constraints,
    update_constraints,
)
from dau.foundation.graph import (
    build_graph,
    get_pe_event_log,
    reset_pe_event_log,
)
from dau.foundation.lod import CognitiveMode, LODState
from dau.foundation.meta_observer import bind_memory_store, unbind_memory_store
from dau.foundation.polarity_filter import describe_polarity_filter
from dau.foundation.state import DAUAgentState, InternalState
from dau.memory.store import MemoryStore
from dau.society.environment import (
    POOL_CRISIS_THRESHOLD,
    POOL_MAX,
    EnvironmentState,
)

# ---------------------------------------------------------------------------
# Protocol C′ constants (no magic numbers in logic)
# ---------------------------------------------------------------------------

N_PAIRS: int = int(os.environ.get("DAU_CPRIME_N_PAIRS", "15"))
EVENTS_PER_ARM: int = int(os.environ.get("DAU_CPRIME_EVENTS", "50"))
TEMPERATURE_DEFAULT: float = 0.2
SEED_START: int = int(os.environ.get("DAU_CPRIME_SEED_START", "2001"))
SEEDS: list[int] = list(range(SEED_START, SEED_START + N_PAIRS))
SIGNAL_VERSION: str = os.environ.get("DAU_CPRIME_SIGNAL", "v2")
RESULTS_PATH: Path = Path(
    os.environ.get(
        "DAU_CPRIME_RESULTS",
        "dau_runs/protocol_c_prime_results.json",
    )
)
CHECKPOINT_PATH: Path = Path(
    os.environ.get(
        "DAU_CPRIME_CHECKPOINT",
        "dau_runs/protocol_c_prime_checkpoint.json",
    )
)
HEARTBEAT_PATH: Path = Path(
    os.environ.get(
        "DAU_CPRIME_HEARTBEAT",
        "dau_runs/protocol_c_prime_heartbeat.json",
    )
)
# Must stay strictly above graph.TERMINATION_ENERGY, otherwise the floor never
# protects the run and a single max-PE trauma ends the life at event 1.
AB_ENERGY_FLOOR: float = 0.15
# Below this fraction of EVENTS_PER_ARM a padded PE trace is not measurable.
MIN_TRACE_FRACTION: float = 0.5

ALPHA: float = 0.05
EMPTY_COUNT: int = 0
EMPTY_MEAN: float = 0.0
EMPTY_STD: float = 0.0
# Below this spread the paired differences carry no information and ttest_rel
# reports t=inf / p=0.0 — an overwhelming result from no variation at all.
PAIRED_DIFF_MIN_STD: float = 1e-12
# NULL takes no training, so with the harness clean its replay is exact.
NULL_ARM_MAX_ABS_DELTA: float = 1e-9

# Precision smoke gates — pre-registered; do not retune after seeing outcomes.
SMOKE_SATURATION_MAX_RATE: float = 0.30
SMOKE_PI_MIN_DISTINCT: int = 3
PE_W_SATURATION_VALUE: float = 1.0
PI_DISTINCT_DECIMALS: int = 6
# v1 = usable-pair-only (SMOKE_N3_K5 locked). v2 = all audited arms
# (informational; not pre-registered — do not use to flip a locked FAIL).
SMOKE_POOL_USABLE_PAIRS: str = "usable_pairs_only"
SMOKE_POOL_ALL_AUDITED: str = "all_audited_arms"

# Diversity gate + PE window — pre-registered BEFORE the N=15 final run
# (cheap scan: 5 seeds × 10 evt phase-1 only, sampling T=0.2, no train;
# artefact /tmp/cprime_diversity_scan.json). n_unique=[4,5,5,5,4] →
# median 5 → K=5. Scan pe_gap_max min≈0.666 (not binding under sampling);
# gap floor equals the preference-pair builder's PE_RANK_MIN_GAP so a life
# that cannot form any PE-ranked pair is skipped as degenerate.
# W=10 is the mini-test SAMPLE_LIVED_PE_SEPARATION window with null clean —
# not chosen from the N=15 outcome (post-hoc W forbidden).
DIVERSITY_MIN_UNIQUE: int = 5
DIVERSITY_MIN_PE_GAP: float = 1e-6
PE_WINDOW_EVENTS: int = 10
NAN_DELTA: float = float("nan")

LLM_TEMPERATURE_ENV: str = "DAU_LLM_TEMPERATURE"
LLM_SEED_ENV: str = "DAU_LLM_SEED"
LLM_DO_SAMPLE_ENV: str = "DAU_LLM_DO_SAMPLE"
LORA_ENABLED_ENV: str = "DAU_LORA_ENABLED"
NLI_FILTER_ENABLED_ENV: str = "DAU_NLI_FILTER_ENABLED"
TORCH_THREADS_ENV: str = "DAU_TORCH_THREADS"
CUBLAS_WORKSPACE_CONFIG_ENV: str = "CUBLAS_WORKSPACE_CONFIG"
# Required by torch deterministic mode on CUDA; setdefault so a caller can override.
CUBLAS_WORKSPACE_CONFIG_VALUE: str = ":4096:8"
LLM_DO_SAMPLE_TRUTHY: frozenset[str] = frozenset({"1", "true", "TRUE", "yes", "YES"})

# Thread count changes the CPU reduction order, so it is pinned rather than
# left at whatever torch infers from the host. Default is this host's inferred
# value; override per machine via TORCH_THREADS_ENV.
TORCH_NUM_THREADS: int = int(os.environ.get(TORCH_THREADS_ENV, "14"))
# warn_only for greedy: unsupported ops must not abort a long run. Sampling
# on CUDA needs strict determinism or NULL phase1≢phase2 (measured).
TORCH_DETERMINISTIC_WARN_ONLY: bool = True

STREAM_NODES_PER_EVENT: int = 5
# Cycle: social_pre→agent→evaluator→meta_observer→pool_step (5 nodes after
# pool_step landed in 231c222). Headroom clears END after the last event.
# Historically 10 was too tight for EVENTS=10 under the old 4-node count
# (4*10+10=50 → GRAPH_RECURSION_LIMIT after event 10).
STREAM_RECURSION_HEADROOM: int = 40

# Per-seed niche. Decoding is greedy and the world is deterministic, so a seed
# that only touches RNG changes nothing: every seed in the N=15 overnight run
# produced pe_before = 0.3885. The seed has to vary the life itself. Organisms
# are still born identical (InternalState defaults) — only the niche differs,
# so this varies experience rather than trait.
NICHE_SCARCITY_RANGE: tuple[float, float] = (0.10, 0.70)
NICHE_UNCERTAINTY_RANGE: tuple[float, float] = (0.20, 0.80)
NICHE_SOCIAL_PRESSURE_RANGE: tuple[float, float] = (0.00, 0.60)
NICHE_TIME_PRESSURE_RANGE: tuple[float, float] = (0.00, 0.60)
# Birth pool stays clear of the crisis threshold so ADIM 1 crisis trauma is not
# a per-seed confound at event 1.
NICHE_POOL_FRACTION_RANGE: tuple[float, float] = (0.40, 1.00)

OPPONENT_ID: str = "cprime-npc-opponent"
# Protocol C′ ids end in the seed (``cprime-{arm}-{seed}``); multigen appends a
# generation suffix (``…-g1`` / ``…-g2``). Both must yield the same seed.
AGENT_ID_SEED_PATTERN: re.Pattern[str] = re.compile(r"-(?P<seed>\d+)(?:-g\d+)?$")
ARM_LIVED: str = "lived"
ARM_NULL: str = "null"
ARM_SHUFFLE: str = "shuffle"
ARM_ORDER: tuple[str, ...] = (ARM_LIVED, ARM_NULL, ARM_SHUFFLE)

VERDICT_H1_SUPPORTED: str = "H1_SUPPORTED"
VERDICT_H1_REJECTED: str = "H1_REJECTED"
VERDICT_INCONCLUSIVE: str = "INCONCLUSIVE"

assert AB_ENERGY_FLOOR > graph_mod.TERMINATION_ENERGY, (
    f"AB_ENERGY_FLOOR ({AB_ENERGY_FLOOR}) must exceed "
    f"TERMINATION_ENERGY ({graph_mod.TERMINATION_ENERGY})"
)
assert NICHE_POOL_FRACTION_RANGE[0] > POOL_CRISIS_THRESHOLD, (
    f"birth pool fraction floor ({NICHE_POOL_FRACTION_RANGE[0]}) must exceed "
    f"POOL_CRISIS_THRESHOLD ({POOL_CRISIS_THRESHOLD})"
)

# Constraint snapshot — documents ADIM wiring without silent magic.
_CONSTRAINT_SNAPSHOT: dict[str, float | int | str] = {
    "PPR_ALPHA": PPR_ALPHA,
    "PPR_WEIGHT_IN_SCORE": PPR_WEIGHT_IN_SCORE,
    "NLI_CONTRADICTION_THRESHOLD": NLI_CONTRADICTION_THRESHOLD,
    "PER_AGENT_LORA_RANK": PER_AGENT_LORA_RANK,
    "PER_AGENT_LORA_ALPHA": PER_AGENT_LORA_ALPHA,
    "ADAPTER_BASE_DIR": ADAPTER_BASE_DIR,
    "PRECISION_EPSILON": PRECISION_EPSILON,
    "PRECISION_MAX_WEIGHT": PRECISION_MAX_WEIGHT,
    "PRECISION_MIN_WEIGHT": PRECISION_MIN_WEIGHT,
    "PRECISION_VAR_REF": PRECISION_VAR_REF,
    "PRECISION_MIN_HISTORY": PRECISION_MIN_HISTORY,
    "PRECISION_HISTORY_WINDOW": PRECISION_HISTORY_WINDOW,
}


@dataclass
class ArmResult:
    """One LIVED / NULL / SHUFFLE arm under a locked seed."""

    seed: int
    arm: str  # "lived" | "null" | "shuffle"
    pe_before: float  # mean PE over first PE_WINDOW_EVENTS of phase-1
    pe_after: float  # mean PE over first PE_WINDOW_EVENTS of phase-2
    delta_pe: float  # pe_after - pe_before (NaN when diversity-gated)
    n_events: int
    n_pairs_trained: int  # preference pairs that passed NLI filter
    n_pairs_rejected: int  # rejected by NLI filter
    wall_seconds: float
    gated: bool = False
    gate_reason: str = ""
    n_unique: int = 0
    pe_gap_max: float = 0.0
    # Precision audit (phase-1 + phase-2 pe_event_log rows for this arm).
    saturation_rate: float = EMPTY_MEAN
    pi_n_distinct: int = EMPTY_COUNT
    n_pe_events_audited: int = EMPTY_COUNT
    n_saturated: int = EMPTY_COUNT
    pi_values: list[float] = field(default_factory=list)
    # sha256(decisions ++ PE) for I2.1, and whether this agent has an adapter
    # on disk for I2.2. Recorded rather than asserted so the invariants can be
    # judged from the results file after the fact.
    arm_digest: str = ""
    adapter_present: bool = False


@dataclass
class PairResult:
    """Three arms for one seed (independent agent_ids)."""

    seed: int
    lived: ArmResult
    null: ArmResult
    shuffle: ArmResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _mean(values: list[float]) -> float:
    """Arithmetic mean, or 0.0 when empty."""

    if not values:
        return EMPTY_MEAN
    return float(statistics.mean(values))


def _std(values: list[float]) -> float:
    """Sample stdev for n>1; 0.0 otherwise."""

    if len(values) < 2:
        return EMPTY_STD
    return float(statistics.stdev(values))


def _window_mean(pe_list: list[float], window: int = PE_WINDOW_EVENTS) -> float:
    """Mean over the pre-registered PE window (first ``window`` events)."""

    if not pe_list:
        return EMPTY_MEAN
    return _mean(pe_list[:window])


def _is_finite_delta(value: float) -> bool:
    """True when ΔPE is a real measurement (not diversity-gated NaN)."""

    return isinstance(value, (int, float)) and math.isfinite(float(value))


def _smoke_gates_block(
    *,
    arms: list[ArmResult],
    null_deltas: list[float],
    pool: str,
    pre_registered: bool,
) -> dict[str, Any]:
    """Build one smoke_gates dict from an explicit arm pool + null ΔPE list.

    ``null_deltas`` are caller-selected so v1 (usable pairs) and v2 (all
    finite null arms) stay independent of each other.
    """

    n_pe_total = sum(int(arm.n_pe_events_audited) for arm in arms)
    n_sat_total = sum(int(arm.n_saturated) for arm in arms)
    saturation_rate = (
        float(n_sat_total) / float(n_pe_total) if n_pe_total > 0 else EMPTY_MEAN
    )
    all_pi: list[float] = []
    for arm in arms:
        all_pi.extend(float(value) for value in arm.pi_values)
    pi_values_unique = sorted(
        {round(value, PI_DISTINCT_DECIMALS) for value in all_pi}
    )
    pi_n_distinct = len(pi_values_unique)
    saturation_pass = bool(n_pe_total > 0) and (
        saturation_rate <= SMOKE_SATURATION_MAX_RATE
    )
    pi_distinct_pass = pi_n_distinct >= SMOKE_PI_MIN_DISTINCT
    null_arm_clean = bool(null_deltas) and all(
        abs(value) <= NULL_ARM_MAX_ABS_DELTA for value in null_deltas
    )
    return {
        "pool": pool,
        # Bool flag: is this pool the locked SMOKE_N3_K5 definition?
        "is_pre_registered": pre_registered,
        # Threshold bag (same shape as earlier smoke_gates.pre_registered).
        "pre_registered": {
            "n_pairs": N_PAIRS,
            "events_per_arm": EVENTS_PER_ARM,
            "seed_start": SEED_START,
            "seeds": list(SEEDS),
            "saturation_max_rate": SMOKE_SATURATION_MAX_RATE,
            "pi_min_distinct": SMOKE_PI_MIN_DISTINCT,
            "pe_w_saturation_value": PE_W_SATURATION_VALUE,
        },
        "null_arm_clean": null_arm_clean,
        "saturation_rate": saturation_rate,
        "saturation_pass": saturation_pass,
        "n_pe_events": n_pe_total,
        "n_saturated": n_sat_total,
        "pi_n_distinct": pi_n_distinct,
        "pi_distinct_pass": pi_distinct_pass,
        "pi_values_unique": pi_values_unique,
        "all_pass": bool(null_arm_clean and saturation_pass and pi_distinct_pass),
    }


def _precision_audit_from_pe_rows(
    pe_rows: list[dict[str, Any]],
) -> tuple[float, int, list[float], int, int]:
    """Return (saturation_rate, pi_n_distinct, pi_values, n_events, n_saturated).

    saturation_rate = fraction of rows with PE_w == PE_W_SATURATION_VALUE.
    π distinct uses rounded values at PI_DISTINCT_DECIMALS.
    """

    if not pe_rows:
        return EMPTY_MEAN, EMPTY_COUNT, [], EMPTY_COUNT, EMPTY_COUNT

    pe_w_values = [float(row["prediction_error"]) for row in pe_rows]
    pi_values = [float(row["precision_weight"]) for row in pe_rows]
    n_events = len(pe_w_values)
    n_saturated = sum(
        1 for value in pe_w_values if float(value) == PE_W_SATURATION_VALUE
    )
    saturation_rate = float(n_saturated) / float(n_events)
    unique_n = len({round(value, PI_DISTINCT_DECIMALS) for value in pi_values})
    return saturation_rate, unique_n, pi_values, n_events, n_saturated


def _merge_pe_rows(
    *row_groups: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Concatenate pe_event_log row groups in order."""

    merged: list[dict[str, Any]] = []
    for group in row_groups:
        merged.extend(group)
    return merged


def _phase1_diversity(
    lived_examples: list[Any],
) -> tuple[int, float]:
    """Return (n_unique completions, pe_gap_max) for usable lived decisions."""

    from dau.foundation.lora_update import COMPLETION_FALLBACK

    completions: list[str] = []
    pes: list[float] = []
    for example in lived_examples:
        text = (getattr(example, "completion", None) or COMPLETION_FALLBACK).strip()
        if not text or text == COMPLETION_FALLBACK:
            continue
        completions.append(text)
        pes.append(float(example.prediction_error))
    n_unique = len(set(completions))
    pe_gap_max = (max(pes) - min(pes)) if len(pes) >= 2 else EMPTY_MEAN
    return n_unique, pe_gap_max


def _diversity_gate_reason(n_unique: int, pe_gap_max: float) -> str:
    """Empty string when the arm may train; otherwise a skip reason."""

    if n_unique < DIVERSITY_MIN_UNIQUE:
        return (
            f"n_unique={n_unique} < DIVERSITY_MIN_UNIQUE={DIVERSITY_MIN_UNIQUE}"
        )
    if pe_gap_max < DIVERSITY_MIN_PE_GAP:
        return (
            f"pe_gap_max={pe_gap_max:.6g} < "
            f"DIVERSITY_MIN_PE_GAP={DIVERSITY_MIN_PE_GAP}"
        )
    return ""


def _json_sanitize(value: Any) -> Any:
    """Replace NaN/Inf with null so results JSON stays RFC-compliant."""

    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, dict):
        return {key: _json_sanitize(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_sanitize(item) for item in value]
    return value


def _lock_torch_seed(seed: int) -> None:
    """Pin torch RNG, thread count, and algorithm choice.

    torch is optional — the groq backend never imports it. When local
    sampling is on, CUDA must be strictly deterministic: warn_only left
    NULL phase1≠phase2 at event 1 under T=0.2.
    """

    try:
        import torch
    except ImportError:
        return

    os.environ.setdefault(
        CUBLAS_WORKSPACE_CONFIG_ENV,
        CUBLAS_WORKSPACE_CONFIG_VALUE,
    )
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    torch.set_num_threads(TORCH_NUM_THREADS)
    try:
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False
    except Exception:  # noqa: BLE001 — CPU-only builds
        pass
    sampling = (
        os.environ.get(LLM_DO_SAMPLE_ENV, "0").strip() in LLM_DO_SAMPLE_TRUTHY
    )
    torch.use_deterministic_algorithms(
        True,
        warn_only=(TORCH_DETERMINISTIC_WARN_ONLY and not sampling),
    )


def _temperature() -> float:
    """Effective sampling temperature, read now — not at import time.

    GAP-15: this used to be bound at import and _lock_seeds wrote the frozen
    value back into the environment on every call, so a change made after
    import was silently discarded — while local_llm reads the env at call time
    and could therefore disagree with what the results JSON reported.
    """

    raw = os.environ.get(LLM_TEMPERATURE_ENV, "").strip()
    if not raw:
        return TEMPERATURE_DEFAULT
    # An unparseable temperature must fail the run, not fall back to a value
    # the operator never chose and the JSON would then report as fact.
    return float(raw)


def _lock_seeds(seed: int) -> None:
    """Pin Python, NumPy, torch, and Groq seed for counterfactual replay."""

    random.seed(seed)
    np.random.seed(seed)
    _lock_torch_seed(seed)
    os.environ[LLM_SEED_ENV] = str(seed)
    os.environ[LLM_TEMPERATURE_ENV] = str(_temperature())


def _seed_niche(seed: int) -> tuple[Any, EnvironmentState]:
    """Draw this seed's niche from the pre-registered ranges.

    Uses a private Random so the niche does not depend on how much global RNG
    anything else happened to consume first.
    """

    rng = random.Random(seed)
    constraints = update_constraints(
        build_default_constraints(),
        resource_scarcity=rng.uniform(*NICHE_SCARCITY_RANGE),
        uncertainty=rng.uniform(*NICHE_UNCERTAINTY_RANGE),
        social_pressure=rng.uniform(*NICHE_SOCIAL_PRESSURE_RANGE),
        time_pressure=rng.uniform(*NICHE_TIME_PRESSURE_RANGE),
    )
    pool = POOL_MAX * rng.uniform(*NICHE_POOL_FRACTION_RANGE)
    return constraints, EnvironmentState(pool=pool)


def _initial_state(agent_id: str, seed: int) -> DAUAgentState:
    """Fresh agent with System 2 substrate (LLM path required).

    Body starts at birth defaults for every seed; only the niche varies.
    """

    constraints, env_state = _seed_niche(seed)
    return DAUAgentState(
        agent_id=agent_id,
        opponent_id=OPPONENT_ID,
        environment=constraints,
        env_state=env_state,
        lod_state=LODState(
            mode=CognitiveMode.SYSTEM_2,
            t_cognitive=1.0,
            consecutive_low_steps=0,
            last_escalation_event=0,
        ),
        internal_state=InternalState(),
    )


def _open_temp_memory_store() -> tuple[MemoryStore, tempfile.TemporaryDirectory[str]]:
    """Per-phase isolated MemoryStore (no cross-arm contamination)."""

    tmp = tempfile.TemporaryDirectory(prefix="dau_protocol_c_prime_")
    store = MemoryStore(
        chroma_path=os.path.join(tmp.name, "chroma"),
        sqlite_path=os.path.join(tmp.name, "memory.db"),
    )
    return store, tmp


def _state_from_stream(values: Any) -> DAUAgentState:
    """Normalize stream values into DAUAgentState."""

    if isinstance(values, DAUAgentState):
        return values
    if isinstance(values, dict):
        return DAUAgentState.model_validate(values)
    raise TypeError(f"Unexpected stream value type: {type(values)!r}")


def _is_llm_abort_error(exc: BaseException) -> bool:
    """True for rate-limit or timeout-style LLM failures."""

    if graph_mod._is_quota_error(exc):
        return True
    text = str(exc).lower()
    markers = ("timeout", "timed out", "deadline", "read timed out", "connect")
    return any(marker in text for marker in markers)


def _run_system1_fallback(original: Any, state: DAUAgentState) -> dict[str, Any]:
    """Force NPC System 1 for one decision (LLM abort path)."""

    prior = graph_mod.should_run_llm
    graph_mod.should_run_llm = lambda _lod: False
    try:
        return original(state)
    finally:
        graph_mod.should_run_llm = prior


def _pad_pe_list(pe_list: list[float], n_events: int) -> list[float]:
    """Pad short PE traces with last value (energy-floor early stop).

    A trace shorter than MIN_TRACE_FRACTION is dominated by padding, so its
    mean is an artifact rather than a measurement — surface it loudly.
    """

    if len(pe_list) >= n_events:
        return pe_list[:n_events]
    if len(pe_list) < n_events * MIN_TRACE_FRACTION:
        print(
            f"[PROTOCOL_C_PRIME][WARN] PE trace {len(pe_list)}/{n_events} events "
            f"— mean is padding-dominated, arm not measurable",
            flush=True,
        )
    if not pe_list:
        return [EMPTY_MEAN] * n_events
    last = pe_list[-1]
    return pe_list + [last] * (n_events - len(pe_list))


def _seed_from_agent_id(agent_id: str) -> int:
    """Parse the seed from ``cprime-{arm}-{seed}`` or ``…-{seed}-g{n}``.

    No fallback. ``hash()`` varies per process unless PYTHONHASHSEED is
    pinned, so an id that misses this pattern silently costs the run its
    replay guarantee — GAP-11 was exactly that: the generation suffix made
    ``int("g1")`` raise, and the shuffle arm drew a different permutation in
    every process.
    """

    match = AGENT_ID_SEED_PATTERN.search(str(agent_id))
    if match is None:
        raise ValueError(
            f"agent_id {agent_id!r} carries no seed segment — expected "
            f"cprime-{{arm}}-{{seed}} or cprime-{{arm}}-{{seed}}-g{{n}}"
        )
    return int(match.group("seed"))


def _build_lived_examples(
    state: DAUAgentState,
    pe_rows: list[dict[str, Any]],
) -> list[Any]:
    """Build LivedTraceExample rows; graceful empty list if unavailable.

    Must stay side-effect free. ``maybe_lora_update_after_life`` returns the
    same rows but trains and saves the adapter on the way, and this runs at
    the end of every phase of every arm — including NULL, whose whole job is
    to stay untrained, and including phase 2, after the measurement window.
    """

    try:
        from dau.foundation.lora_update import build_lived_trace_examples
    except ImportError:
        return []

    return list(build_lived_trace_examples(state, pe_rows))


# ---------------------------------------------------------------------------
# Core: collect / train / arms
# ---------------------------------------------------------------------------


def _collect_pe_events(
    agent_id: str,
    seed: int,
    n_events: int,
    energy_floor: float = AB_ENERGY_FLOOR,
) -> tuple[list[float], list[Any], list[dict[str, Any]]]:
    """Run agent for n_events; return (pe_list, lived_examples, pe_rows).

    Uses production ``build_graph`` with Protocol C monkeypatch pattern.
    Collects ``prediction_error`` from evaluator telemetry (pe event log).
    Pads remaining slots with last PE when energy floor ends the life early.
    ``pe_rows`` are the raw audit rows (include raw_pe / precision_weight).
    """

    graph_mod.load_env_file()

    original_agent = graph_mod.agent_node
    original_max_events = graph_mod.MAX_EVENTS
    original_energy_floor = graph_mod.AB_ENERGY_FLOOR

    def _safe_agent(state: DAUAgentState) -> dict[str, Any]:
        lod = state.lod_state
        if not isinstance(lod, LODState):
            lod = LODState()
        if not graph_mod.should_run_llm(lod):
            return original_agent(state)
        try:
            return original_agent(state)
        except Exception as exc:  # noqa: BLE001 — free-tier must not abort life
            if _is_llm_abort_error(exc):
                return _run_system1_fallback(original_agent, state)
            raise

    store: MemoryStore | None = None
    tmp: tempfile.TemporaryDirectory[str] | None = None
    reset_pe_event_log()

    try:
        graph_mod.MAX_EVENTS = int(n_events)
        graph_mod.AB_ENERGY_FLOOR = float(energy_floor)
        graph_mod.agent_node = _safe_agent

        store, tmp = _open_temp_memory_store()
        graph_mod._memory_stores[agent_id] = store
        graph_mod._memory_written[agent_id] = 0
        bind_memory_store(agent_id, store)

        initial = _initial_state(agent_id, seed)
        stream_limit = n_events * STREAM_NODES_PER_EVENT + STREAM_RECURSION_HEADROOM
        result: Any = initial
        app = build_graph(checkpointer=None)
        for values in app.stream(
            initial,
            config={"recursion_limit": stream_limit},
            stream_mode="values",
        ):
            result = values

        state = _state_from_stream(result)
        pe_rows = list(get_pe_event_log())
        pe_list = [float(row["prediction_error"]) for row in pe_rows]
        pe_list = _pad_pe_list(pe_list, n_events)
        lived_examples = _build_lived_examples(state, pe_rows)
        return pe_list, lived_examples, pe_rows
    finally:
        unbind_memory_store(agent_id)
        graph_mod._memory_stores.pop(agent_id, None)
        graph_mod._memory_written.pop(agent_id, None)
        graph_mod.agent_node = original_agent
        graph_mod.MAX_EVENTS = original_max_events
        graph_mod.AB_ENERGY_FLOOR = original_energy_floor
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


def _pair_filter_report() -> dict[str, Any]:
    """Pair-filter counts and the floor's calibration status (D-030).

    ``calibrated`` ships false on purpose: the floor came from a brief's
    claim, not from a measured margin distribution. A results file that
    omitted this would let an uncalibrated threshold read as a settled one.
    """

    from dau.foundation.constraints import SNR_MARGIN_FLOOR_CALIBRATED

    try:
        from dau.foundation.lora_update import (
            POLARITY_FILTER_STATS,
            PROMPT_FILTER_STATS,
            SNR_FILTER_STATS,
        )
        from dau.foundation.polarity_filter import describe_polarity_filter
    except ImportError:
        return {"available": False, "reason": "lora_update unavailable"}

    return {
        "available": True,
        # D-032. Which gate ran, read from the resolver the gate itself uses —
        # not from a separate constant that could drift out of step with it.
        **describe_polarity_filter(),
        # D-032. A life whose decisions carry no recorded prompt trains on
        # nothing, and that must not read like a strict-filter result.
        "prompt_examples_seen": int(PROMPT_FILTER_STATS.get("examples_seen", 0)),
        "prompt_skipped_no_record": int(
            PROMPT_FILTER_STATS.get("skipped_no_recorded_prompt", 0)
        ),
        "snr_margin_floor": SNR_MARGIN_FLOOR,
        "snr_margin_floor_calibrated": SNR_MARGIN_FLOOR_CALIBRATED,
        "snr_candidates": int(SNR_FILTER_STATS.get("total_candidates", 0)),
        "snr_rejected_below_margin": int(
            SNR_FILTER_STATS.get("rejected_below_margin", 0)
        ),
        "polarity_candidates": int(POLARITY_FILTER_STATS.get("total_candidates", 0)),
        "polarity_rejected": int(POLARITY_FILTER_STATS.get("rejected", 0)),
        "pairs_passed": int(POLARITY_FILTER_STATS.get("passed", 0)),
    }


def _train_adapter(
    agent_id: str,
    lived_examples: list[Any],
    shuffled: bool = False,
) -> tuple[int, int]:
    """Build preference pairs (PE-rank + NLI gate), optional shuffle, train.

    Pairs come from ``build_pe_ranked_pairs``: PE-rank first, then
    ``is_genuine_polarity_pair``. Returns ``(n_pairs_trained, n_pairs_rejected)``
    from POLARITY_FILTER_STATS deltas (passed is per-event; rejected per-candidate).
    Guard: ``DAU_LORA_ENABLED=0`` → skip and return ``(0, 0)``.
    """

    if os.environ.get(LORA_ENABLED_ENV, "0").strip() not in {
        "1",
        "true",
        "TRUE",
        "yes",
        "YES",
    }:
        return EMPTY_COUNT, EMPTY_COUNT

    try:
        from dau.foundation.lora_update import (
            POLARITY_FILTER_STATS,
            build_pe_ranked_pairs,
            run_micro_train_preference_step,
            shuffle_preference_pairs,
        )
    except ImportError:
        return EMPTY_COUNT, EMPTY_COUNT

    os.environ.setdefault(NLI_FILTER_ENABLED_ENV, "1")

    from dau.foundation.lora_update import SNR_FILTER_STATS

    before_passed = int(POLARITY_FILTER_STATS.get("passed", EMPTY_COUNT))
    before_rejected = int(POLARITY_FILTER_STATS.get("rejected", EMPTY_COUNT))
    before_snr_rejected = int(SNR_FILTER_STATS.get("rejected_below_margin", 0))

    try:
        pairs = build_pe_ranked_pairs(lived_examples)
    except Exception:  # noqa: BLE001 — graceful fallback if PE/NLI path fails
        return EMPTY_COUNT, EMPTY_COUNT

    n_pairs_trained = int(POLARITY_FILTER_STATS.get("passed", EMPTY_COUNT)) - before_passed
    n_pairs_rejected = (
        int(POLARITY_FILTER_STATS.get("rejected", EMPTY_COUNT)) - before_rejected
    )
    snr_rejected = (
        int(SNR_FILTER_STATS.get("rejected_below_margin", 0)) - before_snr_rejected
    )
    if snr_rejected:
        print(
            f"[SNR] {agent_id}: {snr_rejected} pair(s) dropped below "
            f"SNR_MARGIN_FLOOR={SNR_MARGIN_FLOOR} before the NLI pass",
            flush=True,
        )

    if shuffled and pairs:
        pairs = shuffle_preference_pairs(
            pairs,
            seed=_seed_from_agent_id(agent_id),
        )

    # A skipped train step used to be invisible: the arm still reported the NLI
    # pass count as n_pairs_trained, so a run where DPO never fired looked
    # identical to one where it did.
    try:
        result = run_micro_train_preference_step(pairs, agent_id=agent_id)
    except Exception as exc:  # noqa: BLE001 — train failure must not abort protocol
        print(
            f"[PROTOCOL_C_PRIME][WARN] {agent_id}: train raised {exc!r} — "
            f"arm continues untrained",
            flush=True,
        )
        return EMPTY_COUNT, EMPTY_COUNT

    trained = bool(result.get("trained", False))
    if not trained:
        print(
            f"[PROTOCOL_C_PRIME][WARN] {agent_id}: no training happened "
            f"({result.get('reason', 'no reason given')}) — arm is untrained",
            flush=True,
        )
        return EMPTY_COUNT, EMPTY_COUNT

    print(
        f"[PROTOCOL_C_PRIME] {agent_id}: trained on {len(pairs)} pairs "
        f"(shuffled={shuffled}) loss={result.get('dpo_loss')} "
        f"acc={result.get('dpo_accuracy')}",
        flush=True,
    )
    return max(EMPTY_COUNT, n_pairs_trained), max(EMPTY_COUNT, n_pairs_rejected)


def run_arm(
    seed: int,
    arm: str,
    agent_id: str,
) -> ArmResult:
    """Full arm: lock → phase-1 → diversity gate → train/skip → phase-2.

    ΔPE uses the pre-registered ``PE_WINDOW_EVENTS`` prefix of each phase, not
    the full life mean (plato dilution guard). Train arms that fail the
    diversity gate return NaN ΔPE and skip train/phase-2. NULL never trains and
    is not diversity-gated — it remains the integrity replay check.
    """

    started = time.perf_counter()
    _lock_seeds(seed)

    pe_before_list, lived_examples, pe_rows_before = _collect_pe_events(
        agent_id=agent_id,
        seed=seed,
        n_events=EVENTS_PER_ARM,
        energy_floor=AB_ENERGY_FLOOR,
    )
    pe_before = _window_mean(pe_before_list)
    n_unique, pe_gap_max = _phase1_diversity(lived_examples)

    n_pairs_trained = EMPTY_COUNT
    n_pairs_rejected = EMPTY_COUNT
    if arm in {ARM_LIVED, ARM_SHUFFLE}:
        gate_reason = _diversity_gate_reason(n_unique, pe_gap_max)
        if gate_reason:
            print(
                f"[PROTOCOL_C_PRIME] {agent_id}: diversity gate — {gate_reason} "
                f"(skip train/phase-2)",
                flush=True,
            )
            sat, pi_n, pi_vals, n_aud, n_sat = _precision_audit_from_pe_rows(
                pe_rows_before
            )
            return ArmResult(
                seed=seed,
                arm=arm,
                pe_before=pe_before,
                pe_after=NAN_DELTA,
                delta_pe=NAN_DELTA,
                n_events=EVENTS_PER_ARM,
                n_pairs_trained=n_pairs_trained,
                n_pairs_rejected=n_pairs_rejected,
                wall_seconds=float(time.perf_counter() - started),
                gated=True,
                gate_reason=gate_reason,
                n_unique=n_unique,
                pe_gap_max=pe_gap_max,
                saturation_rate=sat,
                pi_n_distinct=pi_n,
                n_pe_events_audited=n_aud,
                n_saturated=n_sat,
                pi_values=list(pi_vals),
            )
        n_pairs_trained, n_pairs_rejected = _train_adapter(
            agent_id,
            lived_examples,
            shuffled=(arm == ARM_SHUFFLE),
        )
    # null: no training between phases; diversity metrics recorded only

    _lock_seeds(seed)
    pe_after_list, _, pe_rows_after = _collect_pe_events(
        agent_id=agent_id,
        seed=seed,
        n_events=EVENTS_PER_ARM,
        energy_floor=AB_ENERGY_FLOOR,
    )
    pe_after = _window_mean(pe_after_list)
    delta_pe = pe_after - pe_before
    wall_seconds = float(time.perf_counter() - started)
    sat, pi_n, pi_vals, n_aud, n_sat = _precision_audit_from_pe_rows(
        _merge_pe_rows(pe_rows_before, pe_rows_after)
    )

    return ArmResult(
        seed=seed,
        arm=arm,
        pe_before=pe_before,
        pe_after=pe_after,
        delta_pe=delta_pe,
        n_events=EVENTS_PER_ARM,
        n_pairs_trained=n_pairs_trained,
        n_pairs_rejected=n_pairs_rejected,
        wall_seconds=wall_seconds,
        gated=False,
        gate_reason="",
        n_unique=n_unique,
        pe_gap_max=pe_gap_max,
        saturation_rate=sat,
        pi_n_distinct=pi_n,
        n_pe_events_audited=n_aud,
        n_saturated=n_sat,
        pi_values=list(pi_vals),
    )


def run_pair(seed: int) -> PairResult:
    """Run lived → null → shuffle for one seed (fresh agent_id each arm)."""

    arms: dict[str, ArmResult] = {}
    for arm in ARM_ORDER:
        agent_id = f"cprime-{arm}-{seed}"
        print(
            f"[PROTOCOL_C_PRIME] seed={seed} arm={arm} agent={agent_id} …",
            flush=True,
        )
        arms[arm] = run_arm(seed=seed, arm=arm, agent_id=agent_id)

    return PairResult(
        seed=seed,
        lived=arms[ARM_LIVED],
        null=arms[ARM_NULL],
        shuffle=arms[ARM_SHUFFLE],
    )


def _save_checkpoint(completed: list[PairResult]) -> None:
    CHECKPOINT_PATH.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "protocol": "C_PRIME",
        "n_completed": len(completed),
        "seeds_completed": [r.seed for r in completed],
        "pairs": [dataclasses.asdict(r) for r in completed],
    }
    tmp = CHECKPOINT_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2))
    tmp.replace(CHECKPOINT_PATH)


def _load_checkpoint() -> list[int]:
    if not CHECKPOINT_PATH.exists():
        return []
    try:
        data = json.loads(CHECKPOINT_PATH.read_text())
        return [int(s) for s in data.get("seeds_completed", [])]
    except Exception:
        return []


def _write_heartbeat(seed: int, arm: str, elapsed_minutes: float) -> None:
    HEARTBEAT_PATH.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "current_seed": seed,
        "current_arm": arm,
        "elapsed_minutes": round(elapsed_minutes, 1),
        "timestamp": datetime.datetime.now().isoformat(),
    }
    HEARTBEAT_PATH.write_text(json.dumps(data, indent=2))


def _pair_result_from_dict(row: dict[str, Any]) -> PairResult:
    """Rehydrate PairResult from checkpoint JSON row."""

    return PairResult(
        seed=int(row["seed"]),
        lived=ArmResult(**row["lived"]),
        null=ArmResult(**row["null"]),
        shuffle=ArmResult(**row["shuffle"]),
    )


def run_protocol_c_prime() -> list[PairResult]:
    """Run all N_PAIRS seeds; print progress after each pair."""

    assert len(SEEDS) == N_PAIRS, "SEEDS length must equal N_PAIRS"
    graph_mod.load_env_file()
    os.environ[LLM_TEMPERATURE_ENV] = str(_temperature())

    run_start = time.perf_counter()
    completed_seeds = _load_checkpoint()
    if completed_seeds:
        print(f"Resuming: {len(completed_seeds)} seeds already done: {completed_seeds}")

    results: list[PairResult] = []
    if CHECKPOINT_PATH.exists():
        try:
            ckpt = json.loads(CHECKPOINT_PATH.read_text())
            results = [
                _pair_result_from_dict(row) for row in ckpt.get("pairs", [])
            ]
        except Exception:
            results = []

    for idx, seed in enumerate(SEEDS, start=1):
        if seed in completed_seeds:
            print(f"  Seed {seed} — skipped (checkpoint)")
            continue
        elapsed = (time.perf_counter() - run_start) / 60
        _write_heartbeat(seed, "starting", elapsed)

        MAX_RETRIES = 2
        pair = None
        for attempt in range(MAX_RETRIES + 1):
            try:
                pair = run_pair(seed)
                break
            except Exception as e:
                if attempt < MAX_RETRIES:
                    print(
                        f"  Seed {seed} attempt {attempt+1} failed: {e} — retrying in 10s"
                    )
                    time.sleep(10)
                else:
                    print(
                        f"  Seed {seed} FAILED after {MAX_RETRIES+1} attempts: {e} — skipping"
                    )
        if pair is None:
            continue

        results.append(pair)
        _save_checkpoint(results)
        elapsed = (time.perf_counter() - run_start) / 60
        print(
            f"  Seed {seed} done ({elapsed:.1f} min elapsed) — {len(results)}/{N_PAIRS} complete"
        )
        print(
            f"[PROTOCOL_C_PRIME] seed {idx}/{N_PAIRS} done (seed={seed})",
            flush=True,
        )

    if CHECKPOINT_PATH.exists():
        CHECKPOINT_PATH.unlink()
        print("Checkpoint cleared — run complete.")

    return results


def _paired_test(treatment: list[float], control: list[float]) -> dict[str, Any]:
    """Paired t-test plus Wilcoxon, with an explicit zero-variance guard.

    ΔPE is nearly discrete — the adapter either flips the greedy decision or it
    does not — so identical paired differences are a real possibility. In that
    case ttest_rel returns t=inf and p=0.0, which reads as an overwhelming
    result produced by no variation at all. Report that instead of testing it.
    """

    n_pairs = len(treatment)
    out: dict[str, Any] = {
        "n": n_pairs,
        "t_stat": EMPTY_MEAN,
        "p_value": 1.0,
        "wilcoxon_p": 1.0,
        # The smallest two-sided signed-rank p reachable at this n is 2/2**n,
        # so below ~6 pairs Wilcoxon cannot clear ALPHA whatever the data says.
        "wilcoxon_gateable": bool(
            n_pairs > 0 and (2.0 / float(2**n_pairs)) <= ALPHA
        ),
        "degenerate": False,
        "degenerate_reason": "",
    }
    if len(treatment) < 2:
        out["degenerate"] = True
        out["degenerate_reason"] = "fewer than two pairs"
        return out

    diffs = [t - c for t, c in zip(treatment, control)]
    if _std(diffs) <= PAIRED_DIFF_MIN_STD:
        out["degenerate"] = True
        out["degenerate_reason"] = (
            "paired differences have no spread — the seeds are not producing "
            "distinct lives, so N is effectively 1"
        )
        return out

    t_result = stats.ttest_rel(treatment, control)
    out["t_stat"] = float(t_result.statistic)
    out["p_value"] = float(t_result.pvalue)
    try:
        out["wilcoxon_p"] = float(stats.wilcoxon(diffs).pvalue)
    except ValueError:
        # scipy refuses an all-zero difference vector.
        out["wilcoxon_p"] = 1.0
    return out


def _compute_stats(results: list[PairResult]) -> dict[str, Any]:
    """Summary means/stds + paired tests.

    Primary contrast is LIVED vs SHUFFLE: both arms take the same training
    machinery and differ only in preference direction. LIVED vs NULL is kept as
    a secondary read-out, but NULL is an integrity check rather than a
    statistical arm — with the harness clean its ΔPE is exactly zero.

    Diversity-gated arms carry NaN ΔPE and are dropped from the contrast. A
    claim requires ``n_effective >= N_PAIRS`` so N<15 never reads as decisive.
    """

    usable = [
        r
        for r in results
        if _is_finite_delta(r.lived.delta_pe)
        and _is_finite_delta(r.shuffle.delta_pe)
        and _is_finite_delta(r.null.delta_pe)
    ]
    n_gated = len(results) - len(usable)
    n_effective = len(usable)

    lived = [r.lived.delta_pe for r in usable]
    null = [r.null.delta_pe for r in usable]
    shuffle = [r.shuffle.delta_pe for r in usable]

    mean_delta_pe_lived = _mean(lived)
    mean_delta_pe_null = _mean(null)
    mean_delta_pe_shuffle = _mean(shuffle)
    std_delta_pe_lived = _std(lived)
    std_delta_pe_null = _std(null)
    std_delta_pe_shuffle = _std(shuffle)

    primary = _paired_test(lived, shuffle)
    secondary = _paired_test(lived, null)
    t_stat = primary["t_stat"]
    p_value = primary["p_value"]

    null_arm_clean = bool(null) and all(
        abs(value) <= NULL_ARM_MAX_ABS_DELTA for value in null
    )

    # Anti-roadmap: never treat N_effective < design N_PAIRS as decisive.
    underpowered = n_effective < N_PAIRS
    underpowered_reason = (
        f"n_effective={n_effective} < N_PAIRS={N_PAIRS} "
        f"(diversity-gated={n_gated}); N<15 claims forbidden"
        if underpowered
        else ""
    )
    significant = bool(
        not primary["degenerate"]
        and not underpowered
        and p_value < ALPHA
        and (not primary["wilcoxon_gateable"] or primary["wilcoxon_p"] < ALPHA)
    )
    if primary["degenerate"] or not null_arm_clean or underpowered:
        verdict = VERDICT_INCONCLUSIVE
    elif significant and mean_delta_pe_lived < mean_delta_pe_shuffle:
        verdict = VERDICT_H1_SUPPORTED
    elif significant:
        verdict = VERDICT_H1_REJECTED
    else:
        verdict = VERDICT_INCONCLUSIVE

    degenerate_reason = primary["degenerate_reason"] or underpowered_reason

    # Precision smoke gates — dual pools (never collapse into one).
    # v1: usable-pair-only — SMOKE_N3_K5 locked / pre-registered.
    # v2: all audited arms — informational; pair-gate independent.
    smoke_arms_v1 = [
        arm
        for pair in usable
        for arm in (pair.lived, pair.null, pair.shuffle)
    ]
    smoke_arms_v2 = [
        arm
        for pair in results
        for arm in (pair.lived, pair.null, pair.shuffle)
    ]
    null_deltas_v2 = [
        float(pair.null.delta_pe)
        for pair in results
        if _is_finite_delta(pair.null.delta_pe)
    ]
    smoke_gates_v1 = _smoke_gates_block(
        arms=smoke_arms_v1,
        null_deltas=list(null),
        pool=SMOKE_POOL_USABLE_PAIRS,
        pre_registered=True,
    )
    smoke_gates_v2 = _smoke_gates_block(
        arms=smoke_arms_v2,
        null_deltas=null_deltas_v2,
        pool=SMOKE_POOL_ALL_AUDITED,
        pre_registered=False,
    )
    # Backward-compat alias: smoke_gates == locked v1 (do not point at v2).
    smoke_gates = smoke_gates_v1

    return {
        "primary_contrast": "lived_vs_shuffle",
        "primary": primary,
        "secondary_lived_vs_null": secondary,
        "null_arm_clean": null_arm_clean,
        "wilcoxon_p": primary["wilcoxon_p"],
        "degenerate": bool(primary["degenerate"] or underpowered),
        "degenerate_reason": degenerate_reason,
        "underpowered": underpowered,
        "n_gated": n_gated,
        "n_effective": n_effective,
        "diversity_gate": {
            "min_unique": DIVERSITY_MIN_UNIQUE,
            "min_pe_gap": DIVERSITY_MIN_PE_GAP,
            "pe_window_events": PE_WINDOW_EVENTS,
        },
        "niche_ranges": {
            "resource_scarcity": list(NICHE_SCARCITY_RANGE),
            "uncertainty": list(NICHE_UNCERTAINTY_RANGE),
            "social_pressure": list(NICHE_SOCIAL_PRESSURE_RANGE),
            "time_pressure": list(NICHE_TIME_PRESSURE_RANGE),
            "pool_fraction": list(NICHE_POOL_FRACTION_RANGE),
        },
        "mean_delta_pe_lived": mean_delta_pe_lived,
        "mean_delta_pe_null": mean_delta_pe_null,
        "mean_delta_pe_shuffle": mean_delta_pe_shuffle,
        "std_delta_pe_lived": std_delta_pe_lived,
        "std_delta_pe_null": std_delta_pe_null,
        "std_delta_pe_shuffle": std_delta_pe_shuffle,
        "t_stat": t_stat,
        "p_value": p_value,
        "significant": significant,
        "verdict": verdict,
        "alpha": ALPHA,
        "n_pairs": len(results),
        "constraints": dict(_CONSTRAINT_SNAPSHOT),
        "smoke_gates": smoke_gates,
        "smoke_gates_v1": smoke_gates_v1,
        "smoke_gates_v2": smoke_gates_v2,
    }


def write_results_json(
    results: list[PairResult],
    stats: dict[str, Any],
    *,
    lora_choice: str,
) -> Path:
    """Persist Protocol C′ pairs + summary to RESULTS_PATH (indent=2).

    ``lora_choice`` has no default on purpose: the writer cannot recover it
    from the environment, and guessing it would let the file misreport how
    the run was configured (D-004).
    """

    path = RESULTS_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = _json_sanitize(
        {
            "protocol": "C_PRIME",
            "signal_version": SIGNAL_VERSION,
            "n_pairs": N_PAIRS,
            "events_per_arm": EVENTS_PER_ARM,
            "seed_start": SEED_START,
            "pe_window_events": PE_WINDOW_EVENTS,
            "diversity_min_unique": DIVERSITY_MIN_UNIQUE,
            "diversity_min_pe_gap": DIVERSITY_MIN_PE_GAP,
            "temperature": _temperature(),
            "seeds": list(SEEDS),
            "lora_enabled": os.environ.get(LORA_ENABLED_ENV, "0"),
            # D-032 — see the same block in run_cprime_multigen: the env var
            # only gates anything under POLARITY_FILTER=nli, so the active gate
            # is reported from its own resolver rather than inferred.
            **describe_polarity_filter(),
            "nli_filter_enabled_env": os.environ.get(NLI_FILTER_ENABLED_ENV, "1"),
            "llm_do_sample": os.environ.get(LLM_DO_SAMPLE_ENV, "0"),
            # D-030. MIN_PAIRS is uncalibrated (I1.5), so without these counts
            # "few but strong pairs" reads exactly like "the filter emptied the
            # training set". The floor ships uncalibrated and says so.
            "pair_filter": _pair_filter_report(),
            "tool_identity": build_tool_identity(
                lora_choice=lora_choice,
                seeds=list(SEEDS),
            ),
            "pairs": [asdict(r) for r in results],
            "summary": stats,
        }
    )
    path.write_text(json.dumps(payload, indent=2, allow_nan=False), encoding="utf-8")
    print(f"Wrote {path}", flush=True)
    return path


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Protocol C′ — lived/null/shuffle")
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
    return parser


def main(argv: list[str] | None = None) -> None:
    """CLI: run Protocol C′, print summary, write JSON."""

    args = build_arg_parser().parse_args(argv)
    lora_choice = resolve_lora_choice(args.lora)
    if lora_choice == LORA_CHOICE_OFF:
        print(
            "[PROTOCOL_C_PRIME][WARN] LoRA training is OFF — lived and shuffle "
            "differ from null only in bookkeeping, not in weights.",
            flush=True,
        )

    print(
        f"Protocol C′ — N={N_PAIRS} seeds, {EVENTS_PER_ARM} events/arm, "
        f"PE window W={PE_WINDOW_EVENTS}",
        flush=True,
    )
    print(
        f"Signal: {SIGNAL_VERSION} | LORA: {os.environ.get(LORA_ENABLED_ENV, '0')} "
        f"| sample: {os.environ.get(LLM_DO_SAMPLE_ENV, '0')} "
        f"| diversity K>={DIVERSITY_MIN_UNIQUE}",
        flush=True,
    )
    print(f"Monitor: watch -n 30 cat {HEARTBEAT_PATH}")
    print(f"Resume:  re-run same command — checkpoint auto-loads")
    print(f"Checkpoint: {CHECKPOINT_PATH}")
    results = run_protocol_c_prime()
    stats_out = _compute_stats(results)
    path = write_results_json(results, stats_out, lora_choice=lora_choice)

    print("\n=== RESULTS ===", flush=True)
    print(
        f"mean ΔPE lived:   {stats_out['mean_delta_pe_lived']:.4f} "
        f"(sd {stats_out['std_delta_pe_lived']:.4f})",
        flush=True,
    )
    print(
        f"mean ΔPE shuffle: {stats_out['mean_delta_pe_shuffle']:.4f} "
        f"(sd {stats_out['std_delta_pe_shuffle']:.4f})",
        flush=True,
    )
    print(f"mean ΔPE null:    {stats_out['mean_delta_pe_null']:.4f}", flush=True)
    print(
        f"n_effective={stats_out['n_effective']} "
        f"n_gated={stats_out['n_gated']} "
        f"null_arm_clean={stats_out['null_arm_clean']}",
        flush=True,
    )
    print(
        f"primary lived vs shuffle: t={stats_out['t_stat']:.3f} "
        f"p={stats_out['p_value']:.4f} wilcoxon_p={stats_out['wilcoxon_p']:.4f}",
        flush=True,
    )
    if stats_out["degenerate"]:
        print(
            f"[PROTOCOL_C_PRIME][WARN] test not run: "
            f"{stats_out['degenerate_reason']}",
            flush=True,
        )
    if not stats_out["null_arm_clean"]:
        print(
            "[PROTOCOL_C_PRIME][WARN] NULL arm ΔPE is not zero — the control "
            "was disturbed; treat every arm as contaminated",
            flush=True,
        )
    print(f"Verdict: {stats_out['verdict']}", flush=True)
    print(f"Results: {path}", flush=True)


if __name__ == "__main__":
    main()
