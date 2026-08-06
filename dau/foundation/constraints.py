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

# Per-agent QLoRA (Punica pattern) — independent adapters, shared frozen base
PER_AGENT_LORA_RANK: int = 8
PER_AGENT_LORA_ALPHA: int = 16
ADAPTER_BASE_DIR: str = "dau_runs/adapters"
ADAPTER_SWITCH_MAX_MS: int = 1


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
