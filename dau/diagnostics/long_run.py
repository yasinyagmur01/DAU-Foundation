"""Long-horizon stress run — TRAUMA / drift / actuators under real load.

Uses foundation run_demo wiring (build_graph stream + MemoryStore) with
monkey-patched horizon, energy floor, scarce pool, and rising social pressure.
Actuator audit wrappers are installed without modifying production modules.
"""

from __future__ import annotations

import os
from typing import Any

import dau.foundation.graph as graph_mod
import dau.society.environment as env_mod
from dau.diagnostics.actuator_audit import (
    ACTUATOR_NAMES,
    _AUDIT,
    install_actuator_patches,
    print_audit_report,
)
from dau.foundation.constraints import (
    CROSS_AXIS_SPILLOVER,
    build_default_constraints,
    update_constraints,
)
from dau.foundation.delta import (
    DELTA_THRESHOLD_DEEP,
    DELTA_THRESHOLD_NOISE,
    DELTA_THRESHOLD_NORMAL,
)
from dau.foundation.drift import DriftState
from dau.foundation.graph import (
    build_graph,
    get_pe_event_log,
    reset_pe_event_log,
)
from dau.foundation.lod import CognitiveMode, LODState
from dau.foundation.memory_bridge import initialize_memory
from dau.foundation.meta_observer import bind_memory_store, unbind_memory_store
from dau.foundation.social import (
    OUTCOME_COOPERATE,
    OUTCOME_DEADLOCK,
    OUTCOME_DEFECT,
    InteractionRecord,
    SocialState,
    record_interaction,
)
from dau.foundation.state import (
    METRIC_MAX,
    METRIC_MIN,
    DAUAgentState,
    InternalState,
)
from dau.society.environment import EnvironmentState, get_pool_ratio
from langchain_groq import ChatGroq

# ---------------------------------------------------------------------------
# Long-run protocol parameters (no magic numbers in logic)
# ---------------------------------------------------------------------------

MAX_EVENTS: int = 100
AB_ENERGY_FLOOR: float = 0.10
POOL_MAX: float = 100.0
POOL_REGEN_RATE: float = 0.15
INITIAL_POOL: float = 60.0

SOCIAL_PRESSURE_STEP: float = 0.01
# social_pre → agent → evaluator → meta_observer → pool_step
STREAM_NODES_PER_EVENT: int = 5
STREAM_RECURSION_HEADROOM: int = 10
STREAM_RECURSION_LIMIT: int = (
    MAX_EVENTS * STREAM_NODES_PER_EVENT + STREAM_RECURSION_HEADROOM
)

LONG_RUN_AGENT_ID: str = "long-run-0"
LONG_RUN_OPPONENT_ID: str = "long-run-opponent-0"
LLM_REQUEST_TIMEOUT_S: float = 30.0
MAX_LLM_ATTEMPTS: int = 8

# Hostile dyad seed: defects crush trust; mixed outcomes + terminal deadlock
# raise coordination friction so event-1 social_load can push mag into TRAUMA.
HOSTILE_SEED_DEFECTS: int = 10
HOSTILE_SEED_MIX: tuple[str, ...] = (
    OUTCOME_COOPERATE,
    OUTCOME_DEFECT,
    OUTCOME_DEADLOCK,
    OUTCOME_DEFECT,
    OUTCOME_COOPERATE,
    OUTCOME_DEADLOCK,
)
HOSTILE_SEED_COUNTER_START: int = 0

CLASS_TRAUMA: str = "TRAUMA"
CLASS_DEEP: str = "DEEP"
CLASS_NORMAL: str = "NORMAL"
CLASS_NOISE: str = "NOISE"

EMPTY_COUNT: int = 0
PE_MISSING: float = -1.0
LLM_CALL_START: int = 0

# ---------------------------------------------------------------------------
# Mutable audit / LLM counters for this process
# ---------------------------------------------------------------------------

_LLM_CALL_COUNT: int = LLM_CALL_START
_RATE_LIMIT_FALLBACKS: int = EMPTY_COUNT


def _reset_actuator_audit() -> None:
    """Zero actuator_audit counters before a fresh long run."""

    for name in ACTUATOR_NAMES:
        _AUDIT[name] = {"called": 0, "triggered": 0}


def _build_hostile_social(
    agent_id: str,
    opponent_id: str,
) -> SocialState:
    """Seed lived betrayal + deadlock so social_load and friction are real."""

    social = SocialState()
    counter = HOSTILE_SEED_COUNTER_START
    for _ in range(HOSTILE_SEED_DEFECTS):
        counter += 1
        social = record_interaction(
            social,
            InteractionRecord(
                agent_id=opponent_id,
                opponent_id=agent_id,
                outcome=OUTCOME_DEFECT,
                event_counter=counter,
            ),
        )
        social = record_interaction(
            social,
            InteractionRecord(
                agent_id=agent_id,
                opponent_id=opponent_id,
                outcome=OUTCOME_DEFECT,
                event_counter=counter,
            ),
        )
    for outcome in HOSTILE_SEED_MIX:
        counter += 1
        social = record_interaction(
            social,
            InteractionRecord(
                agent_id=opponent_id,
                opponent_id=agent_id,
                outcome=outcome,
                event_counter=counter,
            ),
        )
        social = record_interaction(
            social,
            InteractionRecord(
                agent_id=agent_id,
                opponent_id=opponent_id,
                outcome=outcome,
                event_counter=counter,
            ),
        )
    return social


def _install_protocol_patches() -> None:
    """Pin horizon, floor, and GovSim pool on live modules."""

    graph_mod.MAX_EVENTS = MAX_EVENTS
    graph_mod.AB_ENERGY_FLOOR = AB_ENERGY_FLOOR
    env_mod.POOL_MAX = POOL_MAX
    env_mod.POOL_REGEN_RATE = POOL_REGEN_RATE


def _wrap_build_llm(original: Any) -> Any:
    """Rebuild ChatGroq with an explicit same-thread request timeout."""

    def wrapper() -> Any:
        _ = original  # keep signature parity; we reconstruct with timeout
        graph_mod.load_env_file()
        api_key = os.environ.get(graph_mod.GROQ_API_KEY_ENV, "").strip()
        if not api_key:
            return original()
        temperature = graph_mod._resolve_llm_temperature()
        seed = graph_mod._resolve_llm_seed()
        model_kwargs: dict[str, Any] = {}
        if seed is not None:
            model_kwargs["seed"] = seed
        try:
            return ChatGroq(
                model=graph_mod.MODEL_NAME,
                temperature=temperature,
                max_tokens=graph_mod.MAX_TOKENS,
                api_key=api_key,
                model_kwargs=model_kwargs,
                timeout=LLM_REQUEST_TIMEOUT_S,
            )
        except TypeError:
            return original()

    return wrapper


def _is_llm_abort_error(exc: BaseException) -> bool:
    """True for rate-limit or timeout-style LLM failures."""

    if graph_mod._is_quota_error(exc):
        return True
    text = str(exc).lower()
    markers = ("timeout", "timed out", "deadline", "read timed out", "connect")
    return any(marker in text for marker in markers)


def _magnitude_class(magnitude: float) -> str:
    """Map delta magnitude onto long-run summary buckets."""

    if magnitude >= DELTA_THRESHOLD_DEEP:
        return CLASS_TRAUMA
    if magnitude >= DELTA_THRESHOLD_NORMAL:
        return CLASS_DEEP
    if magnitude >= DELTA_THRESHOLD_NOISE:
        return CLASS_NORMAL
    return CLASS_NOISE


def _as_drift(state: DAUAgentState | Any) -> DriftState:
    """Coerce state.drift_state to DriftState."""

    drift = getattr(state, "drift_state", None)
    return drift if isinstance(drift, DriftState) else DriftState()


def _open_drift_magnitudes(drift: DriftState) -> dict[str, float]:
    """Return {domain: magnitude} for domains with an open drift flag."""

    open_flags: dict[str, float] = {}
    for domain, flagged in drift.flags.items():
        if flagged:
            open_flags[str(domain)] = float(drift.magnitudes.get(domain, METRIC_MIN))
    return open_flags


def _format_mu(setpoints: dict[str, float]) -> dict[str, float]:
    """Round allostatic setpoints for stable console output."""

    return {key: round(float(value), 3) for key, value in setpoints.items()}


def _log_event_row(
    *,
    event_n: int,
    pe: float,
    magnitude: float,
    delta_class: str,
    internal: InternalState,
    drift: DriftState,
) -> None:
    """Print the per-event vitals line required by the long-run protocol."""

    gamma = float(internal.compute_endogenous_recovery_rate(drift))
    mu = _format_mu(internal.get_allostatic_setpoints(drift))
    flags = {str(k): bool(v) for k, v in drift.flags.items()}
    print(
        f"[EVENT] e={event_n}  pe={pe:.3f}  mag={magnitude:.3f}  class={delta_class}",
        flush=True,
    )
    print(
        f"        energy={float(internal.energy):.2f}  "
        f"res={float(internal.resource_load):.2f}  "
        f"soc={float(internal.social_load):.2f}  "
        f"unc={float(internal.uncertainty_load):.2f}",
        flush=True,
    )
    print(
        f"        drift_flags={flags}  gamma={gamma:.3f}  mu={mu}",
        flush=True,
    )


def _run_system1(original: Any, state: DAUAgentState) -> dict[str, Any]:
    """Force the NPC path for one decision regardless of LOD."""

    prior = graph_mod.should_run_llm
    graph_mod.should_run_llm = lambda _lod: False
    try:
        return original(state)
    finally:
        graph_mod.should_run_llm = prior


def _wrap_agent_node(original: Any) -> Any:
    """Count System-2 LLM attempts; on rate-limit/timeout, fall back to System 1."""

    def wrapper(state: DAUAgentState) -> dict[str, Any]:
        global _LLM_CALL_COUNT, _RATE_LIMIT_FALLBACKS

        lod = state.lod_state
        if not isinstance(lod, LODState):
            lod = LODState()

        if not graph_mod.should_run_llm(lod):
            return original(state)

        if _LLM_CALL_COUNT >= MAX_LLM_ATTEMPTS:
            print(
                f"[LLM] budget exhausted ({MAX_LLM_ATTEMPTS}) → System1",
                flush=True,
            )
            return _run_system1(original, state)

        _LLM_CALL_COUNT += 1
        print(
            f"[LLM] call=#{_LLM_CALL_COUNT} "
            f"event={len(state.event_log)} "
            f"mode={CognitiveMode.SYSTEM_2.value}",
            flush=True,
        )

        try:
            return original(state)
        except Exception as exc:  # noqa: BLE001 — free-tier must not abort life
            if _is_llm_abort_error(exc):
                _RATE_LIMIT_FALLBACKS += 1
                print(
                    f"[LLM] abort → System1 fallback "
                    f"(fallbacks={_RATE_LIMIT_FALLBACKS}): {exc}",
                    flush=True,
                )
                return _run_system1(original, state)
            raise

    return wrapper


def _wrap_meta_observer_node(original: Any) -> Any:
    """After Meta-Observer: raise social hostility and log PE vitals.

    Pool advance + crisis trauma are production graph duties (pool_step_node).
    This harness must not call step_pool here — that would double-step the commons.
    """

    def wrapper(state: DAUAgentState) -> dict[str, Any]:
        patch = dict(original(state))

        # Ongoing social hostility: opponent keeps defecting / deadlocking.
        social = state.social_state
        if not isinstance(social, SocialState):
            social = SocialState()
        event_n = len(state.event_log)
        opponent_outcome = (
            OUTCOME_DEADLOCK if event_n % 2 == 0 else OUTCOME_DEFECT
        )
        social = record_interaction(
            social,
            InteractionRecord(
                agent_id=LONG_RUN_OPPONENT_ID,
                opponent_id=state.agent_id,
                outcome=opponent_outcome,
                event_counter=event_n,
            ),
        )
        patch["social_state"] = social

        # Post-meta vitals: PE row from evaluator + drift after actuators.
        pe_events = get_pe_event_log()
        if pe_events:
            row = pe_events[-1]
            drift = patch.get("drift_state", state.drift_state)
            if not isinstance(drift, DriftState):
                drift = _as_drift(state)
            internal = state.internal_state
            if "internal_state" in patch and isinstance(
                patch["internal_state"], InternalState
            ):
                internal = patch["internal_state"]
            _log_event_row(
                event_n=int(row["event_counter"]),
                pe=float(row["prediction_error"]),
                magnitude=float(row["delta_magnitude"]),
                delta_class=str(row["delta_class"]),
                internal=internal,
                drift=drift,
            )
        return patch

    return wrapper


def _wrap_pool_step_node(original: Any) -> Any:
    """After production pool_step: sync scarcity / social_pressure from new pool."""

    def wrapper(state: DAUAgentState) -> dict[str, Any]:
        patch = dict(original(state))

        env = patch.get("env_state", state.env_state)
        if not isinstance(env, EnvironmentState):
            env = EnvironmentState(pool=INITIAL_POOL)

        constraints = state.environment
        if "environment" in patch and patch["environment"] is not None:
            constraints = patch["environment"]
        pool_ratio = get_pool_ratio(env)
        scarcity = max(METRIC_MIN, min(METRIC_MAX, 1.0 - pool_ratio))
        social_pressure = max(
            METRIC_MIN,
            min(METRIC_MAX, float(constraints.social_pressure) + SOCIAL_PRESSURE_STEP),
        )
        patch["environment"] = update_constraints(
            constraints,
            resource_scarcity=scarcity,
            social_pressure=social_pressure,
        )
        return patch

    return wrapper


def _state_from_stream(values: Any) -> DAUAgentState:
    """Normalize stream values into DAUAgentState."""

    if isinstance(values, DAUAgentState):
        return values
    if isinstance(values, dict):
        return DAUAgentState.model_validate(values)
    raise TypeError(f"Unexpected stream value type: {type(values)!r}")


def _print_summary(
    *,
    pe_events: list[dict[str, Any]],
    final_state: DAUAgentState,
    ended_early: bool,
) -> None:
    """Print long-run class counts, drift, peaks, and LLM usage."""

    counts = {
        CLASS_TRAUMA: EMPTY_COUNT,
        CLASS_DEEP: EMPTY_COUNT,
        CLASS_NORMAL: EMPTY_COUNT,
        CLASS_NOISE: EMPTY_COUNT,
    }
    peak_pe = PE_MISSING
    peak_pe_event = EMPTY_COUNT
    peak_mag = PE_MISSING
    peak_mag_event = EMPTY_COUNT

    for row in pe_events:
        mag = float(row["delta_magnitude"])
        pe = float(row["prediction_error"])
        event_n = int(row["event_counter"])
        label = _magnitude_class(mag)
        counts[label] += 1
        if pe >= peak_pe:
            peak_pe = pe
            peak_pe_event = event_n
        if mag >= peak_mag:
            peak_mag = mag
            peak_mag_event = event_n

    drift = _as_drift(final_state)
    internal = final_state.internal_state
    gamma = float(internal.compute_endogenous_recovery_rate(drift))
    mu = _format_mu(internal.get_allostatic_setpoints(drift))
    open_flags = _open_drift_magnitudes(drift)
    total = len(pe_events)

    print()
    print("=== LONG RUN SUMMARY ===")
    print(f"Total events     : {total}")
    print(f"TRAUMA events    : {counts[CLASS_TRAUMA]}  (mag ≥ {DELTA_THRESHOLD_DEEP})")
    print(
        f"DEEP events      : {counts[CLASS_DEEP]}  "
        f"({DELTA_THRESHOLD_NORMAL} ≤ mag < {DELTA_THRESHOLD_DEEP})"
    )
    print(
        f"NORMAL events    : {counts[CLASS_NORMAL]}  "
        f"({DELTA_THRESHOLD_NOISE} ≤ mag < {DELTA_THRESHOLD_NORMAL})"
    )
    print(f"NOISE events     : {counts[CLASS_NOISE]}  (mag < {DELTA_THRESHOLD_NOISE})")
    print(f"Drift flags open : {open_flags}")
    print(f"Final energy     : {float(internal.energy):.2f}")
    print(f"Final gamma      : {gamma:.3f}")
    print(f"Final mu         : {mu}")
    if peak_pe < METRIC_MIN:
        print("Peak PE          : n/a")
        print("Peak magnitude   : n/a")
    else:
        print(f"Peak PE          : {peak_pe:.3f} (event {peak_pe_event})")
        print(f"Peak magnitude   : {peak_mag:.3f} (event {peak_mag_event})")
    print(f"LLM calls        : {_LLM_CALL_COUNT}")
    print(f"LLM rate fallbacks: {_RATE_LIMIT_FALLBACKS}")
    if ended_early:
        print(
            f"Early stop       : yes "
            f"(events={total} < MAX_EVENTS={MAX_EVENTS}; "
            f"energy={float(internal.energy):.2f})"
        )
    else:
        print(f"Early stop       : no (completed {total} events)")

    if counts[CLASS_TRAUMA] == EMPTY_COUNT:
        print(
            "TRAUMA report    : NONE — no event reached mag ≥ "
            f"{DELTA_THRESHOLD_DEEP}"
        )
    else:
        print(f"TRAUMA report    : {counts[CLASS_TRAUMA]} trauma-class event(s) observed")


def run_long() -> int:
    """Execute the 100-event stress protocol and print summary + actuator table."""

    global _LLM_CALL_COUNT, _RATE_LIMIT_FALLBACKS

    _LLM_CALL_COUNT = LLM_CALL_START
    _RATE_LIMIT_FALLBACKS = EMPTY_COUNT
    _reset_actuator_audit()

    original_agent = graph_mod.agent_node
    original_meta = graph_mod.meta_observer_node
    original_pool_step = graph_mod.pool_step_node
    original_build_llm = graph_mod._build_llm
    original_max_events = graph_mod.MAX_EVENTS
    original_energy_floor = graph_mod.AB_ENERGY_FLOOR
    original_pool_max = env_mod.POOL_MAX
    original_pool_regen = env_mod.POOL_REGEN_RATE

    _install_protocol_patches()
    install_actuator_patches()
    graph_mod.agent_node = _wrap_agent_node(original_agent)
    graph_mod.meta_observer_node = _wrap_meta_observer_node(original_meta)
    graph_mod.pool_step_node = _wrap_pool_step_node(original_pool_step)
    graph_mod._build_llm = _wrap_build_llm(original_build_llm)

    reset_pe_event_log()
    environment = build_default_constraints()
    # Birth scarcity mirrors INITIAL_POOL / POOL_MAX.
    environment = update_constraints(
        environment,
        resource_scarcity=max(
            METRIC_MIN,
            min(METRIC_MAX, 1.0 - (INITIAL_POOL / POOL_MAX)),
        ),
    )
    initial = DAUAgentState(
        agent_id=LONG_RUN_AGENT_ID,
        opponent_id=LONG_RUN_OPPONENT_ID,
        environment=environment,
        env_state=EnvironmentState(pool=INITIAL_POOL),
        social_state=_build_hostile_social(
            LONG_RUN_AGENT_ID,
            LONG_RUN_OPPONENT_ID,
        ),
        lod_state=LODState(mode=CognitiveMode.SYSTEM_1),
        internal_state=InternalState(),
    )

    print("=== DAU LONG RUN ===")
    print(f"agent_id={LONG_RUN_AGENT_ID}")
    print(f"opponent_id={LONG_RUN_OPPONENT_ID}")
    print(
        f"MAX_EVENTS={MAX_EVENTS}  AB_ENERGY_FLOOR={AB_ENERGY_FLOOR}  "
        f"INITIAL_POOL={INITIAL_POOL}/{POOL_MAX}  "
        f"POOL_REGEN_RATE={POOL_REGEN_RATE}"
    )
    print(f"CROSS_AXIS_SPILLOVER={CROSS_AXIS_SPILLOVER}  (production)")
    print()

    store = initialize_memory(LONG_RUN_AGENT_ID)
    graph_mod._memory_stores[LONG_RUN_AGENT_ID] = store
    graph_mod._memory_written[LONG_RUN_AGENT_ID] = 0
    bind_memory_store(LONG_RUN_AGENT_ID, store)

    result: Any = initial
    stream_config = {"recursion_limit": STREAM_RECURSION_LIMIT}
    try:
        app = build_graph(checkpointer=None)
        for values in app.stream(
            initial,
            config=stream_config,
            stream_mode="values",
        ):
            result = values
    finally:
        unbind_memory_store(LONG_RUN_AGENT_ID)
        graph_mod._memory_stores.pop(LONG_RUN_AGENT_ID, None)
        graph_mod._memory_written.pop(LONG_RUN_AGENT_ID, None)
        graph_mod.agent_node = original_agent
        graph_mod.meta_observer_node = original_meta
        graph_mod.pool_step_node = original_pool_step
        graph_mod._build_llm = original_build_llm
        graph_mod.MAX_EVENTS = original_max_events
        graph_mod.AB_ENERGY_FLOOR = original_energy_floor
        env_mod.POOL_MAX = original_pool_max
        env_mod.POOL_REGEN_RATE = original_pool_regen
        try:
            store.close()
        except Exception:
            pass

    final_state = _state_from_stream(result)
    pe_events = get_pe_event_log()
    ended_early = len(pe_events) < MAX_EVENTS
    _print_summary(
        pe_events=pe_events,
        final_state=final_state,
        ended_early=ended_early,
    )
    print()
    print_audit_report()
    return 0


def main() -> int:
    """CLI entry: python -m dau.diagnostics.long_run"""

    return run_long()


if __name__ == "__main__":
    raise SystemExit(main())
