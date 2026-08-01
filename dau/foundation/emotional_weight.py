"""Emotional weight — somatic markers as priority modifiers, not labels.

Biology analogy: Damasio's somatic marker hypothesis. Felt bodily signals bias
decision priority. Emotion is a weight vector over the decision surface, not a
JSON tag like "anxious" that leaves behavior unchanged (Dubedy 2025).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .delta import is_trauma
from .state import METRIC_MAX, METRIC_MIN, DeltaRecord, InternalState

# ---------------------------------------------------------------------------
# Marker keys and prompt injection (no magic strings in logic)
# ---------------------------------------------------------------------------

MARKER_THREAT: str = "threat"
MARKER_REWARD: str = "reward"
MARKER_NOVELTY: str = "novelty"
MARKER_SOCIAL: str = "social"
MARKER_LOSS: str = "loss"

# Fixed order for deterministic tie-breaks when selecting the top marker.
MARKER_ORDER: tuple[str, ...] = (
    MARKER_THREAT,
    MARKER_REWARD,
    MARKER_NOVELTY,
    MARKER_SOCIAL,
    MARKER_LOSS,
)

LOSS_ON_TRAUMA: float = 1.0
LOSS_DEFAULT: float = 0.0

PRIORITY_PROMPT_TEMPLATE: str = "You are currently prioritizing: {top_marker}"


@dataclass
class EmotionalWeight:
    """Weight vector over somatic markers that bias decision priority.

    Biology analogy: a momentary bodily readout — threat, reward, novelty,
    social load, and loss — each in [0, 1]. Highest marker sets behavioral bias.
    """

    somatic_markers: dict[str, float] = field(default_factory=dict)


def _clamp(value: float) -> float:
    """Keep a marker weight inside the unit interval."""

    return max(METRIC_MIN, min(METRIC_MAX, value))


def compute_emotional_weight(
    delta: DeltaRecord,
    internal_state: InternalState,
) -> EmotionalWeight:
    """Derive somatic marker weights from delta magnitude and homeostatic axes.

    Biology analogy: the nervous system converts how hard the body was hit and
    what loads were already high into felt priorities — threat under scarcity,
    reward when energy remains and the swing was small, novelty under ambiguity,
    social pressure as itself, and loss only when the swing is traumatic.
    """

    resource_load_weight = float(internal_state.resource_load)
    energy_weight = float(internal_state.energy)
    uncertainty_load_weight = float(internal_state.uncertainty_load)
    social_load_weight = float(internal_state.social_load)
    magnitude = float(delta.magnitude)

    threat = _clamp(magnitude * resource_load_weight)
    reward = _clamp((1.0 - magnitude) * energy_weight)
    novelty = _clamp(magnitude * uncertainty_load_weight)
    social = _clamp(social_load_weight)
    loss = LOSS_ON_TRAUMA if is_trauma(delta) else LOSS_DEFAULT

    return EmotionalWeight(
        somatic_markers={
            MARKER_THREAT: threat,
            MARKER_REWARD: reward,
            MARKER_NOVELTY: novelty,
            MARKER_SOCIAL: social,
            MARKER_LOSS: loss,
        }
    )


def _top_marker(somatic_markers: dict[str, float]) -> str:
    """Return the highest-weighted marker; ties break by MARKER_ORDER."""

    best_marker = MARKER_ORDER[0]
    best_weight = float(somatic_markers.get(best_marker, METRIC_MIN))
    for marker in MARKER_ORDER[1:]:
        weight = float(somatic_markers.get(marker, METRIC_MIN))
        if weight > best_weight:
            best_marker = marker
            best_weight = weight
    return best_marker


def apply_emotional_weight(prompt: str, ew: EmotionalWeight) -> str:
    """Inject the top somatic marker as a one-line behavioral bias into the prompt.

    Biology analogy: only the loudest bodily signal reaches awareness as a
    priority cue — not a trait label, just which pressure currently dominates.
    """

    top_marker = _top_marker(ew.somatic_markers)
    bias_line = PRIORITY_PROMPT_TEMPLATE.format(top_marker=top_marker)
    if not prompt:
        return bias_line
    return f"{prompt}\n{bias_line}"


if __name__ == "__main__":
    demo_delta = DeltaRecord(
        timestamp=1,
        magnitude=0.5,
        affected_domain="resource",
        snapshot_before={
            "energy": 1.0,
            "resource_load": 0.0,
            "uncertainty_load": 0.0,
            "social_load": 0.0,
        },
        snapshot_after={
            "energy": 0.5,
            "resource_load": 0.5,
            "uncertainty_load": 0.0,
            "social_load": 0.0,
        },
    )
    demo_state = InternalState(
        energy=0.8,
        resource_load=0.6,
        uncertainty_load=0.4,
        social_load=0.2,
    )
    weight = compute_emotional_weight(demo_delta, demo_state)
    biased = apply_emotional_weight("Decide.", weight)
    print(f"markers={weight.somatic_markers}")
    print(f"biased_prompt={biased!r}")
    print("OK — emotional_weight demo complete")
