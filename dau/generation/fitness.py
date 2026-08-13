"""Ancestral survival fitness — objective F_agent for generational transfer.

Research: Gemini report (Problem 2, Fitness-Based Transfer). Fitness is not a
trait injection; it is a post-hoc score of how an agent survived energy drain,
commons extraction, and event-time longevity. Transfer weight W_transfer then
multiplies earned memory salience by this lived outcome.
"""

from __future__ import annotations

import math

from dau.foundation.state import METRIC_MAX, METRIC_MIN
from dau.society.extraction import EXTRACTION_DEFECT

# ---------------------------------------------------------------------------
# Fitness weights, thresholds, and transfer scaling (no magic numbers)
# ---------------------------------------------------------------------------

FITNESS_W_ENERGY: float = 0.4  # weight: remaining energy
FITNESS_W_POOL: float = 0.3  # weight: pool preservation
FITNESS_W_SURVIVAL: float = 0.3  # weight: time survived

FITNESS_LOW_THRESHOLD: float = 0.35  # below: trauma → cautionary inherited_warning
FITNESS_HIGH_THRESHOLD: float = 0.70  # above: trauma → inherited warning

ENERGY_MAX: float = 1.0
WARNING_SOMATIC_SCALE: float = 0.3  # inherited warning → 30% somatic weight

MIN_GENERATION_STEPS: int = 1
MIN_EVENTS_LIVED: int = 1  # divisor floor for the per-event pool rate (K4-b)

FITNESS_LABEL_LOW: str = "low"
FITNESS_LABEL_HIGH: str = "high"
FITNESS_LABEL_NORMAL: str = "normal"

W_TRANSFER_VALENCE_BASE: float = 1.0


def _clamp_unit(value: float) -> float:
    """Keep a fitness / transfer metric inside [METRIC_MIN, METRIC_MAX]."""

    return max(METRIC_MIN, min(METRIC_MAX, value))


def compute_fitness(
    energy_final: float,
    delta_pool: float,
    t_survived: int,
    t_generation: int,
    per_event_extraction_max: float = EXTRACTION_DEFECT,
) -> float:
    """Objective ancestral survival fitness F_agent in [0, 1].

    Biology analogy: how much fuel remained, how gently the commons was used
    *while it was used*, and what fraction of the generation's event span the
    organism endured.

    F = w_e·(E/E_max) + w_p·(1 − (|Δpool|/t_survived)/X_max) + w_s·(t_survived / t_gen)

    K4-b (D-070): the pool term is a RATE, not a lifetime sum. Summing the
    ledger made the term a lifespan proxy — the pilot's two lineages spread
    130.8 vs 62.2 (110%), but per event of life that is 6.88 vs 6.22 (10.7%),
    so nine tenths of the "commons" signal was longevity wearing a second hat.
    Stearns (1989) names that double counting directly. Longevity is priced
    once, by the survival term, against the generation's event budget.

    X_max is the largest harvest the deterministic decision→outcome map can
    yield (EXTRACTION_DEFECT), so the term reads behaviourally: 1.0 never
    touched the commons, 0.0 defected at every event. Free-text harvests parse
    above that ceiling and drive the term negative; the final clamp bounds it,
    as it already did for lifetime sums past P_max.
    """

    energy_term = float(energy_final) / ENERGY_MAX
    events_lived = max(int(t_survived), MIN_EVENTS_LIVED)
    pool_per_event = abs(float(delta_pool)) / float(events_lived)
    pool_term = 1.0 - pool_per_event / float(per_event_extraction_max)
    survival_term = float(t_survived) / float(
        max(int(t_generation), MIN_GENERATION_STEPS)
    )
    score = (
        FITNESS_W_ENERGY * energy_term
        + FITNESS_W_POOL * pool_term
        + FITNESS_W_SURVIVAL * survival_term
    )
    return _clamp_unit(score)


def classify_fitness(f_agent: float) -> str:
    """Map F_agent onto low / normal / high transfer policy bands."""

    if float(f_agent) < FITNESS_LOW_THRESHOLD:
        return FITNESS_LABEL_LOW
    if float(f_agent) >= FITNESS_HIGH_THRESHOLD:
        return FITNESS_LABEL_HIGH
    return FITNESS_LABEL_NORMAL


def compute_w_transfer(
    memory_score: float,
    f_agent: float,
    reward_marker: float,
    threat_marker: float,
) -> float:
    """Fitness-weighted transfer salience W_transfer in [0, 1].

    Biology analogy: a trace transfers when it was salient, the life was fit,
    and bodily reward outweighed threat at the moment of imprint.
    W = memory_score · F_agent · (1 + tanh(reward − threat))
    """

    valence = W_TRANSFER_VALENCE_BASE + math.tanh(
        float(reward_marker) - float(threat_marker)
    )
    weight = float(memory_score) * float(f_agent) * valence
    return _clamp_unit(weight)
