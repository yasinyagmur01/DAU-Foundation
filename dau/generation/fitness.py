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

FITNESS_W_ENERGY: float = 0.4  # weight: energy held across the life
FITNESS_W_POOL: float = 0.3  # weight: pool preservation
FITNESS_W_SURVIVAL: float = 0.3  # weight: time survived

# D-086. Which energy reading the w_energy term scores. Runs before D-086 used
# the final reading and runs after use the lifetime mean, and the two produce
# different F_agent from identical lives — 0.139 vs 0.446 on the same twelve
# D-085 lineages. Nothing else in a results file distinguishes them, so the
# label travels in tool_identity (U5 / D-030 pattern: say out loud which
# formula ran rather than letting a reader assume).
FITNESS_ENERGY_READING: str = "mean_over_life"

# Below this spread a cell has no relative structure to read (D-152). Named
# rather than testing == 0.0 because F_agent is a sum of floats and an exact
# tie is not the only way to have nothing to compare.
FITNESS_SPREAD_EPSILON: float = 1e-12

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
    energy_lived: float,
    delta_pool: float,
    t_survived: int,
    t_generation: int,
    per_event_extraction_max: float = EXTRACTION_DEFECT,
) -> float:
    """Objective ancestral survival fitness F_agent in [0, 1].

    Biology analogy: how well fuelled the life was, how gently the commons was
    used *while it was used*, and what fraction of the generation's event span
    the organism endured.

    F = w_e·(E_lived/E_max) + w_p·(1 − (|Δpool|/t_survived)/X_max) + w_s·(t_survived / t_gen)

    D-086: the energy term reads the LIFE, not the ending. It used to take
    E_final, and since D-066 the only way a life ends is energy exhaustion, so
    E_final is fixed at ~0 BY THE DEATH RULE — 10 of 12 lineages reported
    exactly 0.000 in the D-085 validation run and the term contributed nothing
    to 40% of the score. run_protocol_c_prime already carried that diagnosis in
    a comment ("it measures the ending, not the living") but applied it only to
    the K2 endpoint reading, leaving F_agent on the dead term. Same defect class
    as the survival term before D-071 (t_survived/t_survived ≡ 1.0): a term that
    is not measuring what its name claims.

    ``energy_lived`` is the mean energy over the events the agent actually
    lived; self_model.f_agent_inputs derives it. The landmark reading was
    rejected as the alternative: it is K2's ENDPOINT, so feeding it into
    fitness would make F_agent and the outcome share one number and rebuild the
    Mills & Beatty tautology D-075 warned about. The three layers stay separate
    — F_agent (input) → w (heirs) → z (landmark drift, outcome).

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

    energy_term = float(energy_lived) / ENERGY_MAX
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
    """Map F_agent onto low / normal / high transfer policy bands — ABSOLUTE.

    ⚠ Kept, and kept unchanged, because the single-lineage runner still reads
    it: there is no population to be relative TO when one agent lives alone.
    The population path uses ``classify_fitness_relative`` (D-152).
    """

    if float(f_agent) < FITNESS_LOW_THRESHOLD:
        return FITNESS_LABEL_LOW
    if float(f_agent) >= FITNESS_HIGH_THRESHOLD:
        return FITNESS_LABEL_HIGH
    return FITNESS_LABEL_NORMAL


def normalize_fitness(f_agent: float, reference: list[float]) -> float | None:
    """Where this F_agent sits INSIDE its own cell, in [0, 1]. None if flat.

    ⚠ D-152, and the reason is arithmetic rather than preference. The bands
    were calibrated against a quantity spanning [0, 1]; D-086 then moved
    F_agent from ~0.14 to ~0.45 and the observed range collapsed into the
    middle. Measured on C2: 216 of 216 agents landed in `normal`, the low band
    got 0 of 216, and the minimum F_agent (0.3919) sat ABOVE the low threshold
    (0.35). Two of three bands were unreachable, so the transfer policy the
    design wrote three rules for had one rule.

    ⛔ The threshold is NOT the defect and was NOT changed: 0.35 is exactly
    FITNESS_HIGH_THRESHOLD / 2, so it is derived, not magic (D-151). What
    changed is the QUANTITY it is applied to — the same correction D-088 made
    when a bar calibrated for memory_score was found gating a product.

    Relative rather than absolute is also what the rest of this design already
    is: the tournament (P2, k=2) decides fitness by comparing two agents to
    each other. ``fitness_class`` was the one absolute rule left.

    ⚠ Declared cost, not hidden: min-max means the least fit agent of a cell
    always normalizes to 0.0 and the most fit to 1.0, so every cell with any
    spread now names a low and a high. That is a design claim — "in every
    generation somebody is relatively unfit" — and it is what makes the
    inherited-warning branch reachable at all.

    ⚠ Returns None when the cell is FLAT (spread at or below epsilon): with
    identical agents nobody is relatively anything, and inventing a band there
    would manufacture a difference the universe did not make. Callers read
    None as "no relative differentiation exists", not as zero.
    """

    if not reference:
        return None
    low = min(float(v) for v in reference)
    high = max(float(v) for v in reference)
    if (high - low) <= FITNESS_SPREAD_EPSILON:
        return None
    return (float(f_agent) - low) / (high - low)


def classify_fitness_relative(f_agent: float, reference: list[float]) -> str:
    """The band this F_agent occupies WITHIN its cell (D-152).

    Uses the same two thresholds as ``classify_fitness`` — they are not
    re-derived here, because the point of the change is the quantity, not the
    bar. A flat cell reports `normal` for everyone: no agent is relatively
    unfit when all are identical.
    """

    normalized = normalize_fitness(f_agent, reference)
    if normalized is None:
        return FITNESS_LABEL_NORMAL
    return classify_fitness(normalized)


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
