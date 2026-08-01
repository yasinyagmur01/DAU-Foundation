"""DAU Foundation public API.

Re-exports Layer-1 primitives and helpers. Graph runtime lives in graph.py
and is imported directly when needed.
"""

from .constraints import (
    build_default_constraints,
    compute_pressure_score,
    update_constraints,
)
from .delta import (
    DeltaClassification,
    classify_delta,
    compute_delta,
    is_trauma,
    should_persist,
)
from .state import (
    AffectedDomain,
    DAUAgentState,
    DeltaRecord,
    EnvironmentConstraints,
    Event,
    InternalState,
)
from .time_model import (
    EventClock,
    append_event,
    build_event,
    get_event_history,
)

__all__ = [
    "AffectedDomain",
    "DAUAgentState",
    "DeltaClassification",
    "DeltaRecord",
    "EnvironmentConstraints",
    "Event",
    "EventClock",
    "InternalState",
    "append_event",
    "build_default_constraints",
    "build_event",
    "classify_delta",
    "compute_delta",
    "compute_pressure_score",
    "get_event_history",
    "is_trauma",
    "should_persist",
    "update_constraints",
]


if __name__ == "__main__":
    print("DAU Foundation public API:")
    for name in __all__:
        print(f"  - {name}")
    print("OK — foundation package exports listed")
