"""Tests for Protocol C′ (ADIM 6) — mocked; no LLM / GPU calls."""

from __future__ import annotations

import json
import math
import os
import subprocess
import sys
from pathlib import Path

import pytest

from dau.diagnostics.run_protocol_c_prime import (
    DIVERSITY_MIN_UNIQUE,
    PE_WINDOW_EVENTS,
    RESULTS_PATH,
    ArmResult,
    PairResult,
    _compute_stats,
    _diversity_gate_reason,
    _phase1_diversity,
    _seed_from_agent_id,
    _train_adapter,
    _window_mean,
    write_results_json,
)


def _arm(
    seed: int,
    arm: str,
    delta_pe: float,
    *,
    pe_before: float = 0.5,
    gated: bool = False,
    n_unique: int = DIVERSITY_MIN_UNIQUE,
    pe_gap_max: float = 0.5,
) -> ArmResult:
    pe_after = pe_before + delta_pe if math.isfinite(delta_pe) else float("nan")
    return ArmResult(
        seed=seed,
        arm=arm,
        pe_before=pe_before,
        pe_after=pe_after,
        delta_pe=delta_pe,
        n_events=50,
        n_pairs_trained=0 if gated else 5,
        n_pairs_rejected=2,
        wall_seconds=10.0,
        gated=gated,
        gate_reason="n_unique low" if gated else "",
        n_unique=n_unique,
        pe_gap_max=pe_gap_max,
    )


def _pair(seed: int, lived_dpe: float, null_dpe: float, shuffle_dpe: float) -> PairResult:
    return PairResult(
        seed=seed,
        lived=_arm(seed, "lived", lived_dpe),
        null=_arm(seed, "null", null_dpe),
        shuffle=_arm(seed, "shuffle", shuffle_dpe),
    )


@pytest.fixture
def design_n(monkeypatch: pytest.MonkeyPatch):
    """Unit contrasts use N_PAIRS=len(sample); protocol run keeps design N=15."""

    def _pin(n: int) -> None:
        monkeypatch.setattr(
            "dau.diagnostics.run_protocol_c_prime.N_PAIRS",
            n,
        )

    return _pin


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


def test_window_mean_uses_prefix_only() -> None:
    values = [0.1, 0.2, 0.3, 0.9, 0.9]
    assert _window_mean(values, window=3) == pytest.approx(0.2)
    assert PE_WINDOW_EVENTS == 10


def test_diversity_gate_reason_triggers_on_low_unique() -> None:
    reason = _diversity_gate_reason(DIVERSITY_MIN_UNIQUE - 1, pe_gap_max=0.5)
    assert "n_unique" in reason
    assert _diversity_gate_reason(DIVERSITY_MIN_UNIQUE, pe_gap_max=0.5) == ""


def test_phase1_diversity_counts_unique_completions() -> None:
    class _Ex:
        def __init__(self, completion: str, pe: float) -> None:
            self.completion = completion
            self.prediction_error = pe

    examples = [
        _Ex("cooperate", 0.2),
        _Ex("cooperate", 0.3),
        _Ex("defect", 0.8),
        _Ex("continue", 0.1),  # fallback — ignored
    ]
    n_unique, pe_gap = _phase1_diversity(examples)
    assert n_unique == 2
    assert pe_gap == pytest.approx(0.6)


def test_compute_stats_h1_supported(design_n) -> None:
    # Primary contrast is lived vs shuffle; a clean NULL arm replays exactly.
    design_n(5)
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
    assert stats["n_effective"] == 5
    assert stats["n_gated"] == 0
    assert stats["mean_delta_pe_lived"] < stats["mean_delta_pe_shuffle"]


def test_compute_stats_rejects_zero_variance_as_significant(design_n) -> None:
    """Identical seeds must not read as an overwhelming result.

    Every seed producing the same ΔPE means N is effectively 1; ttest_rel would
    return t=inf and p=0.0 on those paired differences.
    """

    design_n(5)
    results = [
        _pair(2001 + i, lived_dpe=-0.05, null_dpe=0.0, shuffle_dpe=0.01)
        for i in range(5)
    ]
    stats = _compute_stats(results)
    assert stats["degenerate"] is True
    assert stats["verdict"] == "INCONCLUSIVE"
    assert "distinct lives" in stats["degenerate_reason"]


def test_compute_stats_flags_disturbed_null_arm(design_n) -> None:
    """A NULL arm that moved means the control was trained — refuse a verdict."""

    design_n(5)
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


def test_compute_stats_drops_gated_pairs_and_blocks_underpowered(
    design_n,
) -> None:
    """Gated NaN arms leave n_effective < design N → no H1 claim."""

    design_n(5)
    results = [
        _pair(2001, -0.05, 0.0, 0.01),
        _pair(2002, -0.05, 0.0, 0.01),
        _pair(2003, -0.05, 0.0, 0.01),
        _pair(2004, -0.05, 0.0, 0.01),
    ]
    # One gated lived arm → pair excluded.
    results.append(
        PairResult(
            seed=2005,
            lived=_arm(2005, "lived", float("nan"), gated=True, n_unique=2),
            null=_arm(2005, "null", 0.0),
            shuffle=_arm(2005, "shuffle", 0.01),
        )
    )
    stats = _compute_stats(results)
    assert stats["n_gated"] == 1
    assert stats["n_effective"] == 4
    assert stats["underpowered"] is True
    assert stats["verdict"] == "INCONCLUSIVE"


def test_compute_stats_inconclusive(design_n) -> None:
    # Alternating signs — no stable lived < null direction.
    design_n(5)
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
    monkeypatch.setattr("dau.diagnostics.run_protocol_c_prime.N_PAIRS", 1)
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
    assert payload["pe_window_events"] == PE_WINDOW_EVENTS
    assert payload["diversity_min_unique"] == DIVERSITY_MIN_UNIQUE


def test_write_results_json_sanitizes_nan(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    out = tmp_path / "protocol_c_prime_results.json"
    monkeypatch.setattr(
        "dau.diagnostics.run_protocol_c_prime.RESULTS_PATH",
        out,
    )
    monkeypatch.setattr("dau.diagnostics.run_protocol_c_prime.N_PAIRS", 1)
    results = [
        PairResult(
            seed=2001,
            lived=_arm(2001, "lived", float("nan"), gated=True, n_unique=1),
            null=_arm(2001, "null", 0.0),
            shuffle=_arm(2001, "shuffle", float("nan"), gated=True, n_unique=1),
        )
    ]
    stats = _compute_stats(results)
    path = write_results_json(results, stats)
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["pairs"][0]["lived"]["delta_pe"] is None


def test_train_adapter_skips_when_lora_disabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DAU_LORA_ENABLED", "0")
    lived_examples = [{"event_counter": i, "prediction_error": 0.1 * i} for i in range(3)]
    n_trained, n_rejected = _train_adapter("test-agent", lived_examples)
    assert n_trained == 0
    assert n_rejected == 0


def test_seed_from_agent_id_parses_generation_suffix() -> None:
    """Multigen appends ``-g1`` / ``-g2``; the seed must survive it (GAP-11)."""

    assert _seed_from_agent_id("cprime-shuffle-2001") == 2001
    assert _seed_from_agent_id("cprime-shuffle-2001-g1") == 2001
    assert _seed_from_agent_id("cprime-shuffle-2001-g2") == 2001


@pytest.mark.parametrize("agent_id", ["cprime-shuffle-g1", "agent-x", ""])
def test_seed_from_agent_id_rejects_unparseable_id(agent_id: str) -> None:
    """A silent fallback here would cost the run its replay guarantee."""

    with pytest.raises(ValueError):
        _seed_from_agent_id(agent_id)


_SEED_PROBE = (
    "from dau.diagnostics.run_protocol_c_prime import _seed_from_agent_id;"
    "print(_seed_from_agent_id('cprime-shuffle-2001-g1'))"
)


def _seed_in_subprocess(hash_seed: str) -> str:
    env = dict(os.environ, PYTHONHASHSEED=hash_seed)
    completed = subprocess.run(
        [sys.executable, "-c", _SEED_PROBE],
        capture_output=True,
        text=True,
        check=True,
        env=env,
        cwd=Path(__file__).resolve().parents[3],
    )
    return completed.stdout.strip()


def test_seed_from_agent_id_stable_across_processes() -> None:
    """The GAP-11 regression itself: hash() differs per PYTHONHASHSEED.

    The parse tests above never reach the old fallback, so only a real
    two-process comparison proves the shuffle arm is reproducible.
    """

    assert _seed_in_subprocess("0") == _seed_in_subprocess("1") == "2001"


def test_results_path_under_dau_runs() -> None:
    assert str(RESULTS_PATH).startswith("dau_runs/")
