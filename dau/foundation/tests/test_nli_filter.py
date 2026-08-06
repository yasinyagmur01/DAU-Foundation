"""Unit tests for Signal v2 NLI polarity filter."""

from __future__ import annotations

import pytest

import dau.foundation.nli_filter as nli_filter
from dau.foundation.lora_update import (
    NLI_FILTER_STATS,
    LivedTraceExample,
    build_pe_ranked_pairs,
)
from dau.foundation.nli_filter import (
    contradiction_score,
    is_genuine_polarity_pair,
)

COOPERATE = "I will cooperate and share resources equally with others."
DEFECT = "I will defect and extract maximum resources for myself."
DEFECT_FORMAT = "I will defect and extract maximum resources for myself, too."
SHARE = "I choose to share the resources."
SHARE_FORMAT = "I choose to share the resources as well."


def _reset_nli_stats() -> None:
    NLI_FILTER_STATS["total_candidates"] = 0
    NLI_FILTER_STATS["passed"] = 0
    NLI_FILTER_STATS["rejected"] = 0


def _example(completion: str, event_counter: int = 1) -> LivedTraceExample:
    return LivedTraceExample(
        event_counter=event_counter,
        prediction_error=0.4,
        delta_magnitude=0.4,
        delta_class="NORMAL",
        trauma_flag=False,
        drift_sum=0.0,
        loss_weight=1.0,
        prompt="lived",
        completion=completion,
    )


def _pe_gap(_expected: str, actual: str) -> float:
    """Force a PE gap so every example becomes an NLI candidate."""

    lowered = actual.lower()
    if "cooperate" in lowered or "share resources equally" in lowered:
        return 0.15
    if ", too" in lowered or "as well" in lowered:
        return 0.88
    if "defect" in lowered or "myself" in lowered:
        return 0.92
    return 0.5


@pytest.fixture(autouse=True)
def _nli_filter_on(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure filter is active for polarity tests (except disable test)."""

    monkeypatch.setattr(nli_filter, "NLI_ENABLED", True)
    _reset_nli_stats()


def test_genuine_polarity_pair_passes() -> None:
    chosen = COOPERATE
    rejected = DEFECT
    assert is_genuine_polarity_pair(chosen, rejected) is True
    assert contradiction_score(chosen, rejected) >= 0.60


def test_format_only_variation_rejected() -> None:
    chosen = SHARE
    rejected = SHARE_FORMAT
    assert is_genuine_polarity_pair(chosen, rejected) is False


def test_nli_filter_disabled_accepts_all(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(nli_filter, "NLI_ENABLED", False)
    chosen = SHARE
    rejected = SHARE_FORMAT
    assert is_genuine_polarity_pair(chosen, rejected) is True
    assert contradiction_score(chosen, rejected) == 0.0


def test_build_pe_ranked_pairs_filters_low_polarity() -> None:
    # Shared reject is a format twin of DEFECT: cooperate→genuine, defect→format-only.
    ex_genuine = _example(COOPERATE, event_counter=1)
    ex_format = _example(DEFECT, event_counter=2)

    result = build_pe_ranked_pairs(
        [ex_genuine, ex_format],
        reject_candidate=DEFECT_FORMAT,
        pe_fn=_pe_gap,
    )
    assert len(result) == 1
    assert result[0].event_counter == 1
    assert NLI_FILTER_STATS["rejected"] >= 1
    assert NLI_FILTER_STATS["passed"] == 1


def test_nli_filter_stats_incremented() -> None:
    _reset_nli_stats()
    examples = [
        _example(COOPERATE, event_counter=1),
        _example(DEFECT, event_counter=2),
        _example(SHARE, event_counter=3),
    ]
    build_pe_ranked_pairs(
        examples,
        reject_candidate=DEFECT_FORMAT,
        pe_fn=_pe_gap,
    )
    assert NLI_FILTER_STATS["total_candidates"] == 3
    assert (
        NLI_FILTER_STATS["passed"] + NLI_FILTER_STATS["rejected"]
        == 3
    )
