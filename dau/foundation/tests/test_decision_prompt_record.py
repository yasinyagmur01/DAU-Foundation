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


# ---------------------------------------------------------------------------
# The reader: what build_pe_ranked_pairs does with the record
# ---------------------------------------------------------------------------

RECORDED_SYSTEM: str = "You are a living being.\nPriority: resource."
LOW_PE: float = 0.22
HIGH_PE: float = 0.87
CHOSEN_TEXT: str = "I cooperate and share resources."
REJECTED_TEXT: str = "I extract everything I can reach."


def _lived_row(counter: int, pe: float, completion: str, *, recorded: bool = True):
    from dau.foundation.lora_update import LivedTraceExample

    return LivedTraceExample(
        event_counter=counter,
        prediction_error=pe,
        delta_magnitude=pe,
        delta_class="NORMAL",
        trauma_flag=False,
        drift_sum=0.0,
        loss_weight=1.0,
        prompt=f"lived scalars {counter}",
        completion=completion,
        decision_system=RECORDED_SYSTEM if recorded else "",
        decision_user=f'{{"event_count": {counter}}}' if recorded else "",
    )


@pytest.fixture
def pair_builder(monkeypatch: pytest.MonkeyPatch):
    """Isolate prompt handling: NLI and the margin floor are tested elsewhere."""

    from dau.foundation import lora_update

    monkeypatch.setattr(lora_update, "is_genuine_polarity_pair", lambda _c, _r: True)
    monkeypatch.setattr(lora_update, "SNR_MARGIN_FLOOR", 0.0)
    lora_update.PROMPT_FILTER_STATS["examples_seen"] = 0
    lora_update.PROMPT_FILTER_STATS["skipped_no_recorded_prompt"] = 0
    return lora_update


def test_pair_prompt_is_the_chosen_events_recorded_prompt(pair_builder) -> None:
    """Not a PE-value template — the situation the chosen decision was made in.

    Mutation guard for the retired PREF_LIVED_CONTEXT_TEMPLATE: a prompt built
    from pe_chosen/pe_rejected states the answer key and never occurs at
    inference, so it must not reappear.
    """

    chosen_row = _lived_row(1, LOW_PE, CHOSEN_TEXT)
    pairs = pair_builder.build_pe_ranked_pairs(
        [chosen_row, _lived_row(2, HIGH_PE, REJECTED_TEXT)]
    )

    assert len(pairs) == 1
    assert pairs[0].prompt == chosen_row.decision_user
    assert pairs[0].system == RECORDED_SYSTEM
    assert "Lived preference" not in pairs[0].prompt
    assert f"{LOW_PE:.3f}" not in pairs[0].prompt


def test_event_without_recorded_prompt_is_skipped_and_counted(
    pair_builder,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Skipping is allowed; skipping quietly is not (CLAUDE.md 2.9)."""

    pairs = pair_builder.build_pe_ranked_pairs(
        [
            _lived_row(1, LOW_PE, CHOSEN_TEXT, recorded=False),
            _lived_row(2, HIGH_PE, REJECTED_TEXT),
        ]
    )

    assert pairs == []
    assert pair_builder.PROMPT_FILTER_STATS["examples_seen"] == 2
    assert pair_builder.PROMPT_FILTER_STATS["skipped_no_recorded_prompt"] == 1
    assert "[LORA][WARN]" in capsys.readouterr().out


def test_shuffled_control_keeps_the_same_conditioning(pair_builder) -> None:
    """The control arm must differ in preference direction and nothing else.

    Field-by-field reconstruction used to drop any newly added field; a
    shuffled arm training without the system prompt would make the two arms
    incomparable rather than opposite.
    """

    pairs = pair_builder.build_pe_ranked_pairs(
        [_lived_row(1, LOW_PE, CHOSEN_TEXT), _lived_row(2, HIGH_PE, REJECTED_TEXT)]
    )
    shuffled = pair_builder.shuffle_preference_pairs(pairs)

    assert len(shuffled) == 1
    assert shuffled[0].system == pairs[0].system
    assert shuffled[0].prompt == pairs[0].prompt
    assert shuffled[0].chosen == pairs[0].rejected
    assert shuffled[0].rejected == pairs[0].chosen


def test_shuffle_inverts_every_pair_not_a_random_half(pair_builder) -> None:
    """D-040: the control's strength must not be drawn per seed.

    Under the old coin flip the realised net signal on seeds 2001-2003 came
    out +14.9%, +2.4% and -21.1% of lived — three different controls wearing
    one name. A control that varies is not a control, so every pair inverts.
    """

    pairs = pair_builder.build_pe_ranked_pairs(
        [
            _lived_row(counter, LOW_PE, CHOSEN_TEXT)
            for counter in range(1, 40, 2)
        ]
        + [
            _lived_row(counter, HIGH_PE, REJECTED_TEXT)
            for counter in range(2, 41, 2)
        ]
    )
    assert len(pairs) > 1, "need several pairs for a half-swap to be visible"

    shuffled = pair_builder.shuffle_preference_pairs(pairs)

    assert len(shuffled) == len(pairs)
    for before, after in zip(pairs, shuffled):
        assert after.chosen == before.rejected
        assert after.rejected == before.chosen
        assert after.pe_chosen == before.pe_rejected
        assert after.pe_rejected == before.pe_chosen

    # No pair left facing the lived direction — the old rule left roughly half.
    assert not [
        after for before, after in zip(pairs, shuffled) if after.chosen == before.chosen
    ]
