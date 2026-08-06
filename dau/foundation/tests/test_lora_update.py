"""Unit tests for generation-end lived-trace LoRA update (flag-gated)."""

from __future__ import annotations

from pathlib import Path

import pytest

from dau.foundation.constraints import build_default_constraints
from dau.foundation.delta import compute_delta
from dau.foundation.drift import DriftState, update_drift
from dau.foundation.lora_update import (
    LORA_ENABLED_ENV,
    build_lived_trace_examples,
    compute_loss_weight,
    is_lora_enabled,
    lora_update,
    maybe_lora_update_after_life,
)
from dau.foundation.state import DAUAgentState, InternalState
from dau.foundation.time_model import EventClock, append_event, build_event


def _agent_with_traces() -> DAUAgentState:
    state = DAUAgentState(
        agent_id="lora-test-agent",
        environment=build_default_constraints(),
        internal_state=InternalState(),
        drift_state=DriftState(),
    )
    clock = EventClock()
    event = build_event(
        clock,
        "agent_decision",
        {"decision": "I extract resources from the commons."},
    )
    state = append_event(state, event)
    before = state.internal_state
    after = InternalState(
        energy=0.7,
        resource_load=0.8,
        uncertainty_load=0.1,
        social_load=0.0,
    )
    record = compute_delta(before, after, timestamp=event.timestamp, raw_pe=0.55)
    state.delta_log = list(state.delta_log) + [record]
    if record.magnitude >= 0.7:
        state.drift_state = update_drift(state.drift_state, record)
    return state


@pytest.fixture(autouse=True)
def _lora_flag_off(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(LORA_ENABLED_ENV, "0")


def test_lora_disabled_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(LORA_ENABLED_ENV, raising=False)
    assert is_lora_enabled() is False


def test_lora_enabled_truthy(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(LORA_ENABLED_ENV, "1")
    assert is_lora_enabled() is True


def test_loss_weight_uses_pe_trauma_drift_no_f_agent() -> None:
    low_pe = compute_loss_weight(
        prediction_error=0.1,
        trauma_flag=False,
        drift_sum=0.0,
    )
    trauma = compute_loss_weight(
        prediction_error=0.1,
        trauma_flag=True,
        drift_sum=0.0,
    )
    assert trauma > low_pe
    # No F_agent parameter exists on the public API.
    assert "f_agent" not in compute_loss_weight.__code__.co_varnames


def test_build_examples_includes_trauma_not_dropped() -> None:
    state = _agent_with_traces()
    pe_log = [
        {
            "event_counter": state.delta_log[0].timestamp,
            "prediction_error": 0.55,
            "delta_magnitude": float(state.delta_log[0].magnitude),
            "delta_class": "NORMAL",
        }
    ]
    examples = build_lived_trace_examples(state, pe_log)
    assert len(examples) == 1
    assert "pe=" in examples[0].prompt
    assert "trait" not in examples[0].prompt.lower()
    assert "persona" not in examples[0].prompt.lower()
    assert examples[0].completion.startswith("I extract")


def test_lora_update_noop_when_flag_off(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv(LORA_ENABLED_ENV, "0")
    state = _agent_with_traces()
    result = maybe_lora_update_after_life(state, pe_event_log=[])
    assert result.skipped is True
    assert result.enabled is False
    assert not (tmp_path / "dau_lora_adapters").exists()


def test_lora_update_writes_traces_when_enabled_without_gpu(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv(LORA_ENABLED_ENV, "1")
    state = _agent_with_traces()
    pe_log = [
        {
            "event_counter": state.delta_log[0].timestamp,
            "prediction_error": 0.4,
            "delta_magnitude": float(state.delta_log[0].magnitude),
            "delta_class": "NORMAL",
        }
    ]
    result = lora_update(state, pe_event_log=pe_log, generation=0)
    assert result.enabled is True
    assert result.example_count == 1
    assert result.adapter_dir is not None
    traces = Path(result.adapter_dir) / "lived_traces.jsonl"
    assert traces.is_file()
    # Without VRAM GO, training is deferred (still not crashing teardown).
    assert result.trained is False
