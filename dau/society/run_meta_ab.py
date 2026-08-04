"""Meta-Observer A/B harness — Layer 5 actuators on vs off, same scenario.

Runs fixed event-cycles: social_pre → agent → evaluator → (meta | telemetry-only).
Metrics are deterministic Python (delta magnitudes, m_ratio, energy, steps).
No trait injection. No LLM-as-judge. No new layer.

Default: System 1 NPC (free). Optional: force SYSTEM_2 for Groq A/B.
Labeled under current Jaccard sensor for PE-derived deltas.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from dau.foundation.constraints import build_default_constraints
from dau.foundation.lod import CognitiveMode, LODState
from dau.foundation.graph import (
    agent_node,
    evaluator_node,
    social_pre_node,
)
from dau.foundation.meta_observer import meta_observer_node
from dau.foundation.self_model import build_self_model
from dau.foundation.state import DAUAgentState, InternalState
from dau.society.environment import EnvironmentState
from dau.society.run_convention_pilot import SENSOR_LABEL

# ---------------------------------------------------------------------------
# A/B parameters (no magic numbers in logic)
# ---------------------------------------------------------------------------

AB_N_CYCLES: int = 20
AB_AGENT_ID_ON: str = "meta-ab-on-0"
AB_AGENT_ID_OFF: str = "meta-ab-off-0"
AB_MODE_ON: str = "meta_on"
AB_MODE_OFF: str = "meta_off"
TERMINATION_ENERGY: float = 0.05
# Fixed-horizon A/B: Jaccard PE can zero energy in one NPC step — keep a floor
# so meta on/off remains comparable across AB_N_CYCLES (documented protocol).
AB_ENERGY_FLOOR: float = 0.35
M_RATIO_MISSING: float = -1.0


@dataclass
class CycleTelemetry:
    """One cycle snapshot after evaluator (+ optional meta)."""

    cycle: int
    energy: float
    delta_magnitude: float
    m_ratio: float
    cognitive_mode: str


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


@dataclass
class ABComparison:
    """Paired on/off summary."""

    sensor_label: str
    on: ABRunResult
    off: ABRunResult
    delta_mean_diff: float
    m_ratio_mean_diff: float


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

    state = DAUAgentState(
        agent_id=agent_id,
        environment=build_default_constraints(),
        env_state=EnvironmentState(),
        lod_state=LODState(mode=CognitiveMode.SYSTEM_1),
        internal_state=InternalState(),
    )
    return state


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


def run_ab_arm(
    *,
    agent_id: str,
    meta_enabled: bool,
    n_cycles: int = AB_N_CYCLES,
    force_system_2: bool = False,
) -> ABRunResult:
    """Run one A/B arm for n_cycles or until energy exhaustion."""

    mode = AB_MODE_ON if meta_enabled else AB_MODE_OFF
    state = _initial_state(agent_id)
    if force_system_2:
        state = _ensure_system2(state)
    else:
        state = _ensure_system1(state)

    cycles: list[CycleTelemetry] = []
    ended_on_energy = False
    system2_cycles = 0

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
            # Telemetry-only: build SelfModel without actuators (fair m_ratio compare)
            state = state.model_copy(update={"self_model": build_self_model(state)})

        # Fixed-horizon protocol: restore energy floor so PE=1 under Jaccard
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
    mean_delta = sum(deltas) / float(len(deltas)) if deltas else 0.0
    mean_m = sum(ratios) / float(len(ratios)) if ratios else M_RATIO_MISSING

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


def main() -> None:
    """CLI: Meta A/B. Set DAU_META_AB_SYSTEM2=1 for Groq System-2 arms."""

    import os

    force_s2 = os.environ.get("DAU_META_AB_SYSTEM2", "").strip() in {
        "1",
        "true",
        "TRUE",
        "yes",
    }
    n_cycles_raw = os.environ.get("DAU_META_AB_CYCLES", "").strip()
    n_cycles = int(n_cycles_raw) if n_cycles_raw else AB_N_CYCLES
    label = "System 2 / Groq" if force_s2 else "NPC System 1"
    comp = run_meta_ab(n_cycles=n_cycles, force_system_2=force_s2)
    summary = comparison_summary(comp)
    print(f"=== DAU Meta-Observer A/B ({label}) ===")
    for key, value in summary.items():
        print(f"{key}={value}")


if __name__ == "__main__":
    main()
