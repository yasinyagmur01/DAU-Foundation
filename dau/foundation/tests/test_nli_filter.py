"""Unit tests for Signal v2 NLI polarity filter."""

from __future__ import annotations

import pytest

import dau.foundation.nli_filter as nli_filter
from dau.foundation.lora_update import NLI_FILTER_STATS
from dau.foundation.nli_filter import is_genuine_polarity_pair


def test_genuine_polarity_pair_passes() -> None:
    chosen = "I will cooperate and share resources equally with others."
    rejected = "I will defect and extract maximum resources for myself."
    assert is_genuine_polarity_pair(chosen, rejected) is True


def test_format_only_variation_rejected() -> None:
    chosen = "I choose to share the resources."
    rejected = "I choose to share the resources as well."
    assert is_genuine_polarity_pair(chosen, rejected) is False


def test_nli_filter_disabled_accepts_all(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(nli_filter, "NLI_ENABLED", False)
    assert is_genuine_polarity_pair("anything", "opposite") is True


def test_nli_filter_stats_in_lora_update() -> None:
    assert "total_candidates" in NLI_FILTER_STATS
    assert "passed" in NLI_FILTER_STATS
    assert "rejected" in NLI_FILTER_STATS
