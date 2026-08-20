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

# ---------------------------------------------------------------------------
# Stock-proportional harvest ceiling — Layer 1 (D-162)
# ---------------------------------------------------------------------------
# The commons used to serve a CONSTANT quota: whatever an agent announced was
# handed over in full until the stock ran out, and then nobody got anything.
# Measured consequence (real `step_pool`, 8 agents, all defecting): the
# short-fall is EXACTLY ZERO through event 16 and the pool is at absolute zero
# from event ~18 onward. So the pasture had two stable regimes and nothing in
# between — D-081's "no gradual scarcity, only a scarcity moment" — and P0-①
# had nothing to differentiate on until the collapse had already happened.
#
# That this is the binding problem, rather than "scarcity never bites", was
# measured across four seeds: in the ONE founder generation whose pool actually
# collapsed the eight founders came out with three distinct F_agent values,
# while in the three whose pool never bit they were bit-identical (D-162 §1).
# Sequential access works. It just needs a short-fall to work on.
#
# The ceiling makes the squeeze GRADUATED: what an agent may take falls with
# the stock, so a short-fall exists from the second event on and grows
# smoothly, and the pool relaxes toward an equilibrium instead of hitting an
# absorbing zero.
#
# ⛔ DEMAND IS UNTOUCHED. EXTRACTION_DEFECT stays 8.0 and the decision→outcome
# map is not edited: what an agent WANTS is behaviour, and reaching into it
# would be the cognitive prior K7 closed on axiom grounds. Only what the
# commons can GIVE changed — a property of the environment, which is the test
# D-082 §P.5 set for a legitimate lever.
#
# ⭐ The ratio is DERIVED, not chosen. A ceiling makes the stock settle where
# what the herd may take equals what the pasture regrows, and that equilibrium
# is a closed form: r*p = REGEN*p*(1 - p/capacity) gives p/capacity = 1 - r/REGEN.
# So the ratio IS the choice of where the commons comes to rest, and the
# defensible place to put it is the floor the code already calls collapse:
#
#     equilibrium = COLLAPSE_EPSILON  ⇒  r = POOL_REGEN_RATE * (1 - COLLAPSE_EPSILON)
#
# The criterion is structural — the universe must be able to traverse the
# regimes it defines — and no run data enters it, which is the same standard
# LANDMARK_EVENT met by being tied to METABOLIC_GRACE_EVENTS.
#
# ⛔ The obvious alternative, r = EXTRACTION_DEFECT / POOL_INIT ("bind the
# maximum demand at the initial stock"), was DERIVED JUST AS CLEANLY and was
# rejected on a measurement: it puts the equilibrium at capacity/3 = 0.333,
# above POOL_CRISIS_THRESHOLD = 0.30, so the pool can never enter crisis. The
# crisis channel is not decorative — it fires in 127 of 192 lives in the last
# real run (1461 events), and D-070's K6 defines S5's first trauma as exactly
# this event. A ratio that silently deletes a pre-registered channel is worse
# than one that starts biting five events later (D-163).
#
# Written as the expression, not as 0.1425, so the derivation cannot quietly
# become a tuned number (§2.8) and so a change to either constant carries the
# ceiling with it.
EXTRACTION_LIMIT_RATIO: float = POOL_REGEN_RATE * (1.0 - COLLAPSE_EPSILON)

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


def harvest_ceiling(available: float, n_requesters: int) -> float:
    """The most one agent may take from this stock right now (D-162).

    Biology analogy: a thinning pasture does not just run out one day — each
    mouthful gets smaller as the sward gets shorter.

    Proportional to the PER-CAPITA stock, so the rule reads the same for one
    agent as for eight: N grazers on a pasture N times larger face the same
    ceiling each, which is the invariant D-081 locked when the commons was
    scaled with N.

    A caller with no requesters gets the whole stock as its ceiling rather than
    a ZeroDivisionError; there is nobody to serve, so the number is unused, and
    a silent zero here would look like "the ceiling closed everything" in the
    ledger — the kind of fallback §2.9 forbids.
    """

    if n_requesters <= 0:
        return max(POOL_MIN, float(available))
    return EXTRACTION_LIMIT_RATIO * (max(POOL_MIN, float(available)) / n_requesters)


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
    # D-162. The ceiling applies here too: it is a property of the commons, not
    # of the service order, so a run that turns sequential access off must not
    # quietly get the old constant-quota physics back.
    ceiling = harvest_ceiling(available, len(requested))
    capped = {
        agent: min(max(0.0, float(amount)), ceiling)
        for agent, amount in requested.items()
    }
    total_requested = sum(capped.values())
    if total_requested <= available:
        return capped
    if total_requested <= POOL_MIN:
        return {agent: 0.0 for agent in requested}
    share = available / total_requested
    return {agent: amount * share for agent, amount in capped.items()}


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
    n_requesters = len(requested)
    granted: dict[str, float] = {}
    for agent_id, amount in requested.items():
        want = max(0.0, float(amount))
        # D-162. Recomputed from what is STILL THERE when this agent's turn
        # comes, and that is the whole mechanism: an agent served earlier looks
        # at a larger stock and may take more. A ceiling computed once per
        # round would cap everyone identically and identical agents would stay
        # identical — the degeneracy this layer exists to break.
        take = min(want, harvest_ceiling(available, n_requesters), available)
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
