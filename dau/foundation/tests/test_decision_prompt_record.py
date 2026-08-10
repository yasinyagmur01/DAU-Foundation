"""The decision event must record the prompt the decision was made under.

Channel 2 (LoRA) trains on this record. Before it existed, DPO ran on
``"Lived preference: pe=0.413 decision over pe=0.873"`` — a 51-token prompt
with no system message, while inference runs SYSTEM_PROMPT + memory + somatic
+ the full AgentView at 246-306 tokens. These tests pin the record to what the
model actually received, not to anything regenerated from constants.
"""

from __future__ import annotations

from typing import Any

import pytest

import dau.foundation.graph as graph_mod
from dau.foundation.constraints import build_default_constraints
from dau.foundation.drift import DriftState
from dau.foundation.graph import (
    DECISION_PROMPT_SYSTEM_KEY,
    DECISION_PROMPT_USER_KEY,
    LLM_BACKEND_ENV,
    LLM_BACKEND_GROQ,
    SYSTEM_PROMPT,
    agent_node,
)
from dau.foundation.lod import CognitiveMode, LODState
from dau.foundation.state import DAUAgentState, DeltaRecord, InternalState

AGENT_ID: str = "prompt-record-0"
MOCK_DECISION: str = "I will extract resources to increase my energy."
# A body that swung hard enough for the somatic layer to fire, so system_content
# is provably richer than the SYSTEM_PROMPT constant. Without this the "record
# follows the tool" mutation below would pass on a bare state.
SOMATIC_MAGNITUDE: float = 0.9
LOW_ENERGY: float = 0.1


class _RecordingResponse:
    def __init__(self, content: str) -> None:
        self.content = content


class _RecordingLLM:
    """Stands in for the groq client and keeps what agent_node sent it."""

    def __init__(self) -> None:
        self.messages: list[dict[str, str]] = []

    def invoke(self, messages: list[dict[str, str]]) -> _RecordingResponse:
        self.messages = list(messages)
        return _RecordingResponse(MOCK_DECISION)

    def _content(self, role: str) -> str:
        for message in self.messages:
            if message["role"] == role:
                return str(message["content"])
        raise AssertionError(f"agent_node sent no {role} message")


def _state(mode: CognitiveMode) -> DAUAgentState:
    snapshot = {
        "energy": LOW_ENERGY,
        "resource_load": 0.8,
        "uncertainty_load": 0.6,
        "social_load": 0.0,
    }
    return DAUAgentState(
        agent_id=AGENT_ID,
        environment=build_default_constraints(),
        internal_state=InternalState(energy=LOW_ENERGY, resource_load=0.8),
        drift_state=DriftState(),
        lod_state=LODState(mode=mode),
        delta_log=[
            DeltaRecord(
                timestamp=0,
                magnitude=SOMATIC_MAGNITUDE,
                affected_domain="resource",
                snapshot_before=snapshot,
                snapshot_after=dict(snapshot),
            )
        ],
        event_log=[],
    )


@pytest.fixture
def recording_llm(monkeypatch: pytest.MonkeyPatch) -> _RecordingLLM:
    llm = _RecordingLLM()
    monkeypatch.setenv(LLM_BACKEND_ENV, LLM_BACKEND_GROQ)
    monkeypatch.setattr(graph_mod, "MEMORY_ENABLED", False)
    monkeypatch.setattr(graph_mod, "_build_llm", lambda: llm)
    return llm


def _decision_payload(state: DAUAgentState) -> dict[str, Any]:
    patch = agent_node(state)
    events = patch["event_log"]
    assert events, "agent_node appended no event"
    return dict(events[-1].payload)


def test_decision_records_the_exact_prompt_the_model_received(
    recording_llm: _RecordingLLM,
) -> None:
    """Both halves are stored verbatim — byte-identical to what was sent."""

    payload = _decision_payload(_state(CognitiveMode.SYSTEM_2))

    assert payload[DECISION_PROMPT_SYSTEM_KEY] == recording_llm._content("system")
    assert payload[DECISION_PROMPT_USER_KEY] == recording_llm._content("user")


def test_recorded_system_prompt_is_not_the_bare_constant(
    recording_llm: _RecordingLLM,
) -> None:
    """Mutation guard for the repeating failure (CLAUDE.md 2.8).

    Rebuilding the record from SYSTEM_PROMPT at read time is the tempting
    shortcut and it silently drops the somatic / drift / memory layers. This
    state swings the body, so the sent system message is strictly longer than
    the constant — a record that equals the constant is a regenerated one.
    """

    payload = _decision_payload(_state(CognitiveMode.SYSTEM_2))
    recorded = payload[DECISION_PROMPT_SYSTEM_KEY]

    assert recorded != SYSTEM_PROMPT
    assert recorded.startswith(SYSTEM_PROMPT)
    assert len(recorded) > len(SYSTEM_PROMPT)


def test_recorded_user_prompt_is_the_agent_view_json(
    recording_llm: _RecordingLLM,
) -> None:
    """The user half is the AgentView JSON, the same object inference sends."""

    payload = _decision_payload(_state(CognitiveMode.SYSTEM_2))
    recorded = payload[DECISION_PROMPT_USER_KEY]

    assert recorded.startswith("{") and '"energy"' in recorded


def test_system_1_decision_records_no_prompt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """NPC decisions never had a prompt, so they must not claim one.

    Their absence is load-bearing: it is what stops the pair builder from
    training the policy on System 1 heuristic text it never generated.
    """

    monkeypatch.setattr(graph_mod, "MEMORY_ENABLED", False)
    payload = _decision_payload(_state(CognitiveMode.SYSTEM_1))

    assert DECISION_PROMPT_SYSTEM_KEY not in payload
    assert DECISION_PROMPT_USER_KEY not in payload
    assert payload["decision"]
