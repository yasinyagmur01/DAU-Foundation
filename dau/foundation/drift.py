"""Drift detection — permanent domain shift after trauma-class deltas.

Biology analogy: extreme homeostatic overrun does not just leave a memory; it
shifts the decision surface in the affected domain. Drift accumulates and does
not decay here — Layer 3 healing is the only path back.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .delta import is_trauma
from .state import DeltaRecord

# ---------------------------------------------------------------------------
# Drift defaults / healing (no magic numbers in logic)
# ---------------------------------------------------------------------------

DRIFT_BIAS_ABSENT: float = 0.0
MAGNITUDE_ACCUMULATOR_INIT: float = 0.0
FLAG_SET_ON_TRAUMA: bool = True
HEAL_THRESHOLD: float = 0.6  # strong positive experience required to heal
HEAL_RATE: float = 0.3  # slow: ~3+ strong experiences to clear one trauma
HEALED_MAGNITUDE: float = 0.0


@dataclass
class DriftState:
    """Permanent per-domain drift flags and accumulated trauma magnitudes.

    Biology analogy: scar tissue on the decision map — which niches were
    traumatically overwritten, and how hard. Keys are AffectedDomain strings.
    """

    flags: dict[str, bool] = field(default_factory=dict)
    magnitudes: dict[str, float] = field(default_factory=dict)


def update_drift(drift_state: DriftState, delta: DeltaRecord) -> DriftState:
    """Apply trauma-driven drift; non-trauma leaves DriftState unchanged.

    Biology analogy: only traumatic swings rewrite the decision domain. Ordinary
    and deep imprints leave memory without shifting the function surface.
    Drift is permanent until Layer 3 healing.
    """

    if not is_trauma(delta):
        return drift_state

    domain = str(delta.affected_domain)
    new_flags = dict(drift_state.flags)
    new_magnitudes = dict(drift_state.magnitudes)
    new_flags[domain] = FLAG_SET_ON_TRAUMA
    new_magnitudes[domain] = (
        new_magnitudes.get(domain, MAGNITUDE_ACCUMULATOR_INIT) + float(delta.magnitude)
    )
    return DriftState(flags=new_flags, magnitudes=new_magnitudes)


def heal_drift(drift_state: DriftState, delta: DeltaRecord) -> DriftState:
    """Slowly reduce trauma drift when a strong non-trauma experience lands.

    Biology analogy: scar tissue does not fade on its own — only repeated
    strong positive experience in the same niche can overwrite it, and even
    then healing is partial. More trauma never heals trauma.
    """

    domain = str(delta.affected_domain)
    if not drift_state.flags.get(domain):
        return drift_state
    if float(delta.magnitude) < HEAL_THRESHOLD:
        return drift_state
    if is_trauma(delta):
        return drift_state

    new_flags = dict(drift_state.flags)
    new_magnitudes = dict(drift_state.magnitudes)
    reduced = max(
        HEALED_MAGNITUDE,
        float(new_magnitudes.get(domain, MAGNITUDE_ACCUMULATOR_INIT))
        - float(delta.magnitude) * HEAL_RATE,
    )
    new_magnitudes[domain] = reduced
    if reduced == HEALED_MAGNITUDE:
        new_flags[domain] = False
    return DriftState(flags=new_flags, magnitudes=new_magnitudes)


def get_drift_bias(drift_state: DriftState, domain: str) -> float:
    """Return accumulated drift magnitude for a flagged domain, else 0.0.

    Biology analogy: how strongly a scarred niche still pulls decisions —
    zero when that domain was never traumatically rewritten.
    """

    if drift_state.flags.get(domain):
        return float(drift_state.magnitudes[domain])
    return DRIFT_BIAS_ABSENT


if __name__ == "__main__":
    empty = DriftState()
    trauma = DeltaRecord(
        timestamp=1,
        magnitude=0.8,
        affected_domain="resource",
        snapshot_before={
            "energy": 1.0,
            "resource_load": 0.0,
            "uncertainty_load": 0.0,
            "social_load": 0.0,
        },
        snapshot_after={
            "energy": 0.2,
            "resource_load": 0.8,
            "uncertainty_load": 0.0,
            "social_load": 0.0,
        },
    )
    drifted = update_drift(empty, trauma)
    print(f"flags={drifted.flags}")
    print(f"magnitudes={drifted.magnitudes}")
    print(f"bias_resource={get_drift_bias(drifted, 'resource')}")
    print(f"bias_social={get_drift_bias(drifted, 'social')}")
    print("OK — drift demo complete")
