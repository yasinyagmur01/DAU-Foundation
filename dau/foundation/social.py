"""Social load — cooperation stress vs coordination friction.

Research: Akata et al. 2025 + Gemini report (Problem 1). Cooperation failure
(betrayal risk) and coordination failure (convention breakdown) are structurally
different. They are computed separately and only then combined into social_load.

No LLM calls. All metrics are deterministic Python floats in [0, 1].
"""

from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass, field

from .state import METRIC_MAX, METRIC_MIN

# ---------------------------------------------------------------------------
# Social-load weights and trust / window constants (no magic numbers in logic)
# ---------------------------------------------------------------------------

SOCIAL_W1: float = 0.5  # weight for cooperation_stress in social_load
SOCIAL_W2: float = 0.5  # weight for coordination_friction in social_load

TRUST_DECAY: float = 0.1  # bilateral trust reduction per defection
TRUST_INIT: float = 1.0  # starting trust between any two agents
TRUST_RECOVERY_FACTOR: float = 0.5  # cooperate restores at half the decay rate
TRUST_RECOVERY: float = TRUST_DECAY * TRUST_RECOVERY_FACTOR

ENTROPY_WINDOW: int = 10  # last N interactions for Shannon entropy
MARKOV_WINDOW: int = 20  # last N interactions for P(cooperate)

OUTCOME_COOPERATE: str = "cooperate"
OUTCOME_DEFECT: str = "defect"
OUTCOME_COORDINATE: str = "coordinate"
OUTCOME_DEADLOCK: str = "deadlock"

COOPERATIVE_OUTCOMES: frozenset[str] = frozenset(
    {OUTCOME_COOPERATE, OUTCOME_COORDINATE}
)

TRUST_KEY_SEPARATOR: str = ":"
MIN_DENOMINATOR: int = 1
DEADLOCK_FLAG_ON: float = 1.0
DEADLOCK_FLAG_OFF: float = 0.0
ENTROPY_EMPTY: float = 0.0


@dataclass
class InteractionRecord:
    """One directed social outcome between two agents at an event counter.

    Biology analogy: a single exchange — cooperate, defect, coordinate, or
    deadlock — stamped by event order, never wall-clock time.
    """

    agent_id: str
    opponent_id: str
    outcome: str  # "cooperate" | "defect" | "coordinate" | "deadlock"
    event_counter: int


@dataclass
class SocialState:
    """Accumulated dyadic history and bilateral trust for social_load.

    Biology analogy: the organism's lived record of conspecific exchanges and
    how much trust remains in each directed relationship.
    """

    interactions: list[InteractionRecord] = field(default_factory=list)
    bilateral_trust: dict[str, float] = field(default_factory=dict)
    # key = f"{agent_id}:{opponent_id}"


def _clamp(value: float) -> float:
    """Keep a social metric inside the unit interval."""

    return max(METRIC_MIN, min(METRIC_MAX, value))


def _trust_key(agent_id: str, opponent_id: str) -> str:
    """Build the directed bilateral-trust dict key."""

    return f"{agent_id}{TRUST_KEY_SEPARATOR}{opponent_id}"


def _directed_interactions(
    social: SocialState,
    agent_id: str,
    opponent_id: str,
) -> list[InteractionRecord]:
    """Interactions where agent acted toward opponent."""

    return [
        record
        for record in social.interactions
        if record.agent_id == agent_id and record.opponent_id == opponent_id
    ]


def _pair_interactions(
    social: SocialState,
    agent_id: str,
    opponent_id: str,
) -> list[InteractionRecord]:
    """All interactions between a dyad, either direction."""

    pair = {agent_id, opponent_id}
    return [
        record
        for record in social.interactions
        if {record.agent_id, record.opponent_id} == pair
    ]


def shannon_entropy(outcomes: list[str]) -> float:
    """Shannon entropy H = -sum(p * log2(p)) over outcome frequencies.

    Empty history returns 0.0. Fully uniform over k distinct outcomes → log2(k).
    """

    if not outcomes:
        return ENTROPY_EMPTY

    counts = Counter(outcomes)
    total = len(outcomes)
    entropy = ENTROPY_EMPTY
    for count in counts.values():
        probability = count / total
        if probability > METRIC_MIN:
            entropy -= probability * math.log2(probability)
    return entropy


def record_interaction(
    social: SocialState,
    record: InteractionRecord,
) -> SocialState:
    """Append an interaction and update bilateral trust both directions.

    Defect lowers trust by TRUST_DECAY (floor 0). Cooperate raises trust by
    TRUST_RECOVERY (ceiling 1). Coordinate / deadlock leave trust unchanged.
    """

    new_interactions = list(social.interactions)
    new_interactions.append(record)
    new_trust = dict(social.bilateral_trust)

    keys = (
        _trust_key(record.agent_id, record.opponent_id),
        _trust_key(record.opponent_id, record.agent_id),
    )
    for key in keys:
        current = new_trust.get(key, TRUST_INIT)
        if record.outcome == OUTCOME_DEFECT:
            new_trust[key] = _clamp(current - TRUST_DECAY)
        elif record.outcome == OUTCOME_COOPERATE:
            new_trust[key] = _clamp(current + TRUST_RECOVERY)

    return SocialState(interactions=new_interactions, bilateral_trust=new_trust)


def compute_cooperation_stress(
    social: SocialState,
    agent_id: str,
    opponent_id: str,
) -> float:
    """Betrayal-risk axis: defect rate × (1 − trust), clamped to [0, 1]."""

    directed = _directed_interactions(social, agent_id, opponent_id)
    total = len(directed)
    defect_count = sum(
        1 for record in directed if record.outcome == OUTCOME_DEFECT
    )
    trust = social.bilateral_trust.get(
        _trust_key(agent_id, opponent_id),
        TRUST_INIT,
    )
    defect_rate = defect_count / max(total, MIN_DENOMINATOR)
    return _clamp(defect_rate * (1.0 - trust))


def compute_coordination_friction(
    social: SocialState,
    agent_id: str,
    opponent_id: str,
) -> float:
    """Convention-breakdown axis: Shannon entropy × recent deadlock flag."""

    pair_history = _pair_interactions(social, agent_id, opponent_id)
    window = pair_history[-ENTROPY_WINDOW:]
    outcomes = [record.outcome for record in window]
    entropy = shannon_entropy(outcomes)
    if not window:
        last_deadlock = DEADLOCK_FLAG_OFF
    elif window[-1].outcome == OUTCOME_DEADLOCK:
        last_deadlock = DEADLOCK_FLAG_ON
    else:
        last_deadlock = DEADLOCK_FLAG_OFF
    return _clamp(entropy * last_deadlock)


def compute_social_load(
    social: SocialState,
    agent_id: str,
    opponent_id: str,
) -> float:
    """Weighted composite of cooperation stress and coordination friction."""

    cooperation_stress = compute_cooperation_stress(social, agent_id, opponent_id)
    coordination_friction = compute_coordination_friction(
        social, agent_id, opponent_id
    )
    return _clamp(
        SOCIAL_W1 * cooperation_stress + SOCIAL_W2 * coordination_friction
    )


def compute_markov_expectation(
    social: SocialState,
    agent_id: str,
    opponent_id: str,
) -> float:
    """P(opponent cooperates | recent actions) for pre-node context injection.

    Counts cooperate and coordinate as cooperative outcomes over the last
    MARKOV_WINDOW actions the opponent took toward this agent.
    """

    opponent_actions = _directed_interactions(social, opponent_id, agent_id)
    window = opponent_actions[-MARKOV_WINDOW:]
    total = len(window)
    cooperate_count = sum(
        1 for record in window if record.outcome in COOPERATIVE_OUTCOMES
    )
    return cooperate_count / max(total, MIN_DENOMINATOR)
