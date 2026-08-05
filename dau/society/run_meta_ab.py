"""Meta-Observer A/B harness — Layer 5 actuators on vs off, same scenario.

Post-DAERM / magnitude-decoupling protocol:
  META_ON  — production meta_observer_node (actuators live)
  META_OFF — pass-through node (wiring intact, state unchanged)

Default CLI: 3 replicates × 30 events per arm, deterministic T=0 seed,
AB_ENERGY_FLOOR=0.15, inter-run sleep for Groq free-tier protection.

Unit tests use the lightweight NPC System-1 arm (no Groq).
No trait injection. No LLM-as-judge. No architectural module edits.
"""

from __future__ import annotations

import os
import statistics
import tempfile
import time
from dataclasses import dataclass, field
from typing import Any

import dau.foundation.graph as graph_mod
from dau.foundation.constraints import build_default_constraints
from dau.foundation.delta import DeltaClassification, classify_delta
from dau.foundation.graph import (
    agent_node,
    build_graph,
    evaluator_node,
    get_pe_event_log,
    reset_pe_event_log,
    social_pre_node,
)
from dau.foundation.lod import CognitiveMode, LODState
import dau.foundation.meta_observer as meta_observer_mod
from dau.foundation.meta_observer import (
    bind_memory_store,
    meta_observer_node,
    unbind_memory_store,
)
from dau.foundation.state import DAUAgentState, InternalState
from dau.memory.store import MemoryStore
from dau.society.environment import EnvironmentState
from dau.society.run_convention_pilot import SENSOR_LABEL

# ---------------------------------------------------------------------------
# A/B parameters (no magic numbers in logic)
# ---------------------------------------------------------------------------

AB_N_CYCLES: int = 30
AB_N_REPLICATES: int = 3
AB_AGENT_ID_ON: str = "meta-ab-on-0"
AB_AGENT_ID_OFF: str = "meta-ab-off-0"
AB_OPPONENT_ID: str = "meta-ab-npc-opponent-0"
AB_MODE_ON: str = "meta_on"
AB_MODE_OFF: str = "meta_off"
TERMINATION_ENERGY: float = 0.05
# Fixed-horizon pad — matches production graph.AB_ENERGY_FLOOR (DAERM era).
AB_ENERGY_FLOOR: float = 0.15
M_RATIO_MISSING: float = -1.0
MEMORY_SCORE_MISSING: float = -1.0
EMPTY_COUNT: int = 0
EMPTY_MEAN: float = 0.0
EMPTY_STD: float = 0.0

# Deterministic seed-replay protocol (noise probe): env mirrors graph.py.
DETERMINISTIC_TEMPERATURE: float = 0.0
DEFAULT_REPLAY_SEED: int = 42
LLM_TEMPERATURE_ENV: str = "DAU_LLM_TEMPERATURE"
LLM_SEED_ENV: str = "DAU_LLM_SEED"
META_AB_SYSTEM2_ENV: str = "DAU_META_AB_SYSTEM2"
META_AB_CYCLES_ENV: str = "DAU_META_AB_CYCLES"
META_AB_DETERMINISTIC_ENV: str = "DAU_META_AB_DETERMINISTIC"
META_AB_REPLICATES_ENV: str = "DAU_META_AB_REPLICATES"
META_AB_LIGHTWEIGHT_ENV: str = "DAU_META_AB_LIGHTWEIGHT"

# Groq free-tier spacing between independent runs.
AB_INTER_RUN_SLEEP_S: float = 3.0

STREAM_NODES_PER_EVENT: int = 4
STREAM_RECURSION_HEADROOM: int = 10

# Verdict: difference inside combined replicate noise → NO_DIFF.
NO_DIFF_STD_MULTIPLIER: float = 1.0
NO_DIFF_ABS_FLOOR: float = 1e-6
OVERALL_WIN_MARGIN: int = 1

# Metric polarity: True → higher ON favours META_ON; False → lower is better.
METRIC_HIGHER_IS_BETTER: dict[str, bool] = {
    "delta_mean": True,
    "delta_std": True,
    "trauma_count": False,
    "deep_count": True,
    "system2_cycles": True,
    "memory_score_mean": True,
    "pe_mean": False,
    "final_energy": True,
}
REPORT_METRICS: tuple[str, ...] = tuple(METRIC_HIGHER_IS_BETTER.keys())

CLASS_TRAUMA: str = DeltaClassification.TRAUMA.value
CLASS_DEEP: str = DeltaClassification.DEEP.value
CLASS_NOISE: str = "NOISE"


@dataclass
class CycleTelemetry:
    """One cycle snapshot after evaluator (+ optional meta)."""

    cycle: int
    energy: float
    delta_magnitude: float
    m_ratio: float
    cognitive_mode: str
    prediction_error: float = EMPTY_MEAN
    memory_score: float = MEMORY_SCORE_MISSING


@dataclass
class ABRunMetrics:
    """Aggregated metrics for one independent run."""

    delta_mean: float = EMPTY_MEAN
    delta_std: float = EMPTY_STD
    trauma_count: int = EMPTY_COUNT
    deep_count: int = EMPTY_COUNT
    system2_cycles: int = EMPTY_COUNT
    memory_score_mean: float = EMPTY_MEAN
    pe_mean: float = EMPTY_MEAN
    final_energy: float = EMPTY_MEAN
    n_events: int = EMPTY_COUNT
    ended_early: bool = False


@dataclass
class ABRunResult:
    """Single arm of the A/B (meta on or off)."""

    mode: str
    sensor_label: str
    n_cycles: int
    cycles: list[CycleTelemetry] = field(default_factory=list)
    final_energy: float = 0.0
    mean_delta: float = 0.0
    mean_m_ratio: float = 0.0
    ended_on_energy: bool = False
    system2_cycles: int = 0
    metrics: ABRunMetrics = field(default_factory=ABRunMetrics)


@dataclass
class ABComparison:
    """Paired on/off summary (single replicate, lightweight path)."""

    sensor_label: str
    on: ABRunResult
    off: ABRunResult
    delta_mean_diff: float
    m_ratio_mean_diff: float


@dataclass
class MetricAggregate:
    """Mean ± std across replicates for one arm."""

    mean: float
    std: float
    values: list[float] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def meta_observer_node_off(state: DAUAgentState) -> dict[str, Any]:
    """META_OFF pass-through — graph wiring intact, actuators inactive.

    Returns an empty partial update so LangGraph / _merge_state leave state
    unchanged (equivalent to ``return state`` with no writes).
    """

    _ = state
    return {}


def _merge_state(state: DAUAgentState, patch: dict[str, Any]) -> DAUAgentState:
    """Apply a LangGraph-style partial update onto a DAUAgentState."""

    if not patch:
        return state
    return state.model_copy(update=patch)


def _ensure_system1(state: DAUAgentState) -> DAUAgentState:
    """Force System 1 so A/B smoke needs no Groq tokens."""

    lod = state.lod_state
    if not isinstance(lod, LODState):
        lod = LODState()
    lod = LODState(
        mode=CognitiveMode.SYSTEM_1,
        t_cognitive=0.0,
        consecutive_low_steps=int(lod.consecutive_low_steps),
        last_escalation_event=int(lod.last_escalation_event),
    )
    return state.model_copy(update={"lod_state": lod})


def _ensure_system2(state: DAUAgentState) -> DAUAgentState:
    """Force System 2 for optional live Groq A/B arm."""

    lod = state.lod_state
    if not isinstance(lod, LODState):
        lod = LODState()
    lod = LODState(
        mode=CognitiveMode.SYSTEM_2,
        t_cognitive=1.0,
        consecutive_low_steps=0,
        last_escalation_event=int(lod.last_escalation_event),
    )
    return state.model_copy(update={"lod_state": lod})


def _initial_state(agent_id: str) -> DAUAgentState:
    """Fresh agent with shared-pool env stub and System 1 LOD."""

    return DAUAgentState(
        agent_id=agent_id,
        opponent_id=AB_OPPONENT_ID,
        environment=build_default_constraints(),
        env_state=EnvironmentState(),
        lod_state=LODState(mode=CognitiveMode.SYSTEM_1),
        internal_state=InternalState(),
    )


def _telemetry(cycle: int, state: DAUAgentState) -> CycleTelemetry:
    """Extract deterministic cycle metrics from state."""

    delta_magnitude = 0.0
    if state.delta_log:
        delta_magnitude = float(state.delta_log[-1].magnitude)
    m_ratio = M_RATIO_MISSING
    if state.self_model is not None:
        m_ratio = float(state.self_model.m_ratio)
    mode = CognitiveMode.SYSTEM_1.value
    if isinstance(state.lod_state, LODState):
        mode = state.lod_state.mode.value
    return CycleTelemetry(
        cycle=cycle,
        energy=float(state.internal_state.energy),
        delta_magnitude=delta_magnitude,
        m_ratio=m_ratio,
        cognitive_mode=mode,
    )


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


def _metrics_from_delta_and_pe(
    *,
    magnitudes: list[float],
    trauma_count: int,
    deep_count: int,
    system2_cycles: int,
    memory_scores: list[float],
    pe_values: list[float],
    final_energy: float,
    n_events: int,
    ended_early: bool,
) -> ABRunMetrics:
    """Pack one-run aggregates into ABRunMetrics."""

    return ABRunMetrics(
        delta_mean=_mean(magnitudes),
        delta_std=_std(magnitudes),
        trauma_count=int(trauma_count),
        deep_count=int(deep_count),
        system2_cycles=int(system2_cycles),
        memory_score_mean=_mean(memory_scores),
        pe_mean=_mean(pe_values),
        final_energy=float(final_energy),
        n_events=int(n_events),
        ended_early=bool(ended_early),
    )


def _metrics_from_state(
    state: DAUAgentState,
    *,
    system2_cycles: int,
    memory_scores: list[float],
    pe_rows: list[dict[str, Any]] | None = None,
    max_events: int = AB_N_CYCLES,
) -> ABRunMetrics:
    """Derive report metrics from final state + optional PE audit rows."""

    magnitudes = [float(r.magnitude) for r in state.delta_log]
    trauma_count = EMPTY_COUNT
    deep_count = EMPTY_COUNT
    for record in state.delta_log:
        label = classify_delta(record)
        if label is DeltaClassification.TRAUMA:
            trauma_count += 1
        elif label is DeltaClassification.DEEP:
            deep_count += 1

    if pe_rows is None:
        pe_rows = get_pe_event_log()
    pe_values = [float(row["prediction_error"]) for row in pe_rows]
    if not magnitudes and pe_rows:
        magnitudes = [float(row["delta_magnitude"]) for row in pe_rows]
        trauma_count = sum(
            1 for row in pe_rows if str(row.get("delta_class")) == CLASS_TRAUMA
        )
        deep_count = sum(
            1 for row in pe_rows if str(row.get("delta_class")) == CLASS_DEEP
        )

    n_events = len(state.event_log) if state.event_log else len(pe_rows)
    ended_early = n_events < max_events
    return _metrics_from_delta_and_pe(
        magnitudes=magnitudes,
        trauma_count=trauma_count,
        deep_count=deep_count,
        system2_cycles=system2_cycles,
        memory_scores=memory_scores,
        pe_values=pe_values,
        final_energy=float(state.internal_state.energy),
        n_events=n_events,
        ended_early=ended_early,
    )


def _state_from_stream(values: Any) -> DAUAgentState:
    """Normalize stream values into DAUAgentState."""

    if isinstance(values, DAUAgentState):
        return values
    if isinstance(values, dict):
        return DAUAgentState.model_validate(values)
    raise TypeError(f"Unexpected stream value type: {type(values)!r}")


def _open_temp_memory_store() -> tuple[MemoryStore, tempfile.TemporaryDirectory[str]]:
    """Per-run isolated MemoryStore (no cross-arm contamination)."""

    tmp = tempfile.TemporaryDirectory(prefix="dau_meta_ab_")
    store = MemoryStore(
        chroma_path=os.path.join(tmp.name, "chroma"),
        sqlite_path=os.path.join(tmp.name, "memory.db"),
    )
    return store, tmp


# ---------------------------------------------------------------------------
# Lightweight arm (unit tests / offline NPC)
# ---------------------------------------------------------------------------


def run_ab_arm(
    *,
    agent_id: str,
    meta_enabled: bool,
    n_cycles: int = AB_N_CYCLES,
    force_system_2: bool = False,
) -> ABRunResult:
    """Run one A/B arm for n_cycles or until energy exhaustion.

    Lightweight path: manual node chain (no build_graph). META_OFF uses
    meta_observer_node_off pass-through. Pins System 1 unless force_system_2.
    """

    mode = AB_MODE_ON if meta_enabled else AB_MODE_OFF
    reset_pe_event_log()
    state = _initial_state(agent_id)
    if force_system_2:
        state = _ensure_system2(state)
    else:
        state = _ensure_system1(state)

    cycles: list[CycleTelemetry] = []
    ended_on_energy = False
    system2_cycles = 0
    memory_scores: list[float] = []

    for cycle in range(1, n_cycles + 1):
        if force_system_2:
            # Live A/B: LOD persists so Meta lod_override can keep System 2.
            pass
        else:
            # NPC protocol: pin System 1 every cycle (no Groq in unit tests).
            state = _ensure_system1(state)

        state = _merge_state(state, social_pre_node(state))
        state = _merge_state(state, agent_node(state))
        state = _merge_state(state, evaluator_node(state))

        if meta_enabled:
            state = _merge_state(state, meta_observer_node(state))
        else:
            # Pass-through: wiring preserved, actuators off (state unchanged).
            state = _merge_state(state, meta_observer_node_off(state))

        if state.self_model is not None:
            memory_scores.extend(
                float(s) for s in state.self_model.memory_retrieval_scores
            )
        elif state.retrieval_context:
            for entry in state.retrieval_context:
                if not isinstance(entry, dict):
                    continue
                if "memory_score" in entry:
                    memory_scores.append(float(entry["memory_score"]))
                elif "score" in entry:
                    memory_scores.append(float(entry["score"]))

        # Fixed-horizon protocol: restore energy floor so PE shock
        # does not collapse the A/B window to a single cycle.
        internal = state.internal_state.model_copy(deep=True)
        if float(internal.energy) < AB_ENERGY_FLOOR:
            internal.energy = AB_ENERGY_FLOOR
            state = state.model_copy(update={"internal_state": internal})

        telem = _telemetry(cycle, state)
        if telem.cognitive_mode == CognitiveMode.SYSTEM_2.value:
            system2_cycles += 1
        cycles.append(telem)
        if float(state.internal_state.energy) <= TERMINATION_ENERGY:
            ended_on_energy = True
            break

    deltas = [c.delta_magnitude for c in cycles]
    ratios = [c.m_ratio for c in cycles if c.m_ratio >= 0.0]
    mean_delta = _mean(deltas)
    mean_m = _mean(ratios) if ratios else M_RATIO_MISSING
    metrics = _metrics_from_state(
        state,
        system2_cycles=system2_cycles,
        memory_scores=memory_scores,
        pe_rows=get_pe_event_log(),
        max_events=n_cycles,
    )

    return ABRunResult(
        mode=mode,
        sensor_label=SENSOR_LABEL,
        n_cycles=len(cycles),
        cycles=cycles,
        final_energy=float(state.internal_state.energy),
        mean_delta=mean_delta,
        mean_m_ratio=mean_m,
        ended_on_energy=ended_on_energy,
        system2_cycles=system2_cycles,
        metrics=metrics,
    )


def run_meta_ab(
    n_cycles: int = AB_N_CYCLES,
    *,
    force_system_2: bool = False,
) -> ABComparison:
    """Paired Meta-Observer on/off runs under identical cycle budget."""

    on = run_ab_arm(
        agent_id=AB_AGENT_ID_ON,
        meta_enabled=True,
        n_cycles=n_cycles,
        force_system_2=force_system_2,
    )
    off = run_ab_arm(
        agent_id=AB_AGENT_ID_OFF,
        meta_enabled=False,
        n_cycles=n_cycles,
        force_system_2=force_system_2,
    )
    return ABComparison(
        sensor_label=SENSOR_LABEL,
        on=on,
        off=off,
        delta_mean_diff=on.mean_delta - off.mean_delta,
        m_ratio_mean_diff=on.mean_m_ratio - off.mean_m_ratio,
    )


def comparison_summary(comp: ABComparison) -> dict[str, Any]:
    """JSON-friendly A/B summary."""

    return {
        "sensor_label": comp.sensor_label,
        "delta_mean_diff": comp.delta_mean_diff,
        "m_ratio_mean_diff": comp.m_ratio_mean_diff,
        "system2_cycles_diff": (
            comp.on.system2_cycles - comp.off.system2_cycles
        ),
        "on": {
            "mode": comp.on.mode,
            "n_cycles": comp.on.n_cycles,
            "mean_delta": comp.on.mean_delta,
            "mean_m_ratio": comp.on.mean_m_ratio,
            "final_energy": comp.on.final_energy,
            "ended_on_energy": comp.on.ended_on_energy,
            "system2_cycles": comp.on.system2_cycles,
        },
        "off": {
            "mode": comp.off.mode,
            "n_cycles": comp.off.n_cycles,
            "mean_delta": comp.off.mean_delta,
            "mean_m_ratio": comp.off.mean_m_ratio,
            "final_energy": comp.off.final_energy,
            "ended_on_energy": comp.off.ended_on_energy,
            "system2_cycles": comp.off.system2_cycles,
        },
    }


# ---------------------------------------------------------------------------
# Production-graph protocol arm (CLI)
# ---------------------------------------------------------------------------


def run_production_arm(
    *,
    agent_id: str,
    meta_enabled: bool,
    n_cycles: int = AB_N_CYCLES,
    seed: int = DEFAULT_REPLAY_SEED,
) -> ABRunResult:
    """One arm via production build_graph wiring (social→agent→eval→meta).

    META_OFF monkey-patches meta_observer_node to meta_observer_node_off
    without changing graph topology. Does not edit architectural source files.
    """

    mode = AB_MODE_ON if meta_enabled else AB_MODE_OFF
    graph_mod.load_env_file()
    os.environ[LLM_SEED_ENV] = str(seed)

    original_meta = graph_mod.meta_observer_node
    original_agent = graph_mod.agent_node
    original_retrieve = graph_mod.retrieve_relevant
    original_meta_retrieve = meta_observer_mod.retrieve_relevant
    original_max_events = graph_mod.MAX_EVENTS
    original_energy_floor = graph_mod.AB_ENERGY_FLOOR

    system2_counter = {"n": EMPTY_COUNT}
    memory_scores: list[float] = []

    def _counting_agent(state: DAUAgentState) -> dict[str, Any]:
        lod = state.lod_state
        if isinstance(lod, LODState) and graph_mod.should_run_llm(lod):
            system2_counter["n"] += 1
        return original_agent(state)

    def _scoring_retrieve(*args: Any, **kwargs: Any) -> list[dict[str, Any]]:
        results = original_retrieve(*args, **kwargs)
        for entry in results:
            if "score" in entry:
                memory_scores.append(float(entry["score"]))
            elif "memory_score" in entry:
                memory_scores.append(float(entry["memory_score"]))
        return results

    store: MemoryStore | None = None
    tmp: tempfile.TemporaryDirectory[str] | None = None
    reset_pe_event_log()

    try:
        graph_mod.MAX_EVENTS = int(n_cycles)
        graph_mod.AB_ENERGY_FLOOR = float(AB_ENERGY_FLOOR)
        if meta_enabled:
            graph_mod.meta_observer_node = original_meta
        else:
            graph_mod.meta_observer_node = meta_observer_node_off
        graph_mod.agent_node = _counting_agent
        graph_mod.retrieve_relevant = _scoring_retrieve
        meta_observer_mod.retrieve_relevant = _scoring_retrieve

        store, tmp = _open_temp_memory_store()
        graph_mod._memory_stores[agent_id] = store
        graph_mod._memory_written[agent_id] = 0
        bind_memory_store(agent_id, store)

        initial = _initial_state(agent_id)
        stream_limit = n_cycles * STREAM_NODES_PER_EVENT + STREAM_RECURSION_HEADROOM
        result: Any = initial
        app = build_graph(checkpointer=None)
        for values in app.stream(
            initial,
            config={"recursion_limit": stream_limit},
            stream_mode="values",
        ):
            result = values

        state = _state_from_stream(result)
        pe_rows = get_pe_event_log()
        metrics = _metrics_from_state(
            state,
            system2_cycles=system2_counter["n"],
            memory_scores=list(memory_scores),
            pe_rows=pe_rows,
            max_events=n_cycles,
        )
        if metrics.ended_early:
            print(
                f"[META_AB] early stop mode={mode} seed={seed} "
                f"events={metrics.n_events}/{n_cycles} "
                f"energy={metrics.final_energy:.3f}",
                flush=True,
            )

        return ABRunResult(
            mode=mode,
            sensor_label=SENSOR_LABEL,
            n_cycles=metrics.n_events,
            cycles=[],
            final_energy=metrics.final_energy,
            mean_delta=metrics.delta_mean,
            mean_m_ratio=(
                float(state.self_model.m_ratio)
                if state.self_model is not None
                else M_RATIO_MISSING
            ),
            ended_on_energy=metrics.ended_early,
            system2_cycles=metrics.system2_cycles,
            metrics=metrics,
        )
    finally:
        unbind_memory_store(agent_id)
        graph_mod._memory_stores.pop(agent_id, None)
        graph_mod._memory_written.pop(agent_id, None)
        graph_mod.meta_observer_node = original_meta
        graph_mod.agent_node = original_agent
        graph_mod.retrieve_relevant = original_retrieve
        meta_observer_mod.retrieve_relevant = original_meta_retrieve
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


def _aggregate_metric(
    runs: list[ABRunResult],
    attr: str,
) -> MetricAggregate:
    """Mean ± std of one metric across replicate runs."""

    values = [float(getattr(run.metrics, attr)) for run in runs]
    return MetricAggregate(mean=_mean(values), std=_std(values), values=values)


def _verdict_for_metric(
    on_agg: MetricAggregate,
    off_agg: MetricAggregate,
    *,
    higher_is_better: bool,
) -> str:
    """ON_BETTER / OFF_BETTER / NO_DIFF from replicate means and noise."""

    diff = on_agg.mean - off_agg.mean
    noise = (on_agg.std + off_agg.std) * NO_DIFF_STD_MULTIPLIER
    threshold = max(noise, NO_DIFF_ABS_FLOOR)
    if abs(diff) <= threshold:
        return "NO_DIFF"
    on_wins = diff > 0 if higher_is_better else diff < 0
    return "ON_BETTER" if on_wins else "OFF_BETTER"


def _overall_verdict(verdicts: list[str]) -> str:
    """YES / NO / UNCLEAR from per-metric verdicts."""

    on_wins = sum(1 for v in verdicts if v == "ON_BETTER")
    off_wins = sum(1 for v in verdicts if v == "OFF_BETTER")
    if on_wins > off_wins and (on_wins - off_wins) >= OVERALL_WIN_MARGIN:
        return "YES"
    if off_wins > on_wins and (off_wins - on_wins) >= OVERALL_WIN_MARGIN:
        return "NO"
    return "UNCLEAR"


def format_protocol_report(
    on_runs: list[ABRunResult],
    off_runs: list[ABRunResult],
) -> str:
    """Render the META_ON vs META_OFF mean±std table + OVERALL line."""

    lines: list[str] = [
        "=== DAU Meta-Observer A/B (post-DAERM / magnitude decoupling) ===",
        f"replicates={len(on_runs)}  events/run={AB_N_CYCLES}  "
        f"floor={AB_ENERGY_FLOOR}  deterministic=1",
        "",
    ]
    verdicts: list[str] = []
    for name in REPORT_METRICS:
        on_agg = _aggregate_metric(on_runs, name)
        off_agg = _aggregate_metric(off_runs, name)
        diff = on_agg.mean - off_agg.mean
        verdict = _verdict_for_metric(
            on_agg,
            off_agg,
            higher_is_better=METRIC_HIGHER_IS_BETTER[name],
        )
        verdicts.append(verdict)
        sign = "+" if diff >= 0 else ""
        lines.append(
            f"{name:18s} "
            f"ON={on_agg.mean:.3f}±{on_agg.std:.3f}  "
            f"OFF={off_agg.mean:.3f}±{off_agg.std:.3f}  "
            f"diff={sign}{diff:.3f}  {verdict}"
        )

    overall = _overall_verdict(verdicts)
    lines.append("")
    lines.append(
        f"OVERALL: META_ON sistematik avantaj sağlıyor mu? {overall}"
    )
    for idx, run in enumerate(on_runs):
        if run.metrics.ended_early:
            lines.append(
                f"  note: META_ON run[{idx}] early stop "
                f"events={run.metrics.n_events}"
            )
    for idx, run in enumerate(off_runs):
        if run.metrics.ended_early:
            lines.append(
                f"  note: META_OFF run[{idx}] early stop "
                f"events={run.metrics.n_events}"
            )
    return "\n".join(lines)


def run_meta_ab_protocol(
    *,
    n_cycles: int = AB_N_CYCLES,
    n_replicates: int = AB_N_REPLICATES,
    inter_run_sleep_s: float = AB_INTER_RUN_SLEEP_S,
) -> tuple[list[ABRunResult], list[ABRunResult]]:
    """3×ON + 3×OFF production-graph protocol with matched seeds per replicate."""

    on_runs: list[ABRunResult] = []
    off_runs: list[ABRunResult] = []
    total_runs = n_replicates * 2
    run_index = 0

    for rep in range(n_replicates):
        seed = DEFAULT_REPLAY_SEED + rep
        for meta_enabled, bucket, label in (
            (True, on_runs, "META_ON"),
            (False, off_runs, "META_OFF"),
        ):
            run_index += 1
            agent_id = (
                f"{AB_AGENT_ID_ON}-r{rep}"
                if meta_enabled
                else f"{AB_AGENT_ID_OFF}-r{rep}"
            )
            print(
                f"[META_AB] run {run_index}/{total_runs} "
                f"{label} rep={rep} seed={seed} events={n_cycles}",
                flush=True,
            )
            result = run_production_arm(
                agent_id=agent_id,
                meta_enabled=meta_enabled,
                n_cycles=n_cycles,
                seed=seed,
            )
            bucket.append(result)
            print(
                f"[META_AB] done {label} events={result.metrics.n_events} "
                f"delta_mean={result.metrics.delta_mean:.3f} "
                f"s2={result.metrics.system2_cycles} "
                f"energy={result.metrics.final_energy:.3f}",
                flush=True,
            )
            if run_index < total_runs:
                time.sleep(inter_run_sleep_s)

    return on_runs, off_runs


def _truthy_env(name: str) -> bool:
    """Parse common truthy env strings."""

    return os.environ.get(name, "").strip() in {"1", "true", "TRUE", "yes"}


def _apply_deterministic_env() -> dict[str, Any]:
    """Force T=0 + fixed seed for Meta A/B noise probe when requested."""

    protocol: dict[str, Any] = {
        "deterministic": False,
        "temperature": os.environ.get(LLM_TEMPERATURE_ENV, "").strip() or None,
        "seed": os.environ.get(LLM_SEED_ENV, "").strip() or None,
    }
    if not _truthy_env(META_AB_DETERMINISTIC_ENV):
        return protocol
    os.environ[LLM_TEMPERATURE_ENV] = str(DETERMINISTIC_TEMPERATURE)
    if not os.environ.get(LLM_SEED_ENV, "").strip():
        os.environ[LLM_SEED_ENV] = str(DEFAULT_REPLAY_SEED)
    protocol["deterministic"] = True
    protocol["temperature"] = os.environ[LLM_TEMPERATURE_ENV]
    protocol["seed"] = os.environ[LLM_SEED_ENV]
    return protocol


def main() -> None:
    """CLI: Meta A/B protocol (production graph) or lightweight paired smoke.

    Default: DAU_META_AB_DETERMINISTIC=1 protocol — 3×30 ON/OFF, report table.
    Smoke: DAU_META_AB_LIGHTWEIGHT=1 — single paired NPC arm (no Groq).
    Optional: DAU_META_AB_SYSTEM2=1 with lightweight forces System 2.
    """

    graph_mod.load_env_file()
    # Protocol defaults: enable deterministic probe unless explicitly disabled.
    if META_AB_DETERMINISTIC_ENV not in os.environ:
        os.environ[META_AB_DETERMINISTIC_ENV] = "1"
    protocol = _apply_deterministic_env()

    if _truthy_env(META_AB_LIGHTWEIGHT_ENV):
        force_s2 = _truthy_env(META_AB_SYSTEM2_ENV)
        n_cycles_raw = os.environ.get(META_AB_CYCLES_ENV, "").strip()
        n_cycles = int(n_cycles_raw) if n_cycles_raw else AB_N_CYCLES
        label = "System 2 / Groq" if force_s2 else "NPC System 1"
        if protocol["deterministic"]:
            label = (
                f"{label} | deterministic T={protocol['temperature']} "
                f"seed={protocol['seed']}"
            )
        comp = run_meta_ab(n_cycles=n_cycles, force_system_2=force_s2)
        summary = comparison_summary(comp)
        summary["protocol"] = protocol
        print(f"=== DAU Meta-Observer A/B ({label}) ===")
        for key, value in summary.items():
            print(f"{key}={value}")
        return

    n_cycles_raw = os.environ.get(META_AB_CYCLES_ENV, "").strip()
    n_cycles = int(n_cycles_raw) if n_cycles_raw else AB_N_CYCLES
    n_rep_raw = os.environ.get(META_AB_REPLICATES_ENV, "").strip()
    n_replicates = int(n_rep_raw) if n_rep_raw else AB_N_REPLICATES

    on_runs, off_runs = run_meta_ab_protocol(
        n_cycles=n_cycles,
        n_replicates=n_replicates,
    )
    print()
    print(format_protocol_report(on_runs, off_runs))


if __name__ == "__main__":
    main()
