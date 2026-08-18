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
    # Carrying capacity of THIS pasture. A field rather than the module
    # constant because D-081 decided the commons scales with N while per-capita
    # capacity stays at today's number: N agents graze a pasture N times
    # larger, so their per-capita trajectory is the N=1 universe's, unchanged.
    # Reading POOL_MAX directly would have made a bigger population simply
    # poorer (measured: with N=4 the pasture died by generation 2, D-102).
    # The default keeps every existing single-agent run byte-identical.
    capacity: float = POOL_MAX


def _clamp_pool(value: float, capacity: float = POOL_MAX) -> float:
    """Keep pool level inside [POOL_MIN, capacity]."""

    return max(POOL_MIN, min(float(capacity), value))


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


def realized_extractions_sequential(
    regenerated: float,
    requested: dict[str, float],
) -> dict[str, float]:
    """Serve the announced withdrawals IN ORDER, each from what is left (P0-①).

    Biology analogy: the herd reaches the water one after another, and the last
    animal drinks what the others left.

    This is what "sequential access" in P0 option ① actually means, and it is
    the half that breaks the symmetry: under the proportional split every agent
    that asks for the same amount gets the same amount, so identical agents stay
    identical forever — measured in the D-103 pilot, where eight founders came
    out bit-identical and Cov(w, z) was zero by construction.

    Order is the caller's, carried by the insertion order of ``requested``: the
    act order is a physics decision that has to be declared (D-079), and ① adds
    that it should ROTATE so no position is permanently advantaged.

    Regeneration is NOT repeated per agent — the pasture still grows once per
    round. Only the service is sequential.
    """

    available = max(POOL_MIN, float(regenerated) - POOL_MIN)
    granted: dict[str, float] = {}
    for agent_id, amount in requested.items():
        want = max(0.0, float(amount))
        take = min(want, available)
        granted[agent_id] = take
        available -= take
    return granted


def step_pool(
    env: EnvironmentState,
    extractions: dict[str, float],
    sequential: bool = False,
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
    capacity = float(env.capacity)
    regenerated = pool + POOL_REGEN_RATE * pool * (1.0 - pool / capacity)
    granted = (
        realized_extractions_sequential(regenerated, extractions)
        if sequential
        else realized_extractions(regenerated, extractions)
    )
    total_extraction = sum(granted.values())
    pool_next = _clamp_pool(regenerated - total_extraction, capacity)

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
        collapsed=pool_next <= capacity * COLLAPSE_EPSILON,
        extraction_history=history,
        capacity=capacity,
    )


def get_pool_ratio(env: EnvironmentState) -> float:
    """Return pool / capacity — scarcity signal for T_cognitive and F_agent.

    Divides by the pasture's OWN capacity, so the ratio means the same thing to
    one agent and to a population of N sharing an N-times-larger commons: the
    crisis threshold, the collapse floor and F_agent's pool term all keep their
    calibration as N changes (D-081).
    """

    return float(env.pool) / float(env.capacity)


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


def crisis_trauma_magnitude(
    pool_ratio: float,
    base_magnitude: float = CRISIS_BASE_MAGNITUDE,
) -> float | None:
    """The magnitude a famine at this pool_ratio scars with, or None for no crisis.

    Split out of ``apply_crisis_trauma`` by D-117 so the run can REPORT this
    number instead of a reader inferring it. D-115 is why: ``z`` is written by
    two paths — the agent's own DeltaRecord and this one — and the second wrote
    nothing to any log, so D-112's "distance to the trauma threshold" profile
    described only half the universe and made a seed where 0 of 72 lives
    crossed the individual threshold look identical to one where nothing
    happened, while 72 of 72 of its agents carried drift.

    Kept as the single authority rather than duplicated in the recorder: a
    reporter that multiplied the two constants itself would be §2.8's error,
    which is the error D-115 punished.
    """

    if pool_ratio >= POOL_CRISIS_THRESHOLD:
        return None
    return max(
        METRIC_MIN,
        min(METRIC_MAX, float(base_magnitude) * CRISIS_TRAUMA_MULTIPLIER),
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

    crisis_magnitude = crisis_trauma_magnitude(pool_ratio, base_magnitude)
    if crisis_magnitude is None:
        return drift_state

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
    sequential: bool = False,
) -> tuple[EnvironmentState, dict[str, DriftState]]:
    """Advance the pool, then apply somatic crisis trauma to each agent."""

    new_env = step_pool(env_state, extractions, sequential=sequential)
    pool_ratio = get_pool_ratio(new_env)
    updated_drifts = {
        agent_id: apply_crisis_trauma(ds, pool_ratio)
        for agent_id, ds in drift_states.items()
    }
    return new_env, updated_drifts
