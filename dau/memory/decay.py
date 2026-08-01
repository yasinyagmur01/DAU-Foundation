"""Ebbinghaus decay — retention as a function of event-counter distance.

Biology analogy: memories fade with unused time, but strength (how deeply
the imprint was laid) slows forgetting. Trauma resists erasure.
"""

from __future__ import annotations

from math import exp

from dau.foundation.delta import is_trauma
from dau.foundation.state import DeltaRecord

# ---------------------------------------------------------------------------
# Ebbinghaus parameters (event_counter distance, not wall-clock)
# ---------------------------------------------------------------------------

S_UNIT: float = 0.1
R_MIN: float = 0.05
TRAUMA_S_BASE: int = 10  # trauma imprints forget slowly


def compute_strength_init(record: DeltaRecord) -> int:
    """Map magnitude onto initial memory strength S.

    Biology analogy: stronger physiological swings carve deeper synaptic
    traces. Trauma gets a floor so the scar does not fade like ordinary noise.
    """

    strength = max(1, round(record.magnitude / S_UNIT))
    if is_trauma(record):
        strength = max(strength, TRAUMA_S_BASE)
    return int(strength)


def compute_retention(
    now_counter: int,
    last_activated: int,
    strength: int,
) -> float:
    """Ebbinghaus retention R = exp(-t / S) over event-counter distance.

    Biology analogy: unused engrams decay exponentially; higher strength
    stretches the half-life of the memory trace.
    """

    t = now_counter - last_activated
    if strength <= 0:
        return 0.0
    return float(exp(-t / strength))


def should_forget(retention: float, record: DeltaRecord) -> bool:
    """Decide whether a trace is weak enough to drop from long-term store.

    Biology analogy: ordinary faded memories are pruned in sleep; trauma
    scars are not erased by simple decay.
    """

    if is_trauma(record):
        return False
    return retention < R_MIN


if __name__ == "__main__":
    from dau.foundation.state import DeltaRecord

    snap = {
        "energy": 1.0,
        "resource_load": 0.0,
        "uncertainty_load": 0.0,
        "social_load": 0.0,
    }
    record = DeltaRecord(
        timestamp=1,
        magnitude=0.8,
        affected_domain="resource",
        snapshot_before=snap,
        snapshot_after=dict(snap),
    )
    s = compute_strength_init(record)
    r0 = compute_retention(now_counter=1, last_activated=1, strength=s)
    r_far = compute_retention(now_counter=1 + 1000, last_activated=1, strength=s)
    print(f"strength_init={s} R(t=0)={r0:.4f} R(t=1000)={r_far:.6f}")
    print(f"should_forget(far)={should_forget(r_far, record)}")
    print("OK — decay demo complete")
