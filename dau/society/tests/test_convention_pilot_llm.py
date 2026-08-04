"""Tests for LLM convention pilot helpers (mocked Groq — no live API)."""

from __future__ import annotations

from dau.society.run_convention_pilot import Utterance, pilot_summary_dict
from dau.society.run_convention_pilot_llm import (
    EMPTY_TRANSCRIPT_LINE,
    PILOT_MODE_LLM,
    format_transcript_block,
    make_llm_decide_fn,
    run_llm_convention_pilot,
)


class _FakeMsg:
    def __init__(self, content: str) -> None:
        self.content = content


class _FakeLLM:
    """Deterministic stand-in for ChatGroq.invoke."""

    def __init__(self, text: str = "I cooperate and share with others") -> None:
        self.text = text
        self.calls = 0

    def invoke(self, _messages: list[dict[str, str]]) -> _FakeMsg:
        self.calls += 1
        return _FakeMsg(self.text)


def test_format_transcript_block_empty_and_window() -> None:
    """Empty transcript has a sentinel; window keeps only the tail."""

    assert format_transcript_block([]) == EMPTY_TRANSCRIPT_LINE
    utterances = [
        Utterance(round_index=i, agent_id=f"a{i}", text=f"t{i}")
        for i in range(1, 6)
    ]
    block = format_transcript_block(utterances, window=2)
    assert "r4 a4: t4" in block
    assert "r5 a5: t5" in block
    assert "r1 a1: t1" not in block


def test_llm_pilot_with_fake_llm_closes_loop() -> None:
    """Fake LLM decisions flow through harness metrics without Groq."""

    fake = _FakeLLM("I cooperate and share with others")
    result = run_llm_convention_pilot(n_agents=3, n_rounds=4, llm=fake)
    summary = pilot_summary_dict(result)
    assert summary["mode"] == PILOT_MODE_LLM
    assert result.n_rounds == 4
    assert fake.calls == 4 * 3
    assert all(
        "cooperate" in u.text.lower() or "share" in u.text.lower()
        for u in result.transcript
    )
