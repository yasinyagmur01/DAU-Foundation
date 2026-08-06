"""Shared resource pool physics — GovSim-style CPR dynamics for Layer 4.

Biology analogy: a common pasture regenerates logistically toward carrying
capacity; extraction subtracts from the stock. Collapse is not a label —
it is a pool level that has fallen to a near-empty fraction of capacity.

Somatic enforcement (ADIM 1): when the commons falls below the crisis
threshold, agents absorb amplified resource trauma through update_drift.
That scar feeds F_agent-gated generation transfer (cautionary inheritance).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from dau.foundation.delta import DELTA_THRESHOLD_NORMAL
from dau.foundation.drift import DriftState, update_drift
from dau.foundation.state import METRIC_MAX, METRIC_MIN, DeltaRecord

# ---------------------------------------------------------------------------
# Resource pool parameters (no magic numbers in logic)
# ---------------------------------------------------------------------------

POOL_MAX: float = 100.0
POOL_REGEN_RATE: float = 0.15
POOL_INIT: float = 80.0
COLLAPSE_EPSILON: float = 0.05
POOL_MIN: float = 0.0

# Somatic enforcement — pool crisis → amplified resource trauma (GovSim)
POOL_CRISIS_THRESHOLD: float = 0.30
CRISIS_TRAUMA_MULTIPLIER: float = 2.5
# Pre-multiplier base: NORMAL band; ×2.5 → 1.0 TRAUMA (clamped to METRIC_MAX)
CRISIS_BASE_MAGNITUDE: float = DELTA_THRESHOLD_NORMAL
CRISIS_AFFECTED_DOMAIN: str = "resource"

EXTRACTION_KEY_AGENT_ID: str = "agent_id"
EXTRACTION_KEY_AMOUNT: str = "amount"
EXTRACTION_KEY_EVENT: str = "event"

_CRISIS_SNAPSHOT_AXES: tuple[str, ...] = (
    "energy",
    "resource_load",
    "uncertainty_load",
    "social_load",
)


@dataclass
class EnvironmentState:
    """Shared pool snapshot at one event-counter tick.

    Biology analogy: the current biomass of the commons, whether it has
    crossed the collapse floor, and the immutable ledger of who took what.
    """

    pool: float = POOL_INIT
    event_counter: int = 0
    collapsed: bool = False
    extraction_history: list[dict] = field(default_factory=list)


def _clamp_pool(value: float) -> float:
    """Keep pool level inside [POOL_MIN, POOL_MAX]."""

    return max(POOL_MIN, min(POOL_MAX, value))


def step_pool(
    env: EnvironmentState,
    extractions: dict[str, float],
) -> EnvironmentState:
    """Advance the commons one event: regenerate, extract, record, tick.

    Biology analogy: logistic growth adds stock toward carrying capacity,
    harvests subtract, and if the remainder sits at or below the collapse
    fraction the pasture is treated as collapsed.

    P_next = clamp(P + r·P·(1 − P/P_max) − Σ extractions, POOL_MIN, POOL_MAX)
    """

    pool = float(env.pool)
    regenerated = pool + POOL_REGEN_RATE * pool * (1.0 - pool / POOL_MAX)
    total_extraction = sum(float(amount) for amount in extractions.values())
    pool_next = _clamp_pool(regenerated - total_extraction)

    event_counter = int(env.event_counter) + 1
    history = list(env.extraction_history)
    for agent_id, amount in extractions.items():
        history.append(
            {
                EXTRACTION_KEY_AGENT_ID: str(agent_id),
                EXTRACTION_KEY_AMOUNT: float(amount),
                EXTRACTION_KEY_EVENT: event_counter,
            }
        )

    return EnvironmentState(
        pool=pool_next,
        event_counter=event_counter,
        collapsed=pool_next <= POOL_MAX * COLLAPSE_EPSILON,
        extraction_history=history,
    )


def get_pool_ratio(env: EnvironmentState) -> float:
    """Return pool / POOL_MAX — scarcity signal for T_cognitive and F_agent."""

    return float(env.pool) / POOL_MAX


def agent_delta_pool(env: EnvironmentState, agent_id: str) -> float:
    """Sum of all extractions by agent_id from extraction_history (F_agent)."""

    target = str(agent_id)
    return sum(
        float(entry[EXTRACTION_KEY_AMOUNT])
        for entry in env.extraction_history
        if str(entry[EXTRACTION_KEY_AGENT_ID]) == target
    )


def _crisis_snapshot(resource_load: float) -> dict[str, float]:
    """Minimal InternalState-shaped snapshot for a crisis DeltaRecord."""

    return {
        axis: (float(resource_load) if axis == "resource_load" else METRIC_MIN)
        for axis in _CRISIS_SNAPSHOT_AXES
    }


def crisis_trauma_magnitude(
    base_magnitude: float = CRISIS_BASE_MAGNITUDE,
) -> float:
    """Amplified crisis magnitude clamped to [METRIC_MIN, METRIC_MAX]."""

    return max(
        METRIC_MIN,
        min(METRIC_MAX, float(base_magnitude) * CRISIS_TRAUMA_MULTIPLIER),
    )


def apply_crisis_trauma(
    env: EnvironmentState,
    drift_state: DriftState,
    *,
    base_magnitude: float = CRISIS_BASE_MAGNITUDE,
) -> DriftState:
    """Apply multiplied resource trauma when pool_ratio < crisis threshold.

    Biology analogy: famine below the survival floor leaves a somatic scar —
    not a label, but a permanent domain shift via update_drift. Callers pass
    the post-step EnvironmentState; above-threshold pools are a no-op.

    The resulting DriftState flags feed F_agent-gated generation transfer
    (cautionary inheritance when fitness is low).
    """

    if get_pool_ratio(env) >= POOL_CRISIS_THRESHOLD:
        return drift_state

    magnitude = crisis_trauma_magnitude(base_magnitude)
    scarcity_load = max(METRIC_MIN, min(METRIC_MAX, 1.0 - get_pool_ratio(env)))
    delta = DeltaRecord(
        timestamp=int(env.event_counter),
        magnitude=magnitude,
        affected_domain=CRISIS_AFFECTED_DOMAIN,  # type: ignore[arg-type]
        snapshot_before=_crisis_snapshot(METRIC_MIN),
        snapshot_after=_crisis_snapshot(scarcity_load),
    )
    return update_drift(drift_state, delta)


def step_pool_with_crisis(
    env: EnvironmentState,
    extractions: dict[str, float],
    drift_by_agent: dict[str, DriftState],
) -> tuple[EnvironmentState, dict[str, DriftState]]:
    """Advance the pool, then apply somatic crisis trauma to each agent.

    Equivalent to step_pool followed by apply_crisis_trauma per agent_id.
    Agents absent from drift_by_agent receive a fresh DriftState before
    the crisis check. Returns (new_env, updated_drift_by_agent).
    """

    next_env = step_pool(env, extractions)
    updated: dict[str, DriftState] = {}
    agent_ids = set(drift_by_agent) | {str(aid) for aid in extractions}
    for agent_id in agent_ids:
        prior = drift_by_agent.get(str(agent_id), DriftState())
        updated[str(agent_id)] = apply_crisis_trauma(next_env, prior)
    return next_env, updated
