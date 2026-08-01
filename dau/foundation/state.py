"""DAU Foundation — agent state primitives.

Core axiom: you cannot inject a trait into an agent.
You can only give it life. Traits emerge from lived experience.

All metrics are deterministic Python floats in [METRIC_MIN, METRIC_MAX].
Time is event-driven (ordinal timestamps), never clock-driven.
"""

from __future__ import annotations

from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator

# ---------------------------------------------------------------------------
# Tunable bounds / homeostatic setpoints (no magic numbers in fields)
# ---------------------------------------------------------------------------

METRIC_MIN: float = 0.0
METRIC_MAX: float = 1.0

DEFAULT_ENERGY: float = 1.0
DEFAULT_RESOURCE_LOAD: float = 0.0
DEFAULT_UNCERTAINTY_LOAD: float = 0.0
DEFAULT_SOCIAL_LOAD: float = 0.0
DEFAULT_GENERATION: int = 0
DEFAULT_EVENT_TIMESTAMP: int = 0

AffectedDomain = Literal["energy", "resource", "social", "uncertainty"]


class EnvironmentConstraints(BaseModel):
    """Read-only universe parameters — the five universal pressures of lived experience.

    Biology analogy: the external world an organism is born into cannot be
    rewritten by the organism itself. Gravity, seasons, and scarcity are given.
    These constraints shape evolution; they are not traits of the agent.
    """

    model_config = ConfigDict(frozen=True)

    # Temporal finitude: every organism faces urgency because time ends.
    # Maps to mortality awareness, circadian pressure, and generation deadlines.
    time_pressure: float = Field(
        ...,
        ge=METRIC_MIN,
        le=METRIC_MAX,
        description=(
            "Biology: temporal finitude — everything has an end. "
            "Urgency from mortality, circadian cycles, and generation deadlines."
        ),
    )

    # Metabolic scarcity: energy and matter are finite; hunger drives selection.
    # Maps to CPR-style resource pressure without assigning a cooperation trait.
    resource_scarcity: float = Field(
        ...,
        ge=METRIC_MIN,
        le=METRIC_MAX,
        description=(
            "Biology: metabolic scarcity — matter and energy are finite. "
            "Hunger and resource competition create selective pressure."
        ),
    )

    # Conspecific presence: others occupy the niche; belonging and conflict ensue.
    # Maps to hierarchy, attachment, rejection — social load, not a personality score.
    social_pressure: float = Field(
        ...,
        ge=METRIC_MIN,
        le=METRIC_MAX,
        description=(
            "Biology: conspecific presence — others share the niche. "
            "Belonging, competition, and conflict arise from cohabitation."
        ),
    )

    # Incomplete information: the nervous system must act without full prediction.
    # Maps to ambiguity stress and exploratory drive under unknown futures.
    uncertainty: float = Field(
        ...,
        ge=METRIC_MIN,
        le=METRIC_MAX,
        description=(
            "Biology: incomplete information — the organism must act without "
            "full prediction. Ambiguity stress forces provisional decisions."
        ),
    )

    # Senescence / generational boundary: death closes one life and opens inheritance.
    # Maps to consolidation triggers and transfer of what survived pressure.
    generation_end: float = Field(
        ...,
        ge=METRIC_MIN,
        le=METRIC_MAX,
        description=(
            "Biology: senescence and generational boundary — death ends one life "
            "and opens inheritance. Triggers consolidation of what survived."
        ),
    )


class InternalState(BaseModel):
    """Mutable homeostatic baseline — the organism's present physiological loads.

    Biology analogy: Claude Bernard / homeostasis. At first breath the body
    starts near a setpoint (full energy, empty loads). Experience moves these
    dials; nothing here is a named personality trait.
    """

    model_config = ConfigDict(frozen=False)

    energy: float = Field(
        default=DEFAULT_ENERGY,
        ge=METRIC_MIN,
        le=METRIC_MAX,
        description="Vital metabolic reserve — full at first breath.",
    )
    resource_load: float = Field(
        default=DEFAULT_RESOURCE_LOAD,
        ge=METRIC_MIN,
        le=METRIC_MAX,
        description="Accumulated scarcity burden on the organism.",
    )
    uncertainty_load: float = Field(
        default=DEFAULT_UNCERTAINTY_LOAD,
        ge=METRIC_MIN,
        le=METRIC_MAX,
        description="Cognitive burden from unresolved ambiguity.",
    )
    social_load: float = Field(
        default=DEFAULT_SOCIAL_LOAD,
        ge=METRIC_MIN,
        le=METRIC_MAX,
        description="Burden from conspecific demand, conflict, or isolation.",
    )
    # Damasio somatic marker hypothesis — empty at birth; Layer 2 fills from experience.
    somatic_markers: dict[str, float] = Field(
        default_factory=dict,
        description=(
            "Damasio somatic markers: felt tags linking situations to bodily "
            "outcome signals. Empty at birth; filled by lived experience (Layer 2)."
        ),
    )

    @field_validator("somatic_markers")
    @classmethod
    def _somatic_markers_in_unit_interval(
        cls, value: dict[str, float]
    ) -> dict[str, float]:
        for marker_key, marker_value in value.items():
            if not (METRIC_MIN <= marker_value <= METRIC_MAX):
                raise ValueError(
                    f"somatic_markers[{marker_key!r}]={marker_value} "
                    f"outside [{METRIC_MIN}, {METRIC_MAX}]"
                )
        return value


class DeltaRecord(BaseModel):
    """Immutable trace of how an event moved internal state.

    Biology analogy: a physiological delta — how much the body changed, in
    which domain, and what the before/after snapshots were. Magnitude is the
    local measure of lived time (large delta → deep imprint).
    """

    model_config = ConfigDict(frozen=True)

    timestamp: int = Field(
        ...,
        description="Event ordinal (sequence index), not wall-clock time.",
    )
    magnitude: float = Field(
        ...,
        ge=METRIC_MIN,
        le=METRIC_MAX,
        description="How much internal state moved — the local weight of lived time.",
    )
    affected_domain: AffectedDomain = Field(
        ...,
        description="Which homeostatic domain absorbed the change.",
    )
    snapshot_before: dict[str, float] = Field(
        ...,
        description="InternalState field copy immediately before the delta.",
    )
    snapshot_after: dict[str, float] = Field(
        ...,
        description="InternalState field copy immediately after the delta.",
    )


class Event(BaseModel):
    """Immutable discrete lived experience — one unit of world contact.

    Biology analogy: a sensory/episodic event. It happens once in sequence;
    the organism cannot rewrite what occurred, only how it is later consolidated.
    """

    model_config = ConfigDict(frozen=True)

    event_id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Unique identity of this lived event (UUID string).",
    )
    event_type: str = Field(
        ...,
        description="Semantic class of the experience (not a trait label).",
    )
    payload: dict[str, Any] = Field(
        default_factory=dict,
        description="Structured facts of what occurred in the world.",
    )
    timestamp: int = Field(
        default=DEFAULT_EVENT_TIMESTAMP,
        description="Event ordinal in the agent's lived sequence.",
    )


class DAUAgentState(BaseModel):
    """Mutable whole-organism state — life given, traits not injected.

    Biology analogy: the living agent as a system: identity, generation
    (lineage age), the external pressures it faces, its current homeostasis,
    and the immutable logs of what it lived and how it changed.
    """

    model_config = ConfigDict(frozen=False)

    agent_id: str = Field(..., description="Stable identity of this organism.")
    generation: int = Field(
        default=DEFAULT_GENERATION,
        description="Lineage age — how many consolidations this line has survived.",
    )
    environment: EnvironmentConstraints = Field(
        ...,
        description="Read-only universe pressures shaping this life.",
    )
    internal_state: InternalState = Field(
        default_factory=InternalState,
        description="Mutable homeostatic baseline — first breath defaults.",
    )
    event_log: list[Event] = Field(
        default_factory=list,
        description="Ordered record of lived events (append-only history).",
    )
    delta_log: list[DeltaRecord] = Field(
        default_factory=list,
        description="Ordered record of internal-state deltas (append-only history).",
    )


if __name__ == "__main__":
    default_environment = EnvironmentConstraints(
        time_pressure=METRIC_MIN,
        resource_scarcity=METRIC_MIN,
        social_pressure=METRIC_MIN,
        uncertainty=METRIC_MIN,
        generation_end=METRIC_MIN,
    )
    state = DAUAgentState(
        agent_id="demo-agent-0",
        environment=default_environment,
    )
    print(state.model_dump_json(indent=2))
    print(
        "OK — DAUAgentState constructed; "
        f"energy={state.internal_state.energy}, "
        f"generation={state.generation}, "
        f"events={len(state.event_log)}, "
        f"deltas={len(state.delta_log)}"
    )
