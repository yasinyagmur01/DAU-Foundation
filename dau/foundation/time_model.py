"""Event-driven time — sequence counters, not wall clocks.

Biology analogy: lived time is counted in encounters with the world.
A heartbeat of experience advances the ordinal; chronometers do not.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any

from .state import DAUAgentState, Event

# ---------------------------------------------------------------------------
# Event ordinal origin
# ---------------------------------------------------------------------------

INITIAL_EVENT_COUNTER: int = 0


@dataclass
class EventClock:
    """Ordinal event counter — the organism's lived-time ticker.

    Biology analogy: not a circadian clock, but a count of discrete contacts
    with the world. Each tick is one event in the life sequence.
    """

    counter: int = INITIAL_EVENT_COUNTER

    def tick(self) -> int:
        """Advance the event counter and return the new timestamp.

        Biology analogy: one more lived encounter — the sequence index of
        what just happened becomes the timestamp of that event.
        """

        self.counter += 1
        return self.counter

    def reset(self) -> None:
        """Reset the counter to the initial ordinal.

        Biology analogy: a new life sequence begins; prior event counts
        do not carry into the next lineage run.
        """

        self.counter = INITIAL_EVENT_COUNTER


def build_event(
    clock: EventClock,
    event_type: str,
    payload: dict[str, Any] | None = None,
) -> Event:
    """Tick the clock and build an immutable Event with that timestamp.

    Biology analogy: when something happens in the world, time advances by
    one lived unit and the episode is sealed with that ordinal.
    """

    timestamp = clock.tick()
    return Event(
        event_type=event_type,
        payload=payload if payload is not None else {},
        timestamp=timestamp,
    )


def append_event(state: DAUAgentState, event: Event) -> DAUAgentState:
    """Return a new agent state with the event appended; leave original intact.

    Biology analogy: memory is append-only — adding an episode does not rewrite
    the prior life. This function deep-copies so callers keep immutability.
    """

    new_state = deepcopy(state)
    new_state.event_log = list(new_state.event_log) + [event]
    return new_state


def get_event_history(state: DAUAgentState, event_type: str) -> list[Event]:
    """Filter the event log to a single semantic class.

    Biology analogy: recall only episodes of one kind — e.g. only foraging
    contacts, only social contacts — from the ordered life history.
    """

    return [event for event in state.event_log if event.event_type == event_type]


if __name__ == "__main__":
    from .constraints import build_default_constraints

    clock = EventClock()
    state = DAUAgentState(
        agent_id="demo-time-0",
        environment=build_default_constraints(),
    )
    event = build_event(clock, "forage", {"item": "seed"})
    new_state = append_event(state, event)
    history = get_event_history(new_state, "forage")
    print(
        f"original_events={len(state.event_log)} "
        f"new_events={len(new_state.event_log)} "
        f"timestamp={event.timestamp} "
        f"history={len(history)}"
    )
    print("OK — time_model demo complete")
