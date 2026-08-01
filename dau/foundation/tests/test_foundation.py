"""Pytest suite for DAU Foundation Layer-1 helpers.

Biology analogy: verify the measurement instruments — delta thresholds,
constraint snapshots, and event-time plumbing — before any organism lives.
"""

from __future__ import annotations

import pytest

from dau.foundation.constraints import (
    DEFAULT_GENERATION_END,
    DEFAULT_RESOURCE_SCARCITY,
    DEFAULT_SOCIAL_PRESSURE,
    DEFAULT_TIME_PRESSURE,
    DEFAULT_UNCERTAINTY,
    build_default_constraints,
    compute_pressure_score,
    update_constraints,
)
from dau.foundation.delta import (
    DELTA_THRESHOLD_DEEP,
    DELTA_THRESHOLD_NOISE,
    DELTA_THRESHOLD_NORMAL,
    DeltaClassification,
    classify_delta,
    compute_delta,
    is_trauma,
    should_persist,
)
from dau.foundation.graph import dominant_load_domain
from dau.foundation.memory_bridge import (
    consolidate_run,
    record_delta,
    retrieve_relevant,
)
from dau.foundation.state import DAUAgentState, DeltaRecord, InternalState
from dau.foundation.time_model import (
    EventClock,
    append_event,
    build_event,
)
from dau.memory import MemoryStore


def _record_with_magnitude(magnitude: float) -> DeltaRecord:
    """Build a minimal DeltaRecord for threshold tests."""

    return DeltaRecord(
        timestamp=1,
        magnitude=magnitude,
        affected_domain="energy",
        snapshot_before={"energy": 1.0, "resource_load": 0.0,
                         "uncertainty_load": 0.0, "social_load": 0.0},
        snapshot_after={"energy": 1.0 - magnitude, "resource_load": 0.0,
                        "uncertainty_load": 0.0, "social_load": 0.0},
    )


def test_compute_delta_magnitude() -> None:
    """Magnitude equals mean absolute change across all homeostatic axes."""

    before = InternalState(resource_load=0.1)
    after = InternalState(resource_load=0.6)
    record = compute_delta(before, after, "resource", timestamp=3)
    # Only resource moved by 0.5 → mean over 4 axes is 0.125.
    assert record.magnitude == pytest.approx(0.125)
    assert record.timestamp == 3
    assert record.affected_domain == "resource"
    assert record.snapshot_before["resource_load"] == pytest.approx(0.1)
    assert record.snapshot_after["resource_load"] == pytest.approx(0.6)


@pytest.mark.parametrize(
    ("magnitude", "expected"),
    [
        (0.09, DeltaClassification.NO_TRACE),
        (0.1, DeltaClassification.NORMAL),
        (0.39, DeltaClassification.NORMAL),
        (0.4, DeltaClassification.DEEP),
        (0.69, DeltaClassification.DEEP),
        (0.7, DeltaClassification.TRAUMA),
        (0.71, DeltaClassification.TRAUMA),
    ],
)
def test_classify_delta_thresholds(
    magnitude: float,
    expected: DeltaClassification,
) -> None:
    """Boundary magnitudes map to the specified imprint classes."""

    assert classify_delta(_record_with_magnitude(magnitude)) == expected
    assert DELTA_THRESHOLD_NOISE == 0.1
    assert DELTA_THRESHOLD_NORMAL == 0.4
    assert DELTA_THRESHOLD_DEEP == 0.7


@pytest.mark.parametrize(
    ("magnitude", "expected"),
    [
        (0.09, False),
        (0.1, False),
        (0.39, False),
        (0.4, True),
        (0.69, True),
        (0.7, True),
        (0.71, True),
    ],
)
def test_should_persist(magnitude: float, expected: bool) -> None:
    """DEEP and TRAUMA persist; NO_TRACE and NORMAL do not."""

    assert should_persist(_record_with_magnitude(magnitude)) is expected


@pytest.mark.parametrize(
    ("magnitude", "expected"),
    [
        (0.09, False),
        (0.1, False),
        (0.39, False),
        (0.4, False),
        (0.69, False),
        (0.7, True),
        (0.71, True),
    ],
)
def test_is_trauma(magnitude: float, expected: bool) -> None:
    """Only TRAUMA-class magnitudes return True."""

    assert is_trauma(_record_with_magnitude(magnitude)) is expected


def test_build_default_constraints_match_constants() -> None:
    """Default snapshot fields equal the module constants."""

    constraints = build_default_constraints()
    assert constraints.time_pressure == DEFAULT_TIME_PRESSURE
    assert constraints.resource_scarcity == DEFAULT_RESOURCE_SCARCITY
    assert constraints.social_pressure == DEFAULT_SOCIAL_PRESSURE
    assert constraints.uncertainty == DEFAULT_UNCERTAINTY
    assert constraints.generation_end == DEFAULT_GENERATION_END


def test_update_constraints_only_changes_given_fields() -> None:
    """update_constraints mutates only the provided kwargs."""

    current = build_default_constraints()
    updated = update_constraints(current, social_pressure=0.8)
    assert updated.social_pressure == pytest.approx(0.8)
    assert updated.time_pressure == current.time_pressure
    assert updated.resource_scarcity == current.resource_scarcity
    assert updated.uncertainty == current.uncertainty
    assert updated.generation_end == current.generation_end
    assert current.social_pressure == DEFAULT_SOCIAL_PRESSURE


def test_compute_pressure_score_in_unit_interval() -> None:
    """Pressure score stays inside [0.0, 1.0]."""

    score = compute_pressure_score(build_default_constraints())
    assert 0.0 <= score <= 1.0
    high = update_constraints(
        build_default_constraints(),
        time_pressure=1.0,
        resource_scarcity=1.0,
        social_pressure=1.0,
        uncertainty=1.0,
        generation_end=1.0,
    )
    assert compute_pressure_score(high) == pytest.approx(1.0)


def test_event_clock_tick_increments_by_one() -> None:
    """Each tick advances the ordinal counter by exactly one."""

    clock = EventClock()
    assert clock.tick() == 1
    assert clock.tick() == 2
    assert clock.tick() == 3
    assert clock.counter == 3


def test_build_event_timestamp_from_clock() -> None:
    """Event timestamps come from EventClock.tick()."""

    clock = EventClock()
    first = build_event(clock, "a", {})
    second = build_event(clock, "b", {"x": 1})
    assert first.timestamp == 1
    assert second.timestamp == 2
    assert first.event_type == "a"
    assert second.payload == {"x": 1}


def test_append_event_preserves_original_state() -> None:
    """append_event returns a new state; the original event_log is untouched."""

    state = DAUAgentState(
        agent_id="test-agent",
        environment=build_default_constraints(),
    )
    clock = EventClock()
    event = build_event(clock, "contact", {"n": 1})
    new_state = append_event(state, event)
    assert len(state.event_log) == 0
    assert len(new_state.event_log) == 1
    assert new_state.event_log[0].event_id == event.event_id
    assert state is not new_state


def test_dominant_load_domain_resource_highest() -> None:
    """When resource_load is highest, dominant_load_domain returns resource."""

    state = DAUAgentState(
        agent_id="load-agent",
        environment=build_default_constraints(),
        internal_state=InternalState(
            energy=0.5,
            resource_load=0.8,
            social_load=0.2,
            uncertainty_load=0.1,
        ),
    )
    assert dominant_load_domain(state) == "resource"


def test_record_delta_trauma_persists_no_trace_skips(tmp_path) -> None:
    """TRAUMA writes to disk; NO_TRACE does not."""

    store = MemoryStore(
        chroma_path=str(tmp_path / "chroma"),
        sqlite_path=str(tmp_path / "memory.db"),
    )
    try:
        trauma = _record_with_magnitude(0.85)
        trauma = trauma.model_copy(update={"affected_domain": "resource"})
        no_trace = _record_with_magnitude(0.05)
        trauma_decision = record_delta(trauma, "bridge-agent", store)
        no_trace_decision = record_delta(no_trace, "bridge-agent", store)
        assert trauma_decision is not None
        assert trauma_decision["persist"] is True
        assert no_trace_decision is not None
        assert no_trace_decision["persist"] is False
        assert len(store.list_nodes("bridge-agent")) == 1
    finally:
        store.close()


def test_retrieve_relevant_empty_store_safe(tmp_path) -> None:
    """retrieve_relevant returns [] on an empty store without raising."""

    store = MemoryStore(
        chroma_path=str(tmp_path / "chroma"),
        sqlite_path=str(tmp_path / "memory.db"),
    )
    try:
        results = retrieve_relevant(
            query_domain="resource",
            agent_id="empty-agent",
            now_counter=0,
            store=store,
        )
        assert results == []
    finally:
        store.close()


def test_consolidate_run_returns_report(tmp_path) -> None:
    """consolidate_run returns a ConsolidationReport with expected fields."""

    store = MemoryStore(
        chroma_path=str(tmp_path / "chroma"),
        sqlite_path=str(tmp_path / "memory.db"),
    )
    try:
        trauma = _record_with_magnitude(0.85).model_copy(
            update={"affected_domain": "resource", "timestamp": 1}
        )
        record_delta(trauma, "sleep-agent", store)
        report = consolidate_run("sleep-agent", now_counter=1, store=store)
        assert report.agent_id == "sleep-agent"
        assert report.timestamp == 1
        assert report.deleted_count >= 0
        assert report.strengthened_count >= 1
        assert report.edges_created >= 0
        assert report.drift_flag_count >= 1
    finally:
        store.close()


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
