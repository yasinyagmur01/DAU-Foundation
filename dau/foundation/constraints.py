"""Environment constraint factory — the five universal pressures at runtime.

Biology analogy: the organism cannot rewrite gravity or seasons, but the
world's pressure snapshot can be refreshed each event while remaining
read-only to the agent itself.
"""

from __future__ import annotations

from .state import METRIC_MAX, METRIC_MIN, EnvironmentConstraints

# ---------------------------------------------------------------------------
# Default universe pressures at first contact with the world
# ---------------------------------------------------------------------------

DEFAULT_TIME_PRESSURE: float = 0.0
DEFAULT_RESOURCE_SCARCITY: float = 0.3  # mild scarcity at birth
DEFAULT_SOCIAL_PRESSURE: float = 0.0
DEFAULT_UNCERTAINTY: float = 0.5  # half-unknown at the start
DEFAULT_GENERATION_END: float = 0.0

# Weighted stress composition — general stress = sum of all pressures
WEIGHT_TIME_PRESSURE: float = 0.2
WEIGHT_RESOURCE_SCARCITY: float = 0.2
WEIGHT_SOCIAL_PRESSURE: float = 0.2
WEIGHT_UNCERTAINTY: float = 0.2
WEIGHT_GENERATION_END: float = 0.2

# DAERM — Dynamic Allostatic Equilibrium Recovery Model
ALLOSTATIC_SETPOINT_MAX: float = 0.75
CROSS_AXIS_SPILLOVER: float = 0.20
METABOLIC_FLOOR: float = 0.05
MAGNITUDE_PEAK_WEIGHT: float = 0.70

# Signal v2 — NLI polarity gate for preference pairs (CPU cross-encoder)
NLI_CONTRADICTION_THRESHOLD: float = 0.60
NLI_MODEL_NAME: str = "cross-encoder/nli-deberta-v3-small"
DAU_NLI_FILTER_ENABLED: bool = True  # override: DAU_NLI_FILTER_ENABLED=0

# Per-agent QLoRA (Punica pattern) — independent adapters, shared frozen base
PER_AGENT_LORA_RANK: int = 8
PER_AGENT_LORA_ALPHA: int = 16
ADAPTER_BASE_DIR: str = "dau_runs/adapters"
ADAPTER_SWITCH_MAX_MS: int = 1

# ADIM 3 — DPO preference micro-train at generation end. The reference policy
# is the same model with adapters disabled, so no second set of base weights
# is held in memory.
DPO_BETA: float = 0.10
DPO_LEARNING_RATE: float = 5e-5
DPO_EPOCHS: int = 1
# One pair per step. A batch holds every pair's forward graph alive at once —
# two sides each — so batch 2 needs four full graphs before backward. The 4-bit
# 8B already occupies 7.49 GiB of an 8 GiB card and OOMs there.
DPO_BATCH_SIZE: int = 1
# D-021/A1. The micro-batch stays 1 — batch 2 OOMs — but the optimizer steps
# once per N micro-steps, so the gradient is averaged over N pairs instead of
# one. What the code had was gradient CHECKPOINTING (a memory technique); this
# is gradient ACCUMULATION (a gradient technique).
# UNCALIBRATED: the pair filter currently yields 1-2 pairs per life, where any
# N degenerates to a single tail flush. The value cannot be calibrated until
# U5 opens that bottleneck; 4 is a conservative default, not a measured one.
DPO_GRADIENT_ACCUMULATION_STEPS: int = 4
# D-027 (was 256). _encode_pair_side drops the prompt HEAD on overflow, and the
# head is the chat template header plus SYSTEM_PROMPT — so training learned
# from a mutilated instruction that generate_completion never truncates. A real
# prompt is 246 tokens with no recalled memory and 306 with MAX_RETRIEVED_
# MEMORIES=3, so one memory already overflowed 256. Measured cost of the wider
# window: +479 MiB training peak (6139.5 -> 6618.6 on a 7807.6 MiB card).
DPO_MAX_SEQUENCE_TOKENS: int = 512
DPO_MAX_GRAD_NORM: float = 1.0

# HippoRAG 2 — Personalized PageRank over SQLite domain co-occurrence (CPU)
PPR_ALPHA = 0.85
PPR_WEIGHT_IN_SCORE = 0.30
PPR_TOP_K_DOMAINS = 10

# ADIM 5 — precision-weighted PE (rolling raw-PE history variance)
PRECISION_EPSILON = 1e-6
PRECISION_HISTORY_WINDOW = 10
PRECISION_MIN_HISTORY = 2  # cold start: fewer samples → neutral π=1.0
# Uniform[0,1] population variance — scales history var into an adaptive band.
PRECISION_VAR_REF = 1.0 / 12.0
PRECISION_MIN_WEIGHT = 0.5  # crisis / high-variance floor
# Ceiling on amplification. Measured raw PE peaks near 0.81; 1.2 keeps
# PE_w = min(raw·π, 1.0) from saturating the majority of events at 1.0.
PRECISION_MAX_WEIGHT = 1.2


def build_default_constraints() -> EnvironmentConstraints:
    """Build the default read-only EnvironmentConstraints snapshot.

    Biology analogy: birth conditions — mild scarcity, half-known world,
    no social or generational pressure yet.
    """

    return EnvironmentConstraints(
        time_pressure=DEFAULT_TIME_PRESSURE,
        resource_scarcity=DEFAULT_RESOURCE_SCARCITY,
        social_pressure=DEFAULT_SOCIAL_PRESSURE,
        uncertainty=DEFAULT_UNCERTAINTY,
        generation_end=DEFAULT_GENERATION_END,
    )


def update_constraints(
    current: EnvironmentConstraints,
    **kwargs: float,
) -> EnvironmentConstraints:
    """Produce a new frozen constraint snapshot with selected fields updated.

    Biology analogy: the external world can shift (season, famine, crowding)
    but the organism receives a fresh immutable reading — never a mutable edit
    of the previous reading in place.

    Validation: every constraint must stay in [METRIC_MIN, METRIC_MAX].
    """

    data = current.model_dump()
    for key, value in kwargs.items():
        if key not in data:
            raise ValueError(f"Unknown constraint field: {key!r}")
        if not (METRIC_MIN <= value <= METRIC_MAX):
            raise ValueError(
                f"{key}={value} outside [{METRIC_MIN}, {METRIC_MAX}]"
            )
        data[key] = value
    return EnvironmentConstraints(**data)


def compute_pressure_score(constraints: EnvironmentConstraints) -> float:
    """Weighted average of the five universal pressures.

    Biology analogy: general stress level — the summed load of all external
    pressures acting on the organism at once. Layer 2 may later modulate
    delta magnitude with this score; here it is only produced.
    """

    score = (
        WEIGHT_TIME_PRESSURE * constraints.time_pressure
        + WEIGHT_RESOURCE_SCARCITY * constraints.resource_scarcity
        + WEIGHT_SOCIAL_PRESSURE * constraints.social_pressure
        + WEIGHT_UNCERTAINTY * constraints.uncertainty
        + WEIGHT_GENERATION_END * constraints.generation_end
    )
    return max(METRIC_MIN, min(METRIC_MAX, score))


if __name__ == "__main__":
    constraints = build_default_constraints()
    updated = update_constraints(constraints, social_pressure=0.4)
    score = compute_pressure_score(updated)
    print(
        f"default.resource_scarcity={constraints.resource_scarcity} "
        f"updated.social_pressure={updated.social_pressure} "
        f"pressure_score={score:.3f}"
    )
    print("OK — constraints demo complete")
