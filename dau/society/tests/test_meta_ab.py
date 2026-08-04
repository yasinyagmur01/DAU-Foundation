"""Tests for Meta-Observer A/B harness (NPC System 1 — no Groq)."""

from __future__ import annotations

import pytest

from dau.society.run_convention_pilot import SENSOR_LABEL
from dau.society.run_meta_ab import (
    AB_MODE_OFF,
    AB_MODE_ON,
    _apply_deterministic_env,
    comparison_summary,
    run_ab_arm,
    run_meta_ab,
)


def test_ab_arm_meta_on_and_off_produce_telemetry() -> None:
    """Both arms complete cycles and attach self_model-derived m_ratio."""

    on = run_ab_arm(agent_id="ab-test-on", meta_enabled=True, n_cycles=5)
    off = run_ab_arm(agent_id="ab-test-off", meta_enabled=False, n_cycles=5)
    assert on.mode == AB_MODE_ON
    assert off.mode == AB_MODE_OFF
    assert on.n_cycles == 5
    assert off.n_cycles == 5
    assert on.sensor_label == SENSOR_LABEL
    assert all(c.m_ratio >= 0.0 for c in on.cycles)
    assert all(c.m_ratio >= 0.0 for c in off.cycles)


def test_run_meta_ab_summary_keys() -> None:
    """Paired comparison returns labeled summary with both arms."""

    comp = run_meta_ab(n_cycles=5, force_system_2=False)
    summary = comparison_summary(comp)
    assert summary["sensor_label"] == SENSOR_LABEL
    assert "delta_mean_diff" in summary
    assert "system2_cycles_diff" in summary
    assert summary["on"]["mode"] == AB_MODE_ON
    assert summary["off"]["mode"] == AB_MODE_OFF
    assert summary["on"]["n_cycles"] == 5
    assert summary["off"]["n_cycles"] == 5
    assert "system2_cycles" in summary["on"]


def test_lod_not_reset_each_cycle_allows_divergence() -> None:
    """After fix: LOD evolves across cycles (meta can keep System 2).

    Smoke: both arms finish fixed horizon; system2_cycles field is populated.
    """

    on = run_ab_arm(agent_id="ab-lod-on", meta_enabled=True, n_cycles=8)
    off = run_ab_arm(agent_id="ab-lod-off", meta_enabled=False, n_cycles=8)
    assert on.n_cycles == 8
    assert off.n_cycles == 8
    assert on.system2_cycles >= 0
    assert off.system2_cycles >= 0


def test_deterministic_env_forces_temperature_and_seed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Noise-probe flag pins T=0 and default seed without Groq calls."""

    monkeypatch.delenv("DAU_LLM_TEMPERATURE", raising=False)
    monkeypatch.delenv("DAU_LLM_SEED", raising=False)
    monkeypatch.setenv("DAU_META_AB_DETERMINISTIC", "1")
    protocol = _apply_deterministic_env()
    assert protocol["deterministic"] is True
    assert protocol["temperature"] == "0.0"
    assert protocol["seed"] == "42"
