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

import dataclasses
import datetime
import json
import os
import random
import statistics
import tempfile
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
from scipy import stats

import dau.foundation.graph as graph_mod
from dau.foundation.constraints import (
    ADAPTER_BASE_DIR,
    NLI_CONTRADICTION_THRESHOLD,
    PER_AGENT_LORA_ALPHA,
    PER_AGENT_LORA_RANK,
    PRECISION_EPSILON,
    PRECISION_MAX_WEIGHT,
    PPR_ALPHA,
    PPR_WEIGHT_IN_SCORE,
    build_default_constraints,
)
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
# Protocol C′ constants (no magic numbers in logic)
# ---------------------------------------------------------------------------

N_PAIRS: int = int(os.environ.get("DAU_CPRIME_N_PAIRS", "15"))
EVENTS_PER_ARM: int = int(os.environ.get("DAU_CPRIME_EVENTS", "50"))
TEMPERATURE: float = float(os.environ.get("DAU_LLM_TEMPERATURE", "0.2"))
SEEDS: list[int] = list(range(2001, 2001 + N_PAIRS))
SIGNAL_VERSION: str = os.environ.get("DAU_CPRIME_SIGNAL", "v2")
RESULTS_PATH: Path = Path("dau_runs/protocol_c_prime_results.json")
CHECKPOINT_PATH: Path = Path("dau_runs/protocol_c_prime_checkpoint.json")
HEARTBEAT_PATH: Path = Path("dau_runs/protocol_c_prime_heartbeat.json")
# Must stay strictly above graph.TERMINATION_ENERGY, otherwise the floor never
# protects the run and a single max-PE trauma ends the life at event 1.
AB_ENERGY_FLOOR: float = 0.15
# Below this fraction of EVENTS_PER_ARM a padded PE trace is not measurable.
MIN_TRACE_FRACTION: float = 0.5

ALPHA: float = 0.05
EMPTY_COUNT: int = 0
EMPTY_MEAN: float = 0.0
EMPTY_STD: float = 0.0

LLM_TEMPERATURE_ENV: str = "DAU_LLM_TEMPERATURE"
LLM_SEED_ENV: str = "DAU_LLM_SEED"
LORA_ENABLED_ENV: str = "DAU_LORA_ENABLED"
NLI_FILTER_ENABLED_ENV: str = "DAU_NLI_FILTER_ENABLED"

STREAM_NODES_PER_EVENT: int = 4
STREAM_RECURSION_HEADROOM: int = 10

OPPONENT_ID: str = "cprime-npc-opponent"
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
}


@dataclass
class ArmResult:
    """One LIVED / NULL / SHUFFLE arm under a locked seed."""

    seed: int
    arm: str  # "lived" | "null" | "shuffle"
    pe_before: float  # mean PE over first EVENTS_PER_ARM events
    pe_after: float  # mean PE over second EVENTS_PER_ARM events
    delta_pe: float  # pe_after - pe_before
    n_events: int
    n_pairs_trained: int  # preference pairs that passed NLI filter
    n_pairs_rejected: int  # rejected by NLI filter
    wall_seconds: float


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


def _lock_seeds(seed: int) -> None:
    """Pin Python, NumPy, and Groq seed for counterfactual replay."""

    random.seed(seed)
    np.random.seed(seed)
    os.environ[LLM_SEED_ENV] = str(seed)
    os.environ[LLM_TEMPERATURE_ENV] = str(TEMPERATURE)


def _initial_state(agent_id: str) -> DAUAgentState:
    """Fresh agent with System 2 substrate (LLM path required)."""

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
    """Parse trailing seed from ``cprime-{arm}-{seed}``; fallback hash."""

    try:
        return int(str(agent_id).rsplit("-", 1)[-1])
    except ValueError:
        return abs(hash(agent_id)) % (2**31)


def _build_lived_examples(
    state: DAUAgentState,
    pe_rows: list[dict[str, Any]],
) -> list[Any]:
    """Build LivedTraceExample rows; graceful empty list if unavailable."""

    try:
        from dau.foundation.lora_update import (
            build_lived_trace_examples,
            maybe_lora_update_after_life,
        )
    except ImportError:
        return []

    examples = build_lived_trace_examples(state, pe_rows)
    # Optional hook — only replace when the hook actually returned examples.
    try:
        result = maybe_lora_update_after_life(state, pe_event_log=pe_rows)
        if getattr(result, "examples", None):
            examples = list(result.examples)
    except Exception:  # noqa: BLE001 — harness must not abort on hook failure
        pass
    return list(examples)


# ---------------------------------------------------------------------------
# Core: collect / train / arms
# ---------------------------------------------------------------------------


def _collect_pe_events(
    agent_id: str,
    seed: int,
    n_events: int,
    energy_floor: float = AB_ENERGY_FLOOR,
) -> tuple[list[float], list[Any]]:
    """Run agent for n_events; return (pe_list, lived_examples).

    Uses production ``build_graph`` with Protocol C monkeypatch pattern.
    Collects ``prediction_error`` from evaluator telemetry (pe event log).
    Pads remaining slots with last PE when energy floor ends the life early.
    """

    _ = seed  # seed locked by caller; kept for API clarity / future audits
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
        pe_rows = list(get_pe_event_log())
        pe_list = [float(row["prediction_error"]) for row in pe_rows]
        pe_list = _pad_pe_list(pe_list, n_events)
        lived_examples = _build_lived_examples(state, pe_rows)
        return pe_list, lived_examples
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


def _train_adapter(
    agent_id: str,
    lived_examples: list[Any],
    shuffled: bool = False,
) -> tuple[int, int]:
    """Build preference pairs, optional shuffle, micro-train per agent.

    NLI filter is active when ``dau.foundation.nli_filter`` is importable.
    Returns ``(n_pairs_trained, n_pairs_rejected)`` from NLI_FILTER_STATS.
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
            NLI_FILTER_STATS,
            build_pe_ranked_pairs,
            run_micro_train_preference_step,
            shuffle_preference_pairs,
        )
    except ImportError:
        return EMPTY_COUNT, EMPTY_COUNT

    os.environ.setdefault(NLI_FILTER_ENABLED_ENV, "1")

    before_passed = int(NLI_FILTER_STATS.get("passed", EMPTY_COUNT))
    before_rejected = int(NLI_FILTER_STATS.get("rejected", EMPTY_COUNT))

    try:
        pairs = build_pe_ranked_pairs(lived_examples)
    except Exception:  # noqa: BLE001 — graceful fallback if PE/NLI path fails
        return EMPTY_COUNT, EMPTY_COUNT

    n_pairs_trained = int(NLI_FILTER_STATS.get("passed", EMPTY_COUNT)) - before_passed
    n_pairs_rejected = (
        int(NLI_FILTER_STATS.get("rejected", EMPTY_COUNT)) - before_rejected
    )

    if shuffled and pairs:
        pairs = shuffle_preference_pairs(
            pairs,
            seed=_seed_from_agent_id(agent_id),
        )

    try:
        run_micro_train_preference_step(pairs, agent_id=agent_id)
    except Exception:  # noqa: BLE001 — train failure must not abort protocol
        pass

    return max(EMPTY_COUNT, n_pairs_trained), max(EMPTY_COUNT, n_pairs_rejected)


def run_arm(
    seed: int,
    arm: str,
    agent_id: str,
) -> ArmResult:
    """Full arm: lock → phase-1 → train/skip → phase-2 → ArmResult."""

    started = time.perf_counter()
    _lock_seeds(seed)

    pe_before_list, lived_examples = _collect_pe_events(
        agent_id=agent_id,
        seed=seed,
        n_events=EVENTS_PER_ARM,
        energy_floor=AB_ENERGY_FLOOR,
    )
    pe_before = _mean(pe_before_list)

    n_pairs_trained = EMPTY_COUNT
    n_pairs_rejected = EMPTY_COUNT
    if arm == ARM_LIVED:
        n_pairs_trained, n_pairs_rejected = _train_adapter(
            agent_id,
            lived_examples,
            shuffled=False,
        )
    elif arm == ARM_SHUFFLE:
        n_pairs_trained, n_pairs_rejected = _train_adapter(
            agent_id,
            lived_examples,
            shuffled=True,
        )
    # null: no training between phases

    _lock_seeds(seed)
    pe_after_list, _ = _collect_pe_events(
        agent_id=agent_id,
        seed=seed,
        n_events=EVENTS_PER_ARM,
        energy_floor=AB_ENERGY_FLOOR,
    )
    pe_after = _mean(pe_after_list)
    delta_pe = pe_after - pe_before
    wall_seconds = float(time.perf_counter() - started)

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
    os.environ[LLM_TEMPERATURE_ENV] = str(TEMPERATURE)

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


def _compute_stats(results: list[PairResult]) -> dict[str, Any]:
    """Summary means/stds + paired t-test (lived ΔPE vs null ΔPE)."""

    lived = [r.lived.delta_pe for r in results]
    null = [r.null.delta_pe for r in results]
    shuffle = [r.shuffle.delta_pe for r in results]

    mean_delta_pe_lived = _mean(lived)
    mean_delta_pe_null = _mean(null)
    mean_delta_pe_shuffle = _mean(shuffle)
    std_delta_pe_lived = _std(lived)
    std_delta_pe_null = _std(null)
    std_delta_pe_shuffle = _std(shuffle)

    if len(results) < 2:
        t_stat = EMPTY_MEAN
        p_value = 1.0
    else:
        t_result = stats.ttest_rel(lived, null)
        t_stat = float(t_result.statistic)
        p_value = float(t_result.pvalue)

    significant = bool(p_value < ALPHA)
    if significant and mean_delta_pe_lived < mean_delta_pe_null:
        verdict = VERDICT_H1_SUPPORTED
    elif significant:
        verdict = VERDICT_H1_REJECTED
    else:
        verdict = VERDICT_INCONCLUSIVE

    return {
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
    }


def write_results_json(results: list[PairResult], stats: dict[str, Any]) -> Path:
    """Persist Protocol C′ pairs + summary to RESULTS_PATH (indent=2)."""

    path = RESULTS_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "protocol": "C_PRIME",
        "signal_version": SIGNAL_VERSION,
        "n_pairs": N_PAIRS,
        "events_per_arm": EVENTS_PER_ARM,
        "temperature": TEMPERATURE,
        "seeds": list(SEEDS),
        "lora_enabled": os.environ.get(LORA_ENABLED_ENV, "0"),
        "nli_filter_enabled": os.environ.get(NLI_FILTER_ENABLED_ENV, "1"),
        "pairs": [asdict(r) for r in results],
        "summary": stats,
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote {path}", flush=True)
    return path


def main() -> None:
    """CLI: run Protocol C′, print summary, write JSON."""

    print(
        f"Protocol C′ — N={N_PAIRS} seeds, {EVENTS_PER_ARM} events/arm",
        flush=True,
    )
    print(
        f"Signal: {SIGNAL_VERSION} | LORA: {os.environ.get(LORA_ENABLED_ENV, '0')}",
        flush=True,
    )
    print(f"Monitor: watch -n 30 cat {HEARTBEAT_PATH}")
    print(f"Resume:  re-run same command — checkpoint auto-loads")
    print(f"Checkpoint: {CHECKPOINT_PATH}")
    results = run_protocol_c_prime()
    stats_out = _compute_stats(results)
    path = write_results_json(results, stats_out)

    print("\n=== RESULTS ===", flush=True)
    print(f"mean ΔPE lived:   {stats_out['mean_delta_pe_lived']:.4f}", flush=True)
    print(f"mean ΔPE null:    {stats_out['mean_delta_pe_null']:.4f}", flush=True)
    print(f"mean ΔPE shuffle: {stats_out['mean_delta_pe_shuffle']:.4f}", flush=True)
    print(
        f"t={stats_out['t_stat']:.3f}  p={stats_out['p_value']:.4f}",
        flush=True,
    )
    print(f"Verdict: {stats_out['verdict']}", flush=True)
    print(f"Results: {path}", flush=True)


if __name__ == "__main__":
    main()
