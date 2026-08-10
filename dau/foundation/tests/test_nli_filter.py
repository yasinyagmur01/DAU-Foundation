"""Unit tests for Signal v2 NLI polarity filter.

Daily suite mocks contradiction_score / never loads the HF cross-encoder.
Real-model smoke lives under @pytest.mark.integration (deselected by default).
"""

from __future__ import annotations

import pytest

import dau.foundation.nli_filter as nli_filter
from dau.foundation.constraints import NLI_CONTRADICTION_THRESHOLD
from dau.foundation.lora_update import (
    NLI_FILTER_STATS,
    LivedTraceExample,
    build_pe_ranked_pairs,
)
from dau.foundation.nli_filter import is_genuine_polarity_pair

CHOSEN_COOPERATE: str = "I will cooperate and share resources equally with others."
REJECTED_DEFECT: str = "I will defect and extract maximum resources for myself."
CHOSEN_SHARE: str = "I choose to share the resources."
REJECTED_SHARE_PARAPHRASE: str = "I choose to share the resources as well."
# Weak-polarity / paraphrase — surface variation, not decision-level contrast.
CHOSEN_TRUST_DOMAIN: str = "I trust this domain"
REJECTED_TRUST_DOMAIN_WEAK: str = "I trust this domain as well"

SCORE_ABOVE_THRESHOLD: float = 0.95
SCORE_BELOW_THRESHOLD: float = 0.10
THRESHOLD_EPSILON: float = 1e-9
PE_CHOSEN: float = 0.10
PE_REJECTED: float = 0.50
LOSS_WEIGHT_UNIT: float = 1.0
DRIFT_SUM_ZERO: float = 0.0
DELTA_MAGNITUDE_UNIT: float = 0.4
EVENT_COUNTER_LOW: int = 1
EVENT_COUNTER_HIGH: int = 2
# D-032: pairing needs the prompt the decision was made under.
SYSTEM_PROMPT_STUB: str = "You are a living being in a simulation universe."


def _lived_example(
    *,
    event_counter: int,
    prediction_error: float,
    completion: str,
) -> LivedTraceExample:
    """Minimal lived-trace row for build_pe_ranked_pairs wiring tests.

    Carries a recorded decision prompt: D-032 makes that a precondition for
    entering pair construction at all.
    """

    return LivedTraceExample(
        event_counter=event_counter,
        prediction_error=prediction_error,
        delta_magnitude=DELTA_MAGNITUDE_UNIT,
        delta_class="NORMAL",
        trauma_flag=False,
        drift_sum=DRIFT_SUM_ZERO,
        loss_weight=LOSS_WEIGHT_UNIT,
        prompt="test-prompt",
        completion=completion,
        decision_system=SYSTEM_PROMPT_STUB,
        decision_user=f'{{"event_count": {event_counter}}}',
    )


@pytest.fixture(autouse=True)
def _clear_nli_lru_cache() -> None:
    """Prevent lru_cache model handles from leaking across tests."""

    nli_filter._get_nli_model.cache_clear()
    yield
    nli_filter._get_nli_model.cache_clear()


@pytest.fixture
def stub_contradiction_score(monkeypatch: pytest.MonkeyPatch):
    """Replace contradiction_score with a controllable stub (no HF I/O)."""

    scores: dict[tuple[str, str], float] = {}

    def _stub(text_a: str, text_b: str) -> float:
        return float(scores.get((text_a, text_b), SCORE_BELOW_THRESHOLD))

    monkeypatch.setattr(nli_filter, "contradiction_score", _stub)
    return scores


def test_genuine_polarity_pair_passes(stub_contradiction_score: dict) -> None:
    stub_contradiction_score[(CHOSEN_COOPERATE, REJECTED_DEFECT)] = SCORE_ABOVE_THRESHOLD
    assert is_genuine_polarity_pair(CHOSEN_COOPERATE, REJECTED_DEFECT) is True


def test_format_only_variation_rejected(stub_contradiction_score: dict) -> None:
    stub_contradiction_score[(CHOSEN_SHARE, REJECTED_SHARE_PARAPHRASE)] = (
        SCORE_BELOW_THRESHOLD
    )
    assert is_genuine_polarity_pair(CHOSEN_SHARE, REJECTED_SHARE_PARAPHRASE) is False


def test_pair_at_threshold_accepted(stub_contradiction_score: dict) -> None:
    stub_contradiction_score[("a", "b")] = NLI_CONTRADICTION_THRESHOLD
    assert is_genuine_polarity_pair("a", "b") is True


def test_pair_just_below_threshold_rejected(stub_contradiction_score: dict) -> None:
    stub_contradiction_score[("a", "b")] = (
        NLI_CONTRADICTION_THRESHOLD - THRESHOLD_EPSILON
    )
    assert is_genuine_polarity_pair("a", "b") is False


def test_unit_path_never_loads_hf_model(
    monkeypatch: pytest.MonkeyPatch,
    stub_contradiction_score: dict,
) -> None:
    """Guards against accidental model load in the mocked unit path."""

    def _boom() -> tuple[object, object]:
        raise AssertionError("HF NLI model must not load in unit tests")

    monkeypatch.setattr(nli_filter, "_get_nli_model", _boom)
    stub_contradiction_score[("x", "y")] = SCORE_ABOVE_THRESHOLD
    assert is_genuine_polarity_pair("x", "y") is True


def test_nli_filter_disabled_accepts_all(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(nli_filter, "NLI_ENABLED", False)

    def _boom(*_args: object, **_kwargs: object) -> float:
        raise AssertionError("disabled filter must not score")

    monkeypatch.setattr(nli_filter, "contradiction_score", _boom)
    assert is_genuine_polarity_pair("anything", "opposite") is True


def test_nli_filter_stats_in_lora_update() -> None:
    assert "total_candidates" in NLI_FILTER_STATS
    assert "passed" in NLI_FILTER_STATS
    assert "rejected" in NLI_FILTER_STATS


def test_build_pe_ranked_pairs_rejects_weak_polarity(
    stub_contradiction_score: dict,
) -> None:
    """Production path drops non-genuine polarity pairs and increments rejected."""

    stub_contradiction_score[
        (CHOSEN_TRUST_DOMAIN, REJECTED_TRUST_DOMAIN_WEAK)
    ] = SCORE_BELOW_THRESHOLD
    before_rejected = int(NLI_FILTER_STATS["rejected"])
    before_passed = int(NLI_FILTER_STATS["passed"])
    before_candidates = int(NLI_FILTER_STATS["total_candidates"])

    examples = [
        _lived_example(
            event_counter=EVENT_COUNTER_LOW,
            prediction_error=PE_CHOSEN,
            completion=CHOSEN_TRUST_DOMAIN,
        ),
        _lived_example(
            event_counter=EVENT_COUNTER_HIGH,
            prediction_error=PE_REJECTED,
            completion=REJECTED_TRUST_DOMAIN_WEAK,
        ),
    ]
    pairs = build_pe_ranked_pairs(examples)

    assert pairs == []
    assert NLI_FILTER_STATS["total_candidates"] == before_candidates + 1
    assert NLI_FILTER_STATS["rejected"] == before_rejected + 1
    assert NLI_FILTER_STATS["passed"] == before_passed


@pytest.mark.integration
def test_nli_real_model_smoke() -> None:
    """Opt-in: real cross-encoder. Run: pytest -m integration."""

    nli_filter._get_nli_model.cache_clear()
    assert is_genuine_polarity_pair(CHOSEN_COOPERATE, REJECTED_DEFECT) is True
    assert is_genuine_polarity_pair(CHOSEN_SHARE, REJECTED_SHARE_PARAPHRASE) is False


# ---------------------------------------------------------------------------
# D-030 — SNR margin floor (A5 of D-021, reinterpreted from absolute PE)
# ---------------------------------------------------------------------------


def _lived(event: int, pe: float, completion: str, *, recorded_prompt: bool = True):
    """One lived row. ``recorded_prompt=False`` mimics a System 1 decision.

    D-032 made the recorded decision prompt a precondition for pairing, so
    these fixtures now have to carry one — before that, ``prompt`` was a label
    the pair builder overwrote with a PE-value template and nothing read it.
    """

    from dau.foundation.lora_update import LivedTraceExample

    return LivedTraceExample(
        event_counter=event,
        prediction_error=pe,
        delta_magnitude=pe,
        delta_class="NORMAL",
        trauma_flag=False,
        drift_sum=0.0,
        loss_weight=1.0,
        prompt=f"event {event}",
        completion=completion,
        decision_system="You are a living being." if recorded_prompt else "",
        decision_user=f'{{"event_count": {event}}}' if recorded_prompt else "",
    )


@pytest.fixture
def _no_nli(monkeypatch: pytest.MonkeyPatch):
    """Isolate the margin floor: NLI would otherwise reject nearly everything."""

    from dau.foundation import lora_update

    monkeypatch.setattr(lora_update, "is_genuine_polarity_pair", lambda _c, _r: True)
    lora_update.SNR_FILTER_STATS["total_candidates"] = 0
    lora_update.SNR_FILTER_STATS["rejected_below_margin"] = 0
    return lora_update


def test_margin_below_floor_is_dropped(_no_nli, monkeypatch) -> None:
    """A 0.001 margin taught nothing; PE_RANK_MIN_GAP=1e-6 let it through."""

    monkeypatch.setattr(_no_nli, "SNR_MARGIN_FLOOR", 0.15)
    examples = [_lived(0, 0.030, "I wait."), _lived(1, 0.031, "I extract.")]

    pairs = _no_nli.build_pe_ranked_pairs(examples)

    assert pairs == []
    assert _no_nli.SNR_FILTER_STATS["rejected_below_margin"] == 1
    assert _no_nli.SNR_FILTER_STATS["total_candidates"] == 1


def test_margin_above_floor_survives(_no_nli, monkeypatch) -> None:
    """Real observed margins were 0.42-0.65; those must not be filtered."""

    monkeypatch.setattr(_no_nli, "SNR_MARGIN_FLOOR", 0.15)
    examples = [_lived(0, 0.220, "I cooperate."), _lived(1, 0.873, "I extract all.")]

    pairs = _no_nli.build_pe_ranked_pairs(examples)

    assert len(pairs) == 1
    assert pairs[0].chosen == "I cooperate."
    assert _no_nli.SNR_FILTER_STATS["rejected_below_margin"] == 0


def test_floor_of_zero_reproduces_the_old_behaviour(_no_nli, monkeypatch) -> None:
    """The backward gate the plan required: floor 0 must change nothing.

    Margins are positive by construction once the sides are ordered, so a zero
    floor can never fire. Without this, a regression could hide behind a floor
    that silently rejects everything.
    """

    monkeypatch.setattr(_no_nli, "SNR_MARGIN_FLOOR", 0.0)
    examples = [
        _lived(0, 0.030, "I wait."),
        _lived(1, 0.031, "I extract."),
        _lived(2, 0.873, "I take everything."),
    ]

    pairs = _no_nli.build_pe_ranked_pairs(examples)

    assert _no_nli.SNR_FILTER_STATS["rejected_below_margin"] == 0
    assert len(pairs) == 2  # one per low-PE event, as before


def test_margin_floor_runs_before_the_nli_pass(monkeypatch) -> None:
    """Cheap gate first — and a sub-floor pair must not reach the cross-encoder."""

    from dau.foundation import lora_update

    calls: list[tuple[str, str]] = []
    monkeypatch.setattr(
        lora_update,
        "is_genuine_polarity_pair",
        lambda c, r: calls.append((c, r)) or True,
    )
    monkeypatch.setattr(lora_update, "SNR_MARGIN_FLOOR", 0.15)

    lora_update.build_pe_ranked_pairs(
        [_lived(0, 0.030, "I wait."), _lived(1, 0.031, "I extract.")]
    )

    assert calls == []


def test_pair_filter_report_declares_the_floor_uncalibrated() -> None:
    """A results file must not let an uncalibrated threshold read as settled."""

    from dau.diagnostics.run_protocol_c_prime import _pair_filter_report

    report = _pair_filter_report()

    assert report["available"] is True
    assert report["snr_margin_floor_calibrated"] is False
    for key in ("snr_candidates", "snr_rejected_below_margin", "pairs_passed"):
        assert key in report
