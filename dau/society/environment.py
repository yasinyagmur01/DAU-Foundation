"""Shared resource pool physics — GovSim-style CPR dynamics for Layer 4.

Biology analogy: a common pasture regenerates logistically toward carrying
capacity; extraction subtracts from the stock. Collapse is not a label —
it is a pool level that has fallen to a near-empty fraction of capacity.
"""

from __future__ import annotations

from dataclasses import dataclass, field

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

# Somatic enforcement — pool crisis → amplified resource trauma
POOL_CRISIS_THRESHOLD: float = 0.30
CRISIS_TRAUMA_MULTIPLIER: float = 2.5
CRISIS_BASE_MAGNITUDE: float = 0.4
CRISIS_AFFECTED_DOMAIN: str = "resource"
CRISIS_EVENT_COUNTER: int = 0

EXTRACTION_KEY_AGENT_ID: str = "agent_id"
EXTRACTION_KEY_AMOUNT: str = "amount"
EXTRACTION_KEY_EVENT: str = "event"

_CRISIS_SNAPSHOT: dict[str, float] = {
    "energy": 1.0,
    "resource_load": 0.0,
    "uncertainty_load": 0.0,
    "social_load": 0.0,
}


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


def realized_extractions(
    regenerated: float,
    requested: dict[str, float],
) -> dict[str, float]:
    """Split what the commons can actually give (D-066).

    Nobody harvests stock that is not there. The pool was always clamped at
    POOL_MIN, but the ledger recorded the REQUESTED amount, so an agent could
    "take 8.0" from an empty pasture and have it written down as taken. That
    made over-extraction free in exactly the place the cost should appear:
    agent_delta_pool summed announcements rather than harvests, and with the
    metabolic loop closed it would have fed energy out of an empty pool
    forever.

    Short-fall is shared in proportion to what each agent asked for; with one
    agent this is simply min(requested, available).
    """

    available = max(POOL_MIN, float(regenerated) - POOL_MIN)
    total_requested = sum(max(0.0, float(amount)) for amount in requested.values())
    if total_requested <= available:
        return {agent: max(0.0, float(amount)) for agent, amount in requested.items()}
    if total_requested <= POOL_MIN:
        return {agent: 0.0 for agent in requested}
    share = available / total_requested
    return {
        agent: max(0.0, float(amount)) * share for agent, amount in requested.items()
    }


def step_pool(
    env: EnvironmentState,
    extractions: dict[str, float],
) -> EnvironmentState:
    """Advance the commons one event: regenerate, extract, record, tick.

    Biology analogy: logistic growth adds stock toward carrying capacity,
    harvests subtract, and if the remainder sits at or below the collapse
    fraction the pasture is treated as collapsed.

    P_next = clamp(P + r·P·(1 − P/P_max) − Σ realized, POOL_MIN, POOL_MAX)

    ``extractions`` is what the agents announced; what the ledger keeps is what
    the pasture could actually deliver (D-066).
    """

    pool = float(env.pool)
    regenerated = pool + POOL_REGEN_RATE * pool * (1.0 - pool / POOL_MAX)
    granted = realized_extractions(regenerated, extractions)
    total_extraction = sum(granted.values())
    pool_next = _clamp_pool(regenerated - total_extraction)

    event_counter = int(env.event_counter) + 1
    history = list(env.extraction_history)
    for agent_id, amount in granted.items():
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


def realized_extraction_at(
    env: EnvironmentState,
    agent_id: str,
    event: int,
) -> float:
    """What agent_id actually harvested at one event, read from the ledger.

    The metabolic loop reads this rather than re-deriving the harvest from the
    decision: the announced amount and the delivered amount separate exactly
    when the pool runs dry, and that is the case the cost depends on (D-066).
    """

    target = str(agent_id)
    return sum(
        float(entry[EXTRACTION_KEY_AMOUNT])
        for entry in env.extraction_history
        if str(entry[EXTRACTION_KEY_AGENT_ID]) == target
        and int(entry[EXTRACTION_KEY_EVENT]) == int(event)
    )


def agent_delta_pool(env: EnvironmentState, agent_id: str) -> float:
    """Sum of all extractions by agent_id from extraction_history (F_agent)."""

    target = str(agent_id)
    return sum(
        float(entry[EXTRACTION_KEY_AMOUNT])
        for entry in env.extraction_history
        if str(entry[EXTRACTION_KEY_AGENT_ID]) == target
    )


def apply_crisis_trauma(
    drift_state: DriftState,
    pool_ratio: float,
    base_magnitude: float = CRISIS_BASE_MAGNITUDE,
) -> DriftState:
    """Apply multiplied resource trauma when pool_ratio < crisis threshold.

    Biology analogy: famine below the survival floor leaves a somatic scar —
    not a label, but a permanent domain shift via update_drift.
    """

    if pool_ratio >= POOL_CRISIS_THRESHOLD:
        return drift_state

    crisis_magnitude = max(
        METRIC_MIN,
        min(METRIC_MAX, float(base_magnitude) * CRISIS_TRAUMA_MULTIPLIER),
    )
    dummy_delta = DeltaRecord(
        timestamp=CRISIS_EVENT_COUNTER,
        magnitude=crisis_magnitude,
        affected_domain=CRISIS_AFFECTED_DOMAIN,  # type: ignore[arg-type]
        snapshot_before=dict(_CRISIS_SNAPSHOT),
        snapshot_after=dict(_CRISIS_SNAPSHOT),
    )
    return update_drift(drift_state, dummy_delta)


def step_pool_with_crisis(
    env_state: EnvironmentState,
    extractions: dict[str, float],
    drift_states: dict[str, DriftState],
) -> tuple[EnvironmentState, dict[str, DriftState]]:
    """Advance the pool, then apply somatic crisis trauma to each agent."""

    new_env = step_pool(env_state, extractions)
    pool_ratio = get_pool_ratio(new_env)
    updated_drifts = {
        agent_id: apply_crisis_trauma(ds, pool_ratio)
        for agent_id, ds in drift_states.items()
    }
    return new_env, updated_drifts
