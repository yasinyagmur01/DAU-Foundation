"""Shared resource pool physics — GovSim-style CPR dynamics for Layer 4.

Biology analogy: a common pasture regenerates logistically toward carrying
capacity; extraction subtracts from the stock. Collapse is not a label —
it is a pool level that has fallen to a near-empty fraction of capacity.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# Resource pool parameters (no magic numbers in logic)
# ---------------------------------------------------------------------------

POOL_MAX: float = 100.0
POOL_REGEN_RATE: float = 0.15
POOL_INIT: float = 80.0
COLLAPSE_EPSILON: float = 0.05
POOL_MIN: float = 0.0

EXTRACTION_KEY_AGENT_ID: str = "agent_id"
EXTRACTION_KEY_AMOUNT: str = "amount"
EXTRACTION_KEY_EVENT: str = "event"


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
