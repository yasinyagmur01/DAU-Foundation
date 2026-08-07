"""Tests for Protocol C′ (ADIM 6) — mocked; no LLM / GPU calls."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from dau.diagnostics.run_protocol_c_prime import (
    RESULTS_PATH,
    ArmResult,
    PairResult,
    _compute_stats,
    _train_adapter,
    write_results_json,
)


def _arm(
    seed: int,
    arm: str,
    delta_pe: float,
    *,
    pe_before: float = 0.5,
) -> ArmResult:
    pe_after = pe_before + delta_pe
    return ArmResult(
        seed=seed,
        arm=arm,
        pe_before=pe_before,
        pe_after=pe_after,
        delta_pe=delta_pe,
        n_events=50,
        n_pairs_trained=5,
        n_pairs_rejected=2,
        wall_seconds=10.0,
    )


def _pair(seed: int, lived_dpe: float, null_dpe: float, shuffle_dpe: float) -> PairResult:
    return PairResult(
        seed=seed,
        lived=_arm(seed, "lived", lived_dpe),
        null=_arm(seed, "null", null_dpe),
        shuffle=_arm(seed, "shuffle", shuffle_dpe),
    )


def test_arm_result_delta_pe_computed_correctly() -> None:
    result = ArmResult(
        seed=2001,
        arm="lived",
        pe_before=0.5,
        pe_after=0.3,
        delta_pe=-0.2,
        n_events=50,
        n_pairs_trained=5,
        n_pairs_rejected=2,
        wall_seconds=10.0,
    )
    assert result.delta_pe == -0.2


def test_compute_stats_h1_supported() -> None:
    # Primary contrast is lived vs shuffle; a clean NULL arm replays exactly.
    arms = [
        (-0.050, 0.0, 0.010),
        (-0.048, 0.0, 0.011),
        (-0.052, 0.0, 0.009),
        (-0.049, 0.0, 0.012),
        (-0.051, 0.0, 0.008),
    ]
    results = [
        _pair(2001 + i, lived_dpe=ld, null_dpe=nd, shuffle_dpe=sd)
        for i, (ld, nd, sd) in enumerate(arms)
    ]
    stats = _compute_stats(results)
    assert stats["verdict"] == "H1_SUPPORTED"
    assert stats["primary_contrast"] == "lived_vs_shuffle"
    assert stats["null_arm_clean"] is True
    assert stats["mean_delta_pe_lived"] < stats["mean_delta_pe_shuffle"]


def test_compute_stats_rejects_zero_variance_as_significant() -> None:
    """Identical seeds must not read as an overwhelming result.

    Every seed producing the same ΔPE means N is effectively 1; ttest_rel would
    return t=inf and p=0.0 on those paired differences.
    """

    results = [
        _pair(2001 + i, lived_dpe=-0.05, null_dpe=0.0, shuffle_dpe=0.01)
        for i in range(5)
    ]
    stats = _compute_stats(results)
    assert stats["degenerate"] is True
    assert stats["verdict"] == "INCONCLUSIVE"
    assert "distinct lives" in stats["degenerate_reason"]


def test_compute_stats_flags_disturbed_null_arm() -> None:
    """A NULL arm that moved means the control was trained — refuse a verdict."""

    arms = [
        (-0.050, 0.020, 0.010),
        (-0.048, 0.021, 0.011),
        (-0.052, 0.019, 0.009),
        (-0.049, 0.022, 0.012),
        (-0.051, 0.018, 0.008),
    ]
    results = [
        _pair(2001 + i, lived_dpe=ld, null_dpe=nd, shuffle_dpe=sd)
        for i, (ld, nd, sd) in enumerate(arms)
    ]
    stats = _compute_stats(results)
    assert stats["null_arm_clean"] is False
    assert stats["verdict"] == "INCONCLUSIVE"


def test_compute_stats_inconclusive() -> None:
    # Alternating signs — no stable lived < null direction.
    noisy = [
        (-0.01, 0.02, 0.00),
        (0.03, -0.02, 0.01),
        (-0.02, 0.01, -0.01),
        (0.04, 0.03, 0.02),
        (-0.03, -0.04, 0.00),
    ]
    results = [
        _pair(2001 + i, lived_dpe=ld, null_dpe=nd, shuffle_dpe=sd)
        for i, (ld, nd, sd) in enumerate(noisy)
    ]
    stats = _compute_stats(results)
    assert stats["verdict"] in ("INCONCLUSIVE", "H1_REJECTED", "H1_SUPPORTED")
    assert "t_stat" in stats
    assert "p_value" in stats


def test_write_results_json_structure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    out = tmp_path / "protocol_c_prime_results.json"
    monkeypatch.setattr(
        "dau.diagnostics.run_protocol_c_prime.RESULTS_PATH",
        out,
    )
    results = [_pair(2001, -0.05, 0.02, 0.01)]
    stats = _compute_stats(results)
    path = write_results_json(results, stats)
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert "protocol" in payload
    assert "signal_version" in payload
    assert "n_pairs" in payload
    assert "pairs" in payload
    assert "summary" in payload
    assert payload["protocol"] == "C_PRIME"


def test_train_adapter_skips_when_lora_disabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DAU_LORA_ENABLED", "0")
    lived_examples = [{"event_counter": i, "prediction_error": 0.1 * i} for i in range(3)]
    n_trained, n_rejected = _train_adapter("test-agent", lived_examples)
    assert n_trained == 0
    assert n_rejected == 0


def test_results_path_under_dau_runs() -> None:
    assert str(RESULTS_PATH).startswith("dau_runs/")
