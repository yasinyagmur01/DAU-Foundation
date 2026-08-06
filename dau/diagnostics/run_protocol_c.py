"""Protocol C — Seed-Locked Counterfactual Meta ON/OFF (Layer 5 empirics).

Paired sampling: for each Seed_k in 1001..1040, run META_OFF then META_ON
with identical seeds (random / numpy / Groq). T=0.2 keeps System 2 alive
while locking LLM noise so Δy_k is attributable to meta intervention.

No architectural module edits. No trait injection. No LLM-as-judge.
"""

from __future__ import annotations

import json
import os
import random
import statistics
import tempfile
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
from scipy import stats

import dau.foundation.graph as graph_mod
import dau.foundation.meta_observer as meta_observer_mod
from dau.foundation.constraints import build_default_constraints
from dau.foundation.drift import DriftState
from dau.foundation.graph import (
    build_graph,
    get_pe_event_log,
    reset_pe_event_log,
)
from dau.foundation.lod import CognitiveMode, LODState
from dau.foundation.meta_observer import bind_memory_store, unbind_memory_store
from dau.foundation.state import DAUAgentState, InternalState
from dau.memory.store import MemoryStore
from dau.society.environment import EnvironmentState

# ---------------------------------------------------------------------------
# Protocol C constants (no magic numbers in logic)
# ---------------------------------------------------------------------------

N_PAIRS: int = 40
EVENTS_PER_RUN: int = 50
LLM_TEMPERATURE: float = 0.2
SEED_START: int = 1001
SEED_END_INCLUSIVE: int = 1040
SEEDS: list[int] = list(range(SEED_START, SEED_END_INCLUSIVE + 1))
AB_ENERGY_FLOOR: float = 0.15

INTER_PAIR_SLEEP_S: float = 5.0
PROGRESS_EVERY_N_PAIRS: int = 5
ALPHA: float = 0.05

LLM_TEMPERATURE_ENV: str = "DAU_LLM_TEMPERATURE"
LLM_SEED_ENV: str = "DAU_LLM_SEED"

STREAM_NODES_PER_EVENT: int = 4
STREAM_RECURSION_HEADROOM: int = 10

AGENT_ID_OFF_PREFIX: str = "protocol-c-off"
AGENT_ID_ON_PREFIX: str = "protocol-c-on"
OPPONENT_ID: str = "protocol-c-npc-opponent"

CLASS_TRAUMA: str = "TRAUMA"
EMPTY_COUNT: int = 0
EMPTY_MEAN: float = 0.0
EMPTY_STD: float = 0.0
MEMORY_SCORE_MISSING: float = 0.0

RESULTS_DIR_NAME: str = "dau_runs"
RESULTS_FILE_NAME: str = "protocol_c_results.json"

# Module-level LLM audit (reset per process; accumulate across pairs).
_LLM_CALL_COUNT: int = EMPTY_COUNT
_RATE_LIMIT_FALLBACKS: int = EMPTY_COUNT
_SYSTEM2_CYCLES_ON: int = EMPTY_COUNT
_SYSTEM2_CYCLES_OFF: int = EMPTY_COUNT
_CYCLE_MEMORY_SCORES: list[float] = []


@dataclass
class EventRow:
    """Per-event telemetry for one arm."""

    pe: float
    magnitude: float
    delta_class: str
    memory_score: float
    gamma: float
    trauma_flag: bool


@dataclass
class ArmResult:
    """One META_ON or META_OFF run under a locked seed."""

    mode: str
    seed: int
    n_events: int
    events: list[EventRow] = field(default_factory=list)
    system2_cycles: int = EMPTY_COUNT
    ended_early: bool = False
    pe_mean: float = EMPTY_MEAN
    trauma_count: int = EMPTY_COUNT
    memory_score_mean: float = EMPTY_MEAN
    gamma_mean: float = EMPTY_MEAN


@dataclass
class PairResult:
    """Seed-locked ON/OFF pair with run-level diffs."""

    seed: int
    mean_delta_pe: float
    trauma_count_on: int
    trauma_count_off: int
    trauma_diff: float
    memory_score_mean_on: float
    memory_score_mean_off: float
    memory_score_diff: float
    gamma_mean_on: float
    gamma_mean_off: float
    gamma_diff: float
    n_events_on: int
    n_events_off: int
    system2_cycles_on: int
    system2_cycles_off: int
    pe_mean_on: float
    pe_mean_off: float


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def meta_observer_node_off(state: DAUAgentState) -> dict[str, Any]:
    """META_OFF pass-through — wiring intact, actuators inactive."""

    _ = state
    return {}


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


def _as_drift(state: DAUAgentState) -> DriftState:
    """Coerce state.drift_state to DriftState."""

    drift = state.drift_state
    return drift if isinstance(drift, DriftState) else DriftState()


def _lock_seeds(seed: int) -> None:
    """Pin Python, NumPy, and Groq seed for counterfactual replay."""

    random.seed(seed)
    np.random.seed(seed)
    os.environ[LLM_SEED_ENV] = str(seed)
    os.environ[LLM_TEMPERATURE_ENV] = str(LLM_TEMPERATURE)


def _initial_state(agent_id: str) -> DAUAgentState:
    """Fresh agent with System 2 substrate (Protocol C requires LLM path)."""

    return DAUAgentState(
        agent_id=agent_id,
        opponent_id=OPPONENT_ID,
        environment=build_default_constraints(),
        env_state=EnvironmentState(),
        lod_state=LODState(
            mode=CognitiveMode.SYSTEM_2,
            t_cognitive=1.0,
            consecutive_low_steps=0,
            last_escalation_event=0,
        ),
        internal_state=InternalState(),
    )


def _open_temp_memory_store() -> tuple[MemoryStore, tempfile.TemporaryDirectory[str]]:
    """Per-run isolated MemoryStore (no cross-arm contamination)."""

    tmp = tempfile.TemporaryDirectory(prefix="dau_protocol_c_")
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
    """Force NPC System 1 for one decision (Groq abort path)."""

    prior = graph_mod.should_run_llm
    graph_mod.should_run_llm = lambda _lod: False
    try:
        return original(state)
    finally:
        graph_mod.should_run_llm = prior


def _arm_aggregates(events: list[EventRow]) -> dict[str, float | int]:
    """Compute run-level means/counts from per-event rows."""

    return {
        "pe_mean": _mean([e.pe for e in events]),
        "trauma_count": sum(1 for e in events if e.trauma_flag),
        "memory_score_mean": _mean([e.memory_score for e in events]),
        "gamma_mean": _mean([e.gamma for e in events]),
    }


# ---------------------------------------------------------------------------
# Single arm
# ---------------------------------------------------------------------------


def run_protocol_c_arm(
    *,
    agent_id: str,
    meta_enabled: bool,
    seed: int,
    n_events: int = EVENTS_PER_RUN,
) -> ArmResult:
    """One META_ON/OFF run via production graph under locked Seed_k."""

    global _LLM_CALL_COUNT, _RATE_LIMIT_FALLBACKS
    global _SYSTEM2_CYCLES_ON, _SYSTEM2_CYCLES_OFF

    mode = "META_ON" if meta_enabled else "META_OFF"
    _lock_seeds(seed)
    graph_mod.load_env_file()

    original_meta = graph_mod.meta_observer_node
    original_agent = graph_mod.agent_node
    original_retrieve = graph_mod.retrieve_relevant
    original_meta_retrieve = meta_observer_mod.retrieve_relevant
    original_max_events = graph_mod.MAX_EVENTS
    original_energy_floor = graph_mod.AB_ENERGY_FLOOR

    event_rows: list[EventRow] = []
    system2_counter = {"n": EMPTY_COUNT}
    cycle_scores = _CYCLE_MEMORY_SCORES

    def _scoring_retrieve(*args: Any, **kwargs: Any) -> list[dict[str, Any]]:
        results = original_retrieve(*args, **kwargs)
        for entry in results:
            if "score" in entry:
                cycle_scores.append(float(entry["score"]))
            elif "memory_score" in entry:
                cycle_scores.append(float(entry["memory_score"]))
        return results

    def _counting_agent(state: DAUAgentState) -> dict[str, Any]:
        global _LLM_CALL_COUNT, _RATE_LIMIT_FALLBACKS

        cycle_scores.clear()
        lod = state.lod_state
        if not isinstance(lod, LODState):
            lod = LODState()

        if not graph_mod.should_run_llm(lod):
            return original_agent(state)

        system2_counter["n"] += 1
        _LLM_CALL_COUNT += 1
        print(
            f"[LLM] call=#{_LLM_CALL_COUNT} "
            f"mode={mode} seed={seed} "
            f"event={len(state.event_log)} "
            f"lod={CognitiveMode.SYSTEM_2.value}",
            flush=True,
        )
        try:
            return original_agent(state)
        except Exception as exc:  # noqa: BLE001 — free-tier must not abort life
            if _is_llm_abort_error(exc):
                _RATE_LIMIT_FALLBACKS += 1
                print(
                    f"[LLM] abort → System1 fallback "
                    f"(fallbacks={_RATE_LIMIT_FALLBACKS}): {exc}",
                    flush=True,
                )
                return _run_system1_fallback(original_agent, state)
            raise

    def _telemetry_meta(state: DAUAgentState) -> dict[str, Any]:
        """Run meta (or pass-through) then harvest per-event Protocol C row."""

        if meta_enabled:
            patch = dict(original_meta(state))
        else:
            patch = dict(meta_observer_node_off(state))

        pe_events = get_pe_event_log()
        if not pe_events:
            return patch

        row = pe_events[-1]
        drift = patch.get("drift_state", state.drift_state)
        if not isinstance(drift, DriftState):
            drift = _as_drift(state)
        internal = state.internal_state
        if "internal_state" in patch and isinstance(
            patch["internal_state"], InternalState
        ):
            internal = patch["internal_state"]

        memory_score = (
            _mean(list(cycle_scores)) if cycle_scores else MEMORY_SCORE_MISSING
        )
        gamma = float(internal.compute_endogenous_recovery_rate(drift))
        delta_class = str(row["delta_class"])
        event_rows.append(
            EventRow(
                pe=float(row["prediction_error"]),
                magnitude=float(row["delta_magnitude"]),
                delta_class=delta_class,
                memory_score=float(memory_score),
                gamma=gamma,
                trauma_flag=(delta_class == CLASS_TRAUMA),
            )
        )
        return patch

    store: MemoryStore | None = None
    tmp: tempfile.TemporaryDirectory[str] | None = None
    reset_pe_event_log()

    try:
        graph_mod.MAX_EVENTS = int(n_events)
        graph_mod.AB_ENERGY_FLOOR = float(AB_ENERGY_FLOOR)
        graph_mod.meta_observer_node = _telemetry_meta
        graph_mod.agent_node = _counting_agent
        graph_mod.retrieve_relevant = _scoring_retrieve
        meta_observer_mod.retrieve_relevant = _scoring_retrieve

        store, tmp = _open_temp_memory_store()
        graph_mod._memory_stores[agent_id] = store
        graph_mod._memory_written[agent_id] = 0
        bind_memory_store(agent_id, store)

        initial = _initial_state(agent_id)
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
        n_completed = len(event_rows)
        ended_early = n_completed < n_events
        if ended_early:
            print(
                f"[PROTOCOL_C] early stop mode={mode} seed={seed} "
                f"events={n_completed}/{n_events} "
                f"energy={float(state.internal_state.energy):.3f}",
                flush=True,
            )

        aggs = _arm_aggregates(event_rows)
        if meta_enabled:
            _SYSTEM2_CYCLES_ON += int(system2_counter["n"])
        else:
            _SYSTEM2_CYCLES_OFF += int(system2_counter["n"])

        return ArmResult(
            mode=mode,
            seed=seed,
            n_events=n_completed,
            events=event_rows,
            system2_cycles=int(system2_counter["n"]),
            ended_early=ended_early,
            pe_mean=float(aggs["pe_mean"]),
            trauma_count=int(aggs["trauma_count"]),
            memory_score_mean=float(aggs["memory_score_mean"]),
            gamma_mean=float(aggs["gamma_mean"]),
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


def run_pair(seed: int, pair_index: int) -> PairResult:
    """META_OFF then META_ON under identical Seed_k; compute paired diffs."""

    print(
        f"[PROTOCOL_C] pair={pair_index}/{N_PAIRS} seed={seed} META_OFF …",
        flush=True,
    )
    off = run_protocol_c_arm(
        agent_id=f"{AGENT_ID_OFF_PREFIX}-{seed}",
        meta_enabled=False,
        seed=seed,
        n_events=EVENTS_PER_RUN,
    )
    print(
        f"[PROTOCOL_C] pair={pair_index}/{N_PAIRS} seed={seed} META_ON …",
        flush=True,
    )
    on = run_protocol_c_arm(
        agent_id=f"{AGENT_ID_ON_PREFIX}-{seed}",
        meta_enabled=True,
        seed=seed,
        n_events=EVENTS_PER_RUN,
    )

    n_aligned = min(len(on.events), len(off.events))
    if n_aligned == EMPTY_COUNT:
        mean_delta_pe = EMPTY_MEAN
    else:
        deltas = [
            on.events[t].pe - off.events[t].pe for t in range(n_aligned)
        ]
        mean_delta_pe = _mean(deltas)

    return PairResult(
        seed=seed,
        mean_delta_pe=mean_delta_pe,
        trauma_count_on=on.trauma_count,
        trauma_count_off=off.trauma_count,
        trauma_diff=float(on.trauma_count - off.trauma_count),
        memory_score_mean_on=on.memory_score_mean,
        memory_score_mean_off=off.memory_score_mean,
        memory_score_diff=on.memory_score_mean - off.memory_score_mean,
        gamma_mean_on=on.gamma_mean,
        gamma_mean_off=off.gamma_mean,
        gamma_diff=on.gamma_mean - off.gamma_mean,
        n_events_on=on.n_events,
        n_events_off=off.n_events,
        system2_cycles_on=on.system2_cycles,
        system2_cycles_off=off.system2_cycles,
        pe_mean_on=on.pe_mean,
        pe_mean_off=off.pe_mean,
    )


# ---------------------------------------------------------------------------
# Statistics + report
# ---------------------------------------------------------------------------


def _one_tailed_paired_t_vs_zero(
    deltas: list[float],
) -> tuple[float, float, str]:
    """H0: μ_ΔPE ≥ 0 vs H1: μ_ΔPE < 0 (one-tailed paired / one-sample t)."""

    if len(deltas) < 2:
        return EMPTY_MEAN, 1.0, "H0"
    # Paired ON−OFF diffs already; one-sample t vs 0 ≡ paired t vs zeros.
    result = stats.ttest_1samp(deltas, popmean=0.0, alternative="less")
    t_stat = float(result.statistic)
    p_value = float(result.pvalue)
    verdict = "H1" if p_value < ALPHA else "H0"
    return t_stat, p_value, verdict


def format_results_table(
    pairs: list[PairResult],
    *,
    pe_p: float,
    pe_verdict: str,
    trauma_p: float | None,
) -> str:
    """Render Protocol C results table + OVERALL VERDICT."""

    pe_on = [p.pe_mean_on for p in pairs]
    pe_off = [p.pe_mean_off for p in pairs]
    trauma_on = [float(p.trauma_count_on) for p in pairs]
    trauma_off = [float(p.trauma_count_off) for p in pairs]
    mem_on = [p.memory_score_mean_on for p in pairs]
    mem_off = [p.memory_score_mean_off for p in pairs]
    gamma_on = [p.gamma_mean_on for p in pairs]
    gamma_off = [p.gamma_mean_off for p in pairs]

    pe_diff = _mean(pe_on) - _mean(pe_off)
    trauma_diff = _mean(trauma_on) - _mean(trauma_off)
    mem_diff = _mean(mem_on) - _mean(mem_off)
    gamma_diff = _mean(gamma_on) - _mean(gamma_off)

    trauma_p_str = f"{trauma_p:.3f}" if trauma_p is not None else "—"
    lines = [
        f"=== PROTOCOL C RESULTS (N={len(pairs)} pairs × {EVENTS_PER_RUN} events) ===",
        (
            f"{'Metric':<20}"
            f"{'META_ON':<18}"
            f"{'META_OFF':<18}"
            f"{'Δ(ON-OFF)':<12}"
            f"{'p-value':<10}"
            f"{'verdict'}"
        ),
        (
            f"{'pe_mean':<20}"
            f"{_mean(pe_on):.3f}±{_std(pe_on):.3f}      "
            f"{_mean(pe_off):.3f}±{_std(pe_off):.3f}      "
            f"{pe_diff:+.3f}       "
            f"{pe_p:.3f}      "
            f"{pe_verdict}"
        ),
        (
            f"{'trauma_count':<20}"
            f"{_mean(trauma_on):.2f}±{_std(trauma_on):.2f}        "
            f"{_mean(trauma_off):.2f}±{_std(trauma_off):.2f}        "
            f"{trauma_diff:+.2f}        "
            f"{trauma_p_str:<10}"
            f"—"
        ),
        (
            f"{'memory_score_mean':<20}"
            f"{_mean(mem_on):.3f}±{_std(mem_on):.3f}      "
            f"{_mean(mem_off):.3f}±{_std(mem_off):.3f}      "
            f"{mem_diff:+.3f}       "
            f"{'—':<10}"
            f"—"
        ),
        (
            f"{'gamma_mean':<20}"
            f"{_mean(gamma_on):.3f}±{_std(gamma_on):.3f}      "
            f"{_mean(gamma_off):.3f}±{_std(gamma_off):.3f}      "
            f"{gamma_diff:+.3f}       "
            f"{'—':<10}"
            f"—"
        ),
        "",
        "OVERALL VERDICT:",
    ]
    if pe_verdict == "H1":
        lines.append(
            "  H1 kabul (p<0.05): META_ON PE anlamlı düşürüyor → SUPPORTED"
        )
    else:
        lines.append(
            "  H0 reddedilemedi (p≥0.05): → UNSUPPORTED (null finding)"
        )
    lines.append(f"  LLM calls total : {_LLM_CALL_COUNT}")
    lines.append(
        f"  System2 cycles  : META_ON={_SYSTEM2_CYCLES_ON} / "
        f"META_OFF={_SYSTEM2_CYCLES_OFF}"
    )
    lines.append(f"  Pairs completed : {len(pairs)}/{N_PAIRS}")
    lines.append(f"  Rate-limit falls: {_RATE_LIMIT_FALLBACKS}")
    return "\n".join(lines)


def _results_path() -> Path:
    """Project-root dau_runs/protocol_c_results.json."""

    root = Path(__file__).resolve().parents[2]
    out_dir = root / RESULTS_DIR_NAME
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir / RESULTS_FILE_NAME


def write_results_json(
    pairs: list[PairResult],
    *,
    pe_t: float,
    pe_p: float,
    pe_verdict: str,
    overall: str,
) -> Path:
    """Persist raw pairs + summary for audit."""

    path = _results_path()
    mean_delta_pe = _mean([p.mean_delta_pe for p in pairs])
    payload = {
        "protocol": "C",
        "n_pairs": len(pairs),
        "events_per_run": EVENTS_PER_RUN,
        "temperature": LLM_TEMPERATURE,
        "seeds": SEEDS[: len(pairs)],
        "ab_energy_floor": AB_ENERGY_FLOOR,
        "alpha": ALPHA,
        "pairs": [asdict(p) for p in pairs],
        "summary": {
            "mean_delta_pe": mean_delta_pe,
            "pe_t_statistic": pe_t,
            "pe_p_value": pe_p,
            "pe_verdict": pe_verdict,
            "overall": overall,
            "llm_calls_total": _LLM_CALL_COUNT,
            "system2_cycles_on": _SYSTEM2_CYCLES_ON,
            "system2_cycles_off": _SYSTEM2_CYCLES_OFF,
            "rate_limit_fallbacks": _RATE_LIMIT_FALLBACKS,
            "pairs_completed": len(pairs),
        },
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def run_protocol_c() -> list[PairResult]:
    """Execute all seed-locked pairs and print progress every 5."""

    assert len(SEEDS) == N_PAIRS, "SEEDS length must equal N_PAIRS"
    graph_mod.load_env_file()
    os.environ[LLM_TEMPERATURE_ENV] = str(LLM_TEMPERATURE)

    pairs: list[PairResult] = []
    for idx, seed in enumerate(SEEDS, start=1):
        pair = run_pair(seed, idx)
        pairs.append(pair)

        if idx % PROGRESS_EVERY_N_PAIRS == 0 or idx == N_PAIRS:
            mean_dpe = _mean([p.mean_delta_pe for p in pairs])
            mean_tdiff = _mean([p.trauma_diff for p in pairs])
            print(
                f"[PROGRESS] pair={idx}/{N_PAIRS} | "
                f"mean_delta_pe={mean_dpe:+.3f} | "
                f"trauma_diff={mean_tdiff:+.1f}",
                flush=True,
            )

        if idx < N_PAIRS:
            time.sleep(INTER_PAIR_SLEEP_S)

    return pairs


def main() -> None:
    """CLI: run Protocol C, print table, write JSON."""

    print(
        f"=== Protocol C start: {N_PAIRS} pairs × {EVENTS_PER_RUN} events, "
        f"T={LLM_TEMPERATURE}, seeds={SEED_START}–{SEED_END_INCLUSIVE} ===",
        flush=True,
    )
    pairs = run_protocol_c()

    deltas = [p.mean_delta_pe for p in pairs]
    pe_t, pe_p, pe_verdict = _one_tailed_paired_t_vs_zero(deltas)

    trauma_deltas = [p.trauma_diff for p in pairs]
    _, trauma_p, _ = _one_tailed_paired_t_vs_zero(trauma_deltas)

    overall = "SUPPORTED" if pe_verdict == "H1" else "UNSUPPORTED"
    report = format_results_table(
        pairs,
        pe_p=pe_p,
        pe_verdict=pe_verdict,
        trauma_p=trauma_p,
    )
    print()
    print(report)

    path = write_results_json(
        pairs,
        pe_t=pe_t,
        pe_p=pe_p,
        pe_verdict=pe_verdict,
        overall=overall,
    )
    print(f"\nWrote {path}", flush=True)


if __name__ == "__main__":
    main()
