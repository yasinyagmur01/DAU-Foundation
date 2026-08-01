"""End-to-end foundation demo without the LangGraph runtime.

Biology analogy: a short life sequence under default pressures — events land,
energy falls, deltas are classified. Graph execution belongs to graph.py.
"""

from __future__ import annotations

from .constraints import build_default_constraints
from .delta import DeltaClassification, classify_delta, compute_delta
from .state import DAUAgentState, InternalState, METRIC_MAX, METRIC_MIN
from .time_model import EventClock, append_event, build_event

DEMO_EVENT_COUNT: int = 5
DEMO_ENERGY_DROP: float = 0.12
DEMO_RESOURCE_STEP: float = 0.15


def run_demo() -> None:
    """Run a five-event manual life loop and print delta classifications.

    Biology analogy: five discrete contacts with the world, each shifting
    homeostasis a bit further, then a census of imprint depths.
    """

    environment = build_default_constraints()
    state = DAUAgentState(
        agent_id="demo-foundation-0",
        environment=environment,
    )
    clock = EventClock()

    print("=== DAU Foundation demo ===")
    print(f"agent_id={state.agent_id}")
    print(f"constraints={environment.model_dump()}")
    print()

    for step in range(1, DEMO_EVENT_COUNT + 1):
        event = build_event(
            clock,
            event_type="demo_contact",
            payload={"step": step, "kind": "resource" if step % 2 else "social"},
        )
        state = append_event(state, event)

        before = state.internal_state.model_copy(deep=True)
        new_energy = max(METRIC_MIN, before.energy - DEMO_ENERGY_DROP)
        new_resource = min(
            METRIC_MAX,
            before.resource_load + (DEMO_RESOURCE_STEP if step % 2 else 0.0),
        )
        new_social = min(
            METRIC_MAX,
            before.social_load + (0.0 if step % 2 else DEMO_RESOURCE_STEP),
        )
        after = InternalState(
            energy=new_energy,
            resource_load=new_resource,
            social_load=new_social,
            uncertainty_load=before.uncertainty_load,
            somatic_markers=dict(before.somatic_markers),
        )
        affected = "resource" if step % 2 else "social"
        record = compute_delta(before, after, affected, timestamp=event.timestamp)
        classification = classify_delta(record)
        state.internal_state = after
        state.delta_log = list(state.delta_log) + [record]

        print(
            f"event={event.timestamp} domain={affected} "
            f"magnitude={record.magnitude:.3f} class={classification.value}"
        )

    counts = {label: 0 for label in DeltaClassification}
    for record in state.delta_log:
        counts[classify_delta(record)] += 1

    print()
    print("=== delta_log summary ===")
    for label in DeltaClassification:
        print(f"{label.value}: {counts[label]}")
    print(f"events={len(state.event_log)} energy={state.internal_state.energy:.3f}")
    print("OK — run_demo complete")


if __name__ == "__main__":
    run_demo()
