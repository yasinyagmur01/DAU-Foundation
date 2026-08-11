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
    LLM_TEMPERATURE_ENV,
    PE_WINDOW_ALL_EVENTS,
    PE_WINDOW_EVENTS,
    RESULTS_PATH,
    TEMPERATURE_DEFAULT,
    ArmResult,
    PairResult,
    _compute_stats,
    _diversity_gate_reason,
    _lock_seeds,
    _phase1_diversity,
    _seed_from_agent_id,
    _temperature,
    _train_adapter,
    _window_mean,
    describe_pe_window,
    write_results_json,
)
from dau.diagnostics.tool_identity import (
    BACKEND_LOCAL,
    LORA_CHOICE_OFF,
    LORA_CHOICE_ON,
    LORA_ENABLED_ENV,
    build_tool_identity,
    resolve_lora_choice,
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


def test_window_mean_prefix_mode_still_works() -> None:
    """A positive window keeps the historical prefix behaviour."""

    values = [0.1, 0.2, 0.3, 0.9, 0.9]
    assert _window_mean(values, window=3) == pytest.approx(0.2)


def test_window_mean_default_reads_the_whole_phase() -> None:
    """D-036. The window used to be the first 10 of a 50-event phase.

    Measured in D-035: the adapter changed 21 of seed 2001's 50 phase-2
    decisions with none in the first ten, and delta_pe came out bit-identical
    to the untrained arm. Averaging a prefix answers a question about the
    prefix, not about the intervention.
    """

    values = [0.1, 0.2, 0.3, 0.9, 0.9]
    assert PE_WINDOW_EVENTS == PE_WINDOW_ALL_EVENTS
    assert _window_mean(values) == pytest.approx(sum(values) / len(values))
    # Deliberately not equal to the old prefix answer.
    assert _window_mean(values) != pytest.approx(_window_mean(values, window=3))


def test_window_report_names_the_mode_not_the_sentinel() -> None:
    """"pe_window_events: 0" would read as a broken run, not as whole-phase."""

    assert describe_pe_window()["pe_window_mode"] == "all_events"
    assert describe_pe_window(window=3)["pe_window_mode"] == "prefix"
    assert describe_pe_window(window=3)["pe_window_events"] == 3


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
    path = write_results_json(results, stats, lora_choice=LORA_CHOICE_OFF)
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert "protocol" in payload
    assert "signal_version" in payload
    assert "n_pairs" in payload
    assert "pairs" in payload
    assert "summary" in payload
    assert payload["protocol"] == "C_PRIME"
    assert payload["pe_window_events"] == PE_WINDOW_EVENTS
    assert payload["pe_window_mode"] == "all_events"
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
    path = write_results_json(results, stats, lora_choice=LORA_CHOICE_OFF)
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["pairs"][0]["lived"]["delta_pe"] is None


def test_train_adapter_skips_when_lora_disabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DAU_LORA_ENABLED", "0")
    lived_examples = [{"event_counter": i, "prediction_error": 0.1 * i} for i in range(3)]
    outcome = _train_adapter("test-agent", lived_examples)
    assert outcome.n_pairs_trained == 0
    assert outcome.n_pairs_rejected == 0
    # Skipped, not "trained and moved nothing" — I1.1 has to tell them apart.
    assert outcome.lora_b_abs_sum_delta != outcome.lora_b_abs_sum_delta


def test_lock_seeds_honours_env_temperature_set_after_import(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """GAP-15: _lock_seeds used to write the import-time value back."""

    monkeypatch.setenv("DAU_LLM_SEED", "0")
    monkeypatch.setenv(LLM_TEMPERATURE_ENV, "0.7")
    _lock_seeds(2001)
    assert os.environ[LLM_TEMPERATURE_ENV] == "0.7"


def test_temperature_defaults_when_env_unset(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(LLM_TEMPERATURE_ENV, raising=False)
    assert _temperature() == TEMPERATURE_DEFAULT


def test_temperature_rejects_unparseable_env(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A silent fallback would run one tool and report another."""

    monkeypatch.setenv(LLM_TEMPERATURE_ENV, "warm")
    with pytest.raises(ValueError):
        _temperature()


def test_write_results_json_reports_effective_temperature(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The JSON must report the T the backend actually reads (D-004)."""

    out = tmp_path / "protocol_c_prime_results.json"
    monkeypatch.setattr("dau.diagnostics.run_protocol_c_prime.RESULTS_PATH", out)
    monkeypatch.setattr("dau.diagnostics.run_protocol_c_prime.N_PAIRS", 1)
    monkeypatch.setenv(LLM_TEMPERATURE_ENV, "0.7")
    results = [_pair(2001, -0.05, 0.02, 0.01)]
    path = write_results_json(results, _compute_stats(results), lora_choice=LORA_CHOICE_OFF)
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["temperature"] == 0.7


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


@pytest.fixture
def lora_env(monkeypatch: pytest.MonkeyPatch):
    """Declare the env resolve_lora_choice writes so it is restored after."""

    monkeypatch.setenv(LORA_ENABLED_ENV, "0")
    monkeypatch.setenv("DAU_LLM_BACKEND", "groq")
    return monkeypatch


def test_lora_choice_required(lora_env) -> None:
    """GAP-1: falling through to the default is not a choice."""

    with pytest.raises(SystemExit) as excinfo:
        resolve_lora_choice(None)
    assert "--lora" in str(excinfo.value)
    assert "--no-lora" in str(excinfo.value)


def test_lora_off_is_allowed_but_recorded(lora_env) -> None:
    """An untrained run stays legal — it just cannot be silent."""

    assert resolve_lora_choice(False) == LORA_CHOICE_OFF
    assert os.environ[LORA_ENABLED_ENV] == "0"


def test_lora_on_requires_local_backend(lora_env) -> None:
    """Remote endpoints have no weights to train; skipping would be silent."""

    with pytest.raises(SystemExit) as excinfo:
        resolve_lora_choice(True)
    assert "local" in str(excinfo.value)
    # The gate must not leave the environment claiming training is on.
    assert os.environ[LORA_ENABLED_ENV] == "0"


def test_lora_on_sets_env_under_local_backend(lora_env) -> None:
    lora_env.setenv("DAU_LLM_BACKEND", BACKEND_LOCAL)
    assert resolve_lora_choice(True) == LORA_CHOICE_ON
    assert os.environ[LORA_ENABLED_ENV] == "1"


def test_backend_local_name_matches_graph() -> None:
    """tool_identity spells the backend name; graph owns it."""

    from dau.foundation.graph import LLM_BACKEND_LOCAL

    assert BACKEND_LOCAL == LLM_BACKEND_LOCAL


def test_tool_identity_has_no_undeterminable_field(lora_env) -> None:
    """I0.1: any field that cannot be determined must not ship as null."""

    identity = build_tool_identity(lora_choice=LORA_CHOICE_OFF, seeds=[2001, 2002])

    def _walk(node, path: str) -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                _walk(value, f"{path}.{key}")
        elif isinstance(node, list):
            for i, value in enumerate(node):
                _walk(value, f"{path}[{i}]")
        else:
            assert node is not None, f"undeterminable field: {path}"

    _walk(identity, "tool_identity")
    for key in ("backend", "model_id", "quantization", "dpo", "lora", "sampling",
                "seeds", "versions"):
        assert key in identity
    assert identity["seeds"]["start"] == 2001
    assert identity["seeds"]["end"] == 2002
    assert identity["versions"]["torch"]
    # Was a literal 1, which was a fact only while no accumulation existed
    # (D-021/A1, U4). Bound to the constants instead: the point of this field
    # is that the report tracks the trainer, and a literal cannot do that.
    from dau.foundation.constraints import (
        DPO_BATCH_SIZE,
        DPO_GRADIENT_ACCUMULATION_STEPS,
    )

    assert identity["dpo"]["gradient_accumulation_steps"] == (
        DPO_GRADIENT_ACCUMULATION_STEPS
    )
    assert identity["dpo"]["effective_batch_size"] == (
        DPO_BATCH_SIZE * DPO_GRADIENT_ACCUMULATION_STEPS
    )


def test_tool_identity_quantization_matches_loader(lora_env) -> None:
    """The report must read the loader's config, not rebuild its own.

    Two constructions would drift, and a results file that misreports its own
    quantization is the failure this block exists to prevent.
    """

    lora_env.setenv("DAU_LLM_BACKEND", BACKEND_LOCAL)
    from dau.foundation.local_llm import build_load_kwargs

    reported = build_tool_identity(lora_choice=LORA_CHOICE_OFF, seeds=[2001])
    config = build_load_kwargs().get("quantization_config")
    quantization = reported["quantization"]
    if config is None:  # CPU-only build without bitsandbytes
        assert quantization["load_in_4bit"] is False
    else:
        assert quantization["load_in_4bit"] == config.load_in_4bit
        assert quantization["quant_type"] == str(config.bnb_4bit_quant_type)


def test_results_json_carries_tool_identity(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    out = tmp_path / "protocol_c_prime_results.json"
    monkeypatch.setattr("dau.diagnostics.run_protocol_c_prime.RESULTS_PATH", out)
    monkeypatch.setattr("dau.diagnostics.run_protocol_c_prime.N_PAIRS", 1)
    results = [_pair(2001, -0.05, 0.02, 0.01)]
    path = write_results_json(
        results,
        _compute_stats(results),
        lora_choice=LORA_CHOICE_OFF,
    )
    identity = json.loads(path.read_text(encoding="utf-8"))["tool_identity"]
    assert identity["lora"]["choice"] == LORA_CHOICE_OFF
    assert identity["backend"] in {"groq", BACKEND_LOCAL}
    assert identity["model_id"]


def test_results_path_under_dau_runs() -> None:
    assert str(RESULTS_PATH).startswith("dau_runs/")
