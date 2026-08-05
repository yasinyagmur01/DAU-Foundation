"""Delta measurement — how much an event moved internal homeostasis.

Biology analogy: a physiological delta is the body's local measure of lived
time. Large swings leave deep imprints; tiny ones leave no lasting trace.
"""

from __future__ import annotations

from enum import StrEnum

from .constraints import CROSS_AXIS_SPILLOVER, MAGNITUDE_PEAK_WEIGHT
from .state import (
    METRIC_MAX,
    METRIC_MIN,
    AffectedDomain,
    DeltaRecord,
    InternalState,
)

# ---------------------------------------------------------------------------
# Magnitude thresholds for imprint depth (no magic numbers in logic)
# ---------------------------------------------------------------------------

DELTA_THRESHOLD_NOISE: float = 0.1  # below: no lasting trace
DELTA_THRESHOLD_NORMAL: float = 0.4  # below: short-term memory territory
DELTA_THRESHOLD_DEEP: float = 0.7  # below: persist flag; at/above: trauma / drift

# Map AffectedDomain labels onto InternalState attribute names.
DOMAIN_ATTR: dict[str, str] = {
    "energy": "energy",
    "resource": "resource_load",
    "social": "social_load",
    "uncertainty": "uncertainty_load",
}


class DeltaClassification(StrEnum):
    """Depth of imprint left by a state change.

    Biology analogy: sensory noise vs. salient memory vs. deep consolidation
    vs. traumatic override — ranked by how far homeostasis moved.
    """

    NO_TRACE = "NO_TRACE"
    NORMAL = "NORMAL"
    DEEP = "DEEP"
    TRAUMA = "TRAUMA"


def _internal_snapshot(state: InternalState) -> dict[str, float]:
    """Copy InternalState scalar loads into a flat float dict.

    Biology analogy: a lab panel snapshot — only the measurable vitals,
    taken at one moment for before/after comparison.
    """

    return {
        "energy": float(state.energy),
        "resource_load": float(state.resource_load),
        "uncertainty_load": float(state.uncertainty_load),
        "social_load": float(state.social_load),
    }


def compute_delta(
    before: InternalState,
    after: InternalState,
    affected_domain: str | None = None,
    timestamp: int | None = None,
    raw_pe: float | None = None,
) -> DeltaRecord:
    """Measure imprint magnitude and freeze before/after snapshots.

    Biology analogy: compare the full vital panel before and after a stimulus.
    When raw_pe is given, magnitude is peak-weighted surprise (independent of
    DAERM recovery). Otherwise magnitude is mean absolute axis swing (legacy).
    affected_domain only tags which axis triggered the event.
    """

    if raw_pe is not None:
        # Peak-weighted: DAERM recovery'den bağımsız şiddet ölçümü
        # Uniform spillover varsayımı (CROSS_AXIS_SPILLOVER=0.20)
        pe_primary = raw_pe
        pe_secondary = raw_pe * CROSS_AXIS_SPILLOVER
        pe_vec = [pe_primary, pe_secondary, pe_secondary, pe_secondary]
        peak = max(pe_vec)
        mean_pe = sum(pe_vec) / len(pe_vec)
        magnitude = (
            MAGNITUDE_PEAK_WEIGHT * peak
            + (1.0 - MAGNITUDE_PEAK_WEIGHT) * mean_pe
        )
    else:
        # Geriye dönük uyumluluk — raw_pe verilmezse eski hesap
        axes = ["energy", "resource_load", "social_load", "uncertainty_load"]
        deltas = [abs(getattr(after, a) - getattr(before, a)) for a in axes]
        magnitude = sum(deltas) / len(deltas)
    magnitude = max(METRIC_MIN, min(METRIC_MAX, magnitude))
    resolved_domain: AffectedDomain = (
        "resource" if affected_domain is None else affected_domain  # type: ignore[assignment]
    )
    resolved_timestamp = 0 if timestamp is None else int(timestamp)
    return DeltaRecord(
        timestamp=resolved_timestamp,
        magnitude=magnitude,
        affected_domain=resolved_domain,
        snapshot_before=_internal_snapshot(before),
        snapshot_after=_internal_snapshot(after),
    )


def classify_delta(record: DeltaRecord) -> DeltaClassification:
    """Classify imprint depth from magnitude alone.

    Biology analogy: the nervous system tags change intensity — noise,
    ordinary memory, deep consolidation, or trauma — by how far the body moved.
    """

    magnitude = record.magnitude
    if magnitude < DELTA_THRESHOLD_NOISE:
        return DeltaClassification.NO_TRACE
    if magnitude < DELTA_THRESHOLD_NORMAL:
        return DeltaClassification.NORMAL
    if magnitude < DELTA_THRESHOLD_DEEP:
        return DeltaClassification.DEEP
    return DeltaClassification.TRAUMA


def should_persist(record: DeltaRecord) -> bool:
    """Return True when the imprint is deep enough to persist.

    Biology analogy: only strong physiological swings are written into
    long-term consolidation; shallow ripples fade.
    """

    classification = classify_delta(record)
    return classification in (
        DeltaClassification.DEEP,
        DeltaClassification.TRAUMA,
    )


def is_trauma(record: DeltaRecord) -> bool:
    """Return True only for trauma-class deltas.

    Biology analogy: trauma is an extreme overrun of homeostasis — not every
    deep memory, only the magnitude that crosses the trauma threshold.
    """

    return classify_delta(record) == DeltaClassification.TRAUMA


if __name__ == "__main__":
    before = InternalState(energy=1.0, resource_load=0.0)
    after = InternalState(energy=1.0, resource_load=0.55)
    record = compute_delta(before, after, "resource", timestamp=1)
    classification = classify_delta(record)
    print(
        f"magnitude={record.magnitude:.2f} "
        f"class={classification} "
        f"persist={should_persist(record)} "
        f"trauma={is_trauma(record)}"
    )
    print("OK — delta demo complete")
