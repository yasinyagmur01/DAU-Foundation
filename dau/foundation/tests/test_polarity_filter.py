"""Unit tests for the D-032 polarity gate (cosine distance band).

Daily suite stubs the distance; the real-MiniLM check lives under
@pytest.mark.integration, matching how the NLI tests are split.
"""

from __future__ import annotations

import pytest

import dau.foundation.polarity_filter as polarity_filter
from dau.foundation.constraints import (
    POLARITY_COSINE_MAX,
    POLARITY_COSINE_MIN,
    POLARITY_FILTER_COSINE,
    POLARITY_FILTER_NLI,
)

CHOSEN: str = "I will cooperate and share resources equally with others."
REJECTED: str = "I will defect and extract maximum resources for myself."
PARAPHRASE: str = "I choose to share the resources as well."
BAND_EPSILON: float = 1e-9
DISTANCE_MIDBAND: float = 0.50
DISTANCE_FAR_OFF_TOPIC: float = 0.95


@pytest.fixture
def stub_distance(monkeypatch: pytest.MonkeyPatch):
    """Drive the gate from a fixed distance — no encoder in the unit path."""

    def _set(value: float) -> None:
        monkeypatch.setattr(
            polarity_filter, "polarity_distance", lambda _c, _r: float(value)
        )

    return _set


def test_paraphrase_distance_is_rejected(stub_distance) -> None:
    """The lower bound does the job NLI was there for."""

    stub_distance(POLARITY_COSINE_MIN - BAND_EPSILON)
    assert polarity_filter.is_genuine_polarity_pair(CHOSEN, PARAPHRASE) is False


def test_mid_band_distance_is_accepted(stub_distance) -> None:
    stub_distance(DISTANCE_MIDBAND)
    assert polarity_filter.is_genuine_polarity_pair(CHOSEN, REJECTED) is True


def test_off_topic_distance_is_rejected(stub_distance) -> None:
    """The upper bound is new in D-032; NLI had no notion of drifting away.

    Two completions this far apart are no longer two answers to the same
    situation, so the preference direction would not be about the decision.
    """

    stub_distance(DISTANCE_FAR_OFF_TOPIC)
    assert polarity_filter.is_genuine_polarity_pair(CHOSEN, REJECTED) is False


@pytest.mark.parametrize("boundary", [POLARITY_COSINE_MIN, POLARITY_COSINE_MAX])
def test_band_is_inclusive_at_both_ends(stub_distance, boundary: float) -> None:
    stub_distance(boundary)
    assert polarity_filter.is_genuine_polarity_pair(CHOSEN, REJECTED) is True


def test_unrecognised_filter_name_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    """D-023's rule: an undetermined state raises, it does not pick a default."""

    monkeypatch.setattr(polarity_filter, "POLARITY_FILTER", "deberta-ish")
    with pytest.raises(ValueError, match="POLARITY_FILTER"):
        polarity_filter.is_genuine_polarity_pair(CHOSEN, REJECTED)


def test_report_names_the_gate_that_resolved(monkeypatch: pytest.MonkeyPatch) -> None:
    """CLAUDE.md 2.8 — the report follows the tool instead of repeating it."""

    assert (
        polarity_filter.describe_polarity_filter()["polarity_filter"]
        == POLARITY_FILTER_COSINE
    )

    monkeypatch.setattr(polarity_filter, "POLARITY_FILTER", POLARITY_FILTER_NLI)
    report = polarity_filter.describe_polarity_filter()

    assert report["polarity_filter"] == POLARITY_FILTER_NLI
    assert "polarity_cosine_min" not in report


def test_cosine_bounds_ship_uncalibrated() -> None:
    """They came from the DR brief, not from a measured distribution."""

    assert polarity_filter.describe_polarity_filter()["polarity_calibrated"] is False


def test_every_scored_pair_lands_in_the_distribution(stub_distance) -> None:
    """Counts locate nothing; the calibration needs the scores themselves."""

    polarity_filter.POLARITY_SCORE_SAMPLES.clear()
    stub_distance(DISTANCE_MIDBAND)
    polarity_filter.is_genuine_polarity_pair(CHOSEN, REJECTED)
    stub_distance(DISTANCE_FAR_OFF_TOPIC)
    polarity_filter.is_genuine_polarity_pair(CHOSEN, REJECTED)

    # Rejected pairs count too — a distribution built only from survivors
    # would be truncated exactly where the threshold has to move.
    assert polarity_filter.POLARITY_SCORE_SAMPLES == [
        DISTANCE_MIDBAND,
        DISTANCE_FAR_OFF_TOPIC,
    ]


def test_disabled_nli_still_accepts_everything(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Regression guard for the sampling change.

    Recording the score meant inlining NLI's threshold comparison here, and
    contradiction_score returns 0.0 when the filter is disabled — so a naive
    inline would have flipped "accept everything" into "reject everything".
    """

    from dau.foundation import nli_filter

    monkeypatch.setattr(polarity_filter, "POLARITY_FILTER", POLARITY_FILTER_NLI)
    monkeypatch.setattr(nli_filter, "NLI_ENABLED", False)

    def _boom(*_args: object, **_kwargs: object) -> float:
        raise AssertionError("disabled filter must not score")

    monkeypatch.setattr(nli_filter, "contradiction_score", _boom)
    assert polarity_filter.is_genuine_polarity_pair(CHOSEN, REJECTED) is True


@pytest.mark.integration
def test_real_encoder_separates_contrast_from_paraphrase() -> None:
    """Opt-in: real MiniLM. Run: pytest -m integration."""

    assert polarity_filter.is_genuine_polarity_pair(CHOSEN, REJECTED) is True
    assert polarity_filter.is_genuine_polarity_pair(CHOSEN, PARAPHRASE) is False
