"""Protocol C′ — mini pilot with shared lived-trace LoRA adapter.

Attribution-safe rules:
1. Shared adapter for META_ON and META_OFF under the same seed.
2. Train-then-A/B: pretrain once, freeze adapter, then run arms.
3. Controls: null LoRA (untrained) + shuffle-PE LoRA (permuted scalars).
4. Seed-lock + T=0.2; wall-clock measured (do not trust prior ~8 min estimates).

When CUDA / VRAM GO is unavailable, the harness still validates protocol
ordering and writes a DEFERRED report — LoRA stays flag-off until GO.

LoRA is a leading testable path, not a guaranteed metacognition fix.
No trait injection. No LLM-as-judge. No Groq Protocol C re-run.
"""

from __future__ import annotations

import json
import os
import random
import statistics
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

from dau.diagnostics.run_protocol_c import (
    CLASS_TRAUMA,
    EMPTY_COUNT,
    EMPTY_MEAN,
    LLM_TEMPERATURE_ENV,
    PairResult,
    _lock_seeds,
    _mean,
    run_protocol_c_arm,
)
from dau.foundation.constraints import build_default_constraints
from dau.foundation.local_llm import (
    STATUS_CUDA_UNAVAILABLE,
    clear_active_adapter,
    load_adapter,
    lora_plasticity_allowed,
)
from dau.foundation.llm_backend import (
    BACKEND_LOCAL,
    LLM_BACKEND_ENV,
)
from dau.foundation.lora_update import (
    LORA_ENABLED_ENV,
    SIGNAL_V1_ID,
    SIGNAL_V2_ID,
    LivedTraceExample,
    PreferencePair,
    build_lived_trace_examples,
    build_pe_ranked_pairs,
    compute_loss_weight,
    shuffle_preference_pairs,
    write_lived_traces,
    write_preference_pairs,
)
from dau.foundation.state import DAUAgentState, InternalState
from dau.foundation.time_model import EventClock, append_event, build_event

# ---------------------------------------------------------------------------
# Protocol C′ constants (mini pilot — no magic numbers in logic)
# ---------------------------------------------------------------------------

N_PAIRS: int = 5
EVENTS_PER_RUN: int = 50
PRETRAIN_EVENTS: int = 20
LLM_TEMPERATURE: float = 0.2
SEED_START: int = 2001
SEEDS: list[int] = list(range(SEED_START, SEED_START + N_PAIRS))

# Optional runtime overrides (smoke / mini without editing constants).
CPRIME_N_PAIRS_ENV: str = "DAU_CPRIME_N_PAIRS"
CPRIME_EVENTS_ENV: str = "DAU_CPRIME_EVENTS"
CPRIME_SEEDS_ENV: str = "DAU_CPRIME_SEEDS"
CPRIME_SIGNAL_ENV: str = "DAU_CPRIME_SIGNAL"
SIGNAL_V1: str = "v1"
SIGNAL_V2: str = "v2"
SIGNAL_DEFAULT: str = SIGNAL_V1

ADAPTER_SHARED: str = "shared_lived"
ADAPTER_NULL: str = "null_control"
ADAPTER_SHUFFLE: str = "shuffle_pe_control"

RESULTS_DIR_NAME: str = "dau_runs"
RESULTS_FILE_NAME: str = "protocol_c_prime_results.json"
ADAPTER_ROOT: str = "dau_lora_adapters"

STATUS_DEFERRED: str = "DEFERRED_NO_GPU_GO"
STATUS_RAN: str = "RAN"
ALPHA: float = 0.05

AGENT_ID_PRETRAIN_PREFIX: str = "cprime-pretrain"
AGENT_ID_OFF_PREFIX: str = "cprime-off"
AGENT_ID_ON_PREFIX: str = "cprime-on"


@dataclass
class AdapterSpec:
    """Frozen adapter identity shared across A/B arms for one seed."""

    adapter_id: str
    kind: str
    path: str
    trained: bool
    example_count: int = 0


@dataclass
class ConditionResult:
    """A/B (or control) pair under one adapter condition."""

    condition: str
    adapter_id: str
    pair: PairResult
    wall_clock_s: float


@dataclass
class ProtocolCPrimeReport:
    """Mini-pilot aggregate report."""

    status: str
    n_pairs: int
    seeds: list[int]
    temperature: float
    conditions: list[dict[str, Any]] = field(default_factory=list)
    mean_delta_pe_lived: float = EMPTY_MEAN
    mean_delta_pe_null: float = EMPTY_MEAN
    mean_delta_pe_shuffle: float = EMPTY_MEAN
    wall_clock_total_s: float = 0.0
    detail: str = ""
    decision: str = ""
    signal: str = SIGNAL_V1_ID

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def resolve_cprime_signal() -> str:
    """Return ``v1`` or ``v2`` from DAU_CPRIME_SIGNAL (default v1)."""

    raw = os.environ.get(CPRIME_SIGNAL_ENV, SIGNAL_DEFAULT).strip().lower()
    if raw in (SIGNAL_V2, SIGNAL_V2_ID, "pref", "preference"):
        return SIGNAL_V2
    return SIGNAL_V1


def _adapter_path(seed: int, adapter_id: str) -> Path:
    return Path.cwd() / ADAPTER_ROOT / f"cprime_seed{seed}_{adapter_id}"


def _synthetic_pretrain_state(seed: int) -> DAUAgentState:
    """Offline lived-trace substrate when GPU / LLM arm is unavailable."""

    rng = random.Random(seed)
    state = DAUAgentState(
        agent_id=f"{AGENT_ID_PRETRAIN_PREFIX}-{seed}",
        environment=build_default_constraints(),
        internal_state=InternalState(),
    )
    clock = EventClock()
    pe_log: list[dict[str, Any]] = []
    for step in range(1, PRETRAIN_EVENTS + 1):
        event = build_event(
            clock,
            "agent_decision",
            {"decision": f"step-{step} extract resource"},
        )
        state = append_event(state, event)
        pe = rng.uniform(0.05, 0.9)
        magnitude = min(1.0, pe * 0.9 + 0.05)
        delta_class = CLASS_TRAUMA if magnitude >= 0.7 else "NORMAL"
        pe_log.append(
            {
                "event_counter": event.timestamp,
                "prediction_error": pe,
                "delta_magnitude": magnitude,
                "delta_class": delta_class,
            }
        )
        # Keep delta_log aligned for trauma scalar via magnitude proxy records.
        from dau.foundation.state import DeltaRecord

        snap = {
            "energy": 1.0,
            "resource_load": 0.0,
            "uncertainty_load": 0.0,
            "social_load": 0.0,
        }
        record = DeltaRecord(
            timestamp=event.timestamp,
            magnitude=magnitude,
            affected_domain="resource",
            snapshot_before=snap,
            snapshot_after=dict(snap),
        )
        state.delta_log = list(state.delta_log) + [record]
    state._cprime_pe_log = pe_log  # type: ignore[attr-defined]
    return state


def build_shared_adapter(
    seed: int,
    *,
    kind: str = ADAPTER_SHARED,
    examples: list[LivedTraceExample] | None = None,
    pairs: list[PreferencePair] | None = None,
    signal: str = SIGNAL_V1,
) -> AdapterSpec:
    """Materialize adapter directory (traces on disk; weights if GO+CUDA)."""

    path = _adapter_path(seed, kind)
    path.mkdir(parents=True, exist_ok=True)
    rows = list(examples) if examples is not None else []
    pref_rows = list(pairs) if pairs is not None else []
    use_v2 = signal == SIGNAL_V2 and (pref_rows or rows)

    if use_v2 and not pref_rows and rows:
        pref_rows = build_pe_ranked_pairs(rows)
    if use_v2 and kind == ADAPTER_SHUFFLE and pref_rows:
        pref_rows = shuffle_preference_pairs(pref_rows, seed=seed + 17)
    if kind == ADAPTER_NULL:
        rows = []
        pref_rows = []

    if not use_v2:
        if kind == ADAPTER_SHUFFLE and rows:
            pe_values = [row.prediction_error for row in rows]
            random.Random(seed + 17).shuffle(pe_values)
            shuffled: list[LivedTraceExample] = []
            for row, pe in zip(rows, pe_values, strict=True):
                weight = compute_loss_weight(
                    prediction_error=pe,
                    trauma_flag=row.trauma_flag,
                    drift_sum=row.drift_sum,
                )
                shuffled.append(
                    LivedTraceExample(
                        event_counter=row.event_counter,
                        prediction_error=pe,
                        delta_magnitude=row.delta_magnitude,
                        delta_class=row.delta_class,
                        trauma_flag=row.trauma_flag,
                        drift_sum=row.drift_sum,
                        loss_weight=weight,
                        prompt=row.prompt.replace(
                            f"pe={row.prediction_error:.3f}",
                            f"pe={pe:.3f}",
                        ),
                        completion=row.completion,
                    )
                )
            rows = shuffled
        if kind == ADAPTER_NULL:
            rows = []
        if rows:
            write_lived_traces(rows, path)
        example_count = len(rows)
        signal_id = SIGNAL_V1_ID
    else:
        if pref_rows:
            write_preference_pairs(pref_rows, path)
        if rows and kind != ADAPTER_NULL:
            write_lived_traces(rows, path)
        example_count = len(pref_rows)
        signal_id = SIGNAL_V2_ID

    meta = {
        "seed": seed,
        "adapter_id": kind,
        "kind": kind,
        "example_count": example_count,
        "shared_for_ab": True,
        "train_then_ab": True,
        "signal": signal_id,
    }
    (path / "adapter_meta.json").write_text(
        json.dumps(meta, indent=2) + "\n",
        encoding="utf-8",
    )
    trained = False
    train_payload_ok = bool(pref_rows) if use_v2 else bool(rows)
    if kind in (ADAPTER_SHARED, ADAPTER_SHUFFLE) and train_payload_ok and lora_plasticity_allowed():
        try:
            from dau.foundation.local_llm import (
                attach_lora_adapter,
                cuda_is_available,
                load_base_model_4bit,
                run_micro_train_preference_step,
                run_micro_train_step,
                save_adapter,
            )

            if cuda_is_available():
                load_base_model_4bit()
                attach_lora_adapter(adapter_name=kind)
                if use_v2 and pref_rows:
                    run_micro_train_preference_step(pairs=pref_rows)
                else:
                    run_micro_train_step(examples=rows)
                save_adapter(path, adapter_name=kind)
                trained = True
                from dau.foundation.local_llm import clear_active_adapter

                clear_active_adapter()
        except Exception:
            trained = False
            from dau.foundation.local_llm import clear_active_adapter

            clear_active_adapter()
    return AdapterSpec(
        adapter_id=kind,
        kind=kind,
        path=str(path),
        trained=trained,
        example_count=example_count,
    )


def _resolve_seed_list(seeds: list[int] | None) -> list[int]:
    """Seeds from arg, else DAU_CPRIME_SEEDS / DAU_CPRIME_N_PAIRS, else default."""

    if seeds is not None:
        return list(seeds)
    raw_seeds = os.environ.get(CPRIME_SEEDS_ENV, "").strip()
    if raw_seeds:
        return [int(part.strip()) for part in raw_seeds.split(",") if part.strip()]
    raw_n = os.environ.get(CPRIME_N_PAIRS_ENV, "").strip()
    if raw_n:
        n_pairs = max(1, int(raw_n))
        return list(range(SEED_START, SEED_START + n_pairs))
    return list(SEEDS)


def _resolve_events_per_run() -> int:
    raw = os.environ.get(CPRIME_EVENTS_ENV, "").strip()
    if raw:
        return max(1, int(raw))
    return EVENTS_PER_RUN


def _activate_adapter_for_condition(adapter: AdapterSpec) -> None:
    """Load shared/shuffle adapter weights, or clear for null control."""

    if adapter.kind == ADAPTER_NULL or not adapter.trained:
        clear_active_adapter()
        return
    load_adapter(Path(adapter.path), adapter_name=adapter.adapter_id)


def run_ab_with_shared_adapter(
    seed: int,
    adapter: AdapterSpec,
    *,
    pair_index: int,
    n_events: int = EVENTS_PER_RUN,
    dry_run: bool = False,
) -> ConditionResult:
    """Train-then-A/B: freeze adapter identity, run OFF then ON."""

    _lock_seeds(seed)
    os.environ[LLM_TEMPERATURE_ENV] = str(LLM_TEMPERATURE)
    started = time.perf_counter()

    if dry_run:
        # Deterministic synthetic ΔPE for harness validation (not empiric claim).
        rng = np.random.default_rng(seed + hash(adapter.adapter_id) % 10_000)
        noise = float(rng.normal(0.0, 0.01))
        bias = 0.0
        if adapter.kind == ADAPTER_SHARED:
            bias = -0.002  # tiny placeholder; not a significance claim
        elif adapter.kind == ADAPTER_SHUFFLE:
            bias = float(rng.normal(0.0, 0.02))
        pair = PairResult(
            seed=seed,
            mean_delta_pe=bias + noise,
            trauma_count_on=EMPTY_COUNT,
            trauma_count_off=EMPTY_COUNT,
            trauma_diff=EMPTY_MEAN,
            memory_score_mean_on=EMPTY_MEAN,
            memory_score_mean_off=EMPTY_MEAN,
            memory_score_diff=EMPTY_MEAN,
            gamma_mean_on=EMPTY_MEAN,
            gamma_mean_off=EMPTY_MEAN,
            gamma_diff=EMPTY_MEAN,
            n_events_on=n_events,
            n_events_off=n_events,
            system2_cycles_on=EMPTY_COUNT,
            system2_cycles_off=EMPTY_COUNT,
            pe_mean_on=EMPTY_MEAN,
            pe_mean_off=EMPTY_MEAN,
        )
        elapsed = time.perf_counter() - started
        return ConditionResult(
            condition=adapter.kind,
            adapter_id=adapter.adapter_id,
            pair=pair,
            wall_clock_s=elapsed,
        )

    # Live path: shared adapter identity; local backend; same weights ON/OFF.
    _activate_adapter_for_condition(adapter)
    print(
        f"[C′] pair={pair_index} seed={seed} "
        f"adapter={adapter.adapter_id} trained={adapter.trained} META_OFF …",
        flush=True,
    )
    off = run_protocol_c_arm(
        agent_id=f"{AGENT_ID_OFF_PREFIX}-{seed}-{adapter.adapter_id}",
        meta_enabled=False,
        seed=seed,
        n_events=n_events,
    )
    print(
        f"[C′] pair={pair_index} seed={seed} "
        f"adapter={adapter.adapter_id} META_ON …",
        flush=True,
    )
    on = run_protocol_c_arm(
        agent_id=f"{AGENT_ID_ON_PREFIX}-{seed}-{adapter.adapter_id}",
        meta_enabled=True,
        seed=seed,
        n_events=n_events,
    )
    n_aligned = min(len(on.events), len(off.events))
    if n_aligned == EMPTY_COUNT:
        mean_delta_pe = EMPTY_MEAN
    else:
        mean_delta_pe = _mean(
            [on.events[t].pe - off.events[t].pe for t in range(n_aligned)]
        )
    pair = PairResult(
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
    elapsed = time.perf_counter() - started
    return ConditionResult(
        condition=adapter.kind,
        adapter_id=adapter.adapter_id,
        pair=pair,
        wall_clock_s=elapsed,
    )



def run_protocol_c_prime(
    *,
    seeds: list[int] | None = None,
    dry_run: bool | None = None,
    n_events: int | None = None,
    signal: str | None = None,
) -> ProtocolCPrimeReport:
    """Mini Protocol C′: pretrain shared adapter → A/B + null + shuffle."""

    seed_list = _resolve_seed_list(seeds)
    events = int(n_events) if n_events is not None else _resolve_events_per_run()
    signal_mode = signal if signal is not None else resolve_cprime_signal()
    signal_id = SIGNAL_V2_ID if signal_mode == SIGNAL_V2 else SIGNAL_V1_ID
    use_dry = dry_run if dry_run is not None else (not lora_plasticity_allowed())
    t0 = time.perf_counter()
    conditions: list[ConditionResult] = []

    prior_lora = os.environ.get(LORA_ENABLED_ENV)
    prior_backend = os.environ.get(LLM_BACKEND_ENV)
    if use_dry:
        os.environ[LORA_ENABLED_ENV] = "0"
    elif lora_plasticity_allowed():
        os.environ[LORA_ENABLED_ENV] = "1"
        # Live C′ is local-only — no Groq token / TPD cost.
        os.environ[LLM_BACKEND_ENV] = BACKEND_LOCAL

    try:
        for index, seed in enumerate(seed_list, start=1):
            pretrain_state = _synthetic_pretrain_state(seed)
            pe_log = getattr(pretrain_state, "_cprime_pe_log", [])
            examples = build_lived_trace_examples(pretrain_state, pe_log)
            pref_pairs: list[PreferencePair] | None = None
            if signal_mode == SIGNAL_V2:
                pref_pairs = build_pe_ranked_pairs(examples)

            shared = build_shared_adapter(
                seed,
                kind=ADAPTER_SHARED,
                examples=examples,
                pairs=pref_pairs,
                signal=signal_mode,
            )
            null = build_shared_adapter(
                seed,
                kind=ADAPTER_NULL,
                examples=[],
                pairs=[],
                signal=signal_mode,
            )
            shuffle = build_shared_adapter(
                seed,
                kind=ADAPTER_SHUFFLE,
                examples=examples,
                pairs=pref_pairs,
                signal=signal_mode,
            )

            assert shared.adapter_id == ADAPTER_SHARED

            for adapter in (shared, null, shuffle):
                result = run_ab_with_shared_adapter(
                    seed,
                    adapter,
                    pair_index=index,
                    n_events=events,
                    dry_run=use_dry,
                )
                assert result.adapter_id == adapter.adapter_id
                conditions.append(result)
    finally:
        if prior_lora is None:
            os.environ.pop(LORA_ENABLED_ENV, None)
        else:
            os.environ[LORA_ENABLED_ENV] = prior_lora
        if prior_backend is None:
            os.environ.pop(LLM_BACKEND_ENV, None)
        else:
            os.environ[LLM_BACKEND_ENV] = prior_backend
        clear_active_adapter()

    def _mean_for(kind: str) -> float:
        values = [c.pair.mean_delta_pe for c in conditions if c.condition == kind]
        return _mean(values)

    lived = _mean_for(ADAPTER_SHARED)
    null_pe = _mean_for(ADAPTER_NULL)
    shuffle_pe = _mean_for(ADAPTER_SHUFFLE)
    total_s = time.perf_counter() - t0

    if use_dry:
        status = STATUS_DEFERRED
        detail = (
            "Harness validated (shared adapter + train-then-A/B + controls). "
            f"VRAM/CUDA GO absent ({STATUS_CUDA_UNAVAILABLE} or no GO report). "
            "Keep DAU_LORA_ENABLED=0 until GPU spike returns GO, then re-run live. "
            f"signal={signal_id}"
        )
        decision = (
            "DEFER empiric claim — infrastructure ready; no ΔPE significance claim."
        )
    else:
        status = STATUS_RAN
        detail = (
            f"signal={signal_id}; Lived mean ΔPE={lived:.4f}; null={null_pe:.4f}; "
            f"shuffle={shuffle_pe:.4f}; wall_clock_s={total_s:.1f}"
        )
        # Smoke (N=1): separation only — no significance claim.
        if len(seed_list) <= 1:
            if lived < null_pe and lived < shuffle_pe:
                decision = (
                    "SMOKE_SEPARATION — lived below controls; discuss N expand. "
                    "No significance claim. Keep DAU_LORA_ENABLED=0."
                )
            else:
                decision = (
                    "SMOKE_NO_SEPARATION — no N=15; keep WEAK appendix; "
                    "DAU_LORA_ENABLED=0; spine unchanged."
                )
        elif lived < null_pe and lived < shuffle_pe and lived < -1e-3:
            decision = "CAUTIOUS_EXPAND — lived ΔPE better than controls (recheck n)."
        else:
            decision = (
                "WEAK_LORA_HYPOTHESIS — flag off; strengthen frozen null; "
                "leave Layer 0–5 spine unchanged."
            )

    report = ProtocolCPrimeReport(
        status=status,
        n_pairs=len(seed_list),
        seeds=seed_list,
        temperature=LLM_TEMPERATURE,
        conditions=[asdict(c) for c in conditions],
        mean_delta_pe_lived=lived,
        mean_delta_pe_null=null_pe,
        mean_delta_pe_shuffle=shuffle_pe,
        wall_clock_total_s=total_s,
        detail=detail,
        decision=decision,
        signal=signal_id,
    )
    return report


def write_report(report: ProtocolCPrimeReport, path: Path | None = None) -> Path:
    out = path or (Path.cwd() / RESULTS_DIR_NAME / RESULTS_FILE_NAME)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report.to_dict(), indent=2) + "\n", encoding="utf-8")
    return out


def main() -> int:
    report = run_protocol_c_prime()
    path = write_report(report)
    print(f"status={report.status}")
    print(f"decision={report.decision}")
    print(f"wall_clock_total_s={report.wall_clock_total_s:.2f}")
    print(f"mean_delta_pe_lived={report.mean_delta_pe_lived:.4f}")
    print(f"wrote={path}")
    # Exit 0 even when deferred — harness success; empiric GO is separate.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
